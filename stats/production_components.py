"""Configurable multi-turn industrial production rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pydantic

from stats.industry_components import (
    RESOURCE_CATALOG,
    ExtractionGroup,
    ResourceType,
)


class ProductionRecipeId(StrEnum):
    BASIC_BUILDING_MATERIALS = "basic_building_materials"
    EXPENSIVE_BUILDING_MATERIALS = "expensive_building_materials"


@dataclass(frozen=True)
class ProductionRecipe:
    recipe: ProductionRecipeId
    name: str
    inputs: dict[ResourceType, float]
    outputs: dict[ResourceType, float]
    byproducts: dict[ResourceType, float]


PRODUCTION_RECIPES: dict[ProductionRecipeId, ProductionRecipe] = {
    ProductionRecipeId.BASIC_BUILDING_MATERIALS: ProductionRecipe(
        recipe=ProductionRecipeId.BASIC_BUILDING_MATERIALS,
        name="Базовые стройматериалы",
        inputs={
            ResourceType.IRON: 2.0,
            ResourceType.COAL: 1.0,
            ResourceType.SILICON: 0.5,
        },
        outputs={ResourceType.BASIC_BUILDING_MATERIALS: 2.5},
        byproducts={ResourceType.SLAG: 0.4},
    ),
    ProductionRecipeId.EXPENSIVE_BUILDING_MATERIALS: ProductionRecipe(
        recipe=ProductionRecipeId.EXPENSIVE_BUILDING_MATERIALS,
        name="Дорогие стройматериалы",
        inputs={
            ResourceType.BASIC_BUILDING_MATERIALS: 2.0,
            ResourceType.COPPER: 0.5,
            ResourceType.ALUMINUM: 0.5,
        },
        outputs={ResourceType.EXPENSIVE_BUILDING_MATERIALS: 1.0},
        byproducts={ResourceType.SLAG: 0.2},
    ),
}


class ProductionRule(pydantic.BaseModel):
    """A production transformation repeated once per turn for a duration.

    A built-in ``recipe`` fills its resource maps automatically. A custom
    rule can instead provide ``rule_id``, ``inputs`` and ``outputs``.
    ``turns_remaining=None`` means the rule has no automatic expiry.
    """

    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    rule_id: str | None = pydantic.Field(None, min_length=1)
    name: str | None = None
    recipe: ProductionRecipeId | None = None
    target_group: ExtractionGroup | None = None
    target_resource: ResourceType | None = None
    batches: float = pydantic.Field(..., ge=0)
    turns_remaining: int | None = pydantic.Field(None, ge=0)
    enabled: bool = True
    inputs: dict[ResourceType, float] = pydantic.Field(default_factory=dict)
    outputs: dict[ResourceType, float] = pydantic.Field(default_factory=dict)
    byproducts: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )

    @pydantic.model_validator(mode="after")
    def populate_and_validate(self) -> ProductionRule:
        if self.recipe is not None:
            recipe = PRODUCTION_RECIPES[self.recipe]
            if self.rule_id is None:
                object.__setattr__(self, "rule_id", recipe.recipe.value)
            if self.name is None:
                object.__setattr__(self, "name", recipe.name)
            if not self.inputs:
                object.__setattr__(self, "inputs", dict(recipe.inputs))
            if not self.outputs:
                object.__setattr__(self, "outputs", dict(recipe.outputs))
            if not self.byproducts:
                object.__setattr__(
                    self,
                    "byproducts",
                    dict(recipe.byproducts),
                )

        if self.rule_id is None:
            raise ValueError("Пользовательскому правилу нужен rule_id")
        if self.name is None:
            object.__setattr__(self, "name", self.rule_id)
        if not self.outputs:
            raise ValueError("Правило производства должно иметь выход")
        if self.target_group is not None and self.target_resource is not None:
            raise ValueError(
                "Правило относится либо к группе, либо к ресурсу, но не "
                "к обоим одновременно"
            )
        if self.target_group is None and self.target_resource is None:
            output_resources = tuple(self.outputs)
            if len(output_resources) == 1:
                object.__setattr__(
                    self,
                    "target_resource",
                    output_resources[0],
                )
            else:
                output_groups = {
                    RESOURCE_CATALOG[resource].group
                    for resource in output_resources
                }
                if len(output_groups) == 1:
                    object.__setattr__(
                        self,
                        "target_group",
                        output_groups.pop(),
                    )
                else:
                    raise ValueError(
                        "Для правила с выходами из разных групп нужно явно "
                        "задать target_group или target_resource"
                    )
        if self.target_resource is not None:
            unrelated = set(self.outputs) - {self.target_resource}
            if unrelated:
                raise ValueError(
                    "Выход правила ресурса должен содержать только целевой "
                    "ресурс"
                )
        if self.target_group is not None:
            unrelated = [
                resource
                for resource in self.outputs
                if RESOURCE_CATALOG[resource].group is not self.target_group
            ]
            if unrelated:
                raise ValueError(
                    "Все выходы группового правила должны относиться к "
                    f"группе {self.target_group.value}"
                )
        for mapping_name, mapping in (
            ("inputs", self.inputs),
            ("outputs", self.outputs),
            ("byproducts", self.byproducts),
        ):
            if any(amount < 0 for amount in mapping.values()):
                raise ValueError(
                    f"Количество ресурса в {mapping_name} не может быть "
                    "отрицательным"
                )
        if self.turns_remaining == 0:
            object.__setattr__(self, "enabled", False)
        return self

    def advance_turn(self) -> None:
        """Consume one configured turn after an execution attempt."""
        if not self.enabled or self.turns_remaining is None:
            return
        remaining = max(self.turns_remaining - 1, 0)
        object.__setattr__(self, "turns_remaining", remaining)
        if remaining == 0:
            object.__setattr__(self, "enabled", False)


@dataclass(frozen=True)
class ProductionResult:
    recipe: ProductionRecipeId | None
    requested_batches: float
    completed_batches: float
    inputs_spent: dict[ResourceType, float]
    outputs_produced: dict[ResourceType, float]
    byproducts_produced: dict[ResourceType, float]
    rule_id: str = ""
    name: str = ""
    turns_remaining: int | None = None
