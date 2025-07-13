from dataclasses import dataclass, field
from typing import Tuple

from functions.basic_in_move_functions import \
    BasicInMoveFunctions
from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats


@dataclass
class SkipMove:
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BasicInMoveFunctions)

    @classmethod
    def skip_move(cls):
        logistic_wastes = cls.Economy.gov_wastes[
                              1] + cls.InnerPolitics.provinces_count * cls.InnerPolitics.provinces_waste

        logistic_wastes_discount, food_security_spotter, tax_income_coefficient, contentment_spotter = cls.calculate_logistic_based_params(
            logistic_wastes)

        culture_coefficient = cls.InMoveFunctions.calculate_cultural_coefficient(
            cls.InnerPolitics.cultural_level,
            cls.InnerPolitics.egocentrism_development)

        contentment_coefficient_1, contentment_coefficient_2 = cls.InMoveFunctions.calculate_contentment_coefficients(
            cls.InnerPolitics.contentment + contentment_spotter)
        expected_infrastructure_waste = cls.InMoveFunctions.calculate_expected_infrastructure_wastes(
            cls.Economy.population_count)
        small_enterprise_tax_spotter = 1.1 if cls.Economy.gov_wastes[
                                                  0] > expected_infrastructure_waste else 0.85
        cls.Agriculture.expected_wastes = cls.InMoveFunctions.calculate_agriculture_wastes(
            cls.Economy.population_count,
            cls.Agriculture.securities,
            cls.Agriculture.biome_richness,
            cls.Agriculture.agriculture_development)
        cls.Agriculture.agriculture_efficiency = cls.InMoveFunctions.calculate_agriculture_efficiency(
            cls.Agriculture.securities,
            cls.Agriculture.agriculture_wastes,
            cls.Agriculture.expected_wastes)

        cls.Agriculture.food_security = round(
            cls.InMoveFunctions.calculate_food_security_spotter(
                cls.Agriculture.agriculture_efficiency,
                cls.Agriculture.biome_richness,
                cls.Agriculture.overprotective_effects))

        cls.Economy.income *= cls.InMoveFunctions.calculate_goods_coefficient(
            cls.Industry.tvr1)
        cls.Economy.income *= cls.InMoveFunctions.calculate_stability_coefficient(
            cls.InnerPolitics.poor_level,
            cls.InnerPolitics.jobless_level,
            sum(cls.Economy.med_wastes),
            cls.Economy.population_count) * contentment_coefficient_1 * (
                                  0.012 * cls.InnerPolitics.many_children_propoganda + 1)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_agriculture(
            cls.Agriculture.agriculture_efficiency,
            cls.Agriculture.agriculture_development, food_security_spotter)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_social_decline(
            cls.InnerPolitics.society_decline)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_food_diversity(
            cls.Agriculture.food_diversity)



    @classmethod
    def calculate_logistic_based_params(cls, logistic_wastes: float) -> Tuple[
        float, float, float, int]:
        logistic_wastes_discount, food_security_spotter, tax_income_coefficient = 0, 0, 0
        if cls.InMoveFunctions.calculate_expected_logistic_wastes(
                cls.Economy.gov_wastes) <= logistic_wastes:
            logistic_wastes_discount = cls.Economy.gov_wastes[0] * 0.1
        else:
            food_security_spotter = 7
            tax_income_coefficient = 0.1

        contentment_spotter = 0
        if 0 <= cls.InnerPolitics.salt_security < 50:
            contentment_spotter -= cls.InnerPolitics.salt_security // 5
        elif cls.InnerPolitics.salt_security >= 100:
            contentment_spotter += min(cls.InnerPolitics.salt_security,
                                       150) // 15
            contentment_spotter = min(contentment_spotter,
                                      100 - cls.InnerPolitics.contentment)

        total_control = cls.InnerPolitics.control[0] + \
                        cls.InnerPolitics.control[1]
        if total_control >= 90:
            contentment_spotter = min(contentment_spotter + 5,
                                      100 - cls.InnerPolitics.contentment)
            tax_income_coefficient -= 0.05
            food_security_spotter -= 4
        else:
            control_sum = cls.InnerPolitics.control[2] + \
                          cls.InnerPolitics.control[3]
            contentment_spotter -= 5
            tax_income_coefficient += control_sum / 400

        return logistic_wastes_discount, food_security_spotter, tax_income_coefficient, contentment_spotter
