from typing import List

from functions.basic_in_move_functions import BasicInMoveFunctions


class IsfInMoveFunctions(BasicInMoveFunctions):
    @staticmethod
    def calculate_huge_economy_buff(egocentrism_development: float) -> float:
        return max(1.0, (egocentrism_development * 0.3) / 10)

    @staticmethod
    def calculate_agriculture_base_wastes(biome_richness: float,
                                          agriculture_development: float,
                                          C=550, K=10) -> float:
        """Рассчитывает базовый коэффициент затрат на сельское хозяйство."""
        biome_factor = (1 - biome_richness / 100)
        development_factor = (100 - agriculture_development) / 100

        base_cost = C * (biome_factor + development_factor) * K
        return max(base_cost / 100, 1)

    @classmethod
    def calculate_agriculture_wastes(
            cls,
            population_count: int,
            securities: List[float],
            biome_richness: float,
            agriculture_development: float
    ) -> float:
        """Считает ожидаемые траты на СХ"""
        base_cost = cls.calculate_agriculture_base_wastes(
            biome_richness,
            agriculture_development
        )
        influence_factor = sum(
            securities) / 100  # Преобразуем проценты в коэффициент
        expenses = (population_count / 1000000) * influence_factor * base_cost
        return expenses
