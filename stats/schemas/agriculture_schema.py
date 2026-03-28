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
            'income_from_resources',
            'storages_upkeep'
        ],
    'Качественные показатели': [
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'workers_percent',
        'workers_redistribution',
        'environmental_food',
        'consumption_factor',
        'overstock_percent',
        'food_supplies'
    ]
}
ATTERIUM_FIELD_GROUPS = {
    'Экономические показатели': [
        'income_from_resources',
        'storages_upkeep'
    ],
    'Качественные показатели': [
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'workers_percent',
        'workers_redistribution',
        'environmental_food',
        'consumption_factor',
        'overstock_percent',
        'food_supplies'
    ]
}
ISF_FIELD_GROUPS = {
    'Экономические показатели': [
        'income_from_resources',
        'storages_upkeep'
    ],
    'Территориальные и качественные показатели': [
        'agriculture_deceases',
        'agriculture_natural_deceases',
        'empire_land_unmastery',
        'workers_percent',
        'workers_redistribution',
        'environmental_food',
        'consumption_factor',
        'overstock_percent',
        'food_supplies'
    ]
}

COMMON_FIELD_NAMES: Dict[str, str] = {
    'agriculture_deceases': 'Хвори сельхоза (%)',
    'agriculture_development': 'Развитость сельского хозяйства (%)',
    'agriculture_efficiency': 'Эффективность сельского хозяйства (%)',
    'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза (%)',
    'biome_richness': 'Богатство биомов (%)',
    'expected_wastes': 'Ожидаемые траты (ед.вал.)',
    'food_security': 'Обеспеченность едой', 'husbandry': 'Земледелие (%)',
    'income_from_resources': 'Доход от редкой и дорогой еды (ед.вал.)',
    'livestock': 'Животноводство (%)', 'others': 'Рыболовство (%)',
    'overprotective_effects': 'Эффекты от сверхплодородных земель',
    'securities': 'Обеспеченности (технологии, удобрения, орудия труда)',
    'workers_percent': 'Процент рабочих (%)',
    'workers_redistribution': 'Рабочее перераспределение (%)',
    'environmental_food': 'Еда из окружающей среды',
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
    raise ValueError(f"Unknown kind: {kind}")


def build_field_groups(mode: str) -> Dict[str, List[str]]:
    base = deepcopy(COMMON_FIELD_GROUPS)
    base.update(deepcopy(_mode_dict(mode, kind="groups")))
    return base


def build_field_names(mode: str) -> Dict[str, str]:
    base = deepcopy(COMMON_FIELD_NAMES)
    base.update(deepcopy(_mode_dict(mode, kind="names")))
    return base

