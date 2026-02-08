from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from stats.stats_base import StatsBase
from utils.logger_manager import get_logger

logger = get_logger("Finalizer")


@dataclass
class FinalizerBase(ABC):
    """Finishes a run by rendering / exporting updated stats."""

    Economy: StatsBase
    Industry: StatsBase
    Agriculture: StatsBase
    InnerPolitics: StatsBase

    @abstractmethod
    def finalize(self) -> bool:
        raise NotImplementedError


@dataclass
class PrintFinalizer(FinalizerBase):
    """Default finalizer: prints stats and logs them."""

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


# Backwards-compatible aliases
BasicFinalizer = PrintFinalizer
AtteriumFinalizer = PrintFinalizer
IsfFinalizer = PrintFinalizer
