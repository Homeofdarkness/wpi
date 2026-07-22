"""Shared turn engine for every world ruleset."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from numpy.random import Generator

from functions import agriculture_models as agriculture
from functions import industry_models as industry
from functions import probability_models as probability
from functions import production_models as production
from functions import resource_models as resources
from functions import trade_models as trade
from functions.income_models import (
    agriculture_factor,
    expected_infrastructure_wastes,
    inflation_factor,
    simple_stability_income_boost,
    stability_income_boost,
)
from functions.society_models import (
    agriculture_income_factor,
    contentment_coefficients,
    cultural_coefficient,
    expected_state_apparatus_size,
    food_diversity_income_factor,
    knowledge_level,
    population_decrement_factor,
    social_decline_income_factor,
    stability_coefficient,
)
from functions.time_models import MONTH_YEARS, TURN_MONTHS, TURN_YEARS
from modules.skip_move_rules import BasicSkipMoveRules, SkipMoveRules
from modules.skip_move_types import (
    CalculationResults,
    SkipMoveContext,
    SkipMoveReport,
    TurnLedger,
    WorldState,
)
from stats.industry_components import ResourceKind
from utils.logger_manager import get_logger
from utils.user_io import ConsoleIO, UserIO


logger = get_logger("Turn Engine")


@dataclass(kw_only=True)
class TurnEngine:
    """Resolve one turn by mutating a single explicit world state."""

    state: WorldState
    rules: SkipMoveRules = field(default_factory=BasicSkipMoveRules)
    io: UserIO = field(default_factory=ConsoleIO)
    mode_name: str = "basic"
    waste: float = 0.0
    rng: Generator = field(default_factory=np.random.default_rng)
    last_report: SkipMoveReport | None = field(default=None, init=False)

    def _ctx(self) -> SkipMoveContext:
        return SkipMoveContext(state=self.state, waste=self.waste)

    def run(self) -> SkipMoveReport:
        # API clients may reuse an engine for several turns.  Start from the
        # current primary state, not from derived values already modified by
        # the previous turn.
        self.state.economy.recalculate_derived_fields()
        self.state.industry.recalculate_derived_fields()
        self.state.inner_politics.recalculate_derived_fields()
        economy = self.state.economy
        budget_before = float(economy.current_budget)
        logistic_wastes = self._logistic_wastes()
        results = self._prepare_calculations(logistic_wastes)
        self._update_industrial_workforce()
        self._calculate_operational_probabilities()

        self._calculate_agriculture(results)
        self._calculate_population(results)
        self._calculate_industry()
        self._calculate_tax(results)
        self._calculate_trade()
        ledger = self._calculate_income(results, logistic_wastes)
        self._calculate_event_probabilities()

        report = self._finalize(
            budget_before=budget_before,
            logistic_discount=float(results.logistic_params.discount),
            contentment_coefficient=float(results.contentment_coefficient_2),
            ledger=ledger,
        )
        taken, amount, final_budget = self._apply_credit_if_needed()
        report.credit_taken = taken
        report.credit_amount = float(amount or 0.0)
        report.budget_final = final_budget
        self.last_report = report
        return report

    def _logistic_wastes(self) -> float:
        economy = self.state.economy
        politics = self.state.inner_politics
        return float(
            economy.gov_wastes[1]
            + politics.provinces_count * politics.provinces_waste
        )

    def _total_wastes(self, logistic_wastes: float) -> float:
        economy = self.state.economy
        agriculture_state = self.state.agriculture
        return float(
            sum(economy.med_wastes)
            + sum(economy.gov_wastes)
            + sum(economy.war_wastes)
            + sum(economy.other_wastes)
            + logistic_wastes
            - economy.gov_wastes[1]
            + self.waste
            + agriculture_state.expected_wastes
            - agriculture_state.income_from_resources
            + self._debt_interest()
            + self._forced_labor_cost()
        )

    def _debt_interest(self) -> float:
        economy = self.state.economy
        return float(
            economy.public_debt
            * economy.annual_interest_rate
            / 100
            * TURN_YEARS
        )

    def _forced_labor_cost(self) -> float:
        state = self.state.industry
        return state.workforce.forced_workers / 10_000 * 0.1

    def _update_industrial_workforce(self) -> None:
        economy = self.state.economy
        industry_state = self.state.industry
        agriculture_state = self.state.agriculture
        politics = self.state.inner_politics
        workforce = industry_state.workforce
        workforce.specialist_capacity = resources.specialist_capacity(
            economy.population_count,
            politics.knowledge_level,
            politics.education_level,
        )
        if workforce.auto_size:
            workforce.specialist_workers = workforce.specialist_capacity
            worker_security = (
                industry_state.usages[2]
                if len(industry_state.usages) > 2
                else 0.0
            )
            workforce.ordinary_workers = round(
                economy.population_count
                * 0.35
                * min(max(worker_security / 100, 0.0), 1.0)
            )
        population_millions = max(economy.population_count / 1_000_000, 0.1)
        healthcare = economy.med_wastes[1] / population_millions
        social_spending = economy.med_wastes[3] / population_millions
        food_security = float(agriculture_state.food_security or 50.0)
        health_target = probability.clip_percent(
            40 + healthcare * 1.5 + min(max(food_security, 0.0), 100) * 0.25
        )
        social_target = probability.clip_percent(
            35
            + social_spending * 2
            + politics.contentment * 0.3
            - politics.poor_level * 0.2
        )
        adjustment = 0.5 * TURN_YEARS
        workforce.health += (health_target - workforce.health) * adjustment
        workforce.social_support += (
            social_target - workforce.social_support
        ) * adjustment

    def _worker_allocations(self) -> dict[str, tuple[int, int, int]]:
        """Allocate workers by automatically calculated rule capacity."""
        capacities = self._extraction_capacities()
        total_capacity = sum(capacities.values())
        if total_capacity <= 0:
            return {}
        workforce = self.state.industry.workforce
        return {
            operation.target_key: (
                round(
                    workforce.ordinary_workers
                    * capacities[operation.target_key]
                    / total_capacity
                ),
                round(
                    workforce.specialist_workers
                    * capacities[operation.target_key]
                    / total_capacity
                ),
                round(
                    workforce.forced_workers
                    * capacities[operation.target_key]
                    / total_capacity
                ),
            )
            for operation in self._active_extraction_operations()
        }

    def _extraction_capacities(self) -> dict[str, float]:
        operations = self._active_extraction_operations()
        total_priority = sum(operation.priority for operation in operations)
        if total_priority <= 0:
            return {}
        extraction_spending = self.rules.get_resource_extraction_budget(
            self._ctx()
        )
        national_capacity = resources.national_extraction_capacity(
            extraction_spending
        )
        return {
            operation.target_key: (
                national_capacity
                * operation.priority
                / total_priority
                * operation.intensity
                / 100
            )
            for operation in operations
        }

    def _active_extraction_operations(self):
        return [
            operation
            for operation in self.state.industry.extraction_operations
            if operation.intensity > 0
        ]

    def _calculate_operational_probabilities(self) -> None:
        state = self.state.industry
        politics = self.state.inner_politics
        stats = self.state.probabilities
        equipment_mean = probability.equipment_availability_mean(
            state.processing_efficiency,
            state.standardization,
            state.processing_usage,
        )
        attendance_mean = probability.workforce_attendance_mean(
            state.workforce.health,
            state.workforce.social_support,
            politics.war_fatigue,
        )
        process_mean = probability.process_yield_mean(
            state.processing_efficiency,
            state.standardization,
        )
        logistics_mean = probability.logistics_integrity_mean(
            state.logistic,
            politics.regional_separatism,
            politics.war_fatigue,
        )
        storage_mean = probability.storage_preservation_mean(state.logistic)
        research_mean = probability.research_reproducibility_mean(
            politics.knowledge_level,
            politics.education_level,
            politics.erudition_will,
            politics.information_quality,
        )
        stats.equipment_availability = probability.sample_percent(
            equipment_mean,
            self.rng,
        )
        stats.workforce_attendance = probability.sample_percent(
            attendance_mean,
            self.rng,
        )
        stats.process_yield = probability.sample_percent(
            process_mean,
            self.rng,
        )
        stats.logistics_integrity = probability.sample_percent(
            logistics_mean,
            self.rng,
        )
        stats.storage_preservation = probability.sample_percent(
            storage_mean,
            self.rng,
        )
        stats.research_reproducibility = probability.sample_percent(
            research_mean,
            self.rng,
        )

    def _calculate_event_probabilities(self) -> None:
        economy = self.state.economy
        industry_state = self.state.industry
        agriculture_state = self.state.agriculture
        politics = self.state.inner_politics
        stats = self.state.probabilities
        allocations = self._worker_allocations()
        ordinary = sum(item[0] for item in allocations.values())
        specialists = sum(item[1] for item in allocations.values())
        forced = sum(item[2] for item in allocations.values())
        total_workers = ordinary + specialists + forced
        forced_share = forced / max(total_workers, 1)
        safety = industry_state.standardization
        control_balance = (
            politics.control[0]
            + politics.control[1]
            - politics.control[2]
            - politics.control[3]
        )
        healthcare_per_million = (
            economy.med_wastes[1]
            / max(economy.population_count, 1)
            * 1_000_000
        )
        provinces_support = min(max(politics.provinces_waste / 5, 0.0), 1.0)
        stats.industrial_accident_chance = (
            probability.industrial_accident_chance(
                industry_state.processing_usage,
                stats.equipment_availability,
                industry_state.standardization,
                forced_share,
                safety,
            )
        )
        stats.supply_disruption_chance = probability.supply_disruption_chance(
            stats.logistics_integrity,
            politics.regional_separatism,
            politics.war_fatigue,
        )
        stats.population_epidemic_chance = (
            probability.population_epidemic_chance(
                healthcare_per_million,
                politics.poor_level,
                agriculture_state.food_security,
                politics.information_quality,
            )
        )
        stats.agricultural_epidemic_chance = (
            probability.agricultural_epidemic_chance(
                agriculture_state.agriculture_deceases,
                agriculture_state.food_diversity,
                agriculture_state.agriculture_efficiency,
            )
        )
        stats.natural_disaster_chance = probability.natural_disaster_chance(
            agriculture_state.agriculture_natural_deceases,
            agriculture_state.biome_richness,
        )
        stats.mass_protest_chance = probability.mass_protest_chance(
            politics.contentment,
            politics.government_trust,
            politics.inequality,
            politics.polarization,
            politics.war_fatigue,
        )
        stats.separatist_crisis_chance = probability.separatist_crisis_chance(
            politics.regional_separatism,
            politics.polarization,
            control_balance,
            provinces_support,
        )
        stats.major_sabotage_chance = probability.major_sabotage_chance(
            forced_share,
            politics.violence_tendency,
            politics.polarization,
            politics.information_quality,
        )

    def _prepare_calculations(
        self,
        logistic_wastes: float,
    ) -> CalculationResults:
        economy = self.state.economy
        agriculture_state = self.state.agriculture
        politics = self.state.inner_politics
        logistic = self.rules.calculate_logistic_params(
            self._ctx(),
            logistic_wastes,
        )
        culture = cultural_coefficient(
            politics.cultural_level,
            politics.egocentrism_development,
        )
        contentment_first, contentment_second = contentment_coefficients(
            politics.contentment + logistic.contentment_spotter
        )
        return CalculationResults(
            logistic_params=logistic,
            culture_coefficient=culture,
            contentment_coefficient_1=contentment_first,
            contentment_coefficient_2=contentment_second,
            expected_infrastructure_waste=expected_infrastructure_wastes(
                economy.population_count
            ),
            workers_count=agriculture.workers_count(
                economy.population_count,
                agriculture_state.workers_percent,
                agriculture_state.workers_redistribution,
            ),
        )

    def _calculate_agriculture(self, results: CalculationResults) -> None:
        economy = self.state.economy
        state = self.state.agriculture
        state.expected_wastes = agriculture.agriculture_wastes(
            results.workers_count,
            state.securities,
            state.husbandry,
            state.livestock,
            state.others,
        )
        state.food_diversity = agriculture.food_diversity(
            state.husbandry,
            state.livestock,
            state.others,
            state.biome_richness,
        )
        state.agriculture_efficiency = agriculture.agriculture_efficiency(
            state.securities,
            state.biome_richness,
            state.husbandry,
            state.livestock,
            state.others,
            state.agriculture_deceases,
            state.agriculture_natural_deceases,
            results.workers_count,
            economy.population_count,
        )
        state.agriculture_development = agriculture.agriculture_development(
            state.securities,
            results.workers_count,
            economy.population_count,
            state.biome_richness,
            state.food_diversity,
            state.husbandry,
            state.livestock,
            state.others,
        )
        produced = round(
            agriculture.food_income(
                results.workers_count,
                state.securities,
                state.overprotective_effects,
                state.agriculture_deceases,
                state.agriculture_natural_deceases,
                state.environmental_food,
            )
        )
        consumed = round(
            agriculture.food_consumption(
                economy.population_count,
                state.consumption_factor,
            )
        )
        state.food_security = agriculture.food_security_index(
            produced,
            consumed,
        )
        self.rules.postprocess_agriculture(self._ctx())
        state.food_security += results.logistic_params.food_security_spotter
        adjusted_index = max(float(state.food_security), 0.0)
        food_balance = (
            consumed * (adjusted_index / 100 - 1) if consumed > 0 else 0.0
        )

        if food_balance >= 0:
            state.food_supplies = round(
                agriculture.food_supplies(
                    state.food_supplies,
                    food_balance,
                    state.overstock_percent,
                    state.storages_upkeep,
                ),
                1,
            )
        else:
            taken_from_supplies = min(-food_balance, state.food_supplies)
            state.food_supplies = round(
                state.food_supplies - taken_from_supplies,
                1,
            )
            food_balance += taken_from_supplies

        effective_food = consumed + food_balance
        state.food_security = round(
            agriculture.food_security_index(effective_food, consumed),
            1,
        )
        results.food_balance = food_balance

    def _calculate_population(self, results: CalculationResults) -> None:
        economy = self.state.economy
        agriculture_state = self.state.agriculture
        politics = self.state.inner_politics
        multipliers = (
            industry.goods_coefficient(self.state.industry.tvr1),
            stability_coefficient(
                politics.poor_level,
                politics.jobless_level,
                sum(economy.med_wastes),
                economy.population_count,
            )
            * results.contentment_coefficient_1
            * (0.015 * politics.many_children_propoganda + 1),
            agriculture_income_factor(agriculture_state.food_security),
            social_decline_income_factor(politics.society_decline),
            food_diversity_income_factor(agriculture_state.food_diversity),
        )
        for multiplier in multipliers:
            economy.income *= multiplier

        population_after_decline = round(
            economy.population_count
            * population_decrement_factor(economy.decrement_coefficient)
        )
        population_with_growth = population_after_decline + round(
            economy.income
        )
        deaths = agriculture.population_underfeed(
            population_with_growth,
            results.food_balance,
            agriculture_state.biome_richness,
            rng=self.rng,
        )
        economy.population_count = max(0, int(population_with_growth - deaths))

    def _calculate_industry(self) -> None:
        economy = self.state.economy
        state = self.state.industry
        self._advance_industrial_resources()
        self._process_production_rules()
        self._spend_industrial_resources()
        # Resource coverage changes civil security.  Refresh its dependent
        # efficiency and cost fields before trade and income use them.
        state.recalculate_derived_fields()
        state.consumption_of_goods = industry.consumption_of_goods(
            economy.population_count,
            economy.trade_usage,
            economy.trade_efficiency,
            state.tvr1,
            state.tvr2,
        )[0]
        state.overproduction_coefficient += (
            industry.industry_overproduction_change(
                state.tvr1,
                state.tvr2,
                state.consumption_of_goods,
                economy.trade_usage,
            )
        )
        state.overproduction_coefficient = min(
            100.0,
            max(0.0, state.overproduction_coefficient),
        )
        state.industry_income = industry.industry_income(
            economy.gov_wastes,
            state.civil_usage,
            state.max_potential,
            state.expected_wastes,
        )

    def _advance_industrial_resources(self) -> None:
        state = self.state.industry
        operational = self.state.probabilities
        state.last_extracted = {}
        allocations = self._worker_allocations()
        capacities = self._extraction_capacities()
        for _ in range(TURN_MONTHS):
            for operation in self._active_extraction_operations():
                operation_capacity = capacities.get(operation.target_key, 0.0)
                if operation_capacity <= 0:
                    continue
                target_states = self._extraction_targets(operation)
                shares = self._extraction_shares(target_states)
                ordinary, specialists, forced = allocations[
                    operation.target_key
                ]
                for resource_state, share in zip(
                    target_states,
                    shares,
                    strict=True,
                ):
                    if share <= 0:
                        continue
                    labor = resources.effective_workers(
                        round(ordinary * share),
                        round(specialists * share),
                        round(forced * share),
                        state.workforce.health,
                        state.workforce.social_support,
                        operational.workforce_attendance,
                    )
                    extracted = resources.extraction_output(
                        extraction_capacity=(operation_capacity * share),
                        accessibility=resource_state.accessibility,
                        quality=resource_state.quality,
                        technology=state.processing_efficiency,
                        effective_labor=labor,
                        equipment_availability=(
                            operational.equipment_availability
                        ),
                        process_yield=operational.process_yield,
                        years=MONTH_YEARS,
                        profile=resources.GROUP_PROFILES[
                            state.resolve_extraction_target(operation)[0]
                        ],
                    )
                    transfer = resource_state.collect(extracted)
                    state.last_extracted[resource_state.resource] = (
                        state.last_extracted.get(
                            resource_state.resource,
                            0.0,
                        )
                        + transfer.actual
                    )
        for resource_state in state.resource_inventory.resources.values():
            resource_state.apply_storage_preservation(
                operational.storage_preservation
            )

    def _extraction_targets(self, operation):
        state = self.state.industry
        inventory = state.resource_inventory.resources
        target_group, target_resource = state.resolve_extraction_target(
            operation
        )
        if target_resource is not None:
            candidates = [inventory[target_resource]]
        else:
            resource_overrides = {
                resolved_resource
                for item in self._active_extraction_operations()
                if (
                    resolved_resource := state.resolve_extraction_target(item)[
                        1
                    ]
                )
                is not None
            }
            candidates = [
                resource_state
                for resource_state in inventory.values()
                if resource_state.definition.group is target_group
                and resource_state.resource not in resource_overrides
            ]
        return [
            resource_state
            for resource_state in candidates
            if resource_state.enabled
            and resource_state.definition.kind
            not in {ResourceKind.MANUFACTURED, ResourceKind.BYPRODUCT}
            and resource_state.stockpile < resource_state.storage_capacity
        ]

    def _extraction_shares(self, target_states) -> list[float]:
        if not target_states:
            return []
        industry_state = self.state.industry
        urgent = [
            max(
                industry_state.resource_demands.get(item.resource, 0.0)
                - item.stockpile,
                0.0,
            )
            + industry_state.resource_shortages.get(item.resource, 0.0)
            for item in target_states
        ]
        weights = urgent
        if sum(weights) <= 0:
            weights = [
                max(item.storage_capacity - item.stockpile, 0.0)
                for item in target_states
            ]
        if sum(weights) <= 0:
            weights = [1.0] * len(target_states)
        total = sum(weights)
        return [weight / total for weight in weights]

    def _process_production_rules(self) -> None:
        state = self.state.industry
        active_rules = [
            rule for rule in state.production_rules if rule.enabled
        ]
        state.last_production = []
        for rule in active_rules:
            result = production.execute_rule(
                state.resource_inventory,
                rule,
                self.state.probabilities.process_yield,
            )
            rule.advance_turn()
            state.last_production.append(
                replace(result, turns_remaining=rule.turns_remaining)
            )

    def _spend_industrial_resources(self) -> None:
        state = self.state.industry
        state.resource_shortages = {}
        total_requested = 0.0
        total_spent = 0.0
        for resource, amount in state.resource_demands.items():
            transfer = state.spend_resource(resource, amount)
            state.resource_shortages[resource] = transfer.shortage
            total_requested += transfer.requested
            total_spent += transfer.actual
        if total_requested <= 0:
            return
        resource_security = total_spent / total_requested * 100
        state.civil_security = round(
            (state.civil_security + resource_security) / 2,
            2,
        )

    def _calculate_tax(self, results: CalculationResults) -> None:
        self.state.economy.tax_income = self.rules.calculate_tax_income(
            self._ctx(),
            results,
        )

    def _calculate_trade(self) -> None:
        economy = self.state.economy
        industry_state = self.state.industry
        politics = self.state.inner_politics
        logistic_wastes = self._logistic_wastes()
        total_wastes = self._total_wastes(logistic_wastes)
        control = (
            politics.control[0]
            + politics.control[1]
            - politics.control[2]
            - politics.control[3]
        )
        features = trade.ForexFeatures(
            stability=economy.stability,
            income=economy.tax_income,
            wastes=total_wastes,
            budget=economy.current_budget,
            trade_rank=economy.trade_rank,
            trade_efficiency=economy.trade_efficiency,
            trade_overload=economy.trade_usage_load(),
            industry_efficiency=industry_state.civil_efficiency,
            state_apparatus_efficiency=(politics.state_apparatus_efficiency),
            contentment=politics.contentment,
            poor_level=politics.poor_level,
            jobless_level=politics.jobless_level,
            control_balance=control,
        )
        economy.forex = trade.forex_course(features)
        economy.trade_income = trade.trade_income(
            economy.trade_potential,
            economy.trade_usage,
            economy.trade_efficiency,
            economy.trade_wastes,
            economy.high_quality_percent,
            economy.mid_quality_percent,
            economy.low_quality_percent,
            economy.forex,
            economy.valgery,
        )
        self.rules.postprocess_trade_income(self._ctx())

    def _calculate_income(
        self,
        results: CalculationResults,
        logistic_wastes: float,
    ) -> TurnLedger:
        economy = self.state.economy
        industry_state = self.state.industry
        politics = self.state.inner_politics
        agriculture_state = self.state.agriculture
        trade_factor = trade.allegorization_trade_factor(
            economy.allegorization
        )
        economy_factor = trade.allegorization_economy_factor(
            economy.allegorization
        )
        agriculture_addition = agriculture_factor(
            economy.tax_income,
            agriculture_state.agriculture_development,
            results.workers_count,
        )
        economy.trade_income *= trade_factor
        economy.branches_income *= trade_factor
        economy.tax_income *= economy_factor
        economy.tax_income += agriculture_addition
        industry_state.industry_income *= economy_factor
        science_income = float(
            getattr(politics, "income_from_scientific", 0) or 0
        )
        ledger = TurnLedger(
            tax_income=float(economy.tax_income),
            trade_income=float(economy.trade_income),
            branches_income=float(economy.branches_income),
            industry_income=float(industry_state.industry_income),
            science_income=science_income,
            resource_balance=float(economy.resource_balance),
            debt_interest=self._debt_interest(),
            total_wastes=self._total_wastes(logistic_wastes),
            inflation_factor=inflation_factor(economy.inflation),
        )
        mode_factor = 1.0
        for multiplier in self.rules.money_income_extra_multipliers(
            self._ctx()
        ):
            mode_factor *= multiplier
        ledger = replace(ledger, mode_income_factor=mode_factor)
        economy.money_income = ledger.net_income
        return ledger

    def _update_stability(
        self,
        contentment_coefficient: float,
    ) -> tuple[float, float]:
        economy = self.state.economy
        politics = self.state.inner_politics
        expected_size = expected_state_apparatus_size(
            economy.population_count,
            self.rules.get_state_apparatus_budget_spent(self._ctx()),
        )
        updated = economy.stability
        if expected_size > politics.state_apparatus_size:
            updated -= 10
        elif politics.state_apparatus_efficiency > 60 and updated < 100:
            updated = min(updated + 5, 99)

        if (
            80 <= updated <= 99
            and politics.poor_level < 6
            and politics.jobless_level < 12
            and contentment_coefficient > 0.8
        ):
            boost = stability_income_boost(
                updated,
                politics.poor_level,
                politics.jobless_level,
            )
        else:
            boost = simple_stability_income_boost(updated)
        return float(updated), float(boost)

    def _update_education(self) -> None:
        economy = self.state.economy
        politics = self.state.inner_politics
        expected = min(
            knowledge_level(
                economy.population_count,
                economy.med_wastes[0] + economy.med_wastes[4],
            ),
            100,
        )
        difference = expected - politics.education_level
        if difference < 0:
            reduction = abs(difference) // 8
            politics.education_level = round(
                max(expected, politics.education_level - reduction)
            )
        else:
            politics.education_level += abs(difference) / max(
                politics.education_level,
                1,
            )
        politics.recalculate_derived_fields()

    def _update_military_equipment(self) -> None:
        economy = self.state.economy
        industry_state = self.state.industry
        politics = self.state.inner_politics
        politics.military_equipment += (
            economy.war_wastes[1]
            * industry_state.war_production_efficiency
            / 50
        )

    def _finalize(
        self,
        *,
        budget_before: float,
        logistic_discount: float,
        contentment_coefficient: float,
        ledger: TurnLedger,
    ) -> SkipMoveReport:
        economy = self.state.economy
        economy.prev_budget = budget_before
        budget_after_raw = (
            budget_before + ledger.net_income + logistic_discount
        )
        stability_after, boost = self._update_stability(
            contentment_coefficient
        )
        ledger = replace(ledger, stability_income_factor=boost)
        economy.money_income = ledger.net_income
        budget_after_boost = (
            budget_before + ledger.net_income + logistic_discount
        )
        economy.current_budget = budget_after_boost
        economy.stability = round(stability_after)
        self._update_education()
        self._update_military_equipment()
        return SkipMoveReport(
            mode=self.mode_name,
            budget_before=budget_before,
            logistic_wastes=self._logistic_wastes(),
            total_wastes=ledger.total_wastes,
            logistic_discount=logistic_discount,
            tax_income=ledger.tax_income,
            trade_income=ledger.trade_income,
            branches_income=ledger.branches_income,
            industry_income=ledger.industry_income,
            science_income=ledger.science_income,
            resource_balance=ledger.resource_balance,
            debt_interest=ledger.debt_interest,
            money_income=float(ledger.net_income),
            budget_after_raw=float(budget_after_raw),
            stability_after=stability_after,
            income_boost=boost,
            budget_after_boost=float(budget_after_boost),
            budget_final=float(budget_after_boost),
            ledger=ledger,
            probabilities=self.state.probabilities.model_copy(deep=True),
        )

    def _apply_credit_if_needed(self) -> tuple[bool, float | None, float]:
        economy = self.state.economy
        if economy.current_budget >= 0:
            return False, None, float(economy.current_budget)
        deficit = float(-economy.current_budget)
        desired_final = self.io.request_credit(deficit)
        if desired_final is None:
            return False, None, float(economy.current_budget)
        credit_amount = deficit + float(desired_final)
        self.io.print(f"Сумма кредита - {credit_amount}")
        economy.current_budget = float(desired_final)
        economy.public_debt += credit_amount
        return True, credit_amount, float(economy.current_budget)
