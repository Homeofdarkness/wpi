"""Operational variability and informational event probabilities."""

from __future__ import annotations

import math

import numpy as np
from numpy.random import Generator

from functions.time_models import TURN_YEARS


def clip_percent(value: float) -> float:
    return min(100.0, max(0.0, float(value)))


def turn_chance(
    annual_hazard: float,
    years: float = TURN_YEARS,
) -> float:
    """Convert an annual hazard into a chance for the current turn."""
    hazard = max(float(annual_hazard), 0.0)
    return clip_percent((1 - math.exp(-hazard * max(years, 0.0))) * 100)


def half_year_chance(annual_hazard: float) -> float:
    """Compatibility alias; the result now follows the configured turn."""
    return turn_chance(annual_hazard)


def sample_percent(
    mean: float,
    rng: Generator,
    concentration: float = 800.0,
) -> float:
    probability = min(max(float(mean) / 100, 1e-6), 1 - 1e-6)
    alpha = probability * concentration
    beta = (1 - probability) * concentration
    return clip_percent(float(rng.beta(alpha, beta)) * 100)


def equipment_availability_mean(
    condition: float,
    maintenance: float,
    utilization: float,
) -> float:
    overload = max(utilization - 80, 0.0)
    return clip_percent(
        67 + 0.18 * condition + 0.13 * maintenance - 0.08 * overload
    )


def workforce_attendance_mean(
    health: float,
    social_support: float,
    war_fatigue: float,
) -> float:
    return clip_percent(
        74 + 0.13 * health + 0.1 * social_support - 0.08 * war_fatigue
    )


def process_yield_mean(
    processing_efficiency: float,
    standardization: float,
) -> float:
    return clip_percent(
        55 + 0.2 * processing_efficiency + 0.25 * standardization
    )


def logistics_integrity_mean(
    logistic: float,
    regional_separatism: float,
    war_fatigue: float,
) -> float:
    return clip_percent(
        86 + 0.12 * logistic - 0.04 * regional_separatism - 0.025 * war_fatigue
    )


def storage_preservation_mean(logistic: float) -> float:
    return clip_percent(91 + 0.08 * logistic)


def research_reproducibility_mean(
    knowledge: float,
    education: float,
    erudition: float,
    information_quality: float,
) -> float:
    return clip_percent(
        25
        + 0.2 * knowledge
        + 0.2 * education
        + 0.12 * erudition
        + 0.18 * information_quality
    )


def industrial_accident_chance(
    utilization: float,
    equipment_availability: float,
    standardization: float,
    forced_worker_share: float,
    safety: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.55
        + 1.6 * (utilization / 100) ** 2
        + 1.4 * (1 - equipment_availability / 100)
        + 0.8 * (1 - standardization / 100)
        + 1.2 * forced_worker_share
        + 1.0 * (1 - safety / 100)
    )
    return turn_chance(0.045 * max(risk, 0.0), years)


def supply_disruption_chance(
    logistics_integrity: float,
    regional_separatism: float,
    war_fatigue: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.5
        + 1.5 * (1 - logistics_integrity / 100)
        + regional_separatism / 80
        + war_fatigue / 150
    )
    return turn_chance(0.035 * max(risk, 0.0), years)


def population_epidemic_chance(
    healthcare_per_million: float,
    poor_level: float,
    food_security: float,
    information_quality: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    healthcare_protection = min(max(healthcare_per_million / 40, 0.0), 1.0)
    food_risk = max(0.0, 100 - food_security) / 100
    risk = (
        0.35
        + poor_level / 70
        + food_risk
        + 0.8 * (1 - information_quality / 100)
        + 0.8 * (1 - healthcare_protection)
    )
    return turn_chance(0.025 * max(risk, 0.0), years)


def agricultural_epidemic_chance(
    disease_level: float,
    food_diversity: float,
    agriculture_efficiency: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.4
        + disease_level / 35
        + max(0.0, 60 - food_diversity) / 60
        + max(0.0, 60 - agriculture_efficiency) / 80
    )
    return turn_chance(0.04 * max(risk, 0.0), years)


def natural_disaster_chance(
    natural_deceases: float,
    biome_richness: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = 0.45 + natural_deceases / 30 + max(0.0, 40 - biome_richness) / 80
    return turn_chance(0.035 * max(risk, 0.0), years)


def mass_protest_chance(
    contentment: float,
    government_trust: float,
    inequality: float,
    polarization: float,
    war_fatigue: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.25
        + max(0.0, 60 - contentment) / 35
        + max(0.0, 60 - government_trust) / 40
        + inequality / 100
        + polarization / 80
        + war_fatigue / 100
    )
    return turn_chance(0.055 * max(risk, 0.0), years)


def separatist_crisis_chance(
    regional_separatism: float,
    polarization: float,
    control_balance: float,
    provinces_support: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.2
        + regional_separatism / 55
        + polarization / 130
        + max(0.0, -control_balance) / 50
        + max(0.0, 1 - provinces_support)
    )
    return turn_chance(0.04 * max(risk, 0.0), years)


def major_sabotage_chance(
    forced_worker_share: float,
    violence_tendency: float,
    polarization: float,
    information_quality: float,
    *,
    years: float = TURN_YEARS,
) -> float:
    risk = (
        0.2
        + 2.2 * forced_worker_share
        + violence_tendency / 100
        + polarization / 100
        + max(0.0, 50 - information_quality) / 70
    )
    return turn_chance(0.035 * max(risk, 0.0), years)


def mean_or_default(values: list[float], default: float = 100.0) -> float:
    return float(np.mean(values)) if values else default
