from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from utils.logger_manager import get_logger


logger = get_logger("Run Skip Move")


class Finalizer:
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    @classmethod
    def finalize(cls) -> bool:
        print("Стата - ")
        print(cls.Economy)
        logger.info(cls.Economy)
        print(cls.Industry)
        logger.info(cls.Industry)
        print(cls.Agriculture)
        logger.info(cls.Agriculture)
        print(cls.InnerPolitics)
        logger.info(cls.InnerPolitics)

        return True
