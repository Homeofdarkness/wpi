from __future__ import annotations

import numpy as np
import pytest

from functions.agriculture_models import (
    agricultural_area_hectares,
    agricultural_input_demand_per_month,
    food_diversity,
    food_requisition_amount,
    food_requisition_social_penalties,
    food_security_index,
    population_underfeed,
    underfeed_reference_death_probability,
)
from functions.society_models import (
    food_diversity_income_factor,
    natural_fertility_factor,
    racial_diversity_fertility_factor,
)
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def _engine_for(bundle) -> TurnEngine:
    return TurnEngine(
        state=WorldState(
            economy=bundle.economy,
            industry=bundle.industry,
            agriculture=bundle.agriculture,
            inner_politics=bundle.inner_politics,
        ),
        io=TestIO(),
        rng=np.random.default_rng(1),
    )


@pytest.mark.parametrize(
    ("produced", "consumed", "expected"),
    ((100, 100, 100), (107.2, 100, 107.2), (75, 100, 75)),
)
def test_food_security_is_a_unitless_coverage_index(
    produced: float,
    consumed: float,
    expected: float,
) -> None:
    assert food_security_index(produced, consumed) == pytest.approx(expected)


def test_food_diversity_is_bounded_and_its_growth_effect_is_monotonic() -> (
    None
):
    assert food_diversity(100, 0, 0, 10) == 0
    assert food_diversity(40, 40, 20, 150) == 100
    factors = [food_diversity_income_factor(value) for value in (0, 50, 100)]
    assert factors == sorted(factors)
    assert factors[0] > 0


def test_agricultural_area_and_inputs_follow_customer_rule() -> None:
    workers = 42_000

    assert agricultural_area_hectares(workers) == 84_000
    fertilizers, tools = agricultural_input_demand_per_month(workers)
    assert fertilizers == pytest.approx(84.0)
    assert tools == pytest.approx(42.0)


def test_fertility_factors_use_documented_percentage_scales() -> None:
    assert natural_fertility_factor(0) == 0
    assert natural_fertility_factor(100) == 1
    assert natural_fertility_factor(250) == 2.5
    assert racial_diversity_fertility_factor(-1000) == 0
    assert racial_diversity_fertility_factor(200) == pytest.approx(1.2)
    assert racial_diversity_fertility_factor(1000) == 2


def test_food_supplies_cover_a_shortage_before_hunger() -> None:
    bundle = make_basic_bundle()
    bundle.agriculture.workers_percent = 0
    bundle.agriculture.environmental_food = 0
    bundle.agriculture.food_supplies = 1_000
    bundle.economy.decrement_coefficient = 0
    population_before = bundle.economy.population_count

    _engine_for(bundle).run()

    assert bundle.agriculture.food_security == pytest.approx(100.0)
    assert 0 < bundle.agriculture.food_supplies < 1_000
    assert bundle.economy.population_count == (
        population_before + round(bundle.economy.income)
    )


def test_uncovered_shortage_reduces_security_and_population() -> None:
    bundle = make_basic_bundle()
    bundle.agriculture.workers_percent = 0
    bundle.agriculture.environmental_food = 0
    bundle.agriculture.food_supplies = 0
    population_before = bundle.economy.population_count

    _engine_for(bundle).run()

    assert bundle.agriculture.food_security == 0
    assert bundle.economy.population_count < population_before


@pytest.mark.parametrize(
    ("food_security", "expected"),
    (
        (100, 0.0),
        (90, 0.0025),
        (80, 0.01),
        (70, 0.02),
        (60, 0.05),
        (50, 0.10),
        (0, 0.36),
    ),
)
def test_underfeed_mortality_has_three_continuous_nonlinear_zones(
    food_security: float,
    expected: float,
) -> None:
    assert underfeed_reference_death_probability(
        food_security
    ) == pytest.approx(expected)


def test_underfeed_mortality_accelerates_below_fifty_percent() -> None:
    probabilities = [
        underfeed_reference_death_probability(value)
        for value in (100, 90, 80, 70, 60, 50, 40, 25, 0)
    ]

    assert probabilities == sorted(probabilities)
    assert probabilities[6] > probabilities[5] * 1.8
    assert probabilities[7] > probabilities[6]


class _RecordingBinomial:
    def __init__(self) -> None:
        self.population = 0
        self.probability = 0.0

    def binomial(self, population: int, probability: float) -> int:
        self.population = population
        self.probability = probability
        return round(population * probability)


def test_underfeed_uses_the_actual_food_consumption_as_denominator() -> None:
    rng = _RecordingBinomial()

    deaths = population_underfeed(
        1_000_000,
        food_balance=-200,
        biome_richness=0,
        rng=rng,  # type: ignore[arg-type]
        reference_scale=0.5,
        food_consumed=1_000,
    )

    expected_probability = 1 - (1 - 0.01) ** 0.5
    assert rng.population == 200_000
    assert rng.probability == pytest.approx(expected_probability)
    assert deaths == round(200_000 * expected_probability)


@pytest.mark.parametrize(
    (
        "food_balance",
        "policy_percent",
        "storage_room",
        "expected",
    ),
    (
        (-200, 50, 1_000, 200),
        (0, 50, 1_000, 300),
        (-200, 50, 50, 50),
        (-600, 100, 1_000, 0),
        (-610, 100, 1_000, 0),
        (100, 100, 1_000, 0),
    ),
)
def test_food_requisition_only_uses_food_above_the_forty_percent_floor(
    food_balance: float,
    policy_percent: float,
    storage_room: float,
    expected: float,
) -> None:
    assert food_requisition_amount(
        1_000,
        food_balance,
        policy_percent,
        storage_room,
    ) == pytest.approx(expected)


def test_food_requisition_penalties_scale_with_consumption_share() -> None:
    contentment, trust = food_requisition_social_penalties(200, 1_000)

    assert contentment == pytest.approx(5)
    assert trust == pytest.approx(10 / 3)


def test_food_requisition_is_temporary_but_affects_the_current_turn() -> None:
    control = make_basic_bundle()
    affected = make_basic_bundle()
    for bundle, policy in ((control, 0), (affected, 50)):
        bundle.agriculture.workers_percent = 0
        bundle.agriculture.environmental_food = 280
        bundle.agriculture.food_supplies = 0
        bundle.agriculture.overstock_percent = policy
        bundle.economy.decrement_coefficient = 0

    contentment_before = affected.inner_politics.contentment
    trust_before = affected.inner_politics.government_trust
    control_report = _engine_for(control).run()
    affected_report = _engine_for(affected).run()
    requisition = affected_report.food_requisition

    assert requisition is not None
    assert control.agriculture.food_security == pytest.approx(80)
    assert affected.agriculture.food_security == pytest.approx(60)
    assert affected.agriculture.food_supplies == pytest.approx(35)
    assert requisition.amount == pytest.approx(35)
    assert requisition.consumption_share == pytest.approx(20)
    assert requisition.contentment_penalty == pytest.approx(5)
    assert requisition.government_trust_penalty == pytest.approx(10 / 3)
    assert affected.inner_politics.contentment == contentment_before
    assert affected.inner_politics.government_trust == trust_before
    assert (
        affected_report.probabilities.mass_protest_chance
        > control_report.probabilities.mass_protest_chance
    )
    assert (
        affected_report.population_growth.contentment_factor
        < control_report.population_growth.contentment_factor
    )
