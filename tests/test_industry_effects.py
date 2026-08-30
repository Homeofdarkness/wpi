from __future__ import annotations

import numpy as np
import pydantic
import pytest

from modules.mode_spec import GameMode, get_mode
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from stats.basic_stats import EconomyStats, IndustrialStats
from stats.industry_components import (
    ExtractionGroup,
    ResourceRegistration,
    ResourceType,
)
from stats.industry_effects import (
    DependencyMetric,
    EffectDependency,
    EffectTarget,
    IndustrialEffect,
    default_industrial_effects,
    evaluate_effect_formula,
    resolve_effect_target,
)
from tests.factories import (
    make_atterium_bundle,
    make_basic_bundle,
    make_isf_bundle,
)
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


def configure_fresh_water_shortage(bundle) -> None:
    bundle.industry.register_resource(
        ResourceRegistration(
            resource=ResourceType.FRESH_WATER,
            storage_capacity=100,
            consumption_per_turn=100,
        )
    )


def water_effect(*targets: str, formula: str) -> IndustrialEffect:
    return IndustrialEffect(
        id="configured_water_effect",
        dependencies=[EffectDependency(resource=ResourceType.FRESH_WATER)],
        targets=list(targets),
        formula=formula,
    )


def test_formula_reads_only_declared_dependency_metrics() -> None:
    effect = IndustrialEffect(
        id="weighted_water",
        dependencies=[
            EffectDependency(resource=ResourceType.FRESH_WATER),
            EffectDependency(group=ExtractionGroup.CONSTRUCTION),
        ],
        targets=[EffectTarget.POPULATION_GROWTH],
        formula=(
            "-target * max(resources.fresh_water.deficit "
            "- resources.fresh_water.surplus, 0) "
            "+ target * groups.construction.deficit"
        ),
    )

    result = evaluate_effect_formula(
        effect,
        target=200,
        resources={"fresh_water": DependencyMetric(deficit=0.4, surplus=0.1)},
        groups={"construction": DependencyMetric(deficit=0.2)},
    )

    assert result == pytest.approx(-20)


@pytest.mark.parametrize(
    "formula",
    (
        "resources.iron.deficit",
        "__import__('os')",
        "target if target > 0 else 0",
    ),
)
def test_formula_rejects_undeclared_or_unsafe_access(formula: str) -> None:
    with pytest.raises(ValueError):
        IndustrialEffect(
            id="unsafe_effect",
            dependencies=[EffectDependency(resource=ResourceType.FRESH_WATER)],
            targets=[EffectTarget.POPULATION_GROWTH],
            formula=formula,
        )


def test_fresh_water_deficit_reduces_growth_in_the_same_turn() -> None:
    affected = make_basic_bundle()
    control = make_basic_bundle()
    for bundle in (affected, control):
        bundle.economy.decrement_coefficient = 0
        bundle.industry.register_resource(
            ResourceRegistration(
                resource=ResourceType.FRESH_WATER,
                storage_capacity=100,
                consumption_per_turn=100,
            )
        )
    control.industry.effects = []

    affected_report = make_engine(affected, seed=10).run()
    control_report = make_engine(control, seed=10).run()

    assert (
        affected.industry.resource_shortages[ResourceType.FRESH_WATER] == 100
    )
    assert affected.economy.income == pytest.approx(
        control.economy.income * 0.8
    )
    assert affected_report.population_growth is not None
    assert control_report.population_growth is not None
    assert affected_report.population_growth.resource_adjustment == (
        pytest.approx(-affected_report.population_growth.base_growth * 0.2)
    )
    assert affected.economy.population_count < control.economy.population_count


def test_default_water_effect_uses_twenty_percent_penalty() -> None:
    effect = next(
        item
        for item in default_industrial_effects()
        if item.id == "freshwater_population_growth"
    )

    assert effect.formula == ("-target * resources.fresh_water.deficit * 0.2")


