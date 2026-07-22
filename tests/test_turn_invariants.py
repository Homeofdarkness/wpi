from __future__ import annotations

import pytest
from pydantic import ValidationError

from functions.agriculture_models import workers_count
from functions.industry_models import overproduction_tax_factor
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.basic_stats import EconomyStats, IndustrialStats
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def engine_for(bundle) -> TurnEngine:
    return TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(),
    )


def test_final_budget_is_stock_plus_turn_flow_not_multiplied_stock():
    bundle = make_basic_bundle(budget=1000.0)
    report = engine_for(bundle).run()

    assert report.budget_final == pytest.approx(
        report.budget_before + report.money_income + report.logistic_discount
    )


def test_stability_is_persisted_in_next_state():
    bundle = make_basic_bundle()
    report = engine_for(bundle).run()

    assert bundle.economy.stability == report.stability_after


def test_population_growth_is_applied_and_remains_integer():
    bundle = make_basic_bundle()
    bundle.economy.decrement_coefficient = 0
    bundle.agriculture.environmental_food = 1_000
    population_before = bundle.economy.population_count

    engine_for(bundle).run()

    assert isinstance(bundle.economy.population_count, int)
    assert bundle.economy.population_count == (
        population_before + round(bundle.economy.income)
    )


def test_full_inflation_does_not_erase_expenses():
    bundle = make_basic_bundle()
    bundle.economy.inflation = 100
    report = engine_for(bundle).run()

    assert report.money_income == pytest.approx(-report.total_wastes)


def test_overproduction_cannot_create_negative_trade_income():
    bundle = make_basic_bundle()
    bundle.industry.overproduction_coefficient = 99
    report = engine_for(bundle).run()

    assert report.trade_income >= 0
    assert 0 <= bundle.industry.overproduction_coefficient <= 100


def test_agricultural_worker_share_uses_percentage_scale():
    full_staff = workers_count(10_000_000, 100, 0)

    assert full_staff == 100_000
    assert workers_count(10_000_000, 50, 0) == 50_000
    assert workers_count(10_000_000, 100, 25) == 75_000


def test_overproduction_cannot_erase_the_whole_economy():
    assert overproduction_tax_factor(100) == pytest.approx(0.8)
    assert overproduction_tax_factor(0) == pytest.approx(1.0)


def test_zero_industry_inputs_are_valid_and_safe():
    source = make_basic_bundle().industry.model_dump()
    source.update(processing_production=0, processing_usage=0)

    state = IndustrialStats(**source)

    assert state.industry_coefficient == 0


def test_non_positive_population_is_rejected_at_boundary():
    source = make_basic_bundle().economy.model_dump()
    source["population_count"] = 0

    with pytest.raises(ValidationError):
        EconomyStats(**source)


def test_derived_industry_stats_are_deterministic():
    first = make_basic_bundle().industry
    second = make_basic_bundle().industry

    assert first.civil_efficiency == second.civil_efficiency
    assert first.expected_wastes == second.expected_wastes


def test_reused_engine_does_not_compound_derived_branch_income():
    bundle = make_basic_bundle()
    engine = engine_for(bundle)

    engine.run()
    engine.run()

    expected_base = bundle.economy.branches_count * (
        bundle.economy.branches_efficiency / 10
    )
    assert bundle.economy.branches_income == pytest.approx(
        expected_base * 0.97
    )
