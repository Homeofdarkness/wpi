from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxIncomeModel:
    @staticmethod
    def calculate(
        universal_tax: float,
        excise: float,
        additions: float,
        small_enterprise_tax: float,
        large_enterprise_tax: float,
        small_enterprise_percent: float,
        large_enterprise_count: float,
        population_count: int,
    ) -> float:
        universal_tax_income = 1.9882 * (universal_tax / ((8 + universal_tax) * 10)) * population_count / 1000
        excise_income = excise / (excise + 100) * 2000
        coefficient = population_count * small_enterprise_percent / 1000 - population_count * small_enterprise_percent / 1000 * 0.4
        small_enterprise_tax_income = small_enterprise_tax * coefficient / 3000
        large_enterprise_tax_income = (large_enterprise_tax / 10) * large_enterprise_count
        return universal_tax_income + excise_income + small_enterprise_tax_income + large_enterprise_tax_income + additions


@dataclass(frozen=True)
class MoneyIncomeModel:
    @staticmethod
    def collaboration_factor(agriculture_efficiency: float, civil_efficiency: float) -> float:
        return 1 + ((agriculture_efficiency / 1000) + (civil_efficiency / 1000))

    @staticmethod
    def inflation_factor(inflation: float) -> float:
        return 1 - (inflation / 100)

    @staticmethod
    def agriculture_factor(current_tax_income: float, agriculture_development: float, workers_count: int) -> float:
        economic_involvement = current_tax_income / 100
        hyperbolic_percent = economic_involvement * agriculture_development
        base_addition = hyperbolic_percent / 100
        if workers_count < 1_000_000:
            return base_addition
        return base_addition * (workers_count // 1_000_000)

    @staticmethod
    def boost(stability: int, poor_level: float, jobless_level: float) -> float:
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

        poor_jobless_condition = poor_level < 3 and jobless_level < 10
        poor_jobless_weight = 1 if poor_jobless_condition else 0

        value_80_90 = 1.5 * poor_jobless_weight + 1.17 * (1 - poor_jobless_weight)
        value_above_90 = 1.7 * (1 - int(poor_level > 0 and jobless_level > 0)) + 1.18 * int(poor_level > 0 and jobless_level > 0)
        return (1 - weight_80_90 - weight_above_90) + weight_80_90 * value_80_90 + weight_above_90 * value_above_90

    @staticmethod
    def simple_boost(stability: int) -> float:
        if stability < 20:
            return 0.5
        capped_stability = min(stability, 100)
        return 0.008 * capped_stability + 0.493


@dataclass(frozen=True)
class InfrastructureModel:
    @staticmethod
    def expected_wastes(population_count: int) -> float:
        return (population_count // 10000) * 0.34


@dataclass(frozen=True)
class LogisticsModel:
    @staticmethod
    def expected_wastes(government_wastes: list[float]) -> float:
        return sum(government_wastes) * 0.2
