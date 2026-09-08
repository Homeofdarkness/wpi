"""Output the resolved state."""

from __future__ import annotations

from functions.time_models import format_months
from modules.skip_move_types import SkipMoveReport, WorldState
from utils.logger_manager import get_logger


logger = get_logger("Finalizer")


def _boxed_report(
    title: str,
    sections: tuple[tuple[str, list[tuple[str, str]]], ...],
) -> str:
    """Render a readable two-column console report with stable borders."""
    rows = [row for _, section_rows in sections for row in section_rows]
    label_width = max(len(label) for label, _ in rows)
    value_width = max(len(value) for _, value in rows)
    content_width = label_width + value_width + 3
    if len(title) > content_width:
        label_width += len(title) - content_width
        content_width = len(title)
    border = f"╫{'═' * (label_width + 2)}╫{'═' * (value_width + 2)}╫"
    result = [border, f"╫ {title.center(content_width)} ╫", border]
    for index, (section_name, section_rows) in enumerate(sections):
        if section_name:
            result.append(f"╫ {section_name.center(content_width, '─')} ╫")
        result.extend(
            f"╫ {label:<{label_width}} ╫ {value:>{value_width}} ╫"
            for label, value in section_rows
        )
        if index < len(sections) - 1:
            result.append(border)
    result.append(border)
    return "\n".join(result)


def render_budget_report(report: SkipMoveReport) -> str:
    """Render the resolved turn as a compact, auditable budget statement."""
    ledger = report.ledger
    if ledger is None:
        return "ОТЧЁТ БЮДЖЕТА\nНет данных"

    income_lines = [
        ("Налоговый доход", report.tax_income),
        ("Торговый доход", report.trade_income),
        ("Доход филиалов", report.branches_income),
        ("Доход промышленности", report.industry_income),
        ("Доход науки", report.science_income),
        ("Баланс ресурсов", report.resource_balance),
        ("Валовые доходы", ledger.gross_income),
        ("Доходы после модификаторов", ledger.effective_income),
    ]
    expense_lines = [
        ("Поправка расходов от ресурсов", report.resource_effect_wastes),
        ("Общие расходы", report.total_wastes),
        ("Логистическая скидка", report.logistic_discount),
    ]
    result_lines = [
        ("Казна до хода", report.budget_before),
        (
            "Изменение казны до кредита",
            report.budget_after_boost - report.budget_before,
        ),
        ("Казна до кредита", report.budget_after_boost),
    ]
    if report.credit_taken:
        result_lines.extend(
            (
                ("Полученный кредит", report.credit_amount),
                ("Казна после кредита", float(report.budget_final or 0.0)),
            )
        )
    stability_lines = [
        ("Стабильность до хода", f"{report.stability_before:.1f}%"),
        (
            "Поправка государственного аппарата",
            f"{report.stability_policy_adjustment:+.1f} п.п.",
        ),
        (
            "Поправка эффектов",
            f"{report.stability_effect_adjustment:+.1f} п.п.",
        ),
        ("Стабильность после хода", f"{report.stability_after:.1f}%"),
    ]

    def money_rows(values: list[tuple[str, float]]) -> list[tuple[str, str]]:
        return [(label, f"{value:.1f} ед.вал") for label, value in values]

    title = (
        f"ОТЧЁТ БЮДЖЕТА ({format_months(report.turn_months, uppercase=True)})"
    )
    return _boxed_report(
        title,
        (
            ("ДОХОДЫ", money_rows(income_lines)),
            ("РАСХОДЫ", money_rows(expense_lines)),
            ("ИТОГ", money_rows(result_lines)),
            ("ЭКОНОМИЧЕСКАЯ СТАБИЛЬНОСТЬ", stability_lines),
        ),
    )


def print_budget_report(report: SkipMoveReport) -> None:
    text = render_budget_report(report)
    print(text)
    logger.info(text)


def _people(value: float | int, *, signed: bool = False) -> str:
    rounded = round(float(value))
    prefix = "+" if signed and rounded > 0 else ""
    return f"{prefix}{rounded:,}".replace(",", " ") + " чел."


def render_population_growth_report(report: SkipMoveReport) -> str:
    """Render every factor used to form the turn's population change."""
    growth = report.population_growth
    if growth is None:
        return "ОТЧЁТ ПРИРОСТА НАСЕЛЕНИЯ\nНет данных"

    number_lines = [
        ("Население до хода", _people(growth.population_before)),
        ("Базовый прирост", _people(growth.base_growth)),
        (
            "Поправка формул ресурсов",
            _people(growth.resource_adjustment, signed=True),
        ),
        (
            "Прирост после ресурсов",
            _people(growth.growth_after_resources),
        ),
    ]
    factor_lines = [
        ("Коэффициент обеспеченности ТЖН", growth.goods_factor),
        ("Коэффициент стабильности", growth.stability_factor),
        ("Коэффициент довольства", growth.contentment_factor),
        ("Коэффициент многодетности", growth.child_policy_factor),
        ("Коэффициент продовольствия", growth.food_security_factor),
        ("Коэффициент упадка общества", growth.social_decline_factor),
        ("Коэффициент разнообразия", growth.food_diversity_factor),
        ("Совокупный коэффициент", growth.total_factor),
    ]
    result_lines = [
        ("Итоговый расчётный прирост", _people(growth.final_growth)),
        ("Убыль по УНЧС", _people(-growth.decline_deaths)),
        ("Смерти от недоедания", _people(-growth.underfeed_deaths)),
        (
            "Чистое изменение населения",
            _people(growth.net_change, signed=True),
        ),
        ("Население после хода", _people(growth.population_after)),
    ]
    title = (
        "ОТЧЁТ ПРИРОСТА НАСЕЛЕНИЯ "
        f"({format_months(growth.turn_months, uppercase=True)})"
    )
    return _boxed_report(
        title,
        (
            ("ОСНОВА", number_lines),
            (
                "КОЭФФИЦИЕНТЫ",
                [(label, f"×{value:.4f}") for label, value in factor_lines],
            ),
            ("ИТОГ", result_lines),
        ),
    )


def print_population_growth_report(report: SkipMoveReport) -> None:
    text = render_population_growth_report(report)
    print(text)
    logger.info(text)


def print_final_state(state: WorldState) -> None:
    print("Стата - ")
    for section in (
        state.economy,
        state.industry,
        state.agriculture,
        state.inner_politics,
        state.probabilities,
    ):
        print(section)
        logger.info(section)

    # Rules and their remaining duration are deliberately kept outside the
    # public stat block.  They still have to be returned after every turn so
    # the next moves_skipper run does not lose or reset them.
    production_report = state.industry.render_production_results()
    effect_report = state.industry.render_effect_results()
    next_turn_configuration = state.industry.render_configuration()
    print("\nОтдельный отчёт промышленности -")
    print(production_report)
    print()
    print(effect_report)
    print("\nTOML промышленности для следующего хода -")
    print(next_turn_configuration)
    logger.info(production_report)
    logger.info(effect_report)
    logger.info(next_turn_configuration)
