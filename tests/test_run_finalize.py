from modules.run_finalize import print_final_state, render_budget_report
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
    assert "Настройки промышленности для следующего хода" in output
    assert "НАСТРОЙКА ПРОМЫШЛЕННОСТИ" in output


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

    assert "ОТЧЁТ БЮДЖЕТА" in output
    assert "Валовые доходы" in output
    assert "Общие расходы" in output
    assert "Изменение казны до кредита" in output
    assert f"{report.total_wastes:.1f} ед.вал" in output
