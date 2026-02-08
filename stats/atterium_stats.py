from typing import List, Tuple, Dict, Union

import pydantic
from typing_extensions import override

from functions.atterium_stats_functions import AtteriumStatsFunctions
from functions.basic_stats_functions import BasicStatsFunctions
from stats.basic_stats import IndustrialStats
from stats.stats_base import StatsBase


class AtteriumEconomyStats(StatsBase):
    population_count: int
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    freedom_and_efficiency_of_small_business: float
    investment_of_large_companies: float
    plan_efficiency: float = pydantic.Field(..., ge=0, le=100)
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
    adrian_effect: float
    power_of_economic_formation: float
    tax_income: float = None
    forex: float = None
    trade_income: float = None
    money_income: float = None
    prev_budget: float = None

    @pydantic.model_validator(mode='after')
    def check_trade_sum(self) -> 'AtteriumEconomyStats':
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
        return round(BasicStatsFunctions.calculate_population_growth(
            self.population_count))

    @income.setter
    def income(self, value):
        self._income = value

    @property
    def trade_potential(self):
        if self._trade_potential is not None:
            return self._trade_potential
        return BasicStatsFunctions.calculate_trade_potential(self.trade_rank,
                                                             self.trade_efficiency)

    @trade_potential.setter
    def trade_potential(self, value):
        self._trade_potential = value

    @property
    def branches_income(self):
        if self._branches_income is not None:
            return self._branches_income
        return BasicStatsFunctions.calculate_branches_income(
            self.branches_count, self.branches_efficiency)

    @branches_income.setter
    def branches_income(self, value):
        self._branches_income = value

    @override
    def debug(self):
        result_string = f"""Население-{int(self.population_count)}                  УНЧС - {self.decrement_coefficient}                        Прирост-{round(self.income)}               
Казна- хз               Экономическая стабильность - {self.stability}%                Инфляция - {self.inflation}%
ДОХОДЫ - + хз ед.вал в ход
УН - {self.universal_tax}                    Акцизы - {self.excise}                        Дополнительные средства - +{self.additions} ед.вал
СиРМБ - {self.freedom_and_efficiency_of_small_business}                         Вложения крупных компаний - {self.investment_of_large_companies}
Эфисп приказов Цесаркии - {self.plan_efficiency}%
Содержание инфраструктуры - {self.gov_wastes[0]}                                  логистики - {self.gov_wastes[1]}                       
федеративное - {self.gov_wastes[2]}                 республиканское - {self.gov_wastes[3]}                                   ресурсодобычи - {self.gov_wastes[4]} 
Траты на образование - {self.med_wastes[0]}               здравоохранение - {self.med_wastes[1]}               охранные учреждения - {self.med_wastes[2]} 
соц.сферу - {self.med_wastes[3]}                                                                     науку - {self.med_wastes[4]}
Внешние расходы - {self.other_wastes[0]}                                               Оккупация - {self.other_wastes[1]}                 
Траты на армию - {self.war_wastes[0]}              военное производство - {self.war_wastes[1]}                  флот - {self.war_wastes[2]} ```

```ТОРГОВЛЯ
Торговый ранг - {self.trade_rank}                                        Торговый потенциал - {round(self.trade_potential)} т.п.
Эффективность торговли - {self.trade_efficiency}%                               Загруженность торговых путей - {round(self.trade_usage / self.trade_potential * 100)}%
Транспортные издержки - {self.trade_wastes} ед.вал.                         Доступные торговые пути - {5 + 3 * (self.trade_rank - 1)}
Процент продаж ресурсов:
Высокого качества - {self.high_quality_percent}%                  Среднего качества - {self.mid_quality_percent}%              Низкого качества - {self.low_quality_percent}%
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - {round(self.forex, 2)}                    
Аллегоризация - {self.allegorization}%                                                   Торговая прибыль - {round(self.trade_income, 3)}   
Количество филиалов - {self.branches_count}           Эффективность - {self.branches_efficiency}%              Доход - хз
Эффект Адриана (Рантье) - {self.adrian_effect}                                           Сила СЭЗ - {self.power_of_economic_formation}
```
"""
        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```Население-{int(self.population_count)}                  УНЧС - {self.decrement_coefficient}                        Прирост-{round(self.income)}               
Казна- {"+" if self.current_budget > self.prev_budget else ""}{round(self.current_budget - self.prev_budget, 3)} ({round(self.current_budget, 3)})               Экономическая стабильность - {self.stability}%                Инфляция - {self.inflation}%
ДОХОДЫ - + {round(self.tax_income, 3)} ед.вал в ход
УН - {self.universal_tax}                    Акцизы - {self.excise}                        Дополнительные средства - +{self.additions} ед.вал
СиРМБ - {self.freedom_and_efficiency_of_small_business}                         Вложения крупных компаний - {self.investment_of_large_companies}
Эфисп приказов Цесаркии - {self.plan_efficiency}%
Содержание инфраструктуры - {self.gov_wastes[0]}                                  логистики - {self.gov_wastes[1]}                       
федеративное - {self.gov_wastes[2]}                 республиканское - {self.gov_wastes[3]}                                   ресурсодобычи - {self.gov_wastes[4]} 
Траты на образование - {self.med_wastes[0]}               здравоохранение - {self.med_wastes[1]}               охранные учреждения - {self.med_wastes[2]} 
соц.сферу - {self.med_wastes[3]}                                                                     науку - {self.med_wastes[4]}
Внешние расходы - {self.other_wastes[0]}                                               Оккупация - {self.other_wastes[1]}       
Траты на армию - {self.war_wastes[0]}              военное производство - {self.war_wastes[1]}                  флот - {self.war_wastes[2]} ```

