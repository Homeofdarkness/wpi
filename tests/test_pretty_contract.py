from stats.basic_stats import EconomyStats, AgricultureStats


def test_economy_pretty_contains_section_titles():
    stats = EconomyStats(
        population_count=1000000,
        decrement_coefficient=1,
        stability=80,
        inflation=5.0,
        current_budget=1000.0,
        prev_budget=990.0,
        universal_tax=10.0,
        excise=5.0,
        additions=2.0,
        tax_income=123.0,
        small_enterprise_tax=3.0,
        large_enterprise_tax=4.0,
        gov_wastes=[100.0, 50.0, 30.0, 10.0],
        med_wastes=[20.0, 15.0, 10.0, 5.0, 3.0],
        other_wastes=[5.0, 2.0, 1.0],
        war_wastes=[10.0, 5.0, 2.0],
        trade_rank=2,
        trade_efficiency=80.0,
        trade_usage=10,
        trade_wastes=1.0,
        high_quality_percent=30.0,
        mid_quality_percent=40.0,
        low_quality_percent=30.0,
        valgery=10.0,
        allegorization=0.0,
        forex=1.5,
        trade_income=2.5,
        branches_count=2,
        branches_efficiency=80.0,
        branches_income=16.0,
    )

    text = stats.render_pretty(debug=False)

    assert "ЭКОНОМИКА" in text
    assert "ТРАТЫ" in text
    assert "ТОРГОВЛЯ" in text
    assert "ФИЛИАЛЫ" in text


def test_economy_pretty_uses_old_expense_labels():
    stats = EconomyStats(
        population_count=1000000,
        decrement_coefficient=1,
        stability=80,
        inflation=5.0,
        current_budget=1000.0,
        prev_budget=990.0,
        universal_tax=10.0,
        excise=5.0,
        additions=2.0,
        tax_income=123.0,
        small_enterprise_tax=3.0,
        large_enterprise_tax=4.0,
        gov_wastes=[100.0, 50.0, 30.0, 10.0],
        med_wastes=[20.0, 15.0, 10.0, 5.0, 3.0],
        other_wastes=[5.0, 2.0, 1.0],
        war_wastes=[10.0, 5.0, 2.0],
        trade_rank=2,
        trade_efficiency=80.0,
        trade_usage=10,
        trade_wastes=1.0,
        high_quality_percent=30.0,
        mid_quality_percent=40.0,
        low_quality_percent=30.0,
        valgery=10.0,
        allegorization=0.0,
        forex=1.5,
        trade_income=2.5,
        branches_count=2,
        branches_efficiency=80.0,
        branches_income=16.0,
    )

    text = stats.render_pretty(debug=False)
    print(text)

    assert "Содержание инфраструктуры - 100.0" in text
    assert "Гос.аппарата - 30.0" in text
    assert "Субсидирование бизнеса - 5.0" in text
    assert "Траты на армию - 10.0" in text


def test_agriculture_pretty_contains_obespechennosti_title():
    stats = AgricultureStats(
        husbandry=40.0,
        livestock=40.0,
        others=20.0,
        biome_richness=80.0,
        overprotective_effects=0,
        securities=[50.0, 60.0, 70.0],
        workers_percent=50.0,
        workers_redistribution=0.0,
        storages_upkeep=5.0,
        consumption_factor=100.0,
        environmental_food=0,
        food_security=10.0,
        agriculture_deceases=0.0,
        agriculture_natural_deceases=0.0,
        income_from_resources=0.0,
        overstock_percent=0.0,
    )

    text = stats.render_pretty(debug=False)
    print(text)

    assert "ОБЕСПЕЧЕННОСТИ" in text
    assert "Технологиями возделывания" in text
    assert "Удобрениями, средствами" in text