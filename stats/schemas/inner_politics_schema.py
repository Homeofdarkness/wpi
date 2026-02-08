"""Schema definitions generated from existing stats classes.

These centralize field groups/names/regex patterns and reduce duplication between modes.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List

MODES = ['basic', 'atterium', 'isf']

COMMON_FIELD_GROUPS: Dict[str, List[str]] = {'Культура и образование': ['education_level', 'erudition_will', 'cultural_level', 'violence_tendency', 'panic_level', 'unemployment_rate']}
BASIC_FIELD_GROUPS: Dict[str, List[str]] = {'Государственный аппарат': ['state_apparatus_size', 'state_apparatus_efficiency', 'knowledge_level', 'many_children_propoganda', 'integrity_of_faith', 'corruption_level'], 'Экономика и социум': ['salt_security', 'poor_level', 'jobless_level', 'income_from_scientific', 'small_enterprise_percent', 'large_enterprise_count'], 'Управление территорией': ['provinces_count', 'provinces_waste', 'military_equipment', 'control'], 'Общественные настроения': ['contentment', 'government_trust', 'many_children_traditions', 'sexual_asceticism', 'egocentrism_development'], 'Духовность и убеждения': ['grace_of_the_highest', 'commitment_to_cause', 'departure_from_truths']}
ATTERIUM_FIELD_GROUPS: Dict[str, List[str]] = {'Государственный аппарат': ['state_apparatus_functionality', 'state_apparatus_size', 'state_apparatus_efficiency', 'knowledge_level', 'many_children_propoganda', 'integrity_of_faith', 'corruption_level'], 'Экономика и социум': ['salt_security', 'poor_level', 'jobless_level', 'small_enterprise_percent', 'large_enterprise_count'], 'Управление территорией': ['provinces_count', 'provinces_waste', 'military_equipment', 'control'], 'Общественные настроения': ['contentment', 'government_trust', 'many_children_traditions', 'sexual_asceticism', 'egocentrism_development', 'capitalistic_decay'], 'Социальные показатели': ['equality'], 'Духовность и убеждения': ['grace_of_the_highest', 'commitment_to_cause', 'departure_from_truths']}
ISF_FIELD_GROUPS: Dict[str, List[str]] = {'Государственный аппарат': ['state_apparatus_size', 'state_apparatus_efficiency', 'knowledge_level', 'many_children_propoganda', 'integrity_of_faith', 'corruption_level'], 'Экономика и социум': ['salt_security', 'poor_level', 'jobless_level', 'small_enterprise_percent', 'large_enterprise_count'], 'Управление территорией': ['provinces_count', 'provinces_waste', 'military_equipment', 'control', 'allegory_influence'], 'Общественные настроения': ['contentment', 'government_trust', 'many_children_traditions', 'sexual_asceticism', 'egocentrism_development'], 'Власть и духовность': ['imperial_court_power', 'grace_of_the_silver', 'commitment_to_cause', 'departure_from_truths', 'separatism_of_the_highest']}

COMMON_FIELD_NAMES: Dict[str, str] = {'commitment_to_cause': 'Собственная Убеждённость Делу', 'contentment': 'Довольство населения', 'corruption_level': 'Коррупция', 'cultural_level': 'Уровень культуры', 'departure_from_truths': 'Отхождение от истин', 'education_level': 'Образованность', 'erudition_will': 'Стремление к эрудиции', 'government_trust': 'Доверие властям', 'integrity_of_faith': 'Целостность веры', 'jobless_level': 'Процент безработицы', 'knowledge_level': 'Уровень образования', 'many_children_propoganda': 'Пропаганда многодетности', 'many_children_traditions': 'Традиции многодетности', 'military_equipment': 'ЗВО', 'panic_level': 'Паника (%)', 'poor_level': 'Процент бедности', 'provinces_count': 'Число провинций', 'provinces_waste': 'Траты на одну провинцию (ед.вал.)', 'salt_security': 'Солевой достаток (%)', 'sexual_asceticism': 'Сексуальный аскетизм', 'state_apparatus_efficiency': 'Эффективность бюрократического аппарата (%)', 'state_apparatus_size': 'Размер бюрократического аппарата (%)', 'unemployment_rate': 'Процент тунеядства', 'violence_tendency': 'Склонность к насилию'}
BASIC_FIELD_NAMES: Dict[str, str] = {'income_from_scientific': 'Доход от научных предприятий (ед.вал.)', 'small_enterprise_percent': 'Процент предпринимателей', 'large_enterprise_count': 'Количество крупных предпринимателей', 'control': 'Контроль (правящая сила, представительство, имеющие силу, автономии)', 'egocentrism_development': 'Эгоцентризм развития', 'grace_of_the_highest': 'Милость Высших'}
ATTERIUM_FIELD_NAMES: Dict[str, str] = {'state_apparatus_functionality': 'Связь Федерации с Республиками (%)', 'small_enterprise_percent': 'Малый бизнес', 'large_enterprise_count': 'Клюпр Цесаркии', 'control': 'Контроль (правящая сила, представительство, имеющие силу, автономии)', 'egocentrism_development': 'БТЗГ', 'capitalistic_decay': 'Капиталистическое разложение', 'equality': 'Равенство (%)', 'grace_of_the_highest': 'Милость Высших'}
ISF_FIELD_NAMES: Dict[str, str] = {'small_enterprise_percent': 'Малый бизнес', 'large_enterprise_count': 'Аристократические и коммерческие дома', 'control': 'Контроль (императорский двор, представительство, Аристократия, автономии)', 'allegory_influence': 'Влияние Аллегории (%)', 'egocentrism_development': 'Эгоцентризм развития', 'imperial_court_power': 'Сила Имперского Двора (%)', 'grace_of_the_silver': 'Милость Серебрянной', 'separatism_of_the_highest': 'Сепаратизм Высших'}

COMMON_REGEX_PATTERNS: Dict[str, Any] = {'commitment_to_cause': 'Собственная Убеждённость Делу - (\\d+)', 'contentment': 'Довольство населения - (\\d+)', 'corruption_level': 'Коррупция - (\\d+)', 'cultural_level': 'Уровень культуры - (\\d+)', 'departure_from_truths': 'Отхождение от истин - (\\d+)', 'erudition_will': 'Стремление к эрудиции - (\\d+)', 'government_trust': 'Доверие властям - ([\\d.]+)', 'integrity_of_faith': 'Целостность веры - (\\d+)', 'jobless_level': 'Процент безработицы - ([\\d.]+)', 'many_children_propoganda': 'Пропаганда многодетности - (\\d+)', 'many_children_traditions': 'Традиции многодетности - (\\d+)', 'military_equipment': 'ЗВО - ([\\d.]+)', 'panic_level': 'Паника - ([\\d.]+)%', 'poor_level': 'Процент бедности - ([\\d.]+)', 'provinces_count': 'Число провинций - (\\d+)', 'provinces_waste': 'Траты на одну - ([\\d.]+) ед\\.вал', 'salt_security': 'Солевой достаток - (\\d+)%', 'sexual_asceticism': 'Сексуальный аскетизм - ([\\d.]+)', 'state_apparatus_efficiency': 'Эффективность - (\\d+)%', 'state_apparatus_size': 'Размер - (\\d+)%', 'unemployment_rate': 'Процент тунеядства - ([\\d.]+)', 'violence_tendency': 'Склонность к насилию - ([\\d.]+)'}
BASIC_REGEX_PATTERNS: Dict[str, Any] = {'knowledge_level': 'Уровень образования - ([\\d.]+)', 'income_from_scientific': 'Доход от научных предприятий - ([\\d.]+) ед\\.вал', 'small_enterprise_percent': 'Процент предпринимателей - ([\\d.]+)', 'large_enterprise_count': 'Количество крупных предпринимателей - (\\d+)', 'control': ['Правящая сила - ([\\d.]+)%', 'Представительство - ([\\d.]+)%', 'Имеющие силу - ([\\d.]+)%', 'Автономии - ([\\d.]+)%'], 'egocentrism_development': 'Эгоцентризм развития - ([\\d.]+)', 'education_level': 'Образованность - ([\\d.]+)', 'grace_of_the_highest': 'Милость Высших - (\\d+)'}
ATTERIUM_REGEX_PATTERNS: Dict[str, Any] = {'state_apparatus_functionality': 'Cвязь Федерации с Республиками - ([\\d.]+)%', 'knowledge_level': 'Уровень образования - (\\d+)', 'small_enterprise_percent': 'Малый бизнес - ([\\d.]+)', 'large_enterprise_count': 'Клюпр Цесаркии - (\\d+)', 'control': ['Правящая сила - ([\\d.]+)%', 'Представительство - ([\\d.]+)%', 'Имеющие силу - ([\\d.]+)%', 'Автономии - ([\\d.]+)%'], 'egocentrism_development': 'БТЗГ - ([\\d.]+)', 'capitalistic_decay': 'Капиталистическое разложение - ([\\d.]+)', 'education_level': 'Образованность - ([\\d.]+)', 'equality': 'Равенство - ([\\d.]+)%', 'grace_of_the_highest': 'Милость Высших - (\\d+)'}
ISF_REGEX_PATTERNS: Dict[str, Any] = {'knowledge_level': 'Уровень образования - (\\d+)', 'small_enterprise_percent': 'Малый бизнес - ([\\d.]+)', 'large_enterprise_count': 'Аристократические и коммерческие дома - (\\d+)', 'allegory_influence': 'Влияние Аллегории - ([\\d.]+)%', 'control': ['Императорский двор - ([\\d.]+)%', 'Представительство - ([\\d.]+)%', 'Аристократия - ([\\d.]+)%', 'Автономии - ([\\d.]+)%'], 'egocentrism_development': 'Эгоцентризм развития - ([\\d.]+)', 'education_level': 'Образованность - (\\d+)', 'imperial_court_power': 'Сила Имперского Двора - ([\\d.]+)%', 'grace_of_the_silver': 'Милость Серебрянной - (\\d+)', 'separatism_of_the_highest': 'Сепаратизм Высших - (\\d+)'}

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
