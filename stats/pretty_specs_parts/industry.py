from __future__ import annotations

from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, field, list_item

INDUSTRY_LAYOUT = PrettyLayoutSpec(
    fields={
        "processing_production": field("processing_production", "Произв. переработки", decimals=1, suffix="%", aliases=("Процент производства",)),
        "processing_usage": field("processing_usage", "Исп. переработки", decimals=1, suffix="%", aliases=("Процент использования",)),
        "processing_efficiency": field("processing_efficiency", "Эфф. добычи", decimals=1, suffix="%", aliases=("Эффективность добычи",)),
        "usage0": list_item("usages", "Ресурсная база", 0, decimals=1, suffix="%", aliases=("Cобственной ресурсной базой",)),
        "usage1": list_item("usages", "Сырье", 1, decimals=1, suffix="%", aliases=("Сырьем",)),
        "usage2": list_item("usages", "Рабочие", 2, decimals=1, suffix="%", aliases=("Предприятий рабочими",)),
        "usage3": list_item("usages", "Квалификация", 3, decimals=1, suffix="%", aliases=("Квалификация рабочих",)),
        "industry_coefficient": field("industry_coefficient", "Коэф. производительности", decimals=3, read_only=True, default=0.0, aliases=("Коэффициент производительности",)),
        "civil_security": field("civil_security", "Обесп. сырьем", decimals=1, suffix="%", aliases=("Обеспеченность сырьем",)),
        "standardization": field("standardization", "Стандартизация", decimals=1, suffix="%"),
        "logistic": field("logistic", "Логистика", decimals=1, suffix="%", aliases=("Логистика предприятий",)),
        "tvr1": field("tvr1", "ТЖН", decimals=0, aliases=("Обеспеченность ТЖН",)),
        "tvr2": field("tvr2", "ТНП", decimals=0, aliases=("Обеспеченность ТНП",)),
        "consumption_of_goods": field("consumption_of_goods", "Потребление товаров", decimals=1, suffix="%", default=0.0, aliases=("Потребление товаров",)),
        "civil_efficiency": field("civil_efficiency", "Эфф. гражданки", decimals=2, suffix="%", read_only=True, default=0.0, aliases=("Эффективность производства",)),
        "expected_wastes": field("expected_wastes", "Ожидаемые траты", decimals=3, suffix=" ед.вал", default=0.0, aliases=("Ожидаемые траты",)),
        "overproduction_coefficient": field("overproduction_coefficient", "Перепроизводство", decimals=1, suffix="%", aliases=("Процент перепроизводства",)),
        "max_potential": field("max_potential", "Макс. потенциал", decimals=2, suffix="%", read_only=True, default=0.0, aliases=("Максимальный потенциал использования",)),
        "civil_usage": field("civil_usage", "Исп. гражданки", decimals=1, suffix="%", read_only=True, default=0.0, aliases=("Процент использования",)),
        "industry_income": field("industry_income", "ПСС", decimals=2, suffix=" ед.вал", default=0.0),
        "war_production_efficiency": field("war_production_efficiency", "Воен. эффективность", decimals=1, suffix="%", aliases=("Эффективность военного производства",)),
    },
    lines=(
        PrettyLineSpec(title="ПРОМЫШЛЕННОСТЬ"),
        PrettyLineSpec(fields=("processing_production", "processing_usage", "processing_efficiency")),
        PrettyLineSpec(fields=("usage0", "usage1")),
        PrettyLineSpec(fields=("usage2", "usage3", "industry_coefficient")),
        PrettyLineSpec(fields=("civil_security", "standardization", "logistic")),
        PrettyLineSpec(fields=("tvr1", "tvr2")),
        PrettyLineSpec(fields=("consumption_of_goods", "civil_efficiency", "expected_wastes")),
        PrettyLineSpec(fields=("overproduction_coefficient", "max_potential", "civil_usage")),
        PrettyLineSpec(fields=("industry_income", "war_production_efficiency")),
    ),
)
