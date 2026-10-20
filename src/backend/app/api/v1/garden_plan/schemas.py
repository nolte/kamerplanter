"""Request/response schemas of the garden plan, version 1 (REQ-053 §21.1, §21.3, ``schema_version: "1"``).

The plan read model is deliberately **lean** (GP-NFR-031: ≤ 500 KB for a large garden): a
location carries what the map draws and the counters it badges (geometry, status, task and
plant counts), not its soil profile, notes or description — those come with the single-bed
endpoints (GP-API-012). ``plan_updated_by`` (an account key) never leaves the server; the
last editor is named by display name (§22.1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.garden_objects.schemas import GardenObjectResponse
from app.common.enums import BedStatus, FlowRateSource, IrrigationZoneType, SlotRole, SunExposure
from app.domain.models.garden_plan import MAX_OPERATIONS
from app.domain.models.garden_plan_import import MAX_OFFSET_M, PlanImportReport
from app.domain.models.geometry import Geometry

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


class PlanBoundaryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"plan_revision": 1, "total_area_m2": 100.0, "boundary": _RECT}]}
    )

    plan_revision: int
    total_area_m2: float
    boundary: Geometry | None = None


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
    sun_exposure: SunExposure = SunExposure.UNKNOWN
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


class GardenPlanResponse(BaseModel):
    """GP-API-001: the whole plan in one response."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1",
                    "site_key": "site_7f3a",
                    "site_name": "Vegetable garden",
                    "plan_revision": 42,
                    "plan": {"north_angle_deg": 15.0, "default_grid_m": 0.1, "adjacency_factor": 1.5},
                    "locations": [],
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
    plan_revision: int = 0
    #: ``null`` = a site without a garden plan (§20.2).
    plan: PlanSettingsResponse | None = None
    locations: list[PlanLocationResponse] = Field(default_factory=list)
    garden_objects: list[PlanGardenObjectResponse] = Field(default_factory=list)
    slots: list[PlanSlotResponse] = Field(default_factory=list)
    plants: list[PlanPlantResponse] = Field(default_factory=list)
    zones: list[PlanZoneResponse] = Field(
        default_factory=list, description="Irrigation zones of the site with the beds they cover (`include=zones`)."
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
