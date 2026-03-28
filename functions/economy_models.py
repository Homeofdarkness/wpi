from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PopulationGrowthModel:
    @staticmethod
    def calculate(current_population_count: int) -> float:
        population_in_thousands = current_population_count * 10 ** -3

        if current_population_count > 8 * 10 ** 6:
            return population_in_thousands * 8.77
        if current_population_count >= 5.5 * 10 ** 6:
            return population_in_thousands * 9.87
        if current_population_count >= 2.5 * 10 ** 6:
            return population_in_thousands * 11.77
        if current_population_count >= 10 ** 6:
            return population_in_thousands * 9.87
        return population_in_thousands * 6.87


@dataclass(frozen=True)
class TradePotentialModel:
    @staticmethod
    def calculate(trade_rank: int, trade_efficiency: int) -> float:
        if trade_rank >= 7:
            return 5 + 3 * (trade_rank - 6) * (trade_efficiency / 100)
        return 3 + 2 * (trade_rank - 2) * (trade_efficiency / 100)


@dataclass(frozen=True)
class BranchIncomeModel:
    @staticmethod
    def calculate(branches_count: int, branches_efficiency: float) -> float:
        return branches_count * (branches_efficiency / 10)
