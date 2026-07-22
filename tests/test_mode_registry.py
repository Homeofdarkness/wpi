from __future__ import annotations

from modules.mode_spec import GameMode, available_modes, get_mode
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from tests.factories import (
    make_atterium_bundle,
    make_basic_bundle,
    make_isf_bundle,
)
from utils.user_io import TestIO


def test_mode_registry_has_all_modes():
    modes = available_modes()
    assert set(modes.keys()) == {
        GameMode.BASIC,
        GameMode.ATTERIUM,
        GameMode.ISF,
    }


def test_mode_spec_factories_produce_engine_dependencies():
    spec = get_mode(GameMode.BASIC)
    io = TestIO()
    b = make_basic_bundle(budget=1000.0)

    engine = TurnEngine(
        state=WorldState(
            economy=b.economy,
            industry=b.industry,
            agriculture=b.agriculture,
            inner_politics=b.inner_politics,
        ),
        rules=spec.rules_factory(),
        io=io,
        mode_name=spec.mode.value,
    )

    report = engine.run()
    assert report.mode == "basic"


def test_other_modes_can_be_built_via_mode_registry():
    for mode, factory in [
        (GameMode.ATTERIUM, make_atterium_bundle),
        (GameMode.ISF, make_isf_bundle),
    ]:
        spec = get_mode(mode)
        b = factory(budget=500.0)

        engine = TurnEngine(
            state=WorldState(
                economy=b.economy,
                industry=b.industry,
                agriculture=b.agriculture,
                inner_politics=b.inner_politics,
            ),
            rules=spec.rules_factory(),
            io=TestIO(),
            mode_name=spec.mode.value,
        )

        report = engine.run()
        assert report.mode == mode.value
