"""Economy formulas with no state mutation."""

from __future__ import annotations


def population_growth(population_count: int) -> float:
    population_in_thousands = population_count * 10**-3
    if population_count > 8 * 10**6:
        return population_in_thousands * 8.77
    if population_count >= 5.5 * 10**6:
        return population_in_thousands * 9.87
    if population_count >= 2.5 * 10**6:
        return population_in_thousands * 11.77
    if population_count >= 10**6:
        return population_in_thousands * 9.87
    return population_in_thousands * 6.87


def trade_potential(trade_rank: int, trade_efficiency: int) -> float:
    if trade_rank >= 7:
        return 5 + 3 * (trade_rank - 6) * (trade_efficiency / 100)
    return 3 + 2 * (trade_rank - 2) * (trade_efficiency / 100)


def branches_income(
    branches_count: int,
    branches_efficiency: float,
) -> float:
    return branches_count * (branches_efficiency / 10)
