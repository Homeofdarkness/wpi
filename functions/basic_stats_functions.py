from typing import Tuple, List

from functions.agriculture_models import AgricultureDevelopmentModel
from functions.economy_models import BranchIncomeModel, PopulationGrowthModel, TradePotentialModel
from functions.industry_models import CivilEfficiencyLogisticModel, CivilUsageModel, IndustryBasicStatsModel, IndustryCoefficientModel
from functions.society_models import SocietyDeclineModel, SuccessChanceModel


class BasicStatsFunctions:

    # Economy
    @staticmethod
    def calculate_population_growth(current_population_count: int) -> int:
        return PopulationGrowthModel.calculate(current_population_count)

    @staticmethod
    def calculate_trade_potential(trade_rank: int,
                                  trade_efficiency: int) -> float:
        return TradePotentialModel.calculate(trade_rank, trade_efficiency)

    # Industry
    @staticmethod
    def calculate_industry_coefficient(processing_production: float,
                                       processing_usage: float,
                                       processing_efficiency: float,
                                       mean_score: float):
        return IndustryCoefficientModel.calculate(
            processing_production,
            processing_usage,
            processing_efficiency,
            mean_score,
        )

    @staticmethod
    def calculate_civil_usage(civil_security: float, tvr1: float,
                              tvr2: float) -> int:
        return CivilUsageModel.calculate(civil_security, tvr1, tvr2)

    @staticmethod
    def calculate_industry_basic_stats(industry_coefficient: float,
                                       civil_usage: float,
                                       standardization: float) -> \
            Tuple[float, float, float]:
        return IndustryBasicStatsModel.calculate(
            industry_coefficient,
            civil_usage,
            standardization,
        )

    @staticmethod
    def calculate_civil_efficiency_boost_from_logistic(
            logistic: float) -> float:
        return CivilEfficiencyLogisticModel.calculate(logistic)

    # Inner Politics
    @staticmethod
    def calculate_success_chance(
            knowledge_level: float,
            education_level: float,
            erudition_will: float
    ) -> float:
        return SuccessChanceModel.calculate(
            knowledge_level,
            education_level,
            erudition_will,
        )

    @staticmethod
    def calculate_society_decline(
            contentment: int,
            government_trust: float,
            many_children_traditions: int,
            sexual_asceticism: float,
            egocentrism_development: float,
            education_level: float,
            erudition_will: int,
            cultural_level: int,
            violence_tendency: float,
            unemployment_rate: float,
            grace_of_the_highest: int,
            commitment_to_cause: int,
            departure_from_truths: int
    ) -> float:
        return SocietyDeclineModel.calculate(
            contentment,
            government_trust,
            many_children_traditions,
            sexual_asceticism,
            egocentrism_development,
            education_level,
            erudition_will,
            cultural_level,
            violence_tendency,
            unemployment_rate,
            grace_of_the_highest,
            commitment_to_cause,
            departure_from_truths,
        )

    # Agriculture
    @staticmethod
    def calculate_approximate_agriculture_efficiency(
            securities: List[float]) -> float:
        return AgricultureDevelopmentModel.approximate_efficiency(securities)

    @classmethod
    def calculate_approximate_food_security(cls, biome_richness: float,
                                            overproduction_effects: int,
                                            securities: List[float]) -> float:
        return AgricultureDevelopmentModel.approximate_food_security(
            biome_richness,
            overproduction_effects,
            securities,
        )

    @classmethod
    def calculate_agriculture_development(
            cls,
            approximate_food_security: float,
            securities: List[float]
    ) -> float:
        return AgricultureDevelopmentModel.approximate_development(
            approximate_food_security,
            securities,
        )

    @classmethod
    def calculate_branches_income(
            cls,
            branches_count: int,
            branches_efficiency: float
    ) -> float:
        return BranchIncomeModel.calculate(branches_count, branches_efficiency)
