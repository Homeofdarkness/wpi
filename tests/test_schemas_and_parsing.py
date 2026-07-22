from __future__ import annotations

import random

from stats.atterium_stats import AtteriumEconomyStats
from stats.basic_stats import EconomyStats
from stats.isf_stats import IsfEconomyStats
from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, field
from stats.stats_base import StatsBase
from tests.factories import (
    make_atterium_bundle,
    make_basic_bundle,
    make_isf_bundle,
)
from utils.input_parsers import InputParser


class CreatorSample(StatsBase):
    count: int
    ratio: float
    values: list[float]

    @staticmethod
    def _get_pretty_layout() -> PrettyLayoutSpec:
        return PrettyLayoutSpec(
            fields={
                "count": field("count", "Количество"),
                "ratio": field("ratio", "Доля"),
                "values": field("values", "Значения"),
            },
            lines=(PrettyLineSpec(fields=("count", "ratio", "values")),),
        )


def test_economy_modes_have_pretty_layouts():
    assert EconomyStats._get_pretty_layout() is not None
    assert AtteriumEconomyStats._get_pretty_layout() is not None
    assert IsfEconomyStats._get_pretty_layout() is not None


def test_creator_uses_model_types_and_pretty_labels(monkeypatch):
    prompts = []

    def read_int(prompt, _field_info):
        prompts.append(prompt)
        return 7

    def read_float(prompt, _field_info):
        prompts.append(prompt)
        return 2.5

    def read_float_list(prompt):
        prompts.append(prompt)
        return [1.0, 2.0]

    monkeypatch.setattr(InputParser, "input_int", read_int)
    monkeypatch.setattr(InputParser, "input_float", read_float)
    monkeypatch.setattr(InputParser, "input_float_list", read_float_list)

    parsed = CreatorSample.from_user_input()

    assert parsed == CreatorSample(count=7, ratio=2.5, values=[1.0, 2.0])
    assert prompts == ["Количество", "Доля", "Значения"]


def test_basic_economy_parses_from_its_own_rendered_string_roundtrip():
    random.seed(10)
    b = make_basic_bundle(budget=1000.0)
    e = b.economy

    # Make sure optional fields referenced in __str__ are present.
    e.prev_budget = e.current_budget - 10.0
    e.tax_income = 123.0
    e.forex = 1.5
    e.trade_income = 2.5
    e.money_income = 10.0

    text = str(e)
    parsed = EconomyStats.from_stats_text(text)

    assert parsed.population_count == e.population_count
    assert parsed.decrement_coefficient == e.decrement_coefficient
    assert parsed.current_budget == e.current_budget
    assert parsed.prev_budget == e.prev_budget
    assert parsed.gov_wastes == e.gov_wastes
    assert parsed.other_wastes == e.other_wastes


def test_atterium_and_isf_custom_fields_are_parsed():
    random.seed(11)

    a = make_atterium_bundle(budget=500.0).economy
    a.prev_budget = a.current_budget - 5.0
    a.tax_income = 50.0
    a.forex = 1.1
    a.trade_income = 2.0
    a.money_income = 5.0

    at = str(a)
    parsed_a = AtteriumEconomyStats.from_stats_text(at)
    assert parsed_a.plan_efficiency == a.plan_efficiency
    assert parsed_a.gov_wastes == a.gov_wastes

    i = make_isf_bundle(budget=500.0).economy
    i.prev_budget = i.current_budget - 7.0
    i.tax_income = 70.0
    i.forex = 1.2
    i.trade_income = 3.0
    i.money_income = 6.0

    it = str(i)
    parsed_i = IsfEconomyStats.from_stats_text(it)
    assert parsed_i.small_business_tax == i.small_business_tax
    assert parsed_i.other_wastes == i.other_wastes
