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
    installed_on: date | None = None
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


# ── Relationship schemas ────────────────────────────────────────────

class FeedsFromRequest(BaseModel):
    source_tank_key: str
