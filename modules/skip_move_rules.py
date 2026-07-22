"""Ruleset-specific policy for the shared turn engine."""

from __future__ import annotations

from typing import Protocol

from functions import atterium_in_move_functions as atterium
from functions import isf_in_move_functions as isf
from functions.income_models import expected_logistic_wastes, tax_income
from functions.industry_models import (
    goods_coefficient,
    overproduction_tax_factor,
)
from functions.society_models import (
    integrity_of_faith_factor,
    panic_income_factor,
)
from modules.skip_move_types import (
    CalculationResults,
    LogisticParams,
    SkipMoveContext,
)


class SkipMoveRules(Protocol):
    """Operations that may differ between world rulesets."""

    def get_state_apparatus_budget_spent(
        self,
        ctx: SkipMoveContext,
    ) -> float: ...

    def get_resource_extraction_budget(
        self,
        ctx: SkipMoveContext,
    ) -> float: ...

    def calculate_logistic_params(
        self,
        ctx: SkipMoveContext,
        logistic_wastes: float,
    ) -> LogisticParams: ...

    def calculate_tax_income(
        self,
        ctx: SkipMoveContext,
        results: CalculationResults,
    ) -> float: ...

    def postprocess_trade_income(self, ctx: SkipMoveContext) -> None: ...

    def postprocess_agriculture(self, ctx: SkipMoveContext) -> None: ...

    def money_income_extra_multipliers(
        self,
        ctx: SkipMoveContext,
    ) -> tuple[float, ...]: ...


def _apply_tax_modifiers(
    value: float,
    ctx: SkipMoveContext,
    results: CalculationResults,
    *extra: float,
) -> float:
    modifiers = (
        results.contentment_coefficient_2,
        1 - results.logistic_params.tax_income_coefficient,
        integrity_of_faith_factor(ctx.inner_politics.integrity_of_faith),
        panic_income_factor(ctx.inner_politics.panic_level),
        *extra,
        overproduction_tax_factor(ctx.industry.overproduction_coefficient),
    )
    for modifier in modifiers:
        value *= modifier
    return value


class BasicSkipMoveRules:
    """Default world rules."""

    contentment_cap = 100

    def get_state_apparatus_budget_spent(
        self,
        ctx: SkipMoveContext,
    ) -> float:
        return float(ctx.economy.gov_wastes[2])

    def get_resource_extraction_budget(
        self,
        ctx: SkipMoveContext,
    ) -> float:
        return float(ctx.economy.gov_wastes[3])

    def calculate_logistic_params(
        self,
        ctx: SkipMoveContext,
        logistic_wastes: float,
    ) -> LogisticParams:
        params = LogisticParams()
        expected = expected_logistic_wastes(ctx.economy.gov_wastes)
        if expected <= logistic_wastes:
            params.discount = ctx.economy.gov_wastes[0] * 0.1
        else:
            params.tax_income_coefficient = 0.1

        salt_security = ctx.inner_politics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(
                bonus,
                self.contentment_cap - ctx.inner_politics.contentment,
            )

        total_control = sum(ctx.inner_politics.control[:2])
        if total_control >= 90:
            params.contentment_spotter = min(
                params.contentment_spotter + 5,
                self.contentment_cap - ctx.inner_politics.contentment,
            )
            params.tax_income_coefficient -= 0.05
        else:
            params.contentment_spotter -= 5
            params.tax_income_coefficient += (
                sum(ctx.inner_politics.control[2:4]) / 400
            )
        return params

    def calculate_tax_income(
        self,
        ctx: SkipMoveContext,
        results: CalculationResults,
    ) -> float:
        infrastructure_factor = (
            1.1
            if ctx.economy.gov_wastes[0]
            > results.expected_infrastructure_waste
            else 0.85
        )
        value = tax_income(
            ctx.economy.universal_tax * results.culture_coefficient,
            ctx.economy.excise * goods_coefficient(ctx.industry.tvr2),
            ctx.economy.additions,
            ctx.economy.small_enterprise_tax * infrastructure_factor,
            ctx.economy.large_enterprise_tax,
            ctx.inner_politics.small_enterprise_percent,
            ctx.inner_politics.large_enterprise_count,
            ctx.economy.population_count,
        )
        return _apply_tax_modifiers(value, ctx, results)

    def postprocess_trade_income(self, ctx: SkipMoveContext) -> None:
        return None

    def postprocess_agriculture(self, ctx: SkipMoveContext) -> None:
        return None

    def money_income_extra_multipliers(
        self,
        ctx: SkipMoveContext,
    ) -> tuple[float, ...]:
        return ()


