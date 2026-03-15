from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Tank schemas ────────────────────────────────────────────────────


class TankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tank_type: str
    volume_liters: float = Field(gt=0)
    material: str = "plastic"
    has_lid: bool = False
    has_air_pump: bool = False
    has_circulation_pump: bool = False
    has_heater: bool = False
    is_light_proof: bool = False
    has_uv_sterilizer: bool = False
    has_ozone_generator: bool = False
    installed_on: date | None = None
    location_key: str | None = None
    notes: str | None = None


class TankUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    tank_type: str | None = None
    volume_liters: float | None = Field(default=None, gt=0)
    material: str | None = None
    has_lid: bool | None = None
    has_air_pump: bool | None = None
    has_circulation_pump: bool | None = None
    has_heater: bool | None = None
    is_light_proof: bool | None = None
    has_uv_sterilizer: bool | None = None
    has_ozone_generator: bool | None = None
    installed_on: date | None = None
    location_key: str | None = None
    notes: str | None = None


class TankResponse(BaseModel):
    key: str
    name: str
    tank_type: str
    volume_liters: float
    material: str
    has_lid: bool
    has_air_pump: bool
    has_circulation_pump: bool
    has_heater: bool
    is_light_proof: bool = False
    has_uv_sterilizer: bool = False
    has_ozone_generator: bool = False
    installed_on: date | None
    location_key: str | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── TankState schemas ───────────────────────────────────────────────


class TankStateCreate(BaseModel):
    fill_level_liters: float | None = Field(default=None, ge=0)
    fill_level_percent: float | None = Field(default=None, ge=0, le=100)
    ph: float | None = Field(default=None, ge=0, le=14)
    ec_ms: float | None = Field(default=None, ge=0)
    water_temp_celsius: float | None = Field(default=None, ge=0, le=50)
    tds_ppm: float | None = Field(default=None, ge=0)
    dissolved_oxygen_mgl: float | None = Field(default=None, ge=0, le=20)
    orp_mv: int | None = Field(default=None, ge=-500, le=1000)
    source: str = "manual"


class TankStateResponse(BaseModel):
    key: str
    tank_key: str
    recorded_at: datetime | None
    fill_level_liters: float | None
    fill_level_percent: float | None
    ph: float | None
    ec_ms: float | None
    water_temp_celsius: float | None
    tds_ppm: float | None
    dissolved_oxygen_mgl: float | None = None
    orp_mv: int | None = None
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── MaintenanceLog schemas ──────────────────────────────────────────


class MaintenanceLogCreate(BaseModel):
    maintenance_type: str
    performed_by: str = ""
    duration_minutes: int | None = Field(default=None, ge=0)
    products_used: list[str] = Field(default_factory=list)
    notes: str | None = None


class MaintenanceLogResponse(BaseModel):
    key: str
    tank_key: str
    maintenance_type: str
    performed_at: datetime | None
    performed_by: str
    duration_minutes: int | None
    products_used: list[str]
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── MaintenanceSchedule schemas ─────────────────────────────────────


class MaintenanceScheduleCreate(BaseModel):
    maintenance_type: str
    interval_days: int = Field(gt=0)
    reminder_days_before: int = Field(default=3, ge=0)
    is_active: bool = True
    priority: str = "medium"
    auto_create_task: bool = False
    instructions: str | None = None


class MaintenanceScheduleUpdate(BaseModel):
    interval_days: int | None = Field(default=None, gt=0)
    reminder_days_before: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    priority: str | None = None
    auto_create_task: bool | None = None
    instructions: str | None = None


class MaintenanceScheduleResponse(BaseModel):
    key: str
    tank_key: str
    maintenance_type: str
    interval_days: int
    reminder_days_before: int
    is_active: bool
    priority: str
    auto_create_task: bool
    instructions: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Alert & Due Maintenance schemas ─────────────────────────────────


class AlertResponse(BaseModel):
    type: str
    severity: str
    message: str
    value: float


class DueMaintenanceResponse(BaseModel):
    tank_key: str
    tank_name: str | None = None
    schedule_key: str | None
    maintenance_type: str
    next_due: str
    days_until: float
    status: str
    priority: str


# ── TankFillEvent schemas ──────────────────────────────────────────


class FertilizerSnapshotSchema(BaseModel):
    product_key: str | None = None
    product_name: str
    ml_per_liter: float = Field(gt=0)


