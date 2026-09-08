"""Safe, configurable effects driven by industrial resource coverage."""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, get_args

import pydantic

from stats.industry_components import ExtractionGroup, ResourceType


class SpecialEffectTarget(StrEnum):
    """Reserved aliases requiring behavior beyond a normal numeric field."""

    POPULATION_GROWTH = "population_growth"
    INFRASTRUCTURE_EXPENSES = "infrastructure_expenses"


# Existing Python integrations may still import the former enum.  It is no
# longer the type of ``IndustrialEffect.targets`` and does not restrict them.
EffectTarget = SpecialEffectTarget


class EffectPhase(StrEnum):
    """Internal turn stages; the public TOML never has to specify them."""

    AFTER_RESOURCES = "after_resources"
    INDUSTRY_DERIVED = "industry_derived"
    AFTER_INDUSTRY = "after_industry"
    AFTER_TAX = "after_tax"
    AFTER_FOREX = "after_forex"
    AFTER_TRADE = "after_trade"
    AFTER_PROBABILITIES = "after_probabilities"
    FINALIZE = "finalize"


EffectTargetName = Annotated[
    str,
    pydantic.StringConstraints(
        pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?$"
    ),
]

EFFECT_SECTIONS = (
    "economy",
    "industry",
    "agriculture",
    "inner_politics",
    "probabilities",
)

_INDUSTRY_DERIVED_FIELDS = {
    "civil_usage",
    "industry_coefficient",
    "civil_efficiency",
    "max_potential",
    "expected_wastes",
}

_EVENT_PROBABILITY_FIELDS = {
    "industrial_accident_chance",
    "supply_disruption_chance",
    "population_epidemic_chance",
    "agricultural_epidemic_chance",
    "natural_disaster_chance",
    "mass_protest_chance",
    "separatist_crisis_chance",
    "major_sabotage_chance",
}