class AtteriumSkipMoveRules(BasicSkipMoveRules):
    """Atterium taxation and income modifiers."""

    def get_state_apparatus_budget_spent(
        self,
        ctx: SkipMoveContext,
    ) -> float:
        return float(ctx.economy.gov_wastes[2] + ctx.economy.gov_wastes[3])

    def get_resource_extraction_budget(
        self,
        ctx: SkipMoveContext,
    ) -> float:
        return float(ctx.economy.gov_wastes[4])

    def calculate_tax_income(
        self,
        ctx: SkipMoveContext,
        results: CalculationResults,
    ) -> float:
        _, adrian_income = atterium.adrian_effect_factors(
            ctx.economy.adrian_effect
        )
        _, excise_factor, business_factor, _ = (
            atterium.economic_formation_factors(
                ctx.economy.power_of_economic_formation
            )
        )
        infrastructure_factor = (
            1.1
            if ctx.economy.gov_wastes[0]
            > results.expected_infrastructure_waste
            else 0.85
        )
        large_entities = max(
            ctx.inner_politics.large_enterprise_count / 4,
            0,
        )
        value = tax_income(
            ctx.economy.universal_tax * 0.7 * results.culture_coefficient,
            ctx.economy.excise
            * goods_coefficient(ctx.industry.tvr2)
            * excise_factor,
            ctx.economy.additions,
            ctx.economy.freedom_and_efficiency_of_small_business
            * infrastructure_factor
            * business_factor,
            ctx.economy.investment_of_large_companies
            * 0.35
            * atterium.plan_efficiency_factor(
                ctx.inner_politics.state_apparatus_functionality
            ),
            ctx.inner_politics.small_enterprise_percent,
            large_entities,
            ctx.economy.population_count,
        )
        value += atterium.plan_efficiency_income(
            ctx.economy.plan_efficiency,
            large_entities,
        )
        return _apply_tax_modifiers(
            value,
            ctx,
            results,
            atterium.huge_economy_buff(
                ctx.inner_politics.egocentrism_development
            ),
            adrian_income,
        )

    def postprocess_trade_income(self, ctx: SkipMoveContext) -> None:
        adrian_trade, _ = atterium.adrian_effect_factors(
            ctx.economy.adrian_effect
        )
        trade_factor, _, _, branches_factor = (
            atterium.economic_formation_factors(
                ctx.economy.power_of_economic_formation
            )
        )
        ctx.economy.trade_income *= adrian_trade * trade_factor
        ctx.economy.branches_income *= branches_factor


class IsfSkipMoveRules(BasicSkipMoveRules):
    """Empire of the Silver Phoenix rules."""

    contentment_cap = 125

    def calculate_logistic_params(
        self,
        ctx: SkipMoveContext,
        logistic_wastes: float,
    ) -> LogisticParams:
        params = LogisticParams()
        expected = expected_logistic_wastes(ctx.economy.gov_wastes)
        if expected <= logistic_wastes:
            params.discount = ctx.economy.gov_wastes[0] * 0.1
        else:
            params.tax_income_coefficient = 0.1

        salt_security = ctx.inner_politics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(
                bonus,
                self.contentment_cap - ctx.inner_politics.contentment,
            )
        params.contentment_spotter += isf.allegory_contentment_spotter(
            ctx.inner_politics.contentment,
            ctx.inner_politics.allegory_influence,
        )
        total_control = sum(ctx.inner_politics.control[:2])
        if total_control < 90:
            params.contentment_spotter = min(
                params.contentment_spotter + 5,
                self.contentment_cap - ctx.inner_politics.contentment,
            )
            params.tax_income_coefficient -= 0.05
            params.food_security_spotter -= 4
        else:
            params.contentment_spotter -= 5
            params.tax_income_coefficient += (
                sum(ctx.inner_politics.control[2:4]) / 400
            )
        return params

    def calculate_tax_income(
        self,
        ctx: SkipMoveContext,
        results: CalculationResults,
    ) -> float:
        infrastructure_factor = (
            1.1
            if ctx.economy.gov_wastes[0]
            > results.expected_infrastructure_waste
            else 0.85
        )
        value = tax_income(
            ctx.economy.universal_tax * results.culture_coefficient,
            ctx.economy.excise * goods_coefficient(ctx.industry.tvr2),
            ctx.economy.additions,
            ctx.economy.small_business_tax * infrastructure_factor,
            ctx.economy.large_enterprise_tax,
            ctx.inner_politics.small_enterprise_percent,
            ctx.inner_politics.large_enterprise_count,
            ctx.economy.population_count,
        )
        return _apply_tax_modifiers(value, ctx, results)

    def postprocess_agriculture(self, ctx: SkipMoveContext) -> None:
        ctx.agriculture.food_security *= 1 - (
            ctx.agriculture.empire_land_unmastery / 100
        )

    def money_income_extra_multipliers(
        self,
        ctx: SkipMoveContext,
    ) -> tuple[float, ...]:
        return (
            isf.allegory_income_factor(ctx.inner_politics.allegory_influence),
        )
