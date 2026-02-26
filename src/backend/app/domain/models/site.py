import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import IrrigationSystem, LightType, Orientation, SiteType


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
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    dimensions: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
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
    name: str
    type: SiteType = SiteType.INDOOR
    gps_coordinates: tuple[float, float] | None = None
    climate_zone: str = ""
    total_area_m2: float = Field(default=0.0, ge=0)
    timezone: str = "UTC"
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
