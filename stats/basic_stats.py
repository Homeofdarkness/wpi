import pydantic
from typing_extensions import override

from functions.time_models import REFERENCE_TURN_MONTHS
from stats.derived_fields import (
    populate_basic_economy,
    populate_basic_industry,
    populate_basic_inner_politics,
)
from stats.industry_components import (
    ExtractionGroup,
    ExtractionOperation,
    IndustrialWorkforce,
    ResourceInventory,
    ResourceRegistration,
    ResourceState,
    ResourceTransfer,
    ResourceType,
)
from stats.industry_effects import (
    DependencyMetric,
    IndustrialEffect,
    IndustrialEffectResult,
    default_industrial_effects,
)
from stats.industry_text import (
    parse_industry_configuration,
    render_group_state_table,
    render_industry_configuration,
    render_resource_state_table,
)
from stats.pretty_specs import get_layout_for_class
from stats.production_components import ProductionResult, ProductionRule
from stats.stats_base import StatsBase


class EconomyStatsBase(StatsBase):
    population_count: int = pydantic.Field(..., gt=0)
    decrement_coefficient: int = pydantic.Field(..., ge=0, le=5)
    inflation: float = pydantic.Field(..., ge=0, le=100)
    current_budget: float
    stability: int = pydantic.Field(..., ge=0, le=100)
    universal_tax: float
    excise: float
    additions: float
    gov_wastes: list[float] = pydantic.Field(..., min_length=4)
    med_wastes: list[float] = pydantic.Field(..., min_length=5)
    other_wastes: list[float] = pydantic.Field(..., min_length=2)
    war_wastes: list[float] = pydantic.Field(..., min_length=3)
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
    tax_income: float | None = None
    forex: float | None = None
    trade_income: float | None = None
    money_income: float | None = None
    prev_budget: float | None = None
    income: float | None = None
    trade_potential: float | None = None
    branches_income: float | None = None
    public_debt: float = pydantic.Field(0.0, ge=0)
    annual_interest_rate: float = pydantic.Field(0.0, ge=0, le=100)
    resource_balance: float = 0.0

    @pydantic.model_validator(mode="after")
    def check_trade_sum(self) -> "EconomyStatsBase":
        goods_percent = (
            self.low_quality_percent
            + self.mid_quality_percent
            + self.high_quality_percent
        )
        if abs(goods_percent - 100) > 0.1:
            raise ValueError(
                f"Сумма товаров разных качеств должна "
                f"быть равна 100, а на деле - {goods_percent}"
            )

        return self

    def recalculate_derived_fields(self):
        populate_basic_economy(self)

    def trade_usage_load(self) -> int:
        if not self.trade_potential:
            return 0
        return round(self.trade_usage / self.trade_potential * 100)


class EconomyStats(EconomyStatsBase):
    small_enterprise_tax: float
    large_enterprise_tax: float

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("EconomyStats")


