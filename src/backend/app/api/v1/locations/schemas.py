from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    BedStatus,
    GrowingMediumKind,
    IrrigationSystem,
    LayoutStrategy,
    LightType,
    Orientation,
    PhMethod,
    RowDirection,
    SiteWaterRegime,
    SlotRole,
    SoilConditionFlag,
    SoilDrainage,
    SoilTexture,
    SunExposure,
)
from app.domain.calculators.planting_layout_calculator import (
    MAX_LAYOUT_POSITIONS,
    MAX_SPACING_CM,
    MIN_SPACING_CM,
)
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.planting_run import MAX_EDGE_MARGIN_CM

__all__ = ["LocationPatch"]  # the PATCH body is declared in the domain: the service parses and validates it itself


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


class BedListItemResponse(LocationResponse):
    """A location in the bed list (GP-API-011): the document plus its counters.

    The counters are ``None`` on a plain listing (no ``is_bed`` / ``bed_status`` filter) — they cost three
    queries, and the plain listing is the hot path of every location picker.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "loc_b03",
                    "name": "Hochbeet 3",
                    "site_key": "site_7f3a",
                    "location_type_key": "raised_bed",
                    "area_m2": 2.0,
                    "orientation": "south",
                    "light_type": "natural",
                    "irrigation_system": "drip",
                    "bed_status": "active",
                    "active_plant_count": 6,
                    "open_task_count": 2,
                    "overdue_task_count": 0,
                    "next_due_at": "2026-06-18T00:00:00Z",
                }
            ]
        }
    )

    active_plant_count: int | None = None
    open_task_count: int | None = None
    overdue_task_count: int | None = None
    #: Earliest due date of an open task of the bed.
    next_due_at: datetime | None = None


class LocationPatchResponse(LocationResponse):
    """The stored location after a PATCH or a status change, with the site's revision (GP-API-010/018)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "loc_b03",
                    "name": "Hochbeet 3",
                    "site_key": "site_7f3a",
                    "location_type_key": "raised_bed",
                    "area_m2": 2.0,
                    "orientation": "south",
                    "light_type": "natural",
                    "irrigation_system": "drip",
                    "bed_status": "retired",
                    "plan_revision": 43,
                }
            ]
        }
    )

    plan_revision: int = 0


class LocationStatusRequest(BaseModel):
    """``POST /locations/{key}/status`` (GP-API-018)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"bed_status": "retired", "reason": "Raised bed dismantled for the new shed."}]}
    )

    bed_status: BedStatus
    reason: str | None = Field(
        default=None, min_length=1, max_length=1000, description="Required when retiring a bed (GP-FR-046)."
    )


class BedSummaryResponse(LocationResponse):
    """The head of the bed view (GP-API-012, GP-FR-047)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "loc_b03",
                    "name": "Hochbeet 3",
                    "site_key": "site_7f3a",
                    "location_type_key": "raised_bed",
                    "area_m2": 2.0,
                    "orientation": "south",
                    "light_type": "natural",
                    "irrigation_system": "drip",
                    "is_bed": True,
                    "bed_status": "active",
                    "season_state": "planted",
                    "active_plant_count": 6,
                    "species_keys": ["sp_solanum_lycopersicum"],
                    "open_task_count": 2,
                    "last_care_at": "2026-06-14T18:30:00Z",
                }
            ]
        }
    )

    is_bed: bool = False
    #: Derived, never set (§7.4): ``planted`` or ``empty`` until runs, rotation and covering exist.
    season_state: str = "empty"
    active_plant_count: int = 0
    species_keys: list[str] = Field(default_factory=list)
    open_task_count: int = 0
    overdue_task_count: int = 0
    next_due_at: datetime | None = None
    last_care_at: datetime | None = None


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


class PlantingLayoutEntryRequest(BaseModel):
    """The layout fields of one planting-run entry, in centimetres (GP-API-016, GP-FR-060)."""

    layout_strategy: LayoutStrategy = LayoutStrategy.GRID
    spacing_cm: float = Field(ge=MIN_SPACING_CM, le=MAX_SPACING_CM)
    row_spacing_cm: float | None = Field(
        default=None,
        ge=MIN_SPACING_CM,
        le=MAX_SPACING_CM,
        description="Required for `rows`; `grid` and `triangular` derive it from `spacing_cm`.",
    )
    row_direction: RowDirection = RowDirection.ALONG_LENGTH
    edge_margin_along_cm: float | None = Field(
        default=None, ge=0, le=MAX_EDGE_MARGIN_CM, description="Default `spacing_cm / 2` (0 for a zone)."
    )
    edge_margin_across_cm: float | None = Field(
        default=None, ge=0, le=MAX_EDGE_MARGIN_CM, description="Default `row_spacing / 2` (0 for a zone)."
    )
    row_assignment: list[int] | None = Field(
        default=None, max_length=MAX_LAYOUT_POSITIONS, description="Row indices (0-based) this entry occupies."
    )
    mature_width_cm: float | None = Field(
        default=None, gt=0, le=MAX_SPACING_CM, description="Steckbrief width; only drives the spacing warning."
    )
    max_count: int | None = Field(default=None, ge=1, le=MAX_LAYOUT_POSITIONS)


class PlantingLayoutPreviewRequest(BaseModel):
    """``POST /locations/{key}/planting-layout/preview`` (GP-API-016)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entry": {
                        "layout_strategy": "rows",
                        "spacing_cm": 30,
                        "row_spacing_cm": 40,
                        "edge_margin_along_cm": 15,
                        "edge_margin_across_cm": 15,
                    }
                }
            ]
        }
    )

    entry: PlantingLayoutEntryRequest


class PlantingLayoutSlotResponse(BaseModel):
    """One planned slot: a `position` point or a `zone` polygon in the bed frame (§9.2)."""

    slot_role: SlotRole
    geometry: BedFrameGeometry
    row_index: int | None = None
    sequence: int
    capacity_plants: int


class PlantingLayoutWarningResponse(BaseModel):
    """A hint that never blocks (GP-FR-062, V-07)."""

    code: str
    detail: dict[str, float] = Field(default_factory=dict)


class PlantingLayoutPreviewResponse(BaseModel):
    """What the bed would hold, without persisting anything (GP-API-016)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "slots": [
                        {
                            "slot_role": "position",
                            "geometry": {"kind": "point", "origin": [0.15, 0.15]},
                            "row_index": 0,
                            "sequence": 1,
                            "capacity_plants": 1,
                        }
                    ],
                    "count": 30,
                    "capacity_max": 30,
                    "warnings": [],
                }
            ]
        }
    )

    slots: list[PlantingLayoutSlotResponse]
    count: int
    capacity_max: int
    warnings: list[PlantingLayoutWarningResponse]
