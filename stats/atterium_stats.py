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
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - хз                    Торговая прибыль - хз
Количество филиалов - {self.branches_count}           Эффективность - {self.branches_efficiency}%              Доход - хз
Эффект Адриана (Рантье) - {self.adrian_effect}                                           Сила СЭЗ - {self.power_of_economic_formation}
```
"""
        return result_string

    @override
    def __str__(self) -> str:
        result_string = f"""```Население-{int(self.population_count)}                  УНЧС - {self.decrement_coefficient}                        Прирост-{round(self.income)}               
Казна- {"-" if round(self.current_budget - self.prev_budget) < 0 else "+"}{round(self.current_budget - self.prev_budget, 3)} ({round(self.current_budget, 3)})               Экономическая стабильность - {self.stability}%                Инфляция - {self.inflation}%
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
Число используемых торговых путей - {self.trade_usage}       Вальжерия - {self.valgery}%         Курс валюты - {round(self.forex, 2)}                    Торговая прибыль - {round(self.trade_income, 3)}
Количество филиалов - {self.branches_count}           Эффективность - {self.branches_efficiency}%              Доход - {self.branches_income}
Эффект Адриана (Рантье) - {self.adrian_effect}                                           Сила СЭЗ - {self.power_of_economic_formation}
```
"""
        return result_string

    @staticmethod
    @override
    def _get_field_groups():
        return {
            "Основные параметры": [
                'population_count', 'decrement_coefficient', 'current_budget',
                'stability', 'inflation'
            ],
            "Налоги и доходы": [
                'universal_tax', 'excise', 'additions',
                'freedom_and_efficiency_of_small_business',
                'investment_of_large_companies',
                'plan_efficiency'
            ],
            "Расходы": [
                'gov_wastes', 'med_wastes', 'war_wastes', 'other_wastes'
            ],
            "Торговля": [
                'trade_rank', 'trade_usage', 'trade_efficiency',
                'trade_wastes',
                'high_quality_percent', 'mid_quality_percent',
                'low_quality_percent',
                'valgery', 'branches_count', 'branches_efficiency',
                'adrian_effect', 'power_of_economic_formation'
            ]
        }

    @staticmethod
    @override
    def _get_field_names():
        return {
            'population_count': 'Население',
            'decrement_coefficient': 'УНЧС (0-5)',
            'current_budget': 'Текущий размер казны',
            'stability': 'Экономическая стабильность (%)',
            'inflation': 'Инфляция (%)',
            'universal_tax': 'УН',
            'excise': 'Акцизы',
            'additions': 'Дополнительные средства',
            'freedom_and_efficiency_of_small_business': 'СиРМБ',
            'investment_of_large_companies': 'Вложения крупных компаний',
            'plan_efficiency': 'Эфисп приказов Цесаркии (%)',
            'gov_wastes': 'Расходы на государство (инфраструктура логистика федеративное республиканское ресурсодобыча)',
            'med_wastes': 'Расходы на социальную сферу (образование здравоохранение охрана соц.сфера наука)',
            'war_wastes': 'Расходы на военную сферу (армия военное_производство флот)',
            'other_wastes': 'Дополнительные расходы (внешние оккупация)',
            'trade_rank': 'Торговый ранг',
            'trade_usage': 'Число используемых торговых путей',
            'trade_efficiency': 'Торговая эффективность (%)',
            'trade_wastes': 'Торговые издержки',
            'high_quality_percent': 'Процент товаров высокого качества',
            'mid_quality_percent': 'Процент товаров среднего качества',
            'low_quality_percent': 'Процент товаров низкого качества',
            'valgery': 'Вальжерия',
            'branches_count': 'Количество филиалов',
            'branches_efficiency': 'Эффективность филиалов (%)',
            'adrian_effect': 'Эффект Адриана (Рантье)',
            'power_of_economic_formation': 'Сила СЭЗ'
        }

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        return {
            'population_count': r'Население-(\d+)',
            'decrement_coefficient': r'УНЧС - (\d+)',
            'stability': r'Экономическая стабильность - (\d+)%',
            'inflation': r'Инфляция - ([\d.]+)%',
            'current_budget': {
                'type': 'budget_calculation',
                'pattern': r'Казна- [+-]([\d.]+) \(([\d.]+)\)',
                'field': 'current_budget'
            },
            'prev_budget': {
                'type': 'budget_calculation',
                'pattern': r'Казна- [+-]([\d.]+) \(([\d.]+)\)',
                'field': 'prev_budget'
            },
            'tax_income': r'ДОХОДЫ - \+ ([\d.]+) ед\.вал',
            'universal_tax': r'УН - ([\d.]+)',
            'excise': r'Акцизы - ([\d.]+)',
            'additions': r'Дополнительные средства - \+([\d.]+) ед\.вал',
            'freedom_and_efficiency_of_small_business': r'СиРМБ - ([\d.]+)',
            'investment_of_large_companies': r'Вложения крупных компаний - ([\d.]+)',
            'plan_efficiency': r'Эфисп приказов Цесаркии - ([\d.]+)%',
            'gov_wastes': [
                r'Содержание инфраструктуры - ([\d.]+)',
                r'логистики - ([\d.]+)',
                r'федеративное - ([\d.]+)',
                r'республиканское - ([\d.]+)',
                r'ресурсодобычи - ([\d.]+)'
            ],
            'med_wastes': [
                r'Траты на образование - ([\d.]+)',
                r'здравоохранение - ([\d.]+)',
                r'охранные учреждения - ([\d.]+)',
                r'соц\.сферу - ([\d.]+)',
                r'науку - ([\d.]+)'
            ],
            'other_wastes': [
                r'Внешние расходы - ([\d.]+)',
                r'Оккупация - ([\d.]+)'
            ],
            'war_wastes': [
                r'Траты на армию - ([\d.]+)',
                r'военное производство - ([\d.]+)',
                r'флот - ([\d.]+)'
            ],
            'trade_rank': r'Торговый ранг - (\d+)',
            'trade_usage': r'Число используемых торговых путей - (\d+)',
            'trade_efficiency': r'Эффективность торговли - (\d+)%',
            'trade_wastes': r'Транспортные издержки - ([\d.]+) ед\.вал',
            'high_quality_percent': r'Высокого качества - ([\d.]+)%',
            'mid_quality_percent': r'Среднего качества - ([\d.]+)%',
            'low_quality_percent': r'Низкого качества - ([\d.]+)%',
            'valgery': r'Вальжерия - ([\d.]+)%',
            'branches_count': r'Количество филиалов - (\d+)',
            'branches_efficiency': r'Эффективность - ([\d.]+)%',
            'forex': r'Курс валюты - ([\d.]+)',
            'trade_income': r'Торговая прибыль - ([\d.]+)',
            'adrian_effect': r'Эффект Адриана \(Рантье\) - ([\d.]+)',
            'power_of_economic_formation': r'Сила СЭЗ - ([\d.]+)',
        }


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
        return {
            "Распределение отраслей": [
                'husbandry', 'livestock', 'others'
            ],
            "Природные условия": [
                'biome_richness', 'overprotective_effects'
            ],
            "Обеспеченности": [
                'securities'
            ],
            "Экономические показатели": [
                'agriculture_wastes', 'expected_wastes',
                'income_from_resources'
            ],
            "Качественные показатели": [
                'agriculture_deceases', 'agriculture_natural_deceases',
                'food_diversity'
            ]
        }

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        return {
            'husbandry': 'Земледелие (%)',
            'livestock': 'Животноводство (%)',
            'others': 'Иное (%)',
            'biome_richness': 'Богатство биомов (%)',
            'overprotective_effects': 'Эффекты от сверхплодородных земель',
            'securities': 'Обеспеченности (рабочие, технологии, орудия труда)',
            'agriculture_wastes': 'Траты (ед.вал.)',
            'expected_wastes': 'Ожидаемые траты (ед.вал.)',
            'agriculture_deceases': 'Хвори сельхоза (%)',
            'agriculture_natural_deceases': 'Ненастья и естественные проблемы сельхоза (%)',
            'income_from_resources': 'Доход от редкой и дорогой еды (ед.вал.)',
            'food_diversity': 'Пищевое разнообразие (%)',
            'food_security': 'Обеспеченность едой',
            'agriculture_efficiency': 'Эффективность сельского хозяйства (%)',
            'agriculture_development': 'Развитость сельского хозяйства (%)'
        }

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        return {
            'husbandry': r'Земледелие - ([\d.]+)%',
            'livestock': r'Животноводство - ([\d.]+)%',
            'others': r'Иное - ([\d.]+)%',
            'biome_richness': r'Богатство биомов - ([\d.]+)%',
            'overprotective_effects': r'Эффекты от сверхплодородных земель - (\d+)',
            'securities': [
                r'Рабочими - ([\d.]+)%',
                r'Технологиями возделывания - ([\d.]+)%',
                r'Удобрениями, средствами, орудиями труда - ([\d.]+)%'
            ],
            'agriculture_wastes': r'Траты - ([\d.]+) ед\.вал',
            'agriculture_deceases': r'Хвори сельхоза - ([\d.]+)',
            'agriculture_natural_deceases': r'Ненастья и естественные проблемы сельхоза - ([\d.]+)',
            'income_from_resources': r'Доход от редкой и дорогой еды - ([\d.]+) ед\.вал',
            'food_diversity': r'Пищевое разнообразие - ([\d.]+)%',
            'expected_wastes': r'Ожидаемые траты - ([\d.]+) ед\.вал'
        }


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
        return {
            "Государственный аппарат": [
                'state_apparatus_functionality', 'state_apparatus_size',
                'state_apparatus_efficiency', 'knowledge_level',
                'many_children_propoganda', 'integrity_of_faith',
                'corruption_level'
            ],
            "Экономика и социум": [
                'salt_security', 'poor_level', 'jobless_level',
                'small_enterprise_percent', 'large_enterprise_count'
            ],
            "Управление территорией": [
                'provinces_count', 'provinces_waste', 'military_equipment',
                'control'
            ],
            "Общественные настроения": [
                'contentment', 'government_trust', 'many_children_traditions',
                'sexual_asceticism', 'egocentrism_development',
                'capitalistic_decay'
            ],
            "Культура и образование": [
                'education_level', 'erudition_will', 'cultural_level',
                'violence_tendency', 'panic_level', 'unemployment_rate'
            ],
            "Социальные показатели": [
                'equality'
            ],
            "Духовность и убеждения": [
                'grace_of_the_highest', 'commitment_to_cause',
                'departure_from_truths'
            ]
        }

    @staticmethod
    @override
    def _get_field_names() -> Dict[str, str]:
        return {
            'state_apparatus_functionality': 'Связь Федерации с Республиками (%)',
            'state_apparatus_size': 'Размер бюрократического аппарата (%)',
            'state_apparatus_efficiency': 'Эффективность бюрократического аппарата (%)',
            'knowledge_level': 'Уровень образования',
            'many_children_propoganda': 'Пропаганда многодетности',
            'integrity_of_faith': 'Целостность веры',
            'corruption_level': 'Коррупция',
            'salt_security': 'Солевой достаток (%)',
            'poor_level': 'Процент бедности',
            'jobless_level': 'Процент безработицы',
            'small_enterprise_percent': 'Малый бизнес',
            'large_enterprise_count': 'Клюпр Цесаркии',
            'provinces_count': 'Число провинций',
            'provinces_waste': 'Траты на одну провинцию (ед.вал.)',
            'military_equipment': 'ЗВО',
            'control': 'Контроль (правящая сила, представительство, имеющие силу, автономии)',
            'contentment': 'Довольство населения',
            'government_trust': 'Доверие властям',
            'many_children_traditions': 'Традиции многодетности',
            'sexual_asceticism': 'Сексуальный аскетизм',
            'egocentrism_development': 'БТЗГ',
            'capitalistic_decay': 'Капиталистическое разложение',
            'education_level': 'Образованность',
            'erudition_will': 'Стремление к эрудиции',
            'cultural_level': 'Уровень культуры',
            'violence_tendency': 'Склонность к насилию',
            'panic_level': 'Паника (%)',
            'unemployment_rate': 'Процент тунеядства',
            'equality': 'Равенство (%)',
            'grace_of_the_highest': 'Милость Высших',
            'commitment_to_cause': 'Собственная Убеждённость Делу',
            'departure_from_truths': 'Отхождение от истин'
        }

    @staticmethod
    @override
    def _get_regex_patterns() -> Dict[str, Union[str, List[str]]]:
        return {
            'state_apparatus_functionality': r'Cвязь Федерации с Республиками - ([\d.]+)%',
            'state_apparatus_size': r'Размер - (\d+)%',
            'state_apparatus_efficiency': r'Эффективность - (\d+)%',
            'knowledge_level': r'Уровень образования - (\d+)',
            'many_children_propoganda': r'Пропаганда многодетности - (\d+)',
            'integrity_of_faith': r'Целостность веры - (\d+)',
            'corruption_level': r'Коррупция - (\d+)',
            'salt_security': r'Солевой достаток - (\d+)%',
            'poor_level': r'Процент бедности - ([\d.]+)',
            'jobless_level': r'Процент безработицы - ([\d.]+)',
            'small_enterprise_percent': r'Малый бизнес - ([\d.]+)',
            'large_enterprise_count': r'Клюпр Цесаркии - (\d+)',
            'provinces_count': r'Число провинций - (\d+)',
            'provinces_waste': r'Траты на одну - ([\d.]+) ед\.вал',
            'military_equipment': r'ЗВО - ([\d.]+)',
            'control': [
                r'Правящая сила - ([\d.]+)%',
                r'Представительство - ([\d.]+)%',
                r'Имеющие силу - ([\d.]+)%',
                r'Автономии - ([\d.]+)%'
            ],
            'contentment': r'Довольство населения - (\d+)',
            'government_trust': r'Доверие властям - ([\d.]+)',
            'many_children_traditions': r'Традиции многодетности - (\d+)',
            'sexual_asceticism': r'Сексуальный аскетизм - ([\d.]+)',
            'egocentrism_development': r'БТЗГ - ([\d.]+)',
            'capitalistic_decay': r'Капиталистическое разложение - ([\d.]+)',
            'education_level': r'Образованность - ([\d.]+)',
            'erudition_will': r'Стремление к эрудиции - (\d+)',
            'cultural_level': r'Уровень культуры - (\d+)',
            'violence_tendency': r'Склонность к насилию - ([\d.]+)',
            'panic_level': r'Паника - ([\d.]+)%',
            'unemployment_rate': r'Процент тунеядства - ([\d.]+)',
            'equality': r'Равенство - ([\d.]+)%',
            'grace_of_the_highest': r'Милость Высших - (\d+)',
            'commitment_to_cause': r'Собственная Убеждённость Делу - (\d+)',
            'departure_from_truths': r'Отхождение от истин - (\d+)'
        }


# Создаем тип для базовых статистик Atterium
ATTERIUM_BASIC_STATS = Tuple[
    AtteriumEconomyStats, AtteriumAgricultureStats, AtteriumInnerPoliticsStats]
