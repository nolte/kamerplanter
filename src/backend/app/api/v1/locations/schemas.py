from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.api.v1.attachments.schemas import ThumbnailUris
from app.api.v1.care_events.schemas import CareEventResponse, care_event_to_response
from app.common.enums import (
    BedStatus,
    EcMethod,
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
    StoneContentClass,
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
from app.domain.engines.crop_rotation_validator import TimelineEntry
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.nutrient_hint import NUTRIENT_HINT_REASONS, NutrientHint, NutrientHintReason
from app.domain.models.planting_reservation import PlantingRow, QuickPlantingInput
from app.domain.models.planting_run import MAX_EDGE_MARGIN_CM, MAX_SPACING_CM, MIN_SPACING_CM, check_row_assignment
from app.domain.models.site import MAX_PHOTO_REF_LENGTH, MAX_PHOTOS_PER_LOCATION, SiteConditions
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
    #: Required with `ec_ms_cm` (U-002): a conductivity is only readable with its extraction method.
    ec_method: EcMethod | None = None
    humus_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    caco3_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    #: Stored as stated; never derived (E-10).
    stone_content_class: StoneContentClass = StoneContentClass.UNKNOWN
    target_ph: float | None = Field(default=None, ge=0.0, le=14.0)
    established_on: date | None = None
    #: Server-owned (WP 8.7, #2706): the `performed_at` of the newest soil analysis whose values the profile holds.
    #: A location write keeps the stored value; sent back as received it is a precondition (409 `soil_profile.stale`
    #: when a soil analysis changed the profile since it was read).
    last_analysis_at: datetime | None = None
    #: Substrate change: the crop-rotation history starts on this day (GP-FR-131).
    rotation_reset_at: date | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def _ec_needs_its_method(self) -> Self:
        if self.ec_ms_cm is not None and self.ec_method is None:
            raise ValueError("ec_ms_cm needs ec_method: a conductivity is only readable with its extraction method.")
        return self


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
    #: The bed's cover photo (REQ-053 GP-FR-051, WP 8.18): an attachment id, served by ``GET /attachments/{id}``
    #: and its thumbnails. ``null`` without one; the gallery itself is ``GET /locations/{key}/photos``.
    cover_photo_ref: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Bed photos (REQ-053 GP-FR-051, WP 8.18) ──────────────────────────────────────


_PHOTO_URI = "/api/v1/t/mein-garten/attachments/8812345"
_PHOTO_EXAMPLE: dict[str, Any] = {
    "attachment_id": "8812345",
    "uri": _PHOTO_URI,
    "thumbnail_uris": {
        "small": f"{_PHOTO_URI}/thumbnails/128",
        "medium": f"{_PHOTO_URI}/thumbnails/512",
        "large": f"{_PHOTO_URI}/thumbnails/1280",
    },
    "mime_type": "image/jpeg",
    "byte_size": 482113,
    "caption": None,
    "taken_on": None,
    "created_at": "2026-05-14T07:42:10Z",
    "is_cover": True,
    "can_remove": True,
}


class LocationPhotoRequest(BaseModel):
    """Link an uploaded photo to the bed: an attachment of category ``location`` of the caller's own garden."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"attachment_id": "8812345"}]})

    attachment_id: str = Field(
        min_length=1,
        max_length=MAX_PHOTO_REF_LENGTH,
        description=(
            "A `location` attachment uploaded beforehand through `POST /attachments`; any other key (another "
            "garden's, another category, absent) is 422 `reference.not_found`."
        ),
    )


class LocationCoverRequest(BaseModel):
    """Choose the bed's cover photo; ``null`` clears it."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"attachment_id": "8812345"}, {"attachment_id": None}]}
    )

    attachment_id: str | None = Field(
        min_length=1,
        max_length=MAX_PHOTO_REF_LENGTH,
        description="One of the bed's photos (else 422 `location.cover_not_a_photo`), or `null` for no cover.",
    )


class LocationPhotoResponse(BaseModel):
    """One photo of a bed. URIs are the tenant's attachment routes; no storage detail, no uploader key."""

    model_config = ConfigDict(json_schema_extra={"examples": [_PHOTO_EXAMPLE]})

    attachment_id: str
    uri: str = Field(description="Download URI of the original (EXIF/GPS stripped on upload).")
    thumbnail_uris: ThumbnailUris | None = Field(default=None, description="Present for image types.")
    mime_type: str
    byte_size: int
    caption: str | None = None
    taken_on: date | None = None
    created_at: datetime | None = None
    is_cover: bool = False
    can_remove: bool = Field(
        default=False,
        description="Whether the caller may remove it: own upload from `grower` up, another member's as `lead`.",
    )


