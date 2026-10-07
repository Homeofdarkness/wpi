from __future__ import annotations

from stats.pretty import PrettyLayoutSpec, PrettyLineSpec, field, list_item
from stats.pretty_specs_parts.common import (
    active_resource_count,
    resource_stockpile,
)


INDUSTRY_LAYOUT = PrettyLayoutSpec(
    fields={
        "processing_production": field(
            "processing_production",
            "Произв. переработки",
            decimals=1,
            suffix="%",
            aliases=("Процент производства",),
        ),
        "processing_usage": field(
            "processing_usage",
            "Исп. переработки",
            decimals=1,
            suffix="%",
            aliases=("Процент использования",),
        ),
        "processing_efficiency": field(
            "processing_efficiency",
            "Эфф. добычи",
            decimals=1,
            suffix="%",
            aliases=("Эффективность добычи",),
        ),
        "usage0": list_item(
            "usages",
            "Ресурсная база",
            0,
            decimals=1,
            suffix="%",
            aliases=("Cобственной ресурсной базой",),
        ),
        "usage1": list_item(
            "usages", "Сырье", 1, decimals=1, suffix="%", aliases=("Сырьем",)
        ),
        "usage2": list_item(
            "usages",
            "Рабочие",
            2,
            decimals=1,
            suffix="%",
            aliases=("Предприятий рабочими",),
        ),
        "usage3": list_item(
            "usages",
            "Квалификация",
            3,
            decimals=1,
            suffix="%",
            aliases=("Квалификация рабочих",),
        ),
        "industry_coefficient": field(
            "industry_coefficient",
            "Коэф. производительности",
            decimals=3,
            read_only=True,
            default=0.0,
            aliases=("Коэффициент производительности",),
        ),
        "civil_security": field(
            "civil_security",
            "Обесп. сырьем",
            decimals=1,
            suffix="%",
            aliases=("Обеспеченность сырьем",),
        ),
        "standardization": field(
            "standardization", "Стандартизация", decimals=1, suffix="%"
        ),
        "logistic": field(
            "logistic",
            "Логистика",
            decimals=1,
            suffix="%",
            aliases=("Логистика предприятий",),
        ),
        "tvr1": field(
            "tvr1", "ТЖН", decimals=0, aliases=("Обеспеченность ТЖН",)
        ),
        "tvr2": field(
            "tvr2", "ТНП", decimals=0, aliases=("Обеспеченность ТНП",)
        ),
        "consumption_of_goods": field(
            "consumption_of_goods",
            "Потребление товаров",
            decimals=1,
            suffix="%",
            default=0.0,
            aliases=("Потребление товаров",),
        ),
        "civil_efficiency": field(
            "civil_efficiency",
            "Эфф. гражданки",
            decimals=2,
            suffix="%",
            read_only=True,
            default=0.0,
            aliases=("Эффективность производства",),
        ),
        "expected_wastes": field(
            "expected_wastes",
            "Ожидаемые траты",
            decimals=3,
            suffix=" ед.вал",
            default=0.0,
            aliases=("Ожидаемые траты",),
        ),
        "overproduction_coefficient": field(
            "overproduction_coefficient",
            "Перепроизводство",
            decimals=1,
            suffix="%",
            aliases=("Процент перепроизводства",),
        ),
        "max_potential": field(
            "max_potential",
            "Макс. потенциал",
            decimals=2,
            suffix="%",
            read_only=True,
            default=0.0,
            aliases=("Максимальный потенциал использования",),
        ),
        "civil_usage": field(
            "civil_usage",
            "Исп. гражданки",
            decimals=1,
            suffix="%",
            read_only=True,
            default=0.0,
            aliases=("Процент использования",),
        ),
        "industry_income": field(
            "industry_income", "ПСС", decimals=2, suffix=" ед.вал", default=0.0
        ),
        "war_production_efficiency": field(
            "war_production_efficiency",
            "Воен. эффективность",
            decimals=1,
            suffix="%",
            aliases=("Эффективность военного производства",),
        ),
        "active_resource_count": field(
            "active_resource_count",
            "Активные ресурсы",
            decimals=0,
            read_only=True,
            getter=active_resource_count,
        ),
        "resource_stockpile": field(
            "resource_stockpile",
            "Всего на складах",
            decimals=2,
            suffix=" ед.рес.",
            read_only=True,
            getter=resource_stockpile,
        ),
        "ordinary_workers": field(
            "ordinary_workers",
            "Обычные рабочие",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.ordinary_workers,
        ),
        "specialist_workers": field(
            "specialist_workers",
            "Специалисты",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.specialist_workers,
        ),
        "forced_workers": field(
            "forced_workers",
            "Принуждённые",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.forced_workers,
        ),
        "total_workers": field(
            "total_workers",
            "Всего доступно",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.total_workers,
        ),
        "industrial_population_target_share": field(
            "industrial_population_target_share",
            "Целевая доля населения",
            decimals=1,
            suffix="%",
            read_only=True,
            getter=lambda model: (
                model.workforce.industrial_population_target_share
            ),
        ),
        "employed_workers": field(
            "employed_workers",
            "Занято",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.employed_workers,
        ),
        "idle_workers": field(
            "idle_workers",
            "Резерв",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.idle_workers,
        ),
        "extraction_workers": field(
            "extraction_workers",
            "В добыче",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.extraction_workers,
        ),
        "extraction_target_share": field(
            "extraction_target_share",
            "Целевая доля добычи",
            decimals=1,
            suffix="%",
            read_only=True,
            getter=lambda model: model.workforce.extraction_target_share,
        ),
        "production_workers": field(
            "production_workers",
            "В производстве",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.production_workers,
        ),
        "unmet_workers": field(
            "unmet_workers",
            "Нехватка рабочих",
            decimals=0,
            read_only=True,
            getter=lambda model: model.workforce.unmet_workers,
        ),
        "labor_coverage": field(
            "labor_coverage",
            "Обеспеченность кадрами",
            decimals=1,
            suffix="%",
            read_only=True,
            getter=lambda model: model.workforce.labor_coverage,
        ),
    },
    lines=(
        PrettyLineSpec(title="ПРОМЫШЛЕННОСТЬ"),
        PrettyLineSpec(
            fields=(
                "processing_production",
                "processing_usage",
                "processing_efficiency",
            )
        ),
        PrettyLineSpec(fields=("usage0", "usage1")),
        PrettyLineSpec(fields=("usage2", "usage3", "industry_coefficient")),
        PrettyLineSpec(
            fields=("civil_security", "standardization", "logistic")
        ),
        PrettyLineSpec(fields=("tvr1", "tvr2")),
        PrettyLineSpec(
            fields=(
                "consumption_of_goods",
                "civil_efficiency",
                "expected_wastes",
            )
        ),
        PrettyLineSpec(
            fields=(
                "overproduction_coefficient",
                "max_potential",
                "civil_usage",
            )
        ),
        PrettyLineSpec(
            fields=("industry_income", "war_production_efficiency")
        ),
        PrettyLineSpec(title="ПРОМЫШЛЕННЫЕ РАБОЧИЕ"),
        PrettyLineSpec(
            fields=(
                "ordinary_workers",
                "specialist_workers",
                "forced_workers",
            )
        ),
        PrettyLineSpec(
            fields=(
                "total_workers",
                "industrial_population_target_share",
                "employed_workers",
                "idle_workers",
            ),
            line_width=170,
            min_gap=8,
        ),
        PrettyLineSpec(
            fields=(
                "extraction_workers",
                "extraction_target_share",
                "production_workers",
                "unmet_workers",
                "labor_coverage",
            ),
            line_width=190,
            min_gap=8,
        ),
        PrettyLineSpec(title="РЕСУРСОДОБЫЧА"),
        PrettyLineSpec(fields=("active_resource_count", "resource_stockpile")),
    ),
)
