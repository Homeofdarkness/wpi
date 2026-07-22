from __future__ import annotations

import numpy as np
import pytest

from functions.probability_models import (
    half_year_chance,
    industrial_accident_chance,
)
from functions.resource_models import (
    GROUP_PROFILES,
    national_extraction_capacity,
    specialist_capacity,
)
from functions.time_models import TURN_MONTHS, TURN_YEARS
from modules.run_skip_move import TurnEngine
from modules.skip_move_rules import AtteriumSkipMoveRules
from modules.skip_move_types import WorldState
from stats.basic_stats import IndustrialStats, InnerPoliticsStats
from stats.industry_components import (
    RESOURCE_CATALOG,
    ExtractionGroup,
    ExtractionOperation,
    ResourceKind,
    ResourceState,
    ResourceType,
)
from stats.probability_stats import ProbabilityStats
from stats.production_components import (
    ProductionRecipeId,
    ProductionRule,
)
from tests.factories import make_atterium_bundle, make_basic_bundle
from utils.user_io import TestIO


def make_engine(bundle, seed: int = 123) -> TurnEngine:
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


def configure_iron_extraction(bundle) -> None:
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.storage_capacity = 1_000
    bundle.industry.workforce.auto_size = False
    bundle.industry.workforce.ordinary_workers = 10_000
    bundle.industry.workforce.specialist_workers = 100
    bundle.industry.set_extraction_operation(
        ExtractionOperation(
            target=ExtractionGroup.FERROUS,
            intensity=100,
            priority=1,
        )
    )


def test_turn_duration_is_six_months():
    assert TURN_YEARS == 0.5
    assert TURN_MONTHS == 6


def test_national_extraction_capacity_comes_from_existing_spending():
    assert national_extraction_capacity(341.3) == pytest.approx(102_390)
    assert national_extraction_capacity(0) == 0
    assert national_extraction_capacity(-10) == 0


def test_atterium_extraction_uses_resource_spending_not_republic_spending():
    bundle = make_atterium_bundle()
    configure_iron_extraction(bundle)
    bundle.economy.gov_wastes[3] = 1.0
    bundle.economy.gov_wastes[4] = 10.0
    engine = TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        rules=AtteriumSkipMoveRules(),
        io=TestIO(),
    )

    assert engine._extraction_capacities()["ferrous"] == pytest.approx(3_000)


def test_resource_catalog_has_every_approved_resource():
    assert len(ResourceType) == 37
    assert set(RESOURCE_CATALOG) == set(ResourceType)
    assert ResourceType.SILVER is not ResourceType.COPPER
    assert RESOURCE_CATALOG[ResourceType.SLAG].kind is ResourceKind.BYPRODUCT
    assert RESOURCE_CATALOG[ResourceType.CORE_CRYSTAL].group is (
        ExtractionGroup.UNIQUE
    )
    assert set(GROUP_PROFILES) == set(ExtractionGroup)
    assert (
        GROUP_PROFILES[ExtractionGroup.PLANTATIONS].labor_weight
        > GROUP_PROFILES[ExtractionGroup.HYDROCARBONS].labor_weight
    )


def test_resource_collect_and_spend_preserve_stock_invariants():
    resource = ResourceState(
        resource=ResourceType.IRON,
        enabled=True,
        storage_capacity=50,
    )

    collected = resource.collect(60)
    spent = resource.spend(70)

    assert collected.actual == 50
    assert collected.overflow == 10
    assert spent.actual == 50
    assert spent.shortage == 20
    assert resource.stockpile == 0


def test_inventory_configuration_and_resource_report_are_readable():
    bundle = make_basic_bundle()
    bundle.industry.resource_inventory.configure(
        ResourceType.IRON,
        stockpile=25,
        storage_capacity=100,
    )

    text = bundle.industry.render_resource_details()

    assert "СОСТОЯНИЕ РЕСУРСОВ" in text
    assert "Железо [iron]" in text
    assert "25 / 100" in text


