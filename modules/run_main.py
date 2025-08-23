from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Dict, Type, Any, Protocol

from modules.run_finalize import BasicFinalizer, AtteriumFinalizer
from modules.run_skip_move import BasicSkipMove, AtteriumSkipMove
from modules.run_start_skip import BasicStartSkipMove, AtteriumStartSkipMove, \
    GameStats
from utils.logger_manager import get_logger


logger = get_logger("Run Main")


class GameMode(StrEnum):
    """Режимы запуска"""
    BASIC = "basic"
    ATTERIUM = "atterium"
    TROY = "troy"
    RECOVERY_BLOCK = "recovery-block"


class Status(StrEnum):
    """Статусы завершения"""
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


# Протоколы для типизации
class StartSkipProtocol(Protocol):
    def parse_user_input_data(self) -> GameStats: ...


class SkipMoveProtocol(Protocol):
    def skip_move(self) -> None: ...

    Economy: Any
    Industry: Any
    Agriculture: Any
    InnerPolitics: Any


class FinalizerProtocol(Protocol):
    def finalize(self) -> bool: ...


@dataclass
class GameConfiguration:
    """Конфигурация для конкретного режима"""
    start_skip_class: Optional[Type[StartSkipProtocol]]
    skip_move_class: Optional[Type[SkipMoveProtocol]]
    finalizer_class: Optional[Type[FinalizerProtocol]]
    name: str
    description: Optional[str] = None
    is_available: bool = True


class GameConfigurationRegistry:
    """Реестр конфигураций"""

    _configurations: Dict[GameMode, GameConfiguration] = {
        GameMode.BASIC: GameConfiguration(
            start_skip_class=BasicStartSkipMove,
            skip_move_class=BasicSkipMove,
            finalizer_class=BasicFinalizer,
            name="Базовый",
            description="Стандартный режим работы"
        ),
        GameMode.ATTERIUM: GameConfiguration(
            start_skip_class=AtteriumStartSkipMove,
            skip_move_class=AtteriumSkipMove,
            finalizer_class=AtteriumFinalizer,
            name="Atterium",
            description="Расширенный режим для Аттериума"
        ),
        GameMode.TROY: GameConfiguration(
            start_skip_class=None,  # Пока не реализован
            skip_move_class=None,
            finalizer_class=None,
            name="Troy",
            description="Режим Troy - в разработке",
            is_available=False
        ),
        GameMode.RECOVERY_BLOCK: GameConfiguration(
            start_skip_class=None,  # Пока не реализован
            skip_move_class=None,
            finalizer_class=None,
            name="Recovery Block",
            description="Режим восстановления - в разработке",
            is_available=False
        )
    }

    @classmethod
    def get_configuration(cls, mode: GameMode) -> Optional[GameConfiguration]:
        """Получает конфигурацию для указанного режима"""
        return cls._configurations.get(mode)

    @classmethod
    def get_available_modes(cls) -> Dict[GameMode, GameConfiguration]:
        """Возвращает только доступные режимы"""
        return {mode: config for mode, config in cls._configurations.items()
                if config.is_available}


class ModeSelector:
    """Класс для выбора режима"""

    @staticmethod
    def display_available_modes() -> None:
        """Отображает доступные режимы"""
        available_modes = GameConfigurationRegistry.get_available_modes()

        print("\nДоступные режимы:")
        for i, (mode, config) in enumerate(available_modes.items(), 1):
            status = "✓ Доступен" if config.is_available else "⚠ В разработке"
            print(f"{i}. {config.name} ({mode.value}) - {status}")
            if config.description:
                print(f"   {config.description}")

    @staticmethod
    def get_mode_by_number(choice: str) -> Optional[GameMode]:
        """Получает режим по номеру"""
        if not choice.isdigit():
            return None

        available_modes = list(
            GameConfigurationRegistry.get_available_modes().keys())
        index = int(choice) - 1

        if 0 <= index < len(available_modes):
            return available_modes[index]

        print(f"Номер должен быть от 1 до {len(available_modes)}")
        return None

    @staticmethod
    def get_mode_by_name(choice: str) -> Optional[GameMode]:
        """Получает режим по названию"""
        try:
            mode = GameMode(choice.lower())
            config = GameConfigurationRegistry.get_configuration(mode)

            if config and config.is_available:
                return mode
            elif config and not config.is_available:
                print(f"Режим '{choice}' находится в разработке")
                return None
            else:
                print(f"Неизвестный режим '{choice}'")
                return None

        except ValueError:
            print(f"Неверный ввод '{choice}'. Попробуйте снова.")
            return None

    @classmethod
    def select_mode(cls) -> GameMode:
        """Интерактивный выбор режима"""
        cls.display_available_modes()

        while True:
            try:
                choice = input(
                    "\nВыберите режим (введите название или номер): ").strip()

                if not choice:
                    print("Пустой ввод. Попробуйте снова.")
                    continue

                # Попытка получить режим по номеру
                mode = cls.get_mode_by_number(choice)
                if mode is not None:
                    return mode

                # Попытка получить режим по названию
                mode = cls.get_mode_by_name(choice)
                if mode is not None:
                    return mode

            except KeyboardInterrupt:
                print("\nОтмена выбора режима.")
                raise
            except Exception as e:
                logger.error(f"Ошибка при выборе режима: {e}")
                raise Exception(f"Произошла ошибка: {e}")


