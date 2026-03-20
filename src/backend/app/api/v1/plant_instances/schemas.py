from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import SubstrateType


class PlantCreate(BaseModel):
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    substrate_key: str | None = None
    plant_name: str | None = None
    planted_on: date
    current_phase_key: str | None = None
    container_volume_liters: float | None = Field(default=None, ge=0.1, le=500)
    substrate_type_override: SubstrateType | None = None


class PlantResponse(BaseModel):
    key: str
    instance_id: str
    species_key: str
    cultivar_key: str | None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None
    substrate_batch_key: str | None
    substrate_key: str | None = None
    plant_name: str | None
    planted_on: date
    removed_on: date | None
    current_phase: str = ""
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    container_volume_liters: float | None = None
    substrate_type_override: SubstrateType | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ValidatePlantingRequest(BaseModel):
    species_key: str


class ValidatePlantingResponse(BaseModel):
    valid: bool
    warnings: list[str]
    benefits: list[str]


class ActiveChannelDosage(BaseModel):
    fertilizer_key: str
    product_name: str
    ml_per_liter: float
    optional: bool = False
    mixing_priority: int = 50


class ActiveChannelResponse(BaseModel):
    channel_id: str
    label: str
    application_method: str
    target_ec_ms: float | None = None
    target_ph: float | None = None
    plan_key: str
    plan_name: str
    entry_key: str | None = None
    phase_name: str
    week_start: int
    week_end: int
    dosages: list[ActiveChannelDosage] = Field(default_factory=list)


class AssignNutrientPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""