class EffectDependency(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    resource: ResourceType | None = None
    group: ExtractionGroup | None = None

    @pydantic.model_validator(mode="after")
    def require_one_reference(self) -> EffectDependency:
        if (self.resource is None) == (self.group is None):
            raise ValueError(
                "Зависимость эффекта должна содержать ровно один resource "
                "или group"
            )
        return self

    @property
    def key(self) -> tuple[str, str]:
        if self.resource is not None:
            return "resources", self.resource.value
        assert self.group is not None
        return "groups", self.group.value


class IndustrialEffect(pydantic.BaseModel):
    """One formula applied independently to every listed target stat."""

    model_config = pydantic.ConfigDict(extra="forbid")

    id: str = pydantic.Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    dependencies: list[EffectDependency] = pydantic.Field(min_length=1)
    targets: list[EffectTargetName] = pydantic.Field(min_length=1)
    formula: str = pydantic.Field(..., min_length=1)

    @pydantic.model_validator(mode="after")
    def validate_effect(self) -> IndustrialEffect:
        dependency_keys = [item.key for item in self.dependencies]
        if len(dependency_keys) != len(set(dependency_keys)):
            raise ValueError(f"Эффект {self.id} содержит повтор зависимости")
        if len(self.targets) != len(set(self.targets)):
            raise ValueError(f"Эффект {self.id} содержит повтор цели")
        _validate_formula(self.formula, set(dependency_keys))
        return self


class DependencyMetric(pydantic.BaseModel):
    deficit: float = pydantic.Field(0.0, ge=0)
    surplus: float = pydantic.Field(0.0, ge=0)


class IndustrialEffectResult(pydantic.BaseModel):
    effect_id: str
    target: EffectTargetName
    target_before: float
    adjustment: float
    target_after: float


@dataclass(frozen=True, slots=True)
class ResolvedEffectTarget:
    """A checked public target bound to one numeric field or special alias."""

    name: str
    phase: EffectPhase
    section: str | None = None
    field_name: str | None = None
    model: pydantic.BaseModel | None = None
    special: SpecialEffectTarget | None = None

    @property
    def canonical_name(self) -> str:
        if self.section is not None and self.field_name is not None:
            return f"{self.section}.{self.field_name}"
        return self.name

    def current_value(self) -> float:
        if self.model is None or self.field_name is None:
            raise ValueError(f"Цель {self.name} требует специальной обработки")
        value = getattr(self.model, self.field_name)
        if value is None:
            raise ValueError(
                f"Цель эффекта {self.name} ещё не рассчитана на текущем этапе"
            )
        return float(value)

    def apply(self, value: float) -> float:
        if self.model is None or self.field_name is None:
            raise ValueError(f"Цель {self.name} требует специальной обработки")
        if not math.isfinite(value):
            raise ValueError(f"Цель эффекта {self.name} получила нечисло")

        field_info = type(self.model).model_fields[self.field_name]
        number_type = _numeric_annotation(field_info.annotation)
        assert number_type is not None
        if self.special is SpecialEffectTarget.POPULATION_GROWTH:
            value = max(value, 0.0)

        bounded = _respect_field_bounds(
            value,
            field_info.metadata,
            number_type,
        )
        validated = pydantic.TypeAdapter(
            field_info.rebuild_annotation()
        ).validate_python(bounded)
        setattr(self.model, self.field_name, validated)
        return float(validated)


def resolve_effect_target(
    world_state: object,
    target_name: str,
) -> ResolvedEffectTarget:
    """Bind declared numeric fields without exposing arbitrary attributes."""
    if target_name == SpecialEffectTarget.INFRASTRUCTURE_EXPENSES:
        return ResolvedEffectTarget(
            name=target_name,
            phase=EffectPhase.AFTER_RESOURCES,
            special=SpecialEffectTarget.INFRASTRUCTURE_EXPENSES,
        )
    if target_name == SpecialEffectTarget.POPULATION_GROWTH:
        return _resolve_model_target(
            world_state,
            section="economy",
            field_name="income",
            public_name=target_name,
            special=SpecialEffectTarget.POPULATION_GROWTH,
        )

    if "." in target_name:
        section, field_name = target_name.split(".", maxsplit=1)
        if section not in EFFECT_SECTIONS:
            raise ValueError(
                f"Неизвестный раздел цели {target_name}: {section}. "
                f"Доступны: {', '.join(EFFECT_SECTIONS)}"
            )
        return _resolve_model_target(
            world_state,
            section=section,
            field_name=field_name,
            public_name=target_name,
        )

    matching_sections = [
        section
        for section in EFFECT_SECTIONS
        if target_name in type(getattr(world_state, section)).model_fields
    ]
    if not matching_sections:
        raise ValueError(f"Неизвестная целевая стата эффекта: {target_name}")
    if len(matching_sections) > 1:
        variants = ", ".join(
            f"{section}.{target_name}" for section in matching_sections
        )
        raise ValueError(
            f"Неоднозначная целевая стата {target_name}. "
            f"Укажите раздел: {variants}"
        )
    return _resolve_model_target(
        world_state,
        section=matching_sections[0],
        field_name=target_name,
        public_name=target_name,
    )


def _resolve_model_target(
    world_state: object,
    *,
    section: str,
    field_name: str,
    public_name: str,
    special: SpecialEffectTarget | None = None,
) -> ResolvedEffectTarget:
    model = getattr(world_state, section)
    field_info = type(model).model_fields.get(field_name)
    if field_info is None:
        raise ValueError(
            f"В разделе {section} отсутствует целевая стата {field_name}"
        )
    if _numeric_annotation(field_info.annotation) is None:
        raise ValueError(
            f"Цель эффекта {public_name} должна быть числовой статой, "
            "а не списком, объектом или строкой"
        )
    return ResolvedEffectTarget(
        name=public_name,
        phase=_phase_for_field(section, field_name),
        section=section,
        field_name=field_name,
        model=model,
        special=special,
    )


def _phase_for_field(section: str, field_name: str) -> EffectPhase:
    if section == "industry":
        if field_name in _INDUSTRY_DERIVED_FIELDS:
            return EffectPhase.INDUSTRY_DERIVED
        if field_name in {"consumption_of_goods", "industry_income"}:
            return EffectPhase.AFTER_INDUSTRY
    if section == "economy":
        if field_name == "tax_income":
            return EffectPhase.AFTER_TAX
        if field_name == "forex":
            return EffectPhase.AFTER_FOREX
        if field_name == "trade_income":
            return EffectPhase.AFTER_TRADE
        if field_name in {"current_budget", "money_income", "prev_budget"}:
            return EffectPhase.FINALIZE
    if section == "probabilities" and field_name in _EVENT_PROBABILITY_FIELDS:
        return EffectPhase.AFTER_PROBABILITIES
    if section == "inner_politics" and field_name in {
        "research_success_chance",
        "society_decline",
    }:
        return EffectPhase.FINALIZE
    return EffectPhase.AFTER_RESOURCES


def _numeric_annotation(annotation: object) -> type[int] | type[float] | None:
    if annotation is int or annotation is float:
        return annotation
    arguments = get_args(annotation)
    non_null = [item for item in arguments if item is not type(None)]
    if len(arguments) == 2 and len(non_null) == 1:
        return _numeric_annotation(non_null[0])
    return None


def _respect_field_bounds(
    value: float,
    metadata: list[object],
    number_type: type[int] | type[float],
) -> int | float:
    result: int | float = round(value) if number_type is int else float(value)
    for item in metadata:
        if (minimum := getattr(item, "ge", None)) is not None:
            bound = math.ceil(minimum) if number_type is int else minimum
            result = max(result, bound)
        if (exclusive_minimum := getattr(item, "gt", None)) is not None:
            bound = (
                math.floor(exclusive_minimum) + 1
                if number_type is int
                else math.nextafter(exclusive_minimum, math.inf)
            )
            result = max(result, bound)
        if (maximum := getattr(item, "le", None)) is not None:
            bound = math.floor(maximum) if number_type is int else maximum
            result = min(result, bound)
        if (exclusive_maximum := getattr(item, "lt", None)) is not None:
            bound = (
                math.ceil(exclusive_maximum) - 1
                if number_type is int
                else math.nextafter(exclusive_maximum, -math.inf)
            )
            result = min(result, bound)
    return int(result) if number_type is int else float(result)


def default_industrial_effects() -> list[IndustrialEffect]:
    return [
        IndustrialEffect(
            id="freshwater_population_growth",
            dependencies=[EffectDependency(resource=ResourceType.FRESH_WATER)],
            targets=[SpecialEffectTarget.POPULATION_GROWTH],
            formula="-target * resources.fresh_water.deficit * 0.2",
        ),
        IndustrialEffect(
            id="construction_infrastructure_expenses",
            dependencies=[
                EffectDependency(group=ExtractionGroup.CONSTRUCTION)
            ],
            targets=[SpecialEffectTarget.INFRASTRUCTURE_EXPENSES],
            formula=(
                "target * (0.4 * groups.construction.deficit - "
                "min(0.25 * groups.construction.surplus, 0.2))"
            ),
        ),
    ]


def evaluate_effect_formula(
    effect: IndustrialEffect,
    *,
    target: float,
    resources: dict[str, DependencyMetric],
    groups: dict[str, DependencyMetric],
) -> float:
    """Evaluate an effect without Python ``eval`` or object access."""
    tree = ast.parse(effect.formula, mode="eval")
    value = _evaluate_node(
        tree.body,
        target=float(target),
        resources=resources,
        groups=groups,
    )
    if not math.isfinite(value):
        raise ValueError(f"Формула эффекта {effect.id} вернула нечисло")
    return float(value)


def _attribute_path(node: ast.AST) -> tuple[str, ...] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return tuple(reversed(parts))


def _validate_formula(
    formula: str,
    dependencies: set[tuple[str, str]],
) -> None:
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as error:
        raise ValueError(
            f"Некорректная формула эффекта: {error.msg}"
        ) from error
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            path = _attribute_path(node)
            # ``ast.walk`` also visits the intermediate
            # ``resources.alias`` node of ``resources.alias.deficit``.
            if path is not None and len(path) == 2:
                continue
            if path is None or len(path) != 3:
                raise ValueError("Доступ в формуле должен иметь три части")
            root, alias, metric = path
            if root not in {"resources", "groups"}:
                raise ValueError(f"Неизвестная область формулы: {root}")
            if (root, alias) not in dependencies:
                raise ValueError(
                    f"Формула использует необъявленную зависимость "
                    f"{root}.{alias}"
                )
            if metric not in {"deficit", "surplus"}:
                raise ValueError(f"Неизвестная метрика зависимости: {metric}")
        elif isinstance(node, ast.Name):
            if node.id not in {
                "target",
                "resources",
                "groups",
                "min",
                "max",
                "abs",
            }:
                raise ValueError(f"Неизвестное имя в формуле: {node.id}")
        elif isinstance(
            node,
            (
                ast.Expression,
                ast.Load,
                ast.Constant,
                ast.BinOp,
                ast.UnaryOp,
                ast.Call,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Pow,
                ast.USub,
                ast.UAdd,
            ),
        ):
            continue
        else:
            raise ValueError(
                f"Конструкция {type(node).__name__} запрещена в формуле"
            )


def _evaluate_node(
    node: ast.AST,
    *,
    target: float,
    resources: dict[str, DependencyMetric],
    groups: dict[str, DependencyMetric],
) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.Name) and node.id == "target":
        return target
    if isinstance(node, ast.Attribute):
        path = _attribute_path(node)
        if path is None or len(path) != 3:
            raise ValueError("Некорректный доступ к зависимости")
        root, alias, metric = path
        namespace = resources if root == "resources" else groups
        try:
            dependency = namespace[alias]
        except KeyError as error:
            raise ValueError(
                f"Нет данных зависимости {root}.{alias}"
            ) from error
        return float(getattr(dependency, metric))
    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(
            node.operand,
            target=target,
            resources=resources,
            groups=groups,
        )
        return -operand if isinstance(node.op, ast.USub) else operand
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(
            node.left,
            target=target,
            resources=resources,
            groups=groups,
        )
        right = _evaluate_node(
            node.right,
            target=target,
            resources=resources,
            groups=groups,
        )
        operations = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.Div: lambda: left / right,
            ast.Pow: lambda: left**right,
        }
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Степень в формуле ограничена диапазоном -8..8")
        try:
            return operations[type(node.op)]()
        except ZeroDivisionError as error:
            raise ValueError("Деление на ноль в формуле эффекта") from error
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        arguments = [
            _evaluate_node(
                item,
                target=target,
                resources=resources,
                groups=groups,
            )
            for item in node.args
        ]
        if node.func.id == "min":
            return min(arguments)
        if node.func.id == "max":
            return max(arguments)
        if node.func.id == "abs" and len(arguments) == 1:
            return abs(arguments[0])
    raise ValueError(f"Недопустимое выражение: {ast.dump(node)}")
