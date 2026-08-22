"""YAML industrial configuration and readable calculated resource state."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import pydantic
import yaml

from stats.industry_components import (
    ExtractionGroup,
    ExtractionOperation,
    ResourceRegistration,
    ResourceState,
    ResourceType,
)
from stats.industry_effects import IndustrialEffect, default_industrial_effects
from stats.production_components import ProductionRecipeId, ProductionRule


CONFIG_START = "НАСТРОЙКА ПРОМЫШЛЕННОСТИ YAML"
CONFIG_END = "КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ"
LEGACY_CONFIG_START = "НАСТРОЙКА ПРОМЫШЛЕННОСТИ"

GROUP_NAMES: dict[ExtractionGroup, str] = {
    ExtractionGroup.FORESTRY: "Лесное хозяйство",
    ExtractionGroup.FRESH_WATER: "Пресная вода",
    ExtractionGroup.MINERAL_WATER: "Минеральная вода",
    ExtractionGroup.PRECIOUS: "Драгоценные ресурсы",
    ExtractionGroup.STRATEGIC_METALS: "Стратегические металлы",
    ExtractionGroup.NONFERROUS: "Цветные металлы",
    ExtractionGroup.FERROUS: "Чёрные металлы",
    ExtractionGroup.HEAVY_METALS: "Тяжёлые металлы",
    ExtractionGroup.CHEMICAL: "Химическое сырьё",
    ExtractionGroup.CONSTRUCTION: "Строительные материалы",
    ExtractionGroup.SOLID_FUEL: "Твёрдое топливо",
    ExtractionGroup.HYDROCARBONS: "Углеводороды",
    ExtractionGroup.RARE_EARTH: "Редкоземельные металлы",
    ExtractionGroup.SALTS: "Соли",
    ExtractionGroup.SOIL: "Почвы",
    ExtractionGroup.PLANTATIONS: "Плантации",
    ExtractionGroup.RECYCLING: "Переработка отходов",
    ExtractionGroup.MINERALS: "Минералы",
    ExtractionGroup.UNIQUE: "Уникальные ресурсы",
}


class _IndentedSafeDumper(yaml.SafeDumper):
    """Keep sequence items indented under their YAML mapping key."""

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, indentless=False)


class _FoldedString(str):
    pass


def _represent_folded_string(
    dumper: _IndentedSafeDumper,
    value: _FoldedString,
):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        value,
        style=">",
    )


_IndentedSafeDumper.add_representer(_FoldedString, _represent_folded_string)


class _ResourceConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str = pydantic.Field(..., min_length=1)
    group: ExtractionGroup
    availability: float = pydantic.Field(100.0, ge=0, le=100)
    quality: float = pydantic.Field(100.0, ge=0, le=100)
    consumption: float = pydantic.Field(0.0, ge=0)
    storage_capacity: float = pydantic.Field(0.0, ge=0)


class _ExtractionConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    intensity: float = pydantic.Field(100.0, ge=0, le=100)
    priority: float = pydantic.Field(1.0, gt=0)


class _ProductionConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    id: str = pydantic.Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    name: str = pydantic.Field(..., min_length=1)
    active: bool = True
    batches: float = pydantic.Field(..., ge=0)
    turns: int | None = pydantic.Field(None, ge=0)
    inputs: dict[ResourceType, float] = pydantic.Field(default_factory=dict)
    outputs: dict[ResourceType, float] = pydantic.Field(min_length=1)
    byproducts: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )

    @pydantic.model_validator(mode="after")
    def non_negative_resource_amounts(self) -> _ProductionConfig:
        for mapping in (self.inputs, self.outputs, self.byproducts):
            if any(value < 0 for value in mapping.values()):
                raise ValueError(
                    "Количество ресурса не может быть отрицательным"
                )
        return self


class _IndustryConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    schema_version: Literal[2]
    resources: dict[ResourceType, _ResourceConfig] = pydantic.Field(
        default_factory=dict
    )
    extraction: dict[str, _ExtractionConfig] = pydantic.Field(
        default_factory=dict
    )
    production: list[_ProductionConfig] = pydantic.Field(default_factory=list)
    effects: list[IndustrialEffect] = pydantic.Field(
        default_factory=default_industrial_effects
    )

    @pydantic.field_validator("extraction")
    @classmethod
    def validate_extraction_aliases(
        cls,
        value: dict[str, _ExtractionConfig],
    ) -> dict[str, _ExtractionConfig]:
        invalid = [
            alias
            for alias in value
            if re.fullmatch(r"[a-z][a-z0-9_]*", alias) is None
        ]
        if invalid:
            raise ValueError(
                f"Некорректные alias добычи: {', '.join(invalid)}"
            )
        return value


@dataclass(frozen=True)
class IndustryTextState:
    registrations: list[ResourceRegistration]
    operations: list[ExtractionOperation]
    production_rules: list[ProductionRule]
    effects: list[IndustrialEffect]
    demands: dict[ResourceType, float]
    extracted: dict[ResourceType, float]
    shortages: dict[ResourceType, float]


def _number(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".rstrip("0").rstrip(".")


def _float(value: str) -> float:
    return float(value.strip().replace(",", "."))


def _pair(value: str) -> tuple[float, float]:
    left, separator, right = value.partition("/")
    if not separator:
        raise ValueError(f"Ожидалась пара текущее/вместимость: {value!r}")
    return _float(left), _float(right)


def render_resource_state_table(
    resources: list[ResourceState],
    extracted: dict[ResourceType, float],
    shortages: dict[ResourceType, float],
) -> list[str]:
    headers = ("Ресурс", "Склад", "Добыто", "Дефицит")
    rows = [
        (
            f"{state.definition.name} [{state.resource.value}]",
            f"{_number(state.stockpile)} / {_number(state.storage_capacity)}",
            _number(extracted.get(state.resource, 0.0)),
            _number(shortages.get(state.resource, 0.0)),
        )
        for state in resources
    ]
    return _aligned_table(headers, rows)


def render_group_state_table(
    resources: list[ResourceState],
    extracted: dict[ResourceType, float],
    shortages: dict[ResourceType, float],
) -> list[str]:
    """Render every fixed group, including groups without country resources."""
    headers = ("Группа", "Ресурсов", "Добыто", "Дефицит")
    rows: list[tuple[str, ...]] = []
    for group in ExtractionGroup:
        group_resources = [item for item in resources if item.group is group]
        rows.append(
            (
                f"{GROUP_NAMES[group]} [{group.value}]",
                str(len(group_resources)),
                _number(
                    sum(
                        extracted.get(item.resource, 0.0)
                        for item in group_resources
                    )
                ),
                _number(
                    sum(
                        shortages.get(item.resource, 0.0)
                        for item in group_resources
                    )
                ),
            )
        )
    return _aligned_table(headers, rows)


def _aligned_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
) -> list[str]:
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def aligned(row: tuple[str, ...]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ).rstrip()

    return [
        aligned(headers),
        aligned(tuple("-" * width for width in widths)),
        *map(aligned, rows),
    ]


def render_industry_configuration(
    *,
    resources: dict[ResourceType, ResourceState],
    operations: list[ExtractionOperation],
    production_rules: list[ProductionRule],
    effects: list[IndustrialEffect],
    demands: dict[ResourceType, float],
) -> str:
    """Render a structured, editable YAML configuration."""
    active_resources = [state for state in resources.values() if state.enabled]
    payload = {
        "schema_version": 2,
        "resources": {
            state.resource.value: {
                "name": state.definition.name,
                "group": state.definition.group.value,
                "availability": round(state.accessibility, 1),
                "quality": round(state.quality, 1),
                "consumption": round(demands.get(state.resource, 0.0), 1),
                "storage_capacity": round(state.storage_capacity, 1),
            }
            for state in active_resources
        },
        "extraction": {
            operation.target: {
                "intensity": round(operation.intensity, 1),
                "priority": round(operation.priority, 1),
            }
            for operation in operations
        },
        "production": [
            {
                "id": rule.rule_id,
                "name": rule.name,
                "active": rule.enabled,
                "batches": round(rule.batches, 1),
                "turns": rule.turns_remaining,
                "inputs": _plain_resource_map(rule.inputs),
                "outputs": _plain_resource_map(rule.outputs),
                "byproducts": _plain_resource_map(rule.byproducts),
            }
            for rule in production_rules
        ],
        "effects": [_effect_payload(effect) for effect in effects],
    }
    body = yaml.dump(
        payload,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    ).rstrip()
    return f"{CONFIG_START}\n{body}\n{CONFIG_END}"


def _plain_resource_map(values: dict[ResourceType, float]) -> dict[str, float]:
    return {
        resource.value: round(amount, 1) for resource, amount in values.items()
    }


def _effect_payload(effect: IndustrialEffect) -> dict:
    payload = effect.model_dump(mode="json", exclude_none=True)
    payload["formula"] = _FoldedString(effect.formula)
    return payload


def _parse_state_row(
    line: str,
) -> tuple[ResourceType, float, float, float, float]:
    cells = [cell.strip() for cell in line.split("|")]
    if len(cells) != 4:
        raise ValueError(f"Некорректная строка состояния ресурса: {line!r}")
    match = re.search(r"\[([a-z][a-z0-9_]*)\]$", cells[0])
    if match is None:
        raise ValueError(f"В состоянии ресурса нет alias: {line!r}")
    stockpile, storage = _pair(cells[1])
    return (
        ResourceType(match.group(1)),
        stockpile,
        storage,
        _float(cells[2]),
        _float(cells[3]),
    )


def _configuration_body(text: str) -> str | None:
    lines = text.splitlines()
    if any(line.strip() == LEGACY_CONFIG_START for line in lines):
        raise ValueError(
            "Старый строковый формат промышленности удалён; нужен YAML "
            "schema_version: 2"
        )
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == CONFIG_START
    ]
    ends = [
        index for index, line in enumerate(lines) if line.strip() == CONFIG_END
    ]
    if not starts:
        return None
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("Ожидался ровно один полный YAML-блок промышленности")
    start, end = starts[0], ends[0]
    if end <= start:
        raise ValueError("Конец настройки промышленности находится до начала")
    return "\n".join(lines[start + 1 : end])


def parse_industry_configuration(text: str) -> IndustryTextState | None:
    """Parse YAML rules and merge the separately rendered calculated state."""
    body = _configuration_body(text)
    if body is None:
        return None
    try:
        raw = yaml.safe_load(body) or {}
    except yaml.YAMLError as error:
        raise ValueError(
            f"Некорректный YAML промышленности: {error}"
        ) from error
    try:
        config = _IndustryConfig.model_validate(raw)
    except pydantic.ValidationError as error:
        raise ValueError(
            f"Некорректная настройка промышленности:\n{error}"
        ) from error

    registrations = {
        alias: ResourceRegistration(
            resource=alias,
            name=item.name,
            group=item.group,
            accessibility=item.availability,
            quality=item.quality,
            consumption_per_turn=item.consumption,
            storage_capacity=item.storage_capacity,
        )
        for alias, item in config.resources.items()
    }
    operations = [
        ExtractionOperation(
            target=alias,
            intensity=item.intensity,
            priority=item.priority,
        )
        for alias, item in config.extraction.items()
    ]
    production_rules: list[ProductionRule] = []
    seen_rules: set[str] = set()
    for item in config.production:
        if item.id in seen_rules:
            raise ValueError(f"Правило {item.id} указано дважды")
        seen_rules.add(item.id)
        target_resource: ResourceType | None = None
        target_group: ExtractionGroup | None = None
        output_resources = list(item.outputs)
        if len(output_resources) == 1:
            target_resource = output_resources[0]
        else:
            try:
                output_groups = {
                    registrations[resource].group
                    for resource in output_resources
                }
            except KeyError as error:
                raise ValueError(
                    f"Выход правила {item.id} не зарегистрирован: "
                    f"{error.args[0]}"
                ) from error
            if len(output_groups) != 1:
                raise ValueError(
                    f"Выходы правила {item.id} относятся к разным группам"
                )
            target_group = output_groups.pop()
        production_rules.append(
            ProductionRule(
                rule_id=item.id,
                name=item.name,
                recipe=(
                    ProductionRecipeId(item.id)
                    if item.id
                    in {recipe.value for recipe in ProductionRecipeId}
                    else None
                ),
                target_resource=target_resource,
                target_group=target_group,
                enabled=item.active,
                batches=item.batches,
                turns_remaining=item.turns,
                inputs=item.inputs,
                outputs=item.outputs,
                byproducts=item.byproducts,
            )
        )

    extracted: dict[ResourceType, float] = {}
    shortages: dict[ResourceType, float] = {}
    state_sections = [
        index
        for index, line in enumerate(text.splitlines())
        if line.strip() == "СОСТОЯНИЕ РЕСУРСОВ"
    ]
    if len(state_sections) > 1:
        raise ValueError("Ожидалось не более одного состояния ресурсов")
    lines = text.splitlines()
    for index in state_sections:
        for state_line in lines[index + 1 :]:
            stripped = state_line.strip()
            compact = stripped.replace("|", "").replace(" ", "")
            if (
                not stripped
                or stripped.startswith("Ресурс")
                or (compact and set(compact) == {"-"})
            ):
                continue
            if "|" not in stripped or not re.search(
                r"\[[a-z][a-z0-9_]*\]", stripped
            ):
                break
            resource, stockpile, shown_storage, mined, shortage = (
                _parse_state_row(stripped)
            )
            if resource not in registrations:
                raise ValueError(
                    "Есть состояние незарегистрированного ресурса "
                    f"{resource.value}"
                )
            registration = registrations[resource]
            if registration.storage_capacity == 0:
                registration.storage_capacity = shown_storage
            if abs(registration.storage_capacity - shown_storage) > 0.051:
                raise ValueError(
                    f"Вместимость склада {resource.value} различается в "
                    "состоянии и настройках"
                )
            registration.stockpile = stockpile
            extracted[resource] = mined
            shortages[resource] = shortage

    demands = {
        registration.resource: registration.consumption_per_turn
        for registration in registrations.values()
        if registration.consumption_per_turn > 0
    }
    return IndustryTextState(
        registrations=list(registrations.values()),
        operations=operations,
        production_rules=production_rules,
        effects=config.effects,
        demands=demands,
        extracted=extracted,
        shortages=shortages,
    )
