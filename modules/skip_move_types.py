"""Common datatypes used during skip-move calculations.

The project has several game modes with slightly different rules and stats.
To keep the skip-move engine extensible and avoid duplication, we centralize
shared dataclasses here.

This module is intentionally dependency-light to avoid circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LogisticParams:
    """Intermediate parameters derived from logistics and internal politics."""

    discount: float = 0.0
    food_security_spotter: float = 0.0
    tax_income_coefficient: float = 0.0
    contentment_spotter: int = 0


@dataclass
class CalculationResults:
    """Results that are reused across multiple calculation steps."""

    logistic_params: LogisticParams
    culture_coefficient: float
    contentment_coefficient_1: float
    contentment_coefficient_2: float
    expected_infrastructure_waste: float


@dataclass
class SkipMoveContext:
    """A lightweight bag of references for rules implementations."""

    economy: Any
    industry: Any
    agriculture: Any
    inner_politics: Any
    waste: float
    in_move: Any


@dataclass
class SkipMoveReport:
    """A structured summary of what happened during a skip-move.

    This is intentionally verbose because it makes debugging and unit testing
    much easier than scraping `print()` output.
    """

    mode: str
    budget_before: float

    # intermediate and final values
    logistic_wastes: float
    total_wastes: float
    logistic_discount: float

    tax_income: float
    trade_income: float
    branches_income: float
    industry_income: float
    science_income: float

    money_income: float

    budget_after_raw: float
    stability_after: float
    income_boost: float
    budget_after_boost: float

    credit_taken: bool = False
    credit_amount: float = 0.0
    budget_final: Optional[float] = None
