from __future__ import annotations

import random

from stats.basic_stats import EconomyStats
from stats.atterium_stats import AtteriumEconomyStats
from stats.isf_stats import IsfEconomyStats
from stats.schemas.economy_schema import build_field_names

from tests.factories import (
    make_basic_bundle,
    make_atterium_bundle,
    make_isf_bundle
)


def test_economy_schema_builders_match_class_methods():
    assert EconomyStats._get_field_names() == build_field_names("basic")
    assert AtteriumEconomyStats._get_field_names() == build_field_names("atterium")
    assert IsfEconomyStats._get_field_names() == build_field_names("isf")

    assert EconomyStats._get_pretty_layout() is not None
    assert AtteriumEconomyStats._get_pretty_layout() is not None
    assert IsfEconomyStats._get_pretty_layout() is not None


def test_common_schema_keys_are_shared_across_modes():
    # A couple of keys that must be identical across all economy variants
    for key in ["population_count", "decrement_coefficient", "inflation", "trade_rank"]:
        assert build_field_names("basic")[key] == build_field_names("atterium")[key]
        assert build_field_names("basic")[key] == build_field_names("isf")[key]


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
