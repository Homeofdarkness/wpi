from __future__ import annotations

from functions import atterium_stats_functions as atterium
from functions import isf_stats_functions as isf
from functions.economy_models import (
    branches_income,
    population_growth,
    trade_potential,
)
from functions.industry_models import (
    civil_efficiency_logistic_factor,
    civil_usage,
    industry_basic_stats,
    industry_coefficient,
)
from functions.society_models import society_decline, success_chance


def populate_basic_economy(stats) -> None:
    stats.income = round(population_growth(stats.population_count))
    stats.trade_potential = trade_potential(
        stats.trade_rank,
        stats.trade_efficiency,
    )
    stats.branches_income = branches_income(
        stats.branches_count,
        stats.branches_efficiency,
    )


def populate_basic_industry(stats) -> None:
    stats.civil_usage = civil_usage(
        stats.civil_security,
        stats.tvr1,
        stats.tvr2,
    )
    stats.industry_coefficient = (
        industry_coefficient(
            stats.processing_production,
            stats.processing_usage,
            stats.processing_efficiency,
            sum(stats.usages) // len(stats.usages),
        )
        if stats.usages
        else 0
    )

    efficiency, max_potential, expected_wastes = industry_basic_stats(
        stats.industry_coefficient,
        stats.civil_usage,
        stats.standardization,
    )

    stats.civil_efficiency = efficiency * civil_efficiency_logistic_factor(
        stats.logistic
    )
    stats.max_potential = max_potential
    stats.expected_wastes = expected_wastes


def populate_basic_inner_politics(stats) -> None:
    stats.research_success_chance = round(
        success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = society_decline(
        stats.contentment,
        stats.government_trust,
        stats.many_children_traditions,
        stats.sexual_asceticism,
        stats.egocentrism_development,
        stats.education_level,
        stats.erudition_will,
        stats.cultural_level,
        stats.violence_tendency,
        stats.unemployment_rate,
        stats.grace_of_the_highest,
        stats.commitment_to_cause,
        stats.departure_from_truths,
    )


def populate_atterium_inner_politics(stats) -> None:
    stats.research_success_chance = round(
        success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = atterium.society_decline(
        stats.contentment,
        stats.government_trust,
        stats.many_children_traditions,
        stats.sexual_asceticism,
        stats.egocentrism_development,
        stats.capitalistic_decay,
        stats.education_level,
        stats.erudition_will,
        stats.cultural_level,
        stats.violence_tendency,
        stats.unemployment_rate,
        stats.grace_of_the_highest,
        stats.commitment_to_cause,
        stats.departure_from_truths,
        stats.equality,
    )


def populate_isf_inner_politics(stats) -> None:
    stats.research_success_chance = round(
        success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = isf.society_decline(
        stats.contentment,
        stats.government_trust,
        stats.many_children_traditions,
        stats.sexual_asceticism,
        stats.egocentrism_development,
        stats.education_level,
        stats.erudition_will,
        stats.cultural_level,
        stats.violence_tendency,
        stats.unemployment_rate,
        stats.grace_of_the_silver,
        stats.commitment_to_cause,
        stats.departure_from_truths,
        stats.imperial_court_power,
        stats.separatism_of_the_highest,
        stats.allegory_influence,
    )
