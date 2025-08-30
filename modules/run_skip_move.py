from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple

from functions.atterium_in_move_functions import AtteriumInMoveFunctions
from functions.base import BaseInMoveFunctions
from functions.basic_in_move_functions import BasicInMoveFunctions
from functions.isf_in_move_functions import IsfInMoveFunctions
from stats.atterium_stats import (
    AtteriumEconomyStats,
    AtteriumIndustrialStats,
    AtteriumAgricultureStats,
    AtteriumInnerPoliticsStats
)
from stats.basic_stats import (
    EconomyStats,
    IndustrialStats,
    AgricultureStats,
    InnerPoliticsStats
)
from stats.isf_stats import (
    IsfEconomyStats,
    IsfIndustrialStats,
    IsfAgricultureStats,
    IsfInnerPoliticsStats
)
from utils.logger_manager import get_logger


logger = get_logger("Run Skip Move")


@dataclass
class LogisticParams:
    """Параметры логистики для улучшения читаемости"""
    discount: float = 0.0
    food_security_spotter: float = 0.0
    tax_income_coefficient: float = 0.0
    contentment_spotter: int = 0


@dataclass
class CalculationResults:
    """Результаты основных расчетов"""
    logistic_params: LogisticParams
    culture_coefficient: float
    contentment_coefficient_1: float
    contentment_coefficient_2: float
    expected_infrastructure_waste: float


