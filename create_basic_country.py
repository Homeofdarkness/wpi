from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from modules.mode_spec import GameMode, get_mode
from modules.run_start_skip import InputMode, StatsInput
from modules.skip_move_types import WorldState
from stats.industry_text import CONFIG_END, CONFIG_START


RESOURCE_STATE_START = "СОСТОЯНИЕ РЕСУРСОВ"


def read_source(path: Path) -> tuple[list[str], str | None]:
    """Read creator answers and an optional readable industry block."""
    answers: list[str] = []
    configuration: list[str] = []
    inside_configuration = False
    configuration_found = False
    state_found = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == CONFIG_START:
            if configuration_found:
                raise ValueError("Найдено несколько настроек промышленности")
            configuration_found = True
            inside_configuration = True
            configuration.append(line)
            continue
        if inside_configuration:
            configuration.append(line)
            if line == CONFIG_END:
                inside_configuration = False
            continue
        if line == RESOURCE_STATE_START:
            if state_found:
                raise ValueError("Найдено несколько состояний ресурсов")
            state_found = True
            configuration.append(line)
            continue
        if state_found:
            configuration.append(line)
            continue
        answers.append(line)

    if inside_configuration:
        raise ValueError(f"После {CONFIG_START!r} отсутствует {CONFIG_END!r}")
    config_text = "\n".join(configuration) if configuration else None
    return answers, config_text


def create_basic_country(input_path: Path) -> WorldState:
    raw_answers, industry_configuration = read_source(input_path)
    answers = iter(raw_answers)
    last_prompt = "неизвестное поле"

    def file_input(prompt: str = "") -> str:
        nonlocal last_prompt
        last_prompt = prompt.strip() or last_prompt
        try:
            return next(answers)
        except StopIteration as error:
            raise RuntimeError(
                f"В {input_path} закончились данные.\n"
                f"Следующее ожидаемое поле: {last_prompt}"
            ) from error

    creator = StatsInput(
        config=get_mode(GameMode.BASIC).stats_config,
        mode=InputMode.COUNTRY_CREATOR,
        industry_configuration=industry_configuration,
    )
    with patch("builtins.input", side_effect=file_input):
        country = creator.read()

    extra_answer = next(answers, None)
    if extra_answer is not None:
        raise RuntimeError(
            "Страна создана, но во входном файле остались лишние данные. "
            f"Первое лишнее значение: {extra_answer!r}"
        )

    return country


def render_country(country: WorldState) -> str:
    sections = (
        country.economy,
        country.industry,
        country.agriculture,
        country.inner_politics,
        country.probabilities,
    )
    return "Стата -\n" + "\n".join(str(section) for section in sections) + "\n"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Создание страны базового режима из файла."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=base_dir / "test_files" / "edem_country_input.txt",
        help="Файл с ответами country_creator",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=base_dir / "test_files" / "edem_country_output.txt",
        help="Куда записать созданную страну",
    )
    parser.add_argument(
        "--industry-settings-output",
        type=Path,
        help=(
            "Куда записать отдельные настройки промышленности. "
            "По умолчанию — рядом с основной статой."
        ),
    )
    args = parser.parse_args()

    country = create_basic_country(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_country(country), encoding="utf-8")
    settings_output = args.industry_settings_output or args.output.with_name(
        f"{args.output.stem}_industry_settings.txt"
    )
    settings_output.parent.mkdir(parents=True, exist_ok=True)
    settings_output.write_text(
        f"{country.industry.render_configuration()}\n",
        encoding="utf-8",
    )
    print(f"Страна базового режима создана: {args.output}")
    print(f"Настройки промышленности: {settings_output}")


if __name__ == "__main__":
    main()
