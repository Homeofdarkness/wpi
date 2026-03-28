from typing import List, Dict, Optional

import pydantic
from typing_extensions import override

from stats.derived_fields import (
    populate_basic_economy,
    populate_basic_industry,
    populate_basic_inner_politics,
)
from stats.pretty_layouts import get_layout_for_class
from stats.stats_base import StatsBase


class EconomyStats(StatsBase):
    population_count: int
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    small_enterprise_tax: float
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
    def check_trade_sum(self) -> 'EconomyStats':
        goods_percent = self.low_quality_percent + self.mid_quality_percent + self.high_quality_percent
        if abs(goods_percent - 100) > 0.1:
            raise ValueError(
                f"Сумма товаров разных качеств должна "
                f"быть равна 100, а на деле - {goods_percent}")

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
        return self.render_pretty()

    @staticmethod
    @override
    def _get_field_groups():
        from stats.schemas.economy_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names():
        from stats.schemas.economy_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("EconomyStats")


class IndustrialStats(StatsBase):
    processing_production: float = pydantic.Field(..., ge=0, le=100)
    processing_usage: float = pydantic.Field(..., ge=0, le=100)
    processing_efficiency: float = pydantic.Field(..., ge=0, le=100)
    usages: List[float]
    civil_security: float = pydantic.Field(..., ge=0, le=100)
    standardization: float = pydantic.Field(..., ge=0, le=100)
    logistic: float = pydantic.Field(..., ge=0, le=100)
    tvr1: int = pydantic.Field(..., ge=0, le=100)
    tvr2: int = pydantic.Field(..., ge=0, le=100)
    overproduction_coefficient: float = pydantic.Field(..., ge=0, le=100)
    war_production_efficiency: float = pydantic.Field(..., ge=0, le=100)
    industry_income: float = 0
    consumption_of_goods: float = 0
    civil_usage: float | None = None
    industry_coefficient: float | None = None
    civil_efficiency: float | None = None
    max_potential: float | None = None
    expected_wastes: float | None = None

    def recalculate_derived_fields(self) -> None:
        populate_basic_industry(self)

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty()

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        return {
            "Перерабатывающая промышленность": [
                'processing_production', 'processing_usage',
                'processing_efficiency'
            ],
            "Обеспеченность": [
                'usages'
            ],
            "Гражданская промышленность": [
                'civil_security', 'standardization', 'logistic',
                'tvr1', 'tvr2', 'overproduction_coefficient'
            ],
            "Военная промышленность": [
                'war_production_efficiency'
            ]
        }

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        return {
            'processing_production': 'Процент производства (%)',
            'processing_usage': 'Процент использования (%)',
            'processing_efficiency': 'Эффективность добычи (%)',
            'usages': 'Обеспеченность (ресурсная база, рабочие, сырье, квалификация)',
            'civil_security': 'Обеспеченность сырьем (%)',
            'standardization': 'Стандартизация (%)',
            'logistic': 'Логистика предприятий (%)',
            'tvr1': 'Обеспеченность ТЖН',
            'tvr2': 'Обеспеченность ТНП',
            'overproduction_coefficient': 'Процент перепроизводства (%)',
            'war_production_efficiency': 'Эффективность военного производства (%)',
            'industry_income': 'ПСС (ед.вал.)',
            'consumption_of_goods': 'Потребление товаров (%)'
        }

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IndustrialStats")


class InnerPoliticsStats(StatsBase):
    state_apparatus_size: int
    state_apparatus_efficiency: int
    knowledge_level: float
    many_children_propoganda: int
    integrity_of_faith: int
    corruption_level: int
    salt_security: int
    poor_level: float
    jobless_level: float
    income_from_scientific: float
    small_enterprise_percent: float
    large_enterprise_count: int
    provinces_count: int
    provinces_waste: float
    military_equipment: float
    control: list
    contentment: int
    government_trust: float
    many_children_traditions: int
    sexual_asceticism: float
    egocentrism_development: float
    education_level: float
    erudition_will: int
    cultural_level: int
    violence_tendency: float
    panic_level: float
    unemployment_rate: float
    grace_of_the_highest: int
    commitment_to_cause: int
    departure_from_truths: int
    success_chance: float | None = None
    society_decline: float | None = None

    def recalculate_derived_fields(self) -> None:
        populate_basic_inner_politics(self)

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty()

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.inner_politics_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.inner_politics_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("InnerPoliticsStats")


class AgricultureStats(StatsBase):
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
    agriculture_deceases: float
    agriculture_natural_deceases: float
    income_from_resources: float
    overstock_percent: float

    # Semi-dynamic param
    food_supplies: float = 0

    # Dynamic params (calculated in skip-move)
    expected_wastes: Optional[float] = None
    food_security: Optional[float] = None
    food_diversity: Optional[float] = None
    agriculture_efficiency: Optional[float] = None
    agriculture_development: Optional[float] = None

    # Inner Stat Params
    _is_negative_food_security: bool = False

    @override
    def debug(self):
        return self.render_pretty(debug=True)

    @override
    def __str__(self):
        return self.render_pretty()

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.agriculture_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.agriculture_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AgricultureStats")
