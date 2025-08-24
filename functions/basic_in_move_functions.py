import random
from typing import List, Tuple

from functions.base import BaseInMoveFunctions
from functions.inbuilt import InbuiltFunctions


class BasicInMoveFunctions(BaseInMoveFunctions):

    @staticmethod
    def calculate_expected_logistic_wastes(
            government_wastes: List[float]) -> float:
        """Считает ожидаемые траты на логистику"""
        return sum(government_wastes) * 0.2

    @staticmethod
    def calculate_cultural_coefficient(cultural_level: int,
                                       egocentrism_development: float) -> float:
        return max(0.0, 0.025 * cultural_level - 0.105 + (
                egocentrism_development / 100))

    @staticmethod
    def calculate_contentment_coefficients(contentment: int) -> Tuple[
        float, float]:
        """Считает 2 коэффициента в зависимости от довольства"""
        return 0.004 * contentment + 0.754, 0.005 * contentment + 0.528

    @staticmethod
    def calculate_expected_infrastructure_wastes(
            population_count: int) -> float:
        """Считает ожидаемые траты на инфраструктуру"""
        return (population_count // 10000) * 0.34

    @staticmethod
    def calculate_agriculture_base_wastes(biome_richness: float,
                                          agriculture_development: float,
                                          C=500, K=7) -> float:
        """Рассчитывает базовый коэффициент затрат на сельское хозяйство."""
        biome_factor = max(0.05,
                           (100 - biome_richness) / (110 - biome_richness))
        development_factor = max(0.1, (100 - agriculture_development) / (
                110 - agriculture_development))

        base_cost = C * (biome_factor + development_factor) * K
        return max(base_cost / 1000, 1)

    @classmethod
    def calculate_agriculture_wastes(cls, population_count: int,
                                     securities: List[float],
                                     biome_richness: float,
                                     agriculture_development: float) -> float:
        """Считает ожидаемые траты на СХ"""
        base_cost = cls.calculate_agriculture_base_wastes(biome_richness,
                                                          agriculture_development)
        influence_factor = sum(
            securities) / 100  # Преобразуем проценты в коэффициент
        expenses = (population_count / 250000) * influence_factor * base_cost
        return expenses

    @staticmethod
    def calculate_agriculture_efficiency(securities: List[float],
                                         wastes: float,
                                         expected_wastes: float) -> float:
        """Считает эффективность СХ"""
        if expected_wastes <= 0:
            return 0

        coefficient = wastes / expected_wastes
        return (sum(securities) / len(securities)) * min(1.0, coefficient)

    @staticmethod
    def calculate_food_security_spotter(agriculture_efficiency: float,
                                        biome_richness: float,
                                        overproduction_effects: int) -> float:
        """Считает отклонение обеспеченности едой"""
        stock = 0 if agriculture_efficiency < 75 else overproduction_effects * 6
        stock *= (1 + (biome_richness / 1000))
        food_security = round((InbuiltFunctions.parabola(
            agriculture_efficiency / 10, 2, 4, 10) + stock))

        return food_security

    @staticmethod
    def calculate_goods_coefficient(goods_count: int) -> float:
        """Считает коэффициент в зависимости от достатка товаров"""
        if goods_count == 100:
            return 1.1
        return 0.004 * goods_count + 0.66

    @staticmethod
    def calculate_stability_coefficient(poor_level: float,
                                        jobless_level: float, med_waste: float,
                                        population: int) -> float:
        """Расчет коэффициента стабильности с учетом затрат на здравоохранение на 1000 человек"""

        if population <= 0:
            raise ValueError(
                "Численность населения должна быть положительным числом.")

        # Траты на медицину в пересчете на 1000 человек
        med_waste_per_1000 = (med_waste / population) * 1000000

        stability_ranges = [
            (3, 80, 1.1, 1.1),
            (3, 70, 0.95, 1.00),
            (4, 45, 0.92, 0.94),
            (6, 40, 0.88, 0.91),
            (8, 30, 0.80, 0.87),
            (10, 20, 0.72, 0.79),
            (13, 10, 0.60, 0.71),
            (float('inf'), 5, 0.1, 0.2),
        ]

        for max_jobless, min_waste, min_val, max_val in stability_ranges:
            if med_waste_per_1000 >= min_waste and (
                    jobless_level <= max_jobless or med_waste_per_1000 >= min_waste or poor_level <= max_jobless * 1.3):
                return round(random.uniform(min_val, max_val), 3)

        return round(random.uniform(0.4, 0.56),
                     3) if poor_level < 56 or med_waste < 36 else 0.01

    @staticmethod
    def calculate_income_coefficient_based_on_agriculture(
            agriculture_efficiency: float,
            agriculture_development: float,
            food_security_spotter: float) -> float:
        """Считает (де)бафф прироста в зависимости от СХ"""
        return ((((2 * agriculture_development * agriculture_efficiency) /
                  (
                          agriculture_development + agriculture_efficiency)) - food_security_spotter) ** 0.5) / 8

    @staticmethod
    def calculate_income_coefficient_based_on_social_decline(
            social_decline: float) -> float:
        """Считает (де)бафф прироста в зависимости от упадка общества"""
        return 1 - (social_decline / 100)

    @staticmethod
    def calculate_income_coefficient_based_on_panic_level(
            panic_level: float) -> float:
        return 1 - (panic_level / 100)

    @staticmethod
    def calculate_income_coefficient_based_on_food_diversity(
            food_diversity: float) -> float:
        """Любопытная формула, возможно на подумать"""
        return InbuiltFunctions.gaussian_kernel(-food_diversity / 10) * (
                1.9 / 0.4)

    @staticmethod
    def calculate_population_decrement_coefficient(
            decrement_coefficient: int) -> float:
        """Считает УНЧС"""
        return -0.01 * decrement_coefficient + 1

    @staticmethod
    def calculate_industry_income(gov_wastes: List[float], civil_usage: float,
                                  max_potential: float,
                                  expected_wastes: float) -> float:
        """Считает ПСС"""
        average_gov_wastes = sum(gov_wastes) / len(gov_wastes)
        adjusted_wastes = max(0.0, average_gov_wastes * 0.3 - expected_wastes)

        return adjusted_wastes * (max_potential / civil_usage)

    @staticmethod
    def calculate_tax_income(universal_tax: float, excise: float,
                             additions: float,
                             small_enterprise_tax: float,
                             large_enterprise_tax: float,
                             small_enterprise_percent: float,
                             large_enterprise_count: float,
                             population_count: int) -> float:
        """Считает доход с налогов (Legacy - возможно надо будет изменить)"""
        universal_tax_income = 1.9882 * (universal_tax / (
                (8 + universal_tax) * 10)) * population_count / 1000  # УН
        excise_income = excise / (excise + 100) * 2000  # Акцизы
        coefficient = population_count * small_enterprise_percent / 1000 - population_count * small_enterprise_percent / 1000 * 0.4
        small_enterprise_tax_income = small_enterprise_tax * coefficient / 3000  # Налог на мелкое предпринимательство
        large_enterprise_tax_income = (
                                              large_enterprise_tax / 10) * large_enterprise_count

        return universal_tax_income + excise_income + small_enterprise_tax_income + large_enterprise_tax_income + additions

    @staticmethod
    def calculate_integrity_of_faith_factor(integrity_of_faith: int) -> float:
        """Считает фактор целостности веры"""
        return 1 + (integrity_of_faith / 5000)

    @staticmethod
    def calculate_forex_course(stability: int, income: float, wastes: float,
                               budget: float,
                               trade_rank: int, trade_efficiency: float,
                               trade_overload: float,
                               industry_efficiency: float,
                               state_apparatus_efficiency: int,
                               contentment: int, poor_level: float,
                               jobless_level: float,
                               control_data: list) -> float:
        """Считает курс валют (Legacy - возможно надо будет иземенить)"""
        control = control_data[0] + control_data[1] - control_data[2] - \
                  control_data[3]
        weights = [-0.0033199, -0.00146846, 0.00220264, -0.00107506,
                   -0.00397517, 0.00255309, 0.00551992, 0.00351142,
                   0.00120634, 0.00119143, -0.00035796, -0.00049678,
                   -0.00304799]
        bias = 0.7665364725212972

        result = stability * weights[0] + income * weights[1] + wastes * \
                 weights[2] + budget * weights[3] + \
                 trade_rank * weights[4] + trade_efficiency * weights[
                     5] + trade_overload * weights[
                     6] + industry_efficiency * weights[7] + \
                 state_apparatus_efficiency * weights[8] + contentment * \
                 weights[9] + poor_level * weights[
                     10] + jobless_level * weights[11] + control * weights[
                     12] + bias

        return max(result, 1)

    @staticmethod
    def calculate_trade_income(trade_potential: float, trade_usage: int,
                               trade_efficiency: float, trade_wastes: float,
                               high_quality_percent: float,
                               mid_quality_percent: float,
                               low_quality_percent: float,
                               forex: float, valgery: float) -> float:
        """Расчет торгового дохода"""

        quality_factor = (
                2.6 * high_quality_percent +
                1.8 * mid_quality_percent +
                low_quality_percent
        ) if trade_usage <= trade_potential else (
                2.2 * high_quality_percent +
                1.5 * mid_quality_percent +
                0.7 * low_quality_percent
        )

        efficiency_factor = (
                trade_efficiency / 100) if trade_usage <= trade_potential else (
                trade_efficiency / 150)
        base_income = (
                          trade_usage / 38 if trade_usage <= trade_potential else trade_usage / 58) + quality_factor * efficiency_factor - trade_wastes

        if trade_usage > trade_potential:
            base_income *= (valgery / 100) + (1 / forex) * (
                    1 - (valgery / 100))

        return base_income

    @staticmethod
    def calculate_money_income_collaboration_factor(
            agriculture_efficiency: float, civil_efficiency: float) -> float:
        """Считает вклад СХ и промышленности в доход"""
        return 1 + ((agriculture_efficiency / 1000) + (
                civil_efficiency / 1000))

    @staticmethod
    def calculate_inflation_factor(inflation: float) -> float:
        """Считает инфляцию"""
        return 1 - (inflation / 100)

    @staticmethod
    def expected_state_apparatus(population_count: int,
                                 apparatus_wastes: float) -> int:
        """Считает размер аппарата"""
        n = population_count // 1000000
        expected_value = apparatus_wastes * n / 100

        return round(
            InbuiltFunctions.sigmoid(expected_value * 1000 // 13) * 100)

    @staticmethod
    def calculate_money_income_boost(stability: int, poor_level: float,
                                     jobless_level: float) -> float:
        """Считает буст дохода, если все очень круто (Legacy - но хорошее)"""
        if stability < 80:
            weight_80_90 = 0
        elif stability > 90:
            weight_80_90 = 1
        else:
            weight_80_90 = (stability - 80) / 10

        if stability <= 90:
            weight_above_90 = 0
        elif stability > 100:
            weight_above_90 = 1
        else:
            weight_above_90 = (stability - 90) / 10

        poor_jobless_condition = poor_level < 3 and jobless_level < 10
        poor_jobless_weight = 1 if poor_jobless_condition else 0

        value_80_90 = 1.5 * poor_jobless_weight + 1.17 * (
                1 - poor_jobless_weight)
        value_above_90 = 1.7 * (1 - int(
            poor_level > 0 and jobless_level > 0)) + 1.18 * int(
            poor_level > 0 and jobless_level > 0)

        return (
                1 - weight_80_90 - weight_above_90) + weight_80_90 * value_80_90 + weight_above_90 * value_above_90

    @staticmethod
    def calculate_money_income_simple_boost(stability: int) -> float:
        """Возвращает коэффициент в зависимотси от экономической стабильности (Legacy - но хорошее)"""
        if stability < 20 or stability >= 100:
            return 0.5
        return 0.008 * stability + 0.493

    @staticmethod
    def apply_corruption(corruption_level: int) -> float:
        """Возвращает коэффициент влияния коррупции"""
        return -0.131 * corruption_level + 1.077

    @classmethod
    def calculate_knowledge(cls, population_count: int,
                            knowledge_wastes: float) -> float:
        """Предсказывает образованность"""
        expected_wastes = population_count / 28000
        constant = (knowledge_wastes / population_count) * 1e4
        minimal_knowledge = round((knowledge_wastes / population_count) * (
            1e6 if population_count > 1e6 else 1e5))

        if expected_wastes >= knowledge_wastes:
            return InbuiltFunctions.tanh(constant) * 120 + minimal_knowledge

        return InbuiltFunctions.sigmoid(constant) * 100 + minimal_knowledge

    @staticmethod
    def calculate_military_equipment_coefficient(
            war_efficiency: float) -> float:
        """Считает повышение ЭВО"""
        return war_efficiency / 50

    @staticmethod
    def calculate_consumption_of_goods(population_count: int, trade_usage: int,
                                       trade_efficiency: float, tvr1: float,
                                       tvr2: float,
                                       base_multiplier: float = 12.0) -> Tuple[
        float, float]:
        """Считает потребление товаров (ТЖН и ТНП)"""

        # Расчет напряженности снабжения (0-100)
        total_goods = tvr1 + tvr2
        goods_per_capita = total_goods / max(1, population_count) * 1000

        tension_raw = (population_count / 1000) / max(1,
                                                      trade_usage) * base_multiplier - goods_per_capita
        tension = min(100.0, max(0.0, tension_raw))

        # Базовое потребление
        base_coefficient = 45.0
        base_consumption = population_count * (base_coefficient / 1000)

        # Модификатор от напряженности (увеличивает потребление при высокой напряженности)
        tension_modifier = 1.0 + (tension / 200.0)

        # Итоговое потребление
        consumption = base_consumption * trade_efficiency * tension_modifier

        return round(consumption / 1000000, 2), round(tension, 1)

    @staticmethod
    def calculate_industry_overproduction_change(tvr1: int, tvr2: int,
                                                 consumption: float) -> float:
        sign = 1 if tvr1 + tvr2 > consumption else -1

        return sign * 0.5

    @staticmethod
    def calculate_allegorization_trade_factor(
            allegorization_percent: float
    ) -> float:
        """Считает бафф торговли относительно процента аллегоризации"""
        if not 0 <= allegorization_percent <= 100:
            raise ValueError(
                f"Процент должен быть в диапазоне [0, 100], "
                f"получен: {allegorization_percent}")

        # Правила: (условие, функция_расчета)
        rules = [
            (lambda x: x == 0, lambda x: 0.97),
            (lambda x: x < 21, lambda x: 1 + x / 200),
            (lambda x: x < 81, lambda x: 1 + (x - 20) / 100),
            (lambda x: True, lambda x: 1 + (x - 20) / 75)
            # Для остальных случаев
        ]

        for condition, calculation in rules:
            if condition(allegorization_percent):
                return calculation(allegorization_percent)

    @staticmethod
    def calculate_allegorization_economy_factor(
            allegorization_percent: float
    ) -> float:
        """Считает дебафф экономики относительно процента аллегоризации"""
        if not 0 <= allegorization_percent <= 100:
            raise ValueError(
                f"Процент должен быть в диапазоне [0, 100], "
                f"получен: {allegorization_percent}")

        rules = [
            (lambda x: x == 0, lambda x: 1.03),
            (lambda x: x < 21, lambda x: 1),
            (lambda x: x < 81, lambda x: 1 - (1.8 + (x - 21) * 0.1) / 100),
            (lambda x: True, lambda x: 1 + (x - 20) / 500)
            # Для остальных случаев
        ]

        for condition, calculation in rules:
            if condition(allegorization_percent):
                return calculation(allegorization_percent)