class GameRunner(ABC):
    """Абстрактный класс для запуска"""

    def __init__(self, configuration: GameConfiguration):
        self.configuration = configuration
        self.stats: Optional[GameStats] = None
        self.skip_move_instance: Optional[SkipMoveProtocol] = None

    @abstractmethod
    def initialize_game(self) -> bool:
        """Инициализирует"""
        pass

    @abstractmethod
    def execute_game_loop(self) -> bool:
        """Выполняет основной цикл"""
        pass

    @abstractmethod
    def finalize_game(self) -> Status:
        """Завершает"""
        pass

    def run(self) -> Status:
        """Запускает полный цикл"""
        try:
            logger.info(f"Запуск в режиме: {self.configuration.name}")

            if not self.initialize_game():
                logger.error("Не удалось инициализировать")
                return Status.ERROR

            if not self.execute_game_loop():
                logger.error("Ошибка при скипе хода")
                return Status.ERROR

            return self.finalize_game()

        except KeyboardInterrupt:
            logger.info("Прервано пользователем")
            return Status.CANCELLED
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return Status.ERROR


class StandardGameRunner(GameRunner):
    """Стандартный запускатель"""

    def initialize_game(self) -> bool:
        """Инициализирует среду"""
        try:
            logger.debug("Инициализация...")
            start_skip = self.configuration.start_skip_class()
            self.stats = start_skip.parse_user_input_data()

            logger.debug("Создание экземпляра skip_move...")
            self.skip_move_instance = self.configuration.skip_move_class(
                Economy=self.stats.Economy,
                Industry=self.stats.Industry,
                Agriculture=self.stats.Agriculture,
                InnerPolitics=self.stats.InnerPolitics
            )

            logger.info("Успешно инициализировано")
            return True

        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")
            return False

    def execute_game_loop(self) -> bool:
        """Выполняет основной игровой цикл"""
        try:
            logger.debug("Выполнение игрового хода...")
            self.skip_move_instance.skip_move()
            logger.info("Игровой ход выполнен успешно")
            return True

        except Exception as e:
            logger.error(f"Ошибка при выполнении игрового хода: {e}")
            return False

    def finalize_game(self) -> Status:
        """Завершает работу"""
        try:
            logger.debug("Финализация...")
            finalizer = self.configuration.finalizer_class(
                self.skip_move_instance.Economy,
                self.skip_move_instance.Industry,
                self.skip_move_instance.Agriculture,
                self.skip_move_instance.InnerPolitics
            )

            if finalizer.finalize():
                logger.info("Победааа!")
                return Status.SUCCESS
            else:
                logger.error("Чето не то")
                return Status.ERROR

        except Exception as e:
            logger.error(f"Ошибка при финализации: {e}")
            return Status.ERROR


class RunMain:
    """Главный класс для запуска"""

    def __init__(self, mode: Optional[GameMode] = None):
        self.mode = mode
        self.configuration: Optional[GameConfiguration] = None
        self.runner: Optional[GameRunner] = None

    def set_running_mode(self,
                         running_mode: Optional[GameMode] = None) -> None:
        """Устанавливает режим запуска"""
        if running_mode is None:
            running_mode = self._parse_mode_from_input()

        self.mode = running_mode
        self.configuration = GameConfigurationRegistry.get_configuration(
            running_mode)

        if self.configuration is None:
            raise ValueError(
                f"Конфигурация для режима {running_mode} не найдена")

        logger.info(f"Установлен режим: {self.configuration.name}")

    def _parse_mode_from_input(self) -> GameMode:
        """Парсит режим из пользовательского ввода"""
        return ModeSelector.select_mode()

    def _create_runner(self) -> GameRunner:
        """Создает подходящий runner"""
        if self.configuration is None:
            raise ValueError("Конфигурация не установлена")

        # Пока используем только стандартный runner
        # В будущем можно добавить разные типы runner'ов
        return StandardGameRunner(self.configuration)

    def run(self):
        """Запускает логику"""
        try:
            # Устанавливаем режим, если не установлен
            if self.mode is None:
                self.set_running_mode()

            # Проверяем доступность режима
            if not self.configuration.is_available:
                print(
                    f"Режим '{self.configuration.name}' находится в разработке")
                logger.warning(
                    f"Попытка запуска недоступного режима: {self.mode}")

            # Создаем и запускаем runner
            self.runner = self._create_runner()
            return self.runner.run()

        except KeyboardInterrupt:
            print("\nПрервано пользователем.")
            return Status.CANCELLED
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise Exception(f"Произошла критическая ошибка: {e}")
