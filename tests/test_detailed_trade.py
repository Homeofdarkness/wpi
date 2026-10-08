from __future__ import annotations

import pytest

from functions.trade_deal_models import route_fulfillment_factor
from modules.run_finalize import render_budget_report
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.industry_components import (
    ExtractionGroup,
    IndustrialStage,
    ResourceRegistration,
    ResourceType,
)
from stats.trade_text import parse_trade_configuration
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def _state_with_resources(
    resources: list[tuple[str, ExtractionGroup, float, float, float]],
) -> WorldState:
    bundle = make_basic_bundle()
    bundle.economy.trade_efficiency = 100
    bundle.economy.trade_usage = 0
    for alias, group, stockpile, capacity, monthly_demand in resources:
        bundle.industry.register_resource(
            ResourceRegistration(
                resource=ResourceType(alias),
                name=alias,
                group=group,
                stage=IndustrialStage.MANUAL,
                stockpile=stockpile,
                storage_capacity=capacity,
                consumption_per_month=monthly_demand,
            )
        )
    return WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )


def test_trade_configuration_roundtrip_and_rejects_remote_country_fields():
    state = _state_with_resources(
        [
            ("copper", ExtractionGroup.NONFERROUS, 100, 500, 0),
            ("fresh_water", ExtractionGroup.FRESH_WATER, 0, 1_000, 50),
        ]
    )
    source = """
schema_version = 2

[[deals]]
id = "water_import"
direction = "import"
delivery = { target = "resource:fresh_water", amount_per_month = 50.0 }
payment = { target = "resource:copper", amount_per_month = 10.0 }
"""

    parsed = parse_trade_configuration(source, state.industry)
    reparsed = parse_trade_configuration(
        parsed.render_configuration(),
        state.industry,
    )

    assert reparsed.deals == parsed.deals
    with pytest.raises(ValueError, match="extra_forbidden"):
        parse_trade_configuration(
            source.replace(
                'direction = "import"',
                'direction = "import"\ncountry = "country_b"',
            ),
            state.industry,
        )
    with pytest.raises(ValueError, match="give|delivery"):
        parse_trade_configuration(
            source.replace("delivery =", "give =").replace(
                "payment =", "receive ="
            ),
            state.industry,
        )
    with pytest.raises(ValueError, match="schema_version = 1 устарел"):
        parse_trade_configuration(
            source.replace("schema_version = 2", "schema_version = 1"),
            state.industry,
        )


def test_partial_barter_scales_both_legs_and_import_reduces_shortage():
    state = _state_with_resources(
        [
            ("copper", ExtractionGroup.NONFERROUS, 60, 500, 0),
            ("fresh_water", ExtractionGroup.FRESH_WATER, 0, 2_000, 250),
        ]
    )
    state.trade = parse_trade_configuration(
        """
schema_version = 2
[[deals]]
id = "water_import"
direction = "import"
delivery = { target = "resource:fresh_water", amount_per_month = 250.0 }
payment = { target = "resource:copper", amount_per_month = 50.0 }
""",
        state.industry,
    )

    TurnEngine(state=state, io=TestIO()).run()

    result = state.trade.last_results[0]
    assert result.planned_delivery == 750
    assert result.planned_payment == 150
    assert result.actual_delivery == pytest.approx(300)
    assert result.actual_payment == pytest.approx(60)
    assert result.fulfillment == pytest.approx(0.4)
    assert state.industry.resource_shortages[ResourceType.FRESH_WATER] < 750