def test_industrial_state_survives_text_roundtrip():
    bundle = make_basic_bundle()
    bundle.industry.resource_inventory.configure(
        ResourceType.IRON,
        stockpile=25,
        storage_capacity=100,
    )
    bundle.industry.set_extraction_operation(
        ExtractionOperation(
            target=ExtractionGroup.FERROUS,
            intensity=40,
            priority=2,
        )
    )
    for resource in (
        ResourceType.COAL,
        ResourceType.SILICON,
        ResourceType.BASIC_BUILDING_MATERIALS,
        ResourceType.SLAG,
    ):
        bundle.industry.resource_inventory.configure(
            resource,
            storage_capacity=100,
        )
    bundle.industry.resource_demands = {ResourceType.IRON: 5}
    bundle.industry.production_rules = [
        ProductionRule(
            recipe=ProductionRecipeId.BASIC_BUILDING_MATERIALS,
            batches=2,
        )
    ]

    parsed = IndustrialStats.from_stats_text(
        f"{bundle.industry}\n{bundle.industry.render_configuration()}"
    )
    parsed_iron = parsed.resource_inventory.resources[ResourceType.IRON]
    parsed_operation = parsed.extraction_operations[0]

    assert parsed_iron.enabled
    assert parsed_iron.stockpile == 25
    assert parsed_operation.target == ExtractionGroup.FERROUS
    assert parsed_operation.intensity == 40
    assert parsed_operation.priority == 2
    assert parsed.resource_demands == {ResourceType.IRON: 5}
    assert parsed.production_rules == bundle.industry.production_rules


def test_disabled_resource_cannot_be_collected():
    resource = ResourceState(
        resource=ResourceType.GOLD,
        storage_capacity=100,
    )

    result = resource.collect(10)

    assert result.actual == 0
    assert result.shortage == 10
    assert resource.stockpile == 0


def test_registered_resource_does_not_require_a_hidden_reserve():
    forest = ResourceState(
        resource=ResourceType.WOOD,
        enabled=True,
        storage_capacity=100,
    )

    collected = forest.collect(40)

    assert collected.actual == 40
    assert forest.stockpile == 40
    assert not hasattr(forest, "reserve")


def test_specialist_capacity_matches_population_education_model():
    assert specialist_capacity(100_000, 0, 0) == 1
    assert specialist_capacity(1_000_000, 50, 20) == 80
    assert specialist_capacity(1_000_000, 100, 100) <= 150_000


def test_half_year_hazard_and_accident_risk_are_monotonic():
    assert half_year_chance(0) == 0
    assert half_year_chance(0.2) == pytest.approx((1 - np.exp(-0.1)) * 100)
    safe = industrial_accident_chance(40, 99, 95, 0, 100)
    unsafe = industrial_accident_chance(100, 60, 20, 0.7, 10)
    assert 0 < safe < unsafe < 100


def test_resource_extraction_and_probabilities_are_seed_reproducible():
    first = make_basic_bundle()
    second = make_basic_bundle()
    configure_iron_extraction(first)
    configure_iron_extraction(second)

    first_engine = make_engine(first, seed=500)
    second_engine = make_engine(second, seed=500)
    first_engine.run()
    second_engine.run()

    first_iron = first.industry.resource_inventory.resources[ResourceType.IRON]
    second_iron = second.industry.resource_inventory.resources[
        ResourceType.IRON
    ]
    assert first_iron.stockpile > 0
    assert first_iron.stockpile == pytest.approx(second_iron.stockpile)
    assert first.industry.last_extracted[ResourceType.IRON] > 0
    assert (
        first_engine.state.probabilities == second_engine.state.probabilities
    )


def test_major_probability_is_informational_and_does_not_trigger_event(
    monkeypatch,
):
    bundle = make_basic_bundle()
    configure_iron_extraction(bundle)
    operation = bundle.industry.extraction_operations[0]

    monkeypatch.setattr(
        "functions.probability_models.industrial_accident_chance",
        lambda *args: 100.0,
    )
    engine = make_engine(bundle)
    report = engine.run()

    assert engine.state.probabilities.industrial_accident_chance == 100
    assert report.probabilities is not engine.state.probabilities
    assert report.probabilities.industrial_accident_chance == 100
    assert operation.intensity == 100
    assert report.budget_final == bundle.economy.current_budget
    assert (
        bundle.industry.resource_inventory.resources[
            ResourceType.IRON
        ].stockpile
        > 0
    )


