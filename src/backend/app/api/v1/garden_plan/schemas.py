"""Request/response schemas of the garden plan, version 1 (REQ-053 §21.1, §21.3, ``schema_version: "1"``).

The plan read model is deliberately **lean** (GP-NFR-031: ≤ 500 KB for a large garden): a
location carries what the map draws and the counters it badges (geometry, status, task and
plant counts), not its notes or description — those come with the single-bed endpoints
(GP-API-012). Of the site conditions and the soil profile it carries only what the map layers and
the properties panel read (sun profile, frost risk, drainage), with unknown values left out (#2538).
``plan_updated_by`` (an account key) never leaves the server; the last editor is named by display
name (§22.1).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.garden_objects.schemas import GardenObjectResponse
from app.api.v1.locations.schemas import RotationYearResponse
from app.common.enums import (
    BedStatus,
    FlowRateSource,
    FrostRisk,
    IrrigationZoneType,
    SiteType,
    SlotRole,
    SoilDrainage,
    SoilTexture,
    SunExposure,
    SunWindow,
)
from app.config.constants import MAX_ROTATION_MATRIX_BEDS
from app.domain.models.garden_plan import MAX_OPERATIONS
from app.domain.models.garden_plan_import import MAX_OFFSET_M, PlanImportReport
from app.domain.models.geometry import Geometry
from app.domain.models.site import (
    SiteUnderlay,
    UnderlayCalibration,
    UnderlayOpacity,
    UnderlayOrigin,
    UnderlayRotation,
)

SCHEMA_VERSION = "1"

_RECT: dict[str, Any] = {"kind": "rect", "origin": [2.0, 3.5], "width_m": 3.0, "length_m": 1.2, "rotation_deg": 0.0}


class PlanBoundaryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0},
                    "north_angle_deg": 0,
                }
            ]
        }
    )

    boundary: Geometry = Field(description="Garden outline in the plan frame; a rect or a polygon (§9.2).")
    north_angle_deg: float | None = Field(
        default=None,
        ge=0,
        lt=360,
        description=(
            "Compass azimuth of geographic north, clockwise, 0 = +y (GP-FR-015). Omitted: the stored one is kept "
            "(0 on the first save)."
        ),
    )
    default_grid_m: float | None = Field(
        default=None, gt=0, le=10.0, description="Snap grid; the stored one if omitted."
    )
    adjacency_factor: float | None = Field(default=None, gt=0, le=10.0)
    expected_revision: int | None = Field(
        default=None,
        ge=0,
        description="Optimistic lock; omitted on the first save of a plan (there is no revision to expect).",
    )


class PlanBatchRequest(BaseModel):
    """The operations stay raw mappings on purpose: the service checks the caller's role per operation
    *before* it parses any of them (SR-013), so the route cannot let Pydantic run first."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "expected_revision": 42,
                    "operations": [
                        {
                            "op": "create_location",
                            "temp_key": "tmp1",
                            "data": {
                                "name": "Bed 6",
                                "location_type_key": "bed",
                                "geometry": {
                                    "kind": "rect",
                                    "origin": [4, 1],
                                    "width_m": 2,
                                    "length_m": 1,
                                    "rotation_deg": 0,
                                },
                            },
                        },
                        {"op": "delete", "entity": "garden_object", "key": "go_old"},
                    ],
                }
            ]
        }
    )

    expected_revision: int = Field(ge=0, description="The plan_revision the client's copy was loaded at (V-14).")
    operations: list[dict[str, Any]] = Field(
        min_length=1,
        description=(
            f"At most {MAX_OPERATIONS} operations of the closed list: create_location, create_garden_object, "
            "update_geometry, update_fields, delete, set_boundary, set_locked, set_z_order."
        ),
    )


class DerivedGeometrySchema(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"area_m2": 2.0, "bbox": [0.0, 1.5, 1.0, 3.5]}]})

    area_m2: float | None = None
    bbox: tuple[float, float, float, float] | None = None


class PlanBatchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plan_revision": 43,
                    "key_map": {"tmp1": "loc_a91c"},
                    "updated": ["loc_b03"],
                    "deleted": ["go_old"],
                    "derived": {"loc_a91c": {"area_m2": 2.0, "bbox": [4.0, 1.0, 6.0, 2.0]}},
                }
            ]
        }
    )

    plan_revision: int
    key_map: dict[str, str] = Field(default_factory=dict, description="temp_key → assigned key.")
    updated: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    derived: dict[str, DerivedGeometrySchema] = Field(default_factory=dict)


class PlaceTemplateRequest(BaseModel):
    """``POST /sites/{key}/plan/place-template`` (§21.7): one bed from a template, at a point, turned."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "template_key": "sys_raised_bed_2x1x0_8",
                    "origin": [4.0, 1.0],
                    "rotation_deg": 90,
                    "expected_revision": 42,
                    "create_recurring_tasks": True,
                }
            ]
        },
    )

    template_key: str = Field(
        min_length=1, max_length=200, description="A system template or one of the tenant's own (GET /bed-templates)."
    )
    origin: tuple[float, float] = Field(
        description="Where the template's anchor (lower-left corner of a rectangle, centre of a circle, first "
        "vertex of a polygon) lands in the plan frame, in metres."
    )
    rotation_deg: float = Field(
        default=0.0, ge=0.0, lt=360.0, description="Counter-clockwise, added to the template's own rotation."
    )
    expected_revision: int = Field(ge=0, description="The plan_revision the client's copy was loaded at (V-14).")
    create_recurring_tasks: bool = Field(
        default=False,
        description="Opt-in (GP-FR-087): create the template's `recurring_task_templates` as tasks on the new bed, "
        "each recurring yearly (RRULE) from its first due date - the day of placement plus the task template's "
        "`days_offset`. Default `false`: the bed only.",
    )


class PlaceTemplateResponse(PlanBatchResponse):
    """The answer of ``place-template``: the batch response plus the tasks created on the new bed (GP-FR-087)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "plan_revision": 43,
                    "key_map": {"template_bed": "loc_b17"},
                    "updated": [],
                    "deleted": [],
                    "derived": {"loc_b17": {"area_m2": 2.0, "bbox": [4.0, 1.0, 6.0, 2.0]}},
                    "created_tasks": ["task_8812"],
                    "recurring_tasks_failed": False,
                }
            ]
        }
    )

    created_tasks: list[str] = Field(
        default_factory=list, description="Keys of the recurring tasks created on the new bed (opt-in)."
    )
    recurring_tasks_failed: bool = Field(
        default=False,
        description="The bed was placed, but writing its recurring tasks failed; none of them exists.",
    )


class PlanBoundaryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"plan_revision": 1, "total_area_m2": 100.0, "boundary": _RECT}]}
    )

    plan_revision: int
    total_area_m2: float
    boundary: Geometry | None = None


class PlanSunProfileResponse(BaseModel):
    """The sun profile a map layer and the properties panel read (GP-FR-158/159); unknown values are absent."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"sun_window": "morning", "direct_sun_hours_summer": 5.5, "foliage_shade_in_summer": True}]
        }
    )

    sun_window: SunWindow | None = Field(default=None, description="Absent = unknown.")
    direct_sun_hours_summer: float | None = Field(default=None, description="Absent = not entered.")
    foliage_shade_in_summer: bool | None = Field(default=None, description="Present only when true.")


class PlanMicroclimateResponse(BaseModel):
    """The frost risk of a bed for the frost layer (GP-FR-162); read only on the plan path."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"frost_risk": "high"}]})

    frost_risk: FrostRisk | None = Field(default=None, description="Absent = unknown.")


class PlanSiteConditionsResponse(BaseModel):
    """The lean slice of ``Location.site_conditions`` the plan carries (D-1 of #2538): sun profile and frost risk.

    A part with nothing known is absent, and so is the whole object (GP-NFR-031 budget).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"sun_profile": {"sun_window": "afternoon"}, "microclimate": {"frost_risk": "low"}}]
        }
    )

    sun_profile: PlanSunProfileResponse | None = None
    microclimate: PlanMicroclimateResponse | None = None


class PlanSoilProfileResponse(BaseModel):
    """The drainage of a bed for the moisture layer (GP-FR-047); the rest of the soil profile is GP-API-012's."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"drainage": "poor"}]})

    drainage: SoilDrainage | None = Field(default=None, description="Absent = unknown.")


class PlanLocationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "loc_b03",
                    "name": "Raised bed 3",
                    "parent_location_key": None,
                    "location_type_key": "raised_bed",
                    "geometry": _RECT,
                    "area_m2": 3.6,
                    "bbox": [2.0, 3.5, 5.0, 4.7],
                    "bed_status": "active",
                    "sun_exposure": "partial_shade",
                    "site_conditions": {
                        "sun_profile": {"sun_window": "morning", "foliage_shade_in_summer": True},
                        "microclimate": {"frost_risk": "high"},
                    },
                    "soil_profile": {"drainage": "poor"},
                    "season_state": "planted",
                    "open_task_count": 2,
                }
            ]
        }
    )

    key: str
    name: str
    parent_location_key: str | None = None
    location_type_key: str = ""
    depth: int = 0
    geometry: Geometry | None = Field(default=None, description="Plan frame; ``null`` = not placed on the plan.")
    area_m2: float = 0.0
    bbox: tuple[float, float, float, float] | None = None
    height_m: float | None = None
    bed_status: BedStatus = BedStatus.ACTIVE
    is_area: bool | None = Field(
        default=None,
        description=(
            "`true`: the location is an area (REQ-053 §9.5) - its type is neither a bed nor carries a slot layout "
            "(garden, terrace, balcony, greenhouse, room); drawn with a light fill below the beds, `bed_status` means "
            "nothing for it. Absent for every other location (GP-NFR-031: the read model omits the default)."
        ),
    )
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    site_conditions: PlanSiteConditionsResponse | None = Field(
        default=None, description="Sun profile and frost risk; absent when nothing is known (#2538)."
    )
    soil_profile: PlanSoilProfileResponse | None = Field(
        default=None, description="Drainage only; absent when unknown. The full profile is GP-API-012's."
    )
    irrigation_zone_key: str | None = None
    #: The bed template this bed was placed from (provenance, WP 7.9).
    template_key: str | None = None
    locked: bool = False
    z_order: int = 0
    season_state: str | None = Field(default=None, description="Derived (§7.4): empty or planted until WP 3.x/4.x.")
    open_task_count: int = 0
    overdue_task_count: int = 0
    last_watered_at: datetime | None = Field(
        default=None, description="Newest watering of the bed within a year (`include=tasks`); never as 'needs water'."
    )


class PlanGardenObjectResponse(GardenObjectResponse):
    """A garden object on the plan with the counters its badge shows (a compost, water source or storage; R-7.2)."""

    open_task_count: int = 0
    overdue_task_count: int = 0


