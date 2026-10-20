"""Operations, read model and write set of the garden plan (REQ-053 §21.1, §21.3).

The plan batch (``POST /sites/{key}/plan/batch``, GP-API-003) takes a **closed**
list of operations. They are declared here, in the domain, because the service
parses them itself: the check order (SR-013) puts the role check *before*
Pydantic, so the route accepts the operations as raw mappings and the service
runs each one through :data:`PlanOperationAdapter` only after the caller's role
has been measured against every operation.

Slot operations are deliberately absent (GP-API-003): slots live in the bed frame
and change outside the plan revision (GP-NFR-007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, model_validator

from app.common.enums import BedStatus, GardenObjectType, GeometrySource, SlotRole, SunExposure
from app.domain.models.care_event import CareEvent
from app.domain.models.garden_object import GardenObject
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.site import Location, Microclimate, SiteConditions, SitePlan, Slot, SoilProfile, SunProfile

if TYPE_CHECKING:
    from app.domain.models.irrigation_zone import IrrigationZone

#: Request-local name for an object created in the same batch (``tmp1``); the server answers with ``key_map``.
TempKey = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]
#: A stored key or a :data:`TempKey` of an object created earlier in the batch.
EntityKey = Annotated[str, StringConstraints(min_length=1, max_length=200)]

#: ``entity`` of ``update_geometry`` / ``update_fields`` / ``delete`` / ``set_locked`` / ``set_z_order``.
PlanEntityType = Literal["location", "garden_object"]

#: GP-API-003 / V-17: operations per request.
MAX_OPERATIONS = 500
#: GP-NFR-013 (SR-012): Σ polygon and polyline points per batch.
MAX_BATCH_POINTS = 20_000
#: GP-NFR-013 (SR-012): request body.
MAX_BATCH_BODY_BYTES = 2 * 1024 * 1024
#: GP-NFR-013 (SR-012): time budget of one batch (validation plus transaction).
BATCH_TIME_BUDGET_SECONDS = 10.0
#: GP-NFR-017 (SR-004): locations plus garden objects per site.
MAX_PLAN_OBJECTS_PER_SITE = 500
#: Irrigation zones the plan read model, the export and the import carry per site (creating them has no quota, #2466).
MAX_PLAN_ZONES = 500
#: GP-NFR-017 (SR-004): slots per site (read-only here; slot routes enforce it).
MAX_SLOTS_PER_SITE = 8_000

#: The closed operation list of GP-API-003, in the order the spec names it.
OPERATION_NAMES: tuple[str, ...] = (
    "create_location",
    "create_garden_object",
    "update_geometry",
    "update_fields",
    "delete",
    "set_boundary",
    "set_locked",
    "set_z_order",
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Operation payloads ────────────────────────────────────────────────────────


class CreateLocationData(_Strict):
    name: str = Field(min_length=1, max_length=200)
    location_type_key: str = Field(min_length=1, max_length=200)
    parent_location_key: EntityKey | None = None
    geometry: Geometry
    height_m: float | None = None
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=4000)
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    locked: bool = False
    z_order: int = Field(default=0, ge=-10_000, le=10_000)


class TemplateLocationData(CreateLocationData):
    """What ``place-template`` creates (REQ-053 §21.7, WP 7.9): a location plus the two things a template adds.

    A subclass **outside** :data:`PlanOperation`'s public union on purpose: ``template_key`` is provenance the
    server resolves against the catalogue (global or the tenant's own), and ``soil_profile`` is the template's
    soil axes - a client of ``POST /plan/batch`` sends neither (``extra="forbid"`` on the parent says so).
    """

    template_key: str | None = Field(default=None, min_length=1, max_length=200)
    soil_profile: SoilProfile | None = None


class CreateGardenObjectData(_Strict):
    object_type: GardenObjectType
    label: str = Field(default="", max_length=200)
    geometry: Geometry
    props: dict[str, Any] = Field(default_factory=dict)
    parent_location_key: EntityKey | None = None
    off_site: bool = False
    locked: bool = False
    z_order: int = Field(default=0, ge=-10_000, le=10_000)
    notes: str | None = Field(default=None, max_length=4000)


class LocationFieldsPatch(_Strict):
    """What ``update_fields`` may change on a location (structure and geometry have their own operations)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=4000)
    sun_exposure: SunExposure | None = None
    height_m: float | None = None


