from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Dict

from functions.atterium_in_move_functions import AtteriumInMoveFunctions
from functions.basic_in_move_functions import BasicInMoveFunctions
from functions.isf_in_move_functions import IsfInMoveFunctions
from modules.run_start_skip import StatsConfig
from modules.skip_move_rules import (
    AtteriumSkipMoveRules,
    BasicSkipMoveRules,
    IsfSkipMoveRules,
    SkipMoveRules,
)
from stats.atterium_stats import (
    AtteriumAgricultureStats,
    AtteriumEconomyStats,
    AtteriumIndustrialStats,
    AtteriumInnerPoliticsStats,
)
from stats.basic_stats import (
    AgricultureStats,
    EconomyStats,
    IndustrialStats,
    InnerPoliticsStats
)
from stats.isf_stats import (
    IsfAgricultureStats,
    IsfEconomyStats,
    IsfIndustrialStats,
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

    The skip-move engine is shared; modes only provide:
      - which Stats models to use
      - which formulas (InMoveFunctions) to use
      - which policy/rules (SkipMoveRules) to use
    """

    mode: GameMode
    name: str
    description: str
    stats_config: StatsConfig
    in_move_functions_factory: Callable[[], object]
    rules_factory: Callable[[], SkipMoveRules]


class ModeRegistry:
    """Central place to register/extend game modes."""

    _modes: Dict[GameMode, ModeSpec] = {
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
            in_move_functions_factory=BasicInMoveFunctions,
            rules_factory=BasicSkipMoveRules,
        ),
        GameMode.ATTERIUM: ModeSpec(
            mode=GameMode.ATTERIUM,
            name="Atterium",
            description="Правила Аттериума",
            stats_config=StatsConfig(
                economy_class=AtteriumEconomyStats,
                industry_class=AtteriumIndustrialStats,
                agriculture_class=AtteriumAgricultureStats,
                inner_politics_class=AtteriumInnerPoliticsStats,
            ),
            in_move_functions_factory=AtteriumInMoveFunctions,
            rules_factory=AtteriumSkipMoveRules,
        ),
        GameMode.ISF: ModeSpec(
            mode=GameMode.ISF,
            name="ISF",
            description="Правила Империи Серебряного Феникса",
            stats_config=StatsConfig(
                economy_class=IsfEconomyStats,
                industry_class=IsfIndustrialStats,
                agriculture_class=IsfAgricultureStats,
                inner_politics_class=IsfInnerPoliticsStats,
            ),
            in_move_functions_factory=IsfInMoveFunctions,
            rules_factory=IsfSkipMoveRules,
        ),
    }

    @classmethod
    def get(cls, mode: GameMode) -> ModeSpec:
        return cls._modes[mode]

    @classmethod
    def available(cls) -> Dict[GameMode, ModeSpec]:
        return dict(cls._modes)
