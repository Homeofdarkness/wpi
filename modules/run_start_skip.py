from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from stats.basic_stats import EconomyStats, IndustrialStats, \
    AgricultureStats, InnerPoliticsStats
from utils.input_parsers import InputParser
from utils.logger_manager import get_logger


logger = get_logger("Run Start Skip Move")


class MODES(StrEnum):
    MODE_CREATOR = 'country_creator'
    MODE_SKIPPER = 'moves_skipper'


class StartSkipMoveBase:
    pass


@dataclass
class BasicStartSkipMove(StartSkipMoveBase):
    mode: Optional[MODES] = None

    @staticmethod
    def set_mode():
        print("Доступные режимы:")
        for i, mode in enumerate(MODES, 1):
            print(f"{i}. {mode.value}")

        while True:
            choice = input(
                "Выберите режим (введите название или номер): ").strip()

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(MODES):
                    return list(MODES)[index]
                else:
                    print(f"Номер должен быть от 1 до {len(MODES)}")
                    continue

            try:
                return MODES(choice.lower())
            except ValueError:
                print(f"Неверный ввод '{choice}'. Попробуйте снова.")

    def parse_user_input_data(self):
        self.mode = self.set_mode()
        match self.mode:
            case MODES.MODE_CREATOR:
                return self._parse_creator_mode_input()
            case MODES.MODE_SKIPPER:
                return self._parse_skipper_mode_input()
            case _:
                raise ValueError("Чет ты ввел не то окуняра")

    @classmethod
    def _parse_creator_mode_input(cls):
        Economy = EconomyStats.from_user_input("=== ВВОД ДАННЫХ ЭКОНОМИКИ ===")
        Industry = IndustrialStats.from_user_input(
            "=== ВВОД ДАННЫХ ПРОМЫШЛЕННОСТИ ===")
        Agriculture = AgricultureStats.from_user_input(
            "=== ВВОД ДАННЫХ СЕЛЬСКОГО ХОЗЯЙСТВА ===")
        InnerPolitics = InnerPoliticsStats.from_user_input(
            "=== ВВОД ДАННЫХ ВНУТРЕННЕЙ ПОЛИТИКИ ===")

        return {
            "Economy": Economy,
            "Industry": Industry,
            "Agriculture": Agriculture,
            "InnerPolitics": InnerPolitics
        }

    @classmethod
    def _parse_skipper_mode_input(cls):
        print("=== ЭКОНОМИКА ===")
        economy_data = InputParser.parse_data_from_str()
        print("=== ТОРГОВЛЯ ===")
        trade_data = InputParser.parse_data_from_str()
        Economy = EconomyStats.from_stats_text(
            economy_data + '\n' + trade_data)

        print("=== ПРОМЫШЛЕННОСТЬ ===")
        industry_data = InputParser.parse_data_from_str()
        Industry = IndustrialStats.from_stats_text(industry_data)

        print("=== СЕЛЬСКОЕ ХОЗЯЙСТВО ===")
        agriculture_data = InputParser.parse_data_from_str()
        Agriculture = AgricultureStats.from_stats_text(agriculture_data)

        print("=== ГОСУДАРСТВО ===")
        government_data = InputParser.parse_data_from_str()
        print("=== НАРОД ===")
        people_data = InputParser.parse_data_from_str()
        InnerPolitics = InnerPoliticsStats.from_stats_text(
            government_data + '\n' + people_data)

        return {
            "Economy": Economy,
            "Industry": Industry,
            "Agriculture": Agriculture,
            "InnerPolitics": InnerPolitics
        }
