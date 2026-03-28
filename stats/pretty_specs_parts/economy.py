from __future__ import annotations

from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, budget_pair, field, \
    list_item
from stats.pretty_specs_parts.common import available_trade_paths, \
    budget_getter, trade_usage_load


ECONOMY_COMMON_FIELDS = {
    "population_count": field("population_count", "Население", decimals=0,
                              aliases=("Население",)),
    "decrement_coefficient": field("decrement_coefficient", "УНЧС",
                                   decimals=0),
    "income": field("income", "Прирост", decimals=0, read_only=True,
                    default=0),
    "budget": field(
        "budget",
        "Казна",
        field_name="current_budget",
        getter=budget_getter,
        formatter=budget_pair,
        parse_kind="budget",
        default=0.0,
        aliases=("Казна",),
    ),
    "stability": field("stability", "Эк. стабильность", decimals=0, suffix="%",
                       aliases=("Экономическая стабильность",)),
    "inflation": field("inflation", "Инфляция", decimals=1, suffix="%"),
    "tax_income": field("tax_income", "ДОХОДЫ", decimals=3,
                        suffix=" ед.вал/ход", default=0.0,
                        aliases=("Доходы",)),
    "universal_tax": field("universal_tax", "УН", decimals=1),
    "excise": field("excise", "Акцизы", decimals=1),
    "additions": field("additions", "Доп. средства", decimals=1,
                       aliases=("Дополнительные средства",)),

    # старые названия
    "med0": list_item("med_wastes", "Траты на образование", 0, decimals=1,
                      aliases=("Образование",)),
    "med1": list_item("med_wastes", "Здравоохранение", 1, decimals=1,
                      aliases=("здравоохранение",)),
    "med2": list_item("med_wastes", "Охранные учреждения", 2, decimals=1,
                      aliases=("охранные учреждения",)),
    "med3": list_item("med_wastes", "Соц.сфера", 3, decimals=1,
                      aliases=("Соц. сфера", "соц.сферу")),
    "med4": list_item("med_wastes", "Наука", 4, decimals=1,
                      aliases=("науку",)),

    "war0": list_item("war_wastes", "Траты на армию", 0, decimals=1,
                      aliases=("Армия",)),
    "war1": list_item("war_wastes", "Военное производство", 1, decimals=1,
                      aliases=("Воен. производство", "военное производство")),
    "war2": list_item("war_wastes", "Флот", 2, decimals=1, aliases=("флот",)),

    "trade_rank": field("trade_rank", "Торговый ранг", decimals=0),
    "trade_potential": field("trade_potential", "Торговый потенциал",
                             decimals=0, read_only=True, suffix=" т.п.",
                             default=0.0),
    "trade_efficiency": field("trade_efficiency", "Эфф. торговли", decimals=0,
                              suffix="%", aliases=("Эффективность торговли",)),
    "trade_usage": field("trade_usage", "Исп. пути", decimals=0,
                         aliases=("Число используемых торговых путей",)),
    "trade_usage_load": field("trade_usage_load", "Загрузка путей", decimals=0,
                              suffix="%", read_only=True,
                              getter=trade_usage_load, default=0.0,
                              aliases=("Загруженность торговых путей",)),
    "trade_wastes": field("trade_wastes", "Трансп. издержки", decimals=1,
                          suffix=" ед.вал",
                          aliases=("Транспортные издержки",)),
    "available_trade_paths": field("available_trade_paths", "Доступные пути",
                                   decimals=0, read_only=True,
                                   getter=available_trade_paths, default=0),

    "hq": field("high_quality_percent", "Высокое качество", decimals=1,
                suffix="%", aliases=("Высокого качества",)),
    "mq": field("mid_quality_percent", "Среднее качество", decimals=1,
                suffix="%", aliases=("Среднего качества",)),
    "lq": field("low_quality_percent", "Низкое качество", decimals=1,
                suffix="%", aliases=("Низкого качества",)),
    "valgery": field("valgery", "Вальжерия", decimals=1, suffix="%"),
    "allegorization": field("allegorization", "Аллегоризация", decimals=1,
                            suffix="%"),
    "forex": field("forex", "Курс валюты", decimals=2, default=0.0),
    "trade_income": field("trade_income", "Торговая прибыль", decimals=3,
                          default=0.0),

    "branches_count": field("branches_count", "Филиалы", decimals=0,
                            aliases=("Количество филиалов",)),
    "branches_efficiency": field("branches_efficiency", "Эффективность",
                                 decimals=1, suffix="%"),
    "branches_income": field("branches_income", "Доход", decimals=3,
                             default=0.0),
}

