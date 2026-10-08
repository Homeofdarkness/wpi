"""Pure balance formulas for optional detailed trade deals."""

from __future__ import annotations


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def route_fulfillment_factor(
    trade_efficiency: float,
    trade_usage: float,
    trade_potential: float,
) -> float:
    """Return the deliverable share after reliability and congestion.

    Even a weak trade system can move part of a contracted shipment.  The
    steepest penalty begins only after the country's available routes are
    overloaded.
    """

    efficiency = _clip(trade_efficiency / 100.0, 0.0, 1.0)
    reliability = 0.55 + 0.45 * efficiency
    potential = max(float(trade_potential or 0.0), 1.0)
    load = max(float(trade_usage), 0.0) / potential
    congestion = 1.0 / (1.0 + 0.75 * max(load - 1.0, 0.0))
    return _clip(reliability * congestion, 0.0, 1.0)


def currency_settlement_factor(forex: float, valgery: float) -> float:
    """Share of configured money retained after currency settlement."""

    protected_share = _clip(valgery / 100.0, 0.0, 1.0)
    safe_forex = max(float(forex or 1.0), 0.2)
    return protected_share + (1.0 - protected_share) / safe_forex


def export_quality_factor(
    high_quality: float,
    middle_quality: float,
    low_quality: float,
) -> float:
    """Price modifier for monetary exports; a normalized mix equals 1."""

    high = max(float(high_quality), 0.0)
    middle = max(float(middle_quality), 0.0)
    low = max(float(low_quality), 0.0)
    total = high + middle + low
    if total <= 0:
        return 1.0
    return (1.25 * high + middle + 0.75 * low) / total
