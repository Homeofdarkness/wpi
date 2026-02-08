from __future__ import annotations

from modules.mode_spec import GameMode, ModeRegistry
from modules.run_skip_move import BasicSkipMove
from utils.user_io import TestIO

from tests.factories import make_basic_bundle, make_atterium_bundle, make_isf_bundle


def test_mode_registry_has_all_modes():
    modes = ModeRegistry.available()
    assert set(modes.keys()) == {GameMode.BASIC, GameMode.ATTERIUM, GameMode.ISF}


def test_mode_spec_factories_produce_engine_dependencies():
    spec = ModeRegistry.get(GameMode.BASIC)
    io = TestIO()
    b = make_basic_bundle(budget=1000.0)

    engine = BasicSkipMove(
        Economy=b.economy,
        Industry=b.industry,
        Agriculture=b.agriculture,
        InnerPolitics=b.inner_politics,
        InMoveFunctions=spec.in_move_functions_factory(),
        Rules=spec.rules_factory(),
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
        spec = ModeRegistry.get(mode)
        b = factory(budget=500.0)

        engine = BasicSkipMove(
            Economy=b.economy,
            Industry=b.industry,
            Agriculture=b.agriculture,
            InnerPolitics=b.inner_politics,
            InMoveFunctions=spec.in_move_functions_factory(),
            Rules=spec.rules_factory(),
            io=TestIO(),
            mode_name=spec.mode.value,
        )

        report = engine.run()
        assert report.mode == mode.value
