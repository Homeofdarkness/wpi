from __future__ import annotations

import random
from dataclasses import asdict

import numpy as np
import pytest

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


SCENARIOS = (
    (
        "basic",
        101,
        make_basic_bundle,
        BasicSkipMoveRules,
        {
            "money_income": -97.91155376732428,
            "tax_income": 138.8322273829015,
            "trade_income": 14.645157,
            "total_wastes": 273.13635772,
            "budget_final": 912.0884462326758,
        },
    ),
    (
        "atterium",
        102,
        make_atterium_bundle,
        AtteriumSkipMoveRules,
        {
            "money_income": -88.62267641695314,
            "tax_income": 137.12510426845196,
            "trade_income": 24.61787832,
            "total_wastes": 272.13635772,
            "budget_final": 921.3773235830469,
        },
    ),
    (
        "isf",
        103,
        make_isf_bundle,
        IsfSkipMoveRules,
        {
            "money_income": -72.19634894238607,
            "tax_income": 169.9400063796194,
            "trade_income": 14.514498,
            "total_wastes": 272.13635772,
            "budget_final": 937.8036510576139,
        },
    ),
)


@pytest.mark.parametrize(
    ("mode", "seed", "factory", "rules_class", "expected"),
    SCENARIOS,
)
def test_turn_characterization(
    mode,
    seed,
    factory,
    rules_class,
    expected,
):
    random.seed(seed)
    bundle = factory(budget=1000.0)
    engine = TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        rules=rules_class(),
        mode_name=mode,
        io=TestIO(),
        rng=np.random.default_rng(seed),
    )

    report = asdict(engine.run())

    assert report["mode"] == mode
    for key, value in expected.items():
        assert report[key] == pytest.approx(value)
