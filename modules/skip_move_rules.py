"""Skip-move rules for different game modes.

The project has several modes (basic / atterium / isf) with:
- mostly shared math formulas (in `functions/*_in_move_functions.py`)
- a few *rule* differences (tax composition, special modifiers, caps)

To keep the skip-move algorithm easy to extend, we split it into:
- **Engine** (`modules.run_skip_move`): generic step ordering + orchestration.
- **Rules** (this module): mode-specific policy decisions.

Adding a new mode should mostly be: implement a new Rules class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from modules.skip_move_types import CalculationResults, LogisticParams, \
    SkipMoveContext


class SkipMoveRules(ABC):
    """Mode-specific policy for the skip-move engine."""

    @abstractmethod
    def get_state_apparatus_budget_spent(self, ctx: SkipMoveContext) -> float:
        """Returns how much is spent on the state apparatus.

        This value is used to estimate the expected size of the apparatus.
        Different modes can store this value in different gov_wastes indices.
        """

    @abstractmethod
    def calculate_logistic_params(
            self,
            ctx: SkipMoveContext,
            logistic_wastes: float,
    ) -> LogisticParams:
        """Derive logistic parameters (discounts/spotters) for this mode."""

    @abstractmethod
    def calculate_tax_income(
            self,
            ctx: SkipMoveContext,
            results: CalculationResults,
            logistic_wastes: float,
    ) -> float:
        """Compute tax income for this mode (already includes all modifiers)."""

    def postprocess_trade_income(self, ctx: SkipMoveContext) -> None:
        """Optional: mutate ctx.economy.trade_income / branches_income."""

    def postprocess_agriculture(self, ctx: SkipMoveContext) -> None:
        """Optional: apply mode-specific agriculture tweaks."""

    def money_income_extra_multipliers(self, ctx: SkipMoveContext) -> list[
        float]:
        """Optional: additional multipliers applied to final money income."""
        return []


class BasicSkipMoveRules(SkipMoveRules):
    """Default rules for the base game."""

    def get_state_apparatus_budget_spent(self, ctx: SkipMoveContext) -> float:
        # In the base mode gov_wastes[2] corresponds to the state apparatus.
        return float(ctx.economy.gov_wastes[2])

    def calculate_logistic_params(self, ctx: SkipMoveContext,
                                  logistic_wastes: float) -> LogisticParams:
        params = LogisticParams()

        expected_logistic = ctx.in_move.calculate_expected_logistic_wastes(
            ctx.economy.gov_wastes)

        if expected_logistic <= logistic_wastes:
            params.discount = ctx.economy.gov_wastes[0] * 0.1
        else:
            params.tax_income_coefficient = 0.1

        # Salt effects
        salt_security = ctx.inner_politics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(bonus,
                                              100 - ctx.inner_politics.contentment)

        # Control effects
        total_control = ctx.inner_politics.control[0] + \
                        ctx.inner_politics.control[1]
        if total_control >= 90:
            params.contentment_spotter = min(params.contentment_spotter + 5,
                                             100 - ctx.inner_politics.contentment)
            params.tax_income_coefficient -= 0.05
        else:
            control_sum = ctx.inner_politics.control[2] + \
                          ctx.inner_politics.control[3]
            params.contentment_spotter -= 5
            params.tax_income_coefficient += control_sum / 400

        return params

    def calculate_tax_income(
            self,
            ctx: SkipMoveContext,
            results: CalculationResults,
            logistic_wastes: float,
    ) -> float:
        # Infrastructure overspend spotter
        small_enterprise_tax_spotter = 1.1 if ctx.economy.gov_wastes[
                                                  0] > results.expected_infrastructure_waste else 0.85

        base_tax_income = ctx.in_move.calculate_tax_income(
            ctx.economy.universal_tax * results.culture_coefficient,
            ctx.economy.excise * ctx.in_move.calculate_goods_coefficient(
                ctx.industry.tvr2),
            ctx.economy.additions,
            ctx.economy.small_enterprise_tax * small_enterprise_tax_spotter,
            ctx.economy.large_enterprise_tax,
            ctx.inner_politics.small_enterprise_percent,
            ctx.inner_politics.large_enterprise_count,
            ctx.economy.population_count,
        )

        modifiers = [
            results.contentment_coefficient_2,
            (1 - results.logistic_params.tax_income_coefficient),
            ctx.in_move.calculate_integrity_of_faith_factor(
                ctx.inner_politics.integrity_of_faith),
            ctx.in_move.calculate_income_coefficient_based_on_panic_level(
                ctx.inner_politics.panic_level),
            ctx.in_move.calculate_overproduction_tax_spotter(
                ctx.industry.overproduction_coefficient),
        ]

        tax_income = base_tax_income
        for m in modifiers:
            tax_income *= m

        return tax_income


class AtteriumSkipMoveRules(BasicSkipMoveRules):
    """Rules for Atterium.

    Differences vs basic:
    - different tax components (small business & large companies investment)
    - extra income from plan efficiency
    - extra buffs from Adrian effect + power of economic formation
    - apparatus spending is split across federal & republican items
    """

    def get_state_apparatus_budget_spent(self, ctx: SkipMoveContext) -> float:
        # In Atterium gov_wastes[2] and [3] are both apparatus-related.
        return float(ctx.economy.gov_wastes[2] + ctx.economy.gov_wastes[3])

    def calculate_tax_income(
            self,
            ctx: SkipMoveContext,
            results: CalculationResults,
            logistic_wastes: float,
    ) -> float:
        (trade_spotter_adrian,
         income_spotter_adrian) = ctx.in_move.calculate_adrian_effect_spotters(
            ctx.economy.adrian_effect)

        (trade_spotter_power, excise_spotter_power, business_spotter_power,
         branches_spotter_power) = (
            ctx.in_move.calculate_power_of_economic_formation_buffs(
                ctx.economy.power_of_economic_formation)
        )

        freedom_business_spotter = 1.1 if ctx.economy.gov_wastes[
                                              0] > results.expected_infrastructure_waste else 0.85

        large_entities = (
                ctx.inner_politics.large_enterprise_count / 4) if ctx.inner_politics.large_enterprise_count > 0 else 0

        base_tax_income = ctx.in_move.calculate_tax_income(
            (ctx.economy.universal_tax * 0.7) * results.culture_coefficient,
            ctx.economy.excise * ctx.in_move.calculate_goods_coefficient(
                ctx.industry.tvr2) * excise_spotter_power,
            ctx.economy.additions,
            ctx.economy.freedom_and_efficiency_of_small_business * freedom_business_spotter * business_spotter_power,
            (
                    ctx.economy.investment_of_large_companies * 0.35) * ctx.in_move.calculate_plan_efficiency_spotter(
                ctx.inner_politics.state_apparatus_functionality),
            ctx.inner_politics.small_enterprise_percent,
            large_entities,
            ctx.economy.population_count,
        )

        plan_efficiency_income = ctx.in_move.calculate_plan_efficiency_income(
            ctx.economy.plan_efficiency, large_entities)

        modifiers = [
            results.contentment_coefficient_2,
            (1 - results.logistic_params.tax_income_coefficient),
            ctx.in_move.calculate_integrity_of_faith_factor(
                ctx.inner_politics.integrity_of_faith),
            ctx.in_move.calculate_income_coefficient_based_on_panic_level(
                ctx.inner_politics.panic_level),
            ctx.in_move.calculate_huge_economy_buff(
                ctx.inner_politics.egocentrism_development),
            income_spotter_adrian,
            ctx.in_move.calculate_overproduction_tax_spotter(
                ctx.industry.overproduction_coefficient),
        ]

        tax_income = base_tax_income + plan_efficiency_income
        for m in modifiers:
            tax_income *= m

        return tax_income

    def postprocess_trade_income(self, ctx: SkipMoveContext) -> None:
        # Adrian + Power of economic formation
        trade_spotter_adrian = ctx.in_move.calculate_adrian_effect_spotters(
            ctx.economy.adrian_effect)[0]
        trade_spotter_power, _, _, branches_spotter_power = ctx.in_move.calculate_power_of_economic_formation_buffs(
            ctx.economy.power_of_economic_formation
        )

        ctx.economy.trade_income *= trade_spotter_adrian * trade_spotter_power
        ctx.economy.branches_income *= branches_spotter_power


class IsfSkipMoveRules(BasicSkipMoveRules):
    """Rules for the Empire of the Silver Phoenix (ISF).

    Differences vs basic:
    - contentment cap is 125
    - additional contentment spotter based on allegory influence
    - control thresholds are inverted (legacy rule)
    - tax field name is `small_business_tax`
    - postprocess agriculture: empire land unmastery
    - extra money income multiplier based on allegory influence
    """

    def get_state_apparatus_budget_spent(self, ctx: SkipMoveContext) -> float:
        return float(ctx.economy.gov_wastes[2])

    def calculate_logistic_params(
            self,
            ctx: SkipMoveContext,
            logistic_wastes: float
    ) -> LogisticParams:
        params = LogisticParams()

        expected_logistic = ctx.in_move.calculate_expected_logistic_wastes(
            ctx.economy.gov_wastes)

        if expected_logistic <= logistic_wastes:
            params.discount = ctx.economy.gov_wastes[0] * 0.1
        else:
            params.tax_income_coefficient = 0.1

        # Salt effects (cap 125)
        salt_security = ctx.inner_politics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(
                bonus,
                125 - ctx.inner_politics.contentment
            )

        # Allegory influence impacts contentment
        params.contentment_spotter += ctx.in_move.calculate_contentment_spotter_allegory(
            ctx.inner_politics.contentment,
            ctx.inner_politics.allegory_influence,
        )

        # Control effects (legacy inverted threshold)
        total_control = (
                ctx.inner_politics.control[0]
                + ctx.inner_politics.control[1]
        )
        if total_control < 90:
            params.contentment_spotter = min(
                params.contentment_spotter + 5,
                125 - ctx.inner_politics.contentment
            )
            params.tax_income_coefficient -= 0.05
            params.food_security_spotter -= 4
        else:
            control_sum = ctx.inner_politics.control[2] + \
                          ctx.inner_politics.control[3]
            params.contentment_spotter -= 5
            params.tax_income_coefficient += control_sum / 400

        return params

    def calculate_tax_income(
            self,
            ctx: SkipMoveContext,
            results: CalculationResults,
            logistic_wastes: float,
    ) -> float:
        # Map ISF field name -> base formula
        small_enterprise_tax_spotter = 1.1 if ctx.economy.gov_wastes[
                                                  0] > results.expected_infrastructure_waste else 0.85

        base_tax_income = ctx.in_move.calculate_tax_income(
            ctx.economy.universal_tax * results.culture_coefficient,
            ctx.economy.excise * ctx.in_move.calculate_goods_coefficient(
                ctx.industry.tvr2),
            ctx.economy.additions,
            ctx.economy.small_business_tax * small_enterprise_tax_spotter,
            ctx.economy.large_enterprise_tax,
            ctx.inner_politics.small_enterprise_percent,
            ctx.inner_politics.large_enterprise_count,
            ctx.economy.population_count,
        )

        modifiers = [
            results.contentment_coefficient_2,
            (1 - results.logistic_params.tax_income_coefficient),
            ctx.in_move.calculate_integrity_of_faith_factor(
                ctx.inner_politics.integrity_of_faith),
            ctx.in_move.calculate_income_coefficient_based_on_panic_level(
                ctx.inner_politics.panic_level),
            ctx.in_move.calculate_overproduction_tax_spotter(
                ctx.industry.overproduction_coefficient),
        ]

        tax_income = base_tax_income
        for m in modifiers:
            tax_income *= m

        return tax_income

    def postprocess_agriculture(self, ctx: SkipMoveContext) -> None:
        # ISF-specific debuff
        ctx.agriculture.food_security *= 1 - (
                ctx.agriculture.empire_land_unmastery / 100)

    def money_income_extra_multipliers(
            self,
            ctx: SkipMoveContext
    ) -> list[float]:
        return [ctx.in_move.calculate_money_income_allegory_factor(
            ctx.inner_politics.allegory_influence)]
