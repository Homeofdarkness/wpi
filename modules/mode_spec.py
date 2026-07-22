from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from modules.run_start_skip import StatsConfig
from modules.skip_move_rules import (
    AtteriumSkipMoveRules,
    BasicSkipMoveRules,
    IsfSkipMoveRules,
    SkipMoveRules,
)
from stats.atterium_stats import (
    AtteriumEconomyStats,
    AtteriumInnerPoliticsStats,
)
from stats.basic_stats import (
    AgricultureStats,
    EconomyStats,
    IndustrialStats,
    InnerPoliticsStats,
)
from stats.isf_stats import (
    IsfAgricultureStats,
    IsfEconomyStats,
    IsfInnerPoliticsStats,
)


class GameMode(StrEnum):
    """World / ruleset modes."""

    BASIC = "basic"
    ATTERIUM = "atterium"
    ISF = "isf"


@dataclass(frozen=True)
class ModeSpec:
    """Everything that differs between world modes.

    The turn engine is shared; modes provide state models and policy rules.
    """

    mode: GameMode
    name: str
    description: str
    stats_config: StatsConfig
    rules_factory: Callable[[], SkipMoveRules]


MODE_SPECS: dict[GameMode, ModeSpec] = {
    GameMode.BASIC: ModeSpec(
        mode=GameMode.BASIC,
        name="Базовый",
        description="Стандартные правила",
        stats_config=StatsConfig(
            economy_class=EconomyStats,
            industry_class=IndustrialStats,
            agriculture_class=AgricultureStats,
            inner_politics_class=InnerPoliticsStats,
        ),
        rules_factory=BasicSkipMoveRules,
    ),
    GameMode.ATTERIUM: ModeSpec(
        mode=GameMode.ATTERIUM,
        name="Atterium",
        description="Правила Аттериума",
        stats_config=StatsConfig(
            economy_class=AtteriumEconomyStats,
            industry_class=IndustrialStats,
            agriculture_class=AgricultureStats,
            inner_politics_class=AtteriumInnerPoliticsStats,
        ),
        rules_factory=AtteriumSkipMoveRules,
    ),
    GameMode.ISF: ModeSpec(
        mode=GameMode.ISF,
        name="ISF",
        description="Правила Империи Серебряного Феникса",
        stats_config=StatsConfig(
            economy_class=IsfEconomyStats,
            industry_class=IndustrialStats,
            agriculture_class=IsfAgricultureStats,
            inner_politics_class=IsfInnerPoliticsStats,
        ),
        rules_factory=IsfSkipMoveRules,
    ),
}


def get_mode(mode: GameMode) -> ModeSpec:
    return MODE_SPECS[mode]


def available_modes() -> dict[GameMode, ModeSpec]:
    return dict(MODE_SPECS)
