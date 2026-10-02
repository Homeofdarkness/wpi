"""Resource extraction and industrial-workforce formulas."""

from __future__ import annotations

import math
from dataclasses import dataclass

from stats.industry_components import ExtractionGroup, IndustrialStage


EXTRACTION_UNITS_PER_SPENDING = 300.0


@dataclass(frozen=True)
class ExtractionGroupProfile:
    labor_weight: float
    labor_scale: float
    efficiency: float = 1.0


@dataclass(frozen=True)
class IndustrialStageProfile:
    """Gameplay calibration for abstract units, not physical tonnes."""

    extraction_multiplier: float
    labor_dependency: float
    equipment_dependency: float


INDUSTRIAL_STAGE_PROFILES: dict[IndustrialStage, IndustrialStageProfile] = {
    IndustrialStage.MANUAL: IndustrialStageProfile(0.55, 1.35, 0.15),
    IndustrialStage.STEAM: IndustrialStageProfile(0.78, 1.15, 0.35),
    IndustrialStage.MACHINE: IndustrialStageProfile(1.00, 1.00, 0.60),
    IndustrialStage.ELECTRIFIED: IndustrialStageProfile(1.18, 0.82, 0.82),
    IndustrialStage.MASS_PRODUCTION: IndustrialStageProfile(1.35, 0.68, 1.00),
}


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


def extraction_allocation_weight(
    priority: int,
    lowest_priority: int,
    intensity: float,
) -> float:
    """Combine a priority rank and intensity into one allocation weight.

    Intensity describes how much of the shared extraction effort should be
    directed to an operation.  Normalising the combined weights prevents the
    unused part of a low-intensity operation from silently disappearing.
    """
    intensity_factor = min(max(float(intensity) / 100, 0.0), 1.0)
    return (
        extraction_priority_weight(priority, lowest_priority)
        * intensity_factor
    )


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


def extraction_factor_breakdown(
    *,
    accessibility: float,
    quality: float,
    technology: float,
    effective_labor: float,
    equipment_availability: float,
    process_yield: float,
    profile: ExtractionGroupProfile | None = None,
    stage: IndustrialStage = IndustrialStage.MACHINE,
) -> dict[str, float]:
    """Return every multiplier used by the extraction formula."""
    group_profile = profile or ExtractionGroupProfile(0.5, 10_000)
    stage_profile = INDUSTRIAL_STAGE_PROFILES[stage]
    labor_ratio = 1 - math.exp(
        -max(effective_labor, 0.0) / group_profile.labor_scale
    )
    labor_factor = labor_ratio ** (
        group_profile.labor_weight * stage_profile.labor_dependency
    )
    technology_ratio = min(max(technology / 100, 0.0), 1.0)
    technology_factor = 0.4 + 0.6 * technology_ratio
    equipment_ratio = min(max(equipment_availability / 100, 0.0), 1.0)
    equipment_factor = 1 - stage_profile.equipment_dependency * (
        1 - equipment_ratio
    )
    return {
        "labor": labor_factor,
        "group_efficiency": group_profile.efficiency,
        "stage": stage_profile.extraction_multiplier,
        "accessibility": min(max(accessibility / 100, 0.0), 1.0),
        "quality": min(max(quality / 100, 0.0), 1.0),
        "technology": technology_factor,
        "equipment": equipment_factor,
        "process_yield": min(max(process_yield / 100, 0.0), 1.0),
    }


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
    stage: IndustrialStage = IndustrialStage.MACHINE,
) -> float:
    if extraction_capacity <= 0 or years <= 0:
        return 0.0
    factors = extraction_factor_breakdown(
        accessibility=accessibility,
        quality=quality,
        technology=technology,
        effective_labor=effective_labor,
        equipment_availability=equipment_availability,
        process_yield=process_yield,
        profile=profile,
        stage=stage,
    )
    capacity_for_period = extraction_capacity * years
    return capacity_for_period * math.prod(factors.values())
