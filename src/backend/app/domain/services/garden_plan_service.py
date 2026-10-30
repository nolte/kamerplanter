"""The garden plan of a site: the one-request read model, the boundary and the transactional batch (REQ-053 WP 1.8).

**Check order (SR-013, §22.1).** (1) authentication — the route's dependency; (2) tenant anchor
and resolution of every referenced key; (3) the caller's role *per operation*; (4) Pydantic;
(5) domain validation; (6) the revision check, which runs **inside** the transaction. The order
is the contract: a foreign site answers 404 before any body field is read, so neither a 409 nor
an ``outside_parent`` can reveal that a site, or its geometry, exists; and a grower's batch with
one ``delete`` is refused with 403 before its geometry is looked at, so the refusal cannot be
turned into an oracle for the rest of the request (SR-001).

**Where the rules live.** Containment and overlap are decided by
:mod:`app.domain.engines.garden_plan_engine` on a *working copy* of the plan, before the
transaction opens (GP-NFR-013): the transaction holds only the revision check and the writes.
Ownership is resolved here, through :mod:`app.domain.services.location_ownership` and the site
join of the repository — never in the router (GP-NFR-014, T-04) — and every public method takes
``*, tenant_key: str`` without a default.

**Locations, slots and garden objects carry no ``tenant_key``** (E-01, #2107): the site is the
owner. Every key in a request is resolved against the structure of the *path* site, so a key of
another site of the same tenant is as unreachable as one of another tenant (T-03).

**Logs carry no user text** (GP-NFR-060, SR-025): site key, revision, counts, durations and error
codes — never a name, a label, a note or a payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any

import structlog
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from app.common.enums import SunProfileSource, TenantRole
from app.common.exceptions import (
    ForbiddenError,
    PlanError,
    PlanRevisionConflictError,
    PlanValidationError,
)
from app.common.types import SiteKey
from app.domain.calculators.geometry_calculator import (
    area_m2,
    to_local_shape,
    transform_bed_to_plan,
    validate_geometry,
)
from app.domain.calculators.template_placement_calculator import place_geometry
from app.domain.engines.garden_plan_engine import (
    ERROR_BOUNDARY_SHRINKS,
    ERROR_OBJECT_LOCKED,
    ERROR_REFERENCE_NOT_FOUND,
    ERROR_SLOT_OUTSIDE_BED,
    PlanEntity,
    boundary_violations,
    check_entity,
    slots_outside_bed,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.site_conditions_merge import merge_site_conditions
from app.domain.interfaces.bed_template_repository import IBedTemplateRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.irrigation_zone_repository import IIrrigationZoneRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.bed_template import BedTemplate
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BATCH_TIME_BUDGET_SECONDS,
    ERROR_ZONE_QUOTA,
    MAX_BATCH_BODY_BYTES,
    MAX_BATCH_POINTS,
    MAX_OPERATIONS,
    MAX_PLAN_OBJECTS_PER_SITE,
    MAX_PLAN_ZONES,
    CreateGardenObjectOp,
    CreateLocationOp,
    DeleteOp,
    DerivedGeometry,
    GardenObjectFieldsPatch,
    GardenPlanView,
    LocationFieldsPatch,
    PlanAuditEntry,
    PlanBatchResult,
    PlanBatchWrite,
    PlanOperation,
    PlanOperationAdapter,
    PlanSiteConditionsPatch,
    PlanSlotView,
    SetBoundaryOp,
    SetLockedOp,
    SetZOrderOp,
    TemplateLocationData,
    UpdateFieldsOp,
    UpdateGeometryOp,
)
from app.domain.models.geometry import (
    GEOMETRY_INVALID,
    POINT_INDEX_KEY,
    CircleGeometry,
    Geometry,
    PointGeometry,
    PolygonGeometry,
    PolylineGeometry,
    round_length,
)
from app.domain.models.site import Location, Site, SiteConditions, SitePlan, Slot
from app.domain.services.location_ownership import require_owned_site
from app.domain.services.site_service import place_in_tree

logger = structlog.get_logger()

#: ``?include=`` values of GP-API-001.
INCLUDE_PARTS: frozenset[str] = frozenset({"plants", "tasks", "zones"})

#: How many findings one refusal lists; the rest would only repeat the same mistake.
_MAX_FINDINGS = 50

_GEOMETRY_FIELDS = frozenset({"geometry", "boundary", "origin", "points", "width_m", "length_m", "radius_m"})

#: What a batch may write on a location / garden object. Everything else a document holds belongs to other
#: paths (status, soil, irrigation zone, tank, pitch …) that run outside the plan revision (GP-NFR-007), and a
#: batch must not write it back with the value it read earlier. ``site_conditions`` is therefore no column here:
#: the batch changes only its sun profile (#2538) and writes that sub-path alone (``location_sun_profiles``).
_LOCATION_COLUMNS: frozenset[str] = frozenset(
    {"geometry", "bbox", "area_m2", "name", "path", "depth", "description", "notes", "sun_exposure", "height_m"}
    | {"locked", "z_order"}
)
_OBJECT_COLUMNS: frozenset[str] = frozenset(
    {"geometry", "bbox", "label", "notes", "props", "off_site", "locked", "z_order"}
)

#: The request-local name of the one bed ``place-template`` creates; the answer maps it to the real key.
_TEMPLATE_TEMP_KEY = "template_bed"

_ENTITY_LOCATION = "location"
_ENTITY_OBJECT = "garden_object"

#: ``(field, code, key)`` plus the op it belongs to.
type _Finding = tuple[int | None, str, str, dict[str, Any]]


@dataclass
class _Work:
    """The plan as the batch's operations leave it — a working copy, never persisted as such."""

    locations: dict[str, Location]
    objects: dict[str, GardenObject]
    boundary: Geometry | None
    #: Stored keys as the batch began; everything else in the dicts is a ``temp_key``.
    stored_locations: dict[str, Location]
    stored_objects: dict[str, GardenObject]
    temp_locations: list[str] = field(default_factory=list)
    temp_objects: list[str] = field(default_factory=list)
    #: ``(entity, key)`` → index of the operation that last touched its geometry.
    moved: dict[tuple[str, str], int] = field(default_factory=dict)
    #: Existing keys deleted by an explicit ``delete`` / by cascade, with the op index and a short summary.
    deleted_locations: dict[str, tuple[int, str, bool]] = field(default_factory=dict)
    deleted_objects: dict[str, tuple[int, str, bool]] = field(default_factory=dict)
    boundary_op: int | None = None
    plan_changes: SetBoundaryOp | None = None
    findings: list[_Finding] = field(default_factory=list)

    def known(self, entity: str, key: str) -> bool:
        return key in (self.locations if entity == _ENTITY_LOCATION else self.objects)


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model.model_dump`` through a receiver typed as the pydantic base.

    The write-route sweep (``tests/unit/api/_write_call_graph.py``) resolves a receiver by its annotation; a
    domain model's inherited ``model_dump`` resolves to nothing, and the sweep's blind-spot ceiling must not grow.
    """
    return model.model_dump(**options)


def _copy[TModel: BaseModel](model: TModel) -> TModel:
    """A deep copy of a model; the working copy of the plan never shares a document with the stored one."""
    return model.model_copy(deep=True)


def _changed_fields(working: BaseModel, stored: BaseModel, columns: frozenset[str]) -> dict[str, Any]:
    """The columns of *columns* in which the working copy differs from what was read, JSON-shaped."""
    now = _dump(working, by_alias=True, mode="json")
    before = _dump(stored, by_alias=True, mode="json")
    return {column: now.get(column) for column in sorted(columns) if now.get(column) != before.get(column)}


def _merged_sun_profile(location: Location, sent: PlanSiteConditionsPatch) -> SiteConditions:
    """The stored site conditions with the sent sun-profile keys laid over them, by the PATCH rule (#2538).

    Called only when *sent* carries at least one sun-profile key. The microclimate is the stored one, so the
    frost risk - and with it the legacy ``frost_exposed`` mirror of ``PATCH /locations`` - cannot change
    through the plan batch. A sun profile edited in the editor is a manual value (``source = manual``),
    whatever it was before.
    """
    merged = merge_site_conditions(location.site_conditions, sent)
    merged.sun_profile.source = SunProfileSource.MANUAL
    return merged


def _sun_profile_of(location: Location) -> dict[str, Any] | None:
    """The location's sun profile, JSON-shaped, or ``None`` when it has no site conditions at all."""
    if location.site_conditions is None:
        return None
    return _dump(location.site_conditions.sun_profile, mode="json")


def _mapping(raw: object) -> dict[str, Any]:
    """*raw* when it is a mapping, else an empty one: an operation is untrusted until Pydantic has read it."""
    return raw if isinstance(raw, dict) else {}


def _errors(error: PydanticValidationError) -> list[ErrorDetails]:
    return error.errors()


def _now() -> float:
    """The monotonic clock; a module function so a test can replace it."""
    return monotonic()


def _json_tail(error: ErrorDetails, *, tagged: bool) -> str:
    """The dotted field path of a Pydantic error; *tagged* drops the leading discriminator tag of a union."""
    loc = error["loc"][1:] if tagged else error["loc"]
    return ".".join(str(part) for part in loc) or "request"


def _finding_code(error: ErrorDetails) -> str:
    """V-01 (``geometry.invalid``) for a geometry defect, the generic code for anything else."""
    parts = {str(part) for part in error["loc"]}
    return "geometry.invalid" if parts & _GEOMETRY_FIELDS else "validation.invalid"


def _finding_extra(error: ErrorDetails) -> dict[str, Any]:
    """The offending vertex of a coordinate-range violation (GP-ACC-056), else nothing."""
    point_index = error.get("ctx", {}).get(POINT_INDEX_KEY) if error["type"] == GEOMETRY_INVALID else None
    return {POINT_INDEX_KEY: point_index} if isinstance(point_index, int) else {}


def _findings_of(error: PydanticValidationError, op_index: int | None, *, tagged: bool = False) -> list[_Finding]:
    return [(op_index, _json_tail(e, tagged=tagged), _finding_code(e), _finding_extra(e)) for e in _errors(error)]


def _count_points(raw: Any) -> int:
    """Σ of polygon and polyline points in a raw operation (GP-NFR-013), without parsing it."""
    mapping = _mapping(raw)
    if mapping:
        points = mapping.get("points")
        own = len(points) if isinstance(points, list) else 0
        return own + sum(_count_points(value) for value in mapping.values())
    if isinstance(raw, list):
        return sum(_count_points(value) for value in raw)
    return 0


def _summary(text: str | None, fallback: str) -> str:
    return (text or fallback)[:200]


class GardenPlanService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        zone_repo: IIrrigationZoneRepository | None = None,
        template_repo: IBedTemplateRepository | None = None,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        #: ``None`` = a caller that never asks for ``include=zones`` (the read model then carries no zones).
        self._zones = zone_repo
        #: ``None`` = a caller that never places a template; no template key is then visible (WP 7.9).
        self._templates = template_repo

    # ── Anchor ────────────────────────────────────────────────────────────────

    def _owned_site(self, site_key: SiteKey, *, tenant_key: str) -> Site:
        """T-01/T-04: the site behind the path key, 404 when it is absent or another tenant's."""
        return require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    @staticmethod
    def _revision_of(site: Site) -> int:
        return site.plan.plan_revision if site.plan is not None else 0

    # ── GP-API-001: the read model ────────────────────────────────────────────

    def get_plan(
        self, site_key: SiteKey, *, tenant_key: str, include: frozenset[str] = INCLUDE_PARTS
    ) -> GardenPlanView:
        """The whole plan of a site in one object: structure, slots in plan coordinates, plants, task counters."""
        site = self._owned_site(site_key, tenant_key=tenant_key)
        data = self._plan.load_read_model(
            site_key, tenant_key=tenant_key, include_plants="plants" in include, include_tasks="tasks" in include
        )
        by_key = {loc.key: loc for loc in data.locations if loc.key}
        slots = [view for slot in data.slots if (view := self._slot_view(slot, by_key.get(slot.location_key)))]
        occupied = {plant.location_key for plant in data.plants if plant.location_key}
        # Derived, never set (§7.4). ``green_manure``, ``fallow`` and ``winter_covered`` need the run's
        # ``plan_role``, the crop-rotation plan and the care events (WP 3.x/4.x); until they exist a bed
        # is ``planted`` when a plant with ``removed_on = null`` stands in it and ``empty`` otherwise.
        season_states = (
            {key: "planted" if key in occupied else "empty" for key in by_key} if "plants" in include else {}
        )
        return GardenPlanView(
            site_key=site_key,
            site_name=site.name,
            plan_revision=self._revision_of(site),
            plan=site.plan,
            plan_updated_by_name=data.plan_updated_by_name,
            locations=data.locations,
            garden_objects=data.garden_objects,
            slots=slots,
            plants=data.plants if "plants" in include else [],
            task_counters=data.task_counters if "tasks" in include else {},
            object_task_counters=data.object_task_counters if "tasks" in include else {},
            season_states=season_states,
            last_watered=data.last_watered if "tasks" in include else {},
            zones=self.zone_rows(site_key, tenant_key=tenant_key) if "zones" in include else [],
            included=sorted(include),
        )

    def count_zones(self, site_key: SiteKey, *, tenant_key: str) -> int:
        """How many irrigation zones the site holds (at most :data:`MAX_PLAN_ZONES` + 1 are read)."""
        if self._zones is None:
            return 0
        return len(self._zones.list_zones_by_site(site_key, tenant_key=tenant_key, offset=0, limit=MAX_PLAN_ZONES + 1))

    def zone_rows(self, site_key: SiteKey, *, tenant_key: str) -> list[dict[str, Any]]:
        """The site's irrigation zones with the beds each covers (GP-API-001 ``include=zones``, WP 7.2).

        The caller has resolved the site under the tenant; the zones are read under the tenant again.

        At most :data:`MAX_PLAN_ZONES`, by name - more is 422 ``irrigation_zone.quota_exceeded``, never a silent
        cut. The technical coupling beyond ``actuator_key`` (the bound Home Assistant entity)
        is never part of the read model (SR-014, GP-NFR-060).
        """
        if self._zones is None:
            return []
        zones = self._zones.list_zones_by_site(site_key, tenant_key=tenant_key, offset=0, limit=MAX_PLAN_ZONES + 1)
        if len(zones) > MAX_PLAN_ZONES:
            # Never a silent cut: a truncated read would make the export an incomplete backup.
            raise PlanError(
                ERROR_ZONE_QUOTA,
                f"The site has more than {MAX_PLAN_ZONES} irrigation zones.",
                status_code=422,
                field="zones",
                limit=MAX_PLAN_ZONES,
            )
        covered = self._zones.covered_location_keys([zone.key or "" for zone in zones], tenant_key=tenant_key)
        return [
            {
                "key": zone.key or "",
                "name": zone.name,
                "irrigation_type": zone.irrigation_type.value,
                "water_source_key": zone.water_source_key,
                "actuator_key": zone.actuator_key,
                "flow_rate_l_per_min": zone.flow_rate_l_per_min,
                "flow_rate_source": zone.flow_rate_source.value,
                "application_efficiency": zone.application_efficiency,
                "color": zone.color,
                "schedule_hint": zone.schedule_hint,
                "location_keys": list(covered.get(zone.key or "", [])),
            }
            for zone in zones
        ]

    @staticmethod
    def _slot_view(slot: Slot, bed: Location | None) -> PlanSlotView | None:
        if not slot.key:
            return None
        plan_geometry: dict[str, Any] | None = None
        if slot.geometry is not None and bed is not None and bed.geometry is not None:
            plan_geometry = _slot_in_plan_frame(slot.geometry, bed.geometry)
        return PlanSlotView(
            key=slot.key,
            slot_id=slot.slot_id,
            location_key=slot.location_key,
            slot_role=slot.slot_role,
            capacity_plants=slot.capacity_plants,
            currently_occupied=slot.currently_occupied,
            row_index=slot.row_index,
            sequence=slot.sequence,
            plan_geometry=plan_geometry,
        )

    # ── GP-API-008: the change log ────────────────────────────────────────────

    def list_audit(
        self, site_key: SiteKey, *, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[PlanAuditEntry]:
        self._owned_site(site_key, tenant_key=tenant_key)
        return self._plan.list_audit(site_key, tenant_key=tenant_key, offset=offset, limit=limit)

    # ── GP-API-002: the boundary ──────────────────────────────────────────────

    def set_boundary(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        operation: SetBoundaryOp,
        expected_revision: int | None,
    ) -> PlanBatchResult:
        """Create the plan or replace its boundary; raises ``plan_revision`` by one (GP-ACC-001).

        ``expected_revision`` is optional here: the first save of a plan has no revision to expect.
        When given it is enforced like in the batch.
        """
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        basis = self._revision_of(site)
        expected = basis if expected_revision is None else expected_revision
        return self._apply(
            site,
            tenant_key=tenant_key,
            user_key=user_key,
            expected_revision=expected,
            basis_revision=basis,
            operations=[operation],
            started=_now(),
        )

    # ── GP-API-003: the batch ─────────────────────────────────────────────────

    def apply_batch(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        expected_revision: int | None,
        operations: list[Any],
        body_bytes: int,
    ) -> PlanBatchResult:
        """Apply the operations atomically, or none (GP-NFR-013). See the module docstring for the order.

        ``expected_revision = None`` expects the revision the validation ran against: the single-resource
        routes (WP 1.9, GP-API-010/013) have no client revision to send, yet a writer that lost the race
        for the site document is still refused with 409.
        """
        started = _now()
        site = self._owned_site(site_key, tenant_key=tenant_key)  # (2) tenant anchor

        # V-17 and the size ceiling concern the request as a whole and say nothing about the plan.
        if len(operations) > MAX_OPERATIONS:
            raise PlanError(
                "batch.too_many_operations",
                f"A batch holds at most {MAX_OPERATIONS} operations.",
                status_code=422,
                limit=MAX_OPERATIONS,
                current=len(operations),
            )
        if body_bytes > MAX_BATCH_BODY_BYTES:
            raise PlanError(
                "batch.too_complex",
                "The batch request is too large.",
                status_code=422,
                limit=MAX_BATCH_BODY_BYTES,
                current=body_bytes,
            )

        locations, objects = self._plan.load_structure(site_key, tenant_key=tenant_key)
        self._resolve_references(operations, locations, objects)  # (2) reference resolution, V-18
        self._check_roles(role, operations)  # (3) role per operation, SR-001
        parsed = self._parse(operations)  # (4) Pydantic
        if sum(_count_points(raw) for raw in operations) > MAX_BATCH_POINTS:
            raise PlanError(
                "batch.too_complex",
                f"A batch holds at most {MAX_BATCH_POINTS} polygon and polyline points.",
                status_code=422,
                limit=MAX_BATCH_POINTS,
                current=sum(_count_points(raw) for raw in operations),
            )
        return self._apply(
            site,
            tenant_key=tenant_key,
            user_key=user_key,
            expected_revision=self._revision_of(site) if expected_revision is None else expected_revision,
            basis_revision=self._revision_of(site),
            operations=parsed,
            started=started,
            structure=(locations, objects),
        )

    # ── §21.7: place a bed template ──────────────────────────────────────────

    def place_template(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        template_key: str,
        origin: tuple[float, float],
        rotation_deg: float,
        expected_revision: int,
    ) -> PlanBatchResult:
        """Create one bed from a template, through the same path as a batch ``create_location`` (WP 7.9, #2475).

        Order (SR-013): tenant anchor (404) -> role (403) -> the template, which must be a system template or the
        tenant's own (422 ``reference.not_found`` for an absent *and* a foreign key alike) -> its location type
        -> the geometry placed at ``origin`` and turned by ``rotation_deg`` (422 ``geometry.invalid``) -> the
        plan rules of any batch: containment (422 ``geometry.outside_parent``), overlap, quota and, inside the
        transaction, the revision (409 ``plan.revision_conflict``).

        The bed receives a **copy** of the template's fields (name, location type, geometry, height, soil axes);
        ``Location.template_key`` records where it came from and nothing else follows the template afterwards.
        ``recurring_task_templates`` are not applied (operator decision of 2026-10-19, #2466 item 9).
        """
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        template = self._visible_template(template_key, tenant_key=tenant_key)
        if template.location_type_key not in self._plan.bed_type_flags([template.location_type_key]):
            raise PlanValidationError([(None, "template_key", ERROR_REFERENCE_NOT_FOUND, {})])
        try:
            data = TemplateLocationData.model_validate(
                {
                    "name": template.name,
                    "location_type_key": template.location_type_key,
                    "geometry": place_geometry(template.default_geometry, origin=origin, rotation_deg=rotation_deg),
                    "height_m": template.height_m,
                    "template_key": template.key,
                    "soil_profile": template.soil_profile_defaults.to_soil_profile()
                    if template.soil_profile_defaults is not None
                    else None,
                }
            )
        except PydanticValidationError as exc:
            raise PlanValidationError(_findings_of(exc, None)) from exc
        operation = CreateLocationOp(op="create_location", temp_key=_TEMPLATE_TEMP_KEY, data=data)
        return self._apply(
            site,
            tenant_key=tenant_key,
            user_key=user_key,
            expected_revision=expected_revision,
            basis_revision=self._revision_of(site),
            operations=[operation],
            started=_now(),
        )

    def _visible_template(self, template_key: str, *, tenant_key: str) -> BedTemplate:
        """The template when it is a system one or the tenant's own; otherwise 422 - a foreign key is no oracle."""
        found = self._templates.get_visible_by_key(template_key, tenant_key=tenant_key) if self._templates else None
        if found is None:
            raise PlanValidationError([(None, "template_key", ERROR_REFERENCE_NOT_FOUND, {})])
        return found

    def visible_template_keys(self, keys: list[str], *, tenant_key: str) -> set[str]:
        """Which of ``keys`` are system templates or the tenant's own (the import resolves ``template_key`` so)."""
        if not keys or self._templates is None:
            return set()
        return self._templates.visible_keys(keys, tenant_key=tenant_key)

    # ── (2) references ────────────────────────────────────────────────────────

    def _resolve_references(
        self, operations: list[Any], locations: list[Location], objects: list[GardenObject]
    ) -> None:
        """T-03 / GP-NFR-058: every referenced key must be a stored one of the path site or a temp key declared earlier.

        Reads only what is needed to find references, defensively: a malformed operation is left
        for the Pydantic step, which reports it with its own code.
        """
        known: dict[str, set[str]] = {
            _ENTITY_LOCATION: {loc.key for loc in locations if loc.key},
            _ENTITY_OBJECT: {obj.key for obj in objects if obj.key},
        }
        declared_locations: set[str] = set()
        declared_objects: set[str] = set()
        type_keys: list[tuple[int, str]] = []
        findings: list[_Finding] = []

        for index, raw in enumerate(operations):
            item = _mapping(raw)
            name = item.get("op")
            data = _mapping(item.get("data"))
            if name in ("update_geometry", "update_fields", "delete", "set_locked", "set_z_order"):
                entity, key = item.get("entity"), item.get("key")
                if entity in (_ENTITY_LOCATION, _ENTITY_OBJECT) and isinstance(key, str):
                    declared = declared_locations if entity == _ENTITY_LOCATION else declared_objects
                    if key not in known[entity] and key not in declared:
                        findings.append((index, "key", ERROR_REFERENCE_NOT_FOUND, {}))
            if name in ("create_location", "create_garden_object"):
                parent = data.get("parent_location_key")
                if isinstance(parent, str) and parent not in known[_ENTITY_LOCATION] | declared_locations:
                    findings.append((index, "data.parent_location_key", ERROR_REFERENCE_NOT_FOUND, {}))
                temp = item.get("temp_key")
                if isinstance(temp, str):
                    (declared_locations if name == "create_location" else declared_objects).add(temp)
                location_type = data.get("location_type_key")
                if name == "create_location" and isinstance(location_type, str):
                    type_keys.append((index, location_type))
        if type_keys:
            flags = self._plan.bed_type_flags([key for _, key in type_keys])
            findings.extend(
                (index, "data.location_type_key", ERROR_REFERENCE_NOT_FOUND, {})
                for index, key in type_keys
                if key not in flags
            )
        if findings:
            raise PlanValidationError(sorted(findings, key=lambda f: (f[0] is None, f[0] or 0))[:_MAX_FINDINGS])

    # ── (3) roles ─────────────────────────────────────────────────────────────

    @staticmethod
    def _check_roles(role: TenantRole, operations: list[Any]) -> None:
        """SR-001: each operation against §21.8 *before* any of them is parsed or validated.

        ``delete`` needs lead; everything else a grower. The batch is refused whole, with the
        index of the first operation above the caller's role.
        """
        for index, raw in enumerate(operations):
            name = _mapping(raw).get("op")
            allowed = (
                MembershipEngine.can_delete_resource(role)
                if name == "delete"
                else MembershipEngine.can_edit_resource(role)
            )
            if not allowed:
                raise PlanError(
                    "batch.operation_forbidden",
                    "The batch contains an operation above your role; nothing was applied.",
                    status_code=403,
                    op_index=index,
                )

    # ── (4) Pydantic ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse(operations: list[Any]) -> list[PlanOperation]:
        parsed: list[PlanOperation] = []
        findings: list[_Finding] = []
        for index, raw in enumerate(operations):
            try:
                operation = PlanOperationAdapter.validate_python(raw)
            except PydanticValidationError as exc:
                findings.extend(_findings_of(exc, index, tagged=True))
                continue
            if isinstance(operation, UpdateFieldsOp):
                findings.extend(GardenPlanService._check_fields_patch(operation, index))
            parsed.append(operation)
        if findings:
            raise PlanValidationError(findings[:_MAX_FINDINGS])
        return parsed

    @staticmethod
    def _check_fields_patch(operation: UpdateFieldsOp, index: int) -> list[_Finding]:
        model = LocationFieldsPatch if operation.entity == _ENTITY_LOCATION else GardenObjectFieldsPatch
        try:
            model(**operation.fields)
        except PydanticValidationError as exc:
            return [(index, f"fields.{_json_tail(e, tagged=False)}", "validation.invalid", {}) for e in _errors(exc)]
        return []

    # ── (5) domain, (6) transaction ───────────────────────────────────────────

    def _apply(
        self,
        site: Site,
        *,
        tenant_key: str,
        user_key: str,
        expected_revision: int,
        basis_revision: int,
        operations: list[PlanOperation],
        started: float,
        structure: tuple[list[Location], list[GardenObject]] | None = None,
    ) -> PlanBatchResult:
        site_key = site.key or ""
        locations, objects = structure or self._plan.load_structure(site_key, tenant_key=tenant_key)
        work = _Work(
            locations={loc.key: _copy(loc) for loc in locations if loc.key},
            objects={obj.key: _copy(obj) for obj in objects if obj.key},
            boundary=site.plan.boundary if site.plan is not None else None,
            stored_locations={loc.key: loc for loc in locations if loc.key},
            stored_objects={obj.key: obj for obj in objects if obj.key},
        )
        objects_before = len(work.locations) + len(work.objects)
        try:
            for index, operation in enumerate(operations):
                self._run_operation(work, operation, index, user_key=user_key, site_key=site_key)
            if work.findings:
                raise PlanValidationError(self._ordered(work.findings))
            self._check_quota(work, objects_before)
            self._check_deadline(started)
            self._validate_geometry(work)
            self._check_slots_of_reshaped_beds(work, site_key=site_key, tenant_key=tenant_key)
            if work.findings:
                raise PlanValidationError(self._ordered(work.findings))
            self._check_active_plants(work, tenant_key=tenant_key)
            self._check_deadline(started)
        except PlanValidationError as exc:
            logger.warning("garden_plan.validation_failed", site_key=site_key, codes=sorted(set(exc.codes)))
            raise

        write = self._build_write(
            work,
            site=site,
            tenant_key=tenant_key,
            editor_key=user_key,
            expected_revision=expected_revision,
            basis_revision=basis_revision,
            remaining=BATCH_TIME_BUDGET_SECONDS - (_now() - started),
        )
        try:
            outcome = self._plan.apply_plan_batch(write)
        except PlanRevisionConflictError:
            logger.warning("garden_plan.revision_conflict", site_key=site_key)
            raise
        result = self._result(work, write, outcome.plan_revision, outcome.key_map)
        logger.info(
            "garden_plan.batch_applied",
            site_key=site_key,
            revision=outcome.plan_revision,
            op_count=len(operations),
            duration_ms=round((_now() - started) * 1000),
        )
        return result

    @staticmethod
    def _ordered(findings: list[_Finding]) -> list[_Finding]:
        return sorted(findings, key=lambda f: (f[0] is None, f[0] or 0))[:_MAX_FINDINGS]

    def _check_deadline(self, started: float) -> None:
        if _now() - started > BATCH_TIME_BUDGET_SECONDS:
            raise PlanError(
                "batch.too_complex",
                "The batch took longer than its time budget; nothing was applied.",
                status_code=422,
                limit=int(BATCH_TIME_BUDGET_SECONDS),
            )

    @staticmethod
    def _check_quota(work: _Work, before: int) -> None:
        """GP-NFR-017: ≤ 500 locations + garden objects per site. An already larger plan may shrink."""
        current = len(work.locations) + len(work.objects)
        if current > MAX_PLAN_OBJECTS_PER_SITE and current > before:
            raise PlanError(
                "plan.quota_exceeded",
                f"A site holds at most {MAX_PLAN_OBJECTS_PER_SITE} locations and garden objects.",
                status_code=422,
                limit=MAX_PLAN_OBJECTS_PER_SITE,
                current=current,
            )

    def _check_active_plants(self, work: _Work, *, tenant_key: str) -> None:
        """V-09: nothing with a plant in it is deleted. The repository re-checks inside the transaction."""
        keys = sorted(work.deleted_locations)
        if not keys:
            return
        count = self._plan.count_active_plants(keys, tenant_key=tenant_key)
        if count:
            index = min(op for op, _, _ in work.deleted_locations.values())
            raise PlanError(
                "location.has_active_plants",
                "A location with active plants cannot be deleted.",
                status_code=409,
                op_index=index,
                active_plant_count=count,
            )

    # ── operations on the working copy ────────────────────────────────────────

    def _run_operation(
        self, work: _Work, operation: PlanOperation, index: int, *, user_key: str, site_key: str
    ) -> None:
        if isinstance(operation, CreateLocationOp):
            self._create_location(work, operation, index, site_key)
        elif isinstance(operation, CreateGardenObjectOp):
            self._create_object(work, operation, index, site_key, user_key)
        elif isinstance(operation, UpdateGeometryOp):
            self._update_geometry(work, operation, index)
        elif isinstance(operation, UpdateFieldsOp):
            self._update_fields(work, operation, index)
        elif isinstance(operation, DeleteOp):
            self._delete(work, operation, index)
        elif isinstance(operation, SetBoundaryOp):
            self._set_boundary(work, operation, index)
        elif isinstance(operation, SetLockedOp):
            self._set_attr(work, operation.entity, operation.key, "locked", operation.locked)
        elif isinstance(operation, SetZOrderOp):
            self._set_attr(work, operation.entity, operation.key, "z_order", operation.z_order)

    def _temp_key_error(self, work: _Work, temp_key: str, index: int) -> bool:
        if temp_key in work.locations or temp_key in work.objects:
            work.findings.append((index, "temp_key", "validation.invalid", {}))
            return True
        return False

    def _create_location(self, work: _Work, op: CreateLocationOp, index: int, site_key: str) -> None:
        if self._temp_key_error(work, op.temp_key, index):
            return
        data = op.data
        try:
            location = Location(
                name=data.name,
                site_key=site_key,
                parent_location_key=data.parent_location_key,
                location_type_key=data.location_type_key,
                geometry=data.geometry,
                height_m=data.height_m,
                description=data.description,
                notes=data.notes,
                sun_exposure=data.sun_exposure,
                locked=data.locked,
                z_order=data.z_order,
                area_m2=0.0,
                template_key=data.template_key if isinstance(data, TemplateLocationData) else None,
                soil_profile=data.soil_profile if isinstance(data, TemplateLocationData) else None,
            )
        except PydanticValidationError as exc:
            work.findings.extend(_findings_of(exc, index))
            return
        parent = work.locations.get(data.parent_location_key) if data.parent_location_key else None
        place_in_tree(location, parent)
        work.locations[op.temp_key] = location
        work.temp_locations.append(op.temp_key)
        work.moved[(_ENTITY_LOCATION, op.temp_key)] = index

    def _create_object(self, work: _Work, op: CreateGardenObjectOp, index: int, site_key: str, user_key: str) -> None:
        if self._temp_key_error(work, op.temp_key, index):
            return
        data = op.data
        props = dict(data.props)
        # The drawn circle is the crown (§9.5): a tree needs no radius twice.
        if (
            data.object_type.value == "tree"
            and "crown_radius_m" not in props
            and isinstance(data.geometry, CircleGeometry)
        ):
            props["crown_radius_m"] = data.geometry.radius_m
        try:
            garden_object = GardenObject(
                site_key=site_key,
                parent_location_key=data.parent_location_key,
                object_type=data.object_type,
                label=data.label,
                geometry=data.geometry,
                props=props,
                off_site=data.off_site,
                locked=data.locked,
                z_order=data.z_order,
                notes=data.notes,
                created_by=user_key,
            )
        except PydanticValidationError as exc:
            work.findings.extend(_findings_of(exc, index))
            return
        work.objects[op.temp_key] = garden_object
        work.temp_objects.append(op.temp_key)
        work.moved[(_ENTITY_OBJECT, op.temp_key)] = index

    def _locked(self, work: _Work, entity: str, key: str, index: int) -> bool:
        """``locked`` guards structure (GP-FR-032): moving or deleting a locked object is refused."""
        target = work.locations.get(key) if entity == _ENTITY_LOCATION else work.objects.get(key)
        if target is not None and target.locked:
            work.findings.append((index, "key", ERROR_OBJECT_LOCKED, {"key": key}))
            return True
        return False

    def _update_geometry(self, work: _Work, op: UpdateGeometryOp, index: int) -> None:
        if not work.known(op.entity, op.key):
            work.findings.append((index, "key", ERROR_REFERENCE_NOT_FOUND, {}))
            return
        if self._locked(work, op.entity, op.key, index):
            return
        try:
            if op.entity == _ENTITY_LOCATION:
                current = work.locations[op.key]
                work.locations[op.key] = Location(**{**_dump(current, by_alias=True), "geometry": op.geometry})
            else:
                garden_object = work.objects[op.key]
                work.objects[op.key] = GardenObject(**{**_dump(garden_object, by_alias=True), "geometry": op.geometry})
        except PydanticValidationError as exc:
            work.findings.extend(_findings_of(exc, index))
            return
        work.moved[(op.entity, op.key)] = index

    def _update_fields(self, work: _Work, op: UpdateFieldsOp, index: int) -> None:
        if not work.known(op.entity, op.key):
            work.findings.append((index, "key", ERROR_REFERENCE_NOT_FOUND, {}))
            return
        try:
            if op.entity == _ENTITY_LOCATION:
                fields = LocationFieldsPatch(**op.fields)
                patch = _dump(fields, exclude_unset=True)
                current = work.locations[op.key]
                # An empty sun-profile patch changes nothing: no default ``SiteConditions``, no ``manual`` stamp.
                patch.pop("site_conditions", None)
                if fields.site_conditions is not None and fields.site_conditions.sun_profile.model_fields_set:
                    patch["site_conditions"] = _merged_sun_profile(current, fields.site_conditions)
                updated = Location(**{**_dump(current, by_alias=True), **patch})
                if "name" in patch:
                    parent = work.locations.get(updated.parent_location_key) if updated.parent_location_key else None
                    place_in_tree(updated, parent)
                work.locations[op.key] = updated
            else:
                patch = _dump(GardenObjectFieldsPatch(**op.fields), exclude_unset=True)
                garden_object = work.objects[op.key]
                merged = {
                    **_dump(garden_object, by_alias=True),
                    **{k: v for k, v in patch.items() if v is not None or k == "notes"},
                }
                if "props" in patch and patch["props"] is not None:
                    merged["props"] = {**patch["props"], "object_type": garden_object.object_type}
                work.objects[op.key] = GardenObject(**merged)
                if "off_site" in patch:
                    # ``off_site`` takes an object in or out of V-03: switching it off is a placement to check.
                    work.moved[(op.entity, op.key)] = index
        except PydanticValidationError as exc:
            work.findings.extend(_findings_of(exc, index))

    def _set_attr(self, work: _Work, entity: str, key: str, name: str, value: Any) -> None:
        target = work.locations.get(key) if entity == _ENTITY_LOCATION else work.objects.get(key)
        if target is not None:
            setattr(target, name, value)

    def _descendants(self, work: _Work, root: str) -> list[str]:
        """Location keys below *root* in the working copy (the root excluded), breadth first."""
        children: dict[str, list[str]] = {}
        for key, location in work.locations.items():
            if location.parent_location_key:
                children.setdefault(location.parent_location_key, []).append(key)
        found: list[str] = []
        queue = list(children.get(root, []))
        while queue:
            key = queue.pop(0)
            if key in found:
                continue
            found.append(key)
            queue.extend(children.get(key, []))
        return found

    def _delete(self, work: _Work, op: DeleteOp, index: int) -> None:
        if not work.known(op.entity, op.key):
            work.findings.append((index, "key", ERROR_REFERENCE_NOT_FOUND, {}))
            return
        if self._locked(work, op.entity, op.key, index):
            return
        if op.entity == _ENTITY_OBJECT:
            self._remove_object(work, op.key, index, cascade=False)
            return
        subtree = [op.key, *self._descendants(work, op.key)]
        inside = [key for key, garden_object in work.objects.items() if garden_object.parent_location_key in subtree]
        locked = [(_ENTITY_LOCATION, key) for key in subtree if work.locations[key].locked] + [
            (_ENTITY_OBJECT, key) for key in inside if work.objects[key].locked
        ]
        if locked:
            # A lock guards structure (GP-FR-032): a locked bed inside an unlocked area is not deleted with it.
            work.findings.extend((index, "key", ERROR_OBJECT_LOCKED, {"key": key}) for _, key in locked)
            return
        for key in subtree:
            self._remove_location(work, key, index, cascade=key != op.key)
        for key in inside:
            self._remove_object(work, key, index, cascade=True)

    def _remove_location(self, work: _Work, key: str, index: int, *, cascade: bool) -> None:
        location = work.locations.pop(key, None)
        if location is None:
            return
        work.moved.pop((_ENTITY_LOCATION, key), None)
        if key in work.temp_locations:
            work.temp_locations.remove(key)  # created and deleted in one batch: net nothing
        else:
            work.deleted_locations[key] = (index, _summary(location.name, key), cascade)

    def _remove_object(self, work: _Work, key: str, index: int, *, cascade: bool) -> None:
        garden_object = work.objects.pop(key, None)
        if garden_object is None:
            return
        work.moved.pop((_ENTITY_OBJECT, key), None)
        if key in work.temp_objects:
            work.temp_objects.remove(key)
        else:
            work.deleted_objects[key] = (index, _summary(garden_object.label, garden_object.object_type.value), cascade)

    def _set_boundary(self, work: _Work, op: SetBoundaryOp, index: int) -> None:
        try:
            plan = SitePlan(boundary=op.boundary, north_angle_deg=op.north_angle_deg or 0.0)
        except PydanticValidationError as exc:
            work.findings.extend(_findings_of(exc, index))
            return
        for code in validate_geometry(op.boundary):
            work.findings.append((index, "boundary", code, {}))
        if plan.boundary is not None:
            work.boundary = plan.boundary
        work.boundary_op = index
        work.plan_changes = op

    # ── (5) geometry rules on the final state ─────────────────────────────────

    def _validate_geometry(self, work: _Work) -> None:
        """V-02, V-03, V-05 and V-19 on the entities this batch touched, against the state it leaves."""
        touched: dict[tuple[str, str], int] = dict(work.moved)
        # A moved or resized location drags its descendants: containment must hold for them again.
        for (entity, key), index in list(work.moved.items()):
            if entity != _ENTITY_LOCATION:
                continue
            below = self._descendants(work, key)
            for child in below:
                touched.setdefault((_ENTITY_LOCATION, child), index)
            inside = {key, *below}
            for object_key, garden_object in work.objects.items():
                if garden_object.parent_location_key in inside:
                    touched.setdefault((_ENTITY_OBJECT, object_key), index)
        if work.boundary_op is not None and work.boundary is not None:
            self._check_boundary(work, touched)
        if not touched:
            return

        flags = self._plan.bed_type_flags(
            sorted({loc.location_type_key for loc in work.locations.values() if loc.location_type_key})
        )
        entities = {
            key: PlanEntity(
                entity=_ENTITY_LOCATION,
                key=key,
                geometry=loc.geometry,
                parent_location_key=loc.parent_location_key,
                is_bed=flags.get(loc.location_type_key, False),
            )
            for key, loc in work.locations.items()
        }
        siblings: dict[str | None, list[PlanEntity]] = {}
        for candidate in entities.values():
            if candidate.geometry is not None and candidate.is_bed:
                siblings.setdefault(candidate.parent_location_key, []).append(candidate)

        for (kind, key), index in sorted(touched.items(), key=lambda item: item[1]):
            if kind == _ENTITY_LOCATION:
                subject = entities.get(key)
            else:
                stored_object = work.objects.get(key)
                subject = (
                    PlanEntity(
                        entity=_ENTITY_OBJECT,
                        key=key,
                        geometry=stored_object.geometry,
                        parent_location_key=stored_object.parent_location_key,
                        off_site=stored_object.off_site,
                    )
                    if stored_object is not None
                    else None
                )
            if subject is None:
                continue
            for field_name, code, entity_key in check_entity(
                subject,
                locations=entities,
                siblings=siblings.get(subject.parent_location_key, []),
                boundary=work.boundary,
            ):
                work.findings.append((index, field_name, code, {"key": entity_key}))

    def _check_boundary(self, work: _Work, touched: dict[tuple[str, str], int]) -> None:
        """V-19: a new boundary may not leave an entity it bounds outside, unless this batch itself placed it."""
        assert work.boundary is not None  # noqa: S101 — the caller checked
        all_locations = {
            key: PlanEntity(_ENTITY_LOCATION, key, loc.geometry, loc.parent_location_key)
            for key, loc in work.locations.items()
        }
        candidates = [entity for key, entity in all_locations.items() if (_ENTITY_LOCATION, key) not in touched] + [
            PlanEntity(_ENTITY_OBJECT, key, obj.geometry, obj.parent_location_key, off_site=obj.off_site)
            for key, obj in work.objects.items()
            if (_ENTITY_OBJECT, key) not in touched
        ]
        outside = boundary_violations(candidates, work.boundary, locations=all_locations)
        if outside:
            work.findings.append((work.boundary_op, "boundary", ERROR_BOUNDARY_SHRINKS, {"keys": outside}))

    def _check_slots_of_reshaped_beds(self, work: _Work, *, site_key: str, tenant_key: str) -> None:
        """V-04: a bed whose *shape* changed must still hold the slots placed in its frame.

        Moving or turning a bed leaves its frame, and so every slot, as it is (§9.2, GP-ACC-005): nothing to
        check. A resized bed or a bed that becomes another shape can leave a slot outside it, and a batch
        that stored that would hand the planting layer positions off the bed.
        """
        reshaped: dict[str, int] = {}
        for (entity, key), index in work.moved.items():
            stored = work.stored_locations.get(key)
            current = work.locations.get(key)
            if entity != _ENTITY_LOCATION or stored is None or current is None:
                continue
            if current.geometry is None:
                continue
            # A bed that is placed for the first time has no frame yet, so slots it already holds are checked too.
            if stored.geometry is None or to_local_shape(stored.geometry) != to_local_shape(current.geometry):
                reshaped[key] = index
        if not reshaped:
            return
        slots = self._plan.load_active_slots(site_key, sorted(reshaped), tenant_key=tenant_key)
        by_bed: dict[str, list[tuple[str, Geometry]]] = {}
        for slot in slots:
            if slot.key and slot.geometry is not None:
                by_bed.setdefault(slot.location_key, []).append((slot.key, slot.geometry))
        for bed_key, placed in by_bed.items():
            bed = work.locations[bed_key].geometry
            if bed is None:
                continue
            for slot_key in slots_outside_bed(bed, placed):
                work.findings.append((reshaped[bed_key], "geometry", ERROR_SLOT_OUTSIDE_BED, {"key": slot_key}))

    # ── the plan import (GP-API-005) ──────────────────────────────────────────

    def check_imported_structure(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        locations: dict[str, Location],
        objects: dict[str, GardenObject],
        imported_locations: list[str],
        imported_objects: list[str],
        boundary: Geometry | None,
        boundary_changed: bool,
    ) -> list[_Finding]:
        """V-01…V-05, V-19 on the plan an import would leave: the same rules, the same engine as a batch.

        ``locations`` and ``objects`` are the whole resulting structure (kept documents and imported ones, the
        latter under their temporary keys); ``imported_*`` name the entities to check, in file order. The finding's
        op index is the position in ``imported_locations`` followed by ``imported_objects`` (``None`` for the
        boundary), which the import maps back to a path in the file.
        """
        work = _Work(
            locations=locations,
            objects=objects,
            boundary=boundary,
            stored_locations={},
            stored_objects={},
        )
        for index, key in enumerate(imported_locations):
            work.moved[(_ENTITY_LOCATION, key)] = index
        for index, key in enumerate(imported_objects, start=len(imported_locations)):
            work.moved[(_ENTITY_OBJECT, key)] = index
        if boundary_changed:
            work.boundary_op = -1
        self._validate_geometry(work)
        return [(None if index == -1 else index, name, code, extra) for index, name, code, extra in work.findings]

    # ── the write set and the answer ──────────────────────────────────────────

    def _build_write(
        self,
        work: _Work,
        *,
        site: Site,
        tenant_key: str,
        editor_key: str,
        expected_revision: int,
        basis_revision: int,
        remaining: float,
    ) -> PlanBatchWrite:
        site_key = site.key or ""
        inserts = sorted(
            work.temp_locations, key=lambda key: (work.locations[key].depth, work.temp_locations.index(key))
        )
        location_updates = [
            (key, changed)
            for key, location in work.locations.items()
            if key in work.stored_locations
            and (changed := _changed_fields(location, work.stored_locations[key], _LOCATION_COLUMNS))
        ]
        sun_profiles = [
            (key, sun_profile)
            for key, location in work.locations.items()
            if key in work.stored_locations
            and (sun_profile := _sun_profile_of(location)) is not None
            and sun_profile != _sun_profile_of(work.stored_locations[key])
        ]
        object_updates = [
            (key, changed)
            for key, garden_object in work.objects.items()
            if key in work.stored_objects
            and (changed := _changed_fields(garden_object, work.stored_objects[key], _OBJECT_COLUMNS))
        ]
        audit: list[dict[str, str]] = []
        for key, (_, summary, cascade) in sorted(work.deleted_locations.items()):
            audit.append(
                {
                    "op": "delete_cascade" if cascade else "delete",
                    "entity": _ENTITY_LOCATION,
                    "key": key,
                    "summary": summary,
                }
            )
        for key, (_, summary, cascade) in sorted(work.deleted_objects.items()):
            audit.append(
                {
                    "op": "delete_cascade" if cascade else "delete",
                    "entity": _ENTITY_OBJECT,
                    "key": key,
                    "summary": summary,
                }
            )
        changes = work.plan_changes
        if changes is not None:
            audit.append({"op": "set_boundary", "entity": "site", "key": site_key, "summary": changes.boundary.kind})
        return PlanBatchWrite(
            site_key=site_key,
            tenant_key=tenant_key,
            editor_key=editor_key,
            expected_revision=expected_revision,
            basis_revision=basis_revision,
            location_inserts=[(key, work.locations[key]) for key in inserts],
            location_updates=location_updates,
            location_sun_profiles=sun_profiles,
            location_deletes=sorted(work.deleted_locations),
            object_inserts=[(key, work.objects[key]) for key in work.temp_objects],
            object_updates=object_updates,
            object_deletes=sorted(work.deleted_objects),
            boundary=changes.boundary if changes is not None else None,
            north_angle_deg=changes.north_angle_deg if changes is not None else None,
            default_grid_m=changes.default_grid_m if changes is not None else None,
            adjacency_factor=changes.adjacency_factor if changes is not None else None,
            total_area_m2=area_m2(changes.boundary) if changes is not None else None,
            audit=audit,
            time_budget_seconds=max(remaining, 0.5),
        )

    @staticmethod
    def _result(work: _Work, write: PlanBatchWrite, revision: int, key_map: dict[str, str]) -> PlanBatchResult:
        derived: dict[str, DerivedGeometry] = {}
        for entity, key in work.moved:
            model = work.locations.get(key) if entity == _ENTITY_LOCATION else work.objects.get(key)
            if model is None:
                continue
            real = key_map.get(key, key)
            derived[real] = DerivedGeometry(
                area_m2=model.area_m2 if isinstance(model, Location) else area_m2(model.geometry),
                bbox=model.bbox,
            )
        return PlanBatchResult(
            plan_revision=revision,
            key_map=key_map,
            updated=sorted(
                {key for key, _ in [*write.location_updates, *write.location_sun_profiles, *write.object_updates]}
            ),
            deleted=sorted([*write.location_deletes, *write.object_deletes]),
            derived=derived,
        )


def _slot_in_plan_frame(geometry: Geometry, bed: Geometry) -> dict[str, Any]:
    """A slot's geometry in the plan frame: ``p_plan = anchor + R(rotation) · p_bed`` (§9.2).

    Compact on purpose (2 000 plants in one response, GP-NFR-002): a point is ``{kind, origin}``,
    a row or zone ``{kind, points[, width_m]}``. Rounded to millimetres.
    """

    def plan_point(point: tuple[float, float]) -> list[float]:
        x, y = transform_bed_to_plan(point, bed)
        return [round_length(x), round_length(y)]

    if isinstance(geometry, PointGeometry):
        return {"kind": "point", "origin": plan_point(geometry.origin)}
    if isinstance(geometry, PolylineGeometry):
        return {"kind": "polyline", "points": [plan_point(p) for p in geometry.points], "width_m": geometry.width_m}
    if isinstance(geometry, PolygonGeometry):
        return {"kind": "polygon", "points": [plan_point(p) for p in geometry.points]}
    # A slot is a point, a row (polyline) or a zone (polygon) — ``Slot`` refuses every other shape (§20.5).
    raise ValueError(f"A slot cannot have a {geometry.kind} geometry.")
