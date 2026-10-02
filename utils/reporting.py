"""Small Unicode renderers shared by human-readable turn reports."""

from __future__ import annotations

from collections.abc import Sequence


def boxed_table(
    title: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> str:
    """Render a compact multi-column table using the report ``╫`` motif."""
    normalized_headers = tuple(str(value) for value in headers)
    normalized_rows = [tuple(str(value) for value in row) for row in rows]
    if any(len(row) != len(normalized_headers) for row in normalized_rows):
        raise ValueError("Строки отчёта должны совпадать с числом колонок")
    widths = [
        max(
            [
                len(normalized_headers[index]),
                *(len(row[index]) for row in normalized_rows),
            ]
        )
        for index in range(len(normalized_headers))
    ]
    content_width = sum(widths) + 3 * (len(widths) - 1)
    if len(title) > content_width:
        widths[0] += len(title) - content_width

    def row_line(values: Sequence[str]) -> str:
        cells = [
            str(value).ljust(widths[index])
            for index, value in enumerate(values)
        ]
        return "╫ " + " ╫ ".join(cells) + " ╫"

    header_line = row_line(normalized_headers)
    full_border = f"╫{'═' * (len(header_line) - 2)}╫"
    column_border = "╫" + "╫".join("═" * (width + 2) for width in widths) + "╫"
    header_border = "╫" + "╫".join("─" * (width + 2) for width in widths) + "╫"
    content_width = len(header_line) - 4
    result = [
        full_border,
        f"╫ {title.center(content_width)} ╫",
        column_border,
        header_line,
        header_border,
    ]
    result.extend(row_line(row) for row in normalized_rows)
    result.append(full_border)
    return "\n".join(result)


def boxed_sections(
    title: str,
    sections: Sequence[tuple[str, Sequence[tuple[str, str]]]],
) -> str:
    """Render titled two-column sections with stable Unicode borders."""
    all_rows = [row for _, rows in sections for row in rows]
    if not all_rows:
        all_rows = [("Состояние", "Нет данных")]
    label_width = max(len(label) for label, _ in all_rows)
    value_width = max(len(value) for _, value in all_rows)
    content_width = label_width + value_width + 3
    if len(title) > content_width:
        label_width += len(title) - content_width
        content_width = len(title)
    border = f"╫{'═' * (label_width + 2)}╫{'═' * (value_width + 2)}╫"
    result = [border, f"╫ {title.center(content_width)} ╫", border]
    for index, (section_name, rows) in enumerate(sections):
        if section_name:
            result.append(f"╫ {section_name.center(content_width, '─')} ╫")
        result.extend(
            f"╫ {label:<{label_width}} ╫ {value:>{value_width}} ╫"
            for label, value in rows
        )
        if index < len(sections) - 1:
            result.append(border)
    result.append(border)
    return "\n".join(result)
