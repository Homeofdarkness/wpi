"""Factories for building minimal valid stats objects for tests.

The Stats classes have a lot of fields because they mirror a game's data.
For tests we want *valid* objects with predictable values.
"""

from __future__ import annotations

from dataclasses import dataclass

from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, InnerPoliticsStats
from stats.atterium_stats import (
    AtteriumEconomyStats,
    AtteriumIndustrialStats,
    AtteriumAgricultureStats,
    AtteriumInnerPoliticsStats,
)
from stats.isf_stats import (
    IsfEconomyStats,
    IsfIndustrialStats,
    IsfAgricultureStats,
    IsfInnerPoliticsStats,
)


@dataclass
class BasicBundle:
    economy: EconomyStats
    industry: IndustrialStats
    agriculture: AgricultureStats
    inner_politics: InnerPoliticsStats


@dataclass
class AtteriumBundle:
    economy: AtteriumEconomyStats
    industry: AtteriumIndustrialStats
    agriculture: AtteriumAgricultureStats
    inner_politics: AtteriumInnerPoliticsStats


@dataclass
class IsfBundle:
    economy: IsfEconomyStats
    industry: IsfIndustrialStats
    agriculture: IsfAgricultureStats
    inner_politics: IsfInnerPoliticsStats


def make_basic_bundle(*, budget: float = 1000.0) -> BasicBundle:
    economy = EconomyStats(
        population_count=1_000_000,
        decrement_coefficient=1,
        inflation=5.0,
        current_budget=budget,
        stability=80,
        universal_tax=10.0,
        excise=5.0,
        additions=2.0,
        small_enterprise_tax=3.0,
        large_enterprise_tax=4.0,
        gov_wastes=[100.0, 50.0, 30.0, 10.0],
        med_wastes=[20.0, 15.0, 10.0, 5.0, 3.0],
        other_wastes=[5.0, 2.0, 1.0],
        war_wastes=[10.0, 5.0, 2.0],
        trade_rank=2,
        trade_usage=10,
        trade_efficiency=80,
        trade_wastes=1.0,
        high_quality_percent=30.0,
        mid_quality_percent=40.0,
        low_quality_percent=30.0,
        valgery=10.0,
        allegorization=0.0,
        branches_count=2,
        branches_efficiency=80.0,
    )

    industry = IndustrialStats(
        processing_production=60.0,
        processing_usage=55.0,
        processing_efficiency=70.0,
        usages=[60.0, 60.0, 60.0],
        civil_security=70.0,
        standardization=60.0,
        logistic=60.0,
        tvr1=70,
        tvr2=70,
        overproduction_coefficient=10.0,
        war_production_efficiency=60.0,
    )

    agriculture = AgricultureStats(
        husbandry=40.0,
        livestock=40.0,
        others=20.0,
        biome_richness=60.0,
        overprotective_effects=2,
        securities=[70.0, 70.0, 70.0],
        agriculture_wastes=20.0,
        agriculture_deceases=2.0,
        agriculture_natural_deceases=1.0,
        income_from_resources=2.0,
        food_diversity=50.0,
    )

    inner = InnerPoliticsStats(
        state_apparatus_size=50,
        state_apparatus_efficiency=70,
        knowledge_level=50.0,
        many_children_propoganda=10,
        integrity_of_faith=50,
        corruption_level=20,
        salt_security=80,
        poor_level=5.0,
        jobless_level=10.0,
        income_from_scientific=1.0,
        small_enterprise_percent=15.0,
        large_enterprise_count=10,
        provinces_count=5,
        provinces_waste=1.0,
        military_equipment=10.0,
        control=[40, 40, 20, 20],
        contentment=70,
        government_trust=60.0,
        many_children_traditions=40,
        sexual_asceticism=20.0,
        egocentrism_development=20.0,
        education_level=50.0,
        erudition_will=50,
        cultural_level=50,
        violence_tendency=20.0,
        panic_level=10.0,
        unemployment_rate=10.0,
        grace_of_the_highest=50,
        commitment_to_cause=50,
        departure_from_truths=10,
    )

    return BasicBundle(economy=economy, industry=industry, agriculture=agriculture, inner_politics=inner)


def make_atterium_bundle(*, budget: float = 1000.0) -> AtteriumBundle:
    b = make_basic_bundle(budget=budget)

    economy = AtteriumEconomyStats(**b.economy.model_dump(exclude_none=True),
        plan_efficiency=60.0,
        investment_of_large_companies=5.0,
        freedom_and_efficiency_of_small_business=3.0,
        adrian_effect=20.0,
        power_of_economic_formation=10.0,
    )

    # Atterium expects 5 gov_wastes entries and 2 other_wastes entries for rendering.
    if len(economy.gov_wastes) < 5:
        economy.gov_wastes = list(economy.gov_wastes) + [0.0] * (5 - len(economy.gov_wastes))
    if len(economy.other_wastes) > 2:
        economy.other_wastes = list(economy.other_wastes)[:2]
    elif len(economy.other_wastes) < 2:
        economy.other_wastes = list(economy.other_wastes) + [0.0] * (2 - len(economy.other_wastes))

    industry = AtteriumIndustrialStats(**b.industry.model_dump(exclude_none=True))

    agriculture = AtteriumAgricultureStats(**b.agriculture.model_dump(exclude_none=True))

    inner = AtteriumInnerPoliticsStats(
        **b.inner_politics.model_dump(exclude_none=True),
        state_apparatus_functionality=60.0,
        equality=50.0,
        capitalistic_decay=10.0,
    )

    return AtteriumBundle(economy=economy, industry=industry, agriculture=agriculture, inner_politics=inner)


def make_isf_bundle(*, budget: float = 1000.0) -> IsfBundle:
    b = make_basic_bundle(budget=budget)

    econ_dump = b.economy.model_dump(exclude_none=True)
    econ_dump.pop('small_enterprise_tax')

    economy = IsfEconomyStats(**econ_dump,
        small_business_tax=3.0,
    )

    # ISF expects 2 other_wastes entries for rendering (external, occupation).
    if len(economy.other_wastes) > 2:
        economy.other_wastes = list(economy.other_wastes)[:2]
    elif len(economy.other_wastes) < 2:
        economy.other_wastes = list(economy.other_wastes) + [0.0] * (2 - len(economy.other_wastes))


    industry = IsfIndustrialStats(**b.industry.model_dump(exclude_none=True))

    agriculture = IsfAgricultureStats(**b.agriculture.model_dump(exclude_none=True),
        empire_land_unmastery=10.0,
    )

    inner_dump = b.inner_politics.model_dump(exclude_none=True)
    inner_dump["many_children_traditions"] = 20
    inner_dump["control"] = [40, 40, 15, 20]
    inner = IsfInnerPoliticsStats(
        **inner_dump,
        allegory_influence=30.0,
        grace_of_the_silver=40,
        imperial_court_power=30.0,
        separatism_of_the_highest=10.0,
    )

    return IsfBundle(economy=economy, industry=industry, agriculture=agriculture, inner_politics=inner)
