"""State and result types used by the turn engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stats.probability_stats import ProbabilityStats


@dataclass
class WorldState:
    """Complete mutable state of one simulated country."""

    economy: Any
    industry: Any
    agriculture: Any
    inner_politics: Any
    probabilities: ProbabilityStats = field(default_factory=ProbabilityStats)


@dataclass(frozen=True)
class TurnLedger:
    """Auditable revenue and expense totals for a resolved turn."""

    tax_income: float
    trade_income: float
    branches_income: float
    industry_income: float
    science_income: float
    resource_balance: float
    debt_interest: float
    resource_effect_wastes: float
    total_wastes: float
    inflation_factor: float
    mode_income_factor: float = 1.0
    stability_income_factor: float = 1.0

    @property
    def gross_income(self) -> float:
        return (
            self.tax_income
            + self.trade_income
            + self.branches_income
            + self.industry_income
            + self.science_income
            + self.resource_balance
        )

    @property
    def effective_income(self) -> float:
        return (
            self.gross_income
            * self.inflation_factor
            * self.mode_income_factor
            * self.stability_income_factor
        )

    @property
    def net_income(self) -> float:
        return self.effective_income - self.total_wastes


@dataclass
class LogisticParams:
    discount: float = 0.0
    food_security_spotter: float = 0.0
    tax_income_coefficient: float = 0.0
    contentment_spotter: float = 0.0


@dataclass
class CalculationResults:
    logistic_params: LogisticParams
    culture_coefficient: float
    contentment_coefficient_1: float
    contentment_coefficient_2: float
    expected_infrastructure_waste: float
    workers_count: int
    food_balance: float = 0.0


@dataclass(frozen=True)
class PopulationGrowthBreakdown:
    """Auditable demographic inputs and results for one resolved turn."""

    turn_months: int
    population_before: int
    base_growth: float
    resource_adjustment: float
    growth_after_resources: float
    goods_factor: float
    stability_factor: float
    contentment_factor: float
    child_policy_factor: float
    food_security_factor: float
    social_decline_factor: float
    food_diversity_factor: float
    final_growth: float
    decline_deaths: int
    underfeed_deaths: int
    population_after: int

    @property
    def total_factor(self) -> float:
        return (
            self.goods_factor
            * self.stability_factor
            * self.contentment_factor
            * self.child_policy_factor
            * self.food_security_factor
            * self.social_decline_factor
            * self.food_diversity_factor
        )

    @property
    def net_change(self) -> int:
        return self.population_after - self.population_before


@dataclass(frozen=True)
class SkipMoveContext:
    state: WorldState
    waste: float

    @property
    def economy(self):
        return self.state.economy

    @property
    def industry(self):
        return self.state.industry

    @property
    def agriculture(self):
        return self.state.agriculture

    @property
    def inner_politics(self):
        return self.state.inner_politics


@dataclass
class SkipMoveReport:
    mode: str
    turn_months: int
    budget_before: float
    logistic_wastes: float
    total_wastes: float
    logistic_discount: float
    tax_income: float
    trade_income: float
    branches_income: float
    industry_income: float
    science_income: float
    resource_balance: float
    debt_interest: float
    resource_effect_wastes: float
    money_income: float
    budget_after_raw: float
    stability_before: float
    stability_after: float
    stability_policy_adjustment: float
    stability_effect_adjustment: float
    income_boost: float
    budget_after_boost: float
    credit_taken: bool = False
    credit_amount: float = 0.0
    budget_final: float | None = None
    ledger: TurnLedger | None = None
    probabilities: ProbabilityStats | None = None
    population_growth: PopulationGrowthBreakdown | None = None
