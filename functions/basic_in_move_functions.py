from typing import List, Tuple

from functions.agriculture_models import (
    AdditionalWastesModel,
    AgricultureDevelopmentModel,
    AgricultureEfficiencyModel,
    AgricultureWastesModel,
    FoodModel,
    WorkersCountModel,
)
from functions.base import BaseInMoveFunctions
from functions.income_models import (
    InfrastructureModel,
    LogisticsModel,
    MoneyIncomeModel,
    TaxIncomeModel,
)
from functions.industry_models import (
    ConsumptionOfGoodsModel,
    IndustryIncomeModel,
    IndustryOverproductionModel,
    OverproductionModel,
)
from functions.society_models import (
    ContentmentModel,
    CorruptionModel,
    CulturalCoefficientModel,
    DemographyModel,
    IncomeModifierModel,
    IntegrityOfFaithModel,
    KnowledgeModel,
    StabilityModel,
    StateApparatusModel,
)
from functions.trade_models import ForexFeatures, TradeModels


class BasicInMoveFunctions(BaseInMoveFunctions):

    @staticmethod
    def calculate_expected_logistic_wastes(
            government_wastes: List[float]) -> float:
        return LogisticsModel.expected_wastes(government_wastes)

    @staticmethod
    def calculate_cultural_coefficient(cultural_level: int,
                                       egocentrism_development: float) -> float:
        return CulturalCoefficientModel.calculate(cultural_level, egocentrism_development)

    @staticmethod
    def calculate_contentment_coefficients(contentment: int) -> Tuple[
        float, float]:
        return ContentmentModel.coefficients(contentment)

    @staticmethod
    def calculate_expected_infrastructure_wastes(
            population_count: int) -> float:
        return InfrastructureModel.expected_wastes(population_count)

    @staticmethod
    def calculate_workers_count(
            population_count: int,
            workers_percent: float,
            workers_redistribution: float
    ) -> int:
        return WorkersCountModel.calculate(
            population_count,
            workers_percent,
            workers_redistribution,
        )

    @staticmethod
    def calculate_additional_wastes(
            security_percent: float
    ) -> float:
        return AdditionalWastesModel.calculate(security_percent)

    @classmethod
    def calculate_agriculture_wastes(
            cls,
            workers_count: int,
            securities: List[float],
            husbandry: float,
            livestock: float,
            others: float
    ) -> float:
        return AgricultureWastesModel.calculate(
            workers_count,
            securities,
            husbandry,
            livestock,
            others,
        )

    @staticmethod
    def calculate_agriculture_development(
            securities: List[float],
            workers_count: int,
            population_count: int,
            biome_richness: float,
            food_diversity: float,
            husbandry: float,
            livestock: float,
            others: float,
    ) -> float:
        return AgricultureDevelopmentModel.calculate(
            securities,
            workers_count,
            population_count,
            biome_richness,
            food_diversity,
            husbandry,
            livestock,
            others,
        )

    @staticmethod
    def calculate_agriculture_efficiency(
            securities: List[float],
            biome_richness: float,
            husbandry: float,
            livestock: float,
            others: float,
            agriculture_deceases: float,
            agriculture_natural_deceases: float,
            workers_count: int,
            population_count: int,
    ) -> float:
        return AgricultureEfficiencyModel.calculate(
            securities,
            biome_richness,
            husbandry,
            livestock,
            others,
            agriculture_deceases,
            agriculture_natural_deceases,
            workers_count,
            population_count,
        )

    @staticmethod
    def calculate_food_diversity(
            husbandry: float,
            livestock: float,
            others: float,
            biome_richness: float
    ) -> float:
        return FoodModel.diversity(husbandry, livestock, others, biome_richness)

    @classmethod
    def calculate_food_income(
            cls,
            workers_count: int,
            securities: List[float],
            overprotective_effects: float,
            agriculture_deceases: float,
            agriculture_natural_deceases: float,
            environmental_food: int
    ) -> float:
        return FoodModel.income(
            workers_count,
            securities,
            overprotective_effects,
            agriculture_deceases,
            agriculture_natural_deceases,
            environmental_food,
        )

    @staticmethod
    def calculate_food_consumption(
            population_count: int,
            consumption_factor: float,
    ) -> float:
        return FoodModel.consumption(population_count, consumption_factor)

    @classmethod
    def calculate_food_security(
            cls,
            food_income: float,
            food_consumption: float,
    ) -> float:
        return FoodModel.security(food_income, food_consumption)

    @staticmethod
    def calculate_food_supplies(
            current_food_supplies: float,
            food_security: float,
            overstock_percent: float,
            storages_upkeep: float
    ) -> float:
        return FoodModel.supplies(
            current_food_supplies,
            food_security,
            overstock_percent,
            storages_upkeep,
        )

    @staticmethod
    def calculate_goods_coefficient(goods_count: int) -> float:
        if goods_count >= 100:
            return 1.1
        return 0.004 * goods_count + 0.66

    @staticmethod
    def calculate_stability_coefficient(
            poor_level: float,
            jobless_level: float,
            med_waste: float,
            population: int
    ) -> float:
        return StabilityModel.coefficient(poor_level, jobless_level, med_waste, population)

    @staticmethod
    def calculate_income_coefficient_based_on_agriculture(
            food_security: float
    ) -> float:
        return IncomeModifierModel.from_agriculture(food_security)

    @staticmethod
    def calculate_income_coefficient_based_on_social_decline(
            social_decline: float) -> float:
        return IncomeModifierModel.from_social_decline(social_decline)

    @staticmethod
    def calculate_income_coefficient_based_on_panic_level(
            panic_level: float) -> float:
        return IncomeModifierModel.from_panic_level(panic_level)

    @staticmethod
    def calculate_income_coefficient_based_on_food_diversity(
            food_diversity: float) -> float:
        return IncomeModifierModel.from_food_diversity(food_diversity)

    @staticmethod
    def calculate_population_decrement_coefficient(
            decrement_coefficient: int
    ) -> float:
        return DemographyModel.decrement_coefficient(decrement_coefficient)

    @staticmethod
    def calculate_population_underfeed(
            population_count: int,
            food_security: float,
            biome_richness: float,
            death_probability: float = 0.36
    ) -> int:
        return FoodModel.underfeed(
            population_count,
            food_security,
            biome_richness,
            death_probability,
        )

    @staticmethod
    def calculate_industry_income(
            gov_wastes: List[float],
            civil_usage: float,
            max_potential: float,
            expected_wastes: float
    ) -> float:
        return IndustryIncomeModel.calculate(gov_wastes, civil_usage, max_potential, expected_wastes)

    @staticmethod
    def calculate_tax_income(
            universal_tax: float,
            excise: float,
            additions: float,
            small_enterprise_tax: float,
            large_enterprise_tax: float,
            small_enterprise_percent: float,
            large_enterprise_count: float,
            population_count: int
    ) -> float:
        return TaxIncomeModel.calculate(
            universal_tax,
            excise,
            additions,
            small_enterprise_tax,
            large_enterprise_tax,
            small_enterprise_percent,
            large_enterprise_count,
            population_count,
        )

    @staticmethod
    def calculate_integrity_of_faith_factor(integrity_of_faith: int) -> float:
        return IntegrityOfFaithModel.factor(integrity_of_faith)

    @staticmethod
    def calculate_forex_course(
            stability: int,
            income: float,
            wastes: float,
            budget: float,
            trade_rank: int,
            trade_efficiency: float,
            trade_overload: float,
            industry_efficiency: float,
            state_apparatus_efficiency: int,
            contentment: int, poor_level: float,
            jobless_level: float,
            control_data: list
    ) -> float:
        control = control_data[0] + control_data[1] - control_data[2] - control_data[3]
        features = ForexFeatures(
            stability=stability,
            income=income,
            wastes=wastes,
            budget=budget,
            trade_rank=trade_rank,
            trade_efficiency=trade_efficiency,
            trade_overload=trade_overload,
            industry_efficiency=industry_efficiency,
            state_apparatus_efficiency=state_apparatus_efficiency,
            contentment=contentment,
            poor_level=poor_level,
            jobless_level=jobless_level,
            control_balance=control,
        )
        return TradeModels.calculate_forex_course(features)

    @staticmethod
    def calculate_trade_income(trade_potential: float, trade_usage: int,
                               trade_efficiency: float, trade_wastes: float,
                               high_quality_percent: float,
                               mid_quality_percent: float,
                               low_quality_percent: float,
                               forex: float, valgery: float) -> float:
        return TradeModels.calculate_trade_income(
            trade_potential=trade_potential,
            trade_usage=trade_usage,
            trade_efficiency=trade_efficiency,
            trade_wastes=trade_wastes,
            high_quality_percent=high_quality_percent,
            mid_quality_percent=mid_quality_percent,
            low_quality_percent=low_quality_percent,
            forex=forex,
            valgery=valgery,
        )

    @staticmethod
    def calculate_money_income_collaboration_factor(
            agriculture_efficiency: float, civil_efficiency: float) -> float:
        return MoneyIncomeModel.collaboration_factor(agriculture_efficiency, civil_efficiency)

    @staticmethod
    def calculate_inflation_factor(inflation: float) -> float:
        return MoneyIncomeModel.inflation_factor(inflation)

    @staticmethod
    def calculate_agriculture_factor(
            current_tax_income: float,
            agriculture_development: float,
            workers_count: int
    ) -> float:
        return MoneyIncomeModel.agriculture_factor(
            current_tax_income,
            agriculture_development,
            workers_count,
        )

    @staticmethod
    def expected_state_apparatus(population_count: int,
                                 apparatus_wastes: float) -> int:
        return StateApparatusModel.expected_size(population_count, apparatus_wastes)

    @staticmethod
    def calculate_money_income_boost(stability: int, poor_level: float,
                                     jobless_level: float) -> float:
        return MoneyIncomeModel.boost(stability, poor_level, jobless_level)

    @staticmethod
    def calculate_money_income_simple_boost(stability: int) -> float:
        return MoneyIncomeModel.simple_boost(stability)

    @staticmethod
    def apply_corruption(corruption_level: int) -> float:
        return CorruptionModel.apply(corruption_level)

    @classmethod
    def calculate_knowledge(
            cls,
            population_count: int,
            knowledge_wastes: float
    ) -> float:
        return KnowledgeModel.calculate(population_count, knowledge_wastes)

    @staticmethod
    def calculate_military_equipment_coefficient(
            war_efficiency: float) -> float:
        return war_efficiency / 50

    @staticmethod
    def calculate_consumption_of_goods(population_count: int, trade_usage: int,
                                       trade_efficiency: float, tvr1: float,
                                       tvr2: float,
                                       base_multiplier: float = 12.0) -> Tuple[
        float, float]:
        return ConsumptionOfGoodsModel.calculate(
            population_count,
            trade_usage,
            trade_efficiency,
            tvr1,
            tvr2,
            base_multiplier,
        )

    @staticmethod
    def calculate_industry_overproduction_change(
            tvr1: int,
            tvr2: int,
            consumption: float,
            trade_usage: int
    ) -> float:
        return IndustryOverproductionModel.calculate_change(
            tvr1,
            tvr2,
            consumption,
            trade_usage,
        )

    @staticmethod
    def calculate_allegorization_trade_factor(
            allegorization_percent: float
    ) -> float:
        return TradeModels.calculate_allegorization_trade_factor(allegorization_percent)

    @staticmethod
    def calculate_allegorization_economy_factor(
            allegorization_percent: float
    ) -> float:
        return TradeModels.calculate_allegorization_economy_factor(allegorization_percent)

    @staticmethod
    def calculate_overproduction_tax_spotter(
            overproduction_coefficient: float
    ) -> float:
        return OverproductionModel.tax_spotter(overproduction_coefficient)

    @staticmethod
    def calculate_overproduction_trade_income(
            overproduction_coefficient: float
    ) -> float:
        return OverproductionModel.trade_income_factor(overproduction_coefficient)