class PlanSlotGeometry(BaseModel):
    """A slot's geometry in the plan frame, as compact as the wire allows (2 000 plants, GP-NFR-031).

    A point — the common slot — is ``{"origin": [x, y]}``: ``kind`` defaults to ``point`` and is left
    out of the response by default-omission. A row carries ``points`` and ``width_m``, a zone ``points``.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"origin": [2.3, 4.4]}, {"kind": "polyline", "points": [[1, 1], [3, 1]], "width_m": 0.1}]
        }
    )

    #: Absent for a point (the common case); ``polyline`` or ``polygon`` otherwise.
    kind: Literal["polyline", "polygon"] | None = None
    origin: tuple[float, float] | None = None
    points: list[tuple[float, float]] | None = None
    width_m: float | None = None


class PlanSlotResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "slot_1",
                    "slot_id": "BED03_R2P05",
                    "location_key": "loc_b03",
                    "slot_role": "position",
                    "capacity_plants": 1,
                    "currently_occupied": True,
                    "plan_geometry": {"origin": [2.3, 4.4]},
                }
            ]
        }
    )

    key: str
    slot_id: str
    location_key: str
    #: Absent = ``position``, 1 and false: the wire leaves out the common value (GP-NFR-031).
    slot_role: SlotRole | None = None
    capacity_plants: int | None = None
    currently_occupied: bool | None = None
    row_index: int | None = None
    sequence: int | None = None
    plan_geometry: PlanSlotGeometry | None = Field(
        default=None, description="The slot's geometry transformed into the plan frame (§9.2)."
    )
    planned_from: date | None = Field(
        default=None,
        description="First day a planned run reserves the slot in a window that has not ended (GP-FR-065/074); "
        "absent for an unreserved slot.",
    )


class PlanPlantResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"key": "pl_1", "instance_id": "TOM-001", "species_key": "sp_tomato", "slot_key": "slot_1"}]
        }
    )

    key: str
    instance_id: str
    species_key: str
    phase_key: str | None = None
    slot_key: str | None = None
    location_key: str | None = None


_UNDERLAY: dict[str, Any] = {
    "attachment_key": "att_7f3a",
    "calibration": {"p1_px": [100, 200], "p2_px": [500, 200], "distance_m": 4.0},
    "origin": [0.0, 12.0],
    "rotation_deg": 0.0,
    "opacity": 0.5,
}


class PlanUnderlayRequest(BaseModel):
    """The background picture of the plan (GP-FR-033): attachment, two-point calibration, placement, opacity."""

    model_config = ConfigDict(json_schema_extra={"examples": [_UNDERLAY]})

    attachment_key: str = Field(
        min_length=1,
        max_length=64,
        description=(
            "A `garden_plan_underlay` attachment of the caller's own tenant; any other key is 422 `reference.not_found`"
        ),
    )
    calibration: UnderlayCalibration = Field(
        description="Two points of the picture in pixels and the real distance between them in metres (the scale)."
    )
    origin: UnderlayOrigin = Field(
        default=(0.0, 0.0), description="Plan-frame position in metres of the picture's top-left pixel."
    )
    rotation_deg: UnderlayRotation = Field(
        default=0.0, description="Counter-clockwise turn about `origin`, in degrees (-360..360)."
    )
    opacity: UnderlayOpacity = Field(default=0.5, description="0.05 (faint) .. 1 (opaque).")

    def to_domain(self) -> SiteUnderlay:
        return SiteUnderlay(
            attachment_key=self.attachment_key,
            calibration=self.calibration,
            origin=self.origin,
            rotation_deg=self.rotation_deg,
            opacity=self.opacity,
        )


class PlanUnderlayResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [_UNDERLAY]})

    attachment_key: str
    calibration: UnderlayCalibration
    origin: tuple[float, float]
    rotation_deg: float
    opacity: float


class PlanSettingsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "boundary": _RECT,
                    "north_angle_deg": 15.0,
                    "default_grid_m": 0.1,
                    "adjacency_factor": 1.5,
                    "plan_revision": 42,
                    "plan_updated_by_name": "Sabine",
                }
            ]
        }
    )

    boundary: Geometry | None = None
    north_angle_deg: float = 0.0
    default_grid_m: float
    adjacency_factor: float
    plan_revision: int = 0
    plan_updated_at: datetime | None = None
    plan_updated_by_name: str | None = Field(default=None, description="Display name, never the account key (§22.1).")
    underlay: PlanUnderlayResponse | None = Field(
        default=None, description="The background picture to trace over (GP-FR-033); shown per user, stored per site."
    )


class PlanZoneResponse(BaseModel):
    """An irrigation zone as the plan shows it (GP-API-001, GP-FR-110): the grouping, not the technical coupling.

    The bound Home Assistant entity is not part of it (SR-014); ``actuator_key`` is, as on the zone's own route.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "zone_sued",
                    "name": "South zone (drip line)",
                    "irrigation_type": "drip",
                    "water_source_key": "go_91ab",
                    "flow_rate_source": "manual",
                    "color": "#2E7D32",
                    "location_keys": ["loc_bed_1", "loc_bed_2"],
                }
            ]
        }
    )

    key: str
    name: str
    irrigation_type: IrrigationZoneType
    water_source_key: str | None = None
    actuator_key: str | None = None
    flow_rate_l_per_min: float | None = None
    flow_rate_source: FlowRateSource = FlowRateSource.MANUAL
    application_efficiency: float | None = None
    color: str
    schedule_hint: str | None = None
    location_keys: list[str] = Field(default_factory=list)


