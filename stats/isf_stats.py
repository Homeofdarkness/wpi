import pydantic
from typing_extensions import override

from stats.basic_stats import AgricultureStats, EconomyStatsBase
from stats.derived_fields import (
    populate_isf_inner_politics,
)
from stats.pretty_specs import get_layout_for_class
from stats.stats_base import StatsBase


class IsfEconomyStats(EconomyStatsBase):
    small_business_tax: float
    large_enterprise_tax: float

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IsfEconomyStats")


class IsfAgricultureStats(AgricultureStats):
    empire_land_unmastery: float

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IsfAgricultureStats")


class IsfInnerPoliticsStats(StatsBase):
    state_apparatus_size: int = pydantic.Field(..., ge=0, le=400)
    state_apparatus_efficiency: int = pydantic.Field(..., ge=0, le=200)
    knowledge_level: int = pydantic.Field(..., ge=0, le=100)
    many_children_propoganda: int = pydantic.Field(..., ge=0, le=25)
    integrity_of_faith: int = pydantic.Field(..., ge=0, le=100)
    corruption_level: int = pydantic.Field(..., ge=0, le=25)
    salt_security: int = pydantic.Field(..., ge=0)  # FYI: Соли много не бывает
    poor_level: float = pydantic.Field(..., ge=0, le=100)
    jobless_level: float = pydantic.Field(..., ge=0, le=100)
    small_enterprise_percent: float = pydantic.Field(..., ge=0, le=100)
    large_enterprise_count: int = pydantic.Field(..., ge=0)
    provinces_count: int = pydantic.Field(..., ge=0)
    provinces_waste: float = pydantic.Field(..., ge=0)
    military_equipment: float = pydantic.Field(..., ge=0)
    allegory_influence: float = pydantic.Field(..., ge=0, le=100)
    control: list[float] = pydantic.Field(
        ...,
        min_length=4,
        max_length=4,
    )
    contentment: int = pydantic.Field(..., ge=0, le=125)
    government_trust: float = pydantic.Field(..., ge=0, le=100)
    many_children_traditions: int = pydantic.Field(..., ge=0, le=25)
    sexual_asceticism: float = pydantic.Field(..., ge=0, le=50)
    egocentrism_development: float = pydantic.Field(..., ge=0, le=50)
    education_level: int = pydantic.Field(..., ge=0, le=100)
    erudition_will: int = pydantic.Field(..., ge=0, le=100)
    cultural_level: int
    violence_tendency: float = pydantic.Field(..., ge=0, le=100)
    panic_level: float = pydantic.Field(..., ge=0, le=100)
    unemployment_rate: float = pydantic.Field(..., ge=0, le=100)
    imperial_court_power: float = pydantic.Field(..., ge=0, le=100)
    grace_of_the_silver: int = pydantic.Field(..., ge=0, le=100)
    commitment_to_cause: int = pydantic.Field(..., ge=0, le=100)
    departure_from_truths: int = pydantic.Field(..., ge=0, le=100)
    separatism_of_the_highest: int = pydantic.Field(..., ge=0, le=100)

    @pydantic.model_validator(mode="after")
    def check_control_sum(self) -> "IsfInnerPoliticsStats":
        if self.control[2] > 15:
            raise ValueError(
                f"Аристократия не может быть больше 15%, получено "
                f"{self.control[2]}"
            )

        return self

    research_success_chance: float | None = None
    society_decline: float | None = None
    inequality: float = pydantic.Field(25.0, ge=0, le=100)
    polarization: float = pydantic.Field(20.0, ge=0, le=100)
    information_quality: float = pydantic.Field(60.0, ge=0, le=100)
    regional_separatism: float = pydantic.Field(0.0, ge=0, le=100)
    social_mobility: float = pydantic.Field(50.0, ge=0, le=100)
    war_fatigue: float = pydantic.Field(0.0, ge=0, le=100)

    def recalculate_derived_fields(self) -> None:
        populate_isf_inner_politics(self)

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IsfInnerPoliticsStats")
