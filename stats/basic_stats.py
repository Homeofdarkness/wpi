import functools
from typing import List, Dict, Union, Any

import pydantic
from typing_extensions import override

from functions.basic_stats_functions import BasicStatsFunctions
from stats.stats_base import StatsBase


class EconomyStats(StatsBase):
    population_count: int
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    small_enterprise_tax: float
    large_enterprise_tax: float
    gov_wastes: List[float]
    med_wastes: List[float]
    other_wastes: List[float]
    war_wastes: List[float]
    trade_rank: int
    trade_usage: int
    trade_efficiency: int
    trade_wastes: float
    high_quality_percent: float
    mid_quality_percent: float
    low_quality_percent: float
    valgery: float
    allegorization: float
    branches_count: int
    branches_efficiency: float
    tax_income: float = None
    forex: float = None
    trade_income: float = None
    money_income: float = None
    prev_budget: float = None

    @pydantic.model_validator(mode='after')
    def check_trade_sum(self) -> 'EconomyStats':
        goods_percent = self.low_quality_percent + self.mid_quality_percent + self.high_quality_percent
        if abs(goods_percent - 100) > 0.1:
            raise ValueError(
                f"Сумма товаров разных качеств должна быть равна 100, а на деле - {goods_percent}")

        return self

    def __init__(self, **data):
        super().__init__(**data)

        self._income = None
        self._trade_potential = None
        self._branches_income = None

    @property
    def income(self):
        if self._income is not None:
            return self._income

        return round(
            BasicStatsFunctions.calculate_population_growth(
                self.population_count))

    @income.setter
    def income(self, value):
        self._income = value

    @property
    def trade_potential(self):
        if self._trade_potential is not None:
            return self._trade_potential

        return BasicStatsFunctions.calculate_trade_potential(
            self.trade_rank,
            self.trade_efficiency
        )

    @trade_potential.setter
    def trade_potential(self, value):
        self._trade_potential = value

    @property
    def branches_income(self):
        if self._branches_income is not None:
            return self._branches_income

        return BasicStatsFunctions.calculate_branches_income(
            self.branches_count,
            self.branches_efficiency)

    @branches_income.setter
    def branches_income(self, value):
        self._branches_income = value

    @override
    def debug(self):
        result_string = f"""Население-{int(self.population_count)}                  УНЧС - {self.decrement_coefficient}                        Прирост-{round(self.income)}               
Казна- хз               Экономическая стабильность - {self.stability}%                Инфляция - {self.inflation}%
ДОХОДЫ - + хз ед.вал в ход
УН - {self.universal_tax}                    Акцизы - {self.excise}                        Дополнительные средства - +{self.additions} ед.вал
Налог на предпринимательство - {self.small_enterprise_tax}                         Налог на крупных предпринимателей - {self.large_enterprise_tax}
Содержание инфраструктуры - {self.gov_wastes[0]}                                  логистики - {self.gov_wastes[1]}                       
гос.аппарата - {self.gov_wastes[2]}                                                 ресурсодобычи - {self.gov_wastes[3]} 
Траты на образование - {self.med_wastes[0]}               здравоохранение - {self.med_wastes[1]}               охранные учреждения - {self.med_wastes[2]} 
соц.сферу - {self.med_wastes[3]}                                                                     науку - {self.med_wastes[4]}
Субсидирование бизнеса - {self.other_wastes[0]}                           Внешние расходы - {self.other_wastes[1]}                  Оккупация - {self.other_wastes[2]}          
Траты на армию - {self.war_wastes[0]}              военное производство - {self.war_wastes[1]}                  флот - {self.war_wastes[2]} ```

```ТОРГОВЛЯ
Торговый ранг - {self.trade_rank}                                        Торговый потенциал - {round(self.trade_potential)} т.п.
Эффективность торговли - {self.trade_efficiency}%                               Загруженность торговых путей - {round(self.trade_usage / self.trade_potential * 100)}%
Транспортные издержки - {self.trade_wastes} ед.вал.                         Доступные торговые пути - {5 + 3 * (self.trade_rank - 1)}
Процент продаж ресурсов:
Высокого качества - {self.high_quality_percent}%                  Среднего качества - {self.mid_quality_percent}%              Низкого качества - {self.low_quality_percent}%
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - {round(self.forex, 2)}                    
Аллегоризация - {self.allegorization}%                                                   Торговая прибыль - {round(self.trade_income, 3)}   
Количество филиалов - {self.branches_count}                    Эффективность - {self.branches_efficiency}%              Доход - хз```
"""
        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```Население-{int(self.population_count)}                  УНЧС - {self.decrement_coefficient}                        Прирост-{round(self.income)}               
Казна- {"+" if self.current_budget > self.prev_budget else ""}{round(self.current_budget - self.prev_budget, 3)} ({round(self.current_budget, 3)})               Экономическая стабильность - {self.stability}%                Инфляция - {self.inflation}%
ДОХОДЫ - + {round(self.tax_income, 3)} ед.вал в ход
УН - {self.universal_tax}                    Акцизы - {self.excise}                        Дополнительные средства - +{self.additions} ед.вал
Налог на предпринимательство - {self.small_enterprise_tax}                         Налог на крупных предпринимателей - {self.large_enterprise_tax}
Содержание инфраструктуры - {self.gov_wastes[0]}                                  логистики - {self.gov_wastes[1]}                       
гос.аппарата - {self.gov_wastes[2]}                                                 ресурсодобычи - {self.gov_wastes[3]} 
Траты на образование - {self.med_wastes[0]}               здравоохранение - {self.med_wastes[1]}               охранные учреждения - {self.med_wastes[2]} 
соц.сферу - {self.med_wastes[3]}                                                                     науку - {self.med_wastes[4]}
Субсидирование бизнеса - {self.other_wastes[0]}                           Внешние расходы - {self.other_wastes[1]}                  Оккупация - {self.other_wastes[2]}             
Траты на армию - {self.war_wastes[0]}              военное производство - {self.war_wastes[1]}                  флот - {self.war_wastes[2]} ```

