"""ISF-only turn modifiers."""


def huge_economy_buff(egocentrism_development: float) -> float:
    return max(1.0, egocentrism_development * 0.3 / 10)


def agriculture_base_wastes(
    biome_richness: float,
    agriculture_development: float,
    constant: float = 550,
    scale: float = 10,
) -> float:
    biome_factor = 1 - biome_richness / 100
    development_factor = (100 - agriculture_development) / 100
    base_cost = constant * (biome_factor + development_factor) * scale
    return max(base_cost / 100, 1)


def allegory_contentment_spotter(
    contentment: int,
    allegory_influence: float,
) -> float:
    return contentment * allegory_influence / 1000


def allegory_income_factor(allegory_influence: float) -> float:
    return 1 - allegory_influence / 1000