@dataclass
class SkipMoverBase(ABC):
    """Базовый класс для пропуска хода с общей логикой"""
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats
    waste: float = 0
    InMoveFunctions: BaseInMoveFunctions = field(
        default_factory=BaseInMoveFunctions)

    @abstractmethod
    def skip_move(self):
        """Основной метод пропуска хода"""
        raise NotImplementedError()

    def _calculate_logistic_wastes(self) -> float:
        """Вычисляет логистические расходы"""
        return (self.Economy.gov_wastes[1] +
                self.InnerPolitics.provinces_count * self.InnerPolitics.provinces_waste)

    def _calculate_total_wastes(self, logistic_wastes: float) -> float:
        """Вычисляет общие расходы"""
        return (sum(self.Economy.med_wastes) + sum(self.Economy.gov_wastes) +
                sum(self.Economy.war_wastes) + sum(self.Economy.other_wastes) +
                logistic_wastes + self.waste + self.Agriculture.agriculture_wastes -
                self.Agriculture.income_from_resources)

    def _handle_negative_budget(self) -> bool:
        """Обрабатывает случай отрицательного бюджета. Возвращает False если игрок отказался от кредита"""
        if self.Economy.current_budget >= 0:
            return True

        deficit = -self.Economy.current_budget
        print(f"У меня нет денег - не хватает {deficit}")

        try:
            take_credit = bool(
                int(input("Взять кредит? 1, если да, 0 - если нет \n")))
        except (ValueError, KeyboardInterrupt):
            return False

        if not take_credit:
            return False

        try:
            final_budget = float(
                input("Введите сумму, которая в итоге будет в казне - "))
            credit_amount = deficit + final_budget
            print(f"Сумма кредита - {credit_amount}")
            self.Economy.current_budget = final_budget
            return True
        except (ValueError, KeyboardInterrupt):
            logger.error("Ошибка при вводе суммы кредита")
            return False

    def _update_stability(self, contentment_coefficient_2: float) -> Tuple[
        float, float]:
        """Обновляет экономическую стабильность и возвращает буффированную стабильность и коэффициент буста"""
        expected_size = self.InMoveFunctions.expected_state_apparatus(
            self.Economy.population_count, self.Economy.gov_wastes[2])
        logger.debug(f"Ожидаемый размер гос. аппарата - {expected_size}")

        buffed_stability = self.Economy.stability
        logger.debug(
            f"Начальная экономическая стабильность - {buffed_stability}%")

        if expected_size > self.InnerPolitics.state_apparatus_size:
            buffed_stability -= 10
            logger.debug(
                f"Размер аппарата недостаточен, стабильность снижена до {buffed_stability}%")
        elif (self.InnerPolitics.state_apparatus_efficiency > 60 and
              buffed_stability < 100):
            buffed_stability = min(buffed_stability + 5, 99)
            logger.debug(
                f"Эффективный аппарат, стабильность повышена до {buffed_stability}%")

        # Расчет буста дохода
        if (80 <= buffed_stability <= 99 and
                self.InnerPolitics.poor_level < 6 and
                self.InnerPolitics.jobless_level < 12 and
                contentment_coefficient_2 > 0.8):
            boost = self.InMoveFunctions.calculate_money_income_boost(
                buffed_stability, self.InnerPolitics.poor_level,
                self.InnerPolitics.jobless_level)
            logger.debug("Применен максимальный буст дохода")
        else:
            boost = self.InMoveFunctions.calculate_money_income_simple_boost(
                buffed_stability)
            logger.debug("Применен стандартный модификатор дохода")

        return buffed_stability, boost

    def _update_education(self):
        """Обновляет уровень образования"""
        expected_knowledge = min(
            self.InMoveFunctions.calculate_knowledge(
                self.Economy.population_count,
                self.Economy.med_wastes[0] + self.Economy.med_wastes[4]
            ), 100
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

    def _update_military_equipment(self):
        """Обновляет военное оборудование"""
        equipment_increase = (self.Economy.war_wastes[1] *
                              self.InMoveFunctions.calculate_military_equipment_coefficient(
                                  self.Industry.war_production_efficiency))
        self.InnerPolitics.military_equipment += equipment_increase


@dataclass(kw_only=True)
class BasicSkipMove(SkipMoverBase):
    """Базовая реализация пропуска хода"""
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats
    waste: int = 0
    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BasicInMoveFunctions)

    def skip_move(self):
        """Выполняет пропуск хода с базовой логикой"""
        try:
            # Основные расчеты
            logistic_wastes = self._calculate_logistic_wastes()
            results = self._perform_basic_calculations(logistic_wastes)

            # Расчеты доходов и расходов
            self._calculate_income_and_expenses(results, logistic_wastes)

            # Обработка бюджета
            if not self._handle_negative_budget():
                return

            # Обновление состояния
            self._finalize_calculations(results.logistic_params.discount,
                                        results.contentment_coefficient_2)

        except Exception as e:
            logger.error(f"Ошибка при выполнении пропуска хода: {e}")
            raise

    def _perform_basic_calculations(
            self,
            logistic_wastes: float
    ) -> CalculationResults:
        """Выполняет основные расчеты для хода"""
        logistic_params = self.calculate_logistic_based_params(logistic_wastes)

        culture_coefficient = self.InMoveFunctions.calculate_cultural_coefficient(
            self.InnerPolitics.cultural_level,
            self.InnerPolitics.egocentrism_development)

        contentment_coefficient_1, contentment_coefficient_2 = (
            self.InMoveFunctions.calculate_contentment_coefficients(
                self.InnerPolitics.contentment + logistic_params.contentment_spotter))

        expected_infrastructure_waste = (
            self.InMoveFunctions.calculate_expected_infrastructure_wastes(
                self.Economy.population_count))

        return CalculationResults(
            logistic_params=logistic_params,
            culture_coefficient=culture_coefficient,
            contentment_coefficient_1=contentment_coefficient_1,
            contentment_coefficient_2=contentment_coefficient_2,
            expected_infrastructure_waste=expected_infrastructure_waste
        )

    def _calculate_income_and_expenses(self, results: CalculationResults,
                                       logistic_wastes: float):
        """Рассчитывает все виды доходов и расходов"""
        # Расчет сельского хозяйства
        self._calculate_agriculture_stats(
            results.logistic_params.food_security_spotter)

        # Расчет базового дохода
        self._calculate_base_income(results)

        # Расчет промышленности
        self._calculate_industry_stats()

        # Расчет налогового дохода
        self._calculate_tax_income(results, logistic_wastes)

        # Расчет торгового дохода
        self._calculate_trade_income()

        # Общий расчет дохода
        self._calculate_total_income(logistic_wastes)

    def _calculate_agriculture_stats(self,
                                     food_security_spotter: float):
        """Рассчитывает статистики сельского хозяйства"""
        self.Agriculture.expected_wastes = self.InMoveFunctions.calculate_agriculture_wastes(
            self.Economy.population_count, self.Agriculture.securities,
            self.Agriculture.biome_richness,
            self.Agriculture.agriculture_development)

        self.Agriculture.agriculture_efficiency = (
            self.InMoveFunctions.calculate_agriculture_efficiency(
                self.Agriculture.securities,
                self.Agriculture.agriculture_wastes,
                self.Agriculture.expected_wastes))

        self.Agriculture.food_security = round(
            self.InMoveFunctions.calculate_food_security_spotter(
                self.Agriculture.agriculture_efficiency,
                self.Agriculture.biome_richness,
                self.Agriculture.overprotective_effects))

        self.Agriculture.food_security *= 1 - (
                self.Agriculture.agriculture_natural_deceases / 100)
        self.Agriculture.food_security *= 1 - (
                self.Agriculture.agriculture_deceases / 100)

    def _calculate_base_income(self, results: CalculationResults):
        """Рассчитывает базовый прирост населения"""
        income_multipliers = [
            self.InMoveFunctions.calculate_goods_coefficient(
                self.Industry.tvr1),

            (self.InMoveFunctions.calculate_stability_coefficient(
                self.InnerPolitics.poor_level,
                self.InnerPolitics.jobless_level,
                sum(self.Economy.med_wastes), self.Economy.population_count) *
             results.contentment_coefficient_1 *
             (0.015 * self.InnerPolitics.many_children_propoganda + 1)),

            self.InMoveFunctions.calculate_income_coefficient_based_on_agriculture(
                self.Agriculture.agriculture_efficiency,
                self.Agriculture.agriculture_development,
                results.logistic_params.food_security_spotter),

            self.InMoveFunctions.calculate_income_coefficient_based_on_social_decline(
                self.InnerPolitics.society_decline),

            self.InMoveFunctions.calculate_income_coefficient_based_on_food_diversity(
                self.Agriculture.food_diversity)
        ]

        # Применяем все множители
        for multiplier in income_multipliers:
            self.Economy.income *= multiplier

        # Обновление населения
        self.Economy.population_count *= (
            self.InMoveFunctions.calculate_population_decrement_coefficient(
                self.Economy.decrement_coefficient))

        logger.debug(f"Итоговый расчетный прирост - {self.Economy.income}")

    def _calculate_industry_stats(self):
        """Рассчитывает промышленные показатели"""
        self.Industry.consumption_of_goods = (
            self.InMoveFunctions.calculate_consumption_of_goods(
                self.Economy.population_count,
                self.Economy.trade_usage,
                self.Economy.trade_efficiency,
                self.Industry.tvr1,
                self.Industry.tvr2)[0])

        self.Industry.overproduction_coefficient += (
            self.InMoveFunctions.calculate_industry_overproduction_change(
                self.Industry.tvr1,
                self.Industry.tvr2,
                self.Industry.consumption_of_goods,
                self.Economy.trade_usage
            )
        )

        self.Industry.industry_income = self.InMoveFunctions.calculate_industry_income(
            self.Economy.gov_wastes,
            self.Industry.civil_usage,
            self.Industry.max_potential,
            self.Industry.expected_wastes
        )

    def _calculate_tax_income(
            self,
            results: CalculationResults,
            logistic_wastes: float
    ):
        """Рассчитывает налоговый доход"""
        small_enterprise_tax_spotter = (1.1 if self.Economy.gov_wastes[0] >
                                               results.expected_infrastructure_waste else 0.85)

        base_tax_income = self.InMoveFunctions.calculate_tax_income(
            self.Economy.universal_tax * results.culture_coefficient,
            (self.Economy.excise *
             self.InMoveFunctions.calculate_goods_coefficient(
                 self.Industry.tvr2)),
            self.Economy.additions,
            self.Economy.small_enterprise_tax * small_enterprise_tax_spotter,
            self.Economy.large_enterprise_tax,
            self.InnerPolitics.small_enterprise_percent,
            self.InnerPolitics.large_enterprise_count,
            self.Economy.population_count)

        # Применяем модификаторы
        modifiers = [
            results.contentment_coefficient_2,
            (1 - results.logistic_params.tax_income_coefficient),
            self.InMoveFunctions.calculate_integrity_of_faith_factor(
                self.InnerPolitics.integrity_of_faith),
            self.InMoveFunctions.calculate_income_coefficient_based_on_panic_level(
                self.InnerPolitics.panic_level),
            self.InMoveFunctions.calculate_overproduction_tax_spotter(
                self.Industry.overproduction_coefficient
            )
        ]

        self.Economy.tax_income = base_tax_income
        for modifier in modifiers:
            self.Economy.tax_income *= modifier

        logger.debug(f"Итоговый налоговый доход - {self.Economy.tax_income}")

    def _calculate_trade_income(self):
        """Рассчитывает доходы от торговли и форекс"""
        # Расчет курса валют
        self.Economy.forex = self.InMoveFunctions.calculate_forex_course(
            self.Economy.stability, self.Economy.tax_income,
            self._calculate_total_wastes(self._calculate_logistic_wastes()),
            self.Economy.current_budget, self.Economy.trade_rank,
            self.Economy.trade_efficiency,
            round(
                self.Economy.trade_usage / self.Economy.trade_potential * 100),
            self.Industry.civil_efficiency,
            self.InnerPolitics.state_apparatus_efficiency,
            self.InnerPolitics.contentment, self.InnerPolitics.poor_level,
            self.InnerPolitics.jobless_level, self.InnerPolitics.control)

        logger.debug(f"Курс валют - {self.Economy.forex}")

        # Расчет торгового дохода
        base_trade_income = self.InMoveFunctions.calculate_trade_income(
            self.Economy.trade_potential, self.Economy.trade_usage,
            self.Economy.trade_efficiency, self.Economy.trade_wastes,
            self.Economy.high_quality_percent,
            self.Economy.mid_quality_percent,
            self.Economy.low_quality_percent, self.Economy.forex,
            self.Economy.valgery
        )

        modifiers = [
            self.InMoveFunctions.calculate_overproduction_trade_income(
                self.Industry.overproduction_coefficient
            )
        ]

        self.Economy.trade_income = base_trade_income
        for modifier in modifiers:
            self.Economy.trade_income *= modifier

        logger.debug(f"Торговый доход - {self.Economy.trade_income}")

    def _calculate_total_income(self, logistic_wastes: float):
        """Рассчитывает общий доход"""
        total_wastes = self._calculate_total_wastes(logistic_wastes)
        logger.debug(f"Общие расходы - {total_wastes}")
        allegorization_trade_factor = self.InMoveFunctions.calculate_allegorization_trade_factor(
            self.Economy.allegorization
        )
        allegorization_economy_factor = self.InMoveFunctions.calculate_allegorization_economy_factor(
            self.Economy.allegorization
        )
        logger.debug(f"Коэффициент аллегоризации для торговли - "
                     f"{allegorization_trade_factor}")
        logger.debug(f"Коэффициент аллегоризации для остального - "
                     f"{allegorization_economy_factor}")

        self.Economy.trade_income *= allegorization_trade_factor
        self.Economy.branches_income *= allegorization_trade_factor

        self.Economy.tax_income *= allegorization_economy_factor
        self.Industry.industry_income *= allegorization_economy_factor

        # Суммируем все доходы
        self.Economy.money_income = (
                self.Economy.tax_income + self.Economy.trade_income +
                self.Economy.branches_income + self.Industry.industry_income +
                self.InnerPolitics.income_from_scientific - total_wastes)

        # Применяем модификаторы
        collaboration_factor = (
            self.InMoveFunctions.calculate_money_income_collaboration_factor(
                self.Agriculture.agriculture_efficiency,
                self.Industry.civil_efficiency))
        inflation_factor = self.InMoveFunctions.calculate_inflation_factor(
            self.Economy.inflation)

        self.Economy.money_income *= collaboration_factor * inflation_factor
        logger.debug(f"Итоговый доход - {self.Economy.money_income}")

    def _finalize_calculations(self, logistic_discount: float,
                               contentment_coefficient_2: float):
        """Завершает расчеты хода"""
        # Обновляем бюджет
        self.Economy.prev_budget = self.Economy.current_budget
        self.Economy.current_budget += self.Economy.money_income + logistic_discount

        # Обновляем стабильность и применяем буст
        buffed_stability, boost = self._update_stability(
            contentment_coefficient_2)
        self.Economy.current_budget *= boost

        logger.debug(f"Итоговый бюджет - {self.Economy.current_budget}, "
                     f"стабильность - {buffed_stability}, буст - {boost}")

        # Обновляем образование и военное оборудование
        self._update_education()
        self._update_military_equipment()

    def calculate_logistic_based_params(
            self,
            logistic_wastes: float
    ) -> LogisticParams:
        """Рассчитывает параметры на основе логистики"""
        params = LogisticParams()

        expected_logistic = self.InMoveFunctions.calculate_expected_logistic_wastes(
            self.Economy.gov_wastes)

        if expected_logistic <= logistic_wastes:
            params.discount = self.Economy.gov_wastes[0] * 0.1
        else:
            params.food_security_spotter = 7
            params.tax_income_coefficient = 0.1

        # Расчет влияния соли на довольство
        salt_security = self.InnerPolitics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(bonus,
                                              100 - self.InnerPolitics.contentment)

        # Расчет влияния контроля
        total_control = self.InnerPolitics.control[0] + \
                        self.InnerPolitics.control[1]
        if total_control >= 90:
            params.contentment_spotter = min(
                params.contentment_spotter + 5,
                100 - self.InnerPolitics.contentment)
            params.tax_income_coefficient -= 0.05
            params.food_security_spotter -= 4
        else:
            control_sum = self.InnerPolitics.control[2] + \
                          self.InnerPolitics.control[3]
            params.contentment_spotter -= 5
            params.tax_income_coefficient += control_sum / 400

        return params


