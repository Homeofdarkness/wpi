from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.basic_stats import IndustrialStats
from stats.industry_components import (
    ExtractionGroup,
    ExtractionOperation,
    ResourceRegistration,
    ResourceType,
)
from stats.industry_text import CONFIG_END, CONFIG_START
from stats.production_components import ProductionRule
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


def register_production_resources(industry: IndustrialStats) -> None:
    industry.register_resource(
        ResourceType.IRON,
        stockpile=100,
        storage_capacity=100,
    )
    industry.register_resource(
        ResourceType.BASIC_BUILDING_MATERIALS,
        storage_capacity=1_000,
    )


def test_external_industry_format_is_human_readable_and_roundtrips():
    industry = make_basic_bundle().industry
    industry.register_resource(
        ResourceType.IRON,
        stockpile=25,
        storage_capacity=100,
        accessibility=80,
        quality=75,
    )
    industry.set_extraction_operation(
        ExtractionOperation(
            target=ExtractionGroup.FERROUS,
            intensity=40,
            priority=2,
        )
    )
    industry.register_resource(
        ResourceType.BASIC_BUILDING_MATERIALS,
        storage_capacity=100,
    )
    industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=12,
            turns_remaining=3,
            inputs={ResourceType.IRON: 2},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )
    state_text = str(industry)
    settings_text = industry.render_configuration()
    parsed = IndustrialStats.from_stats_text(f"{state_text}\n{settings_text}")

    assert CONFIG_START not in state_text
    assert CONFIG_END not in state_text
    assert "СОСТОЯНИЕ РЕСУРСОВ" in state_text
    assert "ПРОИЗВОДСТВО ЗА ХОД" not in state_text
    assert "РАБОЧАЯ СИЛА" not in settings_text
    assert "СОСТОЯНИЕ РЕСУРСОВ" not in settings_text
    assert "iron:\n    name: Железо" in settings_text
    assert "СОСТОЯНИЕ ГРУПП" in state_text
    assert "Чёрные металлы [ferrous]" in state_text
    assert "extraction:\n  ferrous:" in settings_text
    assert "active: true" in settings_text
    assert "id: iron_parts" in settings_text
    assert "{" not in state_text
    assert "ПРОМЫШЛЕННОЕ_СОСТОЯНИЕ:" not in settings_text
    assert (
        parsed.resource_inventory.resources[ResourceType.IRON].stockpile == 25
    )
    assert parsed.production_rules == industry.production_rules


def test_external_industry_numbers_have_at_most_one_decimal_place():
    industry = make_basic_bundle().industry
    industry.register_resource(
        ResourceType.IRON,
        stockpile=12.345,
        storage_capacity=100,
        accessibility=82.345,
    )
    industry.last_extracted = {ResourceType.IRON: 45.678}
    industry.resource_shortages = {ResourceType.IRON: 1.234}

    state_text = str(industry)
    settings_text = industry.render_configuration()

    assert "12.3 / 100" in state_text
    assert "45.7" in state_text
    assert "1.2" in state_text
    assert "storage_capacity: 100.0" in settings_text
    resource_row = next(
        line for line in state_text.splitlines() if "Железо [iron]" in line
    )
    assert re.search(r"\d+\.\d{2,}", resource_row) is None
    assert "availability: 82.3" in settings_text


def test_arbitrary_resource_roundtrips_without_a_global_catalog_entry():
    industry = make_basic_bundle().industry
    custom = ResourceType("reinforced_glass")
    industry.register_resource(
        ResourceRegistration(
            resource=custom,
            name="Армированное стекло",
            group=ExtractionGroup.CONSTRUCTION,
            stockpile=25,
            storage_capacity=300,
            accessibility=72,
            quality=81,
            consumption_per_turn=20,
        )
    )

    settings = industry.render_configuration()
    parsed = IndustrialStats.from_stats_text(f"{industry}\n{settings}")
    restored = parsed.resource_inventory.resources[custom]

    assert "reinforced_glass:\n    name: Армированное стекло" in settings
    assert restored.definition.name == "Армированное стекло"
    assert restored.definition.group is ExtractionGroup.CONSTRUCTION
    assert restored.stockpile == 25
    assert parsed.resource_demands[custom] == 20


def test_checked_in_custom_resource_example_is_executable() -> None:
    path = (
        Path(__file__).parents[1]
        / "test_files"
        / "custom_resource_industry_example.txt"
    )
    bundle = make_basic_bundle(budget=1_000_000_000)
    bundle.industry = IndustrialStats.from_stats_text(
        f"{bundle.industry.render_pretty()}\n"
        f"{path.read_text(encoding='utf-8')}"
    )

    make_engine(bundle, seed=706).run()

    custom = ResourceType("reinforced_glass")
    assert bundle.industry.last_production[0].completed_batches > 0
    assert bundle.industry.last_production[0].outputs_produced[custom] > 0
    assert bundle.industry.resource_shortages[custom] == 0
    assert {effect.target for effect in bundle.industry.last_effects} == {
        "infrastructure_expenses",
        "logistic",
        "civil_efficiency",
        "industrial_accident_chance",
    }


