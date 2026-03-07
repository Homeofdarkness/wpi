from __future__ import annotations

from typing import Any


def budget_getter(model: Any) -> tuple[float, float]:
    current = getattr(model, "current_budget", 0.0)
    prev = getattr(model, "prev_budget", current)
    if prev is None:
        prev = current
    return current, prev


def trade_usage_load(model: Any) -> int:
    method = getattr(model, "trade_usage_load", None)
    if callable(method):
        return method()
    return 0


def available_trade_paths(model: Any) -> int:
    trade_rank = getattr(model, "trade_rank", 1) or 1
    return 5 + 3 * (trade_rank - 1)


def food_security_getter(model: Any) -> tuple[float, bool]:
    value = getattr(model, "food_security", 0.0)
    is_negative = getattr(model, "_is_negative_food_security", False)
    is_negative = getattr(model, "is_negative_food_security", is_negative)
    return value, bool(is_negative)
