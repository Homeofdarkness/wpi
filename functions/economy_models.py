"""Economy formulas with no state mutation."""

from __future__ import annotations

from functions.time_models import (
    REFERENCE_TURN_YEARS,
    TURN_YEARS,
)


def population_growth(
    population_count: int,
    years: float = TURN_YEARS,
) -> float:
    """Return demographic growth for the requested turn duration.

    The historical coefficients describe a six-month reference period.  The
    result is scaled so changing the shared turn duration does not silently
    preserve a half-year population flow.
    """
    population_in_thousands = population_count * 10**-3
    if population_count > 8 * 10**6:
        reference_growth = population_in_thousands * 8.77
    elif population_count >= 5.5 * 10**6:
        reference_growth = population_in_thousands * 9.87
    elif population_count >= 2.5 * 10**6:
        reference_growth = population_in_thousands * 11.77
    elif population_count >= 10**6:
        reference_growth = population_in_thousands * 9.87
    else:
        reference_growth = population_in_thousands * 6.87
    return reference_growth * max(float(years), 0.0) / REFERENCE_TURN_YEARS


def trade_potential(trade_rank: int, trade_efficiency: int) -> float:
    if trade_rank >= 7:
        return 5 + 3 * (trade_rank - 6) * (trade_efficiency / 100)
    return 3 + 2 * (trade_rank - 2) * (trade_efficiency / 100)


def branches_income(
    branches_count: int,
    branches_efficiency: float,
) -> float:
    return branches_count * (branches_efficiency / 10)
