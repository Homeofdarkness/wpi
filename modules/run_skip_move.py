from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Tuple

from functions.atterium_in_move_functions import AtteriumInMoveFunctions
from functions.base import BaseInMoveFunctions
from functions.basic_in_move_functions import BasicInMoveFunctions
from functions.isf_in_move_functions import IsfInMoveFunctions
from modules.skip_move_rules import (
    AtteriumSkipMoveRules,
    BasicSkipMoveRules,
    IsfSkipMoveRules,
    SkipMoveRules,
)
from modules.skip_move_types import (
    CalculationResults,
    LogisticParams,
    SkipMoveContext,
    SkipMoveReport,
)
from stats.atterium_stats import (
    AtteriumAgricultureStats,
    AtteriumEconomyStats,
    AtteriumIndustrialStats,
    AtteriumInnerPoliticsStats,
)
from stats.basic_stats import (
    AgricultureStats,
    EconomyStats,
    IndustrialStats,
    InnerPoliticsStats
)
from stats.isf_stats import (
    IsfAgricultureStats,
    IsfEconomyStats,
    IsfIndustrialStats,
    IsfInnerPoliticsStats
)
from utils.logger_manager import get_logger
from utils.user_io import ConsoleIO, UserIO


logger = get_logger("Run Skip Move")


@dataclass
class SkipMoverBase(ABC):
    """Base class for skip-move with shared utility methods.

    The engine is intentionally mode-agnostic. Differences between modes are
    expressed via `InMoveFunctions` (formulas) and `Rules` (policy decisions).

    For testability, all user interaction goes through `io`.
    """

    Economy: Any
    Industry: Any
    Agriculture: Any
    InnerPolitics: Any
    waste: float = 0.0

    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BaseInMoveFunctions)
    Rules: SkipMoveRules = field(default_factory=BasicSkipMoveRules)

    io: UserIO = field(default_factory=ConsoleIO)
    mode_name: str = "unknown"

    last_report: SkipMoveReport | None = None

    def _ctx(self) -> SkipMoveContext:
        return SkipMoveContext(
            economy=self.Economy,
            industry=self.Industry,
            agriculture=self.Agriculture,
            inner_politics=self.InnerPolitics,
            waste=self.waste,
            in_move=self.InMoveFunctions,
        )

    # Backwards compatible entrypoint used by run_main
    def skip_move(self) -> None:
        self.run()

    @abstractmethod
    def run(self) -> SkipMoveReport:
        raise NotImplementedError

    def _calculate_logistic_wastes(self) -> float:
        """
        Logistic expenses:
        dedicated logistic spend + province management.
        """
        return float(
            self.Economy.gov_wastes[1]
            + self.InnerPolitics.provinces_count
            * self.InnerPolitics.provinces_waste
        )

    def _calculate_total_wastes(self, logistic_wastes: float) -> float:
        """Total expenses for the turn."""
        return float(
            sum(self.Economy.med_wastes)
            + sum(self.Economy.gov_wastes)
            + sum(self.Economy.war_wastes)
            + sum(self.Economy.other_wastes)
            + logistic_wastes
            + self.waste
            + self.Agriculture.expected_wastes
            - self.Agriculture.income_from_resources
        )

    def _apply_credit_if_needed(self) -> tuple[bool, float | None, float]:
        """Ask the user about a credit if the budget is negative.

        We intentionally apply credit **after** all income calculations,
        discounts and boosts. This keeps the math deterministic, and credit is
        treated as an external player decision that overrides the final budget.

        Returns: (credit_taken, credit_amount, budget_final)
        """
        if self.Economy.current_budget >= 0:
            return False, None, float(self.Economy.current_budget)

        deficit = float(-self.Economy.current_budget)
        desired_final = self.io.request_credit(deficit)
        if desired_final is None:
            return False, None, float(self.Economy.current_budget)

        credit_amount = deficit + float(desired_final)
        self.io.print(f"Сумма кредита - {credit_amount}")
        self.Economy.current_budget = float(desired_final)
        return True, credit_amount, float(self.Economy.current_budget)

    def _update_stability(
            self,
            rules: SkipMoveRules,
            contentment_coefficient_2: float
    ) -> Tuple[float, float]:
        """
        Update economic stability and return
        (buffed_stability, income_boost_coef).
        """
        ctx = self._ctx()
        apparatus_budget_spent = rules.get_state_apparatus_budget_spent(ctx)
        expected_size = self.InMoveFunctions.expected_state_apparatus(
            self.Economy.population_count,
            apparatus_budget_spent,
        )
        logger.debug(f"Ожидаемый размер гос. аппарата - {expected_size}")

        buffed_stability = self.Economy.stability
        logger.debug(
            f"Начальная экономическая стабильность - {buffed_stability}%")

        if expected_size > self.InnerPolitics.state_apparatus_size:
            buffed_stability -= 10
            logger.debug(
                f"Размер аппарата недостаточен, "
                f"стабильность снижена до {buffed_stability}%"
            )
        elif (
                self.InnerPolitics.state_apparatus_efficiency > 60
                and buffed_stability < 100
        ):
            buffed_stability = min(buffed_stability + 5, 99)
            logger.debug(
                f"Эффективный аппарат, "
                f"стабильность повышена до {buffed_stability}%"
            )

        if (
                80 <= buffed_stability <= 99
                and self.InnerPolitics.poor_level < 6
                and self.InnerPolitics.jobless_level < 12
                and contentment_coefficient_2 > 0.8
        ):
            boost = self.InMoveFunctions.calculate_money_income_boost(
                buffed_stability,
                self.InnerPolitics.poor_level,
                self.InnerPolitics.jobless_level,
            )
            logger.debug("Применен максимальный буст дохода")
        else:
            boost = self.InMoveFunctions.calculate_money_income_simple_boost(
                buffed_stability)
            logger.debug("Применен стандартный модификатор дохода")

        return float(buffed_stability), float(boost)

    def _update_education(self) -> None:
        """Update education level."""
        expected_knowledge = min(
            self.InMoveFunctions.calculate_knowledge(
                self.Economy.population_count,
                self.Economy.med_wastes[0] + self.Economy.med_wastes[4],
            ),
            100,
        )
        logger.debug(f"Ожидаемая образованность - {expected_knowledge}")

        knowledge_diff = expected_knowledge - self.InnerPolitics.education_level

        if knowledge_diff < 0:
            reduction = abs(knowledge_diff) // 8
            self.InnerPolitics.education_level = round(
                max(expected_knowledge,
                    self.InnerPolitics.education_level - reduction)
            )
            logger.debug(f"Образованность снижена на {reduction}")
        else:
            increase = abs(knowledge_diff) / max(
                self.InnerPolitics.education_level, 1)
            self.InnerPolitics.education_level += increase
            logger.debug(f"Образованность повышена на {increase}")

        self.InnerPolitics.recalculate_derived_fields()

    def _update_military_equipment(self) -> None:
        """Update military equipment score."""
        equipment_increase = (
                self.Economy.war_wastes[1]
                * self.InMoveFunctions.calculate_military_equipment_coefficient(
            self.Industry.war_production_efficiency)
        )
        self.InnerPolitics.military_equipment += equipment_increase


