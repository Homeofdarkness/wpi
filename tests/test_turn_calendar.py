from __future__ import annotations

import numpy as np
import pytest

from functions.time_models import TurnCalendar, format_months
from modules.run_finalize import (
    render_budget_report,
    render_population_growth_report,
)
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.industry_components import ResourceType
from stats.production_components import ProductionRule
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


@pytest.mark.parametrize(
    ("months", "expected"),
    (
        (1, "1 месяц"),
        (2, "2 месяца"),
        (5, "5 месяцев"),
        (9, "9 месяцев"),
        (12, "12 месяцев"),
        (21, "21 месяц"),
    ),
)
def test_month_label_uses_russian_plural_form(
    months: int,
    expected: str,
) -> None:
    assert format_months(months) == expected


@pytest.mark.parametrize("value", (0, -1))
def test_calendar_rejects_non_positive_duration(value: int) -> None:
    with pytest.raises(ValueError):
        TurnCalendar(value)


@pytest.mark.parametrize("value", (True, 2.5, "3"))
def test_calendar_rejects_non_integer_duration(value) -> None:
    with pytest.raises(TypeError):
        TurnCalendar(value)


def test_calendar_scales_reference_flows_and_bounded_progress() -> None:
    quarter = TurnCalendar(3)
    nine_months = TurnCalendar(9)

    assert quarter.years == pytest.approx(0.25)
    assert nine_months.years == pytest.approx(0.75)
    assert quarter.scale_flow(120) == pytest.approx(60)
    assert nine_months.scale_flow(120) == pytest.approx(180)
    assert quarter.scale_progress(0.36) == pytest.approx(0.2)
    assert nine_months.scale_progress(0.36) == pytest.approx(0.488)
    assert quarter.scale_retention(81) == pytest.approx(90)
    assert nine_months.scale_retention(81) == pytest.approx(72.9)


def test_nine_month_turn_uses_calendar_in_engine_and_reports() -> None:
    bundle = make_basic_bundle(budget=1_000_000)
    bundle.economy.decrement_coefficient = 0
    bundle.economy.public_debt = 1_000
    bundle.economy.annual_interest_rate = 10
    bundle.agriculture.environmental_food = 1_000_000

    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    material = bundle.industry.resource_inventory.resources[
        ResourceType.BASIC_BUILDING_MATERIALS
    ]
    iron.enabled = True
    iron.stockpile = 1_000
    iron.storage_capacity = 1_000
    material.enabled = True
    material.storage_capacity = 1_000
    bundle.industry.production_rules = [
        ProductionRule(
            rule_id="iron_parts",
            name="Железные детали",
            batches=10,
            turns_remaining=2,
            inputs={ResourceType.IRON: 1},
            outputs={ResourceType.BASIC_BUILDING_MATERIALS: 1},
        )
    ]

    report = TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(),
        rng=np.random.default_rng(42),
        calendar=TurnCalendar(9),
    ).run()

    growth = report.population_growth
    production = bundle.industry.last_production[0]
    assert growth is not None
    assert report.turn_months == 9
    assert report.debt_interest == pytest.approx(75)
    assert production.requested_batches == pytest.approx(15)
    assert production.turns_remaining == pytest.approx(0.5)
    assert "months = 3" in bundle.industry.render_configuration()
    assert "ОТЧЁТ БЮДЖЕТА (9 МЕСЯЦЕВ)" in render_budget_report(report)
    assert "(9 МЕСЯЦЕВ)" in render_population_growth_report(report)
