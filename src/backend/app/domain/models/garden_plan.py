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
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

from app.common.enums import GardenObjectType, SlotRole, SunExposure
from app.domain.models.garden_object import GardenObject
from app.domain.models.geometry import Geometry
from app.domain.models.site import Location, SitePlan

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
    time_budget_seconds: float = BATCH_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class PlanBatchOutcome:
    """What the transaction reports: the new revision and the temp-key → key assignment."""

    plan_revision: int
    key_map: dict[str, str]


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
    #: ``delete``, ``delete_cascade`` or ``set_boundary``.
    op: str
    #: ``location``, ``garden_object`` or ``site``.
    entity: str
    key: str
    summary: str = Field(default="", max_length=200)
    at: datetime


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


class TaskCounter(BaseModel):
    open_task_count: int = 0
    overdue_task_count: int = 0


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
    season_states: dict[str, str] = Field(default_factory=dict)
    zones: list[dict[str, Any]] = Field(default_factory=list)
    included: list[str] = Field(default_factory=list)
