from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import BufferCapacity, IrrigationStrategy, SubstrateType, WaterRetention


class MixComponentRequest(BaseModel):
    substrate_key: str
    fraction: float = Field(ge=0.01, le=1.0)


class SubstrateMixRequest(BaseModel):
    name_de: str = ""
    name_en: str = ""
    components: list[MixComponentRequest] = Field(min_length=2)


class MixComponentResponse(BaseModel):
    substrate_key: str
    fraction: float


class SubstrateCreate(BaseModel):
    type: SubstrateType = SubstrateType.SOIL
    brand: str | None = None
    name_de: str = ""
    name_en: str = ""
    ph_base: float = Field(default=6.5, ge=0, le=14)
    ec_base_ms: float = Field(default=0.5, ge=0)
    water_retention: WaterRetention = WaterRetention.MEDIUM
    air_porosity_percent: float = Field(default=25.0, ge=0, le=100)
    composition: dict[str, float] = Field(default_factory=dict)
    buffer_capacity: BufferCapacity = BufferCapacity.MEDIUM
    reusable: bool = False
    max_reuse_cycles: int = Field(default=3, ge=1)
    water_holding_capacity_percent: float | None = Field(default=None, ge=0, le=100)
    easily_available_water_percent: float | None = Field(default=None, ge=0, le=100)
    cec_meq_per_100g: float | None = Field(default=None, ge=0)
    particle_size_mm: float | None = Field(default=None, ge=0)
    bulk_density_g_per_l: float | None = Field(default=None, ge=0)
    irrigation_strategy: IrrigationStrategy | None = None


class SubstrateResponse(BaseModel):
    key: str
    type: SubstrateType
    brand: str | None
    name_de: str = ""
    name_en: str = ""
    is_mix: bool = False
    mix_components: list[MixComponentResponse] = Field(default_factory=list)
    ph_base: float
    ec_base_ms: float
    water_retention: WaterRetention
    air_porosity_percent: float
    composition: dict[str, float]
    buffer_capacity: BufferCapacity
    reusable: bool
    max_reuse_cycles: int
    water_holding_capacity_percent: float | None = None
    easily_available_water_percent: float | None = None
    cec_meq_per_100g: float | None = None
    particle_size_mm: float | None = None
    bulk_density_g_per_l: float | None = None
    irrigation_strategy: IrrigationStrategy | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BatchCreate(BaseModel):
    batch_id: str
    substrate_key: str
    volume_liters: float = Field(ge=0)
    mixed_on: date
    temperature_c: float | None = None
    ph_history: list[float] = Field(default_factory=list)
    ec_history: list[float] = Field(default_factory=list)


class BatchResponse(BaseModel):
    key: str
    batch_id: str
    substrate_key: str
    volume_liters: float
    mixed_on: date
    last_amended: date | None
    cycles_used: int
    ph_current: float | None
    ec_current_ms: float | None
    temperature_c: float | None = None
    ph_history: list[float] = Field(default_factory=list)
    ec_history: list[float] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PreparationStep(BaseModel):
    step: str
    hours: float


class ReusabilityResponse(BaseModel):
    can_reuse: bool
    treatments: list[str] = Field(default_factory=list)
    preparation_steps: list[PreparationStep] = Field(default_factory=list)
    estimated_prep_time_hours: float = 0
    ready_date: date | None = None


class PreparationResponse(BaseModel):
    can_reuse: bool
    issues: list[str] = Field(default_factory=list)
    preparation_steps: list[PreparationStep] = Field(default_factory=list)
    estimated_prep_time_hours: float = 0
    ready_date: date | None = None
