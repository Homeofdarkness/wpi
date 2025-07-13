from dataclasses import dataclass, field
from typing import Tuple

from functions.basic_in_move_functions import \
    BasicInMoveFunctions
from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, \
    InnerPoliticsStats
from utils.logger_manager import get_logger


logger = get_logger("Run Skip Move")


@dataclass
class SkipMove:
    Economy: EconomyStats
    Industry: IndustrialStats
    Agriculture: AgricultureStats
    InnerPolitics: InnerPoliticsStats

    waste: int = 0

    InMoveFunctions: BasicInMoveFunctions = field(
        default_factory=BasicInMoveFunctions)

    @classmethod
    def skip_move(cls):
        logistic_wastes = cls.Economy.gov_wastes[
                              1] + cls.InnerPolitics.provinces_count * cls.InnerPolitics.provinces_waste

        logistic_wastes_discount, food_security_spotter, tax_income_coefficient, contentment_spotter = cls.calculate_logistic_based_params(
            logistic_wastes)

        culture_coefficient = cls.InMoveFunctions.calculate_cultural_coefficient(
            cls.InnerPolitics.cultural_level,
            cls.InnerPolitics.egocentrism_development)

        contentment_coefficient_1, contentment_coefficient_2 = cls.InMoveFunctions.calculate_contentment_coefficients(
            cls.InnerPolitics.contentment + contentment_spotter)
        expected_infrastructure_waste = cls.InMoveFunctions.calculate_expected_infrastructure_wastes(
            cls.Economy.population_count)
        small_enterprise_tax_spotter = 1.1 if cls.Economy.gov_wastes[
                                                  0] > expected_infrastructure_waste else 0.85
        cls.Agriculture.expected_wastes = cls.InMoveFunctions.calculate_agriculture_wastes(
            cls.Economy.population_count,
            cls.Agriculture.securities,
            cls.Agriculture.biome_richness,
            cls.Agriculture.agriculture_development)
        cls.Agriculture.agriculture_efficiency = cls.InMoveFunctions.calculate_agriculture_efficiency(
            cls.Agriculture.securities,
            cls.Agriculture.agriculture_wastes,
            cls.Agriculture.expected_wastes)

        cls.Agriculture.food_security = round(
            cls.InMoveFunctions.calculate_food_security_spotter(
                cls.Agriculture.agriculture_efficiency,
                cls.Agriculture.biome_richness,
                cls.Agriculture.overprotective_effects))

        # Часть с приростом
        cls.Economy.income *= cls.InMoveFunctions.calculate_goods_coefficient(
            cls.Industry.tvr1)
        cls.Economy.income *= cls.InMoveFunctions.calculate_stability_coefficient(
            cls.InnerPolitics.poor_level,
            cls.InnerPolitics.jobless_level,
            sum(cls.Economy.med_wastes),
            cls.Economy.population_count) * contentment_coefficient_1 * (
                                      0.012 * cls.InnerPolitics.many_children_propoganda + 1)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_agriculture(
            cls.Agriculture.agriculture_efficiency,
            cls.Agriculture.agriculture_development, food_security_spotter)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_social_decline(
            cls.InnerPolitics.society_decline)
        cls.Economy.income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_food_diversity(
            cls.Agriculture.food_diversity)
        logger.debug(f"Итоговый рассчитанный прирост - {cls.Economy.income}")

        # Странная механика, которую надо доработать
        cls.Industry.consumption_of_goods = \
            cls.InMoveFunctions.calculate_consumption_of_goods(
                cls.Economy.population_count, cls.Economy.trade_usage,
                cls.Economy.trade_efficiency, cls.Industry.tvr1,
                cls.Industry.tvr2)[0]
        cls.Industry.overproduction_coefficient += cls.InMoveFunctions.calculate_industry_overproduction_change(
            cls.Industry.tvr1, cls.Industry.tvr2,
            cls.Industry.consumption_of_goods)

        cls.Industry.industry_income = cls.InMoveFunctions.calculate_industry_income(
            cls.Economy.gov_wastes, cls.Industry.civil_usage,
            cls.Industry.max_potential,
            cls.Industry.expected_wastes)

        # Считаем все расходы из всех стат
        wastes = sum(cls.Economy.med_wastes) + sum(
            cls.Economy.gov_wastes) + sum(
            cls.Economy.war_wastes) + sum(
            cls.Economy.other_wastes) + logistic_wastes + cls.waste + cls.Agriculture.agriculture_wastes - cls.Agriculture.income_from_resources
        logger.debug(f"Общие траты - {wastes}")

        # Часть с доходом с налогов
        cls.Economy.tax_income = cls.InMoveFunctions.calculate_tax_income(
            cls.Economy.universal_tax * culture_coefficient,
            cls.Economy.excise * cls.InMoveFunctions.calculate_goods_coefficient(
                cls.Industry.tvr2), cls.Economy.additions,
            cls.Economy.small_enterprise_tax * small_enterprise_tax_spotter,
            cls.Economy.large_enterprise_tax,
            cls.InnerPolitics.small_enterprise_percent,
            cls.InnerPolitics.large_enterprise_count,
            cls.Economy.population_count) * contentment_coefficient_2 * (
                                         1 - tax_income_coefficient)
        cls.Economy.tax_income *= cls.InMoveFunctions.calculate_integrity_of_faith_factor(
            cls.InnerPolitics.integrity_of_faith)
        cls.Economy.tax_income *= cls.InMoveFunctions.calculate_income_coefficient_based_on_panic_level(
            cls.InnerPolitics.panic_level)
        logger.debug(
            f"Итоговый рассчитанный доход от налогов - {cls.Economy.tax_income}")

        # Часть с курсом валют
        cls.Economy.forex = cls.InMoveFunctions.calculate_forex_course(
            cls.Economy.stability, cls.Economy.tax_income, wastes,
            cls.Economy.current_budget,
            cls.Economy.trade_rank, cls.Economy.trade_efficiency,
            round(
                cls.Economy.trade_usage / cls.Economy.trade_potential * 100),
            cls.Industry.civil_efficiency,
            cls.InnerPolitics.state_apparatus_efficiency,
            cls.InnerPolitics.contentment,
            cls.InnerPolitics.poor_level, cls.InnerPolitics.jobless_level,
            cls.InnerPolitics.control)
        logger.debug(f"Итоговый рассчитанный курс валют - {cls.Economy.forex}")

        # Часть с доходом от торговли (тут планируется очень много нового)
        cls.Economy.trade_income = cls.InMoveFunctions.calculate_trade_income(
            cls.Economy.trade_potential, cls.Economy.trade_usage,
            cls.Economy.trade_efficiency, cls.Economy.trade_wastes,
            cls.Economy.high_quality_percent,
            cls.Economy.mid_quality_percent,
            cls.Economy.low_quality_percent, cls.Economy.forex,
            cls.Economy.valgery)
        logger.debug(
            f"Итоговый рассчитанный доход от торговли - {cls.Economy.trade_income}")

        # Суммируем все в одну кучу
        cls.Economy.money_income = cls.Economy.tax_income + cls.Economy.trade_income + cls.Economy.branches_income + cls.Industry.industry_income + cls.InnerPolitics.income_from_scientific - wastes
        cls.Economy.money_income *= cls.InMoveFunctions.calculate_money_income_collaboration_factor(
            cls.Agriculture.agriculture_efficiency,
            cls.Industry.civil_efficiency)
        cls.Economy.money_income *= cls.InMoveFunctions.calculate_inflation_factor(
            cls.Economy.inflation)
        logger.debug(
            f"Итоговый рассчитанный доход - {cls.Economy.money_income}")

        # Косметика для корректного отображения в стате
        cls.Economy.prev_budget = cls.Economy.current_budget
        cls.Economy.current_budget += cls.Economy.money_income + logistic_wastes_discount

        # С 0 денег жить ну никак нельзя
        if cls.Economy.current_budget < 0:
            print(
                f"У меня нет денег - не хватает {-cls.Economy.current_budget}")
            condition = int(input("Взять кредит? 1, если да, 0 - если нет \n"))
            if not condition:
                return
            else:
                credit = float(
                    input("Введите сумму, которая в итоге будет в казне - "))
                print(
                    f"Сумма кредита - {-cls.Economy.current_budget + credit}")
                cls.Economy.current_budget = credit

        expected_size = cls.InMoveFunctions.expected_state_apparatus(
            cls.Economy.population_count, cls.Economy.gov_wastes[2])
        logger.debug(f"Ожидаемый размер гос. аппарата - {expected_size}")

        buffed_stability = cls.Economy.stability
        logger.debug(
            f"Начинаем сложный этап работы с экономической стабильностью, изначально - {buffed_stability}%")

        if expected_size > cls.InnerPolitics.state_apparatus_size:
            buffed_stability -= 10
            logger.debug(
                f"Размер бюр. аппарата меньше, чем надо, стабильность уменьшена до {buffed_stability}%")
        elif cls.InnerPolitics.state_apparatus_efficiency > 60 and buffed_stability < 100:
            buffed_stability += 5
            buffed_stability = min(buffed_stability, 99)
            logger.debug(
                f"Размер бюр. аппарата тот, что нужен, при этом он эффективен, стабильность увеличена до {buffed_stability}%, при этом включена защита от значений больше 100")

        if 80 <= buffed_stability <= 99 and cls.InnerPolitics.poor_level < 6 and cls.InnerPolitics.jobless_level < 12 and contentment_coefficient_2 > 0.8:
            boost = cls.InMoveFunctions.calculate_money_income_boost(
                buffed_stability,
                cls.InnerPolitics.poor_level,
                cls.InnerPolitics.jobless_level)
            logger.debug("Попали в гигабафф дохода")
        else:
            boost = cls.InMoveFunctions.calculate_money_income_simple_boost(
                buffed_stability)
            logger.debug("Попали в обычный бафф/дебафф дохода")

        cls.Economy.current_budget *= boost
        logger.debug(
            f"Итоговый рассчитанный размер казны - {cls.Economy.current_budget}, стабка - {buffed_stability}, полученный бафф - {boost}")

        # Считаем часть с образованностью
        expected_knowledge = min(cls.InMoveFunctions.calculate_knowledge(
            cls.Economy.population_count,
            cls.Economy.med_wastes[0] + cls.Economy.med_wastes[4]), 100)
        logger.debug(f"Ожидаемая образованность - {expected_knowledge}")
        knowledge_diff = expected_knowledge - cls.InnerPolitics.education_level

        if knowledge_diff < 0:
            cls.InnerPolitics.education_level = round(
                max(expected_knowledge,
                    cls.InnerPolitics.education_level - abs(
                        knowledge_diff) // 8))
            logger.debug(
                f"Понижаем образованность на {abs(knowledge_diff) // 8}")
        else:
            cls.InnerPolitics.education_level += abs(
                knowledge_diff) / cls.InnerPolitics.education_level
            logger.debug(
                f"Понижаем образованность на {abs(knowledge_diff) / cls.InnerPolitics.education_level}")

        # Связанное с военным что-то))
        cls.InnerPolitics.military_equipment += cls.Economy.war_wastes[
                                                    1] * cls.InMoveFunctions.calculate_military_equipment_coefficient(
            cls.Industry.war_production_efficiency)

    @classmethod
    def calculate_logistic_based_params(cls, logistic_wastes: float) -> Tuple[
        float, float, float, int]:
        logistic_wastes_discount, food_security_spotter, tax_income_coefficient = 0, 0, 0
        if cls.InMoveFunctions.calculate_expected_logistic_wastes(
                cls.Economy.gov_wastes) <= logistic_wastes:
            logistic_wastes_discount = cls.Economy.gov_wastes[0] * 0.1
        else:
            food_security_spotter = 7
            tax_income_coefficient = 0.1

        contentment_spotter = 0
        if 0 <= cls.InnerPolitics.salt_security < 50:
            contentment_spotter -= cls.InnerPolitics.salt_security // 5
        elif cls.InnerPolitics.salt_security >= 100:
            contentment_spotter += min(cls.InnerPolitics.salt_security,
                                       150) // 15
            contentment_spotter = min(contentment_spotter,
                                      100 - cls.InnerPolitics.contentment)

        total_control = cls.InnerPolitics.control[0] + \
                        cls.InnerPolitics.control[1]
        if total_control >= 90:
            contentment_spotter = min(contentment_spotter + 5,
                                      100 - cls.InnerPolitics.contentment)
            tax_income_coefficient -= 0.05
            food_security_spotter -= 4
        else:
            control_sum = cls.InnerPolitics.control[2] + \
                          cls.InnerPolitics.control[3]
            contentment_spotter -= 5
            tax_income_coefficient += control_sum / 400

        return logistic_wastes_discount, food_security_spotter, tax_income_coefficient, contentment_spotter
