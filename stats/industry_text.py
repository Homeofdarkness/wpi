"""TOML industrial configuration and readable calculated resource state."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from typing import Literal

import pydantic
import yaml

from functions.time_models import REFERENCE_TURN_MONTHS
from stats.industry_components import (
    ExtractionGroup,
    ExtractionOperation,
    ResourceRegistration,
    ResourceState,
    ResourceType,
)
from stats.industry_effects import IndustrialEffect, default_industrial_effects
from stats.production_components import ProductionRecipeId, ProductionRule


# Deprecated names kept so older integrations can still identify/import the
# former YAML v2 block.  TOML v3 output does not emit either marker.
CONFIG_START = "НАСТРОЙКА ПРОМЫШЛЕННОСТИ YAML"
CONFIG_END = "КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ"
LEGACY_CONFIG_START = "НАСТРОЙКА ПРОМЫШЛЕННОСТИ"
TOML_SCHEMA_PATTERN = re.compile(r"^schema_version\s*=\s*3(?:\s*#.*)?$")

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


class _ResourceConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str = pydantic.Field(..., min_length=1)
    group: ExtractionGroup
    availability: float = pydantic.Field(100.0, ge=0, le=100)
    quality: float = pydantic.Field(100.0, ge=0, le=100)
    consumption_per_month: float = pydantic.Field(
        0.0,
        ge=0,
        validation_alias=pydantic.AliasChoices(
            "consumption_per_month",
            "consumption",
        ),
    )
    storage_capacity: float = pydantic.Field(0.0, ge=0)


class _ExtractionConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    intensity: float = pydantic.Field(100.0, ge=0, le=100)
    priority: int = pydantic.Field(1, ge=1)


class _ProductionConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    id: str = pydantic.Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    name: str = pydantic.Field(..., min_length=1)
    active: bool = True
    batches: float = pydantic.Field(..., ge=0)
    turns: float | None = pydantic.Field(None, ge=0)
    months: int | None = pydantic.Field(None, ge=0)
    inputs: dict[ResourceType, float] = pydantic.Field(default_factory=dict)
    outputs: dict[ResourceType, float] = pydantic.Field(min_length=1)
    byproducts: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )

    @pydantic.model_validator(mode="after")
    def non_negative_resource_amounts(self) -> _ProductionConfig:
        if self.turns is not None and self.months is not None:
            raise ValueError("Укажите либо устаревшее turns, либо months")
        for mapping in (self.inputs, self.outputs, self.byproducts):
            if any(value < 0 for value in mapping.values()):
                raise ValueError(
                    "Количество ресурса не может быть отрицательным"
                )
        return self


class _IndustryConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    schema_version: Literal[2, 3]
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
    """Render marker-free TOML v3 that can be edited or saved directly."""
    active_resources = [state for state in resources.values() if state.enabled]
    lines = ["schema_version = 3"]
    if not active_resources:
        lines.append("resources = {}")
    if not operations:
        lines.append("extraction = {}")
    if not production_rules:
        lines.append("production = []")
    if not effects:
        lines.append("effects = []")

    for state in active_resources:
        _append_toml_block(
            lines,
            [
                f"[resources.{state.resource.value}]",
                f"name = {_toml_string(state.definition.name)}",
                f"group = {_toml_string(state.definition.group.value)}",
                f"availability = {_toml_float(state.accessibility)}",
                f"quality = {_toml_float(state.quality)}",
                "consumption_per_month = "
                f"{_toml_float(demands.get(state.resource, 0.0))}",
                f"storage_capacity = {_toml_float(state.storage_capacity)}",
            ],
        )

    for operation in operations:
        _append_toml_block(
            lines,
            [
                f"[extraction.{operation.target}]",
                f"intensity = {_toml_float(operation.intensity)}",
                f"priority = {operation.priority}",
            ],
        )

    for rule in production_rules:
        block = [
            "[[production]]",
            f"id = {_toml_string(rule.rule_id)}",
            f"name = {_toml_string(rule.name)}",
            f"active = {_toml_bool(rule.enabled)}",
            f"batches = {_toml_float(rule.batches)}",
        ]
        if rule.turns_remaining is not None:
            block.append(
                "months = "
                f"{round(rule.turns_remaining * REFERENCE_TURN_MONTHS)}"
            )
        block.extend(
            (
                f"inputs = {_toml_resource_map(rule.inputs)}",
                f"outputs = {_toml_resource_map(rule.outputs)}",
                f"byproducts = {_toml_resource_map(rule.byproducts)}",
            )
        )
        _append_toml_block(lines, block)

    for effect in effects:
        dependencies = ", ".join(
            (
                f"{{ resource = {_toml_string(item.resource.value)} }}"
                if item.resource is not None
                else f"{{ group = {_toml_string(item.group.value)} }}"
            )
            for item in effect.dependencies
        )
        targets = ", ".join(_toml_string(item) for item in effect.targets)
        _append_toml_block(
            lines,
            [
                "[[effects]]",
                f"id = {_toml_string(effect.id)}",
                f"dependencies = [{dependencies}]",
                f"targets = [{targets}]",
                f"formula = {_toml_string(effect.formula)}",
            ],
        )
    return "\n".join(lines)


def _append_toml_block(lines: list[str], block: list[str]) -> None:
    if lines and lines[-1]:
        lines.append("")
    lines.extend(block)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_float(value: float | int) -> str:
    return f"{round(float(value), 1):.1f}"


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_resource_map(values: dict[ResourceType, float]) -> str:
    if not values:
        return "{}"
    pairs = ", ".join(
        f"{resource.value} = {_toml_float(amount)}"
        for resource, amount in values.items()
    )
    return f"{{ {pairs} }}"


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


def _configuration_body(text: str) -> tuple[str, str] | None:
    lines = text.splitlines()
    if any(line.strip() == LEGACY_CONFIG_START for line in lines):
        raise ValueError(
            "Старый строковый формат промышленности удалён; нужен TOML "
            "schema_version = 3"
        )
    yaml_starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == CONFIG_START
    ]
    yaml_ends = [
        index for index, line in enumerate(lines) if line.strip() == CONFIG_END
    ]
    if yaml_starts or yaml_ends:
        if len(yaml_starts) != 1 or len(yaml_ends) != 1:
            raise ValueError(
                "Ожидался ровно один полный старый YAML-блок промышленности"
            )
        start, end = yaml_starts[0], yaml_ends[0]
        if end <= start:
            raise ValueError(
                "Конец старой настройки промышленности находится до начала"
            )
        return "yaml", "\n".join(lines[start + 1 : end])

    toml_starts = [
        index
        for index, line in enumerate(lines)
        if TOML_SCHEMA_PATTERN.fullmatch(line.strip())
    ]
    if not toml_starts:
        return None
    if len(toml_starts) != 1:
        raise ValueError("Найдено несколько TOML-конфигураций промышленности")
    start = toml_starts[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped == "СОСТОЯНИЕ РЕСУРСОВ" or stripped.startswith("```"):
            end = index
            break
    return "toml", "\n".join(lines[start:end]).rstrip()


def parse_industry_configuration(text: str) -> IndustryTextState | None:
    """Parse TOML v3 or legacy YAML v2 and merge calculated resource state."""
    configuration = _configuration_body(text)
    if configuration is None:
        return None
    format_name, body = configuration
    if format_name == "toml":
        try:
            raw = tomllib.loads(body)
        except tomllib.TOMLDecodeError as error:
            raise ValueError(
                f"Некорректный TOML промышленности: {error}"
            ) from error
    else:
        try:
            raw = yaml.safe_load(body) or {}
        except yaml.YAMLError as error:
            raise ValueError(
                f"Некорректный старый YAML промышленности: {error}"
            ) from error
    try:
        config = _IndustryConfig.model_validate(raw)
    except pydantic.ValidationError as error:
        raise ValueError(
            f"Некорректная настройка промышленности:\n{error}"
        ) from error
    expected_version = 3 if format_name == "toml" else 2
    if config.schema_version != expected_version:
        raise ValueError(
            f"Для {format_name.upper()} ожидается schema_version "
            f"{expected_version}, получено {config.schema_version}"
        )

    registrations = {
        alias: ResourceRegistration(
            resource=alias,
            name=item.name,
            group=item.group,
            accessibility=item.availability,
            quality=item.quality,
            consumption_per_month=item.consumption_per_month,
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
                turns_remaining=(
                    item.turns
                    if item.turns is not None
                    else (
                        item.months / REFERENCE_TURN_MONTHS
                        if item.months is not None
                        else None
                    )
                ),
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
        registration.resource: registration.consumption_per_month
        for registration in registrations.values()
        if registration.consumption_per_month > 0
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
