"""Parse, render and report independent local trade configurations."""

from __future__ import annotations

import json
import tomllib
from typing import Any, Literal

import pydantic

from functions.time_models import format_months
from stats.industry_components import ExtractionGroup
from stats.trade_components import (
    TradeDeal,
    TradeDirection,
    TradeState,
    TradeTargetKind,
)
from utils.reporting import boxed_sections


class _TradeConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    schema_version: Literal[2]
    deals: list[TradeDeal] = pydantic.Field(default_factory=list)


def parse_trade_configuration(text: str, industry: Any) -> TradeState:
    """Parse a standalone trade TOML and validate its local targets."""

    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Некорректный TOML торговли: {error}") from error
    if raw.get("schema_version") == 1:
        raise ValueError(
            "TOML торговли schema_version = 1 устарел: замените give/receive "
            "на delivery/payment и укажите schema_version = 2"
        )
    try:
        config = _TradeConfig.model_validate(raw)
    except pydantic.ValidationError as error:
        raise ValueError(
            f"Некорректная настройка торговли:\n{error}"
        ) from error

    seen: set[str] = set()
    active_resources = {
        state.resource.value: state
        for state in industry.resource_inventory.resources.values()
        if state.enabled
    }
    for deal in config.deals:
        if deal.id in seen:
            raise ValueError(f"Торговая сделка {deal.id} указана дважды")
        seen.add(deal.id)
        for leg in (deal.delivery, deal.payment):
            if leg.kind is TradeTargetKind.RESOURCE:
                assert leg.alias is not None
                if leg.alias not in active_resources:
                    raise ValueError(
                        f"Сделка {deal.id}: ресурс {leg.alias!r} "
                        "не зарегистрирован в промышленном TOML"
                    )
            elif leg.kind is TradeTargetKind.GROUP:
                assert leg.alias is not None
                try:
                    group = ExtractionGroup(leg.alias)
                except ValueError as error:
                    raise ValueError(
                        f"Сделка {deal.id}: неизвестная группа {leg.alias!r}"
                    ) from error
                if not any(
                    state.group is group for state in active_resources.values()
                ):
                    raise ValueError(
                        f"Сделка {deal.id}: в группе {leg.alias!r} "
                        "нет зарегистрированных ресурсов"
                    )
    return TradeState(deals=config.deals)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_leg(target: str, amount: float) -> str:
    return (
        "{ target = "
        f"{_toml_string(target)}, amount_per_month = {float(amount):.1f} }}"
    )


def render_trade_configuration(state: TradeState) -> str:
    """Render an editable, standalone TOML v2 configuration."""

    lines = ["schema_version = 2"]
    if not state.deals:
        lines.append("deals = []")
        return "\n".join(lines)
    for deal in state.deals:
        delivery = _toml_leg(
            deal.delivery.target,
            deal.delivery.amount_per_month,
        )
        payment = _toml_leg(
            deal.payment.target,
            deal.payment.amount_per_month,
        )
        lines.extend(
            (
                "",
                "[[deals]]",
                f"id = {_toml_string(deal.id)}",
                f"direction = {_toml_string(deal.direction.value)}",
                f"active = {'true' if deal.active else 'false'}",
                f"delivery = {delivery}",
                f"payment = {payment}",
            )
        )
    return "\n".join(lines)


def _target_label(target: str) -> str:
    if target == "money":
        return "деньги"
    kind, _, alias = target.partition(":")
    prefix = "ресурс" if kind == "resource" else "группа"
    return f"{prefix} {alias}"


def _amount(value: float, target: str) -> str:
    unit = "ед.вал" if target == "money" else "ед.рес."
    return f"{value:.1f} {unit}"


def _allocations(values: dict[str, float]) -> str:
    if not values:
        return "—"
    return ", ".join(
        f"{alias}: {amount:.1f}" for alias, amount in values.items()
    )


def _leg_summary(
    target: str, actual: float, planned: float | None = None
) -> str:
    result = f"{_target_label(target)} — {_amount(actual, target)}"
    if planned is not None:
        result += f" из {_amount(planned, target)}"
    return result


def render_trade_report(state: TradeState, months: int) -> str:
    """Render configured or actually executed deals in the shared box style."""

    title = f"ТОРГОВЫЕ СДЕЛКИ ({format_months(months, uppercase=True)})"
    if not state.deals:
        return boxed_sections(
            title, (("", (("Состояние", "Сделки не настроены"),)),)
        )
    results = {result.deal_id: result for result in state.last_results}
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for deal in state.deals:
        direction = (
            "ИМПОРТ" if deal.direction is TradeDirection.IMPORT else "ЭКСПОРТ"
        )
        result = results.get(deal.id)
        if not deal.active:
            rows = [("Состояние", "Отключена")]
        elif result is None:
            rows = [
                (
                    "Поставка в месяц",
                    _leg_summary(
                        deal.delivery.target,
                        deal.delivery.amount_per_month,
                    ),
                ),
                (
                    "Оплата в месяц",
                    _leg_summary(
                        deal.payment.target,
                        deal.payment.amount_per_month,
                    ),
                ),
                ("Состояние", "Ожидает расчёта хода"),
            ]
        else:
            if result.direction is TradeDirection.IMPORT:
                local_given = (
                    result.payment_target,
                    result.actual_payment,
                    result.planned_payment,
                )
                local_received = (
                    result.delivery_target,
                    result.actual_delivery,
                    result.planned_delivery,
                )
            else:
                local_given = (
                    result.delivery_target,
                    result.actual_delivery,
                    result.planned_delivery,
                )
                local_received = (
                    result.payment_target,
                    result.actual_payment,
                    result.planned_payment,
                )
            rows = [
                ("Исполнение", f"{result.fulfillment * 100:.1f}%"),
                ("Маршрутный коэффициент", f"×{result.route_factor:.3f}"),
                (
                    "Предмет поставки",
                    _leg_summary(
                        result.delivery_target,
                        result.actual_delivery,
                        result.planned_delivery,
                    ),
                ),
                (
                    "Оплата",
                    _leg_summary(
                        result.payment_target,
                        result.actual_payment,
                        result.planned_payment,
                    ),
                ),
                ("Локально отдано", _leg_summary(*local_given)),
                ("Локально получено", _leg_summary(*local_received)),
                ("Ограничение", result.limitation),
            ]
            if result.delivery_allocations:
                rows.append(
                    (
                        "Состав поставки",
                        _allocations(result.delivery_allocations),
                    )
                )
            if result.payment_allocations:
                rows.append(
                    (
                        "Состав оплаты",
                        _allocations(result.payment_allocations),
                    )
                )
            if abs(result.money_balance) >= 0.0001:
                rows.append(
                    (
                        "Денежный результат",
                        f"{result.money_balance:+.1f} ед.вал",
                    )
                )
        sections.append((f"{deal.id} · {direction}", rows))
    sections.append(
        (
            "ИТОГ",
            [("Баланс сделок", f"{state.last_money_balance:+.1f} ед.вал")],
        )
    )
    return boxed_sections(title, sections)
