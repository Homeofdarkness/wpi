from enum import IntEnum
from typing import Optional

from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from utils.logger_manager import get_logger


logger = get_logger("Run Start Skip Move")


class MODES(IntEnum):
    MODE_CREATOR = 1
    MODE_SKIPPER = 2
    MODE_RECOVERY_BLOCK = 3

class StartSkipMove:
    mode: Optional[MODES] = None

    @classmethod
    def set_mode(cls, mode: MODES):
        mode = MODES(int(input("Введите режим работы программы - ")))
        cls.mode = mode

    @classmethod
    def parse_user_input(cls):
        match cls.mode:
            case MODES.MODE_CREATOR:
                return cls._parse_creator_mode_input()
            case MODES.MODE_SKIPPER:
                return cls._parse_skipper_mode_input()
            case MODES.MODE_RECOVERY_BLOCK:
                return cls._parse_recovery_block_mode_input()
            case _:
                raise ValueError("Чет ты ввел не то окуняра")

    @classmethod
    def _parse_creator_mode_input(cls):
        Economy = EconomyStats.from_user_input("=== ВВОД ДАННЫХ ЭКОНОМИКИ ===")
        Industry = IndustrialStats.from_user_input("=== ВВОД ДАННЫХ ПРОМЫШЛЕННОСТИ ===")
        Agriculture = AgricultureStats.from_user_input("=== ВВОД ДАННЫХ СЕЛЬСКОГО ХОЗЯЙСТВА ===")
        InnerPolitics = InnerPoliticsStats.from_user_input("=== ВВОД ДАННЫХ ВНУТРЕННЕЙ ПОЛИТИКИ ===")

        return Economy, Industry, Agriculture, InnerPolitics

    @classmethod
    def _parse_skipper_mode_input(cls):
        pass

    @classmethod
    def _parse_recovery_block_mode_input(cls):
        pass