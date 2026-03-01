"""Schema definitions generated from existing stats classes.

These centralize field groups/names/regex patterns and reduce duplication between modes.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


MODES = ['basic', 'atterium', 'isf']

COMMON_FIELD_GROUPS = {
    'Обеспеченности': [
        'securities'
    ],
    'Природные условия': [
        'biome_richness',
        'overprotective_effects'
    ],
    'Распределение отраслей': [
        'husbandry',
        'livestock',
        'others'
    ]
}
BASIC_FIELD_GROUPS = {
    'Экономические показатели':
        [
            'agriculture_wastes',
            'expected_wastes',
            'income_from_resources',
            'storages_upkeep'
        ],
    'Качественные показатели': [
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'workers_redistribution',
        'consumption_factor',
        'overstock_percent',
        'food_supplies'
    ]
}
ATTERIUM_FIELD_GROUPS = {
    'Экономические показатели': [
        'agriculture_wastes',
        'expected_wastes',
        'income_from_resources',
        'storages_upkeep'
    ],
    'Качественные показатели': [
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'workers_redistribution',
        'consumption_factor',
        'overstock_percent',
        'food_supplies'
    ]
}
ISF_FIELD_GROUPS = {
    'Экономические показатели': [
        'agriculture_wastes',
        'expected_wastes',
        'income_from_resources',
        'storages_upkeep'
    ],
    'Территориальные и качественные показатели': [
        'empire_land_unmastery',
        'workers_redistribution',
        'consumption_factor',
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'overstock_percent',
        'food_supplies'
    ]
}

COMMON_FIELD_NAMES: Dict[str, str] = {
    'agriculture_deceases': 'Хвори сельхоза (%)',
    'agriculture_development': 'Развитость сельского хозяйства (%)',
    'agriculture_efficiency': 'Эффективность сельского хозяйства (%)',
    'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза (%)',
    'agriculture_wastes': 'Траты (ед.вал.)',
    'biome_richness': 'Богатство биомов (%)',
    'expected_wastes': 'Ожидаемые траты (ед.вал.)',
    'food_security': 'Обеспеченность едой', 'husbandry': 'Земледелие (%)',
    'income_from_resources': 'Доход от редкой и дорогой еды (ед.вал.)',
    'livestock': 'Животноводство (%)', 'others': 'Рыболовство (%)',
    'overprotective_effects': 'Эффекты от сверхплодородных земель',
    'securities': 'Обеспеченности (рабочие, технологии, удобрения, орудия труда)',
    'workers_redistribution': 'Рабочее перераспределение (%)',
    'storages_upkeep': 'Содержание хранилищ (ед.вал.)',
    'consumption_factor': 'Коэффициент потребления (%)',
    'overstock_percent': 'Изъять из потребления (%)',
    'food_supplies': 'Запасы пищи (по дефолту 0, но можно задать другие значения)',
}
BASIC_FIELD_NAMES: Dict[str, str] = {}
ATTERIUM_FIELD_NAMES: Dict[str, str] = {}
ISF_FIELD_NAMES: Dict[str, str] = {
    'empire_land_unmastery': 'Неосвоенность земель Империи'
}

COMMON_REGEX_PATTERNS: Dict[str, Any] = {
    'agriculture_wastes': 'Траты - ([\\d.]+) ед\\.вал',
    'biome_richness': 'Богатство биомов - ([\\d.]+)%',
    'expected_wastes': 'Ожидаемые траты - ([\\d.]+) ед\\.вал',
    'food_diversity': 'Пищевое разнообразие - ([\\d.]+)%',
    'husbandry': 'Земледелие - ([\\d.]+)%',
    'income_from_resources': 'Доход от редкой и дорогой еды - ([\\d.]+) ед\\.вал',
    'livestock': 'Животноводство - ([\\d.]+)%',
    'others': 'Рыболовство - ([\\d.]+)%',
    'workers_redistribution': 'Рабочее перераспределение - ([\\d.]+)%',
    'storages_upkeep': 'Содержание хранилищ (1 к 39) - ([\\d.]+) ед\\.вал',
    'consumption_factor': 'Коэффициент потребления - ([\\d.]+)%',
    'overprotective_effects': 'Эффекты от сверхплодородных земель - (\\d+)',
    'overstock_percent': 'Изъять из потребления - ([\\d.]+)%',
    'food_supplies': 'Запасы пищи - (\\d+)',
    'securities': [
        'Рабочими - ([\\d.]+)%',
        'Технологиями возделывания - ([\\d.]+)%',
        'Удобрениями, средствами - ([\\d.]+)%',
        'Орудия труда - ([\\d.]+)%'
    ]
}
BASIC_REGEX_PATTERNS: Dict[str, Any] = {
    'agriculture_deceases': 'Хвори сельхоза - ([\\d.]+)',
    'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза - ([\\d.]+)'
}
ATTERIUM_REGEX_PATTERNS: Dict[str, Any] = {
    'agriculture_deceases': 'Хвори сельхоза - ([\\d.]+)',
    'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза - ([\\d.]+)'
}
ISF_REGEX_PATTERNS: Dict[str, Any] = {
    'empire_land_unmastery': 'Неосвоенность земель Империи - ([\\d.]+)',
    'agriculture_deceases': 'Хвори сельхоза - ([\\d.]+)%',
    'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза - ([\\d.]+)%'
}


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