class GardenObjectFieldsPatch(_Strict):
    """What ``update_fields`` may change on a garden object."""

    label: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)
    props: dict[str, Any] | None = None
    off_site: bool | None = None


# ── Operations ────────────────────────────────────────────────────────────────


class CreateLocationOp(_Strict):
    op: Literal["create_location"]
    temp_key: TempKey
    data: CreateLocationData


class CreateGardenObjectOp(_Strict):
    op: Literal["create_garden_object"]
    temp_key: TempKey
    data: CreateGardenObjectData


class UpdateGeometryOp(_Strict):
    op: Literal["update_geometry"]
    entity: PlanEntityType
    key: EntityKey
    geometry: Geometry


class UpdateFieldsOp(_Strict):
    op: Literal["update_fields"]
    entity: PlanEntityType
    key: EntityKey
    fields: dict[str, Any] = Field(min_length=1)


class DeleteOp(_Strict):
    op: Literal["delete"]
    entity: PlanEntityType
    key: EntityKey


class SetBoundaryOp(_Strict):
    op: Literal["set_boundary"]
    boundary: Geometry
    north_angle_deg: float | None = None
    default_grid_m: float | None = Field(default=None, gt=0, le=10.0)
    adjacency_factor: float | None = Field(default=None, gt=0, le=10.0)


class SetLockedOp(_Strict):
    op: Literal["set_locked"]
    entity: PlanEntityType
    key: EntityKey
    locked: bool


class SetZOrderOp(_Strict):
    op: Literal["set_z_order"]
    entity: PlanEntityType
    key: EntityKey
    z_order: int = Field(ge=-10_000, le=10_000)


PlanOperation = Annotated[
    CreateLocationOp
    | CreateGardenObjectOp
    | UpdateGeometryOp
    | UpdateFieldsOp
    | DeleteOp
    | SetBoundaryOp
    | SetLockedOp
    | SetZOrderOp,
    Field(discriminator="op"),
]

PlanOperationAdapter: TypeAdapter[PlanOperation] = TypeAdapter(PlanOperation)


# ── Batch result ──────────────────────────────────────────────────────────────


class DerivedGeometry(BaseModel):
    """Server-derived values of a created or moved object (§21.3 ``derived``)."""

    area_m2: float | None = None
    bbox: tuple[float, float, float, float] | None = None


class PlanBatchResult(BaseModel):
    """The 200 answer of ``POST /plan/batch`` (§21.3)."""

    plan_revision: int
    key_map: dict[str, str] = Field(default_factory=dict)
    updated: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    derived: dict[str, DerivedGeometry] = Field(default_factory=dict)


# ── Write set handed to the repository ────────────────────────────────────────


