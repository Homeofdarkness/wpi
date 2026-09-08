"""Resource extraction and industrial-workforce formulas."""

from __future__ import annotations

import math
from dataclasses import dataclass

from stats.industry_components import ExtractionGroup


EXTRACTION_UNITS_PER_SPENDING = 300.0


@dataclass(frozen=True)
class ExtractionGroupProfile:
    labor_weight: float
    labor_scale: float
    efficiency: float = 1.0


GROUP_PROFILES: dict[ExtractionGroup, ExtractionGroupProfile] = {
    ExtractionGroup.FORESTRY: ExtractionGroupProfile(0.60, 8_000),
    ExtractionGroup.FRESH_WATER: ExtractionGroupProfile(0.25, 5_000),
    ExtractionGroup.MINERAL_WATER: ExtractionGroupProfile(0.30, 5_000),
    ExtractionGroup.PRECIOUS: ExtractionGroupProfile(0.45, 12_000),
    ExtractionGroup.STRATEGIC_METALS: ExtractionGroupProfile(0.35, 14_000),
    ExtractionGroup.NONFERROUS: ExtractionGroupProfile(0.40, 12_000),
    ExtractionGroup.FERROUS: ExtractionGroupProfile(0.35, 10_000),
    ExtractionGroup.HEAVY_METALS: ExtractionGroupProfile(0.30, 15_000),
    ExtractionGroup.CHEMICAL: ExtractionGroupProfile(0.35, 8_000),
    ExtractionGroup.CONSTRUCTION: ExtractionGroupProfile(0.45, 8_000),
    ExtractionGroup.SOLID_FUEL: ExtractionGroupProfile(0.45, 11_000),
    ExtractionGroup.HYDROCARBONS: ExtractionGroupProfile(0.20, 6_000),
    ExtractionGroup.RARE_EARTH: ExtractionGroupProfile(0.30, 16_000),
    ExtractionGroup.SALTS: ExtractionGroupProfile(0.40, 8_000),
    ExtractionGroup.SOIL: ExtractionGroupProfile(0.65, 6_000),
    ExtractionGroup.PLANTATIONS: ExtractionGroupProfile(0.70, 7_000),
    ExtractionGroup.RECYCLING: ExtractionGroupProfile(0.50, 6_000),
    ExtractionGroup.MINERALS: ExtractionGroupProfile(0.40, 10_000),
    ExtractionGroup.UNIQUE: ExtractionGroupProfile(0.70, 20_000, 0.75),
}


def specialist_capacity(
    population: int,
    knowledge: float,
    education: float,
    max_workforce_share: float = 0.15,
) -> int:
    denominator = max(10_000.0, 100_000.0 - 1_000.0 * knowledge)
    potential = population / denominator * 2 ** (education / 10)
    cap = max(population, 0) * max_workforce_share
    return max(0, round(min(potential, cap)))


def national_extraction_capacity(extraction_spending: float) -> float:
    """Convert half-year extraction spending into annual abstract capacity."""
    return max(extraction_spending, 0.0) * EXTRACTION_UNITS_PER_SPENDING


def extraction_priority_weight(
    priority: int,
    lowest_priority: int,
) -> float:
    """Convert ordinal ranks to weights while keeping rank 1 strongest."""
    rank = max(int(priority), 1)
    lowest_rank = max(int(lowest_priority), rank)
    return float(lowest_rank - rank + 1)


def effective_workers(
    ordinary_workers: int,
    specialist_workers: int,
    forced_workers: int,
    health: float,
    social_support: float,
    attendance: float,
) -> float:
    health_factor = 0.4 + 0.6 * min(max(health / 100, 0.0), 1.0)
    social_factor = 0.65 + 0.35 * min(
        max(social_support / 100, 0.0),
        1.0,
    )
    attendance_factor = min(max(attendance / 100, 0.0), 1.0)
    ordinary = (
        ordinary_workers * health_factor * social_factor * attendance_factor
    )
    specialists = specialist_workers * 2.0 * attendance_factor
    forced = forced_workers * 0.55
    return ordinary + specialists + forced


def extraction_output(
    *,
    extraction_capacity: float,
    accessibility: float,
    quality: float,
    technology: float,
    effective_labor: float,
    equipment_availability: float,
    process_yield: float,
    years: float,
    profile: ExtractionGroupProfile | None = None,
) -> float:
    if extraction_capacity <= 0 or years <= 0:
        return 0.0
    group_profile = profile or ExtractionGroupProfile(0.5, 10_000)
    labor_factor = 1 - math.exp(
        -max(effective_labor, 0.0) / group_profile.labor_scale
    )
    production_factor = (
        labor_factor**group_profile.labor_weight * group_profile.efficiency
    )
    modifiers = (
        min(max(accessibility / 100, 0.0), 1.0)
        * min(max(quality / 100, 0.0), 1.0)
        * min(max(technology / 100, 0.0), 2.0)
        * min(max(equipment_availability / 100, 0.0), 1.0)
        * min(max(process_yield / 100, 0.0), 1.0)
    )
    capacity_for_period = extraction_capacity * years
    return capacity_for_period * production_factor * modifiers
