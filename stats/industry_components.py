"""State models for industrial resources and extraction operations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

import pydantic


class ResourceType(StrEnum):
    """Resource alias.

    The named members are compatibility shortcuts for the bundled resources.
    Unknown, valid aliases are accepted as dynamic values, so the catalogue no
    longer limits which materials a country can register.
    """

    WOOD = "wood"
    FRESH_WATER = "fresh_water"
    MINERAL_WATER = "mineral_water"
    GOLD = "gold"
    SILVER = "silver"
    COPPER = "copper"
    ALUMINUM = "aluminum"
    TITANIUM = "titanium"
    OTHER_NONFERROUS = "other_nonferrous"
    IRON = "iron"
    HEAVY_METALS = "heavy_metals"
    CHROMIUM = "chromium"
    OTHER_FERROUS = "other_ferrous"
    SULFUR = "sulfur"
    SILICON = "silicon"
    BASIC_BUILDING_MATERIALS = "basic_building_materials"
    EXPENSIVE_BUILDING_MATERIALS = "expensive_building_materials"
    CORE_CRYSTAL = "core_crystal"
    COAL = "coal"
    OIL = "oil"
    GAS = "gas"
    PEAT = "peat"
    NOBLE_GASES = "noble_gases"
    PRECIOUS_STONES = "precious_stones"
    DIAMONDS = "diamonds"
    UNIQUE_RESOURCES = "unique_resources"
    LITHIUM = "lithium"
    RARE_EARTH_METALS = "rare_earth_metals"
    NICKEL = "nickel"
    ROCK_SALT = "rock_salt"
    POTASH_SALT = "potash_salt"
    CHERNOZEM = "chernozem"
    RUBBER = "rubber"
    EXOTIC_WOOD = "exotic_wood"
    SLAG = "slag"
    BIOWASTE = "biowaste"
    MINERALS = "minerals"

    @classmethod
    def _missing_(cls, value: object) -> ResourceType | None:
        if (
            not isinstance(value, str)
            or re.fullmatch(r"[a-z][a-z0-9_]*", value) is None
        ):
            return None
        member = str.__new__(cls, value)
        member._name_ = f"CUSTOM_{value.upper()}"
        member._value_ = value
        return member


class ExtractionGroup(StrEnum):
    FORESTRY = "forestry"
    FRESH_WATER = "fresh_water"
    MINERAL_WATER = "mineral_water"
    PRECIOUS = "precious"
    STRATEGIC_METALS = "strategic_metals"
    NONFERROUS = "nonferrous"
    FERROUS = "ferrous"
    HEAVY_METALS = "heavy_metals"
    CHEMICAL = "chemical"
    CONSTRUCTION = "construction"
    SOLID_FUEL = "solid_fuel"
    HYDROCARBONS = "hydrocarbons"
    RARE_EARTH = "rare_earth"
    SALTS = "salts"
    SOIL = "soil"
    PLANTATIONS = "plantations"
    RECYCLING = "recycling"
    MINERALS = "minerals"
    UNIQUE = "unique"


@dataclass(frozen=True)
class ResourceDefinition:
    name: str
    group: ExtractionGroup
    unit: str = "ед.рес."


def _definition(
    name: str,
    group: ExtractionGroup,
) -> ResourceDefinition:
    return ResourceDefinition(name=name, group=group)


RESOURCE_CATALOG: dict[ResourceType, ResourceDefinition] = {
    ResourceType.WOOD: _definition("Дерево", ExtractionGroup.FORESTRY),
    ResourceType.FRESH_WATER: _definition(
        "Пресная вода", ExtractionGroup.FRESH_WATER
    ),
    ResourceType.MINERAL_WATER: _definition(
        "Солёная и минеральная вода",
        ExtractionGroup.MINERAL_WATER,
    ),
    ResourceType.GOLD: _definition("Золото", ExtractionGroup.PRECIOUS),
    ResourceType.SILVER: _definition("Серебро", ExtractionGroup.PRECIOUS),
    ResourceType.COPPER: _definition("Медь", ExtractionGroup.NONFERROUS),
    ResourceType.ALUMINUM: _definition(
        "Алюминий",
        ExtractionGroup.STRATEGIC_METALS,
    ),
    ResourceType.TITANIUM: _definition(
        "Титан", ExtractionGroup.STRATEGIC_METALS
    ),
    ResourceType.OTHER_NONFERROUS: _definition(
        "Остальные цветные металлы",
        ExtractionGroup.NONFERROUS,
    ),
    ResourceType.IRON: _definition("Железо", ExtractionGroup.FERROUS),
    ResourceType.HEAVY_METALS: _definition(
        "Тяжёлые металлы",
        ExtractionGroup.HEAVY_METALS,
    ),
    ResourceType.CHROMIUM: _definition(
        "Хром", ExtractionGroup.STRATEGIC_METALS
    ),
    ResourceType.OTHER_FERROUS: _definition(
        "Остальные чёрные металлы",
        ExtractionGroup.FERROUS,
    ),
    ResourceType.SULFUR: _definition("Сера", ExtractionGroup.CHEMICAL),
    ResourceType.SILICON: _definition("Кремний", ExtractionGroup.CHEMICAL),
    ResourceType.BASIC_BUILDING_MATERIALS: _definition(
        "Базовые стройматериалы",
        ExtractionGroup.CONSTRUCTION,
    ),
    ResourceType.EXPENSIVE_BUILDING_MATERIALS: _definition(
        "Дорогие стройматериалы",
        ExtractionGroup.CONSTRUCTION,
    ),
    ResourceType.CORE_CRYSTAL: _definition(
        "Кристалл ядра", ExtractionGroup.UNIQUE
    ),
    ResourceType.COAL: _definition("Уголь", ExtractionGroup.SOLID_FUEL),
    ResourceType.OIL: _definition("Нефть", ExtractionGroup.HYDROCARBONS),
    ResourceType.GAS: _definition("Газ", ExtractionGroup.HYDROCARBONS),
    ResourceType.PEAT: _definition("Торф", ExtractionGroup.SOLID_FUEL),
    ResourceType.NOBLE_GASES: _definition(
        "Благородные газы",
        ExtractionGroup.HYDROCARBONS,
    ),
    ResourceType.PRECIOUS_STONES: _definition(
        "Драгоценные камни",
        ExtractionGroup.PRECIOUS,
    ),
    ResourceType.DIAMONDS: _definition("Алмазы", ExtractionGroup.PRECIOUS),
    ResourceType.UNIQUE_RESOURCES: _definition(
        "Уникальные ресурсы", ExtractionGroup.UNIQUE
    ),
    ResourceType.LITHIUM: _definition(
        "Литий", ExtractionGroup.STRATEGIC_METALS
    ),
    ResourceType.RARE_EARTH_METALS: _definition(
        "Редкоземельные металлы",
        ExtractionGroup.RARE_EARTH,
    ),
    ResourceType.NICKEL: _definition(
        "Никель", ExtractionGroup.STRATEGIC_METALS
    ),
    ResourceType.ROCK_SALT: _definition(
        "Каменная соль", ExtractionGroup.SALTS
    ),
    ResourceType.POTASH_SALT: _definition(
        "Калийная соль", ExtractionGroup.SALTS
    ),
    ResourceType.CHERNOZEM: _definition("Чернозём", ExtractionGroup.SOIL),
    ResourceType.RUBBER: _definition("Каучук", ExtractionGroup.PLANTATIONS),
    ResourceType.EXOTIC_WOOD: _definition(
        "Экзотическая древесина",
        ExtractionGroup.FORESTRY,
    ),
    ResourceType.SLAG: _definition("Шлак", ExtractionGroup.RECYCLING),
    ResourceType.BIOWASTE: _definition("Биоотходы", ExtractionGroup.RECYCLING),
    ResourceType.MINERALS: _definition("Минералы", ExtractionGroup.MINERALS),
}


@dataclass(frozen=True)
class ResourceTransfer:
    requested: float
    actual: float
    shortage: float = 0.0
    overflow: float = 0.0


class ResourceState(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    resource: ResourceType
    name: str | None = pydantic.Field(None, min_length=1)
    group: ExtractionGroup | None = None
    enabled: bool = False
    stockpile: float = pydantic.Field(0.0, ge=0)
    storage_capacity: float = pydantic.Field(0.0, ge=0)
    accessibility: float = pydantic.Field(100.0, ge=0, le=100)
    quality: float = pydantic.Field(100.0, ge=0, le=100)

    @pydantic.model_validator(mode="after")
    def populate_definition(self) -> ResourceState:
        bundled = RESOURCE_CATALOG.get(self.resource)
        if self.name is None:
            object.__setattr__(
                self,
                "name",
                bundled.name if bundled is not None else self.resource.value,
            )
        if self.group is None:
            if bundled is None:
                raise ValueError(
                    f"Для нового ресурса {self.resource.value} нужна группа"
                )
            object.__setattr__(self, "group", bundled.group)
        return self

    @property
    def definition(self) -> ResourceDefinition:
        assert self.name is not None
        assert self.group is not None
        return ResourceDefinition(name=self.name, group=self.group)

    def collect(self, amount: float) -> ResourceTransfer:
        requested = max(float(amount), 0.0)
        if not self.enabled:
            return ResourceTransfer(
                requested=requested,
                actual=0.0,
                shortage=requested,
            )
        free_storage = max(self.storage_capacity - self.stockpile, 0.0)
        actual = min(requested, free_storage)
        self.stockpile += actual
        return ResourceTransfer(
            requested=requested,
            actual=actual,
            overflow=max(requested - free_storage, 0.0),
        )

    def spend(self, amount: float) -> ResourceTransfer:
        requested = max(float(amount), 0.0)
        actual = min(requested, self.stockpile)
        self.stockpile -= actual
        return ResourceTransfer(
            requested=requested,
            actual=actual,
            shortage=requested - actual,
        )

    def apply_storage_preservation(
        self,
        percent: float,
        reference_scale: float = 1.0,
    ) -> float:
        reference_retention = min(max(percent, 0.0), 100.0) / 100
        preserved = reference_retention ** max(float(reference_scale), 0.0)
        lost = self.stockpile * (1 - preserved)
        self.stockpile -= lost
        return lost


def default_resource_states() -> dict[ResourceType, ResourceState]:
    return {
        resource: ResourceState(resource=resource) for resource in ResourceType
    }


class ResourceInventory(pydantic.BaseModel):
    resources: dict[ResourceType, ResourceState] = pydantic.Field(
        default_factory=default_resource_states
    )

    def collect(
        self,
        resource: ResourceType,
        amount: float,
    ) -> ResourceTransfer:
        return self.resources[resource].collect(amount)

    def configure(
        self,
        resource: ResourceType,
        *,
        enabled: bool = True,
        stockpile: float = 0.0,
        storage_capacity: float = 0.0,
        accessibility: float = 100.0,
        quality: float = 100.0,
    ) -> ResourceState:
        state = self.resources.get(resource)
        if state is None:
            state = ResourceState(resource=resource)
            self.resources[resource] = state
        state.enabled = enabled
        state.stockpile = stockpile
        state.storage_capacity = storage_capacity
        state.accessibility = accessibility
        state.quality = quality
        return state

    def spend(
        self,
        resource: ResourceType,
        amount: float,
    ) -> ResourceTransfer:
        return self.resources[resource].spend(amount)

    def active_count(self) -> int:
        return sum(item.enabled for item in self.resources.values())

    def total_stockpile(self) -> float:
        return sum(item.stockpile for item in self.resources.values())


class IndustrialWorkforce(pydantic.BaseModel):
    auto_size: bool = True
    ordinary_workers: int = pydantic.Field(0, ge=0)
    specialist_workers: int = pydantic.Field(0, ge=0)
    specialist_capacity: int = pydantic.Field(0, ge=0)
    forced_workers: int = pydantic.Field(0, ge=0)
    health: float = pydantic.Field(100.0, ge=0, le=100)
    social_support: float = pydantic.Field(100.0, ge=0, le=100)

    def forced_labor_cost(self) -> float:
        return self.forced_workers / 10_000 * 0.1


class ExtractionOperation(pydantic.BaseModel):
    """One extraction rule aimed at a whole group or one resource.

    Workers are deliberately absent: the turn engine allocates the country's
    industrial workforce automatically between all extraction rules.
    """

    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    target: str = pydantic.Field(..., pattern=r"^[a-z0-9_]+$")
    intensity: float = pydantic.Field(100.0, ge=0, le=100)
    priority: int = pydantic.Field(1, ge=1)

    @property
    def target_key(self) -> str:
        return self.target


class ResourceRegistration(pydantic.BaseModel):
    """All country-specific data needed to activate one resource."""

    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    resource: ResourceType
    name: str | None = pydantic.Field(None, min_length=1)
    group: ExtractionGroup | None = None
    stockpile: float = pydantic.Field(0.0, ge=0)
    storage_capacity: float = pydantic.Field(0.0, ge=0)
    accessibility: float = pydantic.Field(100.0, ge=0, le=100)
    quality: float = pydantic.Field(100.0, ge=0, le=100)
    consumption_per_month: float = pydantic.Field(
        0.0,
        ge=0,
        validation_alias=pydantic.AliasChoices(
            "consumption_per_month",
            "consumption_per_turn",
        ),
    )

    @property
    def consumption_per_turn(self) -> float:
        """Deprecated compatibility alias for the monthly consumption."""
        return self.consumption_per_month

    @pydantic.model_validator(mode="after")
    def validate_registration(self) -> ResourceRegistration:
        if self.stockpile > self.storage_capacity:
            raise ValueError("Запас на складе превышает его вместимость")
        bundled = RESOURCE_CATALOG.get(self.resource)
        if self.name is None:
            object.__setattr__(
                self,
                "name",
                bundled.name if bundled is not None else self.resource.value,
            )
        if self.group is None:
            if bundled is None:
                raise ValueError(
                    f"Для нового ресурса {self.resource.value} нужна группа"
                )
            object.__setattr__(self, "group", bundled.group)
        return self
