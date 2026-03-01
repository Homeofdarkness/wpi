import math
import random
from typing import List, Tuple

import numpy as np

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
    def calculate_workers_count(
            population_count: int,
            workers_percent: float,
            workers_redistribution: int
    ) -> int:
        """Считает количество рабочих"""
        workers_calculation_rules = [
            {
                "gt": 0,
                "le": 1_000_000,
                "count_per_percent": 5000
            },
            {
                "gt": 1_000_000,
                "le": 10_000_000,
                "count_per_percent": 100_000
            },
            {
                "gt": 10_000_000,
                "le": 50_000_000,
                "count_per_percent": 275_000
            },
            {
                "gt": 50_000_000,
                "le": 125_000_000,
                "count_per_percent": 500_000
            },
            {
                "gt": 125_000_000,
                "le": 200_000_000,
                "count_per_percent": 1_000_000
            },
            {
                "gt": 200_000_000,
                "le": 400_000_000,
                "count_per_percent": 2_000_000
            },
            {
                "gt": 400_000_000,
                "le": 500_000_000,
                "count_per_percent": 2_500_000
            },
            {
                "gt": 500_000_000,
                "le": float('inf'),
                "count_per_percent": 5_000_000
            }
        ]

        for rule in workers_calculation_rules:
            if rule["gt"] < population_count <= rule["le"]:
                count_per_percent = rule["count_per_percent"] * (
                        1 - workers_redistribution / 10)
                return round(count_per_percent * workers_percent)

        return 0

    @staticmethod
    def calculate_additional_wastes(
            security_percent: float
    ) -> float:
        """Считает стоимость каждого рабочего"""
        # Прогнать в линейную регрессию
        calculation_rules = [
            {
                "gt": 0,
                "le": 20,
                "count_per_worker": 0.5
            },
            {
                "gt": 20,
                "le": 40,
                "count_per_worker": 0.75
            },
            {
                "gt": 40,
                "le": 60,
                "count_per_worker": 1
            },
            {
                "gt": 60,
                "le": 80,
                "count_per_worker": 1.5
            },
            {
                "gt": 80,
                "le": 100,
                "count_per_worker": 2
            },
            {
                "gt": 100,
                "le": float('inf'),
                "count_per_worker": 3
            },
        ]

        for rule in calculation_rules:
            if rule["gt"] < security_percent <= rule["le"]:
                return rule["count_per_worker"]

        return 3

    @classmethod
    def calculate_agriculture_wastes(
            cls,
            workers_count: int,
            securities: List[float],
            husbandry: float,
            livestock: float,
            others: float
    ) -> float:
        """Считает ожидаемые траты на СХ"""
        (
            workers_percent,
            technology_percent,
            fertilizer_percent,
            tool_percent
        ) = securities

        workers_wastes = workers_count * (
                cls.calculate_additional_wastes(technology_percent)
                + cls.calculate_additional_wastes(fertilizer_percent)
                + cls.calculate_additional_wastes(tool_percent)
        ) / 10000

        workers_wastes *= (1 + husbandry * 0.0028)
        workers_wastes *= (1 + livestock * 0.005)
        workers_wastes *= (1 + others * 0.0035)

        return workers_wastes

    @staticmethod
    def calculate_agriculture_development(
            securities: List[float],
            workers_count: float,
            biome_richness: float,
            food_diversity: float,
            husbandry: float,
            livestock: float,
            others: float,
    ) -> float:
        pure_coefficient = InbuiltFunctions.tanh(
            (securities[1] + securities[2] + securities[3]) / 100
        )
        interconnection_percent = workers_count * (
                securities[1] + securities[2] + securities[3]) / 3

        standard_deviation = (
            (
                    abs(husbandry - 40)
                    + abs(livestock - 40)
                    + abs(others - 20)
            )
        )
        if standard_deviation > 0:
            standard_deviation /= 3

        return (((
                         interconnection_percent / biome_richness) + food_diversity) / standard_deviation) * pure_coefficient * 10

    @staticmethod
    def calculate_agriculture_efficiency(
            securities: List[float],
            wastes: float,
            expected_wastes: float
    ) -> float:
        """Считает эффективность СХ"""
        if expected_wastes <= 0:
            return 0

        coefficient = wastes / expected_wastes
        return (sum(securities) / len(securities)) * min(1.0, coefficient)

    @staticmethod
    def calculate_food_food_diversity(
            husbandry: float,
            livestock: float,
            others: float,
            biome_richness: float
    ) -> float:
        """Считает пищевое разнообразие"""
        base = biome_richness

        standard_deviation = (
            (
                    abs(husbandry - 40)
                    + abs(livestock - 40)
                    + abs(others - 20)
            )
        )
        if standard_deviation > 0:
            standard_deviation /= 3

        return base - standard_deviation

    @classmethod
    def calculate_food_income(
            cls,
            workers_count: int,
            securities: List[float],
            overprotective_effects: float,
            agriculture_deceases: float,
            agriculture_natural_deceases: float,
    ) -> float:
        """Считает обеспеченность едой"""
        (
            workers_percent,
            technology_percent,
            fertilizer_percent,
            tool_percent
        ) = securities
        base = 0.25
        costs_per_workers = (
                cls.calculate_additional_wastes(technology_percent)
                + cls.calculate_additional_wastes(fertilizer_percent)
                + cls.calculate_additional_wastes(tool_percent)
        )
        costs_per_workers -= base * 3
        coefficient = (costs_per_workers / base) * 1.75

        food_income = (workers_count / 10000) * (coefficient + 10)

        food_income *= (1 + (overprotective_effects / 100))
        food_income *= (1 - (agriculture_deceases / 100))
        food_income *= (1 - (agriculture_natural_deceases / 100))

        return food_income

    @staticmethod
    def calculate_food_consumption(
            population_count: int,
            consumption_factor: float,
    ) -> float:
        return (population_count / 10000) * (2.5 + (0.1 * consumption_factor))

    @classmethod
    def calculate_food_security(
            cls,
            food_income: float,
            food_consumption: float,
    ) -> float:
        """Считает обеспеченность едой"""
        return food_income - food_consumption

    @staticmethod
    def calculate_food_supplies(
            current_food_supplies: float,
            food_security: float,
            overstock_percent: float,
            storages_upkeep: float
    ) -> float:
        food_supplies = current_food_supplies
        available_storage = storages_upkeep * 39
        food_supplies += max(
            food_security - 400,
            food_security * overstock_percent
        )

        return min(food_supplies, available_storage)

    @staticmethod
    def calculate_goods_coefficient(goods_count: int) -> float:
        """Считает коэффициент в зависимости от достатка товаров"""
        if goods_count >= 100:
            return 1.1
        return 0.004 * goods_count + 0.66

    @staticmethod
    def calculate_stability_coefficient(
            poor_level: float,
            jobless_level: float,
            med_waste: float,
            population: int
    ) -> float:
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
            food_security: float
    ) -> float:
        """Считает (де)бафф прироста в зависимости от СХ"""
        if food_security <= 100:
            return 0.45 + 0.55 * (food_security / 100) ** 2
        elif food_security <= 150:
            return 1 + 0.15 * ((food_security - 100) / 50) ** 2
        else:
            return 1.15

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
            decrement_coefficient: int
    ) -> float:
        """Считает УНЧС"""
        return -0.01 * decrement_coefficient + 1

    @staticmethod
    def calculate_population_underfeed(
            population_count: int,
            food_security: float,
            biome_richness: float,
            death_probability: float = 0.36
    ) -> int:
        shortage = max(0.0, -food_security)
        if shortage <= 0:
            return 0

        total_need = (population_count / 10000.0) * 2.5
        shortage_fraction = min(1.0, shortage / total_need)

        at_risk = int(math.ceil(population_count * shortage_fraction))

        # каждые 10% -> минус 2% от вероятности (относительно)
        reduction = 0.02 * (biome_richness / 10.0)
        p_eff = float(
            np.clip(death_probability * (1.0 - reduction), 0.12, 0.36)
        )

        rng = np.random.default_rng()
        deaths = int(rng.binomial(at_risk, p_eff))

        # biome: каждые 10% -> минус 5% от смертей
        reduction = 0.05 * (biome_richness / 10.0)
        return max(0, round(deaths * (1.0 - reduction)))

    @staticmethod
    def calculate_industry_income(
            gov_wastes: List[float],
            civil_usage: float,
            max_potential: float,
            expected_wastes: float
    ) -> float:
        """Считает ПСС"""
        average_gov_wastes = sum(gov_wastes) / len(gov_wastes)
        adjusted_wastes = max(0.0, average_gov_wastes * 0.3 - expected_wastes)

        return adjusted_wastes * (max_potential / civil_usage)

    @staticmethod
    def calculate_tax_income(
            universal_tax: float,
            excise: float,
            additions: float,
            small_enterprise_tax: float,
            large_enterprise_tax: float,
            small_enterprise_percent: float,
            large_enterprise_count: float,
            population_count: int
    ) -> float:
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
    def calculate_forex_course(
            stability: int,
            income: float,
            wastes: float,
            budget: float,
            trade_rank: int,
            trade_efficiency: float,
            trade_overload: float,
            industry_efficiency: float,
            state_apparatus_efficiency: int,
            contentment: int, poor_level: float,
            jobless_level: float,
            control_data: list
    ) -> float:
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
    def calculate_agriculture_factor(
            current_tax_income: float,
            agriculture_development: float,
            workers_count: int
    ) -> float:
        """Считает влияние на доход от развитости сельского СХ"""
        economic_involvement = current_tax_income / 100
        hyperbolic_percent = economic_involvement * agriculture_development

        base_addition = hyperbolic_percent / 100
        if workers_count < 1_000_000:
            return base_addition
        return base_addition * (workers_count // 1_000_000)

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
    def calculate_knowledge(
            cls,
            population_count: int,
            knowledge_wastes: float
    ) -> float:
        """Предсказывает образованность"""
        # TODO: Пересмотреть взгляд на формулу
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
    def calculate_industry_overproduction_change(
            tvr1: int,
            tvr2: int,
            consumption: float,
            trade_usage: int
    ) -> float:
        if trade_usage >= 40:
            return -1 * (trade_usage / 100)

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

    @staticmethod
    def calculate_overproduction_tax_spotter(
            overproduction_coefficient: float
    ) -> float:
        return 1 - (overproduction_coefficient / 100)

    @staticmethod
    def calculate_overproduction_trade_income(
            overproduction_coefficient: float
    ) -> float:
        return 1 - (overproduction_coefficient / 50)
