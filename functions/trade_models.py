from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean


@dataclass(frozen=True)
class ForexFeatures:
    stability: int
    income: float
    wastes: float
    budget: float
    trade_rank: int
    trade_efficiency: float
    trade_overload: float
    industry_efficiency: float
    state_apparatus_efficiency: int
    contentment: int
    poor_level: float
    jobless_level: float
    control_balance: float


class TradeModels:
    """Trade-related helper models.

    The project historically used a single linear forex formula with raw feature
    magnitudes. That made the output fragile: large budget/income values could
    instantly collapse the result to the hard floor of ``1``.

    This module keeps the legacy signal but blends it with a normalized,
    ML-inspired ensemble scorer that is scale-stable and monotonic for the most
    important trade signals.
    """

    @staticmethod
    def _clip(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @classmethod
    def _smoothstep(cls, start: float, end: float, value: float) -> float:
        if end <= start:
            return 1.0 if value >= end else 0.0
        x = cls._clip((value - start) / (end - start), 0.0, 1.0)
        return x * x * (3 - 2 * x)

    @staticmethod
    def _signed_log1p(value: float, scale: float) -> float:
        scale = max(scale, 1e-6)
        return math.copysign(math.log1p(abs(value) / scale), value)

    @staticmethod
    def legacy_forex_score(features: ForexFeatures) -> float:
        weights = [-0.0033199, -0.00146846, 0.00220264, -0.00107506,
                   -0.00397517, 0.00255309, 0.00551992, 0.00351142,
                   0.00120634, 0.00119143, -0.00035796, -0.00049678,
                   -0.00304799]
        bias = 0.7665364725212972
        return (
            features.stability * weights[0]
            + features.income * weights[1]
            + features.wastes * weights[2]
            + features.budget * weights[3]
            + features.trade_rank * weights[4]
            + features.trade_efficiency * weights[5]
            + features.trade_overload * weights[6]
            + features.industry_efficiency * weights[7]
            + features.state_apparatus_efficiency * weights[8]
            + features.contentment * weights[9]
            + features.poor_level * weights[10]
            + features.jobless_level * weights[11]
            + features.control_balance * weights[12]
            + bias
        )

    @classmethod
    def normalized_forex_score(cls, features: ForexFeatures) -> float:
        macro_strength = fmean([
            features.stability / 100,
            features.trade_efficiency / 100,
            features.industry_efficiency / 100,
            features.state_apparatus_efficiency / 100,
            features.contentment / 100,
        ])

        social_drag = (
            0.65 * cls._clip(features.poor_level / 30, 0.0, 1.0)
            + 0.35 * cls._clip(features.jobless_level / 35, 0.0, 1.0)
        )
        control_bonus = cls._clip(features.control_balance / 50, -1.0, 1.0)
        trade_bonus = cls._clip((features.trade_rank - 1) / 8, 0.0, 1.0)

        budget_signal = cls._signed_log1p(features.budget, 1500)
        income_signal = cls._signed_log1p(features.income, 120)
        wastes_signal = cls._signed_log1p(features.wastes, 700)
        macro_balance = income_signal - 0.85 * wastes_signal + 0.35 * budget_signal

        overload_drag = cls._clip(features.trade_overload / 180, 0.0, 1.2)

        score = (
            1.22
            + 0.95 * macro_strength
            + 0.34 * macro_balance
            + 0.18 * trade_bonus
            + 0.12 * control_bonus
            - 0.58 * social_drag
            - 0.22 * overload_drag
        )
        return cls._clip(score, 1.0, 4.5)

    @classmethod
    def calculate_forex_course(cls, features: ForexFeatures) -> float:
        raw_legacy_score = cls.legacy_forex_score(features)
        legacy_score = max(raw_legacy_score, 1.0)
        normalized_score = cls.normalized_forex_score(features)

        # Adaptive blending: once the raw scale of budget/income becomes large,
        # trust the normalized model more because the legacy linear model is
        # known to saturate to the hard floor. We also heavily downweight the
        # legacy branch when it already collapsed below the valid floor.
        scale_pressure = max(
            cls._smoothstep(300, 2000, abs(features.income)),
            cls._smoothstep(1500, 10000, abs(features.budget)),
        )
        floor_pressure = cls._smoothstep(0.0, 2.5, 1.0 - raw_legacy_score)
        normalized_weight = 0.75 + 0.15 * scale_pressure + 0.10 * floor_pressure
        normalized_weight = cls._clip(normalized_weight, 0.75, 0.97)
        legacy_weight = 1.0 - normalized_weight

        result = legacy_score * legacy_weight + normalized_score * normalized_weight
        return round(cls._clip(result, 1.0, 5.0), 4)


    @staticmethod
    def calculate_allegorization_trade_factor(allegorization_percent: float) -> float:
        if not 0 <= allegorization_percent <= 100:
            raise ValueError(
                f"Процент должен быть в диапазоне [0, 100], получен: {allegorization_percent}"
            )
        rules = [
            (lambda x: x == 0, lambda x: 0.97),
            (lambda x: x < 21, lambda x: 1 + x / 200),
            (lambda x: x < 81, lambda x: 1 + (x - 20) / 100),
            (lambda x: True, lambda x: 1 + (x - 20) / 75),
        ]
        for condition, calculation in rules:
            if condition(allegorization_percent):
                return calculation(allegorization_percent)
        raise AssertionError("Unreachable allegorization branch")

    @staticmethod
    def calculate_allegorization_economy_factor(allegorization_percent: float) -> float:
        if not 0 <= allegorization_percent <= 100:
            raise ValueError(
                f"Процент должен быть в диапазоне [0, 100], "
                f"получен: {allegorization_percent}"
            )
        rules = [
            (lambda x: x == 0, lambda x: 1.03),
            (lambda x: x < 21, lambda x: 1),
            (lambda x: x < 81, lambda x: 1 - (1.8 + (x - 21) * 0.1) / 100),
            (lambda x: True, lambda x: 1 + (x - 20) / 500),
        ]
        for condition, calculation in rules:
            if condition(allegorization_percent):
                return calculation(allegorization_percent)
        raise AssertionError("Unreachable allegorization branch")

    @classmethod
    def calculate_trade_income(
        cls,
        trade_potential: float,
        trade_usage: int,
        trade_efficiency: float,
        trade_wastes: float,
        high_quality_percent: float,
        mid_quality_percent: float,
        low_quality_percent: float,
        forex: float,
        valgery: float,
    ) -> float:
        trade_potential = max(float(trade_potential or 0), 1.0)
        trade_usage = max(int(trade_usage), 0)
        trade_efficiency = max(float(trade_efficiency), 0.0)
        trade_wastes = max(float(trade_wastes), 0.0)
        valgery_factor = cls._clip(float(valgery) / 100.0, 0.0, 1.0)
        safe_forex = max(float(forex or 1.0), 0.2)

        load_ratio = trade_usage / trade_potential
        overload_blend = cls._smoothstep(0.95, 1.35, load_ratio)
        overload_ratio = max(0.0, load_ratio - 1.0)

        quality_normal = 2.6 * high_quality_percent + 1.8 * mid_quality_percent + low_quality_percent
        quality_overloaded = 2.25 * high_quality_percent + 1.55 * mid_quality_percent + 0.72 * low_quality_percent
        quality_factor = quality_normal * (1 - overload_blend) + quality_overloaded * overload_blend

        route_divisor = 38.0 + 20.0 * overload_blend
        route_component = trade_usage / route_divisor

        efficiency_divisor = 100.0 + 45.0 * overload_blend
        efficiency_factor = trade_efficiency / efficiency_divisor

        base_income = route_component + quality_factor * efficiency_factor - trade_wastes

        if overload_ratio > 0:
            overload_penalty = 1.0 / (1.0 + 0.85 * overload_ratio)
            currency_factor = valgery_factor + (1.0 / safe_forex) * (1.0 - valgery_factor)
            forex_blend = cls._smoothstep(0.0, 0.6, overload_ratio)
            base_income *= overload_penalty * (1.0 + (currency_factor - 1.0) * forex_blend)

        return round(max(base_income, 0.0), 4)
