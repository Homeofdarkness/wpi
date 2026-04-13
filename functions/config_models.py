from __future__ import annotations

from dataclasses import dataclass

from stats.basic_stats import (
    AgricultureStats,
    EconomyStats,
    IndustrialStats,
    InnerPoliticsStats
)


@dataclass(frozen=True)
class BasicBundleModel:
    economy: EconomyStats
    industry: IndustrialStats
    agriculture: AgricultureStats
    inner_politics: InnerPoliticsStats


class EdenModel:
    """Базовый конфиг, собранный из старого текстового формата пользователя."""

    @staticmethod
    def build() -> BasicBundleModel:
        economy = EconomyStats(
            population_count=15_361_475,
            decrement_coefficient=0,
            inflation=2.0,
            current_budget=-53.668,
            stability=100,
            universal_tax=22.6,
            excise=8.1,
            additions=105.0,
            small_enterprise_tax=8.7,
            large_enterprise_tax=27.0,
            gov_wastes=[932.8, 57.0, 395.5, 341.3],
            med_wastes=[316.2, 178.0, 286.0, 47.0, 169.0],
            other_wastes=[0.0, 82.5, 0.0],
            war_wastes=[248.2, 212.0, 122.0],
            trade_rank=37,
            trade_usage=82,
            trade_efficiency=98,
            trade_wastes=20.5,
            high_quality_percent=45.0,
            mid_quality_percent=55.0,
            low_quality_percent=0.0,
            valgery=100.0,
            allegorization=4.8,
            branches_count=25,
            branches_efficiency=100.0,
        )
        industry = IndustrialStats(
            processing_production=100.0,
            processing_usage=100.0,
            processing_efficiency=69.0,
            usages=[100.0, 100.0, 100.0, 60.0],
            civil_security=100.0,
            standardization=81.0,
            logistic=27.0,
            tvr1=100,
            tvr2=90,
            overproduction_coefficient=98.72,
            war_production_efficiency=55.0,
            industry_income=102.22,
            consumption_of_goods=101.62,
        )
        agriculture = AgricultureStats(
            husbandry=35.0,
            livestock=41.0,
            others=24.0,
            biome_richness=100.0,
            overprotective_effects=6,
            securities=[100.0, 73.0, 58.0],
            workers_percent=100.0,
            workers_redistribution=0.0,
            storages_upkeep=125.0,
            consumption_factor=7.199,
            environmental_food=0,
            agriculture_deceases=0.0,
            agriculture_natural_deceases=16.9,
            income_from_resources=10.5,
            overstock_percent=95.0,
            food_supplies=0.0,
        )
        inner_politics = InnerPoliticsStats(
            state_apparatus_size=101,
            state_apparatus_efficiency=114,
            knowledge_level=72.0,
            many_children_propoganda=1,
            integrity_of_faith=90,
            corruption_level=1,
            salt_security=150,
            poor_level=0.0,
            jobless_level=0.0,
            income_from_scientific=20.5,
            small_enterprise_percent=12.5,
            large_enterprise_count=13,
            provinces_count=106,
            provinces_waste=1.7,
            military_equipment=3952.0,
            control=[80.0, 10.0, 5.0, 5.0],
            contentment=89,
            government_trust=87.0,
            many_children_traditions=11,
            sexual_asceticism=2.0,
            egocentrism_development=11.0,
            education_level=68.02,
            erudition_will=80,
            cultural_level=70,
            violence_tendency=6.0,
            panic_level=0.0,
            unemployment_rate=0.0,
            grace_of_the_highest=20,
            commitment_to_cause=94,
            departure_from_truths=9,
        )
        return BasicBundleModel(
            economy=economy,
            industry=industry,
            agriculture=agriculture,
            inner_politics=inner_politics,
        )
