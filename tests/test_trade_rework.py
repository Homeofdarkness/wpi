from functions.basic_in_move_functions import BasicInMoveFunctions
from functions.trade_models import ForexFeatures, TradeModels


def _base_forex_features(**overrides) -> ForexFeatures:
    data = dict(
        stability=80,
        income=120.0,
        wastes=500.0,
        budget=1000.0,
        trade_rank=3,
        trade_efficiency=80.0,
        trade_overload=60.0,
        industry_efficiency=70.0,
        state_apparatus_efficiency=60,
        contentment=75,
        poor_level=4.0,
        jobless_level=7.0,
        control_balance=8.0,
    )
    data.update(overrides)
    return ForexFeatures(**data)


def test_trade_income_does_not_crash_at_trade_potential_boundary():
    at_capacity = BasicInMoveFunctions.calculate_trade_income(
        trade_potential=20,
        trade_usage=20,
        trade_efficiency=80,
        trade_wastes=1,
        high_quality_percent=30,
        mid_quality_percent=40,
        low_quality_percent=30,
        forex=2.5,
        valgery=10,
    )
    slightly_over = BasicInMoveFunctions.calculate_trade_income(
        trade_potential=20,
        trade_usage=21,
        trade_efficiency=80,
        trade_wastes=1,
        high_quality_percent=30,
        mid_quality_percent=40,
        low_quality_percent=30,
        forex=2.5,
        valgery=10,
    )

    assert slightly_over > 0
    # Раньше здесь был обвал более чем в 4 раза.
    assert slightly_over / at_capacity > 0.8


def test_trade_income_is_never_negative_even_with_extreme_wastes():
    income = BasicInMoveFunctions.calculate_trade_income(
        trade_potential=10,
        trade_usage=20,
        trade_efficiency=10,
        trade_wastes=10_000,
        high_quality_percent=10,
        mid_quality_percent=20,
        low_quality_percent=70,
        forex=0,
        valgery=0,
    )

    assert income == 0.0


def test_forex_model_does_not_collapse_to_one_on_large_budget_scale():
    medium = TradeModels.calculate_forex_course(
        _base_forex_features(budget=2_000.0, income=250.0)
    )
    large = TradeModels.calculate_forex_course(
        _base_forex_features(budget=100_000.0, income=10_000.0)
    )

    assert medium > 1.0
    assert large > 1.0
    assert abs(large - medium) < 2.0


def test_forex_improves_when_macro_conditions_improve():
    weak = TradeModels.calculate_forex_course(
        _base_forex_features(
            stability=45,
            trade_efficiency=40,
            industry_efficiency=35,
            contentment=40,
            poor_level=14,
            jobless_level=18,
            income=20,
            budget=100,
            wastes=900,
        )
    )
    strong = TradeModels.calculate_forex_course(
        _base_forex_features(
            stability=90,
            trade_efficiency=85,
            industry_efficiency=82,
            contentment=85,
            poor_level=3,
            jobless_level=5,
            income=220,
            budget=2000,
            wastes=350,
        )
    )

    assert strong > weak


def test_money_income_simple_boost_has_no_drop_at_100_stability():
    boost_99 = BasicInMoveFunctions.calculate_money_income_simple_boost(99)
    boost_100 = BasicInMoveFunctions.calculate_money_income_simple_boost(100)
    boost_120 = BasicInMoveFunctions.calculate_money_income_simple_boost(120)

    assert boost_100 >= boost_99
    assert boost_120 == boost_100
