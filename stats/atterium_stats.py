import pydantic
from typing_extensions import override

from stats.basic_stats import EconomyStatsBase
from stats.derived_fields import (
    populate_atterium_inner_politics,
)
from stats.pretty_specs import get_layout_for_class
from stats.stats_base import StatsBase


class AtteriumEconomyStats(EconomyStatsBase):
    freedom_and_efficiency_of_small_business: float
    investment_of_large_companies: float
    plan_efficiency: float = pydantic.Field(..., ge=0, le=100)
    adrian_effect: float
    power_of_economic_formation: float

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AtteriumEconomyStats")


class AtteriumInnerPoliticsStats(StatsBase):
    state_apparatus_functionality: float
    state_apparatus_size: int
    state_apparatus_efficiency: int
    knowledge_level: int
    many_children_propoganda: int
    integrity_of_faith: int
    corruption_level: int
    salt_security: int
    poor_level: float
    jobless_level: float
    small_enterprise_percent: float
    large_enterprise_count: int
    provinces_count: int
    provinces_waste: float
    military_equipment: float
    control: list[float] = pydantic.Field(
        ...,
        min_length=4,
        max_length=4,
    )
    contentment: int
    government_trust: float
    many_children_traditions: int
    sexual_asceticism: float
    egocentrism_development: float
    capitalistic_decay: float
    education_level: int
    erudition_will: int
    cultural_level: int
    violence_tendency: float
    panic_level: float
    unemployment_rate: float
    equality: float
    grace_of_the_highest: int
    commitment_to_cause: int
    departure_from_truths: int
    research_success_chance: float | None = None
    society_decline: float | None = None
    inequality: float = pydantic.Field(25.0, ge=0, le=100)
    polarization: float = pydantic.Field(20.0, ge=0, le=100)
    information_quality: float = pydantic.Field(60.0, ge=0, le=100)
    regional_separatism: float = pydantic.Field(0.0, ge=0, le=100)
    social_mobility: float = pydantic.Field(50.0, ge=0, le=100)
    war_fatigue: float = pydantic.Field(0.0, ge=0, le=100)

    def recalculate_derived_fields(self) -> None:
        populate_atterium_inner_politics(self)

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AtteriumInnerPoliticsStats")
