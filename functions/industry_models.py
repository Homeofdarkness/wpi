from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Tuple

from functions.inbuilt import InbuiltFunctions


@dataclass(frozen=True)
class IndustryCoefficientModel:
    @staticmethod
    def calculate(
        processing_production: float,
        processing_usage: float,
        processing_efficiency: float,
        mean_score: float,
    ) -> float:
        industry_coefficient_base = (mean_score + processing_efficiency) / 2
        industry_coefficient_loss = InbuiltFunctions.euclidean_distance(
            processing_production, processing_usage
        ) / 4
        decrement = 1 - (
            abs(processing_production - processing_usage)
            / max(processing_production, processing_usage)
        )
        return min((industry_coefficient_base - industry_coefficient_loss) * decrement, 100)


@dataclass(frozen=True)
class CivilUsageModel:
    @staticmethod
    def calculate(civil_security: float, tvr1: float, tvr2: float) -> int:
        return round((civil_security + tvr1 + tvr2) / 3)


@dataclass(frozen=True)
class IndustryBasicStatsModel:
    @staticmethod
    def calculate(
        industry_coefficient: float,
        civil_usage: float,
        standardization: float,
    ) -> Tuple[float, float, float]:
        mean_value = (industry_coefficient + civil_usage + (standardization / 1.35)) / 2.5
        safe_civil_usage = max(float(civil_usage), 1e-9)
        std_dev = 100 / safe_civil_usage + 0.2

        possible_values = [random.gauss(mean_value, std_dev) for _ in range(1000)]
        probabilities = [
            InbuiltFunctions.pdf_manual(possible_value, mean_value, std_dev)
            for possible_value in possible_values
        ]

        total_density = sum(probabilities)
        if total_density == 0:
            normalized_probabilities = [1 / len(probabilities)] * len(probabilities) if probabilities else []
        else:
            normalized_probabilities = [p / total_density for p in probabilities]

        payoff, dispersion = InbuiltFunctions.count_proba_params(
            possible_values, normalized_probabilities
        )
        while payoff < dispersion:
            dispersion /= 2

        efficiency = random.uniform(payoff - dispersion, payoff + dispersion)
        max_potential = (industry_coefficient + civil_usage) / 1.8
        expected_wastes = payoff * 0.3

        difference = civil_usage - max_potential
        adjustment = max(0.0, min((difference // 5) * 2, 7))
        efficiency -= adjustment

        return efficiency, max_potential, expected_wastes


@dataclass(frozen=True)
class CivilEfficiencyLogisticModel:
    @staticmethod
    def calculate(logistic: float) -> float:
        if logistic <= 30:
            return 1 + math.log1p(logistic) / 10
        return 1.3 + (logistic - 50) / 100


@dataclass(frozen=True)
class IndustryIncomeModel:
    @staticmethod
    def calculate(
        gov_wastes: list[float],
        civil_usage: float,
        max_potential: float,
        expected_wastes: float,
    ) -> float:
        if not gov_wastes:
            return 0.0
        average_gov_wastes = sum(gov_wastes) / len(gov_wastes)
        adjusted_wastes = max(0.0, average_gov_wastes * 0.3 - expected_wastes)
        safe_civil_usage = max(float(civil_usage), 1e-9)
        return adjusted_wastes * (max_potential / safe_civil_usage)


@dataclass(frozen=True)
class ConsumptionOfGoodsModel:
    @staticmethod
    def calculate(
        population_count: int,
        trade_usage: int,
        trade_efficiency: float,
        tvr1: float,
        tvr2: float,
        base_multiplier: float = 12.0,
    ) -> tuple[float, float]:
        total_goods = tvr1 + tvr2
        goods_per_capita = total_goods / max(1, population_count) * 1000
        tension_raw = (population_count / 1000) / max(1, trade_usage) * base_multiplier - goods_per_capita
        tension = min(100.0, max(0.0, tension_raw))
        base_coefficient = 45.0
        base_consumption = population_count * (base_coefficient / 1000)
        tension_modifier = 1.0 + (tension / 200.0)
        consumption = base_consumption * trade_efficiency * tension_modifier
        return round(consumption / 1000000, 2), round(tension, 1)


@dataclass(frozen=True)
class IndustryOverproductionModel:
    @staticmethod
    def calculate_change(
        tvr1: int,
        tvr2: int,
        consumption: float,
        trade_usage: int,
    ) -> float:
        if trade_usage >= 40:
            return -1 * (trade_usage / 100)
        sign = 1 if tvr1 + tvr2 > consumption else -1
        return sign * 0.5


@dataclass(frozen=True)
class OverproductionModel:
    @staticmethod
    def tax_spotter(overproduction_coefficient: float) -> float:
        return 1 - (overproduction_coefficient / 100)

    @staticmethod
    def trade_income_factor(overproduction_coefficient: float) -> float:
        return 1 - (overproduction_coefficient / 50)
