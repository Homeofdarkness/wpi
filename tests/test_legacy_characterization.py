from __future__ import annotations

import random
from dataclasses import asdict

import numpy as np
import pytest

from functions.time_models import TurnCalendar
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
            "money_income": -97.37227008766732,
            "tax_income": 137.03440680337877,
            "trade_income": 16.966172999999998,
            "total_wastes": 273.13635772,
            "budget_final": 912.6277299123327,
        },
    ),
    (
        "atterium",
        102,
        make_atterium_bundle,
        AtteriumSkipMoveRules,
        {
            "money_income": -86.63548300268323,
            "tax_income": 135.1502854047992,
            "trade_income": 28.52060736,
            "total_wastes": 272.13635772,
            "budget_final": 923.3645169973167,
        },
    ),
    (
        "isf",
        103,
        make_isf_bundle,
        IsfSkipMoveRules,
        {
            "money_income": -65.75725583182395,
            "tax_income": 174.13262342537942,
            "trade_income": 16.762085,
            "total_wastes": 272.13635772,
            "budget_final": 944.242744168176,
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
        calendar=TurnCalendar(6),
    )

    report = asdict(engine.run())

    assert report["mode"] == mode
    for key, value in expected.items():
        assert report[key] == pytest.approx(value)