BASIC_ECONOMY_LAYOUT = PrettyLayoutSpec(
    fields={
        **ECONOMY_COMMON_FIELDS,
        "small_enterprise_tax": field("small_enterprise_tax", "Нал. предпр.",
                                      decimals=1, aliases=(
                "Налог на предпринимательство",)),
        "large_enterprise_tax": field("large_enterprise_tax",
                                      "Нал. круп. предпр.", decimals=1,
                                      aliases=(
                                          "Налог на крупных предпринимателей",)),

        # старые названия массива трат
        "gov0": list_item("gov_wastes", "Содержание инфраструктуры", 0,
                          decimals=1, aliases=("Инфраструктура",)),
        "gov1": list_item("gov_wastes", "Логистики", 1, decimals=1,
                          aliases=("Логистика", "логистики")),
        "gov2": list_item("gov_wastes", "Гос.аппарата", 2, decimals=1,
                          aliases=("Гос. аппарат", "гос.аппарата")),
        "gov3": list_item("gov_wastes", "Ресурсодобычи", 3, decimals=1,
                          aliases=("Ресурсодобыча", "ресурсодобычи")),

        "other0": list_item("other_wastes", "Субсидирование бизнеса", 0,
                            decimals=1, aliases=("Субсидии бизнесу",)),
        "other1": list_item("other_wastes", "Внешние расходы", 1, decimals=1),
        "other2": list_item("other_wastes", "Оккупация", 2, decimals=1),
    },
    lines=(
        PrettyLineSpec(title="ЭКОНОМИКА"),
        PrettyLineSpec(
            fields=("population_count", "decrement_coefficient", "income"),
            min_gap=8),
        PrettyLineSpec(fields=("budget", "stability", "inflation"), min_gap=8),
        PrettyLineSpec(fields=("tax_income", "universal_tax", "excise"),
                       min_gap=8),
        PrettyLineSpec(fields=("additions", "small_enterprise_tax",
                               "large_enterprise_tax"), min_gap=8),

        PrettyLineSpec(title="ГРАЖДАНСКИЕ ТРАТЫ", gap_before=1),
        PrettyLineSpec(fields=("gov0", "gov1"), line_width=150, min_gap=18),
        PrettyLineSpec(fields=("gov2", "gov3"), line_width=150, min_gap=18),
        PrettyLineSpec(fields=("med0", "med1", "med2"), line_width=170,
                       min_gap=12),
        PrettyLineSpec(fields=("med3", "med4"), line_width=130, min_gap=30),
        PrettyLineSpec(fields=("other0", "other1", "other2"), line_width=165,
                       min_gap=12),

        PrettyLineSpec(title="ВОЕННЫЕ ТРАТЫ", gap_before=1),
        PrettyLineSpec(fields=("war0", "war1", "war2", "other2"),
                       line_width=165, min_gap=12),

        PrettyLineSpec(title="ТОРГОВЛЯ", gap_before=1),
        PrettyLineSpec(
            fields=("trade_rank", "trade_potential", "trade_efficiency"),
            min_gap=8),
        PrettyLineSpec(
            fields=("trade_usage", "trade_usage_load", "trade_wastes"),
            min_gap=8),
        PrettyLineSpec(fields=("available_trade_paths", "trade_income"),
                       line_width=130, min_gap=24),
        PrettyLineSpec(fields=("hq", "mq", "lq"), min_gap=10),
        PrettyLineSpec(fields=("valgery", "allegorization", "forex"),
                       min_gap=10),

        PrettyLineSpec(title="ФИЛИАЛЫ", gap_before=1),
        PrettyLineSpec(fields=("branches_count", "branches_efficiency",
                               "branches_income"), min_gap=10),
    ),
)

