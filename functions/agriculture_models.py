"""Agriculture, food production, and food-stock formulas."""

from __future__ import annotations

import math

import numpy as np
from numpy.random import Generator

from functions.inbuilt import parabola, safe_div, sigmoid, tanh


WORKERS_PER_FOOD_UNIT = 550.0


def additional_waste_per_worker(security_percent: float) -> float:
    rules = (
        (0, 20, 0.5),
        (20, 40, 0.75),
        (40, 60, 1),
        (60, 80, 1.5),
        (80, 100, 2),
        (100, float("inf"), 3),
    )
    for lower, upper, cost in rules:
        if lower < security_percent <= upper:
            return cost
    return 3


def workers_count(
    population_count: int,
    workers_percent: float,
    workers_redistribution: float,
) -> int:
    points = (
        (0, 5_000),
        (1_000_000, 5_000),
        (10_000_000, 100_000),
        (50_000_000, 275_000),
        (125_000_000, 500_000),
        (200_000_000, 1_000_000),
        (400_000_000, 2_000_000),
        (500_000_000, 2_500_000),
        (float("inf"), 5_000_000),
    )
    # Both values are shown to and entered by the player as percentages.
    # Historically ``workers_percent`` was multiplied as if it were already
    # a 0..1 coefficient, so a perfectly normal input of ``100`` created one
    # hundred times more workers and agricultural expenses.
    workforce_factor = max(float(workers_percent), 0.0) / 100
    redistribution_factor = 1 - min(
        max(float(workers_redistribution), 0.0),
        100.0,
    ) / 100
    for (pop1, workers1), (pop2, workers2) in zip(
        points,
        points[1:],
        strict=False,
    ):
        if pop1 <= population_count <= pop2:
            if pop2 == float("inf"):
                base_workers = workers1
            else:
                progress = (population_count - pop1) / (pop2 - pop1)
                base_workers = workers1 + (workers2 - workers1) * progress
            adjusted_workers = base_workers * redistribution_factor
            return round(adjusted_workers * workforce_factor)
    return 0


def agriculture_wastes(
    workers: int,
    securities: list[float],
    husbandry: float,
    livestock: float,
    others: float,
) -> float:
    technology, fertilizer, tools = securities
    result = (
        workers
        * (
            additional_waste_per_worker(technology)
            + additional_waste_per_worker(fertilizer)
            + additional_waste_per_worker(tools)
        )
        / 10000
    )
    result *= 1 + husbandry * 0.0028
    result *= 1 + livestock * 0.005
    result *= 1 + others * 0.0035
    return result


def agriculture_development(
    securities: list[float],
    workers: int,
    population_count: int,
    biome_richness: float,
    diversity: float,
    husbandry: float,
    livestock: float,
    others: float,
) -> float:
    mean_security = sum(securities) / len(securities) if securities else 0.0
    security_score = tanh(mean_security / 50)
    deviation = (
        abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)
    ) / 3
    balance_bonus = 1.0 / (1.0 + deviation / 30.0)
    workers_ratio = workers / max(population_count, 1)
    diversity_bonus = max(0.0, diversity) / 100.0
    current = (
        security_score
        * balance_bonus
        * (1.0 + workers_ratio)
        * (1.0 + diversity_bonus)
    )
    maximum = 1.3 * (1.0 + biome_richness / 100.0)
    return min(100.0, safe_div(current, maximum) * 100.0)


def approximate_agriculture_efficiency(securities: list[float]) -> float:
    if not securities:
        return 0.0
    return sum(securities) / len(securities)


def approximate_food_security(
    biome_richness: float,
    overproduction_effects: int,
    securities: list[float],
) -> float:
    efficiency = approximate_agriculture_efficiency(securities)
    stock = 0.0
    if efficiency >= 75:
        stock = overproduction_effects * 6 * (1 + biome_richness / 1000)
    return parabola(efficiency / 10, 1, 4, 10) + stock


