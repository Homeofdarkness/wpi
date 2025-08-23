from typing import Tuple, List

from functions.basic_in_move_functions import BasicInMoveFunctions


class AtteriumInMoveFunctions(BasicInMoveFunctions):

    @staticmethod
    def calculate_plan_efficiency_spotter(
            state_apparatus_functionality: float) -> float:
        return state_apparatus_functionality * 0.002

    @staticmethod
    def calculate_dependencies_debuff(trade_dependencies: float) -> float:
        return trade_dependencies * 0.5

    @staticmethod
    def calculate_huge_economy_buff(egocentrism_development: float) -> float:
        return max(1.0, (egocentrism_development * 0.25) / 10)

    @staticmethod
    def calculate_agriculture_base_wastes(biome_richness: float,
                                          agriculture_development: float,
                                          C=400, K=4) -> float:
        """Рассчитывает базовый коэффициент затрат на сельское хозяйство."""
        biome_factor = (1 - biome_richness / 100)
        development_factor = (100 - agriculture_development) / 100

        base_cost = C * (biome_factor + development_factor) * K
        return max(base_cost / 100, 1)

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
        expenses = (
                           population_count / 1000000) * influence_factor * base_cost
        return expenses

    @staticmethod
    def calculate_adrian_effect_spotters(adrian_effect: float) -> Tuple[
        float, float]:
        adrian_effect_percent = adrian_effect / 100
        return 1 + (adrian_effect_percent * 3), 1 + (
                adrian_effect_percent / 4)

    @staticmethod
    def calculate_power_of_economic_formation_buffs(
            power_of_economic_formation: float) -> Tuple[
        float, float, float, float]:
        # даёт 1% баффа к торговым доходам, 1% баффа к доходам от акцизов, 0,5% к доходу от СиРМБ, на 1% баффает доход о филиалов
        power_of_economic_formation_percent = power_of_economic_formation / 200
        return 1 + power_of_economic_formation_percent, 1 + power_of_economic_formation_percent, 1 + (
                power_of_economic_formation_percent / 2), 1 + power_of_economic_formation_percent

    @staticmethod
    def calculate_plan_efficiency_income(plan_efficiency: float,
                                         count: int) -> float:
        return (plan_efficiency / 80) * count
