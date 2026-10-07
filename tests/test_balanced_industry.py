from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from create_basic_country import create_basic_country
from functions.agriculture_models import resource_security_update
from functions.resource_models import (
    GROUP_PROFILES,
    extraction_output,
    extraction_priority_weight,
)
from modules.run_skip_move import TurnEngine
from stats.basic_stats import IndustrialStats
from stats.industry_components import (
    ExtractionGroup,
    IndustrialStage,
    ResourceState,
    ResourceType,
)
from utils.user_io import TestIO


ROOT = Path(__file__).parents[1]
BALANCED_CONFIG = ROOT / "test_files" / "balanced_industry_example.toml"


def _balanced_country():
    country = create_basic_country(
        ROOT / "test_files" / "edem_country_input.txt"
    )
    configuration = BALANCED_CONFIG.read_text(encoding="utf-8")
    country.industry = IndustrialStats.from_stats_text(
        f"{country.industry.render_pretty()}\n{configuration}"
    )
    return country


def test_availability_up_to_200_is_valid_and_increases_real_output() -> None:
    state = ResourceState(
        resource=ResourceType.COPPER,
        enabled=True,
        storage_capacity=1_000,
        accessibility=200,
    )

    common = {
        "extraction_capacity": 100,
        "quality": 100,
        "technology": 100,
        "effective_labor": 1_000_000,
        "equipment_availability": 100,
        "process_yield": 100,
        "years": 1,
        "profile": GROUP_PROFILES[ExtractionGroup.NONFERROUS],
        "stage": IndustrialStage.MACHINE,
    }
    normal = extraction_output(accessibility=100, **common)
    abundant = extraction_output(accessibility=state.accessibility, **common)

    assert abundant == pytest.approx(normal * 2)
    with pytest.raises(ValidationError):
        ResourceState(
            resource=ResourceType.COPPER,
            accessibility=200.1,
        )


def test_priority_one_receives_three_times_priority_three_capacity() -> None:
    assert extraction_priority_weight(1, 3) == 3
    assert extraction_priority_weight(3, 3) == 1


def test_agricultural_security_moves_slowly_and_respects_worker_floor() -> (
    None
):
    assert (
        resource_security_update(
            58,
            deficit=1,
            surplus=0,
            workers_percent=50,
            progress=1,
        )
        == 20
    )
    assert (
        resource_security_update(
            58,
            deficit=1,
            surplus=0,
            workers_percent=49.9,
            progress=1,
        )
        == 5
    )
    assert (
        resource_security_update(
            58,
            deficit=0,
            surplus=0.5,
            workers_percent=100,
            progress=0.05,
        )
        > 58
    )


def test_balanced_customer_configuration_resolves_full_turn() -> None:
    country = _balanced_country()
    stability_before = country.economy.stability
    population_before = country.economy.population_count
    engine = TurnEngine(
        state=country,
        io=TestIO(),
        rng=np.random.default_rng(1),
    )

    engine.run()

    industry = country.industry
    agriculture = country.agriculture
    deficits = [
        industry.resource_shortages.get(resource, 0.0) / demand
        for resource, demand in engine._turn_resource_demands.items()
        if demand > 0
    ]
    assert sum(value == 0 for value in deficits) >= 6
    assert sum(0 < value < 0.5 for value in deficits) >= 3
    assert sum(value >= 0.5 for value in deficits) >= 3
    assert 80 <= engine._resource_coverage <= 90

    assert (
        industry.resource_inventory.resources[
            ResourceType("plumbum")
        ].accessibility
        == 125
    )
    assert (
        industry.last_extracted.get(
            ResourceType.BASIC_BUILDING_MATERIALS,
            0.0,
        )
        == 0
    )
    assert (
        industry.last_extracted.get(ResourceType("simple_hand_tools"), 0.0)
        == 0
    )
    assert all(
        result.completed_batches > 0 for result in industry.last_production
    )

    workforce = industry.workforce
    assert workforce.industrial_population_target_share == pytest.approx(
        100 / 3
    )
    assert workforce.total_workers == round(population_before / 3)
    assert workforce.extraction_target_share == pytest.approx(100 / 3)
    assert workforce.extraction_required_workers == round(
        workforce.total_workers / 3
    )
    assert workforce.employed_workers == (
        workforce.extraction_workers + workforce.production_workers
    )
    assert workforce.total_workers == (
        workforce.employed_workers + workforce.idle_workers
    )
    assert agriculture.last_workers_count == 123_456
    assert agriculture.last_area_hectares == 246_912
    assert agriculture.last_fertilizer_demand == pytest.approx(740.736)
    assert agriculture.last_tools_demand == pytest.approx(370.368)
    assert agriculture.securities[1] < 58
    assert agriculture.securities[2] < 58
    assert country.economy.stability == stability_before
    assert sum(
        (
            country.economy.high_quality_percent,
            country.economy.mid_quality_percent,
            country.economy.low_quality_percent,
        )
    ) == pytest.approx(100)


def test_stability_remains_primary_input_across_repeated_turns() -> None:
    country = _balanced_country()
    stability = country.economy.stability
    engine = TurnEngine(
        state=country,
        io=TestIO(),
        rng=np.random.default_rng(2),
    )

    for _ in range(3):
        report = engine.run()
        assert country.economy.stability == stability
        assert 0 <= report.stability_after <= 100