@dataclass(frozen=True)
class PlanBatchWrite:
    """Everything one batch writes, computed **before** the transaction opens (GP-NFR-013).

    The repository applies it in one stream transaction after re-checking the site's
    ``plan_revision``. The models are fully formed (derived ``area_m2``/``bbox``,
    ``depth``/``path``); ``location_inserts`` and ``object_inserts`` are ordered
    parents first so a child can name its parent's freshly assigned key through
    ``temp_key``. Updates carry only the fields the batch changed, so a field another path changed
    meanwhile is not overwritten with the value read before the transaction.
    """

    site_key: str
    tenant_key: str
    editor_key: str
    expected_revision: int
    #: The revision the validation ran against; a different stored value is a conflict too.
    basis_revision: int
    #: ``(temp_key, model)``; ``parent_location_key`` may name another ``temp_key`` of this write.
    location_inserts: list[tuple[str, Location]] = field(default_factory=list)
    #: ``(key, changed fields)`` — only what the batch changed, JSON-shaped; ``None`` removes a stored value.
    location_updates: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    #: Keys to delete, descendants and the slots below them included by the repository.
    location_deletes: list[str] = field(default_factory=list)
    object_inserts: list[tuple[str, GardenObject]] = field(default_factory=list)
    object_updates: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    object_deletes: list[str] = field(default_factory=list)
    #: ``None`` leaves the stored boundary alone.
    boundary: Geometry | None = None
    north_angle_deg: float | None = None
    default_grid_m: float | None = None
    adjacency_factor: float | None = None
    total_area_m2: float | None = None
    #: ``{op, entity, key, summary}`` — the repository adds revision, site, tenant, editor and time (SR-011).
    audit: list[dict[str, str]] = field(default_factory=list)
    #: Care events written in the same transaction (a bed-status change, GP-FR-046). ``tenant_key`` is stamped by
    #: the service; the repository adds the ``care_event_at`` edge to the event's location.
    care_events: list[CareEvent] = field(default_factory=list)
    #: ``location key → bed_status`` the transition was validated from. The transaction re-reads the stored status
    #: and refuses (409 ``bed_status.changed``) when it is another one — the revision alone does not protect a
    #: check that ran against a location read *before* the revision was read.
    status_from: dict[str, str] = field(default_factory=dict)
    #: ``(location temp_key or key, slot)`` — slots of freshly inserted locations, written in the same transaction
    #: (the plan import, GP-API-005); the batch routes never set it.
    slot_inserts: list[tuple[str, Slot]] = field(default_factory=list)
    #: ``(temp_key, zone)`` - the irrigation zones of an import (WP 7.2), inserted with their ``has_irrigation_zone``
    #: edge before the locations. ``water_source_key`` names an object of ``object_inserts`` by its temp key (or
    #: ``None``); a location names its zone by the zone's temp key. The batch routes never set it.
    zone_inserts: list[tuple[str, IrrigationZone]] = field(default_factory=list)
    #: Zones a ``replace`` import removes with every edge on them (the beds they covered are deleted by it too).
    zone_deletes: list[str] = field(default_factory=list)
    #: The state a ``replace`` import overwrites, stored with its audit row in the same transaction (SR-011).
    snapshot: dict[str, Any] | None = None
    #: Summary of the snapshot row (counts only, never a name — GP-NFR-060).
    snapshot_summary: str = ""
    time_budget_seconds: float = BATCH_TIME_BUDGET_SECONDS


#: GP-FR-062 / V-22: positions one slot batch may carry (``layout.too_many_positions``).
MAX_SLOTS_PER_BATCH = 2_000


@dataclass(frozen=True)
class SlotBatchWrite:
    """One replace/append of a bed's slots (GP-API-015), computed before the transaction opens.

    Slots live in the bed frame and change **outside** the plan revision (GP-NFR-007), so there is no
    revision here. ``delete_keys`` are the unoccupied, unreserved, unarchived slots a ``replace_unoccupied``
    removes; the repository re-checks that inside the transaction.
    """

    location_key: str
    delete_keys: list[str]
    inserts: list[Slot]
    time_budget_seconds: float = BATCH_TIME_BUDGET_SECONDS


class BedCounters(BaseModel):
    """What a bed list row and the bed summary show beside the document (GP-API-011, GP-FR-047)."""

    active_plant_count: int = 0
    species_keys: list[str] = Field(default_factory=list)
    open_task_count: int = 0
    overdue_task_count: int = 0
    #: Earliest ``due_date`` of an open task of the bed (ISO date or datetime as stored).
    next_due_at: datetime | None = None
    #: ``performed_at`` of the newest care event that is not voided.
    last_care_at: datetime | None = None


@dataclass(frozen=True)
class PlanBatchOutcome:
    """What the transaction reports: the new revision and the temp-key → key assignment."""

    plan_revision: int
    key_map: dict[str, str]


@dataclass(frozen=True)
class SlotBatchOutcome:
    """What a slot batch reports: the keys it created and how many it removed."""

    created_keys: list[str]
    deleted_count: int


# ── Single-resource bodies (WP 1.9, GP-API-010, 013, 014, 015, 018) ────────────


def _no_null_for(model: BaseModel, names: tuple[str, ...]) -> None:
    """A field that cannot be cleared must not arrive as an explicit ``null`` (``None`` would be dropped silently)."""
    for name in names:
        if name in model.model_fields_set and getattr(model, name) is None:
            raise ValueError(f"{name} cannot be null.")


