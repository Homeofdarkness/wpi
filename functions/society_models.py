from __future__ import annotations

from dataclasses import dataclass
import random

from functions.inbuilt import InbuiltFunctions


@dataclass(frozen=True)
class CulturalCoefficientModel:
    @staticmethod
    def calculate(cultural_level: int, egocentrism_development: float) -> float:
        return max(0.0, 0.025 * cultural_level - 0.105 + (egocentrism_development / 100))


@dataclass(frozen=True)
class ContentmentModel:
    @staticmethod
    def coefficients(contentment: int) -> tuple[float, float]:
        return 0.004 * contentment + 0.754, 0.005 * contentment + 0.528


@dataclass(frozen=True)
class SuccessChanceModel:
    @staticmethod
    def calculate(knowledge_level: float, education_level: float, erudition_will: float) -> float:
        safe_erudition_will = max(float(erudition_will), 1e-9)
        return random.gauss(knowledge_level + education_level, (safe_erudition_will / 10) ** -1) // 2


@dataclass(frozen=True)
class SocietyDeclineModel:
    @staticmethod
    def calculate(
        contentment: int,
        government_trust: float,
        many_children_traditions: int,
        sexual_asceticism: float,
        egocentrism_development: float,
        education_level: float,
        erudition_will: int,
        cultural_level: int,
        violence_tendency: float,
        unemployment_rate: float,
        grace_of_the_highest: int,
        commitment_to_cause: int,
        departure_from_truths: int,
    ) -> float:
        positive_factors = (
            contentment * 0.05
            + government_trust * 0.15
            + many_children_traditions * 0.05
            + sexual_asceticism * 0.25
            + education_level * 0.05
            + erudition_will * 0.075
            + cultural_level * 0.05
            + grace_of_the_highest * 0.7
            + commitment_to_cause * 0.15
        )
        negative_factors = (
            violence_tendency * 0.5
            + egocentrism_development * 0.3
            + unemployment_rate * 0.3
            + departure_from_truths * 1.1
        )
        societal_decline = max(0.0, negative_factors - positive_factors)
        societal_decline = min(societal_decline, 100)
        return round(societal_decline, 2)


@dataclass(frozen=True)
class StabilityModel:
    @staticmethod
    def coefficient(poor_level: float, jobless_level: float, med_waste: float, population: int) -> float:
        if population <= 0:
            raise ValueError("Численность населения должна быть положительным числом.")
        med_waste_per_1000 = (med_waste / population) * 1000000
        stability_ranges = [
            (3, 80, 1.1, 1.1),
            (3, 70, 0.95, 1.00),
            (4, 45, 0.92, 0.94),
            (6, 40, 0.88, 0.91),
            (8, 30, 0.80, 0.87),
            (10, 20, 0.72, 0.79),
            (13, 10, 0.60, 0.71),
            (float('inf'), 5, 0.1, 0.2),
        ]
        for max_jobless, min_waste, min_val, max_val in stability_ranges:
            if med_waste_per_1000 >= min_waste and (
                jobless_level <= max_jobless or med_waste_per_1000 >= min_waste or poor_level <= max_jobless * 1.3
            ):
                return round(random.uniform(min_val, max_val), 3)
        return round(random.uniform(0.4, 0.56), 3) if poor_level < 56 or med_waste < 36 else 0.01


@dataclass(frozen=True)
class IncomeModifierModel:
    @staticmethod
    def from_agriculture(food_security: float) -> float:
        if food_security <= 100:
            return 0.45 + 0.55 * (food_security / 100) ** 2
        if food_security <= 150:
            return 1 + 0.15 * ((food_security - 100) / 50) ** 2
        return 1.15

    @staticmethod
    def from_social_decline(social_decline: float) -> float:
        return 1 - (social_decline / 100)

    @staticmethod
    def from_panic_level(panic_level: float) -> float:
        return 1 - (panic_level / 100)

    @staticmethod
    def from_food_diversity(food_diversity: float) -> float:
        return InbuiltFunctions.gaussian_kernel(-food_diversity / 10) * (1.9 / 0.4)


@dataclass(frozen=True)
class DemographyModel:
    @staticmethod
    def decrement_coefficient(decrement_coefficient: int) -> float:
        return -0.01 * decrement_coefficient + 1


@dataclass(frozen=True)
class StateApparatusModel:
    @staticmethod
    def expected_size(population_count: int, apparatus_wastes: float) -> int:
        n = population_count // 1000000
        expected_value = apparatus_wastes * n / 100
        return round(InbuiltFunctions.sigmoid(expected_value * 1000 // 13) * 100)


@dataclass(frozen=True)
class KnowledgeModel:
    @staticmethod
    def calculate(population_count: int, knowledge_wastes: float) -> float:
        if population_count <= 0:
            return 0.0
        expected_wastes = population_count / 28000
        constant = (knowledge_wastes / population_count) * 1e4
        minimal_knowledge = round((knowledge_wastes / population_count) * (1e6 if population_count > 1e6 else 1e5))
        if expected_wastes >= knowledge_wastes:
            return InbuiltFunctions.tanh(constant) * 120 + minimal_knowledge
        return InbuiltFunctions.sigmoid(constant) * 100 + minimal_knowledge


@dataclass(frozen=True)
class IntegrityOfFaithModel:
    @staticmethod
    def factor(integrity_of_faith: int) -> float:
        return 1 + (integrity_of_faith / 5000)


@dataclass(frozen=True)
class CorruptionModel:
    @staticmethod
    def apply(corruption_level: int) -> float:
        return -0.131 * corruption_level + 1.077
