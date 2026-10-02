from __future__ import annotations

import numpy as np
import pytest

from functions.industry_models import (
    industrial_income_factor,
    industrial_readiness,
    industrial_strain,
)
from functions.trade_models import effective_quality_shares
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def make_engine(bundle, seed: int = 1) -> TurnEngine:
    return TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(),
        rng=np.random.default_rng(seed),
    )


def test_readiness_is_weighted_geometric_mean() -> None:
    components = {
        "technology": 64,
        "personnel": 81,
        "infrastructure": 100,
        "resources": 49,
        "institutions": 100,
        "market": 64,
    }

    result = industrial_readiness(components)

    expected = 100 * (
        0.64**0.20
        * 0.81**0.20
        * 1.00**0.20
        * 0.49**0.15
        * 1.00**0.10
        * 0.64**0.15
    )
    assert result == pytest.approx(expected)
    assert industrial_strain(result) == pytest.approx(100 - expected)


def test_geometric_readiness_exposes_a_single_weak_link() -> None:
    balanced = dict.fromkeys(
        (
            "technology",
            "personnel",
            "infrastructure",
            "resources",
            "institutions",
            "market",
        ),
        80.0,
    )
    bottlenecked = dict(balanced, resources=10.0)

    assert industrial_readiness(balanced) == pytest.approx(80.0)
    assert industrial_readiness(bottlenecked) < 60.0


def test_strain_reduces_income_by_no_more_than_a_quarter() -> None:
    assert industrial_income_factor(0) == 1.0
    assert industrial_income_factor(40) == pytest.approx(0.9)
    assert industrial_income_factor(100) == 0.75


def test_trade_quality_shift_is_temporary_and_preserves_total() -> None:
    original = (30.0, 40.0, 30.0)

    effective = effective_quality_shares(*original, industrial_strain=50)

    assert sum(effective) == pytest.approx(100.0)
    assert effective[0] < original[0]
    assert effective[2] > original[2]
    assert original == (30.0, 40.0, 30.0)


def test_turn_uses_temporary_quality_and_keeps_primary_stats() -> None:
    bundle = make_basic_bundle()
    bundle.industry.usages.append(50.0)
    original_quality = (
        bundle.economy.high_quality_percent,
        bundle.economy.mid_quality_percent,
        bundle.economy.low_quality_percent,
    )
    stability = bundle.economy.stability

    make_engine(bundle).run()

    readiness = bundle.industry.last_readiness
    assert readiness is not None
    assert readiness.strain == pytest.approx(100 - readiness.readiness)
    assert readiness.effective_high_quality < original_quality[0]
    assert (
        bundle.economy.high_quality_percent,
        bundle.economy.mid_quality_percent,
        bundle.economy.low_quality_percent,
    ) == original_quality
    assert bundle.economy.stability == stability
    report = bundle.industry.render_industrial_readiness_report()
    assert "ПРОМЫШЛЕННАЯ ГОТОВНОСТЬ И НАПРЯЖЁННОСТЬ" in report
    assert "Главные ограничения" in report
    assert "╫" in report
