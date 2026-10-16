from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    BedStatus,
    GrowingMediumKind,
    IrrigationSystem,
    LightType,
    Orientation,
    PhMethod,
    SiteWaterRegime,
    SoilConditionFlag,
    SoilDrainage,
    SoilTexture,
    SunExposure,
)
from app.domain.models.geometry import Geometry


class LocationCreate(BaseModel):
    name: str
    site_key: str
    parent_location_key: str | None = None
    location_type_key: str = ""
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None
    #: Frost exposure override (Issue #706). ``None`` inherits from the site
    #: type; ``True``/``False`` force frost-exposed / protected respectively.
    frost_exposed: bool | None = None


class SoilProfileSchema(BaseModel):
    """The v1 soil profile of a bed (REQ-053 §15.1, GP-FR-120/121)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"soil_texture": "loam", "drainage": "good", "ph": 6.5, "humus_percent": 4.0}]}
    )

    growing_medium_kind: GrowingMediumKind | None = None
    soil_texture: SoilTexture = SoilTexture.UNKNOWN
    drainage: SoilDrainage = SoilDrainage.UNKNOWN
    site_water_regime: SiteWaterRegime = SiteWaterRegime.UNKNOWN
    conditions: list[SoilConditionFlag] = Field(default_factory=list)
    substrate_key: str | None = None
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    ph_method: PhMethod | None = None
    ec_ms_cm: float | None = Field(default=None, ge=0.0)
    humus_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    notes: str | None = Field(default=None, max_length=4000)


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
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None
    #: Frost exposure override (Issue #706); ``None`` inherits from the site type.
    frost_exposed: bool | None = None
    # ── Garden plan (REQ-053 §20.3, §10.1, WP 1.7) — read-only here; PATCH arrives with WP 1.9 ──
    description: str | None = None
    #: Plan frame (§9.2); ``None`` = not placed on the plan (GP-ACC-035).
    geometry: Geometry | None = None
    height_m: float | None = None
    #: ``[min_x, min_y, max_x, max_y]``, derived from ``geometry`` (GP-FR-007).
    bbox: tuple[float, float, float, float] | None = None
    bed_status: BedStatus = BedStatus.ACTIVE
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    irrigation_zone_key: str | None = None
    soil_profile: SoilProfileSchema | None = None
    notes: str | None = None
    locked: bool = False
    z_order: int = 0
    pitch_m: float | None = None
    rotation_exempt: bool = False
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
    """Reactive frost-warning state backing ``binary_sensor.kp_{location}_frost_warning``.

    ``frost_warning`` is the *reactive* state (current ambient temperature); it is
    ``None`` when no reading is available (Home Assistant surfaces this as
    ``unknown``). Its meaning is unchanged so the HA coordinator does not break.

    The proactive forecast early-warning is served once per site via
    ``GET /sites/{site_key}/weather-forecast`` (Issue #409, F1) rather than carried
    on this per-location response.
    """

    location_key: str
    frost_warning: bool | None
    temperature_celsius: float | None = None
    threshold_celsius: float
    source: str
    entity_id: str | None = None
