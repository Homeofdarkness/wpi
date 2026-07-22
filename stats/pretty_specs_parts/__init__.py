from stats.pretty_specs_parts.agriculture import (
    AGRICULTURE_LAYOUT,
    ISF_AGRICULTURE_LAYOUT,
)
from stats.pretty_specs_parts.economy import (
    ATTERIUM_ECONOMY_LAYOUT,
    BASIC_ECONOMY_LAYOUT,
    ISF_ECONOMY_LAYOUT,
)
from stats.pretty_specs_parts.industry import INDUSTRY_LAYOUT
from stats.pretty_specs_parts.inner_politics import (
    ATTERIUM_INNER_LAYOUT,
    BASIC_INNER_LAYOUT,
    ISF_INNER_LAYOUT,
)
from stats.pretty_specs_parts.probability import PROBABILITY_LAYOUT


LAYOUTS_BY_CLASS = {
    "EconomyStats": BASIC_ECONOMY_LAYOUT,
    "AtteriumEconomyStats": ATTERIUM_ECONOMY_LAYOUT,
    "IsfEconomyStats": ISF_ECONOMY_LAYOUT,
    "IndustrialStats": INDUSTRY_LAYOUT,
    "AgricultureStats": AGRICULTURE_LAYOUT,
    "IsfAgricultureStats": ISF_AGRICULTURE_LAYOUT,
    "InnerPoliticsStats": BASIC_INNER_LAYOUT,
    "AtteriumInnerPoliticsStats": ATTERIUM_INNER_LAYOUT,
    "IsfInnerPoliticsStats": ISF_INNER_LAYOUT,
    "ProbabilityStats": PROBABILITY_LAYOUT,
}


def get_layout_for_class(class_name: str):
    return LAYOUTS_BY_CLASS[class_name]
