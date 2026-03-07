from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional


RenderFunc = Callable[[Any, bool], str]
GetterFunc = Callable[[Any], Any]
ParserFunc = Callable[[str], Any]


@dataclass(frozen=True)
class PrettyFieldSpec:
    key: str
    label: str
    field_name: str | None = None
    index: int | None = None
    decimals: int | None = None
    suffix: str = ""
    default: Any = 0
    aliases: tuple[str, ...] = ()
    parse_kind: str = "number"
    read_only: bool = False
    getter: GetterFunc | None = None
    formatter: RenderFunc | None = None
    parser: ParserFunc | None = None

    def all_labels(self) -> tuple[str, ...]:
        return (self.label, *self.aliases)


@dataclass(frozen=True)
class PrettyLineSpec:
    fields: tuple[str, ...] = ()
    title: str | None = None

    # пустые строки вокруг линии/секции
    gap_before: int = 0
    gap_after: int = 0

    # переопределение spacing конкретно для этой строки
    line_width: int | None = None
    min_gap: int | None = None


@dataclass(frozen=True)
class PrettyLayoutSpec:
    fields: dict[str, PrettyFieldSpec]
    lines: tuple[PrettyLineSpec, ...]
    line_width: int = 112
    min_gap: int = 6
    code_block: bool = True


def field(
        key: str,
        label: str,
        *,
        field_name: str | None = None,
        decimals: int | None = None,
        suffix: str = "",
        default: Any = 0,
        aliases: Iterable[str] = (),
        read_only: bool = False,
        getter: GetterFunc | None = None,
        formatter: RenderFunc | None = None,
        parser: ParserFunc | None = None,
        parse_kind: str = "number",
) -> PrettyFieldSpec:
    target_field_name = field_name if field_name is not None else (
        None if read_only else key)
    return PrettyFieldSpec(
        key=key,
        field_name=target_field_name,
        label=label,
        decimals=decimals,
        suffix=suffix,
        default=default,
        aliases=tuple(aliases),
        read_only=read_only,
        getter=getter,
        formatter=formatter,
        parser=parser,
        parse_kind="skip" if read_only else parse_kind,
    )


def list_item(
        key: str,
        label: str,
        index: int,
        *,
        decimals: int | None = 1,
        suffix: str = "",
        default: Any = 0.0,
        aliases: Iterable[str] = (),
        read_only: bool = False,
        getter: GetterFunc | None = None,
        formatter: RenderFunc | None = None,
        parser: ParserFunc | None = None,
        parse_kind: str = "number",
) -> PrettyFieldSpec:
    return PrettyFieldSpec(
        key=f"{key}[{index}]",
        field_name=None if read_only else key,
        index=index,
        label=label,
        decimals=decimals,
        suffix=suffix,
        default=default,
        aliases=tuple(aliases),
        read_only=read_only,
        getter=getter,
        formatter=formatter,
        parser=parser,
        parse_kind="skip" if read_only else parse_kind,
    )


def budget_pair(value: Any, _: bool) -> str:
    if not isinstance(value, tuple) or len(value) != 2:
        value = (0.0, 0.0)
    current_budget, prev_budget = value
    current_budget = _coerce_number(current_budget, 0.0)
    prev_budget = _coerce_number(prev_budget, current_budget)
    delta = current_budget - prev_budget
    return f"{_format_number(delta, 1)} ({_format_number(current_budget, 1)})"


def food_security(value: Any, debug: bool) -> str:
    if not isinstance(value, tuple) or len(value) != 2:
        value = (0.0, False)
    raw_value, is_negative = value
    text = _format_number(_coerce_number(raw_value, 0.0), 3)
    if not debug and is_negative:
        return f"!{text}%"
    return f"{text}%"


def identity(value: Any, _: bool) -> str:
    return str(value)


def parse_budget_pair(text: str) -> tuple[float, float]:
    numbers = parse_numbers(text)
    if len(numbers) >= 2:
        delta, current = numbers[0], numbers[1]
        prev = current - delta
        return current, prev
    current = numbers[0] if numbers else 0.0
    return current, current


