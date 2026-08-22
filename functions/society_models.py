"""Society, administration, and demographic formulas."""

from __future__ import annotations

from functions.inbuilt import sigmoid, tanh


def cultural_coefficient(
    cultural_level: int,
    egocentrism_development: float,
) -> float:
    return max(
        0.0,
        0.025 * cultural_level - 0.105 + egocentrism_development / 100,
    )


def contentment_coefficients(contentment: int) -> tuple[float, float]:
    return 0.004 * contentment + 0.754, 0.005 * contentment + 0.528


def success_chance(
    knowledge_level: float,
    education_level: float,
    erudition_will: float,
) -> float:
    erudition_factor = min(max(float(erudition_will), 0.0), 100.0) / 100
    base = (knowledge_level + education_level) / 2
    return min(100.0, max(0.0, base * (0.9 + 0.1 * erudition_factor)))


def society_decline(
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
    positive = (
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
    negative = (
        violence_tendency * 0.5
        + egocentrism_development * 0.3
        + unemployment_rate * 0.3
        + departure_from_truths * 1.1
    )
    return round(min(max(0.0, negative - positive), 100), 2)


def stability_coefficient(
    poor_level: float,
    jobless_level: float,
    med_waste: float,
    population: int,
) -> float:
    if population <= 0:
        raise ValueError("Численность населения должна быть положительной")
    med_waste_per_million = med_waste / population * 1_000_000
    ranges = (
        (3, 80, 1.1, 1.1),
        (3, 70, 0.95, 1.00),
        (4, 45, 0.92, 0.94),
        (6, 40, 0.88, 0.91),
        (8, 30, 0.80, 0.87),
        (10, 20, 0.72, 0.79),
        (13, 10, 0.60, 0.71),
        (float("inf"), 5, 0.1, 0.2),
    )
    for max_jobless, min_waste, minimum, maximum in ranges:
        if med_waste_per_million >= min_waste and (
            jobless_level <= max_jobless or poor_level <= max_jobless * 1.3
        ):
            return round((minimum + maximum) / 2, 3)
    if poor_level < 56 or med_waste < 36:
        return 0.48
    return 0.01


def agriculture_income_factor(food_security: float) -> float:
    if food_security <= 100:
        return 0.45 + 0.55 * (food_security / 100) ** 2
    if food_security <= 150:
        return 1 + 0.15 * ((food_security - 100) / 50) ** 2
    return 1.15


def social_decline_income_factor(social_decline: float) -> float:
    return 1 - social_decline / 100


def panic_income_factor(panic_level: float) -> float:
    return 1 - panic_level / 100


def food_diversity_income_factor(food_diversity: float) -> float:
    """Bounded demographic effect of the 0..100 diversity index.

    The previous Gaussian expression returned exactly zero at diversity 0,
    rewarded negative values, and was hard to reason about. The replacement
    keeps the effect modest and monotonic: 0 gives a 10% penalty, 50 is close
    to equilibrium, and 100 gives a 12% bonus.
    """
    normalized = min(max(float(food_diversity), 0.0), 100.0) / 100
    return 0.9 + 0.22 * normalized


def population_decrement_factor(decrement_coefficient: int) -> float:
    return -0.01 * decrement_coefficient + 1


def expected_state_apparatus_size(
    population_count: int,
    apparatus_wastes: float,
) -> int:
    population_millions = population_count // 1_000_000
    expected_value = apparatus_wastes * population_millions / 100
    return round(sigmoid(expected_value * 1000 // 13) * 100)


def knowledge_level(population_count: int, knowledge_wastes: float) -> float:
    if population_count <= 0:
        return 0.0
    expected_wastes = population_count / 28000
    constant = knowledge_wastes / population_count * 1e4
    scale = 1e6 if population_count > 1e6 else 1e5
    minimum = round(knowledge_wastes / population_count * scale)
    if expected_wastes >= knowledge_wastes:
        return tanh(constant) * 120 + minimum
    return sigmoid(constant) * 100 + minimum


def integrity_of_faith_factor(integrity_of_faith: int) -> float:
    return 1 + integrity_of_faith / 5000


def corruption_factor(corruption_level: int) -> float:
    return -0.131 * corruption_level + 1.077