```ТОРГОВЛЯ
Торговый ранг - {self.trade_rank}                                        Торговый потенциал - {round(self.trade_potential)} т.п.
Эффективность торговли - {self.trade_efficiency}%                               Загруженность торговых путей - {round(self.trade_usage / self.trade_potential * 100)}%
Транспортные издержки - {self.trade_wastes} ед.вал.                         Доступные торговые пути - {5 + 3 * (self.trade_rank - 1)}
Процент продаж ресурсов:
Высокого качества - {self.high_quality_percent}%                  Среднего качества - {self.mid_quality_percent}%              Низкого качества - {self.low_quality_percent}%
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - {round(self.forex, 2)}                    
Аллегоризация - {self.allegorization}%                                                   Торговая прибыль - {round(self.trade_income, 3)}   
Количество филиалов - {self.branches_count}             Эффективность - {self.branches_efficiency}%              Доход - {self.branches_income}
Эффект Адриана (Рантье) - {self.adrian_effect}                                           Сила СЭЗ - {self.power_of_economic_formation}
```
"""
        return result_string

    @staticmethod
    @override
    def _get_field_groups():
        from stats.schemas.economy_schema import build_field_groups
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names():
        from stats.schemas.economy_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.economy_schema import build_regex_patterns
        return build_regex_patterns("atterium")

class AtteriumIndustrialStats(IndustrialStats):
    """Механики одинаковые и слава Богу """
    pass


class AtteriumAgricultureStats(StatsBase):
    husbandry: float
    livestock: float
    others: float
    biome_richness: float
    overprotective_effects: int
    securities: List[float]
    agriculture_wastes: float
    agriculture_deceases: float
    agriculture_natural_deceases: float
    income_from_resources: float
    food_diversity: float
    expected_wastes: float = None

    def __init__(self, **data):
        super().__init__(**data)
        self._food_security = None
        self._agriculture_efficiency = None
        self._agriculture_development = None

    @property
    def food_security(self):
        if self._food_security is not None:
            return self._food_security
        return round(BasicStatsFunctions.calculate_approximate_food_security(
            self.biome_richness, self.overprotective_effects, self.securities))

    @food_security.setter
    def food_security(self, value):
        self._food_security = value

    @property
    def agriculture_efficiency(self):
        if self._agriculture_efficiency is not None:
            return self._agriculture_efficiency
        return BasicStatsFunctions.calculate_approximate_agriculture_efficiency(
            self.securities)

    @agriculture_efficiency.setter
    def agriculture_efficiency(self, value):
        self._agriculture_efficiency = value

    @property
    def agriculture_development(self):
        if self._agriculture_development is not None:
            return self._agriculture_development
        return BasicStatsFunctions.calculate_agriculture_development(
            self.food_security, self.securities)

    @agriculture_development.setter
    def agriculture_development(self, value):
        self._agriculture_development = value

    @override
    def debug(self) -> str:
        result_string = f"""```СЕЛЬСКОЕ ХОЗЯЙСТВО
Распределение отраслей - 
Земледелие - {self.husbandry}%                        Животноводство - {self.livestock}%                    Иное - {self.others}%
Богатство биомов - {self.biome_richness}%                                    Эффекты от сверхплодородных земель - {self.overprotective_effects}   
Обеспеченности:
Рабочими - {self.securities[0]}%      Технологиями возделывания - {self.securities[1]}%      Удобрениями, средствами, орудиями труда - {self.securities[2]}%
Ожидаемые траты - хз ед.вал.         Траты - {self.agriculture_wastes} ед.вал.                 Обеспеченность едой - хз%
Хвори сельхоза - {self.agriculture_deceases}%                   Ненастья и естественные проблемы сельхоза - {self.agriculture_natural_deceases}%                                              
Доход от редкой и дорогой еды - {self.income_from_resources} ед.вал                  Пищевое разнообразие - {self.food_diversity}% 
Эффективность сельского хозяйства - хз%                    Развитость сельского хозяйства - хз% ```
"""
        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```СЕЛЬСКОЕ ХОЗЯЙСТВО
Распределение отраслей - 
Земледелие - {self.husbandry}%                        Животноводство - {self.livestock}%                    Иное - {self.others}%
Богатство биомов - {self.biome_richness}%                                    Эффекты от сверхплодородных земель - {self.overprotective_effects}   
Обеспеченности:
Рабочими - {self.securities[0]}%      Технологиями возделывания - {self.securities[1]}%      Удобрениями, средствами, орудиями труда - {self.securities[2]}%
Ожидаемые траты - {round(self.expected_wastes, 3)} ед.вал.         Траты - {self.agriculture_wastes} ед.вал.                 Обеспеченность едой - {round(self.food_security, 3)}% 
Хвори сельхоза - {self.agriculture_deceases}%                   Ненастья и естественные проблемы сельхоза - {self.agriculture_natural_deceases}%                                              
Доход от редкой и дорогой еды - {self.income_from_resources} ед.вал                  Пищевое разнообразие - {self.food_diversity}% 
Эффективность сельского хозяйства - {round(self.agriculture_efficiency)}%                    Развитость сельского хозяйства - {round(self.agriculture_development, 2)}% ```
"""
        return result_string

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.agriculture_schema import build_field_groups
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.agriculture_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.agriculture_schema import build_regex_patterns
        return build_regex_patterns("atterium")

class AtteriumInnerPoliticsStats(StatsBase):
    state_apparatus_functionality: float
    state_apparatus_size: int
    state_apparatus_efficiency: int
    knowledge_level: int
    many_children_propoganda: int
    integrity_of_faith: int
    corruption_level: int
    salt_security: int
    poor_level: float
    jobless_level: float
    small_enterprise_percent: float
    large_enterprise_count: int
    provinces_count: int
    provinces_waste: float
    military_equipment: float
    control: List[float]
    contentment: int
    government_trust: float
    many_children_traditions: int
    sexual_asceticism: float
    egocentrism_development: float
    capitalistic_decay: float
    education_level: int
    erudition_will: int
    cultural_level: int
    violence_tendency: float
    panic_level: float
    unemployment_rate: float
    equality: float
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
        return round(BasicStatsFunctions.calculate_success_chance(
            self.knowledge_level, self.education_level, self.erudition_will))

    @success_chance.setter
    def success_chance(self, value):
        self._success_chance = value

    @property
    def society_decline(self):
        if self._society_decline is not None:
            return self._society_decline
        return AtteriumStatsFunctions.calculate_society_decline(
            self.contentment, self.government_trust,
            self.many_children_traditions, self.sexual_asceticism,
            self.egocentrism_development, self.capitalistic_decay,
            self.education_level, self.erudition_will,
            self.cultural_level, self.violence_tendency,
            self.unemployment_rate, self.grace_of_the_highest,
            self.commitment_to_cause, self.departure_from_truths,
            self.equality
        )

    @society_decline.setter
    def society_decline(self, value):
        self._society_decline = value

    @override
    def debug(self) -> str:
        result_string = f"""```ГОСУДАРСТВО
Cвязь Федерации с Республиками - {self.state_apparatus_functionality}%
Бюрократический аппарат          Размер - {self.state_apparatus_size}%                     Эффективность - {self.state_apparatus_efficiency}%
Уровень образованности - {self.knowledge_level}            Шанс на успех - {self.success_chance}%       Пропаганда многодетности - {self.many_children_propoganda}   
Целостность веры - {self.integrity_of_faith}               Коррупция - {self.corruption_level}             Солевой достаток - {self.salt_security}% 
Процент бедности - {self.poor_level}                              Процент безработицы - {self.jobless_level}  
Малый бизнес - {self.small_enterprise_percent}                            Клюпр Цесаркии - {self.large_enterprise_count}
Число провинций - {self.provinces_count}                   Траты на одну - {self.provinces_waste} ед.вал                       ЗВО - {self.military_equipment}
КОНТРОЛЬ
Правящая сила - {self.control[0]}%         Представительство - {self.control[1]}%               Имеющие силу - {self.control[2]}%             Автономии - {self.control[3]}%```

```НАРОД
Довольство населения - {self.contentment}                                      Доверие властям - {self.government_trust}  
Традиции многодетности - {self.many_children_traditions}         Сексуальный аскетизм - {self.sexual_asceticism}            
БТЗГ - {self.egocentrism_development}                       Капиталистическое разложение - {self.capitalistic_decay}
Образованность - {self.education_level}                                             Стремление к эрудиции - {self.erudition_will}    
Уровень культуры - {self.cultural_level}          Склонность к насилию - {self.violence_tendency}           Паника - {self.panic_level}%  
Упадок общества - {self.society_decline}%                                                Процент тунеядства - {self.unemployment_rate}
Равенство - {self.equality}%  
Милость Высших - {self.grace_of_the_highest}             Собственная Убеждённость Делу - {self.commitment_to_cause}          Отхождение от истин - {self.departure_from_truths} ```
"""
        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```ГОСУДАРСТВО
Cвязь Федерации с Республиками - {self.state_apparatus_functionality}%
Бюрократический аппарат          Размер - {self.state_apparatus_size}%                     Эффективность - {self.state_apparatus_efficiency}%
Уровень образования - {self.knowledge_level}            Шанс на успех - {self.success_chance}%       Пропаганда многодетности - {self.many_children_propoganda}   
Целостность веры - {self.integrity_of_faith}               Коррупция - {self.corruption_level}             Солевой достаток - {self.salt_security}% 
Процент бедности - {self.poor_level}                                                   Процент безработицы - {self.jobless_level}
Малый бизнес - {self.small_enterprise_percent}                               Клюпр Цесаркии - {self.large_enterprise_count}
Число провинций - {self.provinces_count}                   Траты на одну - {self.provinces_waste} ед.вал                       ЗВО - {self.military_equipment}
КОНТРОЛЬ
Правящая сила - {self.control[0]}%         Представительство - {self.control[1]}%               Имеющие силу - {self.control[2]}%             Автономии - {self.control[3]}%```

```НАРОД
Довольство населения - {self.contentment}                                      Доверие властям - {self.government_trust}  
Традиции многодетности - {self.many_children_traditions}         Сексуальный аскетизм - {self.sexual_asceticism}            
БТЗГ - {self.egocentrism_development}                       Капиталистическое разложение - {self.capitalistic_decay}
Образованность - {round(self.education_level, 3)}                                             Стремление к эрудиции - {self.erudition_will}    
Уровень культуры - {self.cultural_level}          Склонность к насилию - {self.violence_tendency}           Паника - {self.panic_level}%  
Упадок общества - {self.society_decline}%                                                Процент тунеядства - {self.unemployment_rate}
Равенство - {self.equality}%  
Милость Высших - {self.grace_of_the_highest}             Собственная Убеждённость Делу - {self.commitment_to_cause}          Отхождение от истин - {self.departure_from_truths} ```
"""
        return result_string

    @staticmethod
    @override
    def _get_field_groups() -> Dict[str, List[str]]:
        from stats.schemas.inner_politics_schema import build_field_groups
        return build_field_groups("atterium")

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        from stats.schemas.inner_politics_schema import build_field_names
        return build_field_names("atterium")

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        from stats.schemas.inner_politics_schema import build_regex_patterns
        return build_regex_patterns("atterium")