def test_one_formula_is_applied_independently_to_multiple_targets() -> None:
    bundle = make_basic_bundle()
    bundle.industry.register_resource(
        ResourceRegistration(
            resource=ResourceType.FRESH_WATER,
            storage_capacity=100,
            consumption_per_turn=100,
        )
    )
    bundle.industry.effects = [
        IndustrialEffect(
            id="shared_water_penalty",
            dependencies=[EffectDependency(resource=ResourceType.FRESH_WATER)],
            targets=[
                EffectTarget.POPULATION_GROWTH,
                EffectTarget.INFRASTRUCTURE_EXPENSES,
            ],
            formula="-0.1 * target * resources.fresh_water.deficit",
        )
    ]

    report = make_engine(bundle, seed=12).run()
    by_target = {item.target: item for item in bundle.industry.last_effects}

    assert set(by_target) == set(EffectTarget)
    assert by_target[
        EffectTarget.POPULATION_GROWTH
    ].target_after == pytest.approx(
        by_target[EffectTarget.POPULATION_GROWTH].target_before * 0.9
    )
    assert report.resource_effect_wastes == pytest.approx(
        -bundle.economy.gov_wastes[0] * 0.1
    )


@pytest.mark.parametrize(
    ("stockpile", "expected_sign"),
    ((0, 1), (1_000, -1)),
)
def test_construction_effect_is_a_separate_budget_adjustment(
    stockpile: float,
    expected_sign: int,
) -> None:
    bundle = make_basic_bundle()
    base_infrastructure = bundle.economy.gov_wastes[0]
    bundle.industry.register_resource(
        ResourceRegistration(
            resource=ResourceType.BASIC_BUILDING_MATERIALS,
            stockpile=stockpile,
            storage_capacity=max(stockpile, 100),
            consumption_per_turn=100,
        )
    )

    report = make_engine(bundle, seed=11).run()

    assert bundle.economy.gov_wastes[0] == base_infrastructure
    assert report.resource_effect_wastes * expected_sign > 0
    assert report.ledger is not None
    assert report.ledger.resource_effect_wastes == pytest.approx(
        report.resource_effect_wastes
    )


def test_all_fixed_groups_render_even_without_resources() -> None:
    text = make_basic_bundle().industry.render_resource_details()

    for group in ExtractionGroup:
        assert f"[{group.value}]" in text


def test_effect_report_lists_configured_targets_before_turn():
    bundle = make_basic_bundle()
    bundle.industry.effects = [
        water_effect(
            "contentment",
            "food_diversity",
            "population_epidemic_chance",
            formula="-target * resources.fresh_water.deficit * 0.05",
        )
    ]

    report = bundle.industry.render_effect_results()

    assert "ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ" in report
    assert "configured_water_effect:" in report
    assert "contentment" in report
    assert "food_diversity" in report
    assert "population_epidemic_chance" in report
    assert report.count("ожидает расчёта хода") == 3


def test_effect_report_explains_absence_of_configured_effects():
    bundle = make_basic_bundle()
    bundle.industry.effects = []

    assert bundle.industry.render_effect_results() == (
        "ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ\nЭффекты не настроены"
    )


def test_effect_report_shows_real_delta_to_one_decimal_place():
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "contentment",
            "logistic",
            formula="-target * resources.fresh_water.deficit * 0.1",
        )
    ]

    make_engine(bundle, seed=13).run()
    report = bundle.industry.render_effect_results()

    assert "configured_water_effect:" in report
    assert "70.0 -> 63.0 (-7.0)" in report
    assert "60.0 -> 54.0 (-6.0)" in report
    assert "ожидает расчёта хода" not in report


def test_effect_accepts_any_existing_numeric_stat_without_enum_registration():
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "trade_efficiency",
            "logistic",
            "food_diversity",
            "contentment",
            "industrial_accident_chance",
            formula="-target * resources.fresh_water.deficit * 0.25",
        )
    ]

    report = make_engine(bundle, seed=14).run()
    results = {item.target: item for item in bundle.industry.last_effects}

    assert set(results) == {
        "trade_efficiency",
        "logistic",
        "food_diversity",
        "contentment",
        "industrial_accident_chance",
    }
    assert bundle.economy.trade_efficiency == 60
    assert bundle.industry.logistic == pytest.approx(45)
    assert bundle.inner_politics.contentment == 52
    assert bundle.agriculture.food_diversity == pytest.approx(
        results["food_diversity"].target_before * 0.75
    )
    assert report.probabilities is not None
    assert report.probabilities.industrial_accident_chance == pytest.approx(
        results["industrial_accident_chance"].target_before * 0.75
    )


