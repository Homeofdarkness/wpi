from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Dict, Type, TypeVar, Generic

from stats.atterium_stats import (
    AtteriumEconomyStats, AtteriumIndustrialStats,
    AtteriumInnerPoliticsStats, AtteriumAgricultureStats
)
from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from stats.stats_base import StatsBase
from utils.input_parsers import InputParser
from utils.logger_manager import get_logger


logger = get_logger("Run Start Skip Move")

# Type variables for generic typing
T_Economy = TypeVar('T_Economy', bound=StatsBase)
T_Industry = TypeVar('T_Industry', bound=StatsBase)
T_Agriculture = TypeVar('T_Agriculture', bound=StatsBase)
T_InnerPolitics = TypeVar('T_InnerPolitics', bound=StatsBase)


class GameModes(StrEnum):
    """Режимы игры с более понятными названиями"""
    COUNTRY_CREATOR = 'country_creator'
    MOVES_SKIPPER = 'moves_skipper'


@dataclass
class StatsConfig:
    """Конфигурация для создания статистик"""
    economy_class: Type[StatsBase]
    industry_class: Type[StatsBase]
    agriculture_class: Type[StatsBase]
    inner_politics_class: Type[StatsBase]


@dataclass
class GameStats:
    """Контейнер для всех статистик игры"""
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats


class InputSection:
    """Класс для управления секциями ввода данных"""

    # Константы для секций ввода
    ECONOMY = "=== ЭКОНОМИКА ==="
    TRADE = "=== ТОРГОВЛЯ ==="
    INDUSTRY = "=== ПРОМЫШЛЕННОСТЬ ==="
    AGRICULTURE = "=== СЕЛЬСКОЕ ХОЗЯЙСТВО ==="
    GOVERNMENT = "=== ГОСУДАРСТВО ==="
    PEOPLE = "=== НАРОД ==="

    # Заголовки для режима создателя
    CREATOR_HEADERS = {
        'economy': "=== ВВОД ДАННЫХ ЭКОНОМИКИ ===",
        'industry': "=== ВВОД ДАННЫХ ПРОМЫШЛЕННОСТИ ===",
        'agriculture': "=== ВВОД ДАННЫХ СЕЛЬСКОГО ХОЗЯЙСТВА ===",
        'inner_politics': "=== ВВОД ДАННЫХ ВНУТРЕННЕЙ ПОЛИТИКИ ==="
    }


class ModeSelector:
    """Класс для выбора режима игры"""

    @staticmethod
    def display_available_modes() -> None:
        """Отображает доступные режимы"""
        print("Доступные режимы:")
        for i, mode in enumerate(GameModes, 1):
            print(f"{i}. {mode.value}")

    @staticmethod
    def get_mode_by_number(choice: str) -> Optional[GameModes]:
        """Получает режим по номеру"""
        if not choice.isdigit():
            return None

        index = int(choice) - 1
        modes_list = list(GameModes)

        if 0 <= index < len(modes_list):
            return modes_list[index]

        print(f"Номер должен быть от 1 до {len(modes_list)}")
        return None

    @staticmethod
    def get_mode_by_name(choice: str) -> Optional[GameModes]:
        """Получает режим по названию"""
        try:
            return GameModes(choice.lower())
        except ValueError:
            print(f"Неверный ввод '{choice}'. Попробуйте снова.")
            return None

    @classmethod
    def select_mode(cls) -> GameModes:
        """Интерактивный выбор режима"""
        cls.display_available_modes()

        while True:
            try:
                choice = input(
                    "Выберите режим (введите название или номер): ").strip()

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
                print("Произошла ошибка. Попробуйте снова.")


class DataInputHandler:
    """Обработчик ввода данных с различными стратегиями"""

    @staticmethod
    def get_section_data(section_name: str) -> str:
        """Получает данные для секции с обработкой ошибок"""
        print(section_name)
        try:
            return InputParser.parse_data_from_str()
        except Exception as e:
            logger.error(
                f"Ошибка при парсинге данных секции {section_name}: {e}")
            raise ValueError(
                f"Не удалось получить данные для секции {section_name}")

    @classmethod
    def collect_skipper_sections(cls) -> Dict[str, str]:
        """Собирает все секции для режима skipper"""
        sections = {}
        try:
            sections['economy'] = cls.get_section_data(InputSection.ECONOMY)
            sections['trade'] = cls.get_section_data(InputSection.TRADE)
            sections['industry'] = cls.get_section_data(InputSection.INDUSTRY)
            sections['agriculture'] = cls.get_section_data(
                InputSection.AGRICULTURE)
            sections['government'] = cls.get_section_data(
                InputSection.GOVERNMENT)
            sections['people'] = cls.get_section_data(InputSection.PEOPLE)
            return sections
        except Exception as e:
            logger.error(f"Ошибка при сборе секций: {e}")
            raise