class LocationPhotosResponse(BaseModel):
    """The bed's photos, newest first (``GET|POST /locations/{key}/photos`` and the cover/remove routes)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"location_key": "beet-3", "cover_photo_ref": "8812345", "photos": [_PHOTO_EXAMPLE], "max_photos": 50}
            ]
        }
    )

    location_key: str
    cover_photo_ref: str | None = None
    photos: list[LocationPhotoResponse] = Field(default_factory=list, max_length=MAX_PHOTOS_PER_LOCATION)
    max_photos: int = MAX_PHOTOS_PER_LOCATION


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
                    "nearest_water_source_m": 3.5,
                }
            ]
        }
    )

    active_plant_count: int | None = None
    open_task_count: int | None = None
    overdue_task_count: int | None = None
    #: Earliest due date of an open task of the bed.
    next_due_at: datetime | None = None
    #: GP-FR-167: derived, read-only - metres from the bed's edge to the nearest water source of its site, as in the
    #: summary and the CSV; only when beds are listed, `null` without a geometry or without a water source.
    nearest_water_source_m: float | None = Field(default=None, ge=0)


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


class NutrientHintResponse(BaseModel):
    """The nutrient hint of a bed (GP-FR-125, W-010): a state with reason codes - never a number.

    The UI words `likely_deficit` as "fertiliser likely needed". Every threshold of the rule table (REQ-053 §15.3)
    takes part only with a `source`; none has one yet (E-10), so every bed answers `insufficient_data` with the reason
    `thresholds_without_source` until a sourced value is configured. `compost_and_p_withheld` is `true` when a lab
    result by CAL puts P or K into class D/E: compost then serves no nutrient supply (it stays possible as a soil
    improver) and the hint never points to compost or a phosphorus fertiliser. This is the one qualitative rule active
    by default; `withheld_source` names its source (R-006). `sources` names the source of each threshold that decided
    the state.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "state": "insufficient_data",
                    "confidence": "low",
                    "reasons": ["thresholds_without_source", "preceding_nitrogen_fixer"],
                    "compost_and_p_withheld": False,
                    "sources": [],
                    "withheld_source": None,
                }
            ]
        }
    )

    state: Literal["ok", "check", "likely_deficit", "insufficient_data"]
    confidence: Literal["low", "medium", "high"]
    reasons: list[NutrientHintReason] = Field(default_factory=list, max_length=len(NUTRIENT_HINT_REASONS))
    compost_and_p_withheld: bool = False
    sources: list[str] = Field(default_factory=list, max_length=len(NUTRIENT_HINT_REASONS))
    #: The source of the class D/E rule when it applied (R-006); `null` otherwise.
    withheld_source: str | None = None

    @classmethod
    def from_hint(cls, hint: NutrientHint | None) -> NutrientHintResponse | None:
        if hint is None:
            return None
        return cls(
            state=hint.state,
            confidence=hint.confidence,
            reasons=list(hint.reasons),
            compost_and_p_withheld=hint.compost_and_p_withheld,
            sources=list(hint.sources),
            withheld_source=hint.withheld_source,
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
                    "nearest_water_source_m": 3.5,
                    "path_access": "one",
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
    #: GP-FR-125: only for a bed (`is_bed`); `null` for every other location.
    nutrient_hint: NutrientHintResponse | None = None
    #: GP-FR-167: derived, read-only - metres from the bed's edge to the nearest water source of its site (edge to
    #: edge in the plan frame, 0 when the source lies on or inside it); `null` for a location that is no bed, without a
    #: geometry or without a water source.
    nearest_water_source_m: float | None = Field(default=None, ge=0)
    #: GP-FR-166 (#2703): derived, read-only - the access the site's paths give the bed: `both` when paths run along
    #: two opposite edges across its width, `one` when a path runs along an edge, `none` without; a path counts when it
    #: comes within the site's `reach_thresholds.path_access_max_distance_m` (default 0.3 m) of the edge. Joins
    #: `site_conditions.access_sides` for the `bed.reach_too_wide` hint (the stronger wins). `null` for a location that
    #: is no bed or has no geometry.
    path_access: Literal["both", "one", "none"] | None = None


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

    @classmethod
    def from_entry(cls, entry: TimelineEntry) -> RotationPlantingResponse:
        """The one mapping from a timeline row to its response - the bed timeline and the site matrix both use it."""
        return cls.model_validate(
            {
                "season": entry.season,
                "family_key": entry.family_key,
                "family_name": entry.family_name,
                "species_key": entry.species_key,
                "nutrient_demand": entry.nutrient_demand,
                "plan_role": entry.plan_role,
                "source": entry.source,
                "care_event_key": entry.event_key,
            }
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


def rotation_year_responses(entries: Iterable[TimelineEntry], years: Iterable[int]) -> list[RotationYearResponse]:
    """One :class:`RotationYearResponse` per year of ``years``, in that order, holding the rows of that year.

    The single grouping behind ``GET /locations/{key}/rotation`` (newest year first) and the site rotation matrix
    (oldest first): a year nobody recorded is an empty list, a row outside ``years`` is not shown.
    """
    by_year: dict[int, list[RotationPlantingResponse]] = {year: [] for year in years}
    for entry in entries:
        if entry.year in by_year:
            by_year[entry.year].append(RotationPlantingResponse.from_entry(entry))
    return [RotationYearResponse(year=year, plantings=rows) for year, rows in by_year.items()]


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


class SuccessionSpeciesResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "species_key": "5120",
                    "scientific_name": "Daucus carota",
                    "common_name": "Carrot",
                    "nutrient_demand": "medium_feeder",
                    "nitrogen_fixing": False,
                }
            ]
        }
    )

    species_key: str
    scientific_name: str
    common_name: str | None = None
    nutrient_demand: str | None = None
    nitrogen_fixing: bool | None = Field(default=None, description="Informational; no nitrogen amount is derived.")


class SuccessionFamilyResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "family_key": "Apiaceae",
                    "family_name": "Apiaceae",
                    "benefit_score": 0.7,
                    "benefit_reason": "soil_structure",
                    "pause_years": 3,
                    "species": [
                        {
                            "species_key": "5120",
                            "scientific_name": "Daucus carota",
                            "common_name": "Carrot",
                            "nutrient_demand": "medium_feeder",
                            "nitrogen_fixing": False,
                        }
                    ],
                }
            ]
        }
    )

    family_key: str
    family_name: str | None = None
    benefit_score: float | None = Field(default=None, description="Strength of the `rotation_after` edge (REQ-001).")
    benefit_reason: str | None = None
    pause_years: int | None = Field(
        default=None, description="The pause the family keeps; `null` when no source names one."
    )
    species: list[SuccessionSpeciesResponse] = Field(max_length=10)


class SuccessionHeldBackResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"family_key": "Brassicaceae", "family_name": "Brassicaceae", "last_year": 2024, "pause_years": 4}
            ]
        }
    )

    family_key: str
    family_name: str | None = None
    last_year: int
    pause_years: int


class SuccessionBasisResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"year": 2025, "step": "main_crop", "nutrient_demand": "heavy_feeder", "family_keys": ["Solanaceae"]}
            ]
        }
    )

    year: int
    step: Literal["main_crop", "restoring"]
    nutrient_demand: str | None = None
    family_keys: list[str] = Field(max_length=50)


