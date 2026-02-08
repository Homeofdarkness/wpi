import random

from modules.run_skip_move import BasicSkipMove, AtteriumSkipMove, IsfSkipMove
from utils.user_io import TestIO

from tests.factories import make_basic_bundle, make_atterium_bundle, make_isf_bundle


def test_basic_skip_move_runs_and_returns_report():
    random.seed(1)
    b = make_basic_bundle(budget=1000.0)

    engine = BasicSkipMove(
        Economy=b.economy,
        Industry=b.industry,
        Agriculture=b.agriculture,
        InnerPolitics=b.inner_politics,
        io=TestIO(),
    )

    report = engine.run()

    assert report.mode == "basic"
    assert report.budget_before == 1000.0
    assert report.budget_final == b.economy.current_budget
    assert b.economy.prev_budget == 1000.0

    # Sanity: money income is reflected in the report
    assert abs(report.money_income - float(b.economy.money_income)) < 1e-6

    # Budget after boost should match engine state (before possible credit)
    assert abs(report.budget_after_boost - report.budget_final) < 1e-6
    assert report.total_wastes > 0


def test_credit_is_requested_only_after_all_math_and_overrides_final_budget():
    random.seed(2)
    b = make_basic_bundle(budget=0.0)

    # Force a guaranteed deficit by inflating expenses and lowering taxes
    b.economy.gov_wastes = [5000.0, 2000.0, 1000.0, 500.0]
    b.economy.med_wastes = [1000.0, 1000.0, 500.0, 500.0, 250.0]
    b.economy.war_wastes = [800.0, 400.0, 200.0]
    b.economy.other_wastes = [200.0, 200.0, 200.0]
    b.economy.universal_tax = 0.1
    b.economy.excise = 0.1
    b.economy.additions = 0.0

    io = TestIO(inputs=[True, 100.0])  # take credit, set final budget to 100

    engine = BasicSkipMove(
        Economy=b.economy,
        Industry=b.industry,
        Agriculture=b.agriculture,
        InnerPolitics=b.inner_politics,
        io=io,
    )

    report = engine.run()

    assert report.budget_after_boost < 0  # deficit existed
    assert report.credit_taken is True
    assert report.budget_final == 100.0
    assert b.economy.current_budget == 100.0
    assert report.credit_amount > 0


def test_atterium_mode_runs():
    random.seed(3)
    b = make_atterium_bundle(budget=500.0)

    engine = AtteriumSkipMove(
        Economy=b.economy,
        Industry=b.industry,
        Agriculture=b.agriculture,
        InnerPolitics=b.inner_politics,
        io=TestIO(),
    )

    report = engine.run()
    assert report.mode == "atterium"
    assert report.budget_final == b.economy.current_budget


def test_isf_mode_runs():
    random.seed(4)
    b = make_isf_bundle(budget=500.0)

    engine = IsfSkipMove(
        Economy=b.economy,
        Industry=b.industry,
        Agriculture=b.agriculture,
        InnerPolitics=b.inner_politics,
        io=TestIO(),
    )

    report = engine.run()
    assert report.mode == "isf"
    assert report.budget_final == b.economy.current_budget
