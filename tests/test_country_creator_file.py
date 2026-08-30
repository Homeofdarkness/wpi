from pathlib import Path

import numpy as np
import pytest

from create_basic_country import (
    advance_basic_country,
    create_basic_country,
    read_source,
    render_country,
)
from create_basic_country import (
    main as create_country_main,
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
    assert "fresh_water: {intensity: 90, priority: 3}" in source
    assert "schema_version: 2" in source
    assert "targets: [logistic, trade_efficiency]" in source
    assert "population_epidemic_chance" in source
    assert len(country.industry.effects) == 4


def test_country_creator_reads_and_wraps_an_industry_block(monkeypatch):
    answers = iter(
        (
            "schema_version: 2",
            "resources: {}",
            "extraction:",
            "  ferrous:",
            "    intensity: 80",
            "    priority: 2",
            "production: []",
            "effects: []",
            "",
        )
    )
    monkeypatch.setattr("builtins.input", lambda: next(answers))

    configuration = StatsInput._read_creator_industry_configuration()
    normalized = StatsInput._normalize_industry_configuration(configuration)

    assert normalized.startswith("НАСТРОЙКА ПРОМЫШЛЕННОСТИ YAML\n")
    assert "  ferrous:\n    intensity: 80" in normalized
    assert normalized.endswith("КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ")


def test_created_country_output_is_readable_and_has_control_section():
    text = render_country(create_basic_country(FIXTURE))

    assert "КОНТРОЛЬ" in text
    assert "Правящая сила - 80.0%" in text
    assert "НАСТРОЙКА ПРОМЫШЛЕННОСТИ" not in text
    assert "СОСТОЯНИЕ РЕСУРСОВ" in text
    assert "СОСТОЯНИЕ ГРУПП" in text
    assert "Природный запас" not in text
    assert "ПРОИЗВОДСТВО ЗА ХОД" not in text
    assert "Железо [iron]" in text
    assert "{" not in text
    assert "ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ" in text
    assert "freshwater_society:" in text
    assert "population_epidemic_chance" in text
    assert "ожидает расчёта хода" in text


def test_creator_cli_keeps_effect_visible_in_output_and_settings(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    output = tmp_path / "country.txt"
    settings = tmp_path / "industry_settings.txt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "create_basic_country.py",
            str(FIXTURE),
            "--output",
            str(output),
            "--industry-settings-output",
            str(settings),
        ],
    )

    create_country_main()

    country_text = output.read_text(encoding="utf-8")
    settings_text = settings.read_text(encoding="utf-8")
    console = capsys.readouterr().out
    assert "freshwater_society:" in country_text
    assert "contentment" in country_text
    assert "food_diversity" in country_text
    assert "population_epidemic_chance" in country_text
    assert "ожидает расчёта хода" in country_text
    assert "id: freshwater_society" in settings_text
    assert "Эффекты промышленности: 4" in console
    assert "добавьте --turns 1" in console


def test_creator_cli_can_run_a_real_turn_and_show_effect_results(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    output = tmp_path / "country_after_turn.txt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "create_basic_country.py",
            str(FIXTURE),
            "--output",
            str(output),
            "--turns",
            "1",
            "--seed",
            "1",
        ],
    )

    create_country_main()

    country_text = output.read_text(encoding="utf-8")
    settings_text = output.with_name(
        "country_after_turn_industry_settings.txt"
    ).read_text(encoding="utf-8")
    console = capsys.readouterr().out
    assert "ОТЧЁТ БЮДЖЕТА" in country_text
    assert "ОТЧЁТ ПРИРОСТА НАСЕЛЕНИЯ (3 МЕСЯЦА)" in country_text
    assert "Поправка формул ресурсов" in country_text
    assert "ПРОИЗВОДСТВО ЗА ХОД" in country_text
    assert "ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ" in country_text
    assert "freshwater_society:" in country_text
    assert "infrastructure_expenses" in country_text
    assert "932.8 -> 746.2 (-186.6)" in country_text
    assert "ожидает расчёта хода" not in country_text
    assert "turns: 5" in settings_text
    assert "Рассчитано ходов: 1" in console


