from typing import List, Dict

import pydantic
from typing_extensions import override

from stats.basic_stats import IndustrialStats
from stats.stats_base import StatsBase
from stats.pretty_layouts import get_layout_for_class
from stats.derived_fields import (
    populate_basic_economy,
    populate_isf_inner_politics,
)


class IsfEconomyStats(StatsBase):
    population_count: int
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    small_business_tax: float
    large_enterprise_tax: float
    gov_wastes: List[float]
    med_wastes: List[float]
    other_wastes: List[float]
    war_wastes: List[float]
    trade_rank: int
    trade_usage: int
    trade_efficiency: int
    trade_wastes: float
    high_quality_percent: float
    mid_quality_percent: float
    low_quality_percent: float
    valgery: float
    allegorization: float
    branches_count: int
    branches_efficiency: float
    tax_income: float | None = None
    forex: float | None = None
    trade_income: float | None = None
    money_income: float | None = None
    prev_budget: float | None = None
    income: float | None = None
    trade_potential: float | None = None
    branches_income: float | None = None

    @pydantic.model_validator(mode='after')
    def check_trade_sum(self) -> 'IsfEconomyStats':
        goods_percent = (
                self.low_quality_percent
                + self.mid_quality_percent
                + self.high_quality_percent
        )
        if abs(goods_percent - 100) > 0.1:
            raise ValueError(
                f"Сумма товаров разных качеств должна быть равна 100, "
                f"а на деле - {goods_percent}"
            )

        return self

    def recalculate_derived_fields(self) -> None:
        populate_basic_economy(self)

    def trade_usage_load(self) -> int:
        if not self.trade_potential:
            return 0
        return round(self.trade_usage / self.trade_potential * 100)

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty(debug=False)

    @staticmethod
    @override
    def _get_field_groups():
        from stats.schemas.economy_schema import build_field_groups
        return build_field_groups("isf")

    @staticmethod
    @override
    def _get_field_names():
        from stats.schemas.economy_schema import build_field_names
        return build_field_names("isf")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IsfEconomyStats")


class IsfIndustrialStats(IndustrialStats):
    pass


class IsfAgricultureStats(StatsBase):
    husbandry: float
    livestock: float
    others: float
    biome_richness: float
    overprotective_effects: int
    securities: list
    workers_percent: float
    workers_redistribution: float
    storages_upkeep: float
    consumption_factor: float
    environmental_food: int
    empire_land_unmastery: float
    agriculture_deceases: float
    agriculture_natural_deceases: float
    income_from_resources: float
    overstock_percent: float

    # Dynamic params (calculated in skip-move)
    expected_wastes: float = None
    food_security: float = None
    food_diversity: float = None
    agriculture_efficiency: float = None
    agriculture_development: float = None
    food_supplies: float = None

    _is_negative_food_security: bool = False

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty(debug=False)

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.agriculture_schema import build_field_groups
        return build_field_groups("isf")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.agriculture_schema import build_field_names
        return build_field_names("isf")

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
    control: List[float]
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

    @pydantic.model_validator(mode='after')
    def check_control_sum(self) -> 'IsfInnerPoliticsStats':
        if self.control[2] > 15:
            raise ValueError(
                f"Аристократия не может быть больше 15%, получено "
                f"{self.control[2]}"
            )

        return self

    success_chance: float | None = None
    society_decline: float | None = None

    def recalculate_derived_fields(self) -> None:
        populate_isf_inner_politics(self)

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty(debug=False)

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.inner_politics_schema import build_field_groups
        return build_field_groups("isf")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.inner_politics_schema import build_field_names
        return build_field_names("isf")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IsfInnerPoliticsStats")
