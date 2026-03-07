from stats.pretty_specs_parts.economy import (
    BASIC_ECONOMY_LAYOUT,
    ATTERIUM_ECONOMY_LAYOUT,
    ISF_ECONOMY_LAYOUT,
)
from stats.pretty_specs_parts.industry import INDUSTRY_LAYOUT
from stats.pretty_specs_parts.agriculture import AGRICULTURE_LAYOUT, ISF_AGRICULTURE_LAYOUT
from stats.pretty_specs_parts.inner_politics import (
    BASIC_INNER_LAYOUT,
    ATTERIUM_INNER_LAYOUT,
    ISF_INNER_LAYOUT,
)

LAYOUTS_BY_CLASS = {
    "EconomyStats": BASIC_ECONOMY_LAYOUT,
    "AtteriumEconomyStats": ATTERIUM_ECONOMY_LAYOUT,
    "IsfEconomyStats": ISF_ECONOMY_LAYOUT,
    "IndustrialStats": INDUSTRY_LAYOUT,
    "AtteriumIndustrialStats": INDUSTRY_LAYOUT,
    "IsfIndustrialStats": INDUSTRY_LAYOUT,
    "AgricultureStats": AGRICULTURE_LAYOUT,
    "AtteriumAgricultureStats": AGRICULTURE_LAYOUT,
    "IsfAgricultureStats": ISF_AGRICULTURE_LAYOUT,
    "InnerPoliticsStats": BASIC_INNER_LAYOUT,
    "AtteriumInnerPoliticsStats": ATTERIUM_INNER_LAYOUT,
    "IsfInnerPoliticsStats": ISF_INNER_LAYOUT,
}


def get_layout_for_class(class_name: str):
    return LAYOUTS_BY_CLASS[class_name]
