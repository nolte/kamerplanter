from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import IrrigationSystem, LightType, Orientation


class LocationCreate(BaseModel):
    name: str
    site_key: str
    parent_location_key: str | None = None
    location_type_key: str = ""
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    dimensions: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None


class LocationResponse(BaseModel):
    key: str
    name: str
    site_key: str
    parent_location_key: str | None = None
    location_type_key: str = ""
    depth: int = 0
    path: str = ""
    area_m2: float
    orientation: Orientation | None
    light_type: LightType
    irrigation_system: IrrigationSystem
    dimensions: tuple[float, float, float]
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LocationTreeNode(BaseModel):
    key: str
    name: str
    location_type_key: str = ""
    depth: int = 0
    parent_location_key: str | None = None
    slot_count: int = 0
    active_plant_count: int = 0
    tank_name: str | None = None
    children: list[LocationTreeNode] = []


class FrostWarningResponse(BaseModel):
    """Frost-warning state backing ``binary_sensor.kp_{location}_frost_warning``.

    ``frost_warning`` is the *reactive* state (current ambient temperature); it is
    ``None`` when no reading is available (Home Assistant surfaces this as
    ``unknown``). Its meaning is unchanged so the HA coordinator does not break.

    The ``forecast_*`` fields (Issue #392) add the *proactive*, forecast-based
    early warning. They are ``None`` when no usable forecast is available (no
    coordinates, ``weather_enabled`` off, or no in-horizon record).
    """

    location_key: str
    frost_warning: bool | None
    temperature_celsius: float | None = None
    threshold_celsius: float
    source: str
    entity_id: str | None = None
    forecast_frost_warning: bool | None = None
    forecast_min_temperature: float | None = None
    forecast_expected_date: date | None = None
    forecast_source: str | None = None
