"""Small numerical helpers shared by domain formulas."""

from __future__ import annotations

import math


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def tanh(value: float) -> float:
    return math.tanh(value)


def distance_from_ideal(first: float, second: float) -> float:
    """Distance from the ideal ``(100, 100)`` production point."""
    return math.hypot(100 - first, 100 - second)


def normal_pdf(value: float, mean: float, sigma: float) -> float:
    coefficient = 1 / (sigma * math.sqrt(2 * math.pi))
    exponent = math.exp(-((value - mean) ** 2) / (2 * sigma**2))
    return coefficient * exponent


def weighted_moments(
    points: list[float],
    probabilities: list[float],
) -> tuple[float, float]:
    pairs = list(zip(points, probabilities, strict=True))
    expected_value = sum(value * probability for value, probability in pairs)
    variance = sum(
        ((value - expected_value) ** 2) * probability
        for value, probability in pairs
    )
    return expected_value, variance


def parabola(
    value: float,
    a: float = 1,
    b: float = 1,
    c: float = 1,
) -> float:
    return a * value**2 + b * value + c


def gaussian_kernel(value: float) -> float:
    if value == 0:
        return 0.0
    inverted_root = 1 / math.sqrt(2 * math.pi)
    return inverted_root * math.exp(-((value - 1) ** 2) / (2 * value**2))


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator != 0 else 0.0
