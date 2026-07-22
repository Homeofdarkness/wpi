import random

from modules.run_skip_move import TurnEngine
from modules.skip_move_rules import (
    AtteriumSkipMoveRules,
    BasicSkipMoveRules,
    IsfSkipMoveRules,
)
from modules.skip_move_types import WorldState
from tests.factories import (
    make_atterium_bundle,
    make_basic_bundle,
    make_isf_bundle,
)
from utils.user_io import TestIO


def make_engine(bundle, rules=None, mode="basic", io=None):
    return TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        rules=rules or BasicSkipMoveRules(),
        mode_name=mode,
        io=io or TestIO(),
    )


def test_basic_skip_move_runs_and_returns_report():
    random.seed(1)
    bundle = make_basic_bundle(budget=1000.0)
    report = make_engine(bundle).run()

    assert report.mode == "basic"
    assert report.budget_before == 1000.0
    assert report.budget_final == bundle.economy.current_budget
    assert bundle.economy.prev_budget == 1000.0
    assert report.money_income == bundle.economy.money_income
    assert report.budget_after_boost == report.budget_final
    assert report.total_wastes > 0
    assert report.ledger is not None
    assert report.ledger.net_income == report.money_income


def test_credit_is_applied_after_turn_math():
    random.seed(2)
    bundle = make_basic_bundle(budget=0.0)
    bundle.economy.gov_wastes = [5000.0, 2000.0, 1000.0, 500.0]
    bundle.economy.med_wastes = [1000.0, 1000.0, 500.0, 500.0, 250.0]
    bundle.economy.war_wastes = [800.0, 400.0, 200.0]
    bundle.economy.other_wastes = [200.0, 200.0, 200.0]
    bundle.economy.universal_tax = 0.1
    bundle.economy.excise = 0.1
    bundle.economy.additions = 0.0

    report = make_engine(
        bundle,
        io=TestIO(inputs=[True, 100.0]),
    ).run()

    assert report.budget_after_boost < 0
    assert report.credit_taken is True
    assert report.budget_final == 100.0
    assert bundle.economy.current_budget == 100.0
    assert report.credit_amount > 0


def test_atterium_mode_runs():
    random.seed(3)
    bundle = make_atterium_bundle(budget=500.0)
    report = make_engine(
        bundle,
        AtteriumSkipMoveRules(),
        "atterium",
    ).run()
    assert report.mode == "atterium"
    assert report.budget_final == bundle.economy.current_budget


def test_isf_mode_runs():
    random.seed(4)
    bundle = make_isf_bundle(budget=500.0)
    report = make_engine(bundle, IsfSkipMoveRules(), "isf").run()
    assert report.mode == "isf"
    assert report.budget_final == bundle.economy.current_budget