class PlanSunDirectionResponse(BaseModel):
    """Where the sun stands at sunrise or sunset: compass azimuth (0 = north, clockwise) and the site's local time."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"azimuth_deg": 47.8, "time": "04:43"}]})

    azimuth_deg: float = Field(description="Compass azimuth, 0 = north, clockwise, [0, 360) in steps of 0.1.")
    time: str = Field(description="Local time at the site (`Site.timezone`), `HH:MM`.")


class PlanSunDirectionsResponse(BaseModel):
    """GP-FR-016: today's sunrise and sunset directions at the site - for the compass; no shading (§29)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "day": "2026-06-21",
                    "sunrise": {"azimuth_deg": 47.8, "time": "04:43"},
                    "sunset": {"azimuth_deg": 312.2, "time": "21:32"},
                }
            ]
        }
    )

    day: date = Field(description="The site's current day (`Site.timezone`) the directions are for.")
    sunrise: PlanSunDirectionResponse
    sunset: PlanSunDirectionResponse


class GardenPlanResponse(BaseModel):
    """GP-API-001: the whole plan in one response."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1",
                    "site_key": "site_7f3a",
                    "site_name": "Vegetable garden",
                    "site_type": "outdoor",
                    "site_default_grid_m": 0.1,
                    "plan_revision": 42,
                    "plan": {"north_angle_deg": 15.0, "default_grid_m": 0.1, "adjacency_factor": 1.5},
                    "locations": [],
                    "area_type_keys": ["balcony", "garden", "greenhouse", "terrace"],
                    "garden_objects": [],
                    "slots": [],
                    "plants": [],
                    "zones": [],
                }
            ]
        }
    )

    #: No default on purpose: the read model omits fields at their default (GP-NFR-031), and the version
    #: marker must always be on the wire.
    schema_version: str
    site_key: str
    site_name: str
    #: No default either: the client tells an indoor plan by it (GP-FR-182), so it is always on the wire.
    site_type: SiteType = Field(
        description="The site's type; `indoor`, `windowsill` and `grow_tent` make the plan an indoor plan (§9.8)."
    )
    site_default_grid_m: float = Field(
        description=(
            "The snap grid a new plan of this site starts with: 0.05 indoor, 0.1 otherwise (GP-FR-011/182). "
            "A stored `plan.default_grid_m` wins."
        )
    )
    plan_revision: int = 0
    #: ``null`` = a site without a garden plan (§20.2).
    plan: PlanSettingsResponse | None = None
    locations: list[PlanLocationResponse] = Field(default_factory=list)
    area_type_keys: list[str] = Field(
        default_factory=list,
        description=(
            "Every location type the plan draws as an area (REQ-053 §9.5, GP-UX-071), sorted - also those no location "
            "of this plan has yet, so a client draws an area it creates as one before the save."
        ),
    )
    garden_objects: list[PlanGardenObjectResponse] = Field(default_factory=list)
    slots: list[PlanSlotResponse] = Field(default_factory=list)
    plants: list[PlanPlantResponse] = Field(default_factory=list)
    zones: list[PlanZoneResponse] = Field(
        default_factory=list, description="Irrigation zones of the site with the beds they cover (`include=zones`)."
    )
    sun_directions: PlanSunDirectionsResponse | None = Field(
        default=None,
        description=(
            "Today's sunrise and sunset directions at the site (GP-FR-016); absent without `gps_coordinates` and on "
            "a day of polar day or night."
        ),
    )


class PlanAuditEntryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "revision": 43,
                    "op": "delete",
                    "entity": "garden_object",
                    "key": "go_old",
                    "summary": "Old path",
                    "at": "2026-10-17T09:12:33Z",
                    "changed_by_name": "Sabine",
                }
            ]
        }
    )

    revision: int
    op: str
    entity: str
    key: str
    summary: str = ""
    at: datetime
    changed_by_name: str | None = Field(default=None, description="Display name; ``null`` once the account is erased.")


#: One axis of ``offset_m``: finite (``inf`` / ``nan`` are a 422, never a 500, #2529) and inside the plan frame.
_OffsetM = Annotated[float, Field(allow_inf_nan=False, ge=-MAX_OFFSET_M, le=MAX_OFFSET_M)]


class PlanImportRequest(BaseModel):
    """The envelope of ``POST /sites/{key}/plan/import``; ``document`` is a ``GET /plan/export`` file, as is.

    ``document`` stays a raw mapping on purpose: the service checks ``schema_version`` and the top-level keys of an
    untrusted file *before* Pydantic reads it (GP-NFR-051), and answers with the file's own paths.
    """

    model_config = ConfigDict(extra="forbid")

    mode: Literal["replace", "merge"] = Field(
        description="`replace` swaps the site's structure for the file's (writes a snapshot first); `merge` adds."
    )
    dry_run: bool = Field(default=False, description="Check the file and report; write nothing.")
    force: bool = Field(
        default=False,
        description="Lifts only the condition that no bed holds an active plant; those beds then stay (V-09).",
    )
    confirm_site_name: str | None = Field(
        default=None,
        max_length=200,
        description="`replace` (not a dry run) needs the name of the site, typed by the person who confirms.",
    )
    target: Literal["same_site", "other_site", "other_tenant"] = Field(
        default="same_site",
        description=(
            "Where the file goes relative to where it came from (GP-FR-172). Keys of the file are always "
            "replaced by new ones. `same_site` lets a reference that is not in the file resolve against this site; "
            "`other_site` and "
            "`other_tenant` never do - such a reference becomes `null` and is listed in `dropped_references[]`. "
            "`other_tenant` needs the lead role of *this* tenant only: the file is the transport, nothing is read "
            "across tenants."
        ),
    )
    offset_m: tuple[_OffsetM, _OffsetM] | None = Field(
        default=None,
        description="`merge` only: `[dx, dy]` in metres added to every geometry of the file (422 for `replace`).",
    )
    document: dict[str, Any] = Field(description='The backup file, `schema_version: "1"`.')


class PlanImportResponse(PlanImportReport):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mode": "replace",
                    "dry_run": True,
                    "target": "same_site",
                    "offset_m": None,
                    "would_create": {"locations": 5, "garden_objects": 3, "slots": 20, "plan_settings": 0},
                    "would_update": {"locations": 0, "garden_objects": 0, "slots": 0, "plan_settings": 1},
                    "would_delete": {"locations": 4, "garden_objects": 2, "slots": 12, "plan_settings": 0},
                    "kept_locations": 0,
                    "dropped_references": [
                        {"entity": "location", "key": "loc_7", "field": "irrigation_zone_key", "reason": "not_found"}
                    ],
                    "dropped_references_total": 1,
                    "errors": [],
                    "errors_total": 0,
                    "applied": False,
                    "plan_revision": None,
                    "snapshot_written": False,
                }
            ]
        }
    )


class BedCsvLineFindingResponse(BaseModel):
    """One problem of one line of a CSV bed list (GP-FR-174): the line, the column as the file spells it, a code.

    `line` counts the header as line 1; `column` is `null` when the whole row is concerned (its placement, e.g.
    `geometry.outside_parent` or `bed.overlap`). The cell's value is never echoed.
    """

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"line": 3, "column": "Breite_m", "code": "csv.invalid_number"}]}
    )

    line: int
    column: str | None = None
    code: str


class BedCsvRowResponse(BaseModel):
    """A line the import writes (or wrote): the bed it becomes, placed as a `rect` with `origin` lower-left."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "line": 2,
                    "name": "Hochbeet 1",
                    "location_type_key": "raised_bed",
                    "width_m": 2.0,
                    "length_m": 1.2,
                    "origin": [0.0, 8.8],
                    "sun_exposure": "full_sun",
                    "soil_texture": "loam",
                    "irrigation_zone_key": None,
                    "location_key": None,
                }
            ]
        }
    )

    line: int
    name: str
    location_type_key: str
    width_m: float
    length_m: float
    origin: tuple[float, float]
    sun_exposure: SunExposure
    soil_texture: SoilTexture | None = None
    irrigation_zone_key: str | None = None
    location_key: str | None = Field(default=None, description="The new bed's key; `null` in a dry run.")