def parse_numbers(text: str) -> list[float]:
    values: list[float] = []
    token: list[str] = []

    def flush() -> None:
        if not token:
            return
        raw = "".join(token).strip()
        token.clear()
        normalized = _normalize_number_token(raw)
        if not normalized or normalized in {"+", "-", ".", "+.", "-."}:
            return
        try:
            values.append(float(normalized))
        except ValueError:
            return

    allowed = set("+-0123456789.")
    for char in text:
        if char in allowed:
            token.append(char)
        else:
            flush()
    flush()
    return values


def parse_first_number(text: str, default: float = 0.0) -> float:
    numbers = parse_numbers(text)
    return numbers[0] if numbers else default


def _normalize_number_token(token: str) -> str:
    sign_part = []
    rest_start = 0
    while rest_start < len(token) and token[rest_start] in "+-":
        sign_part.append(token[rest_start])
        rest_start += 1
    rest = token[rest_start:]
    if not rest:
        return ""
    minus_count = sign_part.count("-")
    sign = "-" if minus_count % 2 else ""
    return f"{sign}{rest}"


def _coerce_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value: Any, decimals: int | None) -> str:
    number = _coerce_number(value, 0.0)
    if decimals is None:
        return str(number)
    if decimals == 0:
        return str(int(round(number)))
    return f"{number:.{decimals}f}"


def _default_value_for_spec(spec: PrettyFieldSpec) -> Any:
    return spec.default


def _resolve_value(model: Any, spec: PrettyFieldSpec) -> Any:
    if spec.getter is not None:
        return spec.getter(model)

    target_name = spec.field_name or spec.key
    raw = getattr(model, target_name, None)
    if spec.index is not None:
        if not isinstance(raw, (list, tuple)) or len(raw) <= spec.index:
            return _default_value_for_spec(spec)
        raw = raw[spec.index]
    if raw is None:
        return _default_value_for_spec(spec)
    return raw


def _render_value(spec: PrettyFieldSpec, value: Any, debug: bool) -> str:
    if spec.formatter is not None:
        return spec.formatter(value, debug)

    text = _format_number(value, spec.decimals)
    if spec.suffix:
        text = f"{text}{spec.suffix}"
    return text


def render_pretty(model: Any, layout: PrettyLayoutSpec, *,
                  debug: bool = False) -> str:
    lines: list[str] = []

    for line_spec in layout.lines:
        _append_blank_lines(lines, line_spec.gap_before)

        if line_spec.title is not None:
            lines.append(line_spec.title)
            _append_blank_lines(lines, line_spec.gap_after)
            continue

        if not line_spec.fields:
            lines.append("")
            _append_blank_lines(lines, line_spec.gap_after)
            continue

        texts: list[str] = []
        for field_key in line_spec.fields:
            spec = layout.fields[field_key]
            value = _resolve_value(model, spec)
            texts.append(f"{spec.label} - {_render_value(spec, value, debug)}")

        row_line_width = line_spec.line_width or layout.line_width
        row_min_gap = line_spec.min_gap or layout.min_gap
        lines.append(_render_row(texts, row_line_width, row_min_gap))

        _append_blank_lines(lines, line_spec.gap_after)

    while lines and lines[-1] == "":
        lines.pop()

    body = "\n".join(lines)
    if layout.code_block:
        return f"```\n{body}\n```"
    return body


def _append_blank_lines(lines: list[str], count: int) -> None:
    for _ in range(max(count, 0)):
        if not lines or lines[-1] != "":
            lines.append("")
        else:
            lines.append("")


def _render_row(texts: list[str], line_width: int, min_gap: int) -> str:
    if len(texts) == 1:
        return texts[0]

    total_width = sum(len(text) for text in texts)
    gap_count = len(texts) - 1
    free_space = max(line_width - total_width, min_gap * gap_count)

    base_gap = free_space // gap_count
    extra = free_space % gap_count

    parts: list[str] = []
    for idx, text in enumerate(texts):
        parts.append(text)
        if idx < gap_count:
            gap = base_gap + (1 if idx < extra else 0)
            parts.append(" " * gap)

    return "".join(parts).rstrip()


