from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, field


def probability_field(key: str, label: str):
    return field(
        key,
        label,
        decimals=1,
        suffix="%",
        read_only=True,
        default=0.0,
    )


PROBABILITY_LAYOUT = PrettyLayoutSpec(
    fields={
        "equipment_availability": probability_field(
            "equipment_availability", "Доступность оборудования"
        ),
        "workforce_attendance": probability_field(
            "workforce_attendance", "Явка работников"
        ),
        "process_yield": probability_field(
            "process_yield", "Выход годной продукции"
        ),
        "logistics_integrity": probability_field(
            "logistics_integrity", "Сохранность при перевозке"
        ),
        "storage_preservation": probability_field(
            "storage_preservation", "Сохранность на складах"
        ),
        "research_reproducibility": probability_field(
            "research_reproducibility", "Воспроизводимость исследований"
        ),
        "industrial_accident_chance": probability_field(
            "industrial_accident_chance", "Промышленная авария"
        ),
        "supply_disruption_chance": probability_field(
            "supply_disruption_chance", "Нарушение снабжения"
        ),
        "population_epidemic_chance": probability_field(
            "population_epidemic_chance", "Эпидемия населения"
        ),
        "agricultural_epidemic_chance": probability_field(
            "agricultural_epidemic_chance", "Сельскохозяйственная эпидемия"
        ),
        "natural_disaster_chance": probability_field(
            "natural_disaster_chance", "Природное бедствие"
        ),
        "mass_protest_chance": probability_field(
            "mass_protest_chance", "Массовые протесты"
        ),
        "separatist_crisis_chance": probability_field(
            "separatist_crisis_chance", "Сепаратистский кризис"
        ),
        "major_sabotage_chance": probability_field(
            "major_sabotage_chance", "Крупный саботаж"
        ),
    },
    lines=(
        PrettyLineSpec(title="НАДЁЖНОСТЬ СИСТЕМ"),
        PrettyLineSpec(
            fields=(
                "equipment_availability",
                "workforce_attendance",
                "process_yield",
            )
        ),
        PrettyLineSpec(
            fields=(
                "logistics_integrity",
                "storage_preservation",
                "research_reproducibility",
            )
        ),
        PrettyLineSpec(title="ВЕРОЯТНОСТИ СОБЫТИЙ ЗА КВАРТАЛ"),
        PrettyLineSpec(
            fields=(
                "industrial_accident_chance",
                "supply_disruption_chance",
            )
        ),
        PrettyLineSpec(
            fields=(
                "population_epidemic_chance",
                "agricultural_epidemic_chance",
            )
        ),
        PrettyLineSpec(
            fields=("natural_disaster_chance", "mass_protest_chance")
        ),
        PrettyLineSpec(
            fields=("separatist_crisis_chance", "major_sabotage_chance")
        ),
    ),
)
