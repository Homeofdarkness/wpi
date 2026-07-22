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
            "money_income": -97.95469716151058,
            "tax_income": 138.78978907032686,
            "trade_income": 14.645738999999999,
            "total_wastes": 273.13635772,
            "budget_final": 912.0453028384894,
        },
    ),
    (
        "atterium",
        102,
        make_atterium_bundle,
        AtteriumSkipMoveRules,
        {
            "money_income": -88.66181941755161,
            "tax_income": 137.08615124713884,
            "trade_income": 24.618856080000004,
            "total_wastes": 272.13635772,
            "budget_final": 921.3381805824483,
        },
    ),
    (
        "isf",
        103,
        make_isf_bundle,
        IsfSkipMoveRules,
        {
            "money_income": -72.24642364348034,
            "tax_income": 169.8899230391489,
            "trade_income": 14.514498,
            "total_wastes": 272.13635772,
            "budget_final": 937.7535763565197,
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
