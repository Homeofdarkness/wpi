from __future__ import annotations

import random

import pytest

from functions.config_models import EdenModel
from functions.economy_models import population_growth, trade_potential
from functions.income_models import (
    simple_stability_income_boost,
    state_apparatus_stability,
    tax_income,
)
from functions.industry_models import civil_usage
from functions.society_models import (
    integrity_of_faith_factor,
    population_decrement_factor,
)
from functions.time_models import TURN_SCALE
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from utils.user_io import TestIO


def test_core_formulas_are_direct_functions():
    assert population_growth(1_500_000) == pytest.approx(14_805 * TURN_SCALE)
    assert trade_potential(8, 95) == pytest.approx(10.7)
    assert civil_usage(100.0, 80.0, 70.0) == 83


def test_finance_and_society_formulas():
    assert (
        tax_income(
            22.6,
            8.1,
            105.0,
            8.7,
            27.0,
            12.5,
            13,
            15_361_475,
        )
        > 0
    )
    assert simple_stability_income_boost(100) == pytest.approx(1.293)
    assert population_decrement_factor(3) == pytest.approx(
        (1 - 0.03) ** TURN_SCALE
    )


def test_stability_formula_uses_a_value_copy() -> None:
    original = 80.0

    after_debuff = state_apparatus_stability(
        original,
        expected_apparatus_size=100,
        actual_apparatus_size=50,
        apparatus_efficiency=100,
        reference_scale=0.5,
    )

    assert original == 80
    assert after_debuff == 75
    assert integrity_of_faith_factor(90) == 1.018


def test_eden_model_maps_legacy_numbers_into_valid_basic_bundle():
    bundle = EdenModel.build()

    assert bundle.economy.population_count == 15_361_475
    assert bundle.economy.trade_rank == 37
    assert bundle.economy.trade_usage == 82
    assert bundle.economy.high_quality_percent == 45.0
    assert bundle.economy.mid_quality_percent == 55.0
    assert bundle.economy.low_quality_percent == 0.0
    assert bundle.industry.processing_efficiency == 69.0
    assert bundle.agriculture.biome_richness == 100.0
    assert bundle.inner_politics.state_apparatus_efficiency == 114
    assert (
        sum(
            [
                bundle.economy.high_quality_percent,
                bundle.economy.mid_quality_percent,
                bundle.economy.low_quality_percent,
            ]
        )
        == 100.0
    )


def test_skip_move_runs_for_eden_model():
    random.seed(7)
    bundle = EdenModel.build()

    engine = TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(inputs=[True, 0.0]),
    )

    report = engine.run()

    assert report.mode == "basic"
    assert report.budget_before == -53.668
    assert report.budget_final == bundle.economy.current_budget
    assert report.money_income is not None