def test_creator_rejects_negative_turn_count(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv", ["create_basic_country.py", "--turns", "-1"]
    )

    with pytest.raises(SystemExit):
        create_country_main()


def test_file_driven_turn_does_not_request_interactive_credit(capsys) -> None:
    country = create_basic_country(FIXTURE)
    country.economy.current_budget = -1_000_000

    reports = advance_basic_country(country, turns=1, seed=1)

    assert len(reports) == 1
    assert not reports[0].credit_taken
    assert reports[0].budget_final < 0
    assert "кредит автоматически не оформляется" in capsys.readouterr().out


def test_file_driven_creator_supports_multiple_real_turns() -> None:
    country = create_basic_country(FIXTURE)

    reports = advance_basic_country(country, turns=2, seed=1)

    assert len(reports) == 2
    assert country.industry.production_rules[0].turns_remaining == 4
    assert country.industry.production_rules[1].turns_remaining == 2
    assert len(country.industry.last_effects) == 7
    assert (
        "ожидает расчёта хода" not in country.industry.render_effect_results()
    )


def test_custom_resource_and_effect_survive_creator_turn_and_output(
    tmp_path,
) -> None:
    source = FIXTURE.read_text(encoding="utf-8")
    source = source.replace(
        "resources:\n  wood:\n",
        "resources:\n"
        "  moon_dust:\n"
        "    name: Лунная пыль\n"
        "    group: unique\n"
        "    availability: 75\n"
        "    quality: 85\n"
        "    consumption: 20\n"
        "    storage_capacity: 100\n"
        "  wood:\n",
        1,
    )
    source = source.replace(
        "КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ\n",
        "  - id: moon_dust_society\n"
        "    dependencies:\n"
        "      - resource: moon_dust\n"
        "    targets: [contentment, food_diversity]\n"
        "    formula: -target * resources.moon_dust.deficit * 0.1\n"
        "КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ\n",
        1,
    )
    source += "Лунная пыль [moon_dust] | 0 / 100 | 0 | 0\n"
    input_path = tmp_path / "custom_country.txt"
    input_path.write_text(source, encoding="utf-8")

    country = create_basic_country(input_path)
    reports = advance_basic_country(country, turns=1, seed=1)
    output = render_country(country)
    settings = country.industry.render_configuration()
    restored = IndustrialStats.from_stats_text(
        f"{country.industry}\n{settings}"
    )

    custom_resource = ResourceType("moon_dust")
    assert len(reports) == 1
    assert country.industry.resource_shortages[custom_resource] == 20
    assert country.inner_politics.contentment == 80
    assert "Лунная пыль [moon_dust]" in output
    assert "moon_dust_society:" in output
    assert "89.0 -> 80.0 (-9.0)" in output
    assert "moon_dust:\n    name: Лунная пыль" in settings
    assert "id: moon_dust_society" in settings
    assert custom_resource in restored.resource_inventory.resources
    assert any(effect.id == "moon_dust_society" for effect in restored.effects)


def test_checked_in_output_example_can_be_loaded_for_the_next_turn():
    text = OUTPUT_EXAMPLE.read_text(encoding="utf-8")
    settings = SETTINGS_EXAMPLE.read_text(encoding="utf-8")
    industry = IndustrialStats.from_stats_text(f"{text}\n{settings}")

    assert industry.active_resource_count() == 13
    assert industry.production_rules[0].turns_remaining == 5
    assert industry.resource_demands[ResourceType.IRON] == 300
    assert "{" not in text
    assert "freshwater_society:" in text


def test_edem_industry_configuration_resolves_a_full_first_turn():
    country = create_basic_country(FIXTURE)
    TurnEngine(
        state=country,
        rules=get_mode(GameMode.BASIC).rules_factory(),
        io=TestIO(inputs=[False]),
        mode_name="basic",
        rng=np.random.default_rng(20260718),
    ).run()

    assert country.industry.last_extracted[ResourceType.IRON] > 1_000
    assert len(country.industry.last_production) == 2
    assert country.industry.production_rules[0].turns_remaining == 5
    assert country.industry.production_rules[1].turns_remaining == 3
