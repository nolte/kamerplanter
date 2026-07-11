"""REQ-026 Aquaponics domain models.

Fish/plant closed-loop systems couple a fish stock, a nitrifying biofilter and a
grow bed. The nitrogen cycle (ammonia -> nitrite -> nitrate) is the core
monitoring concept; ``WaterTest`` records are immutable measurements from which
the free (unionised) ammonia fraction is derived (Emerson et al. 1975).

Source code is English (NFR-003); the specification lives in
``spec/req/REQ-026_Aquaponik-Management.md`` (German).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    AquaponicSupplementType,
    AquaponicSystemType,
    BiofilterType,
    ClarifierType,
    CyclingStatus,
    FishFeedCategory,
    FishFeedingResponse,
    FishFeedType,
    TemperatureZone,
    WaterTestSource,
)


class RegulatoryNote(BaseModel):
    """Country-specific husbandry regulation attached to a fish species."""

    country: str  # ISO 3166-1 alpha-2, e.g. "DE", "AT", "CH"
    regulation: str
    requirement: str
    hobby_exempt: bool = False


class FishSpecies(BaseModel):
    """Global fish-species master data (seed data, not tenant-scoped)."""

    key: str | None = Field(default=None, alias="_key")
    scientific_name: str = Field(min_length=1)
    common_name_de: str = Field(min_length=1)
    common_name_en: str = Field(min_length=1)
    temperature_zone: TemperatureZone
    temperature_min_c: float
    temperature_max_c: float
    temperature_optimal_min_c: float
    temperature_optimal_max_c: float
    temperature_lethal_low_c: float
    temperature_lethal_high_c: float
    ph_min: float
    ph_max: float
    do_minimum_mgl: float
    do_optimal_mgl: float
    do_stress_mgl: float
    max_tan_mgl: float
    max_nitrite_mgl: float
    max_nitrate_mgl: float
    fcr_hobby: float | None = None
    fcr_professional: float | None = None
    feed_type: FishFeedCategory
    max_stocking_density_kg_per_1000l: float
    max_stocking_density_professional_kg_per_1000l: float | None = None
    growth_rate_g_per_day: float | None = None
    market_weight_g: float | None = None
    time_to_market_days: int | None = None
    schooling: bool = False
    min_group_size: int = 1
    regulatory_notes: list[RegulatoryNote] = Field(default_factory=list)
    notes_de: str | None = None
    notes_en: str | None = None

    model_config = {"populate_by_name": True}


class AquaponicSystem(BaseModel):
    """A coupled fish/plant recirculating system owned by exactly one tenant."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    system_type: AquaponicSystemType
    total_volume_liters: float = Field(gt=0)
    grow_area_m2: float = Field(gt=0)
    cycling_status: CyclingStatus = CyclingStatus.NEW
    cycling_start_date: date | None = None
    cycled_since: date | None = None
    biofilter_type: BiofilterType | None = None
    biofilter_volume_liters: float | None = Field(default=None, gt=0)
    biofilter_media_ssa_m2_per_m3: float | None = None
    has_clarifier: bool = False
    clarifier_type: ClarifierType | None = None
    has_mineralization: bool = False
    has_vermicompost: bool = False
    daily_feed_target_g: float = Field(default=0, ge=0)
    turnover_rate_per_hour: float | None = None
    outdoor: bool = False
    backup_power: bool = False
    ph_target_min: float = Field(default=6.8, ge=5.0, le=9.0)
    ph_target_max: float = Field(default=7.2, ge=5.0, le=9.0)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class FishStock(BaseModel):
    """A cohort of fish of one species held inside a system."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    system_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    species_key: str
    count: int = Field(ge=0)
    initial_count: int = Field(ge=0)
    avg_weight_g: float = Field(gt=0)
    total_biomass_kg: float = Field(default=0, ge=0)
    stocking_date: date
    mortality_count: int = Field(default=0, ge=0)
    last_weighed_at: date | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _derive_biomass(self) -> FishStock:
        self.total_biomass_kg = round(self.count * self.avg_weight_g / 1000, 4)
        return self


class WaterTest(BaseModel):
    """An immutable water-test measurement; ``free_ammonia_mgl`` is derived."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    system_key: str = ""
    tested_at: datetime | None = None
    ph: float = Field(ge=0, le=14)
    ammonia_tan_mgl: float = Field(ge=0)
    nitrite_mgl: float = Field(ge=0)
    nitrate_mgl: float = Field(ge=0)
    temperature_c: float = Field(ge=0, le=45)
    dissolved_oxygen_mgl: float | None = Field(default=None, ge=0)
    kh_dh: float | None = Field(default=None, ge=0)
    gh_dh: float | None = Field(default=None, ge=0)
    iron_ppm: float | None = Field(default=None, ge=0)
    potassium_ppm: float | None = Field(default=None, ge=0)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    phosphate_ppm: float | None = Field(default=None, ge=0)
    free_ammonia_mgl: float = Field(default=0, ge=0)
    source: WaterTestSource = WaterTestSource.MANUAL
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class FishFeedingEvent(BaseModel):
    """An immutable feeding event for a fish stock."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    system_key: str = ""
    stock_key: str = ""
    fed_at: datetime | None = None
    feed_brand: str | None = None
    feed_type: FishFeedType = FishFeedType.PELLET
    protein_percent: float | None = Field(default=None, ge=0, le=100)
    amount_g: float = Field(gt=0)
    water_temp_c: float = Field(ge=0, le=45)
    fish_response: FishFeedingResponse = FishFeedingResponse.NORMAL
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class SupplementationEvent(BaseModel):
    """An immutable nutrient-supplementation event for a system."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    system_key: str = ""
    applied_at: datetime | None = None
    supplement_type: AquaponicSupplementType
    amount_ml: float | None = Field(default=None, gt=0)
    amount_g: float | None = Field(default=None, gt=0)
    target_parameter: str
    measured_before: float | None = None
    measured_after: float | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
