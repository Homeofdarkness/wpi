from utils.reporting import boxed_table


def test_boxed_table_expands_to_fit_a_long_title() -> None:
    report = boxed_table(
        "ОЧЕНЬ ДЛИННЫЙ ЗАГОЛОВОК ОТЧЁТА",
        ("Поле", "Вес"),
        (("Значение", "20%"),),
    )

    assert len({len(line) for line in report.splitlines()}) == 1