```ТОРГОВЛЯ
Торговый ранг - {self.trade_rank}                                        Торговый потенциал - {round(self.trade_potential)} т.п.
Эффективность торговли - {self.trade_efficiency}%                               Загруженность торговых путей - {round(self.trade_usage / self.trade_potential * 100)}%
Транспортные издержки - {self.trade_wastes} ед.вал.                         Доступные торговые пути - {5 + 3 * (self.trade_rank - 1)}
Процент продаж ресурсов:
Высокого качества - {self.high_quality_percent}%                  Среднего качества - {self.mid_quality_percent}%              Низкого качества - {self.low_quality_percent}%
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - {round(self.forex, 2)}                    
Аллегоризация - {self.allegorization}%                                                   Торговая прибыль - {round(self.trade_income, 3)}   
Количество филиалов - {self.branches_count}                                Эффективность - {self.branches_efficiency}%              Доход - {self.branches_income}```
"""

        return result_string

    @staticmethod
    @override
    def _get_field_groups():
        from stats.schemas.economy_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names():
        from stats.schemas.economy_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.economy_schema import build_regex_patterns
        return build_regex_patterns("basic")


class IndustrialStats(StatsBase):
    processing_production: float = pydantic.Field(..., ge=0, le=100)
    processing_usage: float = pydantic.Field(..., ge=0, le=100)
    processing_efficiency: float = pydantic.Field(..., ge=0, le=100)
    usages: List[float]
    civil_security: float = pydantic.Field(..., ge=0, le=100)
    standardization: float = pydantic.Field(..., ge=0, le=100)
    logistic: float = pydantic.Field(..., ge=0, le=100)
    tvr1: int = pydantic.Field(..., ge=0, le=100)
    tvr2: int = pydantic.Field(..., ge=0, le=100)
    overproduction_coefficient: float = pydantic.Field(..., ge=0, le=100)
    war_production_efficiency: float = pydantic.Field(..., ge=0, le=100)
    industry_income: float = 0
    consumption_of_goods: float = 0

    def __init__(self, **data):
        super().__init__(**data)

        self._civil_usage = None
        self._industry_coefficient = None
        self._civil_efficiency = None
        self._max_potential = None
        self._expected_wastes = None

    @property
    def civil_usage(self):
        if self._civil_usage is not None:
            return self._civil_usage

        return BasicStatsFunctions.calculate_civil_usage(
            self.civil_security,
            self.tvr1, self.tvr2)

    @civil_usage.setter
    def civil_usage(self, value):
        self._civil_usage = value

    @property
    def industry_coefficient(self):
        if self._industry_coefficient is not None:
            return self._industry_coefficient

        return BasicStatsFunctions.calculate_industry_coefficient(
            self.processing_production,
            self.processing_usage,
            self.processing_efficiency,
            sum(self.usages) // len(self.usages)
        )

    @industry_coefficient.setter
    def industry_coefficient(self, value):
        self._industry_coefficient = value

    @functools.cached_property
    def industry_basic_stats(self):
        return BasicStatsFunctions.calculate_industry_basic_stats(
            self.industry_coefficient, self.civil_usage, self.standardization)

    @property
    def civil_efficiency(self):
        if self._civil_efficiency is not None:
            return self._civil_efficiency

        return self.industry_basic_stats[
            0] * BasicStatsFunctions.calculate_civil_efficiency_boost_from_logistic(
            self.logistic)

    @civil_efficiency.setter
    def civil_efficiency(self, value):
        self._civil_efficiency = value

    @property
    def max_potential(self):
        if self._max_potential is not None:
            return self._max_potential

        return self.industry_basic_stats[1]

    @max_potential.setter
    def max_potential(self, value):
        self._max_potential = value

    @property
    def expected_wastes(self):
        if self._expected_wastes is not None:
            return self._expected_wastes

        return self.industry_basic_stats[2]

    @expected_wastes.setter
    def expected_wastes(self, value):
        self._expected_wastes = value

    @override
    def debug(self) -> str:
        result_string = f"""```ПРОМЫШЛЕННОСТЬ 
Перерабатывающая - 
Процент производства - {self.processing_production}%            Процент использования - {self.processing_usage}%          Эффективность добычи - {self.processing_efficiency}%                     
Обеспеченности:
Cобственной ресурсной базой - {self.usages[0]}%                             Сырьем - {self.usages[1]}%  
Предприятий рабочими - {self.usages[2]}%                                          Квалификация рабочих - {self.usages[3]}%        
Коэффициент производительности - {round(self.industry_coefficient, 3)} 
Гражданская - 
Обеспеченность сырьем - {self.civil_security}%         Стандартизация - {self.standardization}%           Логистика предприятий - {self.logistic}% 
Обеспеченность ТЖН - {self.tvr1}               Обеспеченность ТНП - {self.tvr2}            Потребление товаров - {self.consumption_of_goods}%
Эффективность производства - {round(self.civil_efficiency, 2)}%            Ожидаемые траты - {round(self.expected_wastes, 3)} ед.вал.            Процент перепроизводства - {self.overproduction_coefficient}%
Максимальный потенциал использования - {round(self.max_potential, 2)}%        Процент использования - {self.civil_usage}%       ПСС - {round(self.industry_income, 2)} ед.вал.
Военная - 
Эффективность военного производства - {self.war_production_efficiency}%```
"""

        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```ПРОМЫШЛЕННОСТЬ 
Перерабатывающая - 
Процент производства - {self.processing_production}%            Процент использования - {self.processing_usage}%          Эффективность добычи - {self.processing_efficiency}%                     
Обеспеченности:
Cобственной ресурсной базой - {self.usages[0]}%                             Сырьем - {self.usages[1]}%  
Предприятий рабочими - {self.usages[2]}%                                          Квалификация рабочих - {self.usages[3]}%        
Коэффициент производительности - {round(self.industry_coefficient, 3)} 
Гражданская - 
Обеспеченность сырьем - {self.civil_security}%         Стандартизация - {self.standardization}%           Логистика предприятий - {self.logistic}% 
Обеспеченность ТЖН - {self.tvr1}               Обеспеченность ТНП - {self.tvr2}            Потребление товаров - {self.consumption_of_goods}%
Эффективность производства - {round(self.civil_efficiency, 2)}%            Ожидаемые траты - {round(self.expected_wastes, 3)} ед.вал.            Процент перепроизводства - {self.overproduction_coefficient}%
Максимальный потенциал использования - {round(self.max_potential, 2)}%        Процент использования - {self.civil_usage}%       ПСС - {round(self.industry_income, 2)} ед.вал.
Военная - 
Эффективность военного производства - {self.war_production_efficiency}%```
"""

        return result_string

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        return {
            "Перерабатывающая промышленность": [
                'processing_production', 'processing_usage',
                'processing_efficiency'
            ],
            "Обеспеченность": [
                'usages'
            ],
            "Гражданская промышленность": [
                'civil_security', 'standardization', 'logistic',
                'tvr1', 'tvr2', 'overproduction_coefficient'
            ],
            "Военная промышленность": [
                'war_production_efficiency'
            ]
        }

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        return {
            'processing_production': 'Процент производства (%)',
            'processing_usage': 'Процент использования (%)',
            'processing_efficiency': 'Эффективность добычи (%)',
            'usages': 'Обеспеченность (ресурсная база, рабочие, сырье, квалификация)',
            'civil_security': 'Обеспеченность сырьем (%)',
            'standardization': 'Стандартизация (%)',
            'logistic': 'Логистика предприятий (%)',
            'tvr1': 'Обеспеченность ТЖН',
            'tvr2': 'Обеспеченность ТНП',
            'overproduction_coefficient': 'Процент перепроизводства (%)',
            'war_production_efficiency': 'Эффективность военного производства (%)',
            'industry_income': 'ПСС (ед.вал.)',
            'consumption_of_goods': 'Потребление товаров (%)'
        }

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        return {
            'processing_production': r'Процент производства - ([\d.]+)%',
            'processing_usage': r'Процент использования - ([\d.]+)%',
            'processing_efficiency': r'Эффективность добычи - ([\d.]+)%',
            'usages': [
                r'Cобственной ресурсной базой - ([\d.]+)%',
                r'Предприятий рабочими - ([\d.]+)%',
                r'Сырьем - ([\d.]+)%',
                r'Квалификация рабочих - ([\d.]+)%'
            ],
            'civil_security': r'Обеспеченность сырьем - ([\d.]+)%',
            'standardization': r'Стандартизация - ([\d.]+)%',
            'logistic': r'Логистика предприятий - ([\d.]+)%',
            'tvr1': r'Обеспеченность ТЖН - (\d+)',
            'tvr2': r'Обеспеченность ТНП - (\d+)',
            'overproduction_coefficient': r'Процент перепроизводства - ([\d.]+)%',
            'war_production_efficiency': r'Эффективность военного производства - ([\d.]+)%',
            'industry_income': r'ПСС - ([\d.]+) ед\.вал',
            'consumption_of_goods': r'Потребление товаров - ([\d.]+)%'
        }


class InnerPoliticsStats(StatsBase):
    state_apparatus_size: int
    state_apparatus_efficiency: int
    knowledge_level: float
    many_children_propoganda: int
    integrity_of_faith: int
    corruption_level: int
    salt_security: int
    poor_level: float
    jobless_level: float
    income_from_scientific: float
    small_enterprise_percent: float
    large_enterprise_count: int
    provinces_count: int
    provinces_waste: float
    military_equipment: float
    control: list
    contentment: int
    government_trust: float
    many_children_traditions: int
    sexual_asceticism: float
    egocentrism_development: float
    education_level: float
    erudition_will: int
    cultural_level: int
    violence_tendency: float
    panic_level: float
    unemployment_rate: float
    grace_of_the_highest: int
    commitment_to_cause: int
    departure_from_truths: int

    def __init__(self, **data):
        super().__init__(**data)

        self._success_chance = None
        self._society_decline = None

    @property
    def success_chance(self):
        if self._success_chance is not None:
            return self._success_chance

        return round(
            BasicStatsFunctions.calculate_success_chance(self.knowledge_level,
                                                         self.education_level,
                                                         self.erudition_will))

    @success_chance.setter
    def success_chance(self, value):
        self._success_chance = value

    @property
    def society_decline(self):
        if self._society_decline is not None:
            return self._society_decline

        return BasicStatsFunctions.calculate_society_decline(
            self.contentment, self.government_trust,
            self.many_children_traditions,
            self.sexual_asceticism,
            self.egocentrism_development,
            self.education_level, self.erudition_will,
            self.cultural_level, self.violence_tendency,
            self.unemployment_rate,
            self.grace_of_the_highest,
            self.commitment_to_cause,
            self.departure_from_truths
        )

    @society_decline.setter
    def society_decline(self, value):
        self._society_decline = value

    @override
    def debug(self) -> str:
        result_string = f"""```ГОСУДАРСТВО
Бюрократический аппарат          Размер - {self.state_apparatus_size}%                     Эффективность - {self.state_apparatus_efficiency}%
Уровень образованности - {self.knowledge_level}            Шанс на успех - {self.success_chance}%       Пропаганда многодетности - {self.many_children_propoganda}   
Целостность веры - {self.integrity_of_faith}               Коррупция - {self.corruption_level}             Солевой достаток - {self.salt_security}% 
Процент бедности - {self.poor_level}                              Процент безработицы - {self.jobless_level}  
Процент предпринимателей - {self.small_enterprise_percent}                       Количество крупных предпринимателей - {self.large_enterprise_count}
Число провинций - {self.provinces_count}                   Траты на одну - {self.provinces_waste} ед.вал                       ЗВО - {self.military_equipment}
КОНТРОЛЬ
Правящая сила - {self.control[0]}%         Представительство - {self.control[1]}%               Имеющие силу - {self.control[2]}%             Автономии - {self.control[3]}%```

```НАРОД
Довольство населения - {self.contentment}                                      Доверие властям - {self.government_trust}  
Традиции многодетности - {self.many_children_traditions}         Сексуальный аскетизм - {self.sexual_asceticism}            Эгоцентризм развития - {self.egocentrism_development}
Образованность - {self.education_level}                                             Стремление к эрудиции - {self.erudition_will}    
Уровень культуры - {self.cultural_level}                           Склонность к насилию - {self.violence_tendency}             
Упадок общества - {self.society_decline}%                                                Процент тунеядства - {self.unemployment_rate}
Милость Высших - {self.grace_of_the_highest}             Собственная Убеждённость Делу - {self.commitment_to_cause}          Отхождение от истин - {self.departure_from_truths} ```
"""

        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```ГОСУДАРСТВО
Бюрократический аппарат          Размер - {self.state_apparatus_size}%                     Эффективность - {self.state_apparatus_efficiency}%
Уровень образования - {self.knowledge_level}            Шанс на успех - {self.success_chance}%       Пропаганда многодетности - {self.many_children_propoganda}   
Целостность веры - {self.integrity_of_faith}               Коррупция - {self.corruption_level}             Солевой достаток - {self.salt_security}% 
Процент бедности - {self.poor_level}       Процент безработицы - {self.jobless_level}      Доход от научных предприятий - {self.income_from_scientific} ед.вал.
Процент предпринимателей - {self.small_enterprise_percent}                       Количество крупных предпринимателей - {self.large_enterprise_count}
Число провинций - {self.provinces_count}                   Траты на одну - {self.provinces_waste} ед.вал                       ЗВО - {self.military_equipment}
КОНТРОЛЬ
Правящая сила - {self.control[0]}%         Представительство - {self.control[1]}%               Имеющие силу - {self.control[2]}%             Автономии - {self.control[3]}%```

