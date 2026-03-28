from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List

import numpy as np

from functions.inbuilt import InbuiltFunctions


@dataclass(frozen=True)
class AdditionalWastesModel:
    @staticmethod
    def calculate(security_percent: float) -> float:
        calculation_rules = [
            {"gt": 0, "le": 20, "count_per_worker": 0.5},
            {"gt": 20, "le": 40, "count_per_worker": 0.75},
            {"gt": 40, "le": 60, "count_per_worker": 1},
            {"gt": 60, "le": 80, "count_per_worker": 1.5},
            {"gt": 80, "le": 100, "count_per_worker": 2},
            {"gt": 100, "le": float('inf'), "count_per_worker": 3},
        ]
        for rule in calculation_rules:
            if rule["gt"] < security_percent <= rule["le"]:
                return rule["count_per_worker"]
        return 3


@dataclass(frozen=True)
class WorkersCountModel:
    @staticmethod
    def calculate(
        population_count: int,
        workers_percent: float,
        workers_redistribution: float,
    ) -> int:
        points = [
            (0, 5_000),
            (1_000_000, 5_000),
            (10_000_000, 100_000),
            (50_000_000, 275_000),
            (125_000_000, 500_000),
            (200_000_000, 1_000_000),
            (400_000_000, 2_000_000),
            (500_000_000, 2_500_000),
            (float("inf"), 5_000_000),
        ]
        redistribution_factor = 1 - workers_redistribution / 100
        for i in range(len(points) - 1):
            pop1, workers1 = points[i]
            pop2, workers2 = points[i + 1]
            if pop1 <= population_count <= pop2:
                if pop2 == float("inf"):
                    base_workers = workers1
                else:
                    t = (population_count - pop1) / (pop2 - pop1)
                    base_workers = workers1 + (workers2 - workers1) * t
                adjusted_workers = base_workers * redistribution_factor
                return round(adjusted_workers * workers_percent)
        return 0


@dataclass(frozen=True)
class AgricultureWastesModel:
    @staticmethod
    def calculate(
        workers_count: int,
        securities: List[float],
        husbandry: float,
        livestock: float,
        others: float,
    ) -> float:
        technology_percent, fertilizer_percent, tool_percent = securities
        workers_wastes = workers_count * (
            AdditionalWastesModel.calculate(technology_percent)
            + AdditionalWastesModel.calculate(fertilizer_percent)
            + AdditionalWastesModel.calculate(tool_percent)
        ) / 10000
        workers_wastes *= (1 + husbandry * 0.0028)
        workers_wastes *= (1 + livestock * 0.005)
        workers_wastes *= (1 + others * 0.0035)
        return workers_wastes


@dataclass(frozen=True)
class AgricultureDevelopmentModel:
    @staticmethod
    def calculate(
        securities: List[float],
        workers_count: int,
        population_count: int,
        biome_richness: float,
        food_diversity: float,
        husbandry: float,
        livestock: float,
        others: float,
    ) -> float:
        mean_security = sum(securities) / len(securities) if securities else 0.0
        s_score = InbuiltFunctions.tanh(mean_security / 50)
        deviation = (abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)) / 3
        balance_bonus = 1.0 / (1.0 + deviation / 30.0)
        workers_ratio = workers_count / max(population_count, 1)
        diversity_bonus = max(0.0, food_diversity) / 100.0
        current = s_score * balance_bonus * (1.0 + workers_ratio) * (1.0 + diversity_bonus)
        max_possible = 1.0 * 1.0 * 1.3 * (1.0 + biome_richness / 100.0)
        return min(100.0, InbuiltFunctions.safe_div(current, max_possible) * 100.0)

    @staticmethod
    def approximate_efficiency(securities: List[float]) -> float:
        if not securities:
            return 0.0
        return sum(securities) / len(securities)

    @classmethod
    def approximate_food_security(
        cls,
        biome_richness: float,
        overproduction_effects: int,
        securities: List[float],
    ) -> float:
        agriculture_efficiency = cls.approximate_efficiency(securities)
        stock = (overproduction_effects * 6 * (1 + biome_richness / 1000)) if agriculture_efficiency >= 75 else 0
        return InbuiltFunctions.parabola(agriculture_efficiency / 10, 1, 4, 10) + stock

    @classmethod
    def approximate_development(
        cls,
        approximate_food_security: float,
        securities: List[float],
    ) -> float:
        agriculture_efficiency = cls.approximate_efficiency(securities)
        value = (approximate_food_security * agriculture_efficiency / 8) / 1000
        sigmoid_result = InbuiltFunctions.sigmoid(value) * 100
        if min(agriculture_efficiency, approximate_food_security) < 50:
            return sigmoid_result
        return min(100.0, sigmoid_result * (100 / 77))