@dataclass(kw_only=True)
class AtteriumSkipMove(BasicSkipMove):
    """Расширенная версия пропуска хода для Atterium"""
    Economy: AtteriumEconomyStats
    Industry: AtteriumIndustrialStats
    Agriculture: AtteriumAgricultureStats
    InnerPolitics: AtteriumInnerPoliticsStats
    waste: int = 0
    InMoveFunctions: AtteriumInMoveFunctions = field(
        default_factory=AtteriumInMoveFunctions)

    def _calculate_tax_income(self, results: CalculationResults,
                              logistic_wastes: float):
        """Переопределенный расчет налогового дохода для Atterium"""
        # Рассчитываем специфичные для Atterium модификаторы
        (trade_spotter_adrian, income_spotter_adrian) = (
            self.InMoveFunctions.calculate_adrian_effect_spotters(
                self.Economy.adrian_effect))

        power_formation_buffs = (
            self.InMoveFunctions.calculate_power_of_economic_formation_buffs(
                self.Economy.power_of_economic_formation))

        (trade_spotter_power, excise_spotter_power,
         business_spotter_power,
         branches_spotter_power) = power_formation_buffs

        freedom_business_spotter = (1.1 if self.Economy.gov_wastes[0] >
                                           results.expected_infrastructure_waste else 0.85)

        # Базовый расчет налогов (модифицированный для Atterium)
        base_tax_income = self.InMoveFunctions.calculate_tax_income(
            (self.Economy.universal_tax * 0.7) * results.culture_coefficient,
            (self.Economy.excise *
             self.InMoveFunctions.calculate_goods_coefficient(
                 self.Industry.tvr2) *
             excise_spotter_power),
            self.Economy.additions,
            (self.Economy.freedom_and_efficiency_of_small_business *
             freedom_business_spotter * business_spotter_power),
            ((self.Economy.investment_of_large_companies * 0.35) *
             self.InMoveFunctions.calculate_plan_efficiency_spotter(
                 self.InnerPolitics.state_apparatus_functionality)),
            self.InnerPolitics.small_enterprise_percent,
            (self.InnerPolitics.large_enterprise_count / 4
             if self.InnerPolitics.large_enterprise_count > 0 else 0),
            self.Economy.population_count)

        # Добавляем доход от плановой эффективности
        plan_efficiency_income = self.InMoveFunctions.calculate_plan_efficiency_income(
            self.Economy.plan_efficiency,
            (self.InnerPolitics.large_enterprise_count / 4
             if self.InnerPolitics.large_enterprise_count > 0 else 0))

        # Применяем все модификаторы
        modifiers = [
            results.contentment_coefficient_2,
            (1 - results.logistic_params.tax_income_coefficient),
            self.InMoveFunctions.calculate_integrity_of_faith_factor(
                self.InnerPolitics.integrity_of_faith),
            self.InMoveFunctions.calculate_income_coefficient_based_on_panic_level(
                self.InnerPolitics.panic_level),
            self.InMoveFunctions.calculate_huge_economy_buff(
                self.InnerPolitics.egocentrism_development
            ),
            income_spotter_adrian,
            self.InMoveFunctions.calculate_overproduction_tax_spotter(
                self.Industry.overproduction_coefficient
            )
        ]

        self.Economy.tax_income = (base_tax_income + plan_efficiency_income)
        for modifier in modifiers:
            self.Economy.tax_income *= modifier

        logger.debug(f"Atterium налоговый доход - {self.Economy.tax_income}")

    def _calculate_trade_income(self):
        """Переопределенный расчет торгового дохода для Atterium"""
        # Базовый расчет
        super()._calculate_trade_income()

        # Применяем специфичные для Atterium модификаторы
        adrian_modifiers = (
            self.InMoveFunctions.calculate_adrian_effect_spotters(
                self.Economy.adrian_effect
            )
        )
        trade_spotter_adrian = adrian_modifiers[0]

        power_formation_buffs = (
            self.InMoveFunctions.calculate_power_of_economic_formation_buffs(
                self.Economy.power_of_economic_formation
            )
        )
        trade_spotter_power = power_formation_buffs[0]
        branches_spotter_power = power_formation_buffs[3]

        # Модифицируем торговый доход
        self.Economy.trade_income *= trade_spotter_adrian * trade_spotter_power

        # Модифицируем доход от отраслей
        self.Economy.branches_income *= branches_spotter_power

        logger.debug(f"Atterium торговый доход - {self.Economy.trade_income}")

    def _calculate_total_income(self, logistic_wastes: float):
        """Рассчитывает общий доход"""
        total_wastes = self._calculate_total_wastes(logistic_wastes)
        logger.debug(f"Общие расходы - {total_wastes}")

        allegorization_trade_factor = self.InMoveFunctions.calculate_allegorization_trade_factor(
            self.Economy.allegorization
        )
        allegorization_economy_factor = self.InMoveFunctions.calculate_allegorization_economy_factor(
            self.Economy.allegorization
        )
        logger.debug(f"Коэффициент аллегоризации для торговли - "
                     f"{allegorization_trade_factor}")
        logger.debug(f"Коэффициент аллегоризации для остального - "
                     f"{allegorization_economy_factor}")

        self.Economy.trade_income *= allegorization_trade_factor
        self.Economy.branches_income *= allegorization_trade_factor

        self.Economy.tax_income *= allegorization_economy_factor
        self.Industry.industry_income *= allegorization_economy_factor

        # Суммируем все доходы - расходы
        self.Economy.money_income = (
                self.Economy.tax_income + self.Economy.trade_income +
                self.Economy.branches_income + self.Industry.industry_income -
                total_wastes
        )

        # Применяем модификаторы
        collaboration_factor = (
            self.InMoveFunctions.calculate_money_income_collaboration_factor(
                self.Agriculture.agriculture_efficiency,
                self.Industry.civil_efficiency))
        inflation_factor = self.InMoveFunctions.calculate_inflation_factor(
            self.Economy.inflation)

        self.Economy.money_income *= collaboration_factor * inflation_factor
        logger.debug(f"Итоговый доход - {self.Economy.money_income}")


