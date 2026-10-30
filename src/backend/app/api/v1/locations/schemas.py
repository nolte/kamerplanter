from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.v1.care_events.schemas import CareEventResponse, care_event_to_response
from app.common.enums import (
    BedStatus,
    GrowingMediumKind,
    IrrigationSystem,
    LayoutStrategy,
    LightType,
    Orientation,
    PhMethod,
    PlanRole,
    RowDirection,
    SiteWaterRegime,
    SlotRole,
    SoilConditionFlag,
    SoilDrainage,
    SoilTexture,
    SunExposure,
    TerminationType,
)
from app.config.constants import MAX_ROTATION_WINDOW_YEARS
from app.domain.calculators.plant_state_calculator import AttentionCode, Lifecycle
from app.domain.calculators.plant_state_inputs import phase_facts
from app.domain.calculators.planting_layout_calculator import (
    MAX_LAYOUT_POSITIONS,
    EntryLayout,
    LayoutResult,
)
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.planting_reservation import PlantingRow, QuickPlantingInput
from app.domain.models.planting_run import MAX_EDGE_MARGIN_CM, MAX_SPACING_CM, MIN_SPACING_CM, check_row_assignment
from app.domain.models.site import SiteConditions
from app.domain.services.bed_history_service import BedHistoryItem
from app.domain.services.plant_state_service import PlantStateEntry

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
    #: Substrate change: the crop-rotation history starts on this day (GP-FR-131).
    rotation_reset_at: date | None = None
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
    #: The bed template this bed was placed from (provenance, WP 7.9).
    template_key: str | None = None
    soil_profile: SoilProfileSchema | None = None
    site_conditions: SiteConditions | None = None
    notes: str | None = None
    locked: bool = False
    z_order: int = 0
    pitch_m: float | None = None
    #: Permanent crop: off for the crop-rotation check whatever ``rotation_enabled`` says (GP-FR-137).
    rotation_exempt: bool = False
    #: Per-bed rotation switch (#2544): ``null`` = type default (off for planter/tent/shelf), ``true`` on, ``false`` off
    rotation_enabled: bool | None = None
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


# ── Crop rotation and companion hints (REQ-053 WP 3.4) ────────────────────────────────────────────────────

RotationSeverityLiteral = Literal["OK", "INFO", "WARNING", "CRITICAL"]


class ValidatePlantingRequest(BaseModel):
    """Body of `POST /locations/{key}/validate-planting` (GP-API-025)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"species_key": "5120"},
                {"species_key": "5120", "slot_key": "8841", "rotation_window_years": 4},
            ]
        },
    )

    species_key: str = Field(min_length=1, max_length=200)
    slot_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="A slot of this bed: its neighbours (`adjacent_to`) are checked instead of the whole bed.",
    )
    rotation_window_years: int | None = Field(
        default=None,
        ge=1,
        le=MAX_ROTATION_WINDOW_YEARS,
        description="Fallback pause when neither the species nor its family names one (default 3, at most 8).",
    )


class RotationFindingResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "severity": "WARNING",
                    "code": "rotation.pause_not_elapsed",
                    "message": "Family 'Solanaceae' grew in this bed 3 year(s) ago; the pause is 4 year(s) (family).",
                    "family_key": "4410",
                    "family_name": "Solanaceae",
                    "species_key": "5120",
                    "last_year": 2023,
                    "years_since": 3,
                    "pause_years": 4,
                    "pause_source": "family",
                    "plan_role": "main_crop",
                }
            ]
        }
    )

    severity: RotationSeverityLiteral
    code: str
    message: str
    family_key: str | None = None
    #: Display name of `family_key`: the OWN family for pause findings, the OTHER family for pest-risk findings.
    #: `null` when it is not in the catalogue. Never fall back to `family_key` as a name.
    family_name: str | None = None
    species_key: str | None = None
    last_year: int | None = None
    years_since: int | None = None
    pause_years: int | None = None
    pause_source: Literal["species", "family", "default"] | None = None
    plan_role: str | None = None
    pest_risk: dict[str, Any] | None = None


class NeighbourHintResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "severity": "WARNING",
                    "code": "companion.incompatible",
                    "message": "Incompatible neighbour: Foeniculum vulgare.",
                    "species_key": "5188",
                    "slot_keys": ["8842"],
                }
            ]
        }
    )

    severity: RotationSeverityLiteral
    code: str
    message: str
    species_key: str
    slot_keys: list[str]
    score: float | None = None


class ValidatePlantingResponse(BaseModel):
    """Hints with a strength, never a blocker (D-09, GP-FR-132)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "8801",
                    "species_key": "5120",
                    "severity": "CRITICAL",
                    "rotation_applicable": True,
                    "not_applicable_reason": None,
                    "rotation_window_years": 3,
                    "rotation_reset_at": None,
                    "rotation": [
                        {
                            "severity": "CRITICAL",
                            "code": "rotation.pause_not_elapsed",
                            "message": "Family 'Brassicaceae' grew here 1 year(s) ago; the pause is 4 year(s).",
                            "family_key": "Brassicaceae",
                            "last_year": 2025,
                            "years_since": 1,
                            "pause_years": 4,
                            "pause_source": "family",
                        }
                    ],
                    "neighbour_scope": "bed",
                    "neighbours": [],
                }
            ]
        }
    )

    location_key: str
    species_key: str
    severity: RotationSeverityLiteral
    rotation_applicable: bool
    not_applicable_reason: str | None = None
    rotation_window_years: int
    rotation_reset_at: date | None = None
    rotation: list[RotationFindingResponse]
    neighbour_scope: Literal["slot", "bed"]
    neighbours: list[NeighbourHintResponse]


class RotationPlantingResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "season": "main",
                    "family_key": "Solanaceae",
                    "family_name": "Solanaceae",
                    "species_key": "5120",
                    "nutrient_demand": "heavy_feeder",
                    "plan_role": "main_crop",
                    "source": "backfill",
                    "care_event_key": "9500",
                }
            ]
        }
    )

    season: Literal["spring", "main", "autumn"] | None = None
    family_key: str | None = None
    family_name: str | None = None
    species_key: str | None = None
    nutrient_demand: str | None = Field(
        default=None, description="Species value, else the family's; `null` for a green manure and a fallow year."
    )
    plan_role: Literal["main_crop", "green_manure", "fallow"]
    source: Literal["plant", "backfill"]
    care_event_key: str | None = Field(
        default=None, description="The backfill event; cancel it with `DELETE …/history/backfill/{key}`."
    )


class RotationYearResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "year": 2025,
                    "plantings": [
                        {
                            "family_key": "Fabaceae",
                            "nutrient_demand": "light_feeder",
                            "plan_role": "main_crop",
                            "source": "plant",
                        }
                    ],
                }
            ]
        }
    )

    year: int
    plantings: list[RotationPlantingResponse]


class RotationTimelineResponse(BaseModel):
    """`GET /locations/{key}/rotation` (GP-API-039): what stood in the bed per year, newest first (GP-ACC-028)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "8801",
                    "years": 5,
                    "rotation_applicable": True,
                    "not_applicable_reason": None,
                    "rotation_reset_at": None,
                    "timeline": [
                        {
                            "year": 2025,
                            "plantings": [
                                {
                                    "family_key": "Fabaceae",
                                    "nutrient_demand": "light_feeder",
                                    "plan_role": "main_crop",
                                    "source": "plant",
                                }
                            ],
                        },
                        {"year": 2024, "plantings": []},
                    ],
                }
            ]
        }
    )

    location_key: str
    years: int
    rotation_applicable: bool
    not_applicable_reason: str | None = None
    rotation_reset_at: date | None = None
    timeline: list[RotationYearResponse]


class BackfillRequest(BaseModel):
    """Body of `POST /locations/{key}/history/backfill` (GP-API-042): *what stood here in {year}?*"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"year": 2024, "family_key": "Solanaceae", "plan_role": "main_crop"},
                {"year": 2023, "season": "spring", "species_key": "5120", "plan_role": "green_manure"},
            ]
        },
    )

    year: int = Field(description="Between the current year minus 10 and the current year minus 1.")
    season: Literal["spring", "main", "autumn"] | None = None
    species_key: str | None = Field(default=None, min_length=1, max_length=200)
    family_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Required unless a species names it or the year was a fallow year.",
    )
    plan_role: PlanRole = PlanRole.MAIN_CROP


class BackfillResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "care_event_key": "9500",
                    "year": 2024,
                    "performed_at": "2024-07-01T12:00:00Z",
                    "family_key": "Solanaceae",
                    "plan_role": "main_crop",
                }
            ]
        }
    )

    care_event_key: str
    year: int
    season: Literal["spring", "main", "autumn"] | None = None
    performed_at: datetime
    family_key: str | None = None
    species_key: str | None = None
    plan_role: Literal["main_crop", "green_manure", "fallow"]


BedHistoryKind = Literal["care_event", "plant_planted", "plant_removed", "run_started", "run_completed"]


