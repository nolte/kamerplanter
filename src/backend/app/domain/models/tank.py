from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    FillType,
    MaintenancePriority,
    MaintenanceType,
    TankMaterial,
    TankType,
    WaterSource,
)

if TYPE_CHECKING:
    from datetime import date, datetime


class Tank(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    tank_type: TankType
    volume_liters: float = Field(gt=0)
    material: TankMaterial = TankMaterial.PLASTIC
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TankState(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tank_key: str = ""
    recorded_at: datetime | None = None
    fill_level_liters: float | None = Field(default=None, ge=0)
    fill_level_percent: float | None = Field(default=None, ge=0, le=100)
    ph: float | None = Field(default=None, ge=0, le=14)
    ec_ms: float | None = Field(default=None, ge=0)
    water_temp_celsius: float | None = Field(default=None, ge=0, le=50)
    tds_ppm: float | None = Field(default=None, ge=0)
    dissolved_oxygen_mgl: float | None = Field(default=None, ge=0, le=20)
    orp_mv: int | None = Field(default=None, ge=-500, le=1000)
    source: str = "manual"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class MaintenanceLog(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tank_key: str = ""
    maintenance_type: MaintenanceType
    performed_at: datetime | None = None
    performed_by: str = ""
    duration_minutes: int | None = Field(default=None, ge=0)
    products_used: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class MaintenanceSchedule(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tank_key: str = ""
    maintenance_type: MaintenanceType
    interval_days: int = Field(gt=0)
    reminder_days_before: int = Field(default=3, ge=0)
    is_active: bool = True
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    auto_create_task: bool = False
    instructions: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_reminder_before_interval(self) -> MaintenanceSchedule:
        if self.reminder_days_before >= self.interval_days:
            raise ValueError(
                f"reminder_days_before ({self.reminder_days_before}) "
                f"must be less than interval_days ({self.interval_days})"
            )
        return self


class FertilizerSnapshot(BaseModel):
    """Lightweight snapshot of a fertilizer used in a fill event."""

    product_key: str | None = None
    product_name: str
    ml_per_liter: float = Field(gt=0)


class TankFillEvent(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tank_key: str = ""
    filled_at: datetime | None = None
    fill_type: FillType
    volume_liters: float = Field(gt=0)
    mixing_result_key: str | None = None
    nutrient_plan_key: str | None = None
    target_ec_ms: float | None = Field(default=None, ge=0)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    measured_ec_ms: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    water_source: WaterSource | None = None
    water_mix_ratio_ro_percent: float | None = Field(default=None, ge=0, le=100)
    source_tank_key: str | None = None
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)
    base_water_ec_ms: float | None = Field(default=None, ge=0)
    chlorine_ppm: float | None = Field(default=None, ge=0)
    chloramine_ppm: float | None = Field(default=None, ge=0)
    alkalinity_ppm: float | None = Field(default=None, ge=0)
    is_organic_fertilizers: bool = False
    performed_by: str | None = None
    notes: str | None = None
    water_defaults_source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_adjustment_requires_target(self) -> TankFillEvent:
        if self.fill_type == FillType.ADJUSTMENT and self.target_ec_ms is None and self.target_ph is None:
            raise ValueError("Adjustment fill type requires at least target_ec_ms or target_ph")
        return self
