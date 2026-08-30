"""Output the resolved state."""

from __future__ import annotations

from modules.skip_move_types import SkipMoveReport, WorldState
from utils.logger_manager import get_logger


logger = get_logger("Finalizer")


def render_budget_report(report: SkipMoveReport) -> str:
    """Render the resolved turn as a compact, auditable budget statement."""
    ledger = report.ledger
    if ledger is None:
        return "ОТЧЁТ БЮДЖЕТА\nНет данных"

    lines = [
        ("Казна до хода", report.budget_before),
        ("Налоговый доход", report.tax_income),
        ("Торговый доход", report.trade_income),
        ("Доход филиалов", report.branches_income),
        ("Доход промышленности", report.industry_income),
        ("Доход науки", report.science_income),
        ("Баланс ресурсов", report.resource_balance),
        ("Поправка расходов от ресурсов", report.resource_effect_wastes),
        ("Валовые доходы", ledger.gross_income),
        ("Доходы после модификаторов", ledger.effective_income),
        ("Общие расходы", report.total_wastes),
        ("Логистическая скидка", report.logistic_discount),
        (
            "Изменение казны до кредита",
            report.budget_after_boost - report.budget_before,
        ),
        ("Казна до кредита", report.budget_after_boost),
    ]
    if report.credit_taken:
        lines.extend(
            (
                ("Полученный кредит", report.credit_amount),
                ("Казна после кредита", float(report.budget_final or 0.0)),
            )
        )
    width = max(len(label) for label, _ in lines)
    result = ["ОТЧЁТ БЮДЖЕТА"]
    result.extend(
        f"{label:<{width}} : {value:.1f} ед.вал" for label, value in lines
    )
    return "\n".join(result)


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
    width = max(
        len(label)
        for label, _ in (*number_lines, *factor_lines, *result_lines)
    )
    lines = [f"ОТЧЁТ ПРИРОСТА НАСЕЛЕНИЯ ({growth.turn_months} МЕСЯЦА)"]
    lines.extend(
        f"{label:<{width}} : {value}" for label, value in number_lines
    )
    lines.extend(
        f"{label:<{width}} : ×{value:.4f}" for label, value in factor_lines
    )
    lines.extend(
        f"{label:<{width}} : {value}" for label, value in result_lines
    )
    return "\n".join(lines)


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
    print("\nНастройки промышленности для следующего хода -")
    print(next_turn_configuration)
    logger.info(production_report)
    logger.info(effect_report)
    logger.info(next_turn_configuration)
