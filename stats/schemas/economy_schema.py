"""Schema definitions generated from existing stats classes.

These centralize field groups/names/regex patterns and reduce duplication between modes.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List

MODES = ['basic', 'atterium', 'isf']

COMMON_FIELD_GROUPS: Dict[str, List[str]] = {'Основные параметры': ['population_count', 'decrement_coefficient', 'current_budget', 'stability', 'inflation'], 'Расходы': ['gov_wastes', 'med_wastes', 'war_wastes', 'other_wastes']}
BASIC_FIELD_GROUPS: Dict[str, List[str]] = {'Налоги и доходы': ['universal_tax', 'excise', 'additions', 'small_enterprise_tax', 'large_enterprise_tax'], 'Торговля': ['trade_rank', 'trade_usage', 'trade_efficiency', 'trade_wastes', 'high_quality_percent', 'mid_quality_percent', 'low_quality_percent', 'valgery', 'allegorization', 'branches_count', 'branches_efficiency']}
ATTERIUM_FIELD_GROUPS: Dict[str, List[str]] = {'Налоги и доходы': ['universal_tax', 'excise', 'additions', 'freedom_and_efficiency_of_small_business', 'investment_of_large_companies', 'plan_efficiency'], 'Торговля': ['trade_rank', 'trade_usage', 'trade_efficiency', 'trade_wastes', 'high_quality_percent', 'mid_quality_percent', 'low_quality_percent', 'valgery', 'allegorization', 'branches_count', 'branches_efficiency', 'adrian_effect', 'power_of_economic_formation']}
ISF_FIELD_GROUPS: Dict[str, List[str]] = {'Налоги и доходы': ['universal_tax', 'excise', 'additions', 'small_business_tax', 'large_enterprise_tax'], 'Торговля': ['trade_rank', 'trade_usage', 'trade_efficiency', 'trade_wastes', 'high_quality_percent', 'mid_quality_percent', 'low_quality_percent', 'valgery', 'allegorization', 'branches_count', 'branches_efficiency']}

COMMON_FIELD_NAMES: Dict[str, str] = {'additions': 'Дополнительные средства', 'allegorization': 'Аллегоризация', 'branches_count': 'Количество филиалов', 'branches_efficiency': 'Эффективность филиалов (%)', 'current_budget': 'Текущий размер казны', 'decrement_coefficient': 'УНЧС (0-5)', 'excise': 'Акцизы', 'high_quality_percent': 'Процент товаров высокого качества', 'inflation': 'Инфляция (%)', 'low_quality_percent': 'Процент товаров низкого качества', 'med_wastes': 'Расходы на социальную сферу (образование здравоохранение охрана соц.сфера наука)', 'mid_quality_percent': 'Процент товаров среднего качества', 'population_count': 'Население', 'stability': 'Экономическая стабильность (%)', 'trade_efficiency': 'Торговая эффективность (%)', 'trade_rank': 'Торговый ранг', 'trade_usage': 'Число используемых торговых путей', 'trade_wastes': 'Торговые издержки', 'universal_tax': 'УН', 'valgery': 'Вальжерия', 'war_wastes': 'Расходы на военную сферу (армия военное_производство флот)'}
BASIC_FIELD_NAMES: Dict[str, str] = {'small_enterprise_tax': 'Налог на мелкое предпринимательство', 'large_enterprise_tax': 'Налог на крупных предпринимателей', 'gov_wastes': 'Расходы на государство (инфраструктура логистика гос.аппарат ресурсодобыча)', 'other_wastes': 'Дополнительные расходы (субсидирование внешние оккупация)'}
ATTERIUM_FIELD_NAMES: Dict[str, str] = {'freedom_and_efficiency_of_small_business': 'СиРМБ', 'investment_of_large_companies': 'Вложения крупных компаний', 'plan_efficiency': 'Эфисп приказов Цесаркии (%)', 'gov_wastes': 'Расходы на государство (инфраструктура логистика федеративное республиканское ресурсодобыча)', 'other_wastes': 'Дополнительные расходы (внешние оккупация)', 'adrian_effect': 'Эффект Адриана (Рантье)', 'power_of_economic_formation': 'Сила СЭЗ'}
ISF_FIELD_NAMES: Dict[str, str] = {'small_business_tax': 'Налог на малый бизнес', 'large_enterprise_tax': 'Налоги с аристократии', 'gov_wastes': 'Расходы на государство (инфраструктура логистика гос.аппарат ресурсодобыча)', 'other_wastes': 'Дополнительные расходы (внешние оккупация)'}

COMMON_REGEX_PATTERNS: Dict[str, Any] = {'additions': 'Дополнительные средства - \\+([\\d.]+) ед\\.вал', 'allegorization': 'Аллегоризация - ([\\d.]+)%', 'branches_count': 'Количество филиалов - (\\d+)', 'branches_efficiency': 'Эффективность - ([\\d.]+)%', 'current_budget': {'type': 'budget_calculation', 'pattern': 'Казна- [+-]([\\d.]+) \\(([\\d.]+)\\)', 'field': 'current_budget'}, 'decrement_coefficient': 'УНЧС - (\\d+)', 'excise': 'Акцизы - ([\\d.]+)', 'forex': 'Курс валюты - ([\\d.]+)', 'high_quality_percent': 'Высокого качества - ([\\d.]+)%', 'inflation': 'Инфляция - ([\\d.]+)%', 'low_quality_percent': 'Низкого качества - ([\\d.]+)%', 'med_wastes': ['Траты на образование - ([\\d.]+)', 'здравоохранение - ([\\d.]+)', 'охранные учреждения - ([\\d.]+)', 'соц\\.сферу - ([\\d.]+)', 'науку - ([\\d.]+)'], 'mid_quality_percent': 'Среднего качества - ([\\d.]+)%', 'population_count': 'Население-(\\d+)', 'prev_budget': {'type': 'budget_calculation', 'pattern': 'Казна- [+-]([\\d.]+) \\(([\\d.]+)\\)', 'field': 'prev_budget'}, 'stability': 'Экономическая стабильность - (\\d+)%', 'tax_income': 'ДОХОДЫ - \\+ ([\\d.]+) ед\\.вал', 'trade_efficiency': 'Эффективность торговли - (\\d+)%', 'trade_income': 'Торговая прибыль - ([\\d.]+)', 'trade_rank': 'Торговый ранг - (\\d+)', 'trade_usage': 'Число используемых торговых путей - (\\d+)', 'trade_wastes': 'Транспортные издержки - ([\\d.]+) ед\\.вал', 'universal_tax': 'УН - ([\\d.]+)', 'valgery': 'Вальжерия - ([\\d.]+)%', 'war_wastes': ['Траты на армию - ([\\d.]+)', 'военное производство - ([\\d.]+)', 'флот - ([\\d.]+)']}
BASIC_REGEX_PATTERNS: Dict[str, Any] = {'small_enterprise_tax': 'Налог на предпринимательство - ([\\d.]+)', 'large_enterprise_tax': 'Налог на крупных предпринимателей - ([\\d.]+)', 'gov_wastes': ['Содержание инфраструктуры - ([\\d.]+)', 'логистики - ([\\d.]+)', 'гос\\.аппарата - ([\\d.]+)', 'ресурсодобычи - ([\\d.]+)'], 'other_wastes': ['Субсидирование бизнеса - ([\\d.]+)', 'Внешние расходы - ([\\d.]+)', 'Оккупация - ([\\d.]+)']}
ATTERIUM_REGEX_PATTERNS: Dict[str, Any] = {'freedom_and_efficiency_of_small_business': 'СиРМБ - ([\\d.]+)', 'investment_of_large_companies': 'Вложения крупных компаний - ([\\d.]+)', 'plan_efficiency': 'Эфисп приказов Цесаркии - ([\\d.]+)%', 'gov_wastes': ['Содержание инфраструктуры - ([\\d.]+)', 'логистики - ([\\d.]+)', 'федеративное - ([\\d.]+)', 'республиканское - ([\\d.]+)', 'ресурсодобычи - ([\\d.]+)'], 'other_wastes': ['Внешние расходы - ([\\d.]+)', 'Оккупация - ([\\d.]+)'], 'adrian_effect': 'Эффект Адриана \\(Рантье\\) - ([\\d.]+)', 'power_of_economic_formation': 'Сила СЭЗ - ([\\d.]+)'}
ISF_REGEX_PATTERNS: Dict[str, Any] = {'small_business_tax': 'Налог на малый бизнес - ([\\d.]+)', 'large_enterprise_tax': 'Налоги с аристократии - ([\\d.]+)', 'gov_wastes': ['Содержание инфраструктуры - ([\\d.]+)', 'логистики - ([\\d.]+)', 'гос\\.аппарата - ([\\d.]+)', 'ресурсодобычи - ([\\d.]+)'], 'other_wastes': ['Внешние расходы - ([\\d.]+)', 'Оккупация - ([\\d.]+)']}

def _mode_dict(mode: str, *, kind: str):
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}. Expected one of {MODES}")
    if kind == "groups":
        return {
            'basic': BASIC_FIELD_GROUPS,
            'atterium': ATTERIUM_FIELD_GROUPS,
            'isf': ISF_FIELD_GROUPS,
        }[mode]
    if kind == "names":
        return {
            'basic': BASIC_FIELD_NAMES,
            'atterium': ATTERIUM_FIELD_NAMES,
            'isf': ISF_FIELD_NAMES,
        }[mode]
    if kind == "patterns":
        return {
            'basic': BASIC_REGEX_PATTERNS,
            'atterium': ATTERIUM_REGEX_PATTERNS,
            'isf': ISF_REGEX_PATTERNS,
        }[mode]
    raise ValueError(f"Unknown kind: {kind}")

def build_field_groups(mode: str) -> Dict[str, List[str]]:
    base = deepcopy(COMMON_FIELD_GROUPS)
    base.update(deepcopy(_mode_dict(mode, kind="groups")))
    return base

def build_field_names(mode: str) -> Dict[str, str]:
    base = deepcopy(COMMON_FIELD_NAMES)
    base.update(deepcopy(_mode_dict(mode, kind="names")))
    return base

def build_regex_patterns(mode: str) -> Dict[str, Any]:
    base = deepcopy(COMMON_REGEX_PATTERNS)
    base.update(deepcopy(_mode_dict(mode, kind="patterns")))
    return base
