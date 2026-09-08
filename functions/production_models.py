"""Execution of auditable resource-production recipes."""

from __future__ import annotations

from stats.industry_components import ResourceInventory, ResourceType
from stats.production_components import (
    ProductionResult,
    ProductionRule,
)


def execute_rule(
    inventory: ResourceInventory,
    rule: ProductionRule,
    process_yield: float,
    requested_batches: float | None = None,
) -> ProductionResult:
    requested = (
        rule.batches if requested_batches is None else requested_batches
    )
    requested = max(float(requested), 0.0) if rule.enabled else 0.0
    yield_factor = min(max(process_yield / 100, 0.0), 1.0)
    limits = [requested]
    for resource, per_batch in rule.inputs.items():
        stock = inventory.resources[resource].stockpile
        limits.append(stock / per_batch if per_batch > 0 else requested)
    for resource, per_batch in rule.outputs.items():
        state = inventory.resources[resource]
        if not state.enabled:
            limits.append(0.0)
            continue
        free_storage = max(state.storage_capacity - state.stockpile, 0.0)
        effective_output = per_batch * yield_factor
        limits.append(
            free_storage / effective_output
            if effective_output > 0
            else requested
        )
    completed = max(0.0, min(limits))
    inputs_spent: dict[ResourceType, float] = {}
    outputs_produced: dict[ResourceType, float] = {}
    byproducts_produced: dict[ResourceType, float] = {}
    for resource, per_batch in rule.inputs.items():
        spent = inventory.spend(resource, per_batch * completed)
        inputs_spent[resource] = spent.actual
    nominal_output = 0.0
    for resource, per_batch in rule.outputs.items():
        amount = per_batch * completed * yield_factor
        nominal_output += per_batch * completed
        outputs_produced[resource] = inventory.collect(
            resource,
            amount,
        ).actual
    for resource, per_batch in rule.byproducts.items():
        amount = per_batch * completed
        if resource == ResourceType.SLAG:
            amount += nominal_output * (1 - yield_factor)
        byproducts_produced[resource] = inventory.collect(
            resource,
            amount,
        ).actual
    return ProductionResult(
        recipe=rule.recipe,
        requested_batches=requested,
        completed_batches=completed,
        inputs_spent=inputs_spent,
        outputs_produced=outputs_produced,
        byproducts_produced=byproducts_produced,
        rule_id=rule.rule_id or "",
        name=rule.name or rule.rule_id or "",
        turns_remaining=rule.turns_remaining,
    )
