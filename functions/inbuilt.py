import math
from typing import Tuple


class InbuiltFunctions:

    @staticmethod
    def sigmoid(n: float) -> float:
        return 1 / (1 + math.exp(-n))

    @staticmethod
    def tanh(n: float) -> float:
        return (math.exp(n) - math.exp(-n)) / (math.exp(n) + math.exp(-n))

    @staticmethod
    def euclidean_distance(a: float, b: float) -> float:
        return ((100 - a) ** 2 + (100 - b) ** 2) ** 0.5

    @staticmethod
    def pdf_manual(x: float, mu: float, sigma: float) -> float:
        coefficient = 1 / (sigma * math.sqrt(2 * math.pi))
        exponent = math.exp(-((x - mu) ** 2) / (2 * sigma ** 2))

        return coefficient * exponent

    @staticmethod
    def count_proba_params(
            points: list,
            probabilities: list
    ) -> Tuple[float, float]:
        expected_value = sum(x * p for x, p in zip(points, probabilities))
        variance = sum(((x - expected_value) ** 2) * p for x, p in
                       zip(points, probabilities))

        return expected_value, variance

    @staticmethod
    def parabola(x: float, a: float = 1, b: float = 1, c: float = 1) -> float:
        return a * x ** 2 + b * x + c

    @staticmethod
    def gaussian_kernel(x: float) -> float:
        inverted_root = 1 / math.sqrt(2 * math.pi)
        return inverted_root * math.exp(-((x - 1) ** 2) / (2 * x ** 2))