def parse_pretty_text(
        text: str,
        layout: PrettyLayoutSpec,
        model_fields: Dict[str, Any],
        defaults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = (defaults or {}).copy()

    list_lengths: Dict[str, int] = {}
    for spec in layout.fields.values():
        if spec.read_only or spec.parse_kind == "skip" or spec.field_name is None:
            continue
        if spec.index is not None:
            list_lengths[spec.field_name] = max(
                list_lengths.get(spec.field_name, 0), spec.index + 1
            )
    for field_name, length in list_lengths.items():
        existing = result.get(field_name)
        if not isinstance(existing, list) or len(existing) < length:
            result[field_name] = [0.0] * length

    parse_specs = [
        spec for spec in layout.fields.values()
        if
        not spec.read_only and spec.parse_kind != "skip" and spec.field_name is not None
    ]

    for line in _normalize_lines(text):
        matches = _find_matches_in_line(line, parse_specs)
        if not matches:
            continue

        for idx, match in enumerate(matches):
            start = match[1]
            end = matches[idx + 1][0] if idx + 1 < len(matches) else len(line)
            value_text = line[start:end].strip()
            spec = match[2]
            _assign_parsed_value(result, spec, value_text, model_fields)

    return result


def _normalize_lines(text: str) -> list[str]:
    cleaned = text.replace("\r", "").replace("\xa0", " ").replace("\t", " ")
    lines: list[str] = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.strip()
        if not line or line == "```":
            continue
        lines.append(line)
    return lines


def _find_matches_in_line(
        line: str,
        specs: list[PrettyFieldSpec]
) -> list[tuple[int, int, PrettyFieldSpec]]:
    candidates: list[tuple[int, int, PrettyFieldSpec]] = []
    for spec in specs:
        best: tuple[int, int] | None = None
        for label in spec.all_labels():
            for token in _token_variants(label):
                pos = line.find(token)
                if pos == -1:
                    continue
                end = pos + len(token)
                if best is None or pos < best[0] or (
                        pos == best[0] and end > best[1]):
                    best = (pos, end)
        if best is not None:
            candidates.append((best[0], best[1], spec))

    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    resolved: list[tuple[int, int, PrettyFieldSpec]] = []
    for candidate in candidates:
        if resolved and candidate[0] < resolved[-1][1]:
            continue
        resolved.append(candidate)
    return resolved


def _token_variants(label: str) -> tuple[str, ...]:
    return (
        f"{label} - ",
        f"{label}-",
        f"{label} -",
    )


def _assign_parsed_value(result: Dict[str, Any], spec: PrettyFieldSpec,
                         value_text: str,
                         model_fields: Dict[str, Any]) -> None:
    if spec.parser is not None:
        parsed_value = spec.parser(value_text)
    elif spec.parse_kind == "budget":
        parsed_value = parse_budget_pair(value_text)
    else:
        parsed_value = parse_first_number(value_text,
                                          _coerce_number(spec.default, 0.0))

    if spec.parse_kind == "budget":
        current_budget, prev_budget = parsed_value
        result["current_budget"] = current_budget
        result["prev_budget"] = prev_budget
        return

    if spec.index is not None:
        target_list = result.setdefault(spec.field_name, [])
        while len(target_list) <= spec.index:
            target_list.append(0.0)
        target_list[spec.index] = _cast_value(spec.field_name, parsed_value,
                                              model_fields)
        return

    result[spec.field_name] = _cast_value(spec.field_name, parsed_value,
                                          model_fields)


def _cast_value(field_name: str, value: Any,
                model_fields: Dict[str, Any]) -> Any:
    field_info = model_fields.get(field_name)
    if field_info is None:
        return value
    annotation = field_info.annotation
    if annotation == int:
        return int(round(_coerce_number(value, 0.0)))
    if annotation == float:
        return float(_coerce_number(value, 0.0))
    return value
