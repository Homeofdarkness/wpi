from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.basic_stats import IndustrialStats
from stats.industry_components import ResourceType
from stats.trade_text import parse_trade_configuration
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


EXAMPLES = Path(__file__).parents[1] / "test_files"


def test_icon_of_saan_example_runs_production_effects_and_sale() -> None:
    bundle = make_basic_bundle(budget=1_000_000)
    source = (EXAMPLES / "icon_of_saan_industry.toml").read_text(
        encoding="utf-8"
    )
    bundle.industry = IndustrialStats.from_stats_text(
        f"{bundle.industry}\n{source}"
    )
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )
    state.trade = parse_trade_configuration(
        (EXAMPLES / "icon_of_saan_trade.toml").read_text(encoding="utf-8"),
        state.industry,
    )

    icon = ResourceType("icon_of_saan")
    blessing = ResourceType(
        "the_blessing_of_the_eternal_ice_of_a_distant_homeland"
    )
    rule = next(
        item
        for item in state.industry.production_rules
        if item.rule_id == icon
    )
    for item in state.industry.production_rules:
        item.enabled = item is rule
    for resource in rule.inputs:
        resource_state = state.industry.resource_inventory.resources[resource]
        resource_state.stockpile = min(
            1_000.0, resource_state.storage_capacity
        )

    state.economy.trade_efficiency = 100
    state.economy.trade_usage = 0
    state.inner_politics.grace_of_the_highest = 20
    state.inner_politics.departure_from_truths = 50
    state.inner_politics.recalculate_derived_fields()
    decline_before = state.inner_politics.society_decline
    tax_before = state.economy.universal_tax

    report = TurnEngine(
        state=state,
        io=TestIO(),
        rng=np.random.default_rng(1),
    ).run()

    production = next(
        item for item in state.industry.last_production if item.rule_id == icon
    )
    effects = {
        item.effect_id: item
        for item in state.industry.last_effects
        if item.effect_id.startswith("icon_of_saan")
    }
    sale = state.trade.last_results[0]
    surplus_before_sale = (
        state.industry.resource_inventory.resources[icon].stockpile
        + sale.actual_delivery
    )

    assert state.industry.resource_inventory.resources[
        icon
    ].definition.name == ("Образок Саан")
    assert (
        state.industry.resource_inventory.resources[blessing].definition.name
        == "Благословление вечных льдов далёкой родины"
    )
    assert production.completed_batches > 0
    assert production.outputs_produced[icon] > 0
    assert state.industry.last_produced[icon] == pytest.approx(
        production.outputs_produced[icon]
    )
    resource_row = next(
        line
        for line in state.industry.render_resource_details().splitlines()
        if "Образок Саан [icon_of_saan]" in line
    )
    assert f"{production.outputs_produced[icon]:.1f}" in resource_row
    assert 18 <= surplus_before_sale <= 27
    assert state.industry.resource_shortages[icon] == 0
    assert (
        tax_before
        < effects["icon_of_saan_universal_tax"].target_after
        <= (tax_before * 1.02)
    )
    assert effects["icon_of_saan_grace"].target_after > 20
    assert state.inner_politics.society_decline < decline_before
    assert sale.actual_delivery > 0
    assert sale.money_balance > 0
    assert state.industry.last_trade_exported[icon] == pytest.approx(
        sale.actual_delivery
    )
    assert report.trade_deal_balance == pytest.approx(sale.money_balance)


def test_icon_example_has_balanced_cast_iron_and_coal_settings() -> None:
    bundle = make_basic_bundle()
    source = (EXAMPLES / "icon_of_saan_industry.toml").read_text(
        encoding="utf-8"
    )
    industry = IndustrialStats.from_stats_text(f"{bundle.industry}\n{source}")
    cast_iron = ResourceType("cast_iron")
    coal = ResourceType.COAL

    cast_rule = next(
        item
        for item in industry.production_rules
        if item.rule_id == "cast_iron"
    )
    coal_state = industry.resource_inventory.resources[coal]
    coal_operation = next(
        item
        for item in industry.extraction_operations
        if item.target == "solid_fuel"
    )
    stones_operation = next(
        item
        for item in industry.extraction_operations
        if item.target == "precious_stones"
    )

    assert industry.resource_demands[cast_iron] == 75
    assert cast_rule.batches == 520
    assert coal_state.stage.value == "steam"
    assert coal_operation.intensity == 70
    assert coal_operation.priority == 1
    assert stones_operation.intensity == 5
    assert stones_operation.priority == 1