def test_same_contract_terms_reverse_local_flows_only_by_direction():
    resources = [
        ("copper", ExtractionGroup.NONFERROUS, 100, 1_000, 0),
        ("fresh_water", ExtractionGroup.FRESH_WATER, 500, 1_000, 0),
    ]
    importer = _state_with_resources(resources)
    exporter = _state_with_resources(resources)
    terms = """
schema_version = 2
[[deals]]
id = "water_trade"
direction = "DIRECTION"
delivery = { target = "resource:fresh_water", amount_per_month = 100.0 }
payment = { target = "resource:copper", amount_per_month = 20.0 }
"""
    importer.trade = parse_trade_configuration(
        terms.replace("DIRECTION", "import"),
        importer.industry,
    )
    exporter.trade = parse_trade_configuration(
        terms.replace("DIRECTION", "export"),
        exporter.industry,
    )

    TurnEngine(state=importer, io=TestIO()).run()
    TurnEngine(state=exporter, io=TestIO()).run()

    import_result = importer.trade.last_results[0]
    export_result = exporter.trade.last_results[0]
    assert import_result.actual_delivery == pytest.approx(300)
    assert export_result.actual_delivery == pytest.approx(300)
    assert import_result.actual_payment == pytest.approx(60)
    assert export_result.actual_payment == pytest.approx(60)
    assert importer.industry.last_trade_imported[ResourceType.FRESH_WATER] == (
        pytest.approx(300)
    )
    assert importer.industry.last_trade_exported[ResourceType.COPPER] == (
        pytest.approx(60)
    )
    assert exporter.industry.last_trade_exported[ResourceType.FRESH_WATER] == (
        pytest.approx(300)
    )
    assert exporter.industry.last_trade_imported[ResourceType.COPPER] == (
        pytest.approx(60)
    )


def test_group_import_closes_largest_current_shortages_first():
    state = _state_with_resources(
        [
            ("sand", ExtractionGroup.CONSTRUCTION, 0, 1_000, 80),
            ("stone", ExtractionGroup.CONSTRUCTION, 0, 1_000, 20),
        ]
    )
    state.trade = parse_trade_configuration(
        """
schema_version = 2
[[deals]]
id = "construction_import"
direction = "import"
delivery = { target = "group:construction", amount_per_month = 100.0 }
payment = { target = "money", amount_per_month = 10.0 }
""",
        state.industry,
    )

    TurnEngine(state=state, io=TestIO()).run()

    allocations = state.trade.last_results[0].delivery_allocations
    assert allocations["sand"] == pytest.approx(240)
    assert allocations["stone"] == pytest.approx(60)
    assert state.trade.last_money_balance < 0


def test_monetary_export_is_separate_in_ledger_and_report():
    state = _state_with_resources(
        [("wood", ExtractionGroup.FORESTRY, 350, 1_000, 50)]
    )
    state.trade = parse_trade_configuration(
        """
schema_version = 2
[[deals]]
id = "wood_export"
direction = "export"
delivery = { target = "resource:wood", amount_per_month = 100.0 }
payment = { target = "money", amount_per_month = 40.0 }
""",
        state.industry,
    )

    stability_before = state.economy.stability
    report = TurnEngine(state=state, io=TestIO()).run()

    result = state.trade.last_results[0]
    assert 0 < result.actual_delivery < result.planned_delivery
    assert result.money_balance > 0
    assert report.trade_deal_balance == pytest.approx(result.money_balance)
    assert state.economy.stability == stability_before
    assert report.ledger is not None
    expected_gross = (
        report.tax_income
        + report.trade_income
        + report.branches_income
        + report.industry_income
        + report.science_income
        + report.resource_balance
        + report.trade_deal_balance
    )
    assert report.ledger.gross_income == pytest.approx(expected_gross)
    assert "Баланс настроенных сделок" in render_budget_report(report)
    trade_report = state.trade.render_turn_report(report.turn_months)
    assert "wood_export · ЭКСПОРТ" in trade_report
    assert "Предмет поставки" in trade_report
    assert "Локально отдано" in trade_report
    assert "Денежный результат" in trade_report
    assert "╫" in trade_report


def test_trade_efficiency_and_route_overload_reduce_fulfillment():
    perfect = route_fulfillment_factor(100, 0, 10)
    weak = route_fulfillment_factor(20, 0, 10)
    overloaded = route_fulfillment_factor(100, 25, 10)

    assert perfect == 1
    assert 0 < weak < perfect
    assert 0 < overloaded < perfect
