from __future__ import annotations

import numpy as np
import pytest

from functions.probability_models import (
    half_year_chance,
    industrial_accident_chance,
    turn_chance,
)
from functions.resource_models import (
    GROUP_PROFILES,
    INDUSTRIAL_STAGE_EXTRACTION_SHARES,
    INDUSTRIAL_STAGE_POPULATION_SHARES,
    INDUSTRIAL_STAGE_PROFILES,
    extraction_allocation_weight,
    extraction_demand_focus,
    extraction_output,
    extraction_priority_weight,
    national_extraction_capacity,
    specialist_capacity,
)
from functions.time_models import TURN_MONTHS, TURN_SCALE, TURN_YEARS
from modules.run_skip_move import TurnEngine
from modules.skip_move_rules import AtteriumSkipMoveRules
from modules.skip_move_types import WorldState
from stats.basic_stats import IndustrialStats, InnerPoliticsStats
from stats.industry_components import (
    RESOURCE_CATALOG,
    ExtractionGroup,
    ExtractionOperation,
    IndustrialStage,
    ResourceRegistration,
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


def test_turn_duration_constants_stay_synchronized():
    assert TURN_YEARS == TURN_MONTHS / 12
    assert TURN_SCALE == TURN_MONTHS / 6


def test_national_extraction_capacity_comes_from_existing_spending():
    assert national_extraction_capacity(341.3) == pytest.approx(307_170)
    assert national_extraction_capacity(0) == 0
    assert national_extraction_capacity(-10) == 0


def test_first_extraction_priority_is_the_strongest_rank():
    assert extraction_priority_weight(1, 3) == pytest.approx(3)
    assert extraction_priority_weight(2, 3) == pytest.approx(2)
    assert extraction_priority_weight(3, 3) == pytest.approx(1)


def test_extraction_allocation_weight_combines_priority_and_intensity():
    assert extraction_allocation_weight(1, 2, 50) == pytest.approx(1)
    assert extraction_allocation_weight(2, 2, 100) == pytest.approx(1)
    assert extraction_allocation_weight(1, 2, 0) == 0


def test_demand_focus_increases_as_previous_coverage_falls() -> None:
    assert extraction_demand_focus(100) == pytest.approx(0.2)
    assert extraction_demand_focus(50) == pytest.approx(0.4)
    assert extraction_demand_focus(0) == pytest.approx(0.6)


def test_manual_and_steam_stages_require_the_same_workers() -> None:
    manual = INDUSTRIAL_STAGE_PROFILES[IndustrialStage.MANUAL]
    steam = INDUSTRIAL_STAGE_PROFILES[IndustrialStage.STEAM]

    assert manual.labor_dependency == steam.labor_dependency


def test_stage_workforce_shares_match_customer_rules() -> None:
    assert {
        IndustrialStage.MANUAL: pytest.approx(1 / 3),
        IndustrialStage.STEAM: pytest.approx(1 / 3),
        IndustrialStage.MACHINE: pytest.approx(1 / 4),
        IndustrialStage.ELECTRIFIED: pytest.approx(1 / 5),
        IndustrialStage.MASS_PRODUCTION: pytest.approx(1 / 5),
    } == INDUSTRIAL_STAGE_POPULATION_SHARES
    assert {
        IndustrialStage.MANUAL: pytest.approx(1 / 3),
        IndustrialStage.STEAM: pytest.approx(1 / 3),
        IndustrialStage.MACHINE: pytest.approx(1 / 4),
        IndustrialStage.ELECTRIFIED: pytest.approx(1 / 4),
        IndustrialStage.MASS_PRODUCTION: pytest.approx(1 / 5),
    } == INDUSTRIAL_STAGE_EXTRACTION_SHARES


@pytest.mark.parametrize("stage", tuple(IndustrialStage))
def test_stage_sets_population_and_extraction_worker_ratios(
    stage: IndustrialStage,
) -> None:
    bundle = make_basic_bundle()
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.stage = stage
    iron.storage_capacity = 10_000
    bundle.industry.usages[2] = 100
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="iron", intensity=100, priority=1)
    ]
    engine = make_engine(bundle)

    engine._update_industrial_workforce()

    workforce = bundle.industry.workforce
    population_share = INDUSTRIAL_STAGE_POPULATION_SHARES[stage]
    extraction_share = INDUSTRIAL_STAGE_EXTRACTION_SHARES[stage]
    expected_total = round(bundle.economy.population_count * population_share)
    assert workforce.industrial_population_target_share == pytest.approx(
        population_share * 100
    )
    assert workforce.total_workers == expected_total
    assert workforce.extraction_target_share == pytest.approx(
        extraction_share * 100
    )
    assert workforce.extraction_required_workers == round(
        expected_total * extraction_share
    )
    assert workforce.ordinary_workers + workforce.specialist_workers == (
        expected_total
    )