@dataclass(frozen=True)
class AgricultureEfficiencyModel:
    @staticmethod
    def calculate(
        securities: List[float],
        biome_richness: float,
        husbandry: float,
        livestock: float,
        others: float,
        agriculture_deceases: float,
        agriculture_natural_deceases: float,
        workers_count: int,
        population_count: int,
    ) -> float:
        mean_security = sum(securities) / len(securities) if securities else 0.0
        s_score = InbuiltFunctions.tanh(mean_security / 50)
        deviation = (abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)) / 3
        balance_bonus = 1.0 / (1.0 + deviation / 30.0)
        p_land = (biome_richness / 100.0) * balance_bonus * s_score
        workers_ratio = workers_count / max(population_count, 1)
        r = 1.0 + workers_ratio * 2.0
        d = (agriculture_deceases + agriculture_natural_deceases) / 100.0
        base_decay = 0.05
        disease_factor = 0.95
        e_star = (r * p_land) / (base_decay + disease_factor * d + 1e-9)
        return min(100.0, e_star * 100.0)


@dataclass(frozen=True)
class FoodModel:
    @staticmethod
    def diversity(husbandry: float, livestock: float, others: float, biome_richness: float) -> float:
        base = biome_richness
        standard_deviation = abs(husbandry - 40) + abs(livestock - 40) + abs(others - 20)
        if standard_deviation > 0:
            standard_deviation /= 3
        return base - standard_deviation

    @staticmethod
    def income(
        workers_count: int,
        securities: List[float],
        overprotective_effects: float,
        agriculture_deceases: float,
        agriculture_natural_deceases: float,
        environmental_food: int,
    ) -> float:
        technology_percent, fertilizer_percent, tool_percent = securities
        base = 0.25
        costs_per_workers = (
            AdditionalWastesModel.calculate(technology_percent)
            + AdditionalWastesModel.calculate(fertilizer_percent)
            + AdditionalWastesModel.calculate(tool_percent)
        )
        costs_per_workers -= base * 3
        coefficient = (costs_per_workers / base) * 1.75
        food_income = (workers_count / 10000) * (coefficient + 10)
        food_income *= (1 + (overprotective_effects / 100))
        food_income *= (1 - (agriculture_deceases / 100))
        food_income *= (1 - (agriculture_natural_deceases / 100))
        return food_income + environmental_food

    @staticmethod
    def consumption(population_count: int, consumption_factor: float) -> float:
        return (population_count / 10000) * (2.5 + (0.1 * consumption_factor))

    @staticmethod
    def security(food_income: float, food_consumption: float) -> float:
        return food_income - food_consumption

    @staticmethod
    def supplies(
        current_food_supplies: float,
        food_security: float,
        overstock_percent: float,
        storages_upkeep: float,
    ) -> float:
        food_supplies = current_food_supplies
        available_storage = storages_upkeep * 39
        food_supplies += max(food_security - 400, food_security * overstock_percent)
        return min(food_supplies, available_storage)

    @staticmethod
    def underfeed(
        population_count: int,
        food_security: float,
        biome_richness: float,
        death_probability: float = 0.36,
    ) -> int:
        shortage = max(0.0, -food_security)
        if shortage <= 0:
            return 0
        total_need = (population_count / 10000.0) * 2.5
        shortage_fraction = min(1.0, shortage / total_need)
        at_risk = int(math.ceil(population_count * shortage_fraction))
        reduction = 0.02 * (biome_richness / 10.0)
        p_eff = float(np.clip(death_probability * (1.0 - reduction), 0.12, 0.36))
        rng = np.random.default_rng()
        deaths = int(rng.binomial(at_risk, p_eff))
        reduction = 0.05 * (biome_richness / 10.0)
        return max(0, round(deaths * (1.0 - reduction)))