class SuccessionRecommendationResponse(BaseModel):
    """`GET /locations/{key}/succession-recommendation` (GP-FR-133): the next step of the feeder cycle for the bed.

    Order only - heavy -> medium -> light feeder -> green manure / fallow -> heavy; no nitrogen amount and no
    fertiliser dose. `status` says why a list is empty; a species without a stored `nutrient_demand` never appears.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "8801",
                    "rotation_applicable": True,
                    "not_applicable_reason": None,
                    "status": "ok",
                    "previous": {
                        "year": 2025,
                        "step": "main_crop",
                        "nutrient_demand": "heavy_feeder",
                        "family_keys": ["Solanaceae"],
                    },
                    "target": "medium_feeder",
                    "families": [
                        {
                            "family_key": "Apiaceae",
                            "family_name": "Apiaceae",
                            "benefit_score": 0.7,
                            "benefit_reason": "soil_structure",
                            "pause_years": 3,
                            "species": [
                                {
                                    "species_key": "5120",
                                    "scientific_name": "Daucus carota",
                                    "common_name": "Carrot",
                                    "nutrient_demand": "medium_feeder",
                                    "nitrogen_fixing": False,
                                }
                            ],
                        }
                    ],
                    "held_back": [],
                    "fallow_option": False,
                }
            ]
        }
    )

    location_key: str
    rotation_applicable: bool
    not_applicable_reason: str | None = None
    status: Literal["ok", "not_applicable", "no_history", "demand_unknown", "no_successor_data", "no_matching_species"]
    previous: SuccessionBasisResponse | None = None
    target: Literal["heavy_feeder", "medium_feeder", "light_feeder", "restoring"] | None = Field(
        default=None, description="`restoring` = green manure or a fallow year."
    )
    families: list[SuccessionFamilyResponse] = Field(max_length=20)
    held_back: list[SuccessionHeldBackResponse] = Field(
        max_length=20, description="Follow-up families left out because their pause in this bed is not over."
    )
    fallow_option: bool = Field(description="A fallow year is an option of the restoring step (no species needed).")


class SoilAnalysisPointResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "performed_at": "2026-03-01T09:00:00Z",
                    "value": 6.4,
                    "unit": "pH",
                    "source": "lab",
                    "sample_depth_cm": 20.0,
                    "content_class": None,
                    "event_key": "ce_8812",
                }
            ]
        }
    )

    performed_at: datetime
    value: float
    unit: str
    source: str
    sample_depth_cm: float | None = None
    #: A CAL content class (A-E), only when the lab stated it; never computed.
    content_class: str | None = None
    event_key: str


class SoilAnalysisSeriesItemResponse(BaseModel):
    """The points of one parameter by one method in one unit, oldest first (never merged with another one)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "parameter": "ph",
                    "method": "cacl2",
                    "unit": "pH",
                    "points": [
                        {
                            "performed_at": "2026-03-01T09:00:00Z",
                            "value": 6.4,
                            "unit": "pH",
                            "source": "lab",
                            "sample_depth_cm": None,
                            "content_class": None,
                            "event_key": "ce_8812",
                        }
                    ],
                }
            ]
        }
    )

    parameter: str
    #: `ec_method` of a conductivity, `ph_method` of a pH, else the `extraction_method`; `unknown` is its own method.
    method: str
    #: The unit of every point of the series (#2706): a value in another unit is another series, never converted.
    unit: str
    points: list[SoilAnalysisPointResponse]


class SoilMethodChangeResponse(BaseModel):
    """The method of `parameter` changed at `at`: the values before and after are not comparable."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "parameter": "ec",
                    "at": "2026-06-01T09:00:00Z",
                    "from_method": "ratio_1_5",
                    "to_method": "saturated_paste",
                }
            ]
        }
    )

    parameter: str
    at: datetime
    from_method: str
    to_method: str


class LimingHintResponse(BaseModel):
    """ "Liming likely" of the bed's current profile (GP-FR-122, §15.1 `needs_lime`): a hint, never an amount.

    `likely` only for grown soil with a pH measured in CaCl2, a known texture and a pH below the stated `target_ph`.
    Otherwise `not_assessable` names the first missing precondition; a pH by water or probe is never converted.
    """

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "not_assessable", "reason": "no_target_ph"}]})

    status: Literal["likely", "not_indicated", "not_assessable"]
    reason: Literal[
        "below_target",
        "at_or_above_target",
        "no_ph",
        "not_native_soil",
        "ph_method_not_cacl2",
        "texture_unknown",
        "no_target_ph",
    ]


class SoilAnalysesResponse(BaseModel):
    """`GET /locations/{key}/soil-analyses` (GP-FR-122): a series per parameter and method, changes marked."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "8801",
                    "series": [
                        {
                            "parameter": "ph",
                            "method": "cacl2",
                            "unit": "pH",
                            "points": [
                                {
                                    "performed_at": "2026-03-01T09:00:00Z",
                                    "value": 6.4,
                                    "unit": "pH",
                                    "source": "lab",
                                    "sample_depth_cm": None,
                                    "content_class": None,
                                    "event_key": "ce_8812",
                                }
                            ],
                        }
                    ],
                    "method_changes": [],
                    "analyses": 1,
                    "truncated": False,
                    "liming_hint": {"status": "not_assessable", "reason": "no_target_ph"},
                }
            ]
        }
    )

    location_key: str
    series: list[SoilAnalysisSeriesItemResponse]
    method_changes: list[SoilMethodChangeResponse]
    analyses: int
    #: `true` when older analyses than the ones listed exist (the read is bounded; narrow it with `from` / `to`).
    truncated: bool
    liming_hint: LimingHintResponse


