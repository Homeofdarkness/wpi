from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from functions.time_models import TURN_SCALE
from modules.mode_spec import GameMode, get_mode
from modules.run_skip_move import TurnEngine
from modules.run_start_skip import InputMode, StatsInput, read_text_section
from stats.industry_components import ResourceType
from utils.user_io import TestIO


ROOT = Path(__file__).parents[1]
EXAMPLE_DIRECTORY = ROOT / "test_files" / "moves_skipper_example"
EXAMPLE_FILES = tuple(
    EXAMPLE_DIRECTORY / name
    for name in (
        "01_economy_and_trade.txt",
        "02_industry.txt",
        "03_industry_settings.toml",
        "04_agriculture.txt",
        "05_government_control_people.txt",
    )
)


def test_fenced_reader_preserves_internal_blank_lines(monkeypatch):
    answers = iter(
        (
            "```",
            "ЭКОНОМИКА",
            "Население - 1000000",
            "",
            "ТОРГОВЛЯ",
            "Торговый ранг - 2",
            "```",
        )
    )
    monkeypatch.setattr("builtins.input", lambda: next(answers))

    result = read_text_section("=== ЭКОНОМИКА ===")

    assert "Население - 1000000\n\nТОРГОВЛЯ" in result
    assert result.endswith("```")


def test_legacy_reader_still_ends_on_one_blank_line(monkeypatch):
    answers = iter(("ЭКОНОМИКА", "Население - 1000000", "", "unused"))
    monkeypatch.setattr("builtins.input", lambda: next(answers))

    result = read_text_section("=== ЭКОНОМИКА ===")

    assert result == "ЭКОНОМИКА\nНаселение - 1000000"
    assert next(answers) == "unused"


def test_moves_skipper_reads_current_pretty_output_and_runs_rules(
    monkeypatch,
    capsys,
):
    answers_list: list[str] = []
    for path in EXAMPLE_FILES:
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines[0].startswith("```"):
            assert lines[-1] == "```"
            lines = lines[1:-1]
        answers_list.extend(lines)
        if path.suffix == ".toml":
            answers_list.extend(("", ""))
        else:
            answers_list.append("")
    answers = iter(answers_list)
    monkeypatch.setattr("builtins.input", lambda: next(answers))

    state = StatsInput(
        config=get_mode(GameMode.BASIC).stats_config,
        mode=InputMode.MOVES_SKIPPER,
    ).read()
    engine = TurnEngine(
        state=state,
        rules=get_mode(GameMode.BASIC).rules_factory(),
        io=TestIO(inputs=[False]),
        rng=np.random.default_rng(20260719),
    )
    engine.run()
    prompts = capsys.readouterr().out

    assert "=== ЭКОНОМИКА И ТОРГОВЛЯ ===" in prompts
    assert "=== ГОСУДАРСТВО, КОНТРОЛЬ И НАРОД ===" in prompts
    assert "=== ТОРГОВЛЯ ===" not in prompts
    assert "=== НАРОД ===" not in prompts
    assert state.economy.trade_rank == 37
    assert state.inner_politics.control == [80.0, 10.0, 5.0, 5.0]
    assert state.industry.last_extracted[ResourceType.IRON] > 0
    assert len(state.industry.last_production) == 2
    assert state.industry.production_rules[0].turns_remaining == pytest.approx(
        6 - TURN_SCALE
    )
    assert {effect.target for effect in state.industry.last_effects} >= {
        "logistic",
        "trade_efficiency",
        "contentment",
        "food_diversity",
        "population_epidemic_chance",
    }
