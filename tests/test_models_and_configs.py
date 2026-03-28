from __future__ import annotations

import random

from functions.basic_in_move_functions import BasicInMoveFunctions
from functions.basic_stats_functions import BasicStatsFunctions
from functions.config_models import EdenModel
from functions.economy_models import PopulationGrowthModel, TradePotentialModel
from functions.income_models import MoneyIncomeModel, TaxIncomeModel
from functions.industry_models import CivilUsageModel
from functions.society_models import DemographyModel, IntegrityOfFaithModel
from modules.run_skip_move import BasicSkipMove
from utils.user_io import TestIO


def test_basic_stats_functions_delegate_to_models():
    assert BasicStatsFunctions.calculate_population_growth(1_500_000) == PopulationGrowthModel.calculate(1_500_000)
    assert BasicStatsFunctions.calculate_trade_potential(8, 95) == TradePotentialModel.calculate(8, 95)
    assert BasicStatsFunctions.calculate_civil_usage(100.0, 80.0, 70.0) == CivilUsageModel.calculate(100.0, 80.0, 70.0)


def test_basic_in_move_functions_delegate_to_models():
    assert BasicInMoveFunctions.calculate_tax_income(22.6, 8.1, 105.0, 8.7, 27.0, 12.5, 13, 15_361_475) == TaxIncomeModel.calculate(22.6, 8.1, 105.0, 8.7, 27.0, 12.5, 13, 15_361_475)
    assert BasicInMoveFunctions.calculate_money_income_simple_boost(100) == MoneyIncomeModel.simple_boost(100)
    assert BasicInMoveFunctions.calculate_population_decrement_coefficient(3) == DemographyModel.decrement_coefficient(3)
    assert BasicInMoveFunctions.calculate_integrity_of_faith_factor(90) == IntegrityOfFaithModel.factor(90)


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
    assert sum([
        bundle.economy.high_quality_percent,
        bundle.economy.mid_quality_percent,
        bundle.economy.low_quality_percent,
    ]) == 100.0


def test_skip_move_runs_for_eden_model():
    random.seed(7)
    bundle = EdenModel.build()

    engine = BasicSkipMove(
        Economy=bundle.economy,
        Industry=bundle.industry,
        Agriculture=bundle.agriculture,
        InnerPolitics=bundle.inner_politics,
        io=TestIO(inputs=[True, 0.0]),
    )

    report = engine.run()

    assert report.mode == "basic"
    assert report.budget_before == -53.668
    assert report.budget_final == bundle.economy.current_budget
    assert report.money_income is not None