class TankFillEventCreate(BaseModel):
    fill_type: str
    volume_liters: float = Field(gt=0)
    mixing_result_key: str | None = None
    nutrient_plan_key: str | None = None
    target_ec_ms: float | None = Field(default=None, ge=0)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    measured_ec_ms: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    water_source: str | None = None
    water_mix_ratio_ro_percent: float | None = Field(default=None, ge=0, le=100)
    source_tank_key: str | None = None
    fertilizers_used: list[FertilizerSnapshotSchema] = Field(default_factory=list)
    base_water_ec_ms: float | None = Field(default=None, ge=0)
    chlorine_ppm: float | None = Field(default=None, ge=0)
    chloramine_ppm: float | None = Field(default=None, ge=0)
    alkalinity_ppm: float | None = Field(default=None, ge=0)
    is_organic_fertilizers: bool = False
    performed_by: str | None = None
    notes: str | None = None


class TankFillEventResponse(BaseModel):
    key: str
    tank_key: str
    filled_at: datetime | None
    fill_type: str
    volume_liters: float
    mixing_result_key: str | None = None
    nutrient_plan_key: str | None = None
    target_ec_ms: float | None = None
    target_ph: float | None = None
    measured_ec_ms: float | None = None
    measured_ph: float | None = None
    water_source: str | None = None
    water_mix_ratio_ro_percent: float | None = None
    source_tank_key: str | None = None
    fertilizers_used: list[FertilizerSnapshotSchema] = Field(default_factory=list)
    base_water_ec_ms: float | None = None
    chlorine_ppm: float | None = None
    chloramine_ppm: float | None = None
    alkalinity_ppm: float | None = None
    is_organic_fertilizers: bool = False
    performed_by: str | None = None
    notes: str | None = None
    water_defaults_source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TankFillEventStatsResponse(BaseModel):
    fill_type_counts: dict[str, int]
    total_volume_liters: float
    total_count: int
    avg_ec_deviation_ms: float | None = None


class FillEventResultResponse(BaseModel):
    fill_event: TankFillEventResponse
    tank_state: TankStateResponse | None = None
    warnings: list[str] = Field(default_factory=list)
    water_defaults_source: str | None = None


# ── Relationship schemas ────────────────────────────────────────────


class FeedsFromRequest(BaseModel):
    source_tank_key: str


class LocationTankValidationResponse(BaseModel):
    valid: bool
    warnings: list[str] = Field(default_factory=list)


# ── Sensor schemas ─────────────────────────────────────────────────


class SensorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    metric_type: str
    ha_entity_id: str | None = None
    mqtt_topic: str | None = None
    tank_key: str | None = None


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    metric_type: str | None = None
    ha_entity_id: str | None = None
    mqtt_topic: str | None = None
    is_active: bool | None = None


class SensorResponse(BaseModel):
    key: str
    name: str
    metric_type: str
    ha_entity_id: str | None = None
    mqtt_topic: str | None = None
    tank_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    is_active: bool


class HAEntitySuggestion(BaseModel):
    entity_id: str
    friendly_name: str
    unit_of_measurement: str | None = None
    device_class: str | None = None
    state: str | None = None
    suggested_metric_type: str | None = None
    suggested_name: str | None = None


class LiveValueEntry(BaseModel):
    value: float
    last_changed: str | None = None
    entity_id: str | None = None
    unit: str | None = None


class LiveStateResponse(BaseModel):
    values: dict[str, LiveValueEntry] = Field(default_factory=dict)
    errors: list[dict] = Field(default_factory=list)
    source: str
    message: str | None = None


# ── Active Nutrient Plan schemas ──────────────────────────────────


class ActivePlanFertilizerInfo(BaseModel):
    key: str
    product_name: str
    brand: str = ""
    fertilizer_type: str
    npk_ratio: list[float] = Field(default_factory=list)
    ec_contribution_per_ml: float = 0.0
    mixing_priority: int = 50


class ActiveNutrientPlanResponse(BaseModel):
    run_key: str
    run_name: str
    run_status: str
    plan_key: str
    plan_name: str
    current_phase: str | None = None
    plant_count: int = 0
    current_phase_entry: dict | None = None
    all_phase_entries: list[dict] = Field(default_factory=list)
    fertilizers: list[ActivePlanFertilizerInfo] = Field(default_factory=list)
    watering_schedule: dict | None = None
    water_mix_ratio_ro_percent: int | None = None