class _StrictSunProfile(SunProfile):
    model_config = ConfigDict(extra="forbid")


class _StrictMicroclimate(Microclimate):
    model_config = ConfigDict(extra="forbid")


class SiteConditionsPatch(SiteConditions):
    """The ``site_conditions`` of ``PATCH /locations/{key}``: the keys present are changed, the others kept (WP 3.9).

    A misspelt key is a 422 instead of a silently dropped value. ``model_fields_set`` of the value and of its two
    nested parts say what was sent; :func:`GardenResourceService._merged_site_conditions` merges exactly that.
    """

    model_config = ConfigDict(extra="forbid")

    sun_profile: _StrictSunProfile = Field(default_factory=_StrictSunProfile)
    microclimate: _StrictMicroclimate = Field(default_factory=_StrictMicroclimate)


class LocationPatch(_Strict):
    """``PATCH /locations/{key}`` (GP-API-010): only the fields present are changed; an explicit ``null`` clears
    the ones that can be cleared (description, notes, height, irrigation zone, soil profile)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=4000)
    height_m: float | None = None
    sun_exposure: SunExposure | None = None
    geometry: Geometry | None = None
    soil_profile: SoilProfile | None = None
    #: Sun profile, microclimate, wind … (§10.2, WP 3.9): the keys sent are merged into the stored value;
    #: an explicit ``null`` clears all of it.
    site_conditions: SiteConditionsPatch | None = None
    irrigation_zone_key: str | None = Field(default=None, min_length=1, max_length=200)
    locked: bool | None = None
    z_order: int | None = Field(default=None, ge=-10_000, le=10_000)
    #: A transition (V-10); ``retired`` needs ``status_reason`` and the lead role.
    bed_status: BedStatus | None = None
    status_reason: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def _only_clearable_fields_take_null(self) -> Self:
        _no_null_for(self, ("name", "sun_exposure", "geometry", "locked", "z_order", "bed_status"))
        if not self.model_fields_set:
            raise ValueError("A PATCH needs at least one field.")
        return self


class GardenObjectPatch(_Strict):
    """``PATCH /garden-objects/{key}`` (GP-API-013): geometry and fields in one structural change."""

    label: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)
    props: dict[str, Any] | None = None
    off_site: bool | None = None
    geometry: Geometry | None = None
    locked: bool | None = None
    z_order: int | None = Field(default=None, ge=-10_000, le=10_000)

    @model_validator(mode="after")
    def _only_notes_take_null(self) -> Self:
        _no_null_for(self, ("label", "props", "off_site", "geometry", "locked", "z_order"))
        if not self.model_fields_set:
            raise ValueError("A PATCH needs at least one field.")
        return self


class SlotPatch(_Strict):
    """``PATCH /slots/{key}`` (GP-API-014): geometry (bed frame), role and capacity."""

    geometry: BedFrameGeometry | None = None
    slot_role: SlotRole | None = None
    capacity_plants: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def _no_null(self) -> Self:
        _no_null_for(self, ("geometry", "slot_role", "capacity_plants"))
        if not self.model_fields_set:
            raise ValueError("A PATCH needs at least one field.")
        return self


class SlotBatchItem(_Strict):
    """One slot of ``POST /locations/{key}/slots/batch`` (GP-API-015); ``location_key`` is the path's."""

    slot_id: str = Field(min_length=3, max_length=100)
    slot_role: SlotRole = SlotRole.POSITION
    geometry: BedFrameGeometry
    capacity_plants: int = Field(default=1, ge=1, le=20)
    row_index: int | None = Field(default=None, ge=0)
    sequence: int | None = Field(default=None, ge=1)
    geometry_source: GeometrySource = GeometrySource.EDITOR
    container_volume_l: float | None = Field(default=None, gt=0)
    planned_spacing_cm: float | None = Field(default=None, gt=0)


class SlotBatchRequest(_Strict):
    """``replace_unoccupied`` removes the bed's unoccupied, unreserved, unarchived slots first; ``append`` keeps all."""

    mode: Literal["replace_unoccupied", "append"]
    slots: list[SlotBatchItem] = Field(max_length=100_000)


@dataclass(frozen=True)
class SlotBatchResult:
    created_keys: list[str]
    deleted_count: int
    kept_count: int