# ── Companion overlay (REQ-053 WP 8.15, GP-FR-134) ───────────────────────────────────────────────────────────


class PlanPointResponse(BaseModel):
    """A point in plan coordinates (metres, the site's plan frame, rounded to millimetres)."""

    x: float = Field(examples=[2.15])
    y: float = Field(examples=[1.3])


class CompanionEndpointResponse(BaseModel):
    slot_key: str = Field(examples=["8841"])
    #: The slot's anchor in plan coordinates: a point's origin, a row's or zone's vertex mean.
    #: `null` when the slot or its bed has no geometry (the line cannot be drawn).
    position: PlanPointResponse | None
    #: The species standing (`removed_on = null`) or planned (live planting run) in the slot, sorted.
    species_keys: list[str] = Field(examples=[["5120"]])
    #: `true` when the slot holds more than 8 species and only the first 8 (by key) were judged and listed.
    species_truncated: bool = Field(default=False, examples=[False])


class CompanionDecidingPairResponse(BaseModel):
    """The two species whose relation decided the pair; a name only where the tenant may read the species."""

    species_a_key: str = Field(examples=["5120"])
    species_a_name: str | None = Field(examples=["Solanum lycopersicum"])
    species_b_key: str = Field(examples=["5188"])
    species_b_name: str | None = Field(examples=["Foeniculum vulgare"])


class CompanionEdgeResponse(BaseModel):
    slot_a: CompanionEndpointResponse
    slot_b: CompanionEndpointResponse
    status: Literal["compatible", "incompatible", "unknown"] = Field(examples=["incompatible"])
    #: `companion.incompatible` | `companion.compatible` | `companion.unknown` (the frontend translates it).
    reason_code: str = Field(examples=["companion.incompatible"])
    #: The curated reason of the deciding `incompatible_with` edge, if it names one.
    reason: str | None = Field(examples=["Fennel inhibits the growth of most neighbours."])
    #: The `compatible_with` score of the deciding pair; `null` for any other status.
    score: float | None = Field(examples=[None, 0.9])
    #: `null` for `unknown`: no companion edge relates any species of the two slots.
    deciding: CompanionDecidingPairResponse | None
    #: `adjacent_to.distance_cm` as stored; `null` for an edge without one (manual or legacy).
    distance_cm: float | None = Field(examples=[30.0])


class CompanionEdgesResponse(BaseModel):
    """`GET /locations/{key}/companion-edges` (GP-FR-134): one judged line per neighbouring pair of occupied slots."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "8801",
                    "edges": [
                        {
                            "slot_a": {"slot_key": "8841", "position": {"x": 2.15, "y": 1.3}, "species_keys": ["5120"]},
                            "slot_b": {"slot_key": "8842", "position": {"x": 2.45, "y": 1.3}, "species_keys": ["5188"]},
                            "status": "incompatible",
                            "reason_code": "companion.incompatible",
                            "reason": "Fennel inhibits the growth of most neighbours.",
                            "score": None,
                            "deciding": {
                                "species_a_key": "5120",
                                "species_a_name": "Solanum lycopersicum",
                                "species_b_key": "5188",
                                "species_b_name": "Foeniculum vulgare",
                            },
                            "distance_cm": 30.0,
                        }
                    ],
                    "total": 1,
                    "truncated": False,
                }
            ]
        }
    )

    location_key: str
    #: Strongest status first (`incompatible`, `compatible`, `unknown`), then by slot keys; at most 500.
    edges: list[CompanionEdgeResponse]
    #: Every pair with species on both sides, counted exactly in the database.
    total: int
    #: `true` when `total` exceeds the pairs answered. At most 2000 pairs (the first by slot keys) are judged; within
    #: them the 500 strongest are answered.
    truncated: bool
