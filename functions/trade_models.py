"""Scale-stable trade and foreign-exchange formulas."""

from __future__ import annotations

import math
from dataclasses import dataclass
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


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _smoothstep(start: float, end: float, value: float) -> float:
    if end <= start:
        return 1.0 if value >= end else 0.0
    normalized = _clip((value - start) / (end - start), 0.0, 1.0)
    return normalized * normalized * (3 - 2 * normalized)


def _signed_log1p(value: float, scale: float) -> float:
    safe_scale = max(scale, 1e-6)
    return math.copysign(math.log1p(abs(value) / safe_scale), value)


def legacy_forex_score(features: ForexFeatures) -> float:
    weights = (
        -0.0033199,
        -0.00146846,
        0.00220264,
        -0.00107506,
        -0.00397517,
        0.00255309,
        0.00551992,
        0.00351142,
        0.00120634,
        0.00119143,
        -0.00035796,
        -0.00049678,
        -0.00304799,
    )
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


def normalized_forex_score(features: ForexFeatures) -> float:
    macro_strength = fmean(
        (
            features.stability / 100,
            features.trade_efficiency / 100,
            features.industry_efficiency / 100,
            features.state_apparatus_efficiency / 100,
            features.contentment / 100,
        )
    )
    social_drag = 0.65 * _clip(
        features.poor_level / 30,
        0.0,
        1.0,
    ) + 0.35 * _clip(features.jobless_level / 35, 0.0, 1.0)
    control_bonus = _clip(features.control_balance / 50, -1.0, 1.0)
    trade_bonus = _clip((features.trade_rank - 1) / 8, 0.0, 1.0)
    budget_signal = _signed_log1p(features.budget, 1500)
    income_signal = _signed_log1p(features.income, 120)
    wastes_signal = _signed_log1p(features.wastes, 700)
    macro_balance = income_signal - 0.85 * wastes_signal + 0.35 * budget_signal
    overload_drag = _clip(features.trade_overload / 180, 0.0, 1.2)
    score = (
        1.22
        + 0.95 * macro_strength
        + 0.34 * macro_balance
        + 0.18 * trade_bonus
        + 0.12 * control_bonus
        - 0.58 * social_drag
        - 0.22 * overload_drag
    )
    return _clip(score, 1.0, 4.5)


def forex_course(features: ForexFeatures) -> float:
    raw_legacy_score = legacy_forex_score(features)
    legacy_score = max(raw_legacy_score, 1.0)
    normalized_score = normalized_forex_score(features)
    scale_pressure = max(
        _smoothstep(300, 2000, abs(features.income)),
        _smoothstep(1500, 10000, abs(features.budget)),
    )
    floor_pressure = _smoothstep(0.0, 2.5, 1.0 - raw_legacy_score)
    normalized_weight = _clip(
        0.75 + 0.15 * scale_pressure + 0.10 * floor_pressure,
        0.75,
        0.97,
    )
    result = (
        legacy_score * (1.0 - normalized_weight)
        + normalized_score * normalized_weight
    )
    return round(_clip(result, 1.0, 5.0), 4)


def allegorization_trade_factor(percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError(
            f"Процент должен быть в диапазоне [0, 100], получен: {percent}"
        )
    if percent == 0:
        return 0.97
    if percent < 21:
        return 1 + percent / 200
    if percent < 81:
        return 1 + (percent - 20) / 100
    return 1 + (percent - 20) / 75


def allegorization_economy_factor(percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError(
            f"Процент должен быть в диапазоне [0, 100], получен: {percent}"
        )
    if percent == 0:
        return 1.03
    if percent < 21:
        return 1
    if percent < 81:
        return 1 - (1.8 + (percent - 21) * 0.1) / 100
    return 1 + (percent - 20) / 500


def trade_income(
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
    safe_potential = max(float(trade_potential or 0), 1.0)
    safe_usage = max(int(trade_usage), 0)
    safe_efficiency = max(float(trade_efficiency), 0.0)
    safe_wastes = max(float(trade_wastes), 0.0)
    valgery_factor = _clip(float(valgery) / 100.0, 0.0, 1.0)
    safe_forex = max(float(forex or 1.0), 0.2)
    load_ratio = safe_usage / safe_potential
    overload_blend = _smoothstep(0.95, 1.35, load_ratio)
    overload_ratio = max(0.0, load_ratio - 1.0)
    quality_normal = (
        2.6 * high_quality_percent
        + 1.8 * mid_quality_percent
        + low_quality_percent
    )
    quality_overloaded = (
        2.25 * high_quality_percent
        + 1.55 * mid_quality_percent
        + 0.72 * low_quality_percent
    )
    quality_factor = (
        quality_normal * (1 - overload_blend)
        + quality_overloaded * overload_blend
    )
    route_component = safe_usage / (38.0 + 20.0 * overload_blend)
    efficiency_factor = safe_efficiency / (100.0 + 45.0 * overload_blend)
    result = route_component + quality_factor * efficiency_factor - safe_wastes
    if overload_ratio > 0:
        overload_penalty = 1.0 / (1.0 + 0.85 * overload_ratio)
        currency_factor = valgery_factor + 1.0 / safe_forex * (
            1.0 - valgery_factor
        )
        forex_blend = _smoothstep(0.0, 0.6, overload_ratio)
        result *= overload_penalty * (
            1.0 + (currency_factor - 1.0) * forex_blend
        )
    return round(max(result, 0.0), 4)
