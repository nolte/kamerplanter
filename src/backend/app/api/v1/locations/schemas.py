from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    TerminationType,
)
from app.domain.calculators.planting_layout_calculator import (
    MAX_LAYOUT_POSITIONS,
    EntryLayout,
    LayoutResult,
)
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.planting_reservation import PlantingRow, QuickPlantingInput
from app.domain.models.planting_run import MAX_EDGE_MARGIN_CM, MAX_SPACING_CM, MIN_SPACING_CM, check_row_assignment

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"layout_strategy": "triangular", "spacing_cm": 40, "mature_width_cm": 60, "max_count": 24},
                {"layout_strategy": "rows", "spacing_cm": 30, "row_spacing_cm": 40, "row_assignment": [0, 2]},
            ]
        }
    )

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

    @field_validator("row_assignment")
    @classmethod
    def validate_row_assignment(cls, value: list[int] | None) -> list[int] | None:
        return check_row_assignment(value)

    def to_layout(self) -> EntryLayout:
        """The calculator's input; ``max_count`` travels beside it."""
        return EntryLayout(
            layout_strategy=self.layout_strategy,
            spacing_cm=self.spacing_cm,
            row_spacing_cm=self.row_spacing_cm,
            row_direction=self.row_direction,
            edge_margin_along_cm=self.edge_margin_along_cm,
            edge_margin_across_cm=self.edge_margin_across_cm,
            row_assignment=None if self.row_assignment is None else tuple(self.row_assignment),
            mature_width_cm=self.mature_width_cm,
        )


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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "slot_role": "position",
                    "geometry": {"kind": "point", "origin": [0.15, 0.55]},
                    "row_index": 1,
                    "sequence": 11,
                    "capacity_plants": 1,
                }
            ]
        }
    )

    slot_role: SlotRole
    geometry: BedFrameGeometry
    row_index: int | None = None
    sequence: int
    capacity_plants: int


class PlantingLayoutWarningResponse(BaseModel):
    """A hint that never blocks (GP-FR-062, V-07)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": "layout.spacing_below_mature_width", "detail": {"spacing_cm": 30.0, "mature_width_cm": 50.0}}
            ]
        }
    )

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

    @classmethod
    def from_result(cls, result: LayoutResult) -> PlantingLayoutPreviewResponse:
        """The wire form of a layout; slot geometries are bed-frame points (positions) or polygons (zones)."""
        slots = [
            PlantingLayoutSlotResponse.model_validate(
                {
                    "slot_role": slot.slot_role,
                    "geometry": (
                        {"kind": "point", "origin": list(slot.point)}
                        if slot.point is not None
                        else {"kind": "polygon", "points": [list(p) for p in slot.outline or ()]}
                    ),
                    "row_index": slot.row_index,
                    "sequence": slot.sequence,
                    "capacity_plants": slot.capacity_plants,
                }
            )
            for slot in result.slots
        ]
        return cls(
            slots=slots,
            count=result.count,
            capacity_max=result.capacity_max,
            warnings=[PlantingLayoutWarningResponse(code=w.code, detail=w.detail) for w in result.warnings],
        )


# ── Plantings of a bed, clearing and quick planting (REQ-053 WP 3.2) ─────────────────────────────


class PlantingItemResponse(BaseModel):
    """One line of `GET /locations/{key}/plantings`: a planned position or a plant (§11.3)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "state": "planned",
                    "slot_key": "8841",
                    "slot_id": "BEET3_011",
                    "species_key": "5120",
                    "run_key": "9302",
                    "entry_key": "9303",
                    "sequence": 11,
                    "planned_from": "2026-05-15",
                    "planned_until": "2026-09-30",
                }
            ]
        }
    )

    state: str = Field(description="`planned`, `active`, `harvested` or `historical`.")
    slot_key: str | None = None
    slot_id: str | None = None
    species_key: str
    cultivar_key: str | None = None
    plant_key: str | None = None
    instance_id: str | None = None
    run_key: str | None = None
    entry_key: str | None = None
    sequence: int | None = None
    planted_on: date | None = None
    removed_on: date | None = None
    termination_type: str | None = None
    planned_from: date | None = None
    planned_until: date | None = None

    @classmethod
    def from_row(cls, row: PlantingRow) -> PlantingItemResponse:
        return cls(
            state=row.state,
            slot_key=row.slot_key,
            slot_id=row.slot_id,
            species_key=row.species_key,
            cultivar_key=row.cultivar_key,
            plant_key=row.plant_key,
            instance_id=row.instance_id,
            run_key=row.run_key,
            entry_key=row.entry_key,
            sequence=row.sequence,
            planted_on=row.planted_on,
            removed_on=row.removed_on,
            termination_type=row.termination_type,
            planned_from=row.planned_from,
            planned_until=row.planned_until,
        )


class ClearBedRequest(BaseModel):
    """Body of `POST /locations/{key}/clear` (GP-API-019)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"termination_type": "senesced"}]})

    termination_type: TerminationType = Field(description="How the plants ended: harvested, senesced, died, cancelled.")
    reason: str | None = Field(default=None, max_length=1000)


class ClearBedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plants_removed": 12,
                    "runs_completed": 2,
                    "slots_archived": 12,
                    "slots_released": 0,
                    "care_event_key": "9417",
                }
            ]
        }
    )

    plants_removed: int
    runs_completed: int
    slots_archived: int
    slots_released: int
    care_event_key: str


class QuickPlantingRequest(QuickPlantingInput):
    """Body of `POST /locations/{key}/quick-planting` (GP-API-017): *I planted n of this species here*."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"species_key": "5120", "quantity": 12, "layout_strategy": "grid", "spacing_cm": 40},
                {"species_key": "5120", "quantity": 6},
            ]
        },
    )


class QuickPlantingResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_key": "9302",
                    "entry_key": "9303",
                    "slot_keys": ["8841", "8842"],
                    "plant_keys": ["7001", "7002"],
                    "instance_ids": ["BEET3_SOL_01", "BEET3_SOL_02"],
                    "warnings": [],
                }
            ]
        }
    )

    run_key: str
    entry_key: str
    slot_keys: list[str]
    plant_keys: list[str]
    instance_ids: list[str]
    warnings: list[str] = Field(
        default_factory=list,
        description="Hints that never block, e.g. `layout.bed_without_geometry`, `layout.capacity_exceeded`.",
    )
