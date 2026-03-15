import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from app.common.enums import IrrigationSystem, LightType, Orientation, SiteType

if TYPE_CHECKING:
    from datetime import date, datetime


class TapWaterProfile(BaseModel):
    ec_ms: float = Field(ge=0, le=2.0)
    ph: float = Field(ge=3.0, le=10.0)
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    gh_ppm: float = Field(default=0, ge=0, le=1000)
    calcium_ppm: float = Field(default=0, ge=0, le=500)
    magnesium_ppm: float = Field(default=0, ge=0, le=200)
    chlorine_ppm: float = Field(default=0, ge=0, le=5)
    chloramine_ppm: float = Field(default=0, ge=0, le=5)
    measurement_date: date | None = None
    source_note: str | None = None


class RoWaterProfile(BaseModel):
    ec_ms: float = Field(default=0.02, ge=0, le=0.5)
    ph: float = Field(default=6.5, ge=3.0, le=10.0)


class SiteWaterConfig(BaseModel):
    has_ro_system: bool = False
    tap_water_profile: TapWaterProfile | None = None
    ro_water_profile: RoWaterProfile | None = None


class Slot(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    slot_id: str
    location_key: str = ""
    position: tuple[int, int] = (0, 0)
    capacity_plants: int = Field(default=1, ge=1, le=20)
    currently_occupied: bool = False
    last_sanitization: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("slot_id")
    @classmethod
    def validate_slot_id(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError("Slot ID must be all uppercase")
        if "_" not in v:
            raise ValueError("Slot ID must follow format 'LOCATION_POSITION' (e.g., 'TENT01_A1')")
        return v


class Location(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    site_key: str = ""
    parent_location_key: str | None = None
    location_type_key: str = ""
    depth: int = 0
    path: str = ""
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    dimensions: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("lights_on", "lights_off")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.match(r"^\d{2}:\d{2}$", v):
                raise ValueError("Time must be in HH:MM format")
            hours, minutes = v.split(":")
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError("Invalid time value")
        return v


class Site(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str
    type: SiteType = SiteType.INDOOR
    gps_coordinates: tuple[float, float] | None = None
    climate_zone: str = ""
    total_area_m2: float = Field(default=0.0, ge=0)
    timezone: str = "UTC"
    water_config: SiteWaterConfig | None = None
    # ── Frost dates (REQ-015 §3.8) ──
    last_frost_date_avg: date | None = None
    first_frost_date_avg: date | None = None
    eisheilige_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("gps_coordinates")
    @classmethod
    def validate_gps(cls, v: tuple[float, float] | None) -> tuple[float, float] | None:
        if v is not None:
            lat, lon = v
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v
