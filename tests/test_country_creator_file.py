from pathlib import Path

import numpy as np

from create_basic_country import (
    create_basic_country,
    read_source,
    render_country,
)
from modules.mode_spec import GameMode, get_mode
from modules.run_skip_move import TurnEngine
from modules.run_start_skip import StatsInput
from stats.basic_stats import IndustrialStats
from stats.industry_components import ResourceType
from utils.user_io import TestIO


FIXTURE = Path(__file__).parents[1] / "test_files" / "edem_country_input.txt"
OUTPUT_EXAMPLE = (
    Path(__file__).parents[1]
    / "test_files"
    / "edem_country_output_example.txt"
)
SETTINGS_EXAMPLE = (
    Path(__file__).parents[1]
    / "test_files"
    / "edem_country_industry_settings_example.txt"
)


def test_file_creator_reads_answers_and_human_industry_configuration():
    answers, configuration = read_source(FIXTURE)
    country = create_basic_country(FIXTURE)

    assert len(answers) == 81
    assert configuration is not None
    assert country.industry.active_resource_count() == 13
    assert country.industry.workforce.auto_size
    assert "РАБОЧАЯ СИЛА" not in configuration
    assert len(country.industry.production_rules) == 2
    assert country.industry.production_rules[0].turns_remaining == 6
    assert (
        country.industry.resource_inventory.resources[
            ResourceType.IRON
        ].stockpile
        == 8_000
    )
    source = FIXTURE.read_text(encoding="utf-8")
    assert "Добыча fresh_water | интенсивность=90 | приоритет=3" in source
    assert "Добыча группы" not in source
    assert "Добыча ресурса" not in source


def test_country_creator_reads_and_wraps_an_industry_block(monkeypatch):
    answers = iter(
        (
            "ГРУППЫ",
            "Группа Чёрные металлы [ferrous]",
            "ДОБЫЧА",
            "# Комментарий из input-файла должен быть безопасен.",
            "Добыча ferrous | интенсивность=80 | приоритет=2",
            "",
        )
    )
    monkeypatch.setattr("builtins.input", lambda: next(answers))

    configuration = StatsInput._read_creator_industry_configuration()
    normalized = StatsInput._normalize_industry_configuration(configuration)

    assert normalized.startswith("НАСТРОЙКА ПРОМЫШЛЕННОСТИ\n")
    assert "Добыча ferrous | интенсивность=80 | приоритет=2" in normalized
    assert "# Комментарий" not in normalized
    assert normalized.endswith("КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ")


def test_created_country_output_is_readable_and_has_control_section():
    text = render_country(create_basic_country(FIXTURE))

    assert "КОНТРОЛЬ" in text
    assert "Правящая сила - 80.0%" in text
    assert "НАСТРОЙКА ПРОМЫШЛЕННОСТИ" not in text
    assert "СОСТОЯНИЕ РЕСУРСОВ" in text
    assert "Природный запас" not in text
    assert "ПРОИЗВОДСТВО ЗА ХОД" not in text
    assert "Железо [iron]" in text
    assert "{" not in text


def test_checked_in_output_example_can_be_loaded_for_the_next_turn():
    text = OUTPUT_EXAMPLE.read_text(encoding="utf-8")
    settings = SETTINGS_EXAMPLE.read_text(encoding="utf-8")
    industry = IndustrialStats.from_stats_text(f"{text}\n{settings}")

    assert industry.active_resource_count() == 13
    assert industry.production_rules[0].turns_remaining == 5
    assert industry.resource_demands[ResourceType.IRON] == 300
    assert "{" not in text


def test_edem_industry_configuration_resolves_a_full_first_turn():
    country = create_basic_country(FIXTURE)
    TurnEngine(
        state=country,
        rules=get_mode(GameMode.BASIC).rules_factory(),
        io=TestIO(inputs=[False]),
        mode_name="basic",
        rng=np.random.default_rng(20260718),
    ).run()

    assert country.industry.last_extracted[ResourceType.IRON] > 2_000
    assert len(country.industry.last_production) == 2
    assert country.industry.production_rules[0].turns_remaining == 5
    assert country.industry.production_rules[1].turns_remaining == 3