def test_worker_security_scales_stage_population_pool() -> None:
    bundle = make_basic_bundle()
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.stage = IndustrialStage.MACHINE
    iron.storage_capacity = 10_000
    bundle.industry.usages[2] = 60
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="iron", intensity=100, priority=1)
    ]

    make_engine(bundle)._update_industrial_workforce()

    assert bundle.industry.workforce.total_workers == round(
        bundle.economy.population_count * (1 / 4) * 0.60
    )


@pytest.mark.parametrize(
    ("stage", "expected_share"),
    tuple(INDUSTRIAL_STAGE_EXTRACTION_SHARES.items()),
)
def test_single_stage_sets_extraction_worker_share(
    stage: IndustrialStage,
    expected_share: float,
) -> None:
    bundle = make_basic_bundle()
    configure_iron_extraction(bundle)
    bundle.industry.resource_inventory.resources[
        ResourceType.IRON
    ].stage = stage
    engine = make_engine(bundle)

    engine._allocate_industrial_workforce()

    workforce = bundle.industry.workforce
    assert workforce.extraction_target_share == pytest.approx(
        expected_share * 100
    )
    assert workforce.extraction_required_workers == round(
        workforce.total_workers * expected_share
    )


def test_mixed_stages_use_one_weighted_worker_share() -> None:
    bundle = make_basic_bundle()
    bundle.industry.workforce.auto_size = False
    bundle.industry.workforce.ordinary_workers = 24_000
    bundle.industry.workforce.specialist_workers = 0
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    wood = bundle.industry.resource_inventory.resources[ResourceType.WOOD]
    for item in (iron, wood):
        item.enabled = True
        item.storage_capacity = 10_000
    iron.stage = IndustrialStage.MANUAL
    wood.stage = IndustrialStage.ELECTRIFIED
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="iron", intensity=100, priority=1),
        ExtractionOperation(target="wood", intensity=100, priority=1),
    ]
    engine = make_engine(bundle)

    engine._allocate_industrial_workforce()

    expected_population_share = (1 / 3 + 1 / 5) / 2
    expected_extraction_share = (1 / 3 + 1 / 4) / 2
    workforce = bundle.industry.workforce
    assert engine._industrial_population_workforce_share() == pytest.approx(
        expected_population_share
    )
    assert workforce.extraction_target_share == pytest.approx(
        expected_extraction_share * 100
    )
    assert workforce.extraction_required_workers == round(
        workforce.total_workers * expected_extraction_share
    )
    assert workforce.extraction_required_workers < round(
        workforce.total_workers * (1 / 3 + 1 / 4)
    )


def test_extraction_report_keeps_turn_start_demand_focus() -> None:
    bundle = make_basic_bundle()
    bundle.industry.civil_security = 35.5
    configure_iron_extraction(bundle)

    make_engine(bundle, seed=700).run()

    assert bundle.industry.last_extraction_demand_focus == pytest.approx(0.458)
    assert "Текущая потребность    ╫ 45.8%" in (
        bundle.industry.render_extraction_allocation_report()
    )


def test_full_extraction_target_does_not_consume_other_priorities():
    bundle = make_basic_bundle()
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    oil = bundle.industry.resource_inventory.resources[ResourceType.OIL]
    iron.enabled = True
    iron.storage_capacity = 10_000
    oil.enabled = True
    oil.stockpile = 100
    oil.storage_capacity = 100
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="oil", intensity=100, priority=1),
        ExtractionOperation(target="iron", intensity=100, priority=2),
    ]

    engine = make_engine(bundle)

    assert engine._extraction_capacities() == {
        "iron": pytest.approx(
            national_extraction_capacity(bundle.economy.gov_wastes[3])
        )
    }


def test_extraction_intensity_redistributes_all_national_capacity():
    low = make_basic_bundle()
    high = make_basic_bundle()
    for bundle, intensity in ((low, 40), (high, 100)):
        iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
        oil = bundle.industry.resource_inventory.resources[ResourceType.OIL]
        iron.enabled = True
        iron.storage_capacity = 10_000
        oil.enabled = True
        oil.storage_capacity = 10_000
        bundle.industry.extraction_operations = [
            ExtractionOperation(
                target="iron",
                intensity=intensity,
                priority=1,
            ),
            ExtractionOperation(target="oil", intensity=100, priority=1),
        ]

    low_capacities = make_engine(low)._extraction_capacities()
    high_capacities = make_engine(high)._extraction_capacities()
    national_capacity = national_extraction_capacity(low.economy.gov_wastes[3])

    assert sum(low_capacities.values()) == pytest.approx(national_capacity)
    assert sum(high_capacities.values()) == pytest.approx(national_capacity)
    assert low_capacities["iron"] == pytest.approx(
        national_capacity * 0.4 / 1.4
    )
    assert high_capacities["iron"] == pytest.approx(national_capacity / 2)


