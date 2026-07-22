"""Console input workflows for constructing a world state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from modules.skip_move_types import WorldState
from stats.industry_text import CONFIG_END, CONFIG_START
from stats.stats_base import StatsBase
from utils.input_parsers import InputParser


class InputMode(StrEnum):
    COUNTRY_CREATOR = "country_creator"
    MOVES_SKIPPER = "moves_skipper"


@dataclass(frozen=True)
class StatsConfig:
    economy_class: type[StatsBase]
    industry_class: type[StatsBase]
    agriculture_class: type[StatsBase]
    inner_politics_class: type[StatsBase]


SKIPPER_SECTIONS = {
    "economy": "=== ЭКОНОМИКА И ТОРГОВЛЯ ===",
    "industry": "=== ПРОМЫШЛЕННОСТЬ ===",
    "industry_configuration": "=== НАСТРОЙКИ ПРОМЫШЛЕННОСТИ ===",
    "agriculture": "=== СЕЛЬСКОЕ ХОЗЯЙСТВО ===",
    "government": "=== ГОСУДАРСТВО, КОНТРОЛЬ И НАРОД ===",
}

CREATOR_HEADERS = {
    "economy": "=== ВВОД ДАННЫХ ЭКОНОМИКИ ===",
    "industry": "=== ВВОД ДАННЫХ ПРОМЫШЛЕННОСТИ ===",
    "agriculture": "=== ВВОД ДАННЫХ СЕЛЬСКОГО ХОЗЯЙСТВА ===",
    "inner_politics": "=== ВВОД ДАННЫХ ВНУТРЕННЕЙ ПОЛИТИКИ ===",
}

_INDUSTRY_CONFIGURATION_UNSET = object()


def _skipper_section_is_complete(section: str, text: str) -> bool:
    """Recognize the last meaningful part of an unfenced current block."""
    if section == "economy":
        return "ТОРГОВЛЯ" in text and any(
            "Филиалы -" in line and "Доход -" in line
            for line in text.splitlines()
        )
    if section == "industry":
        _, marker, resource_state = text.partition("СОСТОЯНИЕ РЕСУРСОВ")
        if not marker:
            return False
        return "Нет данных" in resource_state or any(
            "|" in line and "[" in line and "]" in line
            for line in resource_state.splitlines()
        )
    if section == "agriculture":
        return "Запасы пищи -" in text
    if section == "government":
        return "НАРОД" in text and "Отхождение от истин" in text
    return False


def select_input_mode() -> InputMode:
    modes = list(InputMode)
    print("Доступные способы ввода:")
    for number, mode in enumerate(modes, 1):
        print(f"{number}. {mode.value}")
    while True:
        choice = input("Выберите способ ввода (название или номер): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(modes):
                return modes[index]
        else:
            try:
                return InputMode(choice.lower())
            except ValueError:
                pass
        print("Неизвестный способ ввода. Попробуйте снова.")


def read_text_section(
    title: str,
    *,
    terminator: str | None = None,
    completion_check: Callable[[str], bool] | None = None,
) -> str:
    """Read one legacy section or one complete fenced pretty block.

    A Markdown fence switches the reader to fence-aware mode.  For unfenced
    current output, a blank line terminates only a complete section; internal
    blanks are preserved.  Two consecutive blanks remain a fallback for old
    incomplete formats.  Configuration may provide an explicit terminator.
    """
    print(title)
    lines: list[str] = []
    inside_fence = False
    while True:
        line = input()
        stripped = line.strip()

        if stripped.startswith("```"):
            lines.append(line)
            if inside_fence:
                return "\n".join(lines)
            inside_fence = True
            continue

        if (
            terminator is not None
            and stripped == terminator
            and not inside_fence
        ):
            lines.append(line)
            return "\n".join(lines)
        if not stripped and not inside_fence:
            if not lines:
                return ""
            if terminator is not None:
                lines.append("")
                continue
            current = "\n".join(lines).rstrip()
            if completion_check is None or completion_check(current):
                return current
            if lines[-1] == "":
                return current
            lines.append("")
            continue

        lines.append(line)


@dataclass
class StatsInput:
    config: StatsConfig
    mode: InputMode | None = None
    industry_configuration: str | None | object = _INDUSTRY_CONFIGURATION_UNSET

    def read(self) -> WorldState:
        mode = self.mode or select_input_mode()
        if mode is InputMode.COUNTRY_CREATOR:
            return self._read_creator()
        return self._read_skipper()

    # Compatibility with the previous public entry point.
    def parse_user_input_data(self) -> WorldState:
        return self.read()

    def _read_creator(self) -> WorldState:
        economy = self.config.economy_class.from_user_input(
            CREATOR_HEADERS["economy"]
        )
        industry = self.config.industry_class.from_user_input(
            CREATOR_HEADERS["industry"]
        )
        configuration = self.industry_configuration
        if configuration is _INDUSTRY_CONFIGURATION_UNSET:
            configuration = self._read_creator_industry_configuration()
        if configuration:
            industry = self.config.industry_class.from_stats_text(
                f"{industry.render_pretty()}\n"
                f"{self._normalize_industry_configuration(configuration)}"
            )
        return WorldState(
            economy=economy,
            industry=industry,
            agriculture=self.config.agriculture_class.from_user_input(
                CREATOR_HEADERS["agriculture"]
            ),
            inner_politics=self.config.inner_politics_class.from_user_input(
                CREATOR_HEADERS["inner_politics"]
            ),
        )

    @staticmethod
    def _normalize_industry_configuration(configuration: str) -> str:
        text = "\n".join(
            line.strip()
            for line in configuration.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if not text:
            return ""
        if CONFIG_START not in text:
            text = f"{CONFIG_START}\n{text}"
        if CONFIG_END not in text:
            text = f"{text}\n{CONFIG_END}"
        return text

    @staticmethod
    def _read_creator_industry_configuration() -> str | None:
        print("=== РЕСУРСЫ И ДОБЫЧА ===")
        print(
            "Вставьте промышленный блок из input-файла. "
            "Пустая первая строка оставит промышленность без ресурсов."
        )
        configuration = InputParser.parse_data_from_str().strip()
        return configuration or None

    def _read_skipper(self) -> WorldState:
        print(
            "Блок можно вставлять с рамкой ```...``` или без неё. "
            "Внутренние пустые строки сохраняются; после последней "
            "строки блока нажмите Enter."
        )
        sections = {}
        for name, title in SKIPPER_SECTIONS.items():
            terminator = (
                CONFIG_END if name == "industry_configuration" else None
            )
            sections[name] = read_text_section(
                title,
                terminator=terminator,
                completion_check=(
                    None
                    if name == "industry_configuration"
                    else lambda text, section=name: (
                        _skipper_section_is_complete(section, text)
                    )
                ),
            )
        industry_configuration = sections["industry_configuration"].strip()
        if not industry_configuration:
            raise ValueError(
                "Не вставлены отдельные настройки промышленности. "
                "Используйте файл *_industry_settings.txt"
            )
        return WorldState(
            economy=self.config.economy_class.from_stats_text(
                sections["economy"]
            ),
            industry=self.config.industry_class.from_stats_text(
                f"{sections['industry']}\n"
                f"{self._normalize_industry_configuration(industry_configuration)}"
            ),
            agriculture=self.config.agriculture_class.from_stats_text(
                sections["agriculture"]
            ),
            inner_politics=self.config.inner_politics_class.from_stats_text(
                sections["government"]
            ),
        )


def make_start_skip_move(config: StatsConfig) -> StatsInput:
    return StatsInput(config=config)