@dataclass
class StartSkipMoveBase(ABC, Generic[
    T_Economy, T_Industry, T_Agriculture, T_InnerPolitics]):
    """Базовый абстрактный класс для инициализации игры"""
    mode: Optional[GameModes] = None

    def __post_init__(self):
        self._stats_config = self.get_stats_config()

    @abstractmethod
    def get_stats_config(self) -> StatsConfig:
        """Возвращает конфигурацию классов статистик"""
        pass

    def set_mode(self) -> GameModes:
        """Устанавливает режим игры"""
        if self.mode is None:
            self.mode = ModeSelector.select_mode()
        return self.mode

    def parse_user_input_data(self) -> GameStats:
        """Парсит пользовательский ввод в зависимости от режима"""
        try:
            self.mode = self.set_mode()

            match self.mode:
                case GameModes.COUNTRY_CREATOR:
                    return self._parse_creator_mode_input()
                case GameModes.MOVES_SKIPPER:
                    return self._parse_skipper_mode_input()
                case _:
                    raise ValueError(f"Неподдерживаемый режим: {self.mode}")

        except KeyboardInterrupt:
            logger.info("Операция отменена пользователем")
            raise
        except Exception as e:
            logger.error(f"Ошибка при парсинге пользовательского ввода: {e}")
            raise

    def _parse_creator_mode_input(self) -> GameStats:
        """Парсит ввод в режиме создателя"""
        try:
            stats_data = {}
            config = self._stats_config

            # Создаем статистики через пользовательский ввод
            stats_data['Economy'] = config.economy_class.from_user_input(
                InputSection.CREATOR_HEADERS['economy'])

            stats_data['Industry'] = config.industry_class.from_user_input(
                InputSection.CREATOR_HEADERS['industry'])

            stats_data[
                'Agriculture'] = config.agriculture_class.from_user_input(
                InputSection.CREATOR_HEADERS['agriculture'])

            stats_data[
                'InnerPolitics'] = config.inner_politics_class.from_user_input(
                InputSection.CREATOR_HEADERS['inner_politics'])

            return GameStats(**stats_data)

        except Exception as e:
            logger.error(f"Ошибка в режиме создателя: {e}")
            raise ValueError(
                f"Не удалось создать статистики в режиме создателя: {e}")

    def _parse_skipper_mode_input(self) -> GameStats:
        """Парсит ввод в режиме пропуска ходов"""
        try:
            # Собираем данные всех секций
            sections = DataInputHandler.collect_skipper_sections()
            config = self._stats_config

            # Создаем статистики из текста
            stats_data = {}

            # Экономика (экономика + торговля)
            economy_text = f"{sections['economy']}\n{sections['trade']}"
            stats_data['Economy'] = config.economy_class.from_stats_text(
                economy_text)

            # Промышленность
            stats_data['Industry'] = config.industry_class.from_stats_text(
                sections['industry'])

            # Сельское хозяйство
            stats_data[
                'Agriculture'] = config.agriculture_class.from_stats_text(
                sections['agriculture'])

            # Внутренняя политика (государство + народ)
            politics_text = f"{sections['government']}\n{sections['people']}"
            stats_data[
                'InnerPolitics'] = config.inner_politics_class.from_stats_text(
                politics_text)

            return GameStats(**stats_data)

        except Exception as e:
            logger.error(f"Ошибка в режиме пропуска ходов: {e}")
            raise ValueError(
                f"Не удалось создать статистики в режиме пропуска ходов: {e}")


@dataclass
class BasicStartSkipMove(StartSkipMoveBase[
                             EconomyStats, IndustrialStats, AgricultureStats, InnerPoliticsStats]):
    """Базовая реализация инициализации игры"""

    def get_stats_config(self) -> StatsConfig:
        """Возвращает конфигурацию базовых классов статистик"""
        return StatsConfig(
            economy_class=EconomyStats,
            industry_class=IndustrialStats,
            agriculture_class=AgricultureStats,
            inner_politics_class=InnerPoliticsStats
        )


@dataclass
class AtteriumStartSkipMove(StartSkipMoveBase[
                                AtteriumEconomyStats, AtteriumIndustrialStats, AtteriumAgricultureStats, AtteriumInnerPoliticsStats]):
    """Реализация инициализации для игры Atterium"""

    def get_stats_config(self) -> StatsConfig:
        """Возвращает конфигурацию классов статистик для Atterium"""
        return StatsConfig(
            economy_class=AtteriumEconomyStats,
            industry_class=AtteriumIndustrialStats,
            agriculture_class=AtteriumAgricultureStats,
            inner_politics_class=AtteriumInnerPoliticsStats
        )