class BedHistoryItemResponse(BaseModel):
    """One line of `GET /locations/{key}/history` (GP-API-038): a care event, or a derived planting event."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "plant_planted:pi_tom_003",
                    "kind": "plant_planted",
                    "at": "2026-05-12T00:00:00Z",
                    "category": "planting",
                    "plant_key": "pi_tom_003",
                    "species_key": "5120",
                    "plant_name": "Tomato 'Black Krim' #3",
                }
            ]
        }
    )

    #: Stable per line: `care:{key}`, `plant_planted:{plant}`, `plant_removed:{plant}`, `run_started:{run}`,
    #: `run_completed:{run}`.
    id: str
    kind: BedHistoryKind
    at: datetime
    #: The care category, or `planting` / `removal` for a derived event.
    category: str
    #: Set for `kind = care_event` only: the whole entry, as `GET /care-events/{key}` shows it.
    care_event: CareEventResponse | None = None
    plant_key: str | None = None
    species_key: str | None = None
    plant_name: str | None = None
    termination_type: str | None = None
    run_key: str | None = None
    run_name: str | None = None
    run_status: str | None = None

    @classmethod
    def from_item(cls, item: BedHistoryItem) -> BedHistoryItemResponse:
        if item.care is not None:
            event = item.care.event
            return cls(
                id=f"care:{event.key}",
                kind="care_event",
                at=event.performed_at,
                category=event.category,
                care_event=care_event_to_response(item.care),
            )
        planting = item.planting
        if planting is None:  # an item is exactly one of the two; this keeps the type honest
            raise ValueError("A history item carries a care event or a planting event.")
        ref = planting.plant_key if planting.plant_key is not None else planting.run_key
        return cls(
            id=f"{planting.kind}:{ref}",
            kind=planting.kind,
            at=planting.at,
            category=planting.category,
            plant_key=planting.plant_key,
            species_key=planting.species_key,
            plant_name=planting.plant_name,
            termination_type=planting.termination_type,
            run_key=planting.run_key,
            run_name=planting.run_name,
            run_status=planting.run_status,
        )


# ── Plant states of a bed (REQ-053 WP 3.7, GP-API-054) ───────────────────────────────────────────


class PlantPhaseResponse(BaseModel):
    """The plant's current phase with its progress (GP-FR-190 "Phase")."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "1432",
                    "name": "Flowering",
                    "elapsed_d": 21,
                    "typical_d": 60,
                    "fraction": 0.35,
                    "next_phase_eta": "2026-07-19",
                }
            ]
        }
    )

    key: str
    name: str | None = None
    elapsed_d: int = Field(ge=0, description="Whole days since the phase started (UTC calendar days).")
    typical_d: int | None = Field(default=None, description="The phase's usual length; `null` when not known.")
    fraction: float | None = Field(default=None, ge=0, le=1, description="`elapsed_d / typical_d`, at most 1.")
    next_phase_eta: date | None = Field(default=None, description="Start of the phase plus its usual length.")


class PlantAttentionResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"reason": "overdue", "count": 2}]})
    reason: AttentionCode
    count: int = Field(ge=1)


class PlantLastCareResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"watering": "2026-06-09T07:00:00Z", "feeding": "2026-06-01T07:00:00Z"}]}
    )
    watering: datetime | None = None
    feeding: datetime | None = None


class PlantNextTaskResponse(BaseModel):
    """Name, category and due day of the next open task; never its instruction or comments."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Prune suckers", "category": "pruning", "due": "2026-06-12"}]}
    )

    name: str
    category: str
    due: date | None = None


class PlantHarvestResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"ready": True, "ready_from": "2026-06-01", "harvested_total_g": 150.5}]}
    )
    ready: bool
    ready_from: date | None = None
    harvested_total_g: float | None = None


class PlantOpenTaskResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"category": "watering", "due": "2026-06-10"}]})
    category: str
    due: date | None = None


class PlantStatePhaseInputResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "1432",
                    "started_on": "2026-05-20",
                    "typical_days": 60,
                    "allows_harvest": False,
                    "is_terminal": False,
                }
            ]
        }
    )
    key: str
    started_on: date
    typical_days: int | None = None
    allows_harvest: bool = False
    is_terminal: bool = False


class PlantStateInputsResponse(BaseModel):
    """What the state was computed from, so the client port recomputes it at its own `now` (GP-FR-192).

    Categories and due days only — no task names, instructions or comments.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "open_tasks": [{"category": "watering", "due": "2026-06-10"}],
                    "open_findings": 1,
                    "frost_risk": False,
                    "harvest_batches": 0,
                    "phase": {
                        "key": "1432",
                        "started_on": "2026-05-20",
                        "typical_days": 60,
                        "allows_harvest": False,
                        "is_terminal": False,
                    },
                }
            ]
        }
    )

    open_tasks: list[PlantOpenTaskResponse]
    open_findings: int = Field(ge=0)
    frost_risk: bool
    harvest_batches: int = Field(ge=0)
    phase: PlantStatePhaseInputResponse | None = None