def test_extraction_report_preserves_turn_capacity_and_explains_limits():
    bundle = make_basic_bundle()
    for resource in (ResourceType.IRON, ResourceType.WOOD):
        state = bundle.industry.resource_inventory.resources[resource]
        state.enabled = True
        state.storage_capacity = 1_000_000
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="iron", intensity=50, priority=1),
        ExtractionOperation(target="wood", intensity=100, priority=1),
    ]

    make_engine(bundle, seed=125).run()

    diagnostics = bundle.industry.last_extraction_diagnostics
    expected_capacity = (
        national_extraction_capacity(bundle.economy.gov_wastes[3]) * TURN_YEARS
    )
    report = bundle.industry.render_extraction_allocation_report()
    assert sum(item.allocated_capacity for item in diagnostics) == (
        pytest.approx(expected_capacity)
    )
    assert "╫" in report
    assert "РАСПРЕДЕЛЕНИЕ ДОБЫВАЮЩЕЙ МОЩНОСТИ" in report
    assert "ЛОГИКА РАСПРЕДЕЛЕНИЯ ДОБЫЧИ" in report
    assert "Настроенные приоритеты" in report
    assert "Текущая потребность" in report
    assert "Доля / мощность" in report
    assert "Главные ограничения" in report
    assert "Железо [iron]" in report


def test_single_active_extraction_uses_full_capacity_at_any_intensity():
    bundle = make_basic_bundle()
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.storage_capacity = 10_000
    bundle.industry.extraction_operations = [
        ExtractionOperation(target="iron", intensity=25, priority=3)
    ]

    capacities = make_engine(bundle)._extraction_capacities()

    assert capacities["iron"] == pytest.approx(
        national_extraction_capacity(bundle.economy.gov_wastes[3])
    )


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

    assert engine._extraction_capacities()["ferrous"] == pytest.approx(9_000)


def test_resource_catalog_has_every_approved_resource():
    assert len(ResourceType) == 37
    assert set(RESOURCE_CATALOG) == set(ResourceType)
    assert ResourceType.SILVER is not ResourceType.COPPER
    assert RESOURCE_CATALOG[ResourceType.CORE_CRYSTAL].group is (
        ExtractionGroup.UNIQUE
    )
    custom = ResourceRegistration(
        resource=ResourceType("reinforced_glass"),
        name="Армированное стекло",
        group=ExtractionGroup.CONSTRUCTION,
        storage_capacity=100,
    )
    assert custom.resource.value == "reinforced_glass"
    assert custom.resource not in RESOURCE_CATALOG
    assert set(GROUP_PROFILES) == set(ExtractionGroup)
    assert (
        GROUP_PROFILES[ExtractionGroup.PLANTATIONS].labor_weight
        > GROUP_PROFILES[ExtractionGroup.HYDROCARBONS].labor_weight
    )
    assert set(INDUSTRIAL_STAGE_PROFILES) == set(IndustrialStage)


def stage_output(
    stage: IndustrialStage,
    *,
    equipment_availability: float = 100,
) -> float:
    return extraction_output(
        extraction_capacity=100_000,
        accessibility=100,
        quality=100,
        technology=100,
        effective_labor=100_000,
        equipment_availability=equipment_availability,
        process_yield=100,
        years=1,
        profile=GROUP_PROFILES[ExtractionGroup.FERROUS],
        stage=stage,
    )


def test_industrial_stages_change_abstract_extraction_units() -> None:
    outputs = [stage_output(stage) for stage in IndustrialStage]

    assert outputs == sorted(outputs)
    assert outputs[2] > outputs[0] * 1.8
    assert outputs[-1] > outputs[2] * 1.3


def test_advanced_stage_depends_more_on_equipment_availability() -> None:
    manual_ratio = stage_output(
        IndustrialStage.MANUAL,
        equipment_availability=50,
    ) / stage_output(IndustrialStage.MANUAL)
    mass_ratio = stage_output(
        IndustrialStage.MASS_PRODUCTION,
        equipment_availability=50,
    ) / stage_output(IndustrialStage.MASS_PRODUCTION)

    assert manual_ratio == pytest.approx(0.925)
    assert mass_ratio == pytest.approx(0.5)