def test_production_recipe_consumes_inputs_and_creates_output_and_slag():
    bundle = make_basic_bundle()
    inventory = bundle.industry.resource_inventory.resources
    for resource, amount in {
        ResourceType.IRON: 20,
        ResourceType.COAL: 10,
        ResourceType.SILICON: 5,
    }.items():
        state = inventory[resource]
        state.enabled = True
        state.stockpile = amount
        state.storage_capacity = amount
    for resource in (
        ResourceType.BASIC_BUILDING_MATERIALS,
        ResourceType.SLAG,
    ):
        inventory[resource].enabled = True
        inventory[resource].storage_capacity = 100
    bundle.industry.production_rules = [
        ProductionRule(
            recipe=ProductionRecipeId.BASIC_BUILDING_MATERIALS,
            batches=5,
        )
    ]

    make_engine(bundle, seed=501).run()

    result = bundle.industry.last_production[0]
    assert result.completed_batches == 5
    assert inventory[ResourceType.IRON].stockpile < 20
    assert inventory[ResourceType.BASIC_BUILDING_MATERIALS].stockpile > 0
    assert inventory[ResourceType.SLAG].stockpile > 0


def test_resource_shortage_reduces_legacy_civil_security():
    bundle = make_basic_bundle()
    bundle.industry.civil_security = 80
    bundle.industry.recalculate_derived_fields()
    efficiency_before = bundle.industry.civil_efficiency
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.stockpile = 25
    iron.storage_capacity = 100
    bundle.industry.resource_demands = {ResourceType.IRON: 100}

    engine = make_engine(bundle, seed=502)
    engine.run()

    preserved_stock = (
        25 * engine.state.probabilities.storage_preservation / 100
    )
    assert bundle.industry.resource_shortages[ResourceType.IRON] == (
        pytest.approx(100 - preserved_stock)
    )
    assert bundle.industry.civil_security == pytest.approx(
        round((80 + preserved_stock) / 2, 2)
    )
    assert bundle.industry.civil_efficiency < efficiency_before


def test_worker_allocations_cannot_exceed_available_pool():
    bundle = make_basic_bundle()
    full_pool = make_basic_bundle()
    configure_iron_extraction(bundle)
    configure_iron_extraction(full_pool)
    bundle.industry.workforce.auto_size = False
    bundle.industry.workforce.ordinary_workers = 100

    make_engine(bundle, seed=503).run()
    make_engine(full_pool, seed=503).run()

    extracted = bundle.industry.last_extracted[ResourceType.IRON]
    full_extraction = full_pool.industry.last_extracted[ResourceType.IRON]
    assert 0 < extracted < full_extraction


def test_debt_interest_uses_half_year_and_credit_increases_debt():
    with_debt = make_basic_bundle(budget=1_000)
    without_debt = make_basic_bundle(budget=1_000)
    with_debt.economy.public_debt = 100
    with_debt.economy.annual_interest_rate = 10

    debt_report = make_engine(with_debt).run()
    base_report = make_engine(without_debt).run()

    assert debt_report.debt_interest == pytest.approx(5)
    assert debt_report.total_wastes == pytest.approx(
        base_report.total_wastes + 5
    )

    credit_bundle = make_basic_bundle(budget=-10_000)
    credit_engine = TurnEngine(
        state=WorldState(
            economy=credit_bundle.economy,
            industry=credit_bundle.industry,
            agriculture=credit_bundle.agriculture,
            inner_politics=credit_bundle.inner_politics,
        ),
        io=TestIO(inputs=[True, 0.0]),
        rng=np.random.default_rng(10),
    )
    credit_report = credit_engine.run()
    assert credit_report.credit_taken
    assert credit_bundle.economy.public_debt == pytest.approx(
        credit_report.credit_amount
    )


def test_new_social_fields_roundtrip_and_probability_output():
    bundle = make_basic_bundle()
    bundle.inner_politics.inequality = 42
    bundle.inner_politics.polarization = 37
    bundle.inner_politics.information_quality = 81
    bundle.inner_politics.regional_separatism = 12
    bundle.inner_politics.social_mobility = 64
    bundle.inner_politics.war_fatigue = 18

    parsed = InnerPoliticsStats.from_stats_text(str(bundle.inner_politics))
    probability_text = str(ProbabilityStats())

    assert parsed.inequality == 42
    assert parsed.polarization == 37
    assert parsed.information_quality == 81
    assert parsed.regional_separatism == 12
    assert parsed.social_mobility == 64
    assert parsed.war_fatigue == 18
    assert "НАДЁЖНОСТЬ СИСТЕМ" in probability_text
    assert "ВЕРОЯТНОСТИ СОБЫТИЙ ЗА ПОЛГОДА" in probability_text
