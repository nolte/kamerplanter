from datetime import datetime

from pydantic import BaseModel, Field


class WateringLogFertilizerSchema(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0)


class WateringLogCreate(BaseModel):
    application_method: str = "drench"
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    plant_keys: list[str] = Field(default_factory=list)
    slot_keys: list[str] = Field(default_factory=list)
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    channel_id: str | None = None
    fertilizers_used: list[WateringLogFertilizerSchema] = Field(default_factory=list)
    ec_before: float | None = Field(default=None, ge=0)
    ec_after: float | None = Field(default=None, ge=0)
    ph_before: float | None = Field(default=None, ge=0, le=14)
    ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    water_source: str | None = None
    performed_by: str | None = None
    notes: str | None = None


class WateringLogUpdate(BaseModel):
    application_method: str | None = None
    is_supplemental: bool | None = None
    volume_liters: float | None = Field(default=None, gt=0)
    ec_before: float | None = Field(default=None, ge=0)
    ec_after: float | None = Field(default=None, ge=0)
    ph_before: float | None = Field(default=None, ge=0, le=14)
    ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    notes: str | None = None


class ResolvedPlant(BaseModel):
    key: str
    name: str


class ResolvedFertilizer(BaseModel):
    key: str
    name: str
    ml_per_liter: float


class WateringLogResponse(BaseModel):
    key: str
    logged_at: datetime | None
    application_method: str
    is_supplemental: bool
    volume_liters: float
    plant_keys: list[str]
    slot_keys: list[str]
    tank_fill_event_key: str | None
    nutrient_plan_key: str | None
    task_key: str | None
    channel_id: str | None
    fertilizers_used: list[WateringLogFertilizerSchema]
    ec_before: float | None
    ec_after: float | None
    ph_before: float | None
    ph_after: float | None
    runoff_ec: float | None
    runoff_ph: float | None
    runoff_volume_liters: float | None
    water_source: str | None
    performed_by: str | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_plants: list[ResolvedPlant] = Field(default_factory=list)
    resolved_fertilizers: list[ResolvedFertilizer] = Field(default_factory=list)


class WateringLogWithWarnings(BaseModel):
    log: WateringLogResponse
    warnings: list[dict]


class MethodStats(BaseModel):
    method: str
    count: int
    total_volume: float


class WateringStatsResponse(BaseModel):
    total_events: int
    total_volume: float
    by_method: list[MethodStats]


class WateringConfirmRequest(BaseModel):
    run_key: str
    task_key: str
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    volume_liters: float | None = Field(default=None, gt=0)
    overrides: dict | None = None


class WateringQuickConfirmRequest(BaseModel):
    run_key: str
    task_key: str


class WateringConfirmResponse(BaseModel):
    watering_log_key: str
    task_completed: bool
    warnings: list[dict] = Field(default_factory=list)
