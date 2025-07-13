import math
import random
from typing import Tuple, List

from functions.inbuilt import InbuiltFunctions


class BasicStatsFunctions:

    # Economy
    @staticmethod
    def calculate_population_growth(current_population_count: int) -> int:
        """Расчет прироста населения (legacy)"""
        population_in_thousands = current_population_count * 10 ** -3

        if current_population_count > 8 * 10 ** 6:
            return population_in_thousands * 8.77
        elif current_population_count >= 5.5 * 10 ** 6:
            return population_in_thousands * 9.87
        elif current_population_count >= 2.5 * 10 ** 6:
            return population_in_thousands * 11.77
        elif current_population_count >= 10 ** 6:
            return population_in_thousands * 9.87

        return population_in_thousands * 6.87

    @staticmethod
    def calculate_trade_potential(trade_rank: int,
                                  trade_efficiency: int) -> float:
        """Расчет торгового потенциала"""
        if trade_rank >= 7:
            return 5 + 3 * (trade_rank - 6) * (trade_efficiency / 100)
        else:
            return 3 + 2 * (trade_rank - 2) * (trade_efficiency / 100)

    # Industry
    @staticmethod
    def calculate_industry_coefficient(processing_production: float,
                                       processing_usage: float,
                                       processing_efficiency: float,
                                       mean_score: float):
        """Расчет коэффициента производительности"""
        industry_coefficient_base = (mean_score + processing_efficiency) / 2
        industry_coefficient_loss = InbuiltFunctions.euclidean_distance(
            processing_production, processing_usage) / 4
        decrement = 1 - (abs(processing_production - processing_usage) / max(
            processing_production, processing_usage))

        return min((
                               industry_coefficient_base - industry_coefficient_loss) * decrement,
                   100)

    @staticmethod
    def calculate_civil_usage(civil_security: float, tvr1: float,
                              tvr2: float) -> int:
        """Расчет процента производства"""
        return round((civil_security + tvr1 + tvr2) / 3)

    @staticmethod
    def calculate_industry_basic_stats(industry_coefficient: float,
                                       civil_usage: float,
                                       standardization: float) -> \
            Tuple[float, float, float]:
        """Считает базовые параметры промышленности"""
        mean_value = (industry_coefficient + civil_usage + (
                    standardization / 1.35)) / 2.5
        std_dev = 100 / civil_usage + 0.2

        possible_values = [random.gauss(mean_value, std_dev) for _ in
                           range(1000)]
        probabilities = [
            InbuiltFunctions.pdf_manual(possible_value, mean_value, std_dev)
            for possible_value in
            possible_values]

        total_density = sum(probabilities)
        normalized_probabilities = [p / total_density for p in probabilities]

        payoff, dispersion = InbuiltFunctions.count_proba_params(
            possible_values, normalized_probabilities)
        while payoff < dispersion:
            dispersion /= 2

        efficiency = random.uniform(payoff - dispersion, payoff + dispersion)
        max_potential = (industry_coefficient + civil_usage) / 1.8
        expected_wastes = payoff * 0.3

        difference = civil_usage - max_potential
        adjustment = max(0.0, min((difference // 5) * 2, 7))
        efficiency -= adjustment

        return efficiency, max_potential, expected_wastes

    @staticmethod
    def calculate_civil_efficiency_boost_from_logistic(
            logistic: float) -> float:
        if logistic <= 30:
            return 1 + math.log1p(logistic) / 10
        else:
            return 1.3 + (logistic - 50) / 100

    # Inner Politics
    @staticmethod
    def calculate_success_chance(knowledge_level: float,
                                 education_level: float,
                                 erudition_will: float) -> float:
        """Расчет шанса на успех"""
        return random.gauss(knowledge_level + education_level,
                            (erudition_will / 10) ** -1) // 2

    @staticmethod
    def calculate_society_decline(contentment: int, government_trust: float,
                                  many_children_traditions: int,
                                  sexual_asceticism: float,
                                  egocentrism_development: float,
                                  education_level: int, erudition_will: int,
                                  cultural_level: int,
                                  violence_tendency: float,
                                  unemployment_rate: float,
                                  grace_of_the_highest: int,
                                  commitment_to_cause: int,
                                  departure_from_truths: int) -> float:
        """Считает упадок общества"""
        positive_factors = (
                contentment * 0.05 +
                government_trust * 0.15 +
                many_children_traditions * 0.05 +
                sexual_asceticism * 0.25 +
                education_level * 0.05 +
                erudition_will * 0.075 +
                cultural_level * 0.05 +
                grace_of_the_highest * 0.7 +
                commitment_to_cause * 0.15
        )

        negative_factors = (
                violence_tendency * 0.5 +  # + 2
                egocentrism_development * 0.3 +
                unemployment_rate * 0.3 +
                departure_from_truths * 1.1
        )

        societal_decline = max(0.0, negative_factors - positive_factors)
        societal_decline = min(societal_decline, 100)

        return round(societal_decline, 2)

    # Agriculture
    @staticmethod
    def calculate_approximate_agriculture_efficiency(
            securities: List[float]) -> float:
        """Считает примерную эффективность СХ, идея в том, чтобы внутри класса считать только из параметров класса"""
        return sum(securities) / len(securities)

    @classmethod
    def calculate_approximate_food_security(cls, biome_richness: float,
                                            overproduction_effects: int,
                                            securities: List[float]) -> float:
        """Считает приблизительную обеспеченность едой"""
        agriculture_efficiency = cls.calculate_approximate_agriculture_efficiency(
            securities)

        stock = (overproduction_effects * 6 * (
                    1 + biome_richness / 1000)) if agriculture_efficiency >= 75 else 0

        # Calculate food security using a parabolic function
        food_security = InbuiltFunctions.parabola(agriculture_efficiency / 10,
                                                  1, 4, 10) + stock

        return food_security

    @classmethod
    def calculate_agriculture_development(cls,
                                          approximate_food_security: float,
                                          securities: List[float]) -> float:
        """Считает развитость СХ"""
        agriculture_efficiency = cls.calculate_approximate_agriculture_efficiency(
            securities)
        value = (approximate_food_security * agriculture_efficiency / 8) / 1000
        sigmoid_result = InbuiltFunctions.sigmoid(value) * 100

        if min(agriculture_efficiency, approximate_food_security) < 50:
            return sigmoid_result
        else:
            return min(100.0, sigmoid_result * (100 / 77))

    @classmethod
    def calculate_branches_income(cls, branches_count: int,
                                  branches_efficiency: float) -> float:
        return branches_count * (branches_efficiency / 10)