ATTERIUM_ECONOMY_LAYOUT = PrettyLayoutSpec(
    fields={
        **ECONOMY_COMMON_FIELDS,
        "freedom_and_efficiency_of_small_business": field(
            "freedom_and_efficiency_of_small_business", "СиРМБ", decimals=1),
        "investment_of_large_companies": field("investment_of_large_companies",
                                               "Вложения крупных компаний",
                                               decimals=1),
        "plan_efficiency": field("plan_efficiency", "Эфисп приказов Цесаркии",
                                 decimals=1, suffix="%"),
        "gov0": list_item("gov_wastes", "Инфраструктура", 0, decimals=1,
                          aliases=("Содержание инфраструктуры",)),
        "gov1": list_item("gov_wastes", "Логистика", 1, decimals=1,
                          aliases=("логистики",)),
        "gov2": list_item("gov_wastes", "Федеративное", 2, decimals=1,
                          aliases=("федеративное",)),
        "gov3": list_item("gov_wastes", "Республиканское", 3, decimals=1,
                          aliases=("республиканское",)),
        "gov4": list_item("gov_wastes", "Ресурсодобыча", 4, decimals=1,
                          aliases=("ресурсодобычи",)),
        "other0": list_item("other_wastes", "Внешние расходы", 0, decimals=1),
        "other1": list_item("other_wastes", "Оккупация", 1, decimals=1),
        "adrian_effect": field("adrian_effect", "Эффект Адриана", decimals=1,
                               aliases=("Эффект Адриана (Рантье)",)),
        "power_of_economic_formation": field("power_of_economic_formation",
                                             "Сила СЭЗ", decimals=1),
    },
    lines=(
        PrettyLineSpec(title="ЭКОНОМИКА"),
        PrettyLineSpec(
            fields=("population_count", "decrement_coefficient", "income")),
        PrettyLineSpec(fields=("budget", "stability", "inflation")),
        PrettyLineSpec(fields=("tax_income", "universal_tax", "excise")),
        PrettyLineSpec(
            fields=("additions", "freedom_and_efficiency_of_small_business",
                    "investment_of_large_companies")),
        PrettyLineSpec(fields=("plan_efficiency", "gov0", "gov1")),
        PrettyLineSpec(fields=("gov2", "gov3", "gov4")),
        PrettyLineSpec(fields=("med0", "med1", "med2")),
        PrettyLineSpec(fields=("med3", "med4")),
        PrettyLineSpec(fields=("other0", "other1")),
        PrettyLineSpec(fields=("war0", "war1", "war2")),
        PrettyLineSpec(title="ТОРГОВЛЯ"),
        PrettyLineSpec(
            fields=("trade_rank", "trade_potential", "trade_efficiency")),
        PrettyLineSpec(
            fields=("trade_usage", "trade_usage_load", "trade_wastes")),
        PrettyLineSpec(fields=("available_trade_paths", "trade_income")),
        PrettyLineSpec(fields=("hq", "mq", "lq")),
        PrettyLineSpec(fields=("valgery", "allegorization", "forex")),
        PrettyLineSpec(fields=("branches_count", "branches_efficiency",
                               "branches_income")),
        PrettyLineSpec(
            fields=("adrian_effect", "power_of_economic_formation")),
    ),
)

ISF_ECONOMY_LAYOUT = PrettyLayoutSpec(
    fields={
        **ECONOMY_COMMON_FIELDS,
        "small_business_tax": field("small_business_tax",
                                    "Налог на малый бизнес", decimals=1),
        "large_enterprise_tax": field("large_enterprise_tax",
                                      "Налоги с аристократии", decimals=1),
        "gov0": list_item("gov_wastes", "Инфраструктура", 0, decimals=1,
                          aliases=("Содержание инфраструктуры",)),
        "gov1": list_item("gov_wastes", "Логистика", 1, decimals=1,
                          aliases=("логистики",)),
        "gov2": list_item("gov_wastes", "Гос. аппарат", 2, decimals=1,
                          aliases=("гос.аппарата",)),
        "gov3": list_item("gov_wastes", "Ресурсодобыча", 3, decimals=1,
                          aliases=("ресурсодобычи",)),
        "other0": list_item("other_wastes", "Внешние расходы", 0, decimals=1),
        "other1": list_item("other_wastes", "Оккупация", 1, decimals=1),
    },
    lines=(
        PrettyLineSpec(title="ЭКОНОМИКА"),
        PrettyLineSpec(
            fields=("population_count", "decrement_coefficient", "income")),
        PrettyLineSpec(fields=("budget", "stability", "inflation")),
        PrettyLineSpec(fields=("tax_income", "universal_tax", "excise")),
        PrettyLineSpec(fields=("additions", "small_business_tax",
                               "large_enterprise_tax")),
        PrettyLineSpec(fields=("gov0", "gov1")),
        PrettyLineSpec(fields=("gov2", "gov3")),
        PrettyLineSpec(fields=("med0", "med1", "med2")),
        PrettyLineSpec(fields=("med3", "med4")),
        PrettyLineSpec(fields=("other0", "other1")),
        PrettyLineSpec(fields=("war0", "war1", "war2")),
        PrettyLineSpec(title="ТОРГОВЛЯ"),
        PrettyLineSpec(
            fields=("trade_rank", "trade_potential", "trade_efficiency")),
        PrettyLineSpec(
            fields=("trade_usage", "trade_usage_load", "trade_wastes")),
        PrettyLineSpec(fields=("available_trade_paths", "trade_income")),
        PrettyLineSpec(fields=("hq", "mq", "lq")),
        PrettyLineSpec(fields=("valgery", "allegorization", "forex")),
        PrettyLineSpec(fields=("branches_count", "branches_efficiency",
                               "branches_income")),
    ),
)
