import pytest

from functions.time_models import TURN_MONTHS, format_months
from modules.run_finalize import (
    print_final_state,
    render_budget_report,
    render_population_growth_report,
)
from modules.run_skip_move import TurnEngine
from modules.skip_move_types import WorldState
from tests.factories import make_basic_bundle
from utils.user_io import TestIO


def test_final_output_keeps_production_and_next_turn_settings(capsys):
    bundle = make_basic_bundle()
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )

    print_final_state(state)

    output = capsys.readouterr().out
    assert "Отдельный отчёт промышленности" in output
    assert "Правила производства не загружены" in output
    assert "ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ" in output
    assert "freshwater_population_growth:" in output
    assert "ожидает расчёта хода" in output
    assert "TOML промышленности для следующего хода" in output
    assert "schema_version = 3" in output
    assert "НАСТРОЙКА ПРОМЫШЛЕННОСТИ" not in output


def test_budget_report_explains_the_turn_with_one_decimal() -> None:
    bundle = make_basic_bundle(budget=1_000)
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )
    report = TurnEngine(state=state, io=TestIO()).run()

    output = render_budget_report(report)

    assert "╫" in output
    assert "ОТЧЁТ БЮДЖЕТА" in output
    assert "Валовые доходы" in output
    assert "Общие расходы" in output
    assert "Изменение казны до кредита" in output
    assert "Стабильность до хода" in output
    assert "Поправка государственного аппарата" in output
    assert "Стабильность после хода" in output
    assert f"{report.total_wastes:.1f} ед.вал" in output


def test_population_report_explains_every_growth_factor() -> None:
    bundle = make_basic_bundle(budget=1_000)
    state = WorldState(
        economy=bundle.economy,
        industry=bundle.industry,
        agriculture=bundle.agriculture,
        inner_politics=bundle.inner_politics,
    )
    report = TurnEngine(state=state, io=TestIO()).run()

    output = render_population_growth_report(report)
    growth = report.population_growth

    assert growth is not None
    assert "╫" in output
    assert (
        "ОТЧЁТ ПРИРОСТА НАСЕЛЕНИЯ "
        f"({format_months(TURN_MONTHS, uppercase=True)})"
    ) in output
    assert "Базовый прирост" in output
    assert "Поправка формул ресурсов" in output
    assert "Коэффициент обеспеченности ТЖН" in output
    assert "Коэффициент стабильности" in output
    assert "Коэффициент довольства" in output
    assert "Коэффициент многодетности" in output
    assert "Коэффициент продовольствия" in output
    assert "Коэффициент упадка общества" in output
    assert "Коэффициент разнообразия" in output
    assert "Убыль по УНЧС" in output
    assert "Смерти от недоедания" in output
    assert growth.final_growth == pytest.approx(
        growth.growth_after_resources * growth.total_factor
    )
    assert growth.population_after == (
        growth.population_before
        - growth.decline_deaths
        + round(growth.final_growth)
        - growth.underfeed_deaths
    )