class BedCsvImportResponse(BaseModel):
    """The report of a CSV bed list import (GP-FR-174), the same for the dry run and the confirmation."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "dry_run": True,
                    "rows_total": 3,
                    "rows": [
                        {
                            "line": 2,
                            "name": "Hochbeet 1",
                            "location_type_key": "raised_bed",
                            "width_m": 2.0,
                            "length_m": 1.2,
                            "origin": [0.0, 8.8],
                            "sun_exposure": "full_sun",
                            "soil_texture": None,
                            "irrigation_zone_key": None,
                            "location_key": None,
                        }
                    ],
                    "rows_valid": 1,
                    "rows_skipped": 2,
                    "errors": [
                        {"line": 3, "column": "Breite_m", "code": "csv.invalid_number"},
                        {"line": 4, "column": "Typ", "code": "csv.unknown_type"},
                    ],
                    "errors_total": 2,
                    "warnings": [{"line": 2, "column": "Name", "code": "csv.formula_stripped"}],
                    "warnings_total": 1,
                    "ignored_columns": ["Notiz"],
                    "ignored_columns_total": 1,
                    "applied": False,
                    "plan_revision": 12,
                }
            ]
        }
    )

    dry_run: bool
    rows_total: int = Field(description="Data lines of the file (rows of empty cells not counted).")
    rows: list[BedCsvRowResponse] = Field(description="The lines that pass every check, in file order (<= 500).")
    rows_valid: int
    rows_skipped: int = Field(description="Lines with at least one error; never written.")
    errors: list[BedCsvLineFindingResponse] = Field(description="Line errors, at most 500; see `errors_total`.")
    errors_total: int
    warnings: list[BedCsvLineFindingResponse] = Field(
        description="`csv.formula_stripped`: a leading formula character was discarded (SR-016); at most 500."
    )
    warnings_total: int
    ignored_columns: list[str] = Field(description="Header cells the import does not know; ignored. At most 50.")
    ignored_columns_total: int
    applied: bool = Field(description="`true` once the valid lines were written.")
    plan_revision: int = Field(
        description="The revision the check ran against (send it as `expected_revision` to confirm), or the new one."
    )


class PlanSnapshotResponse(BaseModel):
    """One plan a `replace` import overwrote (GP-FR-148/170); the payload stays on the server."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "audit_key": "7481",
                    "revision": 43,
                    "at": "2026-10-17T09:12:33Z",
                    "summary": "state before the replace import (revision 43)",
                    "changed_by_name": "Sabine",
                    "locations": 12,
                    "garden_objects": 4,
                    "slots": 96,
                    "zones": 2,
                }
            ]
        }
    )

    audit_key: str = Field(description="The handle of `POST …/snapshots/{audit_key}/restore`.")
    revision: int
    at: datetime
    summary: str = ""
    changed_by_name: str | None = Field(default=None, description="Display name; `null` once the account is erased.")
    locations: int = 0
    garden_objects: int = 0
    slots: int = 0
    zones: int = 0