@dataclass(frozen=True)
class BedSummaryView:
    """The head data of the bed view (GP-FR-047): the document, its counters and the derived season state."""

    location: Location
    counters: BedCounters
    #: ``planted`` or ``empty`` until the run, rotation and covering data of wave 3/4 exist (§7.4).
    season_state: str
    is_bed: bool


# ── Read model (GP-API-001) ───────────────────────────────────────────────────


class PlanAuditRecord(BaseModel):
    """A stored row of ``garden_plan_audit`` (REQ-053 §20.13, SR-011): who removed or reshaped what, at which revision.

    Carries ``tenant_key`` (E-01): the log is read per tenant and erased with it. ``user_key`` is
    pseudonymised on account erasure, ``summary`` is the name or label of what was removed.
    """

    tenant_key: str
    site_key: str
    revision: int
    user_key: str
    #: ``delete``, ``delete_cascade``, ``set_boundary``, ``retire`` or ``reactivate`` (a bed's lifecycle, §7.4).
    op: str
    #: ``location``, ``garden_object``, ``site``, ``care_event`` (a redaction) or ``irrigation_zone`` (a zone delete,
    #: REQ-053 WP 7.1).
    entity: str
    key: str
    summary: str = Field(default="", max_length=200)
    at: datetime
    #: Only on the row a ``replace`` import writes (``import_snapshot``): the plan as it was, in the shape of
    #: ``GET /plan/export``. The change-log route lists the row (op, summary) but never the payload.
    snapshot: dict[str, Any] | None = None


class PlanAuditEntry(BaseModel):
    """One row of ``garden_plan_audit`` as the API lists it (the account is a display name, never a key)."""

    revision: int
    op: str
    entity: str
    key: str
    summary: str = ""
    at: datetime
    changed_by_name: str | None = None


class PlantShortInfo(BaseModel):
    key: str
    instance_id: str
    species_key: str
    phase_key: str | None = None
    slot_key: str | None = None
    location_key: str | None = None


class SlotSpeciesHint(BaseModel):
    """What the species standing in, or planned for, a slot says about its neighbourhood (GP-FR-130).

    The raw species strings (``"60--80"`` ranges); the adjacency engine reads the lower value.
    """

    slot_key: str
    species_key: str
    spacing_cm: str | None = None
    row_spacing_cm: str | None = None
    mature_width_cm: str | None = None
    growth_habit: str | None = None


class TaskCounter(BaseModel):
    open_task_count: int = 0
    overdue_task_count: int = 0
    #: Earliest due date of an open task (ISO string as stored); the bed list and summary show it.
    next_due_at: str | None = None


class PlanSlotView(BaseModel):
    """A slot with its geometry transformed into the plan frame (§9.2, GP-ACC-005)."""

    key: str
    slot_id: str
    location_key: str
    slot_role: SlotRole
    capacity_plants: int
    currently_occupied: bool
    row_index: int | None = None
    sequence: int | None = None
    #: ``None`` for a slot without geometry or below a bed without one (unplaced).
    plan_geometry: dict[str, Any] | None = None


class GardenPlanView(BaseModel):
    """The whole plan of a site in one object (GP-API-001)."""

    site_key: str
    site_name: str
    plan_revision: int = 0
    plan: SitePlan | None = None
    plan_updated_by_name: str | None = None
    locations: list[Location] = Field(default_factory=list)
    garden_objects: list[GardenObject] = Field(default_factory=list)
    slots: list[PlanSlotView] = Field(default_factory=list)
    plants: list[PlantShortInfo] = Field(default_factory=list)
    task_counters: dict[str, TaskCounter] = Field(default_factory=dict)
    #: Keyed by garden-object key — a separate map because object and location keys come from different collections.
    object_task_counters: dict[str, TaskCounter] = Field(default_factory=dict)
    season_states: dict[str, str] = Field(default_factory=dict)
    #: Newest watering per bed (GP-UX-006); filled with the task counters (``include=tasks``).
    last_watered: dict[str, datetime] = Field(default_factory=dict)
    zones: list[dict[str, Any]] = Field(default_factory=list)
    included: list[str] = Field(default_factory=list)
