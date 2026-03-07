from typing import List, Dict

import pydantic
from typing_extensions import override

from stats.basic_stats import IndustrialStats, AgricultureStats
from stats.stats_base import StatsBase
from stats.pretty_layouts import get_layout_for_class
from stats.derived_fields import (
    populate_basic_economy,
    populate_atterium_inner_politics,
)


class AtteriumEconomyStats(StatsBase):
    population_count: int
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    freedom_and_efficiency_of_small_business: float
    investment_of_large_companies: float
    plan_efficiency: float = pydantic.Field(..., ge=0, le=100)
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
    adrian_effect: float
    power_of_economic_formation: float
    tax_income: float | None = None
    forex: float | None = None
    trade_income: float | None = None
    money_income: float | None = None
    prev_budget: float | None = None
    income: float | None = None
    trade_potential: float | None = None
    branches_income: float | None = None

    @pydantic.model_validator(mode='after')
    def check_trade_sum(self) -> 'AtteriumEconomyStats':
        goods_percent = self.low_quality_percent + self.mid_quality_percent + self.high_quality_percent
        if abs(goods_percent - 100) > 0.1:
            raise ValueError(
                f"Сумма товаров разных качеств должна быть равна 100, а на деле - {goods_percent}")
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
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names():
        from stats.schemas.economy_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AtteriumEconomyStats")


class AtteriumIndustrialStats(IndustrialStats):
    """Механики одинаковые и слава Богу """
    pass


class AtteriumAgricultureStats(AgricultureStats):

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.agriculture_schema import build_field_groups
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.agriculture_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AtteriumAgricultureStats")


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
    control: List[float]
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
    success_chance: float | None = None
    society_decline: float | None = None

    def recalculate_derived_fields(self) -> None:
        populate_atterium_inner_politics(self)

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
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.inner_politics_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AtteriumInnerPoliticsStats")