class IsfSkipMove(BasicSkipMove):
    Economy: IsfEconomyStats
    Industry: IsfIndustrialStats
    Agriculture: IsfAgricultureStats
    InnerPolitics: IsfInnerPoliticsStats
    waste: int = 0
    InMoveFunctions: IsfInMoveFunctions = field(
        default_factory=IsfInMoveFunctions)

    def calculate_logistic_based_params(
            self,
            logistic_wastes: float
    ) -> LogisticParams:
        """Рассчитывает параметры на основе логистики"""
        params = LogisticParams()

        expected_logistic = (
            self.InMoveFunctions.calculate_expected_logistic_wastes(
                self.Economy.gov_wastes
            )
        )

        if expected_logistic <= logistic_wastes:
            params.discount = self.Economy.gov_wastes[0] * 0.1
        else:
            params.food_security_spotter = 7
            params.tax_income_coefficient = 0.1

        # Расчет влияния соли на довольство
        salt_security = self.InnerPolitics.salt_security
        if 0 <= salt_security < 50:
            params.contentment_spotter -= salt_security // 5
        elif salt_security >= 100:
            bonus = min(salt_security, 150) // 15
            params.contentment_spotter += min(
                bonus,
                100 - self.InnerPolitics.contentment
            )

        params.contentment_spotter += (
            self.InMoveFunctions.calculate_contentment_spotter_allegory(
                self.InnerPolitics.contentment,
                self.InnerPolitics.allegory_influence
            )
        )

        # Расчет влияния контроля
        total_control = self.InnerPolitics.control[0] + \
                        self.InnerPolitics.control[1]
        if total_control < 90:
            params.contentment_spotter = min(
                params.contentment_spotter + 5,
                100 - self.InnerPolitics.contentment)
            params.tax_income_coefficient -= 0.05
            params.food_security_spotter -= 4
        else:
            control_sum = self.InnerPolitics.control[2] + \
                          self.InnerPolitics.control[3]
            params.contentment_spotter -= 5
            params.tax_income_coefficient += control_sum / 400

        return params

    def _calculate_agriculture_stats(
            self,
            food_security_spotter: float
    ):
        super()._calculate_agriculture_stats(food_security_spotter)
        self.Agriculture.food_security *= 1 - (
                self.Agriculture.empire_land_unmastery / 100
        )

    def _calculate_total_income(self, logistic_wastes: float):
        super()._calculate_total_income(logistic_wastes)
        modifiers = [
            self.InMoveFunctions.calculate_money_income_allegory_factor(
                self.InnerPolitics.allegory_influence
            )
        ]

        for modifier in modifiers:
            self.Economy.money_income *= modifier
