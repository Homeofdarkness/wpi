from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from create_basic_country import create_basic_country
from modules.mode_spec import GameMode, get_mode
from modules.run_skip_move import TurnEngine
from utils.user_io import TestIO


def test_edem_turn_does_not_collapse_the_economy() -> None:
    input_path = (
        Path(__file__).parents[1] / "test_files" / "edem_country_input.txt"
    )
    state = create_basic_country(input_path)
    spec = get_mode(GameMode.BASIC)

    report = TurnEngine(
        state=state,
        rules=spec.rules_factory(),
        mode_name=spec.mode.value,
        io=TestIO(),
        rng=np.random.default_rng(1),
    ).run()

    assert state.agriculture.expected_wastes == pytest.approx(
        61.97248559577602
    )
    assert state.agriculture.food_security == pytest.approx(107.6)
    assert "Обеспеченность едой - 107.6" in str(state.agriculture)
    assert "Обеспеченность едой - 107.6%" not in str(state.agriculture)
    assert report.tax_income > 2_500
    assert report.trade_income == pytest.approx(197.9780096)
    assert state.economy.income == pytest.approx(90_334, rel=0.01)
    assert report.resource_effect_wastes < 0
    assert abs(report.money_income) < 700
    assert report.credit_taken is False
    assert report.budget_final == pytest.approx(638.9258055298294)
