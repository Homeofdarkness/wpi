"""Player-facing operational and major-event probabilities."""

from __future__ import annotations

import pydantic
from typing_extensions import override

from stats.pretty_specs import get_layout_for_class
from stats.stats_base import StatsBase


class ProbabilityStats(StatsBase):
    equipment_availability: float = pydantic.Field(100.0, ge=0, le=100)
    workforce_attendance: float = pydantic.Field(100.0, ge=0, le=100)
    process_yield: float = pydantic.Field(100.0, ge=0, le=100)
    logistics_integrity: float = pydantic.Field(100.0, ge=0, le=100)
    storage_preservation: float = pydantic.Field(100.0, ge=0, le=100)
    research_reproducibility: float = pydantic.Field(100.0, ge=0, le=100)

    industrial_accident_chance: float = pydantic.Field(0.0, ge=0, le=100)
    supply_disruption_chance: float = pydantic.Field(0.0, ge=0, le=100)
    population_epidemic_chance: float = pydantic.Field(0.0, ge=0, le=100)
    agricultural_epidemic_chance: float = pydantic.Field(0.0, ge=0, le=100)
    natural_disaster_chance: float = pydantic.Field(0.0, ge=0, le=100)
    mass_protest_chance: float = pydantic.Field(0.0, ge=0, le=100)
    separatist_crisis_chance: float = pydantic.Field(0.0, ge=0, le=100)
    major_sabotage_chance: float = pydantic.Field(0.0, ge=0, le=100)

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("ProbabilityStats")