@dataclass(kw_only=True)
class BasicSkipMove(SkipMoverBase):
    """Generic skip-move engine for the base mode."""

    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats
    waste: float = 0.0

    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BasicInMoveFunctions)
    Rules: SkipMoveRules = field(default_factory=BasicSkipMoveRules)

    mode_name: str = "basic"

    def run(self) -> SkipMoveReport:
        try:
            budget_before = float(self.Economy.current_budget)
            logistic_wastes = self._calculate_logistic_wastes()
            results = self._perform_basic_calculations(logistic_wastes)

            self._calculate_income_and_expenses(results, logistic_wastes)

            total_wastes = self._calculate_total_wastes(logistic_wastes)

            report = self._finalize_calculations(
                budget_before=budget_before,
                logistic_discount=float(results.logistic_params.discount),
                total_wastes=total_wastes,
                contentment_coefficient_2=float(
                    results.contentment_coefficient_2),
            )

            credit_taken, credit_amount, budget_final = self._apply_credit_if_needed()
            report.credit_taken = credit_taken
            report.credit_amount = float(credit_amount or 0.0)
            report.budget_final = float(budget_final)

            self.last_report = report
            return report

        except Exception as e:
            logger.error(f"Ошибка при выполнении пропуска хода: {e}")
            raise

    def _perform_basic_calculations(
            self,
            logistic_wastes: float
    ) -> CalculationResults:
        ctx = self._ctx()
        logistic_params: LogisticParams = self.Rules.calculate_logistic_params(
            ctx, logistic_wastes)

        cultural_coefficient = self.InMoveFunctions.calculate_cultural_coefficient(
            self.InnerPolitics.cultural_level,
            self.InnerPolitics.egocentrism_development,
        )

        contentment_coefficient_1, contentment_coefficient_2 = self.InMoveFunctions.calculate_contentment_coefficients(
            self.InnerPolitics.contentment + logistic_params.contentment_spotter
        )

        expected_infrastructure_waste = self.InMoveFunctions.calculate_expected_infrastructure_wastes(
            self.Economy.population_count
        )

        workers_count = self.InMoveFunctions.calculate_workers_count(
            self.Economy.population_count,
            self.Agriculture.workers_percent,
            self.Agriculture.workers_redistribution
        )

        return CalculationResults(
            logistic_params=logistic_params,
            culture_coefficient=cultural_coefficient,
            contentment_coefficient_1=contentment_coefficient_1,
            contentment_coefficient_2=contentment_coefficient_2,
            expected_infrastructure_waste=expected_infrastructure_waste,
            workers_count=workers_count,
        )

    def _calculate_income_and_expenses(
            self,
            results: CalculationResults,
            logistic_wastes: float
    ) -> None:
        self._calculate_agriculture_stats(results)
        self._calculate_base_income(results)
        self._calculate_industry_stats()
        self._calculate_tax_income(results, logistic_wastes)
        self._calculate_trade_income()
        self._calculate_total_income(results, logistic_wastes)

    def _calculate_agriculture_stats(
            self,
            results: CalculationResults,
    ) -> None:
        self.Agriculture.expected_wastes = \
            self.InMoveFunctions.calculate_agriculture_wastes(
                results.workers_count,
                self.Agriculture.securities,
                self.Agriculture.husbandry,
                self.Agriculture.livestock,
                self.Agriculture.others,
            )
        self.Agriculture.food_diversity = \
            self.InMoveFunctions.calculate_food_diversity(
                self.Agriculture.husbandry,
                self.Agriculture.livestock,
                self.Agriculture.others,
                self.Agriculture.biome_richness
            )
        self.Agriculture.agriculture_development = \
            self.InMoveFunctions.calculate_agriculture_development(
                self.Agriculture.securities,
                results.workers_count,
                self.Agriculture.biome_richness,
                self.Agriculture.food_diversity,
                self.Agriculture.husbandry,
                self.Agriculture.livestock,
                self.Agriculture.others,
            )
        self.Agriculture.agriculture_efficiency = \
            self.InMoveFunctions.calculate_agriculture_efficiency(
                self.Agriculture.securities,
                self.Agriculture.expected_wastes,
                self.Agriculture.expected_wastes,
            )
        food_income = round(
            self.InMoveFunctions.calculate_food_income(
                results.workers_count,
                self.Agriculture.securities,
                self.Agriculture.overprotective_effects,
                self.Agriculture.agriculture_deceases,
                self.Agriculture.agriculture_natural_deceases,
                self.Agriculture.environmental_food
            )
        )
        food_consumption = round(
            self.InMoveFunctions.calculate_food_consumption(
                self.Economy.population_count,
                self.Agriculture.consumption_factor,
            )
        )
        self.Agriculture.food_security = round(
            self.InMoveFunctions.calculate_food_security(
                food_income,
                food_consumption
            )
        )
        self.Rules.postprocess_agriculture(self._ctx())

        self.Agriculture.food_supplies = round(
            self.InMoveFunctions.calculate_food_supplies(
                self.Agriculture.food_supplies,
                max(0., self.Agriculture.food_security),
                self.Agriculture.overstock_percent,
                self.Agriculture.storages_upkeep
            )
        )

        deficit = 1 - (self.Agriculture.food_supplies / food_consumption)
        thresholds = [(0.30, 150), (0.15, 100), (0.08, 50)]
        for d, target in thresholds:
            if deficit <= d or self.Agriculture.food_security >= target:
                continue

            need = target - self.Agriculture.food_security
            taken = min(need, self.Agriculture.food_supplies)
            self.Agriculture.food_supplies -= taken
            self.Agriculture.food_security += taken
            break

        results.real_food_security = self.Agriculture.food_security
        logger.debug(
            f"Итоговая расчетная обеспеченность едой - "
            f"{self.Agriculture.food_security}"
        )
        if self.Agriculture.food_security < 0:
            self.Agriculture._is_negative_food_security = True
            self.Agriculture.food_security = 0
            logger.debug("Прибили обеспеченность едой к 0")

    def _calculate_base_income(self, results: CalculationResults) -> None:
        income_multipliers = [
            self.InMoveFunctions.calculate_goods_coefficient(
                self.Industry.tvr1
            ),
            (
                    self.InMoveFunctions.calculate_stability_coefficient(
                        self.InnerPolitics.poor_level,
                        self.InnerPolitics.jobless_level,
                        sum(self.Economy.med_wastes),
                        self.Economy.population_count,
                    )
                    * results.contentment_coefficient_1
                    * (0.015 * self.InnerPolitics.many_children_propoganda + 1)
            ),
            self.InMoveFunctions.calculate_income_coefficient_based_on_agriculture(
                self.Agriculture.food_security
            ),
            self.InMoveFunctions.calculate_income_coefficient_based_on_social_decline(
                self.InnerPolitics.society_decline
            ),
            self.InMoveFunctions.calculate_income_coefficient_based_on_food_diversity(
                self.Agriculture.food_diversity
            ),
        ]

        for multiplier in income_multipliers:
            self.Economy.income *= multiplier

        self.Economy.population_count *= self.InMoveFunctions.calculate_population_decrement_coefficient(
            self.Economy.decrement_coefficient
        )
        self.Economy.population_count -= self.InMoveFunctions.calculate_population_underfeed(
            self.Economy.population_count,
            results.real_food_security or 0,
            self.Agriculture.biome_richness
        )

        logger.debug(f"Итоговый расчетный прирост - {self.Economy.income}")

    def _calculate_industry_stats(self) -> None:
        self.Industry.consumption_of_goods = \
            self.InMoveFunctions.calculate_consumption_of_goods(
                self.Economy.population_count,
                self.Economy.trade_usage,
                self.Economy.trade_efficiency,
                self.Industry.tvr1,
                self.Industry.tvr2,
            )[0]

        self.Industry.overproduction_coefficient += self.InMoveFunctions.calculate_industry_overproduction_change(
            self.Industry.tvr1,
            self.Industry.tvr2,
            self.Industry.consumption_of_goods,
            self.Economy.trade_usage,
        )

        self.Industry.industry_income = self.InMoveFunctions.calculate_industry_income(
            self.Economy.gov_wastes,
            self.Industry.civil_usage,
            self.Industry.max_potential,
            self.Industry.expected_wastes,
        )

    def _calculate_tax_income(
            self,
            results: CalculationResults,
            logistic_wastes: float
    ) -> None:
        ctx = self._ctx()
        self.Economy.tax_income = self.Rules.calculate_tax_income(
            ctx,
            results,
            logistic_wastes
        )
        logger.debug(f"Итоговый налоговый доход - {self.Economy.tax_income}")

    def _calculate_trade_income(self) -> None:
        logistic_wastes = self._calculate_logistic_wastes()
        total_wastes_for_forex = self._calculate_total_wastes(logistic_wastes)

        self.Economy.forex = self.InMoveFunctions.calculate_forex_course(
            self.Economy.stability,
            self.Economy.tax_income,
            total_wastes_for_forex,
            self.Economy.current_budget,
            self.Economy.trade_rank,
            self.Economy.trade_efficiency,
            self.Economy.trade_usage_load(),
            self.Industry.civil_efficiency,
            self.InnerPolitics.state_apparatus_efficiency,
            self.InnerPolitics.contentment,
            self.InnerPolitics.poor_level,
            self.InnerPolitics.jobless_level,
            self.InnerPolitics.control,
        )
        logger.debug(f"Курс валют - {self.Economy.forex}")

        base_trade_income = self.InMoveFunctions.calculate_trade_income(
            self.Economy.trade_potential,
            self.Economy.trade_usage,
            self.Economy.trade_efficiency,
            self.Economy.trade_wastes,
            self.Economy.high_quality_percent,
            self.Economy.mid_quality_percent,
            self.Economy.low_quality_percent,
            self.Economy.forex,
            self.Economy.valgery,
        )

        self.Economy.trade_income = base_trade_income
        self.Economy.trade_income *= self.InMoveFunctions.calculate_overproduction_trade_income(
            self.Industry.overproduction_coefficient
        )

        # Mode-specific trade tweaks
        self.Rules.postprocess_trade_income(self._ctx())

        logger.debug(f"Торговый доход - {self.Economy.trade_income}")

    def _calculate_total_income(
            self,
            results: CalculationResults,
            logistic_wastes: float
    ) -> None:
        total_wastes = self._calculate_total_wastes(logistic_wastes)
        logger.debug(f"Общие расходы - {total_wastes}")

        allegorization_trade_factor = self.InMoveFunctions.calculate_allegorization_trade_factor(
            self.Economy.allegorization
        )
        allegorization_economy_factor = self.InMoveFunctions.calculate_allegorization_economy_factor(
            self.Economy.allegorization
        )
        logger.debug(
            f"Коэффициент аллегоризации для торговли - "
            f"{allegorization_trade_factor}"
        )
        logger.debug(
            f"Коэффициент аллегоризации для остального - "
            f"{allegorization_economy_factor}"
        )

        # TODO: Перенести в правило
        agriculture_summarizing_factor = \
            self.InMoveFunctions.calculate_agriculture_factor(
                self.Economy.tax_income,
                self.Agriculture.agriculture_development,
                results.workers_count,
            )
        logger.debug(
            f"ОФД от РСХ - {agriculture_summarizing_factor}")

        self.Economy.trade_income *= allegorization_trade_factor
        self.Economy.branches_income *= allegorization_trade_factor

        self.Economy.tax_income *= allegorization_economy_factor
        self.Economy.tax_income += agriculture_summarizing_factor

        self.Industry.industry_income *= allegorization_economy_factor

        science_income = getattr(self.InnerPolitics, "income_from_scientific",
                                 0) or 0

        self.Economy.money_income = (
                self.Economy.tax_income
                + self.Economy.trade_income
                + self.Economy.branches_income
                + self.Industry.industry_income
                + science_income
                - total_wastes
        )

        inflation_factor = self.InMoveFunctions.calculate_inflation_factor(
            self.Economy.inflation)

        self.Economy.money_income *= inflation_factor

        # Mode-specific extra modifiers
        for m in self.Rules.money_income_extra_multipliers(self._ctx()):
            self.Economy.money_income *= m

        logger.debug(f"Итоговый доход - {self.Economy.money_income}")

    def _finalize_calculations(
            self,
            *,
            budget_before: float,
            logistic_discount: float,
            total_wastes: float,
            contentment_coefficient_2: float,
    ) -> SkipMoveReport:
        """Finalize and build a report."""
        self.Economy.prev_budget = budget_before

        budget_after_raw = budget_before + float(
            self.Economy.money_income) + float(logistic_discount)

        stability_after, boost = self._update_stability(
            self.Rules,
            contentment_coefficient_2
        )
        budget_after_boost = budget_after_raw * boost

        self.Economy.current_budget = budget_after_boost

        logger.debug(
            f"Итоговый бюджет - {self.Economy.current_budget}, стабильность - {stability_after}, буст - {boost}"
        )

        self._update_education()
        self._update_military_equipment()

        science_income = float(
            getattr(self.InnerPolitics, "income_from_scientific", 0) or 0)

        report = SkipMoveReport(
            mode=self.mode_name,
            budget_before=float(budget_before),
            logistic_wastes=float(self._calculate_logistic_wastes()),
            total_wastes=float(total_wastes),
            logistic_discount=float(logistic_discount),
            tax_income=float(self.Economy.tax_income or 0),
            trade_income=float(self.Economy.trade_income or 0),
            branches_income=float(self.Economy.branches_income or 0),
            industry_income=float(self.Industry.industry_income or 0),
            science_income=science_income,
            money_income=float(self.Economy.money_income or 0),
            budget_after_raw=float(budget_after_raw),
            stability_after=float(stability_after),
            income_boost=float(boost),
            budget_after_boost=float(budget_after_boost),
            credit_taken=False,
            credit_amount=0.0,
            budget_final=float(budget_after_boost),
        )

        return report


@dataclass(kw_only=True)
class AtteriumSkipMove(BasicSkipMove):
    """Atterium mode: same engine, different rules & formulas."""

    Economy: AtteriumEconomyStats
    Industry: AtteriumIndustrialStats
    Agriculture: AtteriumAgricultureStats
    InnerPolitics: AtteriumInnerPoliticsStats

    InMoveFunctions: AtteriumInMoveFunctions = field(
        default_factory=AtteriumInMoveFunctions)
    Rules: SkipMoveRules = field(default_factory=AtteriumSkipMoveRules)

    mode_name: str = "atterium"


@dataclass(kw_only=True)
class IsfSkipMove(BasicSkipMove):
    """ISF mode: same engine, different rules & formulas."""

    Economy: IsfEconomyStats
    Industry: IsfIndustrialStats
    Agriculture: IsfAgricultureStats
    InnerPolitics: IsfInnerPoliticsStats

    InMoveFunctions: IsfInMoveFunctions = field(
        default_factory=IsfInMoveFunctions)
    Rules: SkipMoveRules = field(default_factory=IsfSkipMoveRules)

    mode_name: str = "isf"