def approximate_agriculture_development(
    food_security: float,
    securities: list[float],
) -> float:
    efficiency = approximate_agriculture_efficiency(securities)
    value = (food_security * efficiency / 8) / 1000
    result = sigmoid(value) * 100
    if min(efficiency, food_security) < 50:
        return result
    return min(100.0, result * (100 / 77))


def agriculture_efficiency(
    securities: list[float],
    biome_richness: float,
    husbandry: float,
    livestock: float,
    others: float,
    agriculture_deceases: float,
    agriculture_natural_deceases: float,
    workers: int,
    population_count: int,
) -> float:
    mean_security = sum(securities) / len(securities) if securities else 0.0
    security_score = tanh(mean_security / 50)
    deviation = (
        abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)
    ) / 3
    balance_bonus = 1.0 / (1.0 + deviation / 30.0)
    land_productivity = (
        (biome_richness / 100.0) * balance_bonus * security_score
    )
    workers_ratio = workers / max(population_count, 1)
    workforce_factor = 1.0 + workers_ratio * 2.0
    disease_pressure = (
        agriculture_deceases + agriculture_natural_deceases
    ) / 100.0
    equilibrium = (workforce_factor * land_productivity) / (
        0.05 + 0.95 * disease_pressure + 1e-9
    )
    return min(100.0, equilibrium * 100.0)


def food_diversity(
    husbandry: float,
    livestock: float,
    others: float,
    biome_richness: float,
) -> float:
    deviation = abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)
    if deviation > 0:
        deviation /= 3
    return biome_richness - deviation


def food_income(
    workers: int,
    securities: list[float],
    overprotective_effects: float,
    agriculture_deceases: float,
    agriculture_natural_deceases: float,
    environmental_food: int,
) -> float:
    technology, fertilizer, tools = securities
    base = 0.25
    costs_per_worker = (
        additional_waste_per_worker(technology)
        + additional_waste_per_worker(fertilizer)
        + additional_waste_per_worker(tools)
    )
    costs_per_worker -= base * 3
    coefficient = costs_per_worker / base * 1.75
    # Food is expressed in aggregate game units rather than physical tonnes.
    # This scale keeps a fully staffed agricultural sector close to the
    # equilibrium index of 100 for the reference country.
    result = workers / WORKERS_PER_FOOD_UNIT * (coefficient + 10)
    result *= 1 + overprotective_effects / 100
    result *= 1 - agriculture_deceases / 100
    result *= 1 - agriculture_natural_deceases / 100
    return result + environmental_food


def food_consumption(
    population_count: int,
    consumption_factor: float,
) -> float:
    return population_count / 10000 * (2.5 + 0.1 * consumption_factor)


def food_security_index(
    food_produced: float,
    food_consumed: float,
) -> float:
    """Return a unitless coverage index where 100 means equilibrium."""
    if food_consumed <= 0:
        return 100.0
    return max(float(food_produced), 0.0) / food_consumed * 100


def food_supplies(
    current_supplies: float,
    food_surplus: float,
    overstock_percent: float,
    storages_upkeep: float,
) -> float:
    available_storage = storages_upkeep * 39
    new_supplies = current_supplies + max(
        food_surplus - 400,
        food_surplus * overstock_percent / 100,
    )
    return min(new_supplies, available_storage)


def population_underfeed(
    population_count: int,
    food_balance: float,
    biome_richness: float,
    death_probability: float = 0.36,
    rng: Generator | None = None,
) -> int:
    shortage = max(0.0, -food_balance)
    if shortage <= 0:
        return 0
    total_need = population_count / 10000.0 * 2.5
    if total_need <= 0:
        return 0
    shortage_fraction = min(1.0, shortage / total_need)
    at_risk = int(math.ceil(population_count * shortage_fraction))
    climate_reduction = 0.02 * (biome_richness / 10.0)
    effective_probability = float(
        np.clip(
            death_probability * (1.0 - climate_reduction),
            0.12,
            0.36,
        )
    )
    generator = rng or np.random.default_rng()
    deaths = int(generator.binomial(at_risk, effective_probability))
    survival_reduction = 0.05 * (biome_richness / 10.0)
    return max(0, round(deaths * (1.0 - survival_reduction)))
