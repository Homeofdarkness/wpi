from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

from modules.mode_spec import GameMode, ModeRegistry
from modules.run_finalize import PrintFinalizer
from modules.run_skip_move import BasicSkipMove
from modules.run_start_skip import make_start_skip_move
from utils.logger_manager import get_logger
from utils.user_io import ConsoleIO, UserIO


logger = get_logger("Run Main")


class Status(StrEnum):
    """Exit status of the application."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class ModeSelector:
    """UI helper to select a world mode."""

    @staticmethod
    def display_available_modes() -> None:
        modes = ModeRegistry.available()
        print("\nДоступные режимы:")
        for i, (mode, spec) in enumerate(modes.items(), 1):
            print(f"{i}. {spec.name} ({mode.value})")
            if spec.description:
                print(f"   {spec.description}")

    @staticmethod
    def _by_number(choice: str) -> Optional[GameMode]:
        if not choice.isdigit():
            return None
        idx = int(choice) - 1
        modes = list(ModeRegistry.available().keys())
        if 0 <= idx < len(modes):
            return modes[idx]
        print(f"Номер должен быть от 1 до {len(modes)}")
        return None

    @staticmethod
    def _by_name(choice: str) -> Optional[GameMode]:
        try:
            return GameMode(choice.lower())
        except ValueError:
            return None

    @classmethod
    def select_mode(cls) -> GameMode:
        cls.display_available_modes()
        while True:
            choice = input("\nВыберите режим (название или номер): ").strip()
            if not choice:
                print("Пустой ввод. Попробуйте снова.")
                continue
            by_num = cls._by_number(choice)
            if by_num is not None:
                return by_num
            by_name = cls._by_name(choice)
            if by_name is not None:
                return by_name
            print("Неизвестный режим. Попробуйте снова.")


@dataclass
class RunMain:
    """Main entrypoint.

    This is intentionally thin: it reads user input, builds the correct mode
    spec, runs the shared engine, then prints the final stats.

    All mode-specific behavior is registered in :class:`ModeRegistry`.
    """

    mode: Optional[GameMode] = None
    io: UserIO = field(default_factory=ConsoleIO)

    def run(self) -> Status:
        try:
            mode = self.mode or ModeSelector.select_mode()
            spec = ModeRegistry.get(mode)
            logger.info(f"Запуск: {spec.name} ({spec.mode.value})")

            start_skip = make_start_skip_move(spec.stats_config)
            stats = start_skip.parse_user_input_data()

            engine = BasicSkipMove(
                Economy=stats.Economy,
                Industry=stats.Industry,
                Agriculture=stats.Agriculture,
                InnerPolitics=stats.InnerPolitics,
                InMoveFunctions=spec.in_move_functions_factory(),
                Rules=spec.rules_factory(),
                io=self.io,
                mode_name=spec.mode.value,
            )

            engine.run()

            PrintFinalizer(
                Economy=engine.Economy,
                Industry=engine.Industry,
                Agriculture=engine.Agriculture,
                InnerPolitics=engine.InnerPolitics,
            ).finalize()

            return Status.SUCCESS

        except KeyboardInterrupt:
            logger.info("Прервано пользователем")
            return Status.CANCELLED
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            print(e)
            return Status.ERROR