class PlantStateResponse(BaseModel):
    """One standing plant of a bed with its visual state and the facts of the info bubble (GP-FR-190, GP-API-054).

    Only the fields of the plant info: no notes, no user names (SR-006/SR-020).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plant_key": "7710",
                    "slot_key": "8841",
                    "slot_id": "BEET3_011",
                    "instance_id": "TOM-2026-004",
                    "species_key": "5120",
                    "species_name": "Tomato",
                    "scientific_name": "Solanum lycopersicum",
                    "cultivar_name": "Roma",
                    "planted_on": "2026-05-15",
                    "lifecycle": "active",
                    "phase": {"key": "1432", "name": "Flowering", "elapsed_d": 21, "typical_d": 60, "fraction": 0.35},
                    "last_care": {"watering": "2026-06-09T07:00:00Z"},
                    "attention": [{"reason": "problem", "count": 1}, {"reason": "overdue", "count": 2}],
                    "finding_label": "Aphids",
                    "harvest": {"ready": False},
                    "inputs": {
                        "open_tasks": [{"category": "watering", "due": "2026-06-07"}],
                        "open_findings": 1,
                        "frost_risk": False,
                        "harvest_batches": 0,
                        "phase": {"key": "1432", "started_on": "2026-05-20", "typical_days": 60},
                    },
                }
            ]
        }
    )

    plant_key: str
    slot_key: str | None = None
    slot_id: str | None = None
    instance_id: str
    species_key: str
    species_name: str | None = None
    scientific_name: str | None = None
    cultivar_name: str | None = None
    planted_on: date
    lifecycle: Lifecycle
    phase: PlantPhaseResponse | None = None
    last_care: PlantLastCareResponse
    next_task: PlantNextTaskResponse | None = None
    attention: list[PlantAttentionResponse]
    finding_label: str | None = Field(default=None, description="Label of the newest open finding, if any.")
    harvest: PlantHarvestResponse
    cover_photo_ref: str | None = Field(default=None, description="Attachment id of the cover photo, if any.")
    inputs: PlantStateInputsResponse

    @classmethod
    def from_entry(cls, entry: PlantStateEntry) -> PlantStateResponse:
        source, state = entry.source, entry.state
        phase = phase_facts(source)
        progress = state.phase_progress
        return cls(
            plant_key=source.plant_key,
            slot_key=source.slot_key,
            slot_id=source.slot_id,
            instance_id=source.instance_id,
            species_key=source.species_key,
            species_name=source.species_name,
            scientific_name=source.scientific_name,
            cultivar_name=source.cultivar_name,
            planted_on=source.planted_on,
            lifecycle=state.lifecycle,
            phase=None
            if state.phase_key is None or progress is None
            else PlantPhaseResponse(
                key=state.phase_key,
                name=source.phase_name,
                elapsed_d=progress.elapsed_d,
                typical_d=progress.typical_d,
                fraction=progress.fraction,
                next_phase_eta=progress.next_phase_eta,
            ),
            last_care=PlantLastCareResponse(watering=source.last_watering_at, feeding=source.last_feeding_at),
            next_task=None
            if source.next_task is None
            else PlantNextTaskResponse(
                name=source.next_task.name, category=source.next_task.category, due=source.next_task.due
            ),
            attention=[PlantAttentionResponse(reason=item.reason, count=item.count) for item in state.attention],
            finding_label=source.finding_label,
            harvest=PlantHarvestResponse(
                ready=state.harvest_ready,
                ready_from=state.harvest_ready_from,
                harvested_total_g=source.harvested_total_g,
            ),
            cover_photo_ref=source.cover_photo_ref,
            inputs=PlantStateInputsResponse(
                open_tasks=[PlantOpenTaskResponse(category=task.category, due=task.due) for task in source.open_tasks],
                open_findings=source.open_finding_count,
                frost_risk=entry.frost_risk,
                harvest_batches=source.harvest_batch_count,
                phase=None
                if phase is None
                else PlantStatePhaseInputResponse(
                    key=phase.key,
                    started_on=phase.started_on,
                    typical_days=phase.typical_days,
                    allows_harvest=phase.allows_harvest,
                    is_terminal=phase.is_terminal,
                ),
            ),
        )
