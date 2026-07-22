"""Public-finance and budget formulas."""

from __future__ import annotations


def tax_income(
    universal_tax: float,
    excise: float,
    additions: float,
    small_enterprise_tax: float,
    large_enterprise_tax: float,
    small_enterprise_percent: float,
    large_enterprise_count: float,
    population_count: int,
) -> float:
    universal = (
        1.9882
        * (universal_tax / ((8 + universal_tax) * 10))
        * population_count
        / 1000
    )
    excise_value = excise / (excise + 100) * 2000
    small_enterprise_base = (
        population_count * small_enterprise_percent / 1000 * 0.6
    )
    small_enterprise = small_enterprise_tax * small_enterprise_base / 3000
    large_enterprise = (large_enterprise_tax / 10) * large_enterprise_count
    return (
        universal
        + excise_value
        + small_enterprise
        + large_enterprise
        + additions
    )


def collaboration_factor(
    agriculture_efficiency: float,
    civil_efficiency: float,
) -> float:
    return 1 + agriculture_efficiency / 1000 + civil_efficiency / 1000


def inflation_factor(inflation: float) -> float:
    return 1 - inflation / 100


def agriculture_factor(
    current_tax_income: float,
    agriculture_development: float,
    workers_count: int,
) -> float:
    economic_involvement = current_tax_income / 100
    hyperbolic_percent = economic_involvement * agriculture_development
    base_addition = hyperbolic_percent / 100
    if workers_count < 1_000_000:
        return base_addition
    return base_addition * (workers_count // 1_000_000)


def stability_income_boost(
    stability: int,
    poor_level: float,
    jobless_level: float,
) -> float:
    if stability < 80:
        weight_80_90 = 0
    elif stability > 90:
        weight_80_90 = 1
    else:
        weight_80_90 = (stability - 80) / 10

    if stability <= 90:
        weight_above_90 = 0
    elif stability > 100:
        weight_above_90 = 1
    else:
        weight_above_90 = (stability - 90) / 10

    good_social_conditions = poor_level < 3 and jobless_level < 10
    social_weight = int(good_social_conditions)
    value_80_90 = 1.5 * social_weight + 1.17 * (1 - social_weight)
    both_above_zero = int(poor_level > 0 and jobless_level > 0)
    value_above_90 = 1.7 * (1 - both_above_zero) + 1.18 * both_above_zero
    return (
        1
        - weight_80_90
        - weight_above_90
        + weight_80_90 * value_80_90
        + weight_above_90 * value_above_90
    )


def simple_stability_income_boost(stability: int) -> float:
    if stability < 20:
        return 0.5
    capped_stability = min(stability, 100)
    return 0.008 * capped_stability + 0.493


def expected_infrastructure_wastes(population_count: int) -> float:
    return (population_count // 10000) * 0.34


def expected_logistic_wastes(government_wastes: list[float]) -> float:
    return sum(government_wastes) * 0.2
