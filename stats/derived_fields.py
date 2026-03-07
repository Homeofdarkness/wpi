from __future__ import annotations

from functions.atterium_stats_functions import AtteriumStatsFunctions
from functions.basic_stats_functions import BasicStatsFunctions
from functions.isf_stats_functions import IsfStatsFunctions


def populate_basic_economy(stats) -> None:
    stats.income = round(
        BasicStatsFunctions.calculate_population_growth(stats.population_count)
    )
    stats.trade_potential = BasicStatsFunctions.calculate_trade_potential(
        stats.trade_rank,
        stats.trade_efficiency,
    )
    stats.branches_income = BasicStatsFunctions.calculate_branches_income(
        stats.branches_count,
        stats.branches_efficiency,
    )


def populate_basic_industry(stats) -> None:
    stats.civil_usage = BasicStatsFunctions.calculate_civil_usage(
        stats.civil_security,
        stats.tvr1,
        stats.tvr2,
    )
    stats.industry_coefficient = BasicStatsFunctions.calculate_industry_coefficient(
        stats.processing_production,
        stats.processing_usage,
        stats.processing_efficiency,
        sum(stats.usages) // len(stats.usages),
    ) if stats.usages else 0

    efficiency, max_potential, expected_wastes = (
        BasicStatsFunctions.calculate_industry_basic_stats(
            stats.industry_coefficient,
            stats.civil_usage,
            stats.standardization,
        )
    )

    stats.civil_efficiency = (
        efficiency * BasicStatsFunctions.calculate_civil_efficiency_boost_from_logistic(
            stats.logistic
        )
    )
    stats.max_potential = max_potential
    stats.expected_wastes = expected_wastes


def populate_basic_inner_politics(stats) -> None:
    stats.success_chance = round(
        BasicStatsFunctions.calculate_success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = BasicStatsFunctions.calculate_society_decline(
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
    stats.success_chance = round(
        BasicStatsFunctions.calculate_success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = AtteriumStatsFunctions.calculate_society_decline(
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
    stats.success_chance = round(
        BasicStatsFunctions.calculate_success_chance(
            stats.knowledge_level,
            stats.education_level,
            stats.erudition_will,
        )
    )
    stats.society_decline = IsfStatsFunctions.calculate_society_decline(
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
