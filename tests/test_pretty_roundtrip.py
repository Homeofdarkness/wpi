from __future__ import annotations

import random

from stats.basic_stats import EconomyStats, IndustrialStats, AgricultureStats, InnerPoliticsStats
from tests.factories import make_basic_bundle, make_atterium_bundle, make_isf_bundle


def test_basic_industry_roundtrip_from_pretty():
    random.seed(20)
    industry = make_basic_bundle().industry
    text = str(industry)
    parsed = IndustrialStats.from_stats_text(text)
    print(text)

    assert parsed.processing_production == industry.processing_production
    assert parsed.processing_usage == industry.processing_usage
    assert parsed.processing_efficiency == industry.processing_efficiency
    assert parsed.usages[:len(industry.usages)] == industry.usages
    assert parsed.logistic == industry.logistic
    assert parsed.war_production_efficiency == industry.war_production_efficiency


def test_basic_agriculture_roundtrip_from_pretty():
    random.seed(21)
    agriculture = make_basic_bundle().agriculture
    agriculture.food_supplies = 123.45
    text = str(agriculture)
    parsed = AgricultureStats.from_stats_text(text)
    print(text)

    assert parsed.husbandry == agriculture.husbandry
    assert parsed.livestock == agriculture.livestock
    assert parsed.others == agriculture.others
    assert parsed.securities == agriculture.securities
    assert parsed.overstock_percent == agriculture.overstock_percent
    assert parsed.food_supplies == agriculture.food_supplies


def test_basic_inner_politics_roundtrip_from_pretty():
    random.seed(22)
    inner = make_basic_bundle().inner_politics
    text = str(inner)
    parsed = InnerPoliticsStats.from_stats_text(text)
    print(text)

    assert parsed.state_apparatus_size == inner.state_apparatus_size
    assert parsed.knowledge_level == inner.knowledge_level
    assert parsed.control == inner.control
    assert parsed.commitment_to_cause == inner.commitment_to_cause
    assert parsed.departure_from_truths == inner.departure_from_truths


def test_legacy_basic_economy_spacing_without_spaces_before_dash_is_still_parsed():
    text = """Население-13828502                  УНЧС - 0                        Прирост-202322
Казна- --89.0 (0.0)               Экономическая стабильность - 92%                Инфляция - 14.0%
ДОХОДЫ - + 3361.377 ед.вал в ход
УН - 20.1                    Акцизы - 14.1                        Дополнительные средства - +67.0 ед.вал
Налог на предпринимательство - 15.1                         Налог на крупных предпринимателей - 25.1
Содержание инфраструктуры - 841.3                                  логистики - 51.0
гос.аппарата - 542.2                                                 ресурсодобычи - 269.0
Траты на образование - 641.8               здравоохранение - 233.0               охранные учреждения - 500.0
соц.сферу - 95.6                                                                     науку - 189.0
Субсидирование бизнеса - 17.0                           Внешние расходы - 90.0                  Оккупация - 0.0
Траты на армию - 215.5              военное производство - 34.0                  флот - 15.0
ТОРГОВЛЯ
Торговый ранг - 2                         Торговый потенциал - 3 т.п.                        Эффективность торговли - 80%
Исп. пути - 1                        Загрузка путей - 33%                        Трансп. издержки - 1.0 ед.вал
Доступные пути - 8                                                                      Торговая прибыль - 2.000
Высокого качества - 30.0%                     Среднего качества - 40.0%                    Низкого качества - 30.0%
Вальжерия - 10.0%                             Аллегоризация - 0.0%                            Курс валюты - 1.20
Филиалы - 2                                 Эффективность - 80.0%                                 Доход - 16.000
"""
    parsed = EconomyStats.from_stats_text(text)

    assert parsed.population_count == 13_828_502
    assert parsed.decrement_coefficient == 0
    assert parsed.current_budget == 0.0
    assert parsed.prev_budget == -89.0
    assert parsed.gov_wastes == [841.3, 51.0, 542.2, 269.0]
    assert parsed.other_wastes == [17.0, 90.0, 0.0]
    assert parsed.war_wastes == [215.5, 34.0, 15.0]


def test_all_mode_layouts_are_available_after_split():
    assert make_basic_bundle().economy._get_pretty_layout() is not None
    assert make_atterium_bundle().economy._get_pretty_layout() is not None
    assert make_isf_bundle().economy._get_pretty_layout() is not None