def test_storage_limit_is_a_setting_and_workforce_is_not():
    industry = make_basic_bundle().industry
    industry.register_resource(
        ResourceType.IRON,
        stockpile=25,
        storage_capacity=100,
    )
    settings = industry.render_configuration()

    assert "storage_capacity: 100.0" in settings
    assert "25 / 100" not in settings
    assert "РАБОЧАЯ СИЛА" not in settings
    assert "25 / 100" in str(industry)

    parsed = IndustrialStats.from_stats_text(f"{industry}\n{settings}")
    iron = parsed.resource_inventory.resources[ResourceType.IRON]
    assert iron.storage_capacity == 100
    assert iron.stockpile == 25

    invalid = settings.replace(
        "schema_version: 2", "schema_version: 2\nworkforce: {}"
    )
    with pytest.raises(ValueError, match="Некорректная настройка"):
        IndustrialStats.from_stats_text(
            f"{industry.render_pretty()}\n{invalid}"
        )


def test_human_can_edit_rule_batches_and_duration_in_text():
    industry = make_basic_bundle().industry
    register_production_resources(industry)
    industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=10,
            turns_remaining=2,
            inputs={ResourceType.IRON: 2},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )
    settings = industry.render_configuration().replace(
        "batches: 10.0\n    turns: 2",
        "batches: 25.0\n    turns: 4",
    )

    parsed = IndustrialStats.from_stats_text(f"{industry}\n{settings}")
    rule = parsed.production_rules[0]

    assert rule.batches == 25
    assert rule.turns_remaining == 4


def test_production_status_explains_why_there_is_no_result():
    empty = make_basic_bundle().industry
    assert "не загружены" in empty.render_production_results()

    register_production_resources(empty)
    empty.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=1,
            inputs={ResourceType.IRON: 1},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )
    assert "ещё не рассчитывался" in empty.render_production_results()

    without_settings = str(empty)
    with pytest.raises(ValueError, match="нужен отдельный блок"):
        IndustrialStats.from_stats_text(without_settings)


def test_external_format_reports_typos_and_incomplete_blocks():
    industry = make_basic_bundle().industry
    register_production_resources(industry)
    industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=10,
            inputs={ResourceType.IRON: 2},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )
    text = industry.render_configuration()
    snapshot = f"{industry.render_pretty()}\n{text}"

    with pytest.raises(ValueError, match="Некорректная настройка"):
        IndustrialStats.from_stats_text(
            snapshot.replace("batches: 10.0", "batchess: 10.0")
        )
    with pytest.raises(ValueError, match="ровно один полный .*блок"):
        IndustrialStats.from_stats_text(snapshot.replace(CONFIG_END, ""))

    with pytest.raises(ValueError, match="Старый строковый формат"):
        IndustrialStats.from_stats_text(
            f"{industry.render_pretty()}\n"
            "НАСТРОЙКА ПРОМЫШЛЕННОСТИ\nГРУППЫ\n"
            f"{CONFIG_END}"
        )


def test_external_format_rejects_unregistered_rule_resources():
    industry = make_basic_bundle().industry
    industry.register_resource(
        ResourceType.IRON,
        stockpile=10,
        storage_capacity=10,
    )
    industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=1,
            inputs={ResourceType.IRON: 1},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )

    with pytest.raises(ValueError, match="незарегистрированные ресурсы"):
        IndustrialStats.from_stats_text(
            f"{industry.render_pretty()}\n{industry.render_configuration()}"
        )


def test_multi_turn_rule_expires_after_configured_number_of_turns():
    bundle = make_basic_bundle(budget=1_000_000_000)
    register_production_resources(bundle.industry)
    rule = ProductionRule(
        rule_id="iron_parts",
        name="Железные детали",
        batches=5,
        turns_remaining=2,
        inputs={ResourceType.IRON: 2},
        outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
    )
    bundle.industry.set_production_rule(rule)
    engine = make_engine(bundle, seed=700)

    engine.run()
    assert rule.enabled
    assert rule.turns_remaining == 1
    assert len(bundle.industry.last_production) == 1

    engine.run()
    assert not rule.enabled
    assert rule.turns_remaining == 0
    assert len(bundle.industry.last_production) == 1

    engine.run()
    assert bundle.industry.last_production == []


def test_post_turn_configuration_roundtrip_preserves_operational_state():
    bundle = make_basic_bundle()
    register_production_resources(bundle.industry)
    bundle.industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=5,
            turns_remaining=2,
            inputs={ResourceType.IRON: 2},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )
    make_engine(bundle, seed=702).run()

    snapshot = f"{bundle.industry}\n{bundle.industry.render_configuration()}"
    parsed = IndustrialStats.from_stats_text(snapshot)
    original_iron = bundle.industry.resource_inventory.resources[
        ResourceType.IRON
    ]
    parsed_iron = parsed.resource_inventory.resources[ResourceType.IRON]

    assert parsed_iron.stockpile == pytest.approx(
        original_iron.stockpile,
        abs=0.051,
    )
    assert parsed.workforce.auto_size
    assert parsed.production_rules[0].turns_remaining == 1


def test_rule_is_limited_by_available_inputs_and_reports_actual_use():
    bundle = make_basic_bundle()
    bundle.industry.register_resource(
        ResourceType.IRON,
        stockpile=5,
        storage_capacity=5,
    )
    bundle.industry.register_resource(
        ResourceType.BASIC_BUILDING_MATERIALS,
        storage_capacity=100,
    )
    bundle.industry.set_production_rule(
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=10,
            turns_remaining=1,
            inputs={ResourceType.IRON: 2},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    )

    make_engine(bundle, seed=701).run()
    result = bundle.industry.last_production[0]

    assert result.completed_batches < result.requested_batches
    assert result.inputs_spent[ResourceType.IRON] <= 5
    assert "Взято: Железо" in bundle.industry.render_production_results()
    assert "Выпущено: Базовые стройматериалы" in (
        bundle.industry.render_production_results()
    )


def test_resource_and_extraction_rules_are_registered_separately():
    industry = make_basic_bundle().industry
    operation = ExtractionOperation(
        target=ExtractionGroup.FERROUS,
        intensity=100,
        priority=1,
    )
    state = industry.register_resource(
        ResourceRegistration(
            resource=ResourceType.IRON,
            stockpile=10,
            storage_capacity=200,
            consumption_per_turn=12,
        )
    )
    industry.set_extraction_operation(operation)

    assert state.enabled
    assert industry.resource_demands[ResourceType.IRON] == 12
    assert "Лесное хозяйство [forestry]" in str(industry)
    assert "Уникальные ресурсы [unique]" in str(industry)
    assert industry.extraction_operations == [operation]

    industry.set_extraction_operation(
        ExtractionOperation(target="unknown", intensity=100)
    )
    with pytest.raises(ValueError, match="Неизвестная цель добычи"):
        industry.validate_industry_configuration()


def test_group_and_resource_extraction_share_workers_automatically():
    bundle = make_basic_bundle(budget=1_000_000_000)
    industry = bundle.industry
    industry.workforce.auto_size = False
    industry.workforce.ordinary_workers = 5_000
    industry.workforce.specialist_workers = 100
    for resource in (ResourceType.IRON, ResourceType.OTHER_FERROUS):
        industry.register_resource(
            resource,
            storage_capacity=10_000,
        )
    industry.set_extraction_operation(
        ExtractionOperation(
            target=ExtractionGroup.FERROUS,
            intensity=80,
            priority=1,
        )
    )
    industry.set_extraction_operation(
        ExtractionOperation(
            target=ResourceType.IRON,
            intensity=100,
            priority=2,
        )
    )

    make_engine(bundle, seed=704).run()

    assert industry.last_extracted[ResourceType.IRON] > 0
    assert industry.last_extracted[ResourceType.OTHER_FERROUS] > 0
    assert (
        industry.last_extracted[ResourceType.IRON]
        > (industry.last_extracted[ResourceType.OTHER_FERROUS])
    )
    assert not hasattr(industry.extraction_operations[0], "ordinary_workers")
    rendered = industry.render_configuration()
    assert "extraction:\n  ferrous:" in rendered
    assert "\n  iron:\n    intensity:" in rendered


def test_group_production_rule_roundtrips_and_produces_group_outputs():
    bundle = make_basic_bundle(budget=1_000_000_000)
    industry = bundle.industry
    industry.register_resource(
        ResourceType.IRON,
        stockpile=100,
        storage_capacity=100,
    )
    for resource in (
        ResourceType.BASIC_BUILDING_MATERIALS,
        ResourceType.EXPENSIVE_BUILDING_MATERIALS,
    ):
        industry.register_resource(resource, storage_capacity=100)
    industry.set_production_rule(
        ProductionRule(
            rule_id="construction_mix",
            name="Комплект стройматериалов",
            target_group=ExtractionGroup.CONSTRUCTION,
            batches=10,
            turns_remaining=2,
            inputs={ResourceType.IRON: 1},
            outputs={
                ResourceType.BASIC_BUILDING_MATERIALS: 0.75,
                ResourceType.EXPENSIVE_BUILDING_MATERIALS: 0.25,
            },
        )
    )

    parsed = IndustrialStats.from_stats_text(
        f"{industry}\n{industry.render_configuration()}"
    )
    assert parsed.production_rules[0].target_group is (
        ExtractionGroup.CONSTRUCTION
    )

    make_engine(bundle, seed=705).run()
    inventory = industry.resource_inventory.resources
    assert inventory[ResourceType.BASIC_BUILDING_MATERIALS].stockpile > 0
    assert inventory[ResourceType.EXPENSIVE_BUILDING_MATERIALS].stockpile > 0