def test_qualified_targets_distinguish_same_name_in_different_sections():
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "industry.expected_wastes",
            "agriculture.expected_wastes",
            formula="target * resources.fresh_water.deficit * 0.1",
        )
    ]

    make_engine(bundle, seed=15).run()
    results = {item.target: item for item in bundle.industry.last_effects}

    assert bundle.industry.expected_wastes == pytest.approx(
        results["industry.expected_wastes"].target_before * 1.1
    )
    assert bundle.agriculture.expected_wastes == pytest.approx(
        results["agriculture.expected_wastes"].target_before * 1.1
    )


@pytest.mark.parametrize(
    ("target", "message"),
    (
        ("expected_wastes", "Неоднозначная целевая стата"),
        ("missing_stat", "Неизвестная целевая стата"),
        ("economy.missing_stat", "отсутствует целевая стата"),
        ("country.population_count", "Неизвестный раздел цели"),
        ("gov_wastes", "должна быть числовой статой"),
        ("industry.workforce", "должна быть числовой статой"),
    ),
)
def test_invalid_targets_fail_before_turn_mutates_state(
    target: str,
    message: str,
) -> None:
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [water_effect(target, formula="-target * 0.1")]
    initial_population = bundle.economy.population_count
    initial_stockpile = bundle.industry.resource_inventory.resources[
        ResourceType.FRESH_WATER
    ].stockpile

    with pytest.raises(ValueError, match=message):
        make_engine(bundle).run()

    assert bundle.economy.population_count == initial_population
    assert (
        bundle.industry.resource_inventory.resources[
            ResourceType.FRESH_WATER
        ].stockpile
        == initial_stockpile
    )


@pytest.mark.parametrize(
    "target",
    (
        "economy.__dict__",
        "economy.population_count.real",
        "_private",
        "economy[population_count]",
    ),
)
def test_target_names_reject_private_or_nested_object_access(target: str):
    with pytest.raises(pydantic.ValidationError):
        water_effect(target, formula="-target * 0.1")


def test_alias_and_qualified_reference_to_same_stat_are_duplicates():
    bundle = make_basic_bundle()
    bundle.industry.effects = [
        water_effect(
            "population_growth",
            "economy.income",
            formula="-target * 0.1",
        )
    ]

    with pytest.raises(ValueError, match="повторно использует целевую стату"):
        make_engine(bundle).run()


@pytest.mark.parametrize(
    ("formula", "expected"),
    (("1000", 100), ("-1000", 0)),
)
def test_effects_respect_declared_numeric_stat_bounds(
    formula: str,
    expected: int,
) -> None:
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "logistic",
            "industrial_accident_chance",
            formula=formula,
        )
    ]

    report = make_engine(bundle, seed=16).run()

    assert bundle.industry.logistic == expected
    assert report.probabilities is not None
    assert report.probabilities.industrial_accident_chance == expected
    for result in bundle.industry.last_effects:
        assert result.adjustment == pytest.approx(
            result.target_after - result.target_before
        )


def test_integer_targets_are_rounded_and_strict_lower_bounds_are_preserved():
    bundle = make_basic_bundle(budget=1_000_000)
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )

    assert resolve_effect_target(state, "contentment").apply(71.6) == 72
    assert isinstance(bundle.inner_politics.contentment, int)
    assert resolve_effect_target(state, "population_count").apply(-100) == 1
    assert bundle.economy.population_count == 1


def test_negative_budget_is_allowed_and_finalize_target_updates_report():
    bundle = make_basic_bundle(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect("current_budget", formula="-target - 50")
    ]
    engine = make_engine(bundle, seed=17)
    engine.io = TestIO(inputs=[False])

    report = engine.run()

    assert bundle.economy.current_budget == -50
    assert report.budget_after_boost == -50
    assert report.budget_final == -50


