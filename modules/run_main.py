from __future__ import annotations

from enum import StrEnum

from modules.mode_spec import GameMode, available_modes, get_mode
from modules.run_finalize import (
    print_budget_report,
    print_final_state,
    print_population_growth_report,
)
from modules.run_skip_move import TurnEngine
from modules.run_start_skip import make_start_skip_move
from utils.logger_manager import get_logger
from utils.user_io import ConsoleIO, UserIO


logger = get_logger("Run Main")


class Status(StrEnum):
    """Exit status of the application."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


def display_available_modes() -> None:
    print("\nДоступные режимы:")
    for number, (mode, spec) in enumerate(available_modes().items(), 1):
        print(f"{number}. {spec.name} ({mode.value})")
        if spec.description:
            print(f"   {spec.description}")


def select_mode() -> GameMode:
    display_available_modes()
    modes = list(available_modes())
    while True:
        choice = input("\nВыберите режим (название или номер): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(modes):
                return modes[index]
            print(f"Номер должен быть от 1 до {len(modes)}")
            continue
        try:
            return GameMode(choice.lower())
        except ValueError:
            message = (
                "Пустой ввод. Попробуйте снова."
                if not choice
                else "Неизвестный режим. Попробуйте снова."
            )
            print(message)


def run_app(
    mode: GameMode | None = None,
    io: UserIO | None = None,
) -> Status:
    """Read input, resolve one turn and print the resulting world state."""

    try:
        selected_mode = mode or select_mode()
        spec = get_mode(selected_mode)
        logger.info(f"Запуск: {spec.name} ({spec.mode.value})")
        state = make_start_skip_move(spec.stats_config).read()
        engine = TurnEngine(
            state=state,
            rules=spec.rules_factory(),
            io=io or ConsoleIO(),
            mode_name=spec.mode.value,
        )
        report = engine.run()
        print_budget_report(report)
        print()
        print_population_growth_report(report)
        print()
        print_final_state(state)
        return Status.SUCCESS
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        return Status.CANCELLED
    except Exception as error:
        logger.error(f"Ошибка запуска: {error}")
        print(error)
        return Status.ERROR
