from __future__ import annotations

import numpy as np
import pytest

from functions.agriculture_models import food_security_index
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def _engine_for(bundle) -> TurnEngine:
    return TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(),
        rng=np.random.default_rng(1),
    )


@pytest.mark.parametrize(
    ("produced", "consumed", "expected"),
    ((100, 100, 100), (107.2, 100, 107.2), (75, 100, 75)),
)
def test_food_security_is_a_unitless_coverage_index(
    produced: float,
    consumed: float,
    expected: float,
) -> None:
    assert food_security_index(produced, consumed) == pytest.approx(expected)


def test_food_supplies_cover_a_shortage_before_hunger() -> None:
    bundle = make_basic_bundle()
    bundle.agriculture.workers_percent = 0
    bundle.agriculture.environmental_food = 0
    bundle.agriculture.food_supplies = 1_000
    bundle.economy.decrement_coefficient = 0
    population_before = bundle.economy.population_count

    _engine_for(bundle).run()

    assert bundle.agriculture.food_security == pytest.approx(100.0)
    assert 0 < bundle.agriculture.food_supplies < 1_000
    assert bundle.economy.population_count == (
        population_before + round(bundle.economy.income)
    )


def test_uncovered_shortage_reduces_security_and_population() -> None:
    bundle = make_basic_bundle()
    bundle.agriculture.workers_percent = 0
    bundle.agriculture.environmental_food = 0
    bundle.agriculture.food_supplies = 0
    population_before = bundle.economy.population_count

    _engine_for(bundle).run()

    assert bundle.agriculture.food_security == 0
    assert bundle.economy.population_count < population_before