# Переделываем с 0)
class IndustrialStats(StatsBase):
    processing_production: float = pydantic.Field(..., ge=0, le=100)
    processing_usage: float = pydantic.Field(..., ge=0, le=100)
    processing_efficiency: float = pydantic.Field(..., ge=0, le=100)
    usages: list[float] = pydantic.Field(..., min_length=1)
    civil_security: float = pydantic.Field(..., ge=0, le=100)
    standardization: float = pydantic.Field(..., ge=0, le=100)
    logistic: float = pydantic.Field(..., ge=0, le=100)
    tvr1: int = pydantic.Field(..., ge=0, le=100)
    tvr2: int = pydantic.Field(..., ge=0, le=100)
    overproduction_coefficient: float = pydantic.Field(..., ge=0, le=100)
    war_production_efficiency: float = pydantic.Field(..., ge=0, le=100)
    industry_income: float = 0
    consumption_of_goods: float = 0
    civil_usage: float | None = None
    industry_coefficient: float | None = None
    civil_efficiency: float | None = None
    max_potential: float | None = None
    expected_wastes: float | None = None
    resource_inventory: ResourceInventory = pydantic.Field(
        default_factory=ResourceInventory
    )
    workforce: IndustrialWorkforce = pydantic.Field(
        default_factory=IndustrialWorkforce
    )
    extraction_operations: list[ExtractionOperation] = pydantic.Field(
        default_factory=list
    )
    last_extracted: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )
    production_rules: list[ProductionRule] = pydantic.Field(
        default_factory=list
    )
    last_production: list[ProductionResult] = pydantic.Field(
        default_factory=list
    )
    # Values are monthly consumption rates; TurnEngine expands them to the
    # actual number of months in the current turn.
    resource_demands: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )
    resource_shortages: dict[ResourceType, float] = pydantic.Field(
        default_factory=dict
    )
    effects: list[IndustrialEffect] = pydantic.Field(
        default_factory=default_industrial_effects
    )
    last_effects: list[IndustrialEffectResult] = pydantic.Field(
        default_factory=list
    )

    def recalculate_derived_fields(self):
        populate_basic_industry(self)

    def collect_resource(
        self,
        resource: ResourceType,
        amount: float,
    ) -> ResourceTransfer:
        return self.resource_inventory.collect(resource, amount)

    def spend_resource(
        self,
        resource: ResourceType,
        amount: float,
    ) -> ResourceTransfer:
        return self.resource_inventory.spend(resource, amount)

    def register_resource(
        self,
        registration: ResourceRegistration | ResourceType,
        **configuration,
    ) -> ResourceState:
        """Register one country resource and its initial state."""
        if isinstance(registration, ResourceType):
            registration = ResourceRegistration(
                resource=registration,
                **configuration,
            )
        elif configuration:
            raise TypeError(
                "configuration нельзя передавать вместе с готовым "
                "ResourceRegistration"
            )

        state = ResourceState(
            resource=registration.resource,
            name=registration.name,
            group=registration.group,
            enabled=True,
            stockpile=registration.stockpile,
            storage_capacity=registration.storage_capacity,
            accessibility=registration.accessibility,
            quality=registration.quality,
        )
        self.resource_inventory.resources[registration.resource] = state
        if registration.consumption_per_month > 0:
            self.resource_demands[registration.resource] = (
                registration.consumption_per_month
            )
        else:
            self.resource_demands.pop(registration.resource, None)
        return state

    def register_resource_group(self, group: ExtractionGroup) -> None:
        """Compatibility no-op: extraction groups are now always available."""
        ExtractionGroup(group)

    def set_extraction_operation(
        self,
        operation: ExtractionOperation,
    ) -> None:
        """Add or replace extraction by one registered alias."""
        for index, current in enumerate(self.extraction_operations):
            if current.target_key == operation.target_key:
                self.extraction_operations[index] = operation
                return
        self.extraction_operations.append(operation)

    def resolve_extraction_target(
        self,
        operation: ExtractionOperation,
    ) -> tuple[ExtractionGroup, ResourceType | None]:
        """Resolve one alias: registered groups take precedence."""
        try:
            return ExtractionGroup(operation.target), None
        except ValueError:
            resource = ResourceType(operation.target)
        try:
            state = self.resource_inventory.resources[resource]
        except KeyError as error:
            raise ValueError(
                f"Неизвестная цель добычи: {operation.target}"
            ) from error
        if not state.enabled:
            raise ValueError(
                f"Ресурс добычи не зарегистрирован: {operation.target}"
            )
        return state.definition.group, resource

    def set_production_rule(self, rule: ProductionRule) -> None:
        """Add or replace a production rule by its stable identifier."""
        for index, current in enumerate(self.production_rules):
            if current.rule_id == rule.rule_id:
                self.production_rules[index] = rule
                return
        self.production_rules.append(rule)

    def validate_industry_configuration(self) -> None:
        """Validate relationships that span several industrial models."""
        resources = self.resource_inventory.resources
        registered_resources = {
            resource for resource, state in resources.items() if state.enabled
        }
        for rule in self.production_rules:
            if not rule.enabled:
                continue
            referenced = (
                set(rule.inputs) | set(rule.outputs) | set(rule.byproducts)
            )
            unavailable = [
                resource
                for resource in referenced
                if resource not in registered_resources
            ]
            if unavailable:
                names = ", ".join(resource.value for resource in unavailable)
                raise ValueError(
                    f"Правило {rule.rule_id} использует "
                    f"незарегистрированные ресурсы: {names}"
                )

            if (
                rule.target_resource is not None
                and rule.target_resource not in registered_resources
            ):
                raise ValueError(
                    f"Цель правила {rule.rule_id} не зарегистрирована: "
                    f"{rule.target_resource.value}"
                )
            if rule.target_group is not None:
                unrelated = [
                    resource
                    for resource in rule.outputs
                    if resources[resource].definition.group
                    is not rule.target_group
                ]
                if unrelated:
                    names = ", ".join(item.value for item in unrelated)
                    raise ValueError(
                        f"Выходы правила {rule.rule_id} не относятся к "
                        f"группе {rule.target_group.value}: {names}"
                    )

        for operation in self.extraction_operations:
            target_group, target_resource = self.resolve_extraction_target(
                operation
            )
            eligible = [
                state
                for state in resources.values()
                if state.enabled
                and state.definition.group is target_group
                and (
                    target_resource is None
                    or state.resource == target_resource
                )
            ]
            if not eligible:
                raise ValueError(
                    f"У добычи {operation.target_key} нет подходящих "
                    "зарегистрированных ресурсов"
                )

    def active_resource_count(self) -> int:
        return self.resource_inventory.active_count()

    def resource_stockpile(self) -> float:
        return self.resource_inventory.total_stockpile()

    def render_resource_details(self) -> str:
        active = [
            state
            for state in self.resource_inventory.resources.values()
            if state.enabled
        ]
        group_lines = render_group_state_table(
            active,
            self.last_extracted,
            self.resource_shortages,
        )
        resource_lines = (
            render_resource_state_table(
                active,
                self.last_extracted,
                self.resource_shortages,
            )
            if active
            else ["Нет данных"]
        )
        return "\n".join(
            (
                "СОСТОЯНИЕ ГРУПП",
                *group_lines,
                "",
                "СОСТОЯНИЕ РЕСУРСОВ",
                *resource_lines,
            )
        )

    def render_production_results(self) -> str:
        rows = ["ПРОИЗВОДСТВО ЗА ХОД"]
        if not self.last_production:
            if not self.production_rules:
                rows.append("Правила производства не загружены")
            elif not any(rule.enabled for rule in self.production_rules):
                rows.append("Нет активных правил производства")
            else:
                rows.append("Текущий ход ещё не рассчитывался")
            return "\n".join(rows)
        for result in self.last_production:
            remaining_months = (
                "∞"
                if result.turns_remaining is None
                else str(round(result.turns_remaining * REFERENCE_TURN_MONTHS))
            )
            rows.append(
                f"{result.name} [{result.rule_id}]: "
                f"план {result.requested_batches:.1f}, "
                f"выполнено {result.completed_batches:.1f} партий, "
                f"осталось месяцев {remaining_months}"
            )
            rows.append(
                "  Взято: "
                f"{self._format_resource_amounts(result.inputs_spent)}"
            )
            rows.append(
                "  Выпущено: "
                f"{self._format_resource_amounts(result.outputs_produced)}"
            )
            if result.byproducts_produced:
                rows.append(
                    "  Побочно: "
                    f"{self._format_resource_amounts(result.byproducts_produced)}"
                )
        return "\n".join(rows)

    def render_effect_results(self) -> str:
        """Expose configured effects and actual deltas for every target."""
        rows = ["ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ"]
        if not self.effects:
            rows.append("Эффекты не настроены")
            return "\n".join(rows)

        results = {
            (result.effect_id, result.target): result
            for result in self.last_effects
        }
        target_width = max(
            len(target) for effect in self.effects for target in effect.targets
        )
        for effect in self.effects:
            rows.append(f"{effect.id}:")
            for target in effect.targets:
                label = f"  {target:<{target_width}} : "
                result = results.get((effect.id, target))
                if result is None:
                    rows.append(f"{label}ожидает расчёта хода")
                    continue
                rows.append(
                    f"{label}{result.target_before:.1f} -> "
                    f"{result.target_after:.1f} "
                    f"({result.adjustment:+.1f})"
                )
        return "\n".join(rows)

    def _format_resource_amounts(
        self,
        values: dict[ResourceType, float],
    ) -> str:
        if not values:
            return "нет"
        return ", ".join(
            f"{self.resource_inventory.resources[resource].definition.name} "
            f"{amount:.1f}"
            for resource, amount in values.items()
        )

    def dependency_metrics(
        self,
        demands: dict[ResourceType, float] | None = None,
    ) -> tuple[dict[str, DependencyMetric], dict[str, DependencyMetric]]:
        """Return normalized deficit/surplus inputs exposed to formulas."""
        effective_demands = (
            self.resource_demands if demands is None else demands
        )
        active = [
            state
            for state in self.resource_inventory.resources.values()
            if state.enabled
        ]
        resource_metrics: dict[str, DependencyMetric] = {}
        for state in active:
            demand = effective_demands.get(state.resource, 0.0)
            resource_metrics[state.resource.value] = DependencyMetric(
                deficit=(
                    self.resource_shortages.get(state.resource, 0.0) / demand
                    if demand > 0
                    else 0.0
                ),
                surplus=state.stockpile / demand if demand > 0 else 0.0,
            )

        group_metrics: dict[str, DependencyMetric] = {}
        for group in ExtractionGroup:
            demanded = [
                state
                for state in active
                if state.group is group
                and effective_demands.get(state.resource, 0.0) > 0
            ]
            total_demand = sum(
                effective_demands[state.resource] for state in demanded
            )
            group_metrics[group.value] = DependencyMetric(
                deficit=(
                    sum(
                        self.resource_shortages.get(state.resource, 0.0)
                        for state in demanded
                    )
                    / total_demand
                    if total_demand > 0
                    else 0.0
                ),
                surplus=(
                    sum(state.stockpile for state in demanded) / total_demand
                    if total_demand > 0
                    else 0.0
                ),
            )
        for effect in self.effects:
            for dependency in effect.dependencies:
                if dependency.resource is not None:
                    resource_metrics.setdefault(
                        dependency.resource.value,
                        DependencyMetric(),
                    )
        return resource_metrics, group_metrics

    def render_configuration(self) -> str:
        return render_industry_configuration(
            resources=self.resource_inventory.resources,
            operations=self.extraction_operations,
            production_rules=self.production_rules,
            effects=self.effects,
            demands=self.resource_demands,
        )

    def __str__(self):
        pretty = self.render_pretty()
        resources = self.render_resource_details()
        if pretty.startswith("```\n") and pretty.endswith("\n```"):
            return f"{pretty[:-4]}\n\n{resources}\n```"
        return f"{pretty}\n{resources}"

    @classmethod
    def from_stats_text(
        cls,
        data: str,
        defaults: dict | None = None,
    ) -> "IndustrialStats":
        stats = super().from_stats_text(data, defaults)
        configuration = parse_industry_configuration(data)
        if configuration is None:
            if (
                "СОСТОЯНИЕ РЕСУРСОВ" in data
                and "СОСТОЯНИЕ РЕСУРСОВ\nНет данных" not in data
            ):
                raise ValueError(
                    "Для состояния ресурсов нужен отдельный TOML-файл "
                    "настроек промышленности"
                )
            return stats

        stats.resource_inventory = ResourceInventory()
        stats.extraction_operations = []
        for registration in configuration.registrations:
            stats.register_resource(registration)
        for operation in configuration.operations:
            stats.set_extraction_operation(operation)
        stats.production_rules = configuration.production_rules
        stats.effects = configuration.effects
        stats.resource_demands = configuration.demands
        stats.last_extracted = configuration.extracted
        stats.resource_shortages = configuration.shortages
        stats.validate_industry_configuration()
        return stats

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("IndustrialStats")


