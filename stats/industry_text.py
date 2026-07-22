"""Human-readable and round-trippable industrial configuration text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from stats.industry_components import (
    RESOURCE_CATALOG,
    ExtractionGroup,
    ExtractionOperation,
    ResourceRegistration,
    ResourceState,
    ResourceType,
)
from stats.production_components import ProductionRecipeId, ProductionRule


CONFIG_START = "НАСТРОЙКА ПРОМЫШЛЕННОСТИ"
CONFIG_END = "КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ"

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

_GROUP_RE = re.compile(r"^Группа .+ \[([a-z0-9_]+)\]$")
_RESOURCE_RE = re.compile(r"^Ресурс .+ \[([a-z0-9_]+)\](?: \| (.*))?$")
_EXTRACTION_RE = re.compile(r"^Добыча ([a-z0-9_]+)(?: \| (.*))?$")
_PRODUCTION_RE = re.compile(r"^Правило .+ \[([a-z0-9_]+)\](?: \| (.*))?$")
_TARGET_RE = re.compile(r"^(группа|ресурс)\[([a-z0-9_]+)\]$")


@dataclass(frozen=True)
class IndustryTextState:
    groups: list[ExtractionGroup]
    registrations: list[ResourceRegistration]
    operations: list[ExtractionOperation]
    production_rules: list[ProductionRule]
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


def _int(value: str) -> int:
    return int(_float(value))


def _bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"да", "1", "true", "авто"}:
        return True
    if normalized in {"нет", "0", "false", "вручную"}:
        return False
    raise ValueError(f"Ожидалось да/нет, получено: {value!r}")


def _options(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    result: dict[str, str] = {}
    for token in raw.split(" | "):
        key, separator, value = token.partition("=")
        if not separator:
            raise ValueError(f"Ожидался параметр ключ=значение: {token!r}")
        normalized = key.strip().lower()
        if normalized in result:
            raise ValueError(f"Параметр {normalized!r} указан дважды")
        result[normalized] = value.strip()
    return result


def _validate_keys(
    values: dict[str, str],
    allowed: set[str],
    context: str,
) -> None:
    unknown = set(values) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Неизвестные параметры {context}: {names}")


def _pair(value: str) -> tuple[float, float]:
    left, separator, right = value.partition("/")
    if not separator:
        raise ValueError(f"Ожидалась пара текущее/вместимость: {value!r}")
    return _float(left), _float(right)


def _resource_map(value: str) -> dict[ResourceType, float]:
    if value.strip().lower() in {"-", "нет", ""}:
        return {}
    result: dict[ResourceType, float] = {}
    for token in value.split(","):
        resource, separator, amount = token.strip().partition(":")
        if not separator:
            raise ValueError(f"Ожидалась запись resource:amount: {token!r}")
        resource_id = ResourceType(resource.strip())
        if resource_id in result:
            raise ValueError(f"Ресурс {resource_id.value} указан дважды")
        result[resource_id] = _float(amount)
    return result


def _render_resource_map(values: dict[ResourceType, float]) -> str:
    if not values:
        return "-"
    return ",".join(
        f"{resource.value}:{_number(amount)}"
        for resource, amount in values.items()
    )


def _duration(value: str) -> int | None:
    if value.strip().lower() in {"∞", "постоянно", "без срока"}:
        return None
    return _int(value)


def _render_resource(state: ResourceState, consumption: float) -> str:
    return (
        f"Ресурс {state.definition.name} [{state.resource.value}]"
        f" | группа={state.definition.group.value}"
        f" | доступность={_number(state.accessibility)}"
        f" | качество={_number(state.quality)}"
        f" | расход={_number(consumption)}"
        f" | склад={_number(state.storage_capacity)}"
    )


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


def _render_extraction(operation: ExtractionOperation) -> str:
    return (
        f"Добыча {operation.target}"
        f" | интенсивность={_number(operation.intensity)}"
        f" | приоритет={_number(operation.priority)}"
    )


def _render_production(rule: ProductionRule) -> str:
    duration = (
        "∞" if rule.turns_remaining is None else str(rule.turns_remaining)
    )
    if rule.target_resource is not None:
        target = f"ресурс[{rule.target_resource.value}]"
    else:
        assert rule.target_group is not None
        target = f"группа[{rule.target_group.value}]"
    status = "активно" if rule.enabled else "завершено"
    return (
        f"Правило {rule.name} [{rule.rule_id}]"
        f" | цель={target}"
        f" | статус={status}"
        f" | партий={_number(rule.batches)}"
        f" | ходов={duration}"
        f" | вход={_render_resource_map(rule.inputs)}"
        f" | выход={_render_resource_map(rule.outputs)}"
        f" | побочно={_render_resource_map(rule.byproducts)}"
    )


def render_industry_configuration(
    *,
    resources: dict[ResourceType, ResourceState],
    operations: list[ExtractionOperation],
    production_rules: list[ProductionRule],
    demands: dict[ResourceType, float],
    registered_groups: list[ExtractionGroup],
) -> str:
    """Render editable rules separately from the calculated state."""
    active_resources = [state for state in resources.values() if state.enabled]
    groups = list(
        dict.fromkeys(
            [*registered_groups]
            + [state.definition.group for state in active_resources]
        )
    )
    lines = [CONFIG_START, "ГРУППЫ"]
    lines.extend(
        f"Группа {GROUP_NAMES[group]} [{group.value}]" for group in groups
    )
    if not groups:
        lines.append("Группы не зарегистрированы")

    lines.append("РЕСУРСЫ")
    lines.extend(
        _render_resource(state, demands.get(state.resource, 0.0))
        for state in active_resources
    )
    if not active_resources:
        lines.append("Ресурсы не зарегистрированы")

    lines.append("ДОБЫЧА")
    lines.extend(_render_extraction(item) for item in operations)
    if not operations:
        lines.append("Добыча не настроена")

    lines.append("ПРАВИЛА ПРОИЗВОДСТВА")
    lines.extend(_render_production(item) for item in production_rules)
    if not production_rules:
        lines.append("Правила не заданы")
    lines.append(CONFIG_END)
    return "\n".join(lines)


def _parse_resource(
    match: re.Match[str],
) -> tuple[ResourceRegistration, ExtractionGroup]:
    resource = ResourceType(match.group(1))
    values = _options(match.group(2))
    _validate_keys(
        values,
        {"группа", "доступность", "качество", "расход", "склад"},
        f"ресурса {resource.value}",
    )
    group = ExtractionGroup(values.get("группа", ""))
    expected_group = RESOURCE_CATALOG[resource].group
    if group is not expected_group:
        raise ValueError(
            f"Ресурс {resource.value} относится к группе "
            f"{expected_group.value}, а не {group.value}"
        )
    return (
        ResourceRegistration(
            resource=resource,
            accessibility=_float(values.get("доступность", "100")),
            quality=_float(values.get("качество", "100")),
            consumption_per_turn=_float(values.get("расход", "0")),
            storage_capacity=_float(values.get("склад", "0")),
        ),
        group,
    )


def _parse_state_row(
    line: str,
) -> tuple[ResourceType, float, float, float, float]:
    cells = [cell.strip() for cell in line.split("|")]
    if len(cells) != 4:
        raise ValueError(f"Некорректная строка состояния ресурса: {line!r}")
    match = re.search(r"\[([a-z0-9_]+)\]$", cells[0])
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


def _parse_extraction(match: re.Match[str]) -> ExtractionOperation:
    target_id = match.group(1)
    values = _options(match.group(2))
    _validate_keys(
        values,
        {"интенсивность", "приоритет"},
        f"добычи {target_id}",
    )
    return ExtractionOperation(
        target=target_id,
        intensity=_float(values.get("интенсивность", "100")),
        priority=_float(values.get("приоритет", "1")),
    )


def _parse_target(
    value: str,
) -> tuple[ExtractionGroup | None, ResourceType | None]:
    match = _TARGET_RE.match(value)
    if match is None:
        raise ValueError(
            "Цель правила должна иметь вид группа[alias] или ресурс[alias]"
        )
    if match.group(1) == "группа":
        return ExtractionGroup(match.group(2)), None
    return None, ResourceType(match.group(2))


def _parse_production(match: re.Match[str], line: str) -> ProductionRule:
    rule_id = match.group(1)
    name = line.removeprefix("Правило ").split(" [", 1)[0]
    values = _options(match.group(2))
    _validate_keys(
        values,
        {"цель", "статус", "партий", "ходов", "вход", "выход", "побочно"},
        f"правила {rule_id}",
    )
    target_group, target_resource = _parse_target(values.get("цель", ""))
    status = values.get("статус", "активно").strip().lower()
    if status not in {"активно", "завершено"}:
        raise ValueError(f"Неизвестный статус правила {rule_id}: {status!r}")
    try:
        recipe = ProductionRecipeId(rule_id)
    except ValueError:
        recipe = None
    return ProductionRule(
        rule_id=rule_id,
        name=name,
        recipe=recipe,
        target_group=target_group,
        target_resource=target_resource,
        enabled=status == "активно",
        batches=_float(values.get("партий", "0")),
        turns_remaining=_duration(values.get("ходов", "∞")),
        inputs=_resource_map(values.get("вход", "-")),
        outputs=_resource_map(values.get("выход", "-")),
        byproducts=_resource_map(values.get("побочно", "-")),
    )


def parse_industry_configuration(text: str) -> IndustryTextState | None:
    """Parse a configuration block; return ``None`` when it is absent."""
    lines = [line.strip() for line in text.splitlines()]
    starts = [
        index for index, line in enumerate(lines) if line == CONFIG_START
    ]
    ends = [index for index, line in enumerate(lines) if line == CONFIG_END]
    if not starts:
        return None
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("Ожидался ровно один полный блок промышленности")
    start, end = starts[0], ends[0]
    if end <= start:
        raise ValueError("Конец настройки промышленности находится до начала")

    groups: list[ExtractionGroup] = []
    registrations: dict[ResourceType, ResourceRegistration] = {}
    operations: list[ExtractionOperation] = []
    production_rules: list[ProductionRule] = []
    extracted: dict[ResourceType, float] = {}
    shortages: dict[ResourceType, float] = {}
    operation_ids: set[str] = set()
    rule_ids: set[str] = set()
    section = ""
    headings = {
        "ГРУППЫ",
        "РЕСУРСЫ",
        "ДОБЫЧА",
        "ПРАВИЛА ПРОИЗВОДСТВА",
    }
    placeholders = {
        "Группы не зарегистрированы",
        "Ресурсы не зарегистрированы",
        "Нет данных",
        "Добыча не настроена",
        "Правила не заданы",
    }

    for line in lines[start + 1 : end]:
        if line == "СОСТОЯНИЕ РЕСУРСОВ":
            raise ValueError(
                "Состояние ресурсов должно находиться вне блока настроек"
            )
        if line == "РАБОЧАЯ СИЛА" or line.startswith("Рабочая сила | "):
            raise ValueError(
                "Рабочая сила рассчитывается и больше не настраивается"
            )
        if line in headings:
            section = line
            continue
        if not line or line in placeholders:
            continue
        if section == "ГРУППЫ" and (match := _GROUP_RE.match(line)):
            group = ExtractionGroup(match.group(1))
            if group in groups:
                raise ValueError(f"Группа {group.value} указана дважды")
            groups.append(group)
        elif section == "РЕСУРСЫ" and (match := _RESOURCE_RE.match(line)):
            registration, group = _parse_resource(match)
            if registration.resource in registrations:
                raise ValueError(
                    f"Ресурс {registration.resource.value} указан дважды"
                )
            if group not in groups:
                raise ValueError(
                    f"Для ресурса {registration.resource.value} не "
                    f"зарегистрирована группа {group.value}"
                )
            registrations[registration.resource] = registration
        elif section == "ДОБЫЧА" and (match := _EXTRACTION_RE.match(line)):
            operation = _parse_extraction(match)
            if operation.target_key in operation_ids:
                raise ValueError(
                    f"Добыча {operation.target_key} указана дважды"
                )
            operation_ids.add(operation.target_key)
            operations.append(operation)
        elif section == "ПРАВИЛА ПРОИЗВОДСТВА" and (
            match := _PRODUCTION_RE.match(line)
        ):
            rule = _parse_production(match, line)
            if rule.rule_id in rule_ids:
                raise ValueError(f"Правило {rule.rule_id} указано дважды")
            rule_ids.add(rule.rule_id or "")
            production_rules.append(rule)
        else:
            raise ValueError(
                f"Неизвестная строка настройки промышленности: {line!r}"
            )

    state_sections = [
        index
        for index, line in enumerate(lines)
        if line == "СОСТОЯНИЕ РЕСУРСОВ"
    ]
    if len(state_sections) > 1:
        raise ValueError("Ожидалось не более одного состояния ресурсов")
    for index in state_sections:
        for state_line in lines[index + 1 :]:
            compact = state_line.replace("|", "").replace(" ", "")
            if (
                not state_line
                or state_line.startswith("Ресурс")
                or (compact and set(compact) == {"-"})
            ):
                continue
            if "|" not in state_line or not re.search(
                r"\[[a-z0-9_]+\]", state_line
            ):
                break
            resource, stockpile, shown_storage, mined, shortage = (
                _parse_state_row(state_line)
            )
            if resource not in registrations:
                raise ValueError(
                    "Есть состояние незарегистрированного ресурса "
                    f"{resource.value}"
                )
            registration = registrations[resource]
            if registration.storage_capacity == 0:
                registration.storage_capacity = shown_storage
            registration.stockpile = stockpile
            extracted[resource] = mined
            shortages[resource] = shortage
    demands = {
        registration.resource: registration.consumption_per_turn
        for registration in registrations.values()
        if registration.consumption_per_turn > 0
    }
    return IndustryTextState(
        groups=groups,
        registrations=list(registrations.values()),
        operations=operations,
        production_rules=production_rules,
        demands=demands,
        extracted=extracted,
        shortages=shortages,
    )
