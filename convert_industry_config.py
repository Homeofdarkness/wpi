"""Convert a country-creator file from marked YAML v2 to TOML v3."""

from __future__ import annotations

import argparse
from pathlib import Path

from create_basic_country import create_basic_country
from stats.industry_components import ResourceState
from stats.industry_text import (
    CONFIG_END,
    CONFIG_START,
    parse_industry_configuration,
    render_industry_configuration,
)


def convert_creator_file(source: Path, destination: Path) -> Path:
    """Replace the legacy marked YAML block while preserving all other text."""
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == CONFIG_START
    ]
    ends = [
        index for index, line in enumerate(lines) if line.strip() == CONFIG_END
    ]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise ValueError(
            "Ожидался один старый YAML-блок между строками "
            f"{CONFIG_START!r} и {CONFIG_END!r}"
        )

    country = create_basic_country(source)
    toml_lines = country.industry.render_configuration().splitlines()
    converted = lines[: starts[0]] + toml_lines + lines[ends[0] + 1 :]
    converted = [
        (
            "# TOML-КОНФИГУРАЦИЯ ПРОМЫШЛЕННОСТИ"
            if line.strip() == "# YAML-КОНФИГУРАЦИЯ ПРОМЫШЛЕННОСТИ"
            else line
        )
        for line in converted
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(converted) + "\n", encoding="utf-8")
    create_basic_country(destination)
    return destination


def convert_settings_file(source: Path, destination: Path) -> Path:
    """Convert a standalone marked YAML settings file to marker-free TOML."""
    source_text = source.read_text(encoding="utf-8")
    parsed = parse_industry_configuration(source_text)
    if parsed is None:
        raise ValueError("В файле не найдена конфигурация промышленности")
    resources = {
        item.resource: ResourceState(
            resource=item.resource,
            name=item.name,
            group=item.group,
            enabled=True,
            stockpile=item.stockpile,
            storage_capacity=item.storage_capacity,
            accessibility=item.accessibility,
            quality=item.quality,
        )
        for item in parsed.registrations
    }
    converted = render_industry_configuration(
        resources=resources,
        operations=parsed.operations,
        production_rules=parsed.production_rules,
        effects=parsed.effects,
        demands=parsed.demands,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = source_text.splitlines()
    ends = [
        index for index, line in enumerate(lines) if line.strip() == CONFIG_END
    ]
    trailing_state = lines[ends[0] + 1 :] if len(ends) == 1 else []
    output_lines = converted.splitlines()
    if trailing_state:
        output_lines.extend(("", *trailing_state))
    output = "\n".join(output_lines).rstrip() + "\n"
    destination.write_text(output, encoding="utf-8")
    parse_industry_configuration(output)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Перенос YAML v2 промышленности в TOML v3 без маркеров."
    )
    parser.add_argument("source", type=Path, help="Старый input-файл")
    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        help="Новый файл; по умолчанию <source>_toml.txt",
    )
    parser.add_argument(
        "--settings-only",
        action="store_true",
        help="Исходник является отдельным YAML-файлом настроек",
    )
    args = parser.parse_args()
    destination = args.destination or args.source.with_name(
        f"{args.source.stem}_toml{args.source.suffix}"
    )
    converter = (
        convert_settings_file if args.settings_only else convert_creator_file
    )
    result = converter(args.source, destination)
    print(f"TOML-конфигурация сохранена: {result}")


if __name__ == "__main__":
    main()