class InnerPoliticsStats(StatsBase):
    state_apparatus_size: int
    state_apparatus_efficiency: int
    knowledge_level: float
    many_children_propoganda: int
    integrity_of_faith: int
    corruption_level: int
    salt_security: int
    poor_level: float
    jobless_level: float
    income_from_scientific: float
    small_enterprise_percent: float
    large_enterprise_count: int
    provinces_count: int
    provinces_waste: float
    military_equipment: float
    control: list[float] = pydantic.Field(
        ...,
        min_length=4,
        max_length=4,
    )
    contentment: int
    government_trust: float
    many_children_traditions: int
    sexual_asceticism: float
    egocentrism_development: float
    education_level: float
    erudition_will: int
    cultural_level: int
    violence_tendency: float
    panic_level: float
    unemployment_rate: float
    grace_of_the_highest: int
    commitment_to_cause: int
    departure_from_truths: int
    research_success_chance: float | None = None
    society_decline: float | None = None
    inequality: float = pydantic.Field(25.0, ge=0, le=100)
    polarization: float = pydantic.Field(20.0, ge=0, le=100)
    information_quality: float = pydantic.Field(60.0, ge=0, le=100)
    regional_separatism: float = pydantic.Field(0.0, ge=0, le=100)
    social_mobility: float = pydantic.Field(50.0, ge=0, le=100)
    war_fatigue: float = pydantic.Field(0.0, ge=0, le=100)

    def recalculate_derived_fields(self):
        populate_basic_inner_politics(self)

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("InnerPoliticsStats")


class AgricultureStats(StatsBase):
    husbandry: float
    livestock: float
    others: float
    biome_richness: float
    overprotective_effects: int
    securities: list[float] = pydantic.Field(
        ...,
        min_length=3,
        max_length=3,
    )
    workers_percent: float = pydantic.Field(..., ge=0)
    workers_redistribution: float = pydantic.Field(..., ge=0, le=100)
    storages_upkeep: float
    consumption_factor: float = pydantic.Field(..., ge=0)
    environmental_food: int
    agriculture_deceases: float
    agriculture_natural_deceases: float
    income_from_resources: float
    overstock_percent: float

    # Semi-dynamic param
    food_supplies: float = 0

    # Dynamic params (calculated in skip-move)
    expected_wastes: float | None = None
    food_security: float | None = None
    food_diversity: float | None = None
    agriculture_efficiency: float | None = None
    agriculture_development: float | None = None

    @staticmethod
    @override
    def _get_pretty_layout():
        return get_layout_for_class("AgricultureStats")