```НАРОД
Довольство населения - {self.contentment}                                      Доверие властям - {self.government_trust}  
Традиции многодетности - {self.many_children_traditions}         Сексуальный аскетизм - {self.sexual_asceticism}            Эгоцентризм развития - {self.egocentrism_development}
Образованность - {round(self.education_level, 3)}                                             Стремление к эрудиции - {self.erudition_will}    
Уровень культуры - {self.cultural_level}          Склонность к насилию - {self.violence_tendency}           Паника - {self.panic_level}%  
Упадок общества - {self.society_decline}%                                                Процент тунеядства - {self.unemployment_rate}
Милость Высших - {self.grace_of_the_highest}             Собственная Убеждённость Делу - {self.commitment_to_cause}          Отхождение от истин - {self.departure_from_truths} ```
"""

        return result_string

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.inner_politics_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.inner_politics_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.inner_politics_schema import build_regex_patterns
        return build_regex_patterns("basic")


class AgricultureStats(StatsBase):
    husbandry: float
    livestock: float
    others: float
    biome_richness: float
    overprotective_effects: int
    securities: list
    workers_redistribution: int
    storages_upkeep: float
    consumption_factor: float
    agriculture_wastes: float
    agriculture_deceases: float
    agriculture_natural_deceases: float
    income_from_resources: float
    overstock_percent: float

    # Semi-dynamic param
    food_supplies: float = 0

    # Dynamic params (calculated in skip-move)
    expected_wastes: float = None
    food_security: float = None
    food_diversity: float = None
    agriculture_efficiency: float = None
    agriculture_development: float = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)

        # Negative impact on _food_security
        self.is_negative_food_security = False

    @override
    def debug(self) -> str:
        result_string = f"""```СЕЛЬСКОЕ ХОЗЯЙСТВО
Распределение отраслей - 
Земледелие - {self.husbandry}%                        Животноводство - {self.livestock}%                    Рыболовство - {self.others}%
Богатство биомов - {self.biome_richness}%                                    Эффекты от сверхплодородных земель - {self.overprotective_effects}   
Обеспеченности:
Рабочими - {self.securities[0]}%      Технологиями возделывания - {self.securities[1]}%      Удобрениями, средствами - {self.securities[2]}%                Орудия труда - {self.securities[3]}%
Рабочее перераспределение - {self.workers_redistribution}%                  Содержание хранилищ (1 к 39) - {round(self.storages_upkeep, 3)} ед.вал.              Коэффициент потребления - {self.consumption_factor}%
Ожидаемые траты - {round(self.expected_wastes, 3)} ед.вал.         Траты - {self.agriculture_wastes} ед.вал.                 Обеспеченность едой - хз%
Хвори сельхоза - {self.agriculture_deceases}%                   Ненастья и естественные проблемы сельхоза - {self.agriculture_natural_deceases}%                                              
Доход от редкой и дорогой еды - {self.income_from_resources} ед.вал                        Пищевое разнообразие - {self.food_diversity}%            Изъять из потребления - {self.overstock_percent}%
Эффективность сельского хозяйства - хз                    Развитость сельского хозяйства - хз%                            Запасы пищи - хз```
"""

        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```СЕЛЬСКОЕ ХОЗЯЙСТВО
Распределение отраслей - 
Земледелие - {self.husbandry}%                        Животноводство - {self.livestock}%                    Рыболовство - {self.others}%
Богатство биомов - {self.biome_richness}%                                    Эффекты от сверхплодородных земель - {self.overprotective_effects}   
Обеспеченности:
Рабочими - {self.securities[0]}%      Технологиями возделывания - {self.securities[1]}%      Удобрениями, средствами - {self.securities[2]}%                Орудия труда - {self.securities[3]}%
Рабочее перераспределение - {self.workers_redistribution}%                  Содержание хранилищ (1 к 39) - {round(self.storages_upkeep, 3)} ед.вал.              Коэффициент потребления - {self.consumption_factor}%
Ожидаемые траты - {round(self.expected_wastes, 3)} ед.вал.         Траты - {self.agriculture_wastes} ед.вал.                 Обеспеченность едой - {"!" if self.is_negative_food_security else ""}{round(self.food_security, 3)}%
Хвори сельхоза - {self.agriculture_deceases}%                   Ненастья и естественные проблемы сельхоза - {self.agriculture_natural_deceases}%                                              
Доход от редкой и дорогой еды - {self.income_from_resources} ед.вал                        Пищевое разнообразие - {self.food_diversity}%            Изъять из потребления - {self.overstock_percent}%
Эффективность сельского хозяйства - {round(self.agriculture_efficiency)}%                    Развитость сельского хозяйства - {round(self.agriculture_development, 2)}%                     Запасы пищи - {round(self.food_supplies, 2)}```
"""

        return result_string

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.agriculture_schema import build_field_groups
        return build_field_groups("basic")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.agriculture_schema import build_field_names
        return build_field_names("basic")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.agriculture_schema import build_regex_patterns
        return build_regex_patterns("basic")