def test_derived_targets_are_applied_after_their_calculation():
    affected = make_basic_bundle(budget=1_000_000)
    control = make_basic_bundle(budget=1_000_000)
    for bundle in (affected, control):
        configure_fresh_water_shortage(bundle)
        bundle.industry.effects = []
    affected.industry.effects = [
        water_effect(
            "civil_efficiency",
            "tax_income",
            "forex",
            "trade_income",
            "research_success_chance",
            "population_epidemic_chance",
            formula="-target * resources.fresh_water.deficit * 0.1",
        )
    ]

    affected_report = make_engine(affected, seed=18).run()
    control_report = make_engine(control, seed=18).run()
    results = {item.target: item for item in affected.industry.last_effects}

    for result in results.values():
        assert result.target_after == pytest.approx(result.target_before * 0.9)
    assert affected.industry.civil_efficiency == pytest.approx(
        results["civil_efficiency"].target_after
    )
    assert affected.economy.forex == pytest.approx(
        results["forex"].target_after
    )
    assert affected.inner_politics.research_success_chance == pytest.approx(
        results["research_success_chance"].target_after
    )
    assert affected_report.tax_income < control_report.tax_income
    assert affected_report.probabilities is not None
    assert (
        affected_report.probabilities.population_epidemic_chance
        == pytest.approx(results["population_epidemic_chance"].target_after)
    )


@pytest.mark.parametrize(
    ("factory", "target"),
    (
        (make_atterium_bundle, "plan_efficiency"),
        (make_atterium_bundle, "capitalistic_decay"),
        (make_isf_bundle, "empire_land_unmastery"),
        (make_isf_bundle, "imperial_court_power"),
    ),
)
def test_mode_specific_numeric_stats_are_discovered_automatically(
    factory,
    target: str,
) -> None:
    bundle = factory()
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )

    resolved = resolve_effect_target(state, target)
    previous = resolved.current_value()

    assert resolved.apply(previous * 0.5) == pytest.approx(previous * 0.5)


def test_new_numeric_model_field_needs_no_target_registry_entry():
    class ExpandedEconomyStats(EconomyStats):
        strategic_reserve: float = pydantic.Field(100, ge=0, le=200)

    bundle = make_basic_bundle(budget=1_000_000)
    bundle.economy = ExpandedEconomyStats(**bundle.economy.model_dump())
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "strategic_reserve",
            formula="-target * resources.fresh_water.deficit * 0.25",
        )
    ]

    make_engine(bundle, seed=19).run()

    assert bundle.economy.strategic_reserve == pytest.approx(75)


@pytest.mark.parametrize(
    ("mode", "factory", "target"),
    (
        (GameMode.BASIC, make_basic_bundle, "social_mobility"),
        (GameMode.ATTERIUM, make_atterium_bundle, "plan_efficiency"),
        (GameMode.ISF, make_isf_bundle, "imperial_court_power"),
    ),
)
def test_configured_stat_effect_runs_a_full_turn_in_every_game_mode(
    mode: GameMode,
    factory,
    target: str,
) -> None:
    bundle = factory(budget=1_000_000)
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            target,
            formula="-target * resources.fresh_water.deficit * 0.1",
        )
    ]
    engine = make_engine(bundle, seed=20)
    engine.rules = get_mode(mode).rules_factory()
    engine.mode_name = mode.value

    report = engine.run()
    result = bundle.industry.last_effects[0]

    assert report.mode == mode.value
    assert result.target == target
    assert result.target_after == pytest.approx(result.target_before * 0.9)


def test_arbitrary_targets_survive_yaml_configuration_roundtrip():
    bundle = make_basic_bundle()
    configure_fresh_water_shortage(bundle)
    bundle.industry.effects = [
        water_effect(
            "logistic",
            "agriculture.expected_wastes",
            "industrial_accident_chance",
            formula="-target * resources.fresh_water.deficit * 0.1",
        )
    ]

    configuration = bundle.industry.render_configuration()
    restored = IndustrialStats.from_stats_text(
        f"{bundle.industry}\n{configuration}"
    )

    assert restored.effects == bundle.industry.effects
    assert "agriculture.expected_wastes" in configuration
