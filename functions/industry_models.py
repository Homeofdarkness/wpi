"""Industry and consumer-goods formulas."""

from __future__ import annotations

import math
from collections.abc import Mapping

from functions.inbuilt import distance_from_ideal


INDUSTRIAL_READINESS_WEIGHTS = {
    "technology": 0.20,
    "personnel": 0.20,
    "infrastructure": 0.20,
    "resources": 0.15,
    "institutions": 0.10,
    "market": 0.15,
}


def _score(value: float) -> float:
    return min(max(float(value), 0.0), 100.0)


def technology_readiness(
    processing_efficiency: float,
    standardization: float,
) -> float:
    """Technology and repeatability of industrial processes."""
    return _score(
        0.55 * _score(processing_efficiency) + 0.45 * _score(standardization)
    )


def personnel_readiness(
    qualification: float,
    education: float,
    knowledge: float,
    workforce_coverage: float = 100.0,
) -> float:
    """Skills available both inside industry and in wider society."""
    return _score(
        0.35 * _score(qualification)
        + 0.25 * _score(education)
        + 0.20 * _score(knowledge)
        + 0.20 * _score(workforce_coverage)
    )


def infrastructure_readiness(
    logistic: float,
    infrastructure_coverage: float,
) -> float:
    """Combine logistics and funded infrastructure as equal bottlenecks."""
    return math.sqrt(_score(logistic) * _score(infrastructure_coverage))


def institutional_readiness(
    state_apparatus_efficiency: float,
    corruption_level: float,
) -> float:
    return _score(
        0.60 * _score(state_apparatus_efficiency)
        + 0.40 * (100.0 - _score(corruption_level))
    )


def market_readiness(
    first_goods_security: float,
    second_goods_security: float,
    trade_efficiency: float,
    poor_level: float,
) -> float:
    return _score(
        0.35 * _score(first_goods_security)
        + 0.35 * _score(second_goods_security)
        + 0.20 * _score(trade_efficiency)
        + 0.10 * (100.0 - _score(poor_level))
    )


def industrial_readiness(
    components: Mapping[str, float],
    *,
    weights: Mapping[str, float] = INDUSTRIAL_READINESS_WEIGHTS,
) -> float:
    """Weighted geometric readiness score on a 0..100 scale."""
    if set(components) != set(weights):
        missing = sorted(set(weights) - set(components))
        extra = sorted(set(components) - set(weights))
        raise ValueError(
            "Компоненты промышленной готовности не совпадают с весами: "
            f"не хватает {missing or 'ничего'}, лишние {extra or 'ничего'}"
        )
    total_weight = sum(float(weight) for weight in weights.values())
    if total_weight <= 0:
        raise ValueError("Сумма весов промышленной готовности должна быть > 0")
    result = 1.0
    for name, weight in weights.items():
        normalized = _score(components[name]) / 100.0
        normalized_weight = float(weight) / total_weight
        if normalized <= 0 and normalized_weight > 0:
            return 0.0
        result *= normalized**normalized_weight
    return _score(result * 100.0)


def industrial_strain(readiness: float) -> float:
    """Inverse pressure score; it is derived, not accumulated state."""
    return 100.0 - _score(readiness)


def industrial_income_factor(strain: float) -> float:
    """At maximum strain, industrial income is reduced by at most 25%."""
    return 1.0 - 0.25 * _score(strain) / 100.0


def industry_coefficient(
    processing_production: float,
    processing_usage: float,
    processing_efficiency: float,
    mean_score: float,
) -> float:
    base = (mean_score + processing_efficiency) / 2
    ideal_distance_loss = (
        distance_from_ideal(
            processing_production,
            processing_usage,
        )
        / 4
    )
    maximum = max(processing_production, processing_usage)
    if maximum <= 0:
        return 0.0
    balance = 1 - abs(processing_production - processing_usage) / maximum
    return min(max((base - ideal_distance_loss) * balance, 0.0), 100.0)


def civil_usage(
    civil_security: float,
    first_goods_security: float,
    second_goods_security: float,
) -> int:
    return round(
        (civil_security + first_goods_security + second_goods_security) / 3
    )


def goods_coefficient(goods_count: int) -> float:
    if goods_count >= 100:
        return 1.1
    return 0.004 * goods_count + 0.66


def industry_basic_stats(
    coefficient: float,
    usage: float,
    standardization: float,
) -> tuple[float, float, float]:
    mean_value = (coefficient + usage + standardization / 1.35) / 2.5
    efficiency = mean_value
    max_potential = (coefficient + usage) / 1.8
    expected_wastes = mean_value * 0.3
    difference = usage - max_potential
    adjustment = max(0.0, min((difference // 5) * 2, 7))
    efficiency -= adjustment
    return efficiency, max_potential, expected_wastes


def civil_efficiency_logistic_factor(logistic: float) -> float:
    safe_logistic = max(logistic, 0.0)
    base = 1 + math.log1p(min(safe_logistic, 30)) / 10
    return base + max(0.0, safe_logistic - 30) / 100


def industry_income(
    gov_wastes: list[float],
    usage: float,
    max_potential: float,
    expected_wastes: float,
) -> float:
    if not gov_wastes:
        return 0.0
    average_gov_wastes = sum(gov_wastes) / len(gov_wastes)
    adjusted_wastes = max(
        0.0,
        average_gov_wastes * 0.3 - expected_wastes,
    )
    safe_usage = max(float(usage), 1e-9)
    return adjusted_wastes * (max_potential / safe_usage)


def consumption_of_goods(
    population_count: int,
    trade_usage: int,
    trade_efficiency: float,
    first_goods_security: float,
    second_goods_security: float,
    base_multiplier: float = 12.0,
) -> tuple[float, float]:
    total_goods = first_goods_security + second_goods_security
    goods_per_capita = total_goods / max(1, population_count) * 1000
    tension_raw = (
        population_count / 1000 / max(1, trade_usage) * base_multiplier
        - goods_per_capita
    )
    tension = min(100.0, max(0.0, tension_raw))
    base_consumption = population_count * 45.0 / 1000
    tension_modifier = 1.0 + tension / 200.0
    consumption = base_consumption * trade_efficiency * tension_modifier
    return round(consumption / 1_000_000, 2), round(tension, 1)


def industry_overproduction_change(
    first_goods_security: int,
    second_goods_security: int,
    consumption: float,
    trade_usage: int,
) -> float:
    if trade_usage >= 40:
        return -(trade_usage / 100)
    sign = (
        1 if first_goods_security + second_goods_security > consumption else -1
    )
    return sign * 0.5


def overproduction_tax_factor(overproduction: float) -> float:
    """Return the economy-wide tax modifier for overproduction.

    Overproduction is a pressure indicator, not the share of the entire
    economy that disappears.  The old linear formula could erase 99% of all
    taxes at a value of 99, although most taxes are unrelated to unsold civil
    goods.  Keep the existing direction of influence but cap the aggregate
    tax loss at 20%.
    """
    pressure = min(max(float(overproduction), 0.0), 100.0) / 100
    return max(0.8, 1 - pressure)
