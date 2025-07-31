from abc import ABC, abstractmethod
from dataclasses import dataclass

from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from utils.logger_manager import get_logger


logger = get_logger("Run Skip Move")


@dataclass
class FinalizerBase(ABC):
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    @abstractmethod
    def finalize(self):
        raise NotImplementedError()


@dataclass
class BasicFinalizer(FinalizerBase):
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    def finalize(self) -> bool:
        print("Стата - ")
        print(self.Economy)
        logger.info(self.Economy)
        print(self.Industry)
        logger.info(self.Industry)
        print(self.Agriculture)
        logger.info(self.Agriculture)
        print(self.InnerPolitics)
        logger.info(self.InnerPolitics)

        return True
