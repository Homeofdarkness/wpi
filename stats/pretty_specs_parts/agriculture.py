from __future__ import annotations
from __future__ import annotations

from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, field, \
    food_security, list_item
from stats.pretty_specs_parts.common import food_security_getter


AGRICULTURE_COMMON_FIELDS = {
    "husbandry": field("husbandry", "Земледелие", decimals=1, suffix="%"),
    "livestock": field("livestock", "Животноводство", decimals=1, suffix="%"),
    "others": field("others", "Рыболовство", decimals=1, suffix="%"),
    "biome_richness": field("biome_richness", "Богатство биомов", decimals=1,
                            suffix="%"),
    "overprotective_effects": field(
        "overprotective_effects",
        "Эффекты от сверхплодородных земель",
        decimals=0,
        aliases=("Сверхплодородные земли",),
    ),

    # старые названия массива
    "sec0": list_item("securities", "Технологиями возделывания", 0, decimals=1,
                      suffix="%", aliases=("Технологии",)),
    "sec1": list_item("securities", "Удобрениями, средствами", 1, decimals=1,
                      suffix="%", aliases=("Удобрения",)),
    "sec2": list_item("securities", "Орудиями труда", 2, decimals=1,
                      suffix="%", aliases=("Орудия труда",)),

    "workers_percent": field("workers_percent", "Процент рабочих", decimals=1,
                             suffix="%"),
    "workers_redistribution": field("workers_redistribution",
                                    "Рабочее перераспределение", decimals=1,
                                    suffix="%",
                                    aliases=("Перераспределение рабочих",)),
    "storages_upkeep": field("storages_upkeep", "Содержание хранилищ",
                             decimals=3, suffix=" ед.вал",
                             aliases=("Хранилища",)),
    "consumption_factor": field("consumption_factor",
                                "Коэффициент потребления", decimals=1,
                                suffix="%", aliases=("Потребление",)),
    "environmental_food": field("environmental_food",
                                "Еда из окружающей среды", decimals=0,
                                aliases=("Еда из среды",)),
    "food_security": field(
        "food_security",
        "Обеспеченность едой",
        read_only=True,
        getter=food_security_getter,
        formatter=food_security,
        default=0.0,
        aliases=("Обесп. едой",),
    ),
    "agriculture_deceases": field("agriculture_deceases", "Хвори сельхоза",
                                  decimals=1, suffix="%"),
    "agriculture_natural_deceases": field(
        "agriculture_natural_deceases",
        "Ненастья и естественные проблемы сельхоза",
        decimals=1,
        suffix="%",
        aliases=("Естеств. проблемы",),
    ),
    "income_from_resources": field(
        "income_from_resources",
        "Доход от редкой и дорогой еды",
        decimals=1,
        suffix=" ед.вал",
        aliases=("Редкая еда",),
    ),
    "food_diversity": field("food_diversity", "Пищевое разнообразие",
                            decimals=1, suffix="%", read_only=True,
                            default=0.0),
    "overstock_percent": field("overstock_percent", "Изъять из потребления",
                               decimals=1, suffix="%"),
    "expected_wastes": field("expected_wastes", "Ожидаемые траты", decimals=3,
                             suffix=" ед.вал", default=0.0),
    "agriculture_efficiency": field(
        "agriculture_efficiency",
        "Эффективность сельского хозяйства",
        decimals=0,
        suffix="%",
        read_only=True,
        default=0.0,
        aliases=("Эфф. сельхоза",),
    ),
    "agriculture_development": field(
        "agriculture_development",
        "Развитость сельского хозяйства",
        decimals=2,
        suffix="%",
        read_only=True,
        default=0.0,
        aliases=("Развитость сельхоза",),
    ),
    "food_supplies": field("food_supplies", "Запасы пищи", decimals=2,
                           default=0.0),
}

AGRICULTURE_LAYOUT = PrettyLayoutSpec(
    fields={**AGRICULTURE_COMMON_FIELDS},
    lines=(
        PrettyLineSpec(title="СЕЛЬСКОЕ ХОЗЯЙСТВО"),
        PrettyLineSpec(fields=("husbandry", "livestock", "others"), min_gap=8),
        PrettyLineSpec(fields=("biome_richness", "overprotective_effects"),
                       line_width=145, min_gap=20),

        PrettyLineSpec(title="ОБЕСПЕЧЕННОСТИ", gap_before=1),
        PrettyLineSpec(fields=("sec0", "sec1"), line_width=170, min_gap=18),
        PrettyLineSpec(
            fields=("sec2", "workers_percent", "workers_redistribution"),
            line_width=170, min_gap=12),

        PrettyLineSpec(title="ТРАТЫ И ПОТРЕБЛЕНИЕ", gap_before=1),
        PrettyLineSpec(fields=("storages_upkeep", "consumption_factor",
                               "environmental_food"), line_width=165,
                       min_gap=12),
        PrettyLineSpec(fields=("food_security", "agriculture_deceases",
                               "agriculture_natural_deceases"), line_width=170,
                       min_gap=12),
        PrettyLineSpec(fields=("income_from_resources", "food_diversity",
                               "overstock_percent"), line_width=170,
                       min_gap=12),
        PrettyLineSpec(fields=("expected_wastes", "agriculture_efficiency",
                               "agriculture_development"), line_width=170,
                       min_gap=12),
        PrettyLineSpec(fields=("food_supplies",), gap_before=1),
    ),
)

ISF_AGRICULTURE_LAYOUT = PrettyLayoutSpec(
    fields={
        **AGRICULTURE_COMMON_FIELDS,
        "empire_land_unmastery": field("empire_land_unmastery",
                                       "Неосвоенность Империи", decimals=1,
                                       aliases=(
                                           "Неосвоенность земель Империи",)),
    },
    lines=(
        PrettyLineSpec(title="СЕЛЬСКОЕ ХОЗЯЙСТВО"),
        PrettyLineSpec(fields=("husbandry", "livestock", "others")),
        PrettyLineSpec(fields=("biome_richness", "overprotective_effects",
                               "empire_land_unmastery")),
        PrettyLineSpec(fields=("sec0", "sec1", "sec2")),
        PrettyLineSpec(fields=("workers_percent", "workers_redistribution",
                               "storages_upkeep")),
        PrettyLineSpec(fields=("consumption_factor", "environmental_food",
                               "food_security")),
        PrettyLineSpec(
            fields=("agriculture_deceases", "agriculture_natural_deceases",
                    "income_from_resources")),
        PrettyLineSpec(
            fields=("food_diversity", "overstock_percent", "expected_wastes")),
        PrettyLineSpec(
            fields=("agriculture_efficiency", "agriculture_development",
                    "food_supplies")),
    ),
)
