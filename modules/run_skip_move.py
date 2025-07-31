from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple

from functions.base import BaseInMoveFunctions
from functions.basic_in_move_functions import \
    BasicInMoveFunctions
from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from utils.logger_manager import get_logger


logger = get_logger("Run Skip Move")


@dataclass
class SkipMoverBase(ABC):
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    waste: int = 0

    # Should be overwritten with needed class
    InMoveFunctions: BaseInMoveFunctions = field(
        default_factory=BaseInMoveFunctions)

    @abstractmethod
    def skip_move(self):
        raise NotImplementedError()


@dataclass(kw_only=True)
class BasicSkipMove(SkipMoverBase):
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    waste: int = 0

    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BasicInMoveFunctions)

    def skip_move(self):
        logistic_wastes = self.Economy.gov_wastes[
                              1] + self.InnerPolitics.provinces_count * self.InnerPolitics.provinces_waste

        logistic_wastes_discount, food_security_spotter, tax_income_coefficient, contentment_spotter = self.calculate_logistic_based_params(
            logistic_wastes)

        culture_coefficient = self.InMoveFunctions.calculate_cultural_coefficient(
            self.InnerPolitics.cultural_level,
            self.InnerPolitics.egocentrism_development)

        contentment_coefficient_1, contentment_coefficient_2 = self.InMoveFunctions.calculate_contentment_coefficients(
            self.InnerPolitics.contentment + contentment_spotter)
        expected_infrastructure_waste = self.InMoveFunctions.calculate_expected_infrastructure_wastes(
            self.Economy.population_count)
        small_enterprise_tax_spotter = 1.1 if self.Economy.gov_wastes[
                                                  0] > expected_infrastructure_waste else 0.85
        self.Agriculture.expected_wastes = self.InMoveFunctions.calculate_agriculture_wastes(
            self.Economy.population_count,
            self.Agriculture.securities,
            self.Agriculture.biome_richness,
            self.Agriculture.agriculture_development)
        self.Agriculture.agriculture_efficiency = self.InMoveFunctions.calculate_agriculture_efficiency(
            self.Agriculture.securities,
            self.Agriculture.agriculture_wastes,
            self.Agriculture.expected_wastes)

        self.Agriculture.food_security = round(
            self.InMoveFunctions.calculate_food_security_spotter(
                self.Agriculture.agriculture_efficiency,
                self.Agriculture.biome_richness,
                self.Agriculture.overprotective_effects))

        # Часть с приростом
        self.Economy.income *= self.InMoveFunctions.calculate_goods_coefficient(
            self.Industry.tvr1)
        self.Economy.income *= self.InMoveFunctions.calculate_stability_coefficient(
            self.InnerPolitics.poor_level,
            self.InnerPolitics.jobless_level,
            sum(self.Economy.med_wastes),
            self.Economy.population_count) * contentment_coefficient_1 * (
                                       0.012 * self.InnerPolitics.many_children_propoganda + 1)
        self.Economy.income *= self.InMoveFunctions.calculate_income_coefficient_based_on_agriculture(
            self.Agriculture.agriculture_efficiency,
            self.Agriculture.agriculture_development, food_security_spotter)
        self.Economy.income *= self.InMoveFunctions.calculate_income_coefficient_based_on_social_decline(
            self.InnerPolitics.society_decline)
        self.Economy.income *= self.InMoveFunctions.calculate_income_coefficient_based_on_food_diversity(
            self.Agriculture.food_diversity)
        logger.debug(f"Итоговый рассчитанный прирост - {self.Economy.income}")

        # Странная механика, которую надо доработать
        self.Industry.consumption_of_goods = \
            self.InMoveFunctions.calculate_consumption_of_goods(
                self.Economy.population_count, self.Economy.trade_usage,
                self.Economy.trade_efficiency, self.Industry.tvr1,
                self.Industry.tvr2)[0]
        self.Industry.overproduction_coefficient += self.InMoveFunctions.calculate_industry_overproduction_change(
            self.Industry.tvr1, self.Industry.tvr2,
            self.Industry.consumption_of_goods)

        self.Industry.industry_income = self.InMoveFunctions.calculate_industry_income(
            self.Economy.gov_wastes, self.Industry.civil_usage,
            self.Industry.max_potential,
            self.Industry.expected_wastes)

        # Считаем все расходы из всех стат
        wastes = sum(self.Economy.med_wastes) + sum(
            self.Economy.gov_wastes) + sum(
            self.Economy.war_wastes) + sum(
            self.Economy.other_wastes) + logistic_wastes + self.waste + self.Agriculture.agriculture_wastes - self.Agriculture.income_from_resources
        logger.debug(f"Общие траты - {wastes}")

        # Часть с доходом с налогов
        self.Economy.tax_income = self.InMoveFunctions.calculate_tax_income(
            self.Economy.universal_tax * culture_coefficient,
            self.Economy.excise * self.InMoveFunctions.calculate_goods_coefficient(
                self.Industry.tvr2), self.Economy.additions,
            self.Economy.small_enterprise_tax * small_enterprise_tax_spotter,
            self.Economy.large_enterprise_tax,
            self.InnerPolitics.small_enterprise_percent,
            self.InnerPolitics.large_enterprise_count,
            self.Economy.population_count) * contentment_coefficient_2 * (
                                          1 - tax_income_coefficient)
        self.Economy.tax_income *= self.InMoveFunctions.calculate_integrity_of_faith_factor(
            self.InnerPolitics.integrity_of_faith)
        self.Economy.tax_income *= self.InMoveFunctions.calculate_income_coefficient_based_on_panic_level(
            self.InnerPolitics.panic_level)
        logger.debug(
            f"Итоговый рассчитанный доход от налогов - {self.Economy.tax_income}")

        # Часть с курсом валют
        self.Economy.forex = self.InMoveFunctions.calculate_forex_course(
            self.Economy.stability, self.Economy.tax_income, wastes,
            self.Economy.current_budget,
            self.Economy.trade_rank, self.Economy.trade_efficiency,
            round(
                self.Economy.trade_usage / self.Economy.trade_potential * 100),
            self.Industry.civil_efficiency,
            self.InnerPolitics.state_apparatus_efficiency,
            self.InnerPolitics.contentment,
            self.InnerPolitics.poor_level, self.InnerPolitics.jobless_level,
            self.InnerPolitics.control)
        logger.debug(
            f"Итоговый рассчитанный курс валют - {self.Economy.forex}")

        # Часть с доходом от торговли (тут планируется очень много нового)
        self.Economy.trade_income = self.InMoveFunctions.calculate_trade_income(
            self.Economy.trade_potential, self.Economy.trade_usage,
            self.Economy.trade_efficiency, self.Economy.trade_wastes,
            self.Economy.high_quality_percent,
            self.Economy.mid_quality_percent,
            self.Economy.low_quality_percent, self.Economy.forex,
            self.Economy.valgery)
        logger.debug(
            f"Итоговый рассчитанный доход от торговли - {self.Economy.trade_income}")

        # Суммируем все в одну кучу
        self.Economy.money_income = self.Economy.tax_income + self.Economy.trade_income + self.Economy.branches_income + self.Industry.industry_income + self.InnerPolitics.income_from_scientific - wastes
        self.Economy.money_income *= self.InMoveFunctions.calculate_money_income_collaboration_factor(
            self.Agriculture.agriculture_efficiency,
            self.Industry.civil_efficiency)
        self.Economy.money_income *= self.InMoveFunctions.calculate_inflation_factor(
            self.Economy.inflation)
        logger.debug(
            f"Итоговый рассчитанный доход - {self.Economy.money_income}")

        # Косметика для корректного отображения в стате
        self.Economy.prev_budget = self.Economy.current_budget
        self.Economy.current_budget += self.Economy.money_income + logistic_wastes_discount

        # С 0 денег жить ну никак нельзя
        if self.Economy.current_budget < 0:
            print(
                f"У меня нет денег - не хватает {-self.Economy.current_budget}")
            condition = int(input("Взять кредит? 1, если да, 0 - если нет \n"))
            if not condition:
                return
            else:
                credit = float(
                    input("Введите сумму, которая в итоге будет в казне - "))
                print(
                    f"Сумма кредита - {-self.Economy.current_budget + credit}")
                self.Economy.current_budget = credit

        expected_size = self.InMoveFunctions.expected_state_apparatus(
            self.Economy.population_count, self.Economy.gov_wastes[2])
        logger.debug(f"Ожидаемый размер гос. аппарата - {expected_size}")

        buffed_stability = self.Economy.stability
        logger.debug(
            f"Начинаем сложный этап работы с экономической стабильностью, изначально - {buffed_stability}%")

        if expected_size > self.InnerPolitics.state_apparatus_size:
            buffed_stability -= 10
            logger.debug(
                f"Размер бюр. аппарата меньше, чем надо, стабильность уменьшена до {buffed_stability}%")
        elif self.InnerPolitics.state_apparatus_efficiency > 60 and buffed_stability < 100:
            buffed_stability += 5
            buffed_stability = min(buffed_stability, 99)
            logger.debug(
                f"Размер бюр. аппарата тот, что нужен, при этом он эффективен, стабильность увеличена до {buffed_stability}%, при этом включена защита от значений больше 100")

        if 80 <= buffed_stability <= 99 and self.InnerPolitics.poor_level < 6 and self.InnerPolitics.jobless_level < 12 and contentment_coefficient_2 > 0.8:
            boost = self.InMoveFunctions.calculate_money_income_boost(
                buffed_stability,
                self.InnerPolitics.poor_level,
                self.InnerPolitics.jobless_level)
            logger.debug("Попали в гигабафф дохода")
        else:
            boost = self.InMoveFunctions.calculate_money_income_simple_boost(
                buffed_stability)
            logger.debug("Попали в обычный бафф/дебафф дохода")

        self.Economy.current_budget *= boost
        logger.debug(
            f"Итоговый рассчитанный размер казны - {self.Economy.current_budget}, стабка - {buffed_stability}, полученный бафф - {boost}")

        # Считаем часть с образованностью
        expected_knowledge = min(self.InMoveFunctions.calculate_knowledge(
            self.Economy.population_count,
            self.Economy.med_wastes[0] + self.Economy.med_wastes[4]), 100)
        logger.debug(f"Ожидаемая образованность - {expected_knowledge}")
        knowledge_diff = expected_knowledge - self.InnerPolitics.education_level

        if knowledge_diff < 0:
            self.InnerPolitics.education_level = round(
                max(expected_knowledge,
                    self.InnerPolitics.education_level - abs(
                        knowledge_diff) // 8))
            logger.debug(
                f"Понижаем образованность на {abs(knowledge_diff) // 8}")
        else:
            self.InnerPolitics.education_level += abs(
                knowledge_diff) / self.InnerPolitics.education_level
            logger.debug(
                f"Понижаем образованность на {abs(knowledge_diff) / self.InnerPolitics.education_level}")

        # Связанное с военным что-то))
        self.InnerPolitics.military_equipment += self.Economy.war_wastes[
                                                     1] * self.InMoveFunctions.calculate_military_equipment_coefficient(
            self.Industry.war_production_efficiency)

    def calculate_logistic_based_params(
            self,
            logistic_wastes: float
    ) -> Tuple[float, float, float, int]:
        logistic_wastes_discount, food_security_spotter, tax_income_coefficient = 0, 0, 0
        if self.InMoveFunctions.calculate_expected_logistic_wastes(
                self.Economy.gov_wastes) <= logistic_wastes:
            logistic_wastes_discount = self.Economy.gov_wastes[0] * 0.1
        else:
            food_security_spotter = 7
            tax_income_coefficient = 0.1

        contentment_spotter = 0
        if 0 <= self.InnerPolitics.salt_security < 50:
            contentment_spotter -= self.InnerPolitics.salt_security // 5
        elif self.InnerPolitics.salt_security >= 100:
            contentment_spotter += min(self.InnerPolitics.salt_security,
                                       150) // 15
            contentment_spotter = min(contentment_spotter,
                                      100 - self.InnerPolitics.contentment)

        total_control = self.InnerPolitics.control[0] + \
                        self.InnerPolitics.control[1]
        if total_control >= 90:
            contentment_spotter = min(contentment_spotter + 5,
                                      100 - self.InnerPolitics.contentment)
            tax_income_coefficient -= 0.05
            food_security_spotter -= 4
        else:
            control_sum = self.InnerPolitics.control[2] + \
                          self.InnerPolitics.control[3]
            contentment_spotter -= 5
            tax_income_coefficient += control_sum / 400

        return (logistic_wastes_discount, food_security_spotter,
                tax_income_coefficient, contentment_spotter)
