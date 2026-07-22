"""Atterium-only turn modifiers."""


def plan_efficiency_factor(state_apparatus_functionality: float) -> float:
    return state_apparatus_functionality * 0.002


def dependencies_debuff(trade_dependencies: float) -> float:
    return trade_dependencies * 0.5


def huge_economy_buff(egocentrism_development: float) -> float:
    return max(1.0, egocentrism_development * 0.25 / 10)


def agriculture_base_wastes(
    biome_richness: float,
    agriculture_development: float,
    constant: float = 400,
    scale: float = 4,
) -> float:
    biome_factor = 1 - biome_richness / 100
    development_factor = (100 - agriculture_development) / 100
    base_cost = constant * (biome_factor + development_factor) * scale
    return max(base_cost / 100, 1)


def adrian_effect_factors(adrian_effect: float) -> tuple[float, float]:
    effect = adrian_effect / 100
    return 1 + effect * 3, 1 + effect / 4


def economic_formation_factors(
    power: float,
) -> tuple[float, float, float, float]:
    factor = power / 200
    return 1 + factor, 1 + factor, 1 + factor / 2, 1 + factor


def plan_efficiency_income(plan_efficiency: float, count: int) -> float:
    return plan_efficiency / 80 * count