def test_resource_stage_changes_extraction_in_a_real_turn() -> None:
    manual = make_basic_bundle(budget=1_000_000)
    mass = make_basic_bundle(budget=1_000_000)
    for bundle, stage in (
        (manual, IndustrialStage.MANUAL),
        (mass, IndustrialStage.MASS_PRODUCTION),
    ):
        iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
        iron.enabled = True
        iron.stage = stage
        iron.storage_capacity = 1_000_000
        bundle.industry.workforce.auto_size = False
        bundle.industry.workforce.ordinary_workers = 50_000
        bundle.industry.workforce.specialist_workers = 1_000
        bundle.industry.extraction_operations = [
            ExtractionOperation(target="iron", intensity=100, priority=1)
        ]

    make_engine(manual, seed=141).run()
    make_engine(mass, seed=141).run()

    manual_output = manual.industry.last_extracted[ResourceType.IRON]
    mass_output = mass.industry.last_extracted[ResourceType.IRON]
    assert mass_output > manual_output * 1.5
    assert manual.industry.last_readiness is not None
    assert mass.industry.last_readiness is not None
    assert manual.industry.last_readiness.readiness == pytest.approx(
        mass.industry.last_readiness.readiness
    )
    assert manual.industry.last_readiness.strain == pytest.approx(
        mass.industry.last_readiness.strain
    )
    assert "Ручной" in manual.industry.render_industrialization_profile()
    assert "Массовое производство" in (
        mass.industry.render_industrialization_profile()
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


def test_turn_hazard_and_accident_risk_are_monotonic():
    assert half_year_chance(0) == 0
    expected = (1 - np.exp(-0.2 * TURN_YEARS)) * 100
    assert turn_chance(0.2) == pytest.approx(expected)
    assert half_year_chance(0.2) == pytest.approx(expected)
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
        lambda *args, **kwargs: 100.0,
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
    assert result.completed_batches == pytest.approx(5 * TURN_SCALE)
    assert inventory[ResourceType.IRON].stockpile < 20
    assert inventory[ResourceType.BASIC_BUILDING_MATERIALS].stockpile > 0
    assert inventory[ResourceType.SLAG].stockpile > 0
    assert any(result.process_losses.values())
    assert "Потери выхода" in bundle.industry.render_production_results()


def test_material_balance_reports_monthly_consumption_and_stock_change():
    bundle = make_basic_bundle()
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.stockpile = 20
    iron.storage_capacity = 100
    bundle.industry.resource_demands = {ResourceType.IRON: 2}

    make_engine(bundle, seed=504).run()

    report = bundle.industry.render_material_balance()
    assert bundle.industry.last_stock_before[ResourceType.IRON] == 20
    assert bundle.industry.last_resource_consumed[ResourceType.IRON] == (
        pytest.approx(2 * TURN_MONTHS)
    )
    assert "╫" in report
    assert "МАТЕРИАЛЬНЫЙ БАЛАНС" in report
    assert "Железо [iron]" in report
    assert "Перераб." in report
    assert "Склад Δ" in report


def test_resource_shortage_reduces_legacy_civil_security():
    bundle = make_basic_bundle()
    bundle.industry.civil_security = 80
    bundle.industry.recalculate_derived_fields()
    civil_usage_before = bundle.industry.civil_usage
    iron = bundle.industry.resource_inventory.resources[ResourceType.IRON]
    iron.enabled = True
    iron.stockpile = 25
    iron.storage_capacity = 100
    bundle.industry.resource_demands = {ResourceType.IRON: 100}

    engine = make_engine(bundle, seed=502)
    engine.run()

    preserved_stock = (
        25
        * (engine.state.probabilities.storage_preservation / 100) ** TURN_SCALE
    )
    assert bundle.industry.resource_shortages[ResourceType.IRON] == (
        pytest.approx(max(100 * TURN_MONTHS - preserved_stock, 0))
    )
    assert bundle.industry.civil_security == pytest.approx(
        round(
            (80 + preserved_stock / (100 * TURN_MONTHS) * 100) / 2,
            2,
        )
    )
    assert bundle.industry.civil_usage < civil_usage_before


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
    workforce = bundle.industry.workforce
    assert workforce.employed_workers == (
        workforce.extraction_workers + workforce.production_workers
    )
    assert workforce.employed_workers <= workforce.total_workers


def test_debt_interest_uses_turn_years_and_credit_increases_debt():
    with_debt = make_basic_bundle(budget=1_000)
    without_debt = make_basic_bundle(budget=1_000)
    with_debt.economy.public_debt = 100
    with_debt.economy.annual_interest_rate = 10

    debt_report = make_engine(with_debt).run()
    base_report = make_engine(without_debt).run()

    assert debt_report.debt_interest == pytest.approx(10 * TURN_YEARS)
    assert debt_report.total_wastes == pytest.approx(
        base_report.total_wastes + debt_report.debt_interest
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
    assert "ВЕРОЯТНОСТИ СОБЫТИЙ ЗА ХОД" in probability_text