class PlanSnapshotRestoreRequest(BaseModel):
    """`POST /sites/{key}/plan/snapshots/{audit_key}/restore`: a `replace` with the snapshot as the file."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"dry_run": True, "force": False, "confirm_site_name": None}]},
    )

    dry_run: bool = Field(default=False, description="Check and report what would change; write nothing.")
    force: bool = Field(
        default=False, description="Lifts only the condition that no bed holds an active plant; those beds then stay."
    )
    confirm_site_name: str | None = Field(
        default=None, max_length=200, description="Needed unless `dry_run`: the name of the site, typed by the lead."
    )


class PlanSeasonRequest(BaseModel):
    """`POST /sites/{key}/plan/new-season`: the structure of last year's runs as free slots (GP-FR-171, WP 7.16)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"year": 2027, "dry_run": True, "expected_revision": None}]},
    )

    year: int = Field(
        strict=True,
        ge=2001,
        le=2100,
        description=(
            "The new season. Whole number; the slots archived in `year - 1` are the source. The server refuses "
            "a year later than next year (422 `season.invalid_year`)."
        ),
    )
    dry_run: bool = Field(default=True, description="Report what would be created; write nothing.")
    expected_revision: int | None = Field(
        default=None,
        ge=0,
        le=2_147_483_647,
        description="The `plan_revision` the caller saw; another stored revision is a 409 `plan.revision_conflict`.",
    )


class PlanSeasonBedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"location_key": "4711", "status": "copied", "slots": 12, "slots_outside_bed": 0}]
        }
    )

    location_key: str
    status: Literal["copied", "skipped_active_plants", "skipped_retired", "skipped_slot_quota", "nothing_to_copy"]
    slots: int = 0
    slots_outside_bed: int = 0


class PlanSeasonResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "year": 2027,
                    "source_year": 2026,
                    "dry_run": True,
                    "applied": False,
                    "plan_revision": 43,
                    "beds_copied": 1,
                    "beds_skipped": 1,
                    "slots_to_create": 12,
                    "beds": [
                        {"location_key": "4711", "status": "copied", "slots": 12, "slots_outside_bed": 0},
                        {"location_key": "4712", "status": "skipped_active_plants", "slots": 0, "slots_outside_bed": 0},
                    ],
                }
            ]
        }
    )

    year: int
    source_year: int
    dry_run: bool
    applied: bool = False
    plan_revision: int | None = None
    beds_copied: int = 0
    beds_skipped: int = 0
    slots_to_create: int = 0
    beds: list[PlanSeasonBedResponse] = Field(default_factory=list, max_length=500)


class RotationMatrixBedResponse(BaseModel):
    """One row of the matrix: a bed and one cell per column (GP-FR-135)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location_key": "4711",
                    "name": "Bed 1",
                    "rotation_applicable": True,
                    "not_applicable_reason": None,
                    "rotation_reset_at": None,
                    "cells": [
                        {
                            "year": 2025,
                            "plantings": [
                                {
                                    "family_key": "Solanaceae",
                                    "nutrient_demand": "heavy_feeder",
                                    "plan_role": "main_crop",
                                    "source": "plant",
                                }
                            ],
                        },
                        {"year": 2026, "plantings": []},
                    ],
                }
            ]
        }
    )

    location_key: str
    name: str
    rotation_applicable: bool = Field(
        description="`false` for a `rotation_exempt` bed and a bed whose own switch is off (`rotation_enabled: false`)."
    )
    not_applicable_reason: str | None = None
    rotation_reset_at: date | None = None
    cells: list[RotationYearResponse] = Field(
        max_length=10,
        description="One cell per `columns` entry, same order; an empty `plantings` is a year nobody recorded.",
    )


class RotationMatrixResponse(BaseModel):
    """`GET /sites/{key}/rotation-matrix` (GP-FR-135): beds x years, a cell is the `/locations/{key}/rotation` year."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "site_key": "4700",
                    "years": 5,
                    "columns": [2022, 2023, 2024, 2025, 2026],
                    "total": 1,
                    "truncated": False,
                    "offset": 0,
                    "limit": 50,
                    "beds": [],
                }
            ]
        }
    )

    site_key: str
    years: int
    columns: list[int] = Field(max_length=10, description="The years, oldest first; the current year is the last.")
    total: int = Field(description="Beds of the site the matrix reads (at most 500), for paging.")
    truncated: bool = Field(description="`true` when the site holds more than 500 beds; the surplus is not listed.")
    offset: int
    limit: int
    beds: list[RotationMatrixBedResponse] = Field(max_length=MAX_ROTATION_MATRIX_BEDS)
