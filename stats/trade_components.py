"""Models for optional resource and monetary trade deals."""

from __future__ import annotations

import re
from enum import StrEnum

import pydantic


class TradeDirection(StrEnum):
    """Direction from the point of view of the current country."""

    IMPORT = "import"
    EXPORT = "export"


class TradeTargetKind(StrEnum):
    RESOURCE = "resource"
    GROUP = "group"
    MONEY = "money"


class TradeLeg(pydantic.BaseModel):
    """One side of a deal, expressed as a monthly rate."""

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    target: str
    amount_per_month: float = pydantic.Field(..., gt=0)

    @pydantic.field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        if value == TradeTargetKind.MONEY.value:
            return value
        match = re.fullmatch(
            r"(resource|group):([a-z][a-z0-9_]*)",
            value,
        )
        if match is None:
            raise ValueError(
                "цель должна быть money, resource:<alias> или group:<alias>"
            )
        return value

    @property
    def kind(self) -> TradeTargetKind:
        if self.target == TradeTargetKind.MONEY.value:
            return TradeTargetKind.MONEY
        return TradeTargetKind(self.target.partition(":")[0])

    @property
    def alias(self) -> str | None:
        if self.kind is TradeTargetKind.MONEY:
            return None
        return self.target.partition(":")[2]


class TradeDeal(pydantic.BaseModel):
    """Contract terms interpreted through the current country's direction."""

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    id: str = pydantic.Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    direction: TradeDirection
    active: bool = True
    delivery: TradeLeg
    payment: TradeLeg

    @pydantic.model_validator(mode="after")
    def validate_contract(self) -> TradeDeal:
        if self.delivery.target == self.payment.target:
            raise ValueError("delivery и payment не могут иметь одну цель")
        if self.delivery.kind is TradeTargetKind.MONEY:
            raise ValueError(
                "delivery должна быть ресурсом или группой ресурсов"
            )
        return self


class TradeDealResult(pydantic.BaseModel):
    """Auditable execution result for one local trade deal."""

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    deal_id: str
    direction: TradeDirection
    delivery_target: str
    payment_target: str
    planned_delivery: float = pydantic.Field(..., ge=0)
    planned_payment: float = pydantic.Field(..., ge=0)
    actual_delivery: float = pydantic.Field(..., ge=0)
    actual_payment: float = pydantic.Field(..., ge=0)
    fulfillment: float = pydantic.Field(..., ge=0, le=1)
    route_factor: float = pydantic.Field(..., ge=0, le=1)
    money_balance: float = 0.0
    limitation: str
    delivery_allocations: dict[str, float] = pydantic.Field(
        default_factory=dict
    )
    payment_allocations: dict[str, float] = pydantic.Field(
        default_factory=dict
    )


class TradeState(pydantic.BaseModel):
    """Optional detailed trade configuration and its latest results."""

    model_config = pydantic.ConfigDict(
        validate_assignment=True, extra="forbid"
    )

    deals: list[TradeDeal] = pydantic.Field(default_factory=list)
    last_results: list[TradeDealResult] = pydantic.Field(
        default_factory=list,
        exclude=True,
    )
    last_turn_calculated: bool = pydantic.Field(False, exclude=True)
    last_money_balance: float = pydantic.Field(0.0, exclude=True)

    def render_configuration(self) -> str:
        from stats.trade_text import render_trade_configuration

        return render_trade_configuration(self)

    def render_turn_report(self, months: int) -> str:
        from stats.trade_text import render_trade_report

        return render_trade_report(self, months)
