from __future__ import annotations

from pathlib import Path

import pytest

from functions.industrialization_models import (
    STAGE_PROFILES,
    IndustrialGroupScenario,
    IndustrialStage,
    calculate_group_output,
)
from industrialization_demo import load_demo_config, render_demo


def reference_scenario(**changes) -> IndustrialGroupScenario:
    source = {
        "id": "reference_coal",
        "group": "solid_fuel",
        "resource": "coal",
        "workers": 10_000,
        "specialists": 1_000,
        "shifts_per_worker_month": 22,
        "mechanization": None,
        "equipment_capacity_per_month": 1_000_000,
        "equipment_condition": 100,
        "energy_supply": 100,
        "organization": 100,
        "accessibility": 100,
        "recovery": 100,
        "logistics": 100,
    }
    source.update(changes)
    return IndustrialGroupScenario.model_validate(source)


def test_reference_coal_rates_are_monotonic_and_reproduced() -> None:
    scenario = reference_scenario()
    rates = []

    for stage, profile in STAGE_PROFILES.items():
        result = calculate_group_output(
            scenario,
            months=3,
            default_stage=stage,
            stage_override=stage,
        )
        rates.append(result.output_per_worker_shift)
        assert result.output_per_worker_shift == pytest.approx(
            profile.reference_output_per_shift
        )

    assert rates == sorted(rates)
    assert rates[2] == pytest.approx(1.069)
    assert rates[3] == pytest.approx(1.1595)
    assert rates[4] == pytest.approx(1.224)


def test_machine_output_requires_real_equipment_capacity() -> None:
    scenario = reference_scenario(
        stage="mass_production",
        mechanization=80,
        equipment_capacity_per_month=0,
    )

    result = calculate_group_output(
        scenario,
        months=3,
        default_stage=IndustrialStage.MASS_PRODUCTION,
    )

    assert result.mechanized_potential > 0
    assert result.mechanized_output == 0
    assert result.main_bottleneck == "оборудование"
    assert result.delivered_output == pytest.approx(result.manual_output)


def test_output_scales_with_months_not_reference_turn_length() -> None:
    scenario = reference_scenario(stage="machine")
    quarter = calculate_group_output(
        scenario,
        months=3,
        default_stage=IndustrialStage.MACHINE,
    )
    nine_months = calculate_group_output(
        scenario,
        months=9,
        default_stage=IndustrialStage.MACHINE,
    )

    assert nine_months.delivered_output == pytest.approx(
        quarter.delivered_output * 3
    )
    assert nine_months.output_per_worker_shift == pytest.approx(
        quarter.output_per_worker_shift
    )


def test_custom_resource_alias_works_in_existing_group() -> None:
    scenario = reference_scenario(resource="anthracite_dust")

    result = calculate_group_output(
        scenario,
        months=3,
        default_stage=IndustrialStage.MACHINE,
    )

    assert result.resource.value == "anthracite_dust"


def test_demo_config_and_report_are_runnable() -> None:
    path = (
        Path(__file__).parents[1]
        / "test_files"
        / ("industrialization_demo.toml")
    )

    config = load_demo_config(path)
    report = render_demo(config)

    assert config.months == 3
    assert "╫" in report
    assert "ДЕМО ГРУППОВОЙ ДОБЫЧИ (3 МЕСЯЦА)" in report
    assert "solid_fuel / coal" in report
    assert "Референс" in report
    assert "без цен, налогов и добавленной стоимости" in report
