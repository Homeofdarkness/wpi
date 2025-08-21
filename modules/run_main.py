from enum import StrEnum
from typing import Optional

from modules.run_finalize import BasicFinalizer
from modules.run_skip_move import BasicSkipMove
from modules.run_start_skip import BasicStartSkipMove
from utils.logger_manager import get_logger


logger = get_logger("Run Main")


class RunningMode(StrEnum):
    MODE_BASIC = "basic"
    MODE_ATTERIUM = "atterium"
    MODE_TROY = "troy"
    MODE_RECOVERY_BLOCK = "recovery-block"


class RunMain:

    def __init__(self, mode: Optional[RunningMode] = None):
        self.mode = mode

    def set_running_mode(self, running_mode: Optional[RunningMode] = None):
        if running_mode is None:
            running_mode = self._parse_mode_from_input()
        self.mode = running_mode

    @staticmethod
    def _parse_mode_from_input():
        print("Доступные режимы:")
        for i, mode in enumerate(RunningMode, 1):
            print(f"{i}. {mode.value}")

        while True:
            choice = input(
                "Выберите режим (введите название или номер): ").strip()

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(RunningMode):
                    return list(RunningMode)[index]
                else:
                    print(f"Номер должен быть от 1 до {len(RunningMode)}")
                    continue

            try:
                return RunningMode(choice.lower())
            except ValueError:
                print(f"Неверный ввод '{choice}'. Попробуйте снова.")

    def run(self):
        match self.mode:
            case RunningMode.MODE_BASIC:
                start_skip_cls = BasicStartSkipMove
                skip_move_cls = BasicSkipMove
                finalize_cls = BasicFinalizer
            case RunningMode.MODE_ATTERIUM:
                pass

            case _:
                print(self.mode)
                print("В разработке")
                return None

        start_skip = start_skip_cls()
        stats = start_skip.parse_user_input_data()

        skip_move = skip_move_cls(
            Economy=stats["Economy"],
            Industry=stats["Industry"],
            Agriculture=stats["Agriculture"],
            InnerPolitics=stats["InnerPolitics"]
        )
        skip_move.skip_move()

        finalizer = finalize_cls(
            skip_move.Economy,
            skip_move.Industry,
            skip_move.Agriculture,
            skip_move.InnerPolitics
        )
        if finalizer.finalize():
            print("ПОБЕДААААААААА")

