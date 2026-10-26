"""The single resources of the garden plan: beds, garden objects and slots (REQ-053 WP 1.9, #2328).

GP-API-010…015 and GP-API-018 are the per-resource counterpart of the plan batch (GP-API-003). They
share its rules instead of copying them:

* **Structure goes through the batch.** A geometry change of a location, every garden-object write and the
  delete of a location run as a one-operation batch of :class:`GardenPlanService` — containment (V-03),
  overlap (V-05), the lock (GP-FR-032), the active-plant refusal (V-09), the audit row (SR-011) and the
  ``plan_revision`` bump are one implementation, not two. The route has no client revision to send, so the
  batch expects the revision it validated against: a writer that lost the race still gets 409.
* **Everything else is outside the revision** (GP-NFR-007): notes, soil, sun, the irrigation zone, slots.
  A bed-status change is the exception — it changes what the plan shows (``retired`` hides the bed) and
  writes a care event in the same transaction, so it travels as a write set of its own.

**Ownership is resolved here, never in the router** (T-01…T-04, #2107). Every public method takes
``*, tenant_key: str`` without a default and resolves the site through
:mod:`app.domain.services.location_ownership` before it reads or computes anything else; no key of a
request body is trusted for the site. A foreign and an absent resource answer identically (404).

**Role rules the router gate cannot express** (§21.8): the gate lets a grower in; this service refuses
``retired`` and the reactivation of a retired bed unless the caller is a lead, and the delete of anything
unless the caller is a lead.

**Logs carry no user text** (GP-NFR-060): keys, counts, codes.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import BedStatus, FrostRisk, TenantRole
from app.common.exceptions import ForbiddenError, PlanError, PlanValidationError
from app.common.types import GardenObjectKey, LocationKey, SiteKey, SlotKey
from app.domain.calculators.planting_layout_calculator import EntryLayout, LayoutResult, compute_layout
from app.domain.engines.frost_exposure_resolver import frost_exposed_from_risk
from app.domain.engines.garden_plan_engine import (
    ERROR_INVALID_BED_TRANSITION,
    ERROR_REFERENCE_NOT_FOUND,
    ERROR_SLOT_OUTSIDE_BED,
    ERROR_SLOT_OVERLAP,
    bed_status_transition_allowed,
    overlapping_zones,
    slots_outside_bed,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.garden_object_repository import IGardenObjectRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.care_event import CATEGORY_BED_STATUS_CHANGE, CareEvent
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    MAX_SLOTS_PER_BATCH,
    MAX_SLOTS_PER_SITE,
    BedCounters,
    BedSummaryView,
    CreateGardenObjectData,
    GardenObjectPatch,
    LocationPatch,
    PlanBatchWrite,
    SiteConditionsPatch,
    SlotBatchItem,
    SlotBatchRequest,
    SlotBatchResult,
    SlotBatchWrite,
    SlotPatch,
)
from app.domain.models.geometry import Geometry
from app.domain.models.site import Location, Site, SiteConditions, Slot
from app.domain.services.adjacency_service import AdjacencyDispatch, request_adjacency_recompute
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_ownership import (
    require_owned_site,
    resolve_owned_location,
    resolve_owned_slot,
)
from app.domain.services.site_service import place_in_tree

logger = structlog.get_logger()

#: The temp key a one-object create uses; the answer's ``key_map`` maps it to the stored key.
_NEW = "new"

_ENTITY_LOCATION = "location"
_ENTITY_OBJECT = "garden_object"

#: What ``PATCH /locations`` writes without the plan revision (GP-NFR-007): the document's own columns.
#: ``geometry``, ``locked`` and ``z_order`` are structure — they go through the plan batch and raise the revision,
#: as ``set_locked`` / ``set_z_order`` do there, so a client holding the plan sees the change as one.
_PATCH_COLUMNS: tuple[str, ...] = (
    "name",
    "path",
    "depth",
    "description",
    "notes",
    "height_m",
    "sun_exposure",
    "soil_profile",
    "site_conditions",
    "irrigation_zone_key",
    "frost_exposed",
)


#: What ``PATCH /slots/{key}`` writes (GP-API-014).
_SLOT_PATCH_COLUMNS: tuple[str, ...] = ("slot_role", "geometry", "capacity_plants", "geometry_source")


#: The two parts of ``SiteConditions`` that are objects of their own (merged key by key on a PATCH).
_NESTED_SITE_PARTS: frozenset[str] = frozenset({"sun_profile", "microclimate"})


def _sent_fields(model: Any) -> dict[str, Any]:
    """The fields a request body set explicitly (``model_fields_set``), by name."""
    return {name: getattr(model, name) for name in model.model_fields_set}


def _dump(model: Any, **options: Any) -> dict[str, Any]:
    """``model_dump`` through an untyped receiver (see the write-route sweep's blind-spot ceiling)."""
    return dict(model.model_dump(**options))


def _not_found(field: str) -> PlanValidationError:
    """422 ``reference.not_found`` — one text for a missing and for another tenant's key (GP-NFR-058)."""
    return PlanValidationError([(None, field, ERROR_REFERENCE_NOT_FOUND, {})])


class GardenResourceService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        object_repo: IGardenObjectRepository,
        plan_service: GardenPlanService,
        dispatch_adjacency: AdjacencyDispatch | None = None,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._objects = object_repo
        self._plan_service = plan_service
        self._dispatch_adjacency = dispatch_adjacency

    # ── Anchor and roles ──────────────────────────────────────────────────────

    def _owned_site(self, site_key: SiteKey, *, tenant_key: str) -> Site:
        return require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    def _owned_location(self, key: LocationKey, *, tenant_key: str) -> Location:
        return resolve_owned_location(self._sites, key, tenant_key)

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_lead(role: TenantRole) -> None:
        if not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Requires lead role.")

    @staticmethod
    def _revision_of(site: Site) -> int:
        return site.plan.plan_revision if site.plan is not None else 0

    # ── GP-API-011: the bed list ──────────────────────────────────────────────

    def list_beds(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        is_bed: bool | None,
        bed_status: BedStatus | None,
    ) -> list[tuple[Location, BedCounters | None]]:
        """A site's locations, filtered; with counters when a bed filter is given (GP-API-011).

        ``is_bed`` is the ``is_bed`` flag of the location's type. Counters cost three queries over the
        listed keys, so a plain listing (neither filter) stays as cheap as before and carries none.
        """
        self._owned_site(site_key, tenant_key=tenant_key)
        locations = self._sites.get_locations_by_site(site_key)
        with_counters = is_bed is not None or bed_status is not None
        if bed_status is not None and is_bed is None:
            is_bed = True  # a status is a bed's property: ``bed_status=`` alone lists beds, not every location
        if is_bed is not None:
            flags = self._plan.bed_type_flags(
                sorted({loc.location_type_key for loc in locations if loc.location_type_key})
            )
            locations = [loc for loc in locations if flags.get(loc.location_type_key, False) is is_bed]
        if bed_status is not None:
            locations = [loc for loc in locations if loc.bed_status is bed_status]
        counters: dict[str, BedCounters] = {}
        if with_counters and locations:
            counters = self._plan.load_bed_counters([loc.key for loc in locations if loc.key], tenant_key=tenant_key)
        return [(loc, (counters.get(loc.key or "", BedCounters()) if with_counters else None)) for loc in locations]

    # ── GP-API-012: the bed summary ───────────────────────────────────────────

    def get_summary(self, key: LocationKey, *, tenant_key: str) -> BedSummaryView:
        location = self._owned_location(key, tenant_key=tenant_key)
        counters = self._plan.load_bed_counters([key], tenant_key=tenant_key).get(key, BedCounters())
        flags = self._plan.bed_type_flags([location.location_type_key]) if location.location_type_key else {}
        return BedSummaryView(
            location=location,
            counters=counters,
            season_state="planted" if counters.active_plant_count else "empty",
            is_bed=flags.get(location.location_type_key, False),
        )

    # ── GP-API-010: PATCH /locations/{key} ────────────────────────────────────

    def patch_location(
        self,
        key: LocationKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        patch: LocationPatch,
    ) -> tuple[Location, int]:
        """Change the fields present; returns the stored location and the site's ``plan_revision``.

        Order: anchor (404) → role (403) → references (422) → status rules → structure (geometry, lock,
        drawing order) through one plan batch, which can still refuse, so it runs first → status → the
        remaining columns. Everything that can be refused is refused before the first write; what runs after
        the structure batch is a status change (refused up front when combined with a geometry, see below) or a
        plain column update of a document just read, which fails only if the document vanished meanwhile.
        A status change and a geometry change are two structural writes, each with its own revision step, and
        cannot be one transaction here — they are refused together (422 ``patch.status_with_geometry``).
        """
        location = self._owned_location(key, tenant_key=tenant_key)
        self._require_editor(role)
        target_status = self._status_target(location, patch, role)
        self._resolve_references(location, patch, tenant_key=tenant_key)

        fields = self._field_changes(location, patch)
        operations = self._structure_operations(location, patch)
        if target_status is not None:
            if any(op["op"] == "update_geometry" for op in operations):
                raise PlanError(
                    "patch.status_with_geometry",
                    "A status change and a geometry change are separate structural writes; send one after the other.",
                    status_code=422,
                    field="bed_status",
                )
            self._check_status_change(location, target_status, patch.status_reason, tenant_key=tenant_key)

        if operations:
            self._plan_service.apply_batch(
                location.site_key,
                tenant_key=tenant_key,
                user_key=user_key,
                role=role,
                expected_revision=None,
                operations=operations,
                body_bytes=0,
            )
        if target_status is not None:
            self._write_status(location, target_status, patch.status_reason, tenant_key=tenant_key, user_key=user_key)
        if fields:
            self._plan.update_location_fields(key, fields)

        stored = self._owned_location(key, tenant_key=tenant_key)
        site = self._owned_site(stored.site_key, tenant_key=tenant_key)
        return stored, self._revision_of(site)

    @staticmethod
    def _structure_operations(location: Location, patch: LocationPatch) -> list[dict[str, Any]]:
        """The batch operations for the structural fields that differ from the stored ones.

        A lock that is lifted comes first and one that is set comes last, so ``{locked: false, geometry}``
        moves a locked bed and ``{locked: true, geometry}`` moves it and then locks it.
        """
        provided = patch.model_fields_set
        key = location.key or ""
        lift = patch.locked is False and "locked" in provided and location.locked
        lock = patch.locked is True and "locked" in provided and not location.locked
        operations: list[dict[str, Any]] = []
        if lift:
            operations.append({"op": "set_locked", "entity": _ENTITY_LOCATION, "key": key, "locked": False})
        if "geometry" in provided and patch.geometry != location.geometry:
            operations.append(
                {
                    "op": "update_geometry",
                    "entity": _ENTITY_LOCATION,
                    "key": key,
                    "geometry": _dump(patch.geometry, mode="json"),
                }
            )
        if "z_order" in provided and patch.z_order != location.z_order:
            operations.append({"op": "set_z_order", "entity": _ENTITY_LOCATION, "key": key, "z_order": patch.z_order})
        if lock:
            operations.append({"op": "set_locked", "entity": _ENTITY_LOCATION, "key": key, "locked": True})
        return operations

    def _status_target(self, location: Location, patch: LocationPatch, role: TenantRole) -> BedStatus | None:
        """The status the PATCH asks for, or ``None`` when it asks for none or for the one the bed has."""
        if "bed_status" not in patch.model_fields_set or patch.bed_status is None:
            return None
        if patch.bed_status is location.bed_status:
            return None
        self._require_status_role(location.bed_status, patch.bed_status, role)
        return patch.bed_status

    @staticmethod
    def _require_status_role(current: BedStatus, target: BedStatus, role: TenantRole) -> None:
        """§21.8: ``retired`` and the way back are the lead's (§7.4 "Reaktivierung durch Leitung")."""
        if (target is BedStatus.RETIRED or current is BedStatus.RETIRED) and not MembershipEngine.can_delete_resource(
            role
        ):
            raise ForbiddenError("Retiring or reactivating a bed requires the lead role.")

    def _resolve_references(self, location: Location, patch: LocationPatch, *, tenant_key: str) -> None:
        """GP-NFR-058: the zone must be one of this site (L1 of #2326), the substrate a catalogue or own one.

        The zone's ``zone_covers`` edge follows the field in the same transaction as the column write
        (``update_location_fields``, WP 7.1): the bed leaves the zone that held it, so it is in at most one.
        """
        if patch.irrigation_zone_key is not None:
            zone_site = self._plan.irrigation_zone_site_key(patch.irrigation_zone_key, tenant_key=tenant_key)
            if zone_site is None or zone_site != location.site_key:
                raise _not_found("irrigation_zone_key")
        substrate = patch.soil_profile.substrate_key if patch.soil_profile is not None else None
        if substrate and not self._plan.substrate_visible(substrate, tenant_key=tenant_key):
            raise _not_found("soil_profile.substrate_key")

    @staticmethod
    def _merged_site_conditions(stored: SiteConditions | None, sent: SiteConditionsPatch) -> SiteConditions:
        """The stored value with exactly the keys of ``sent`` laid over it (WP 3.9).

        A PATCH that sends ``{"wind_exposure": "exposed"}`` changes the wind and nothing else: a replace
        would reset the sun window, the risk and the slope to their defaults. The two nested parts are
        merged by their own sent keys; a list (``access_sides``, ``flags``) is replaced whole.
        """
        merged = _dump(stored if stored is not None else SiteConditions())
        for name in sent.model_fields_set:
            value = getattr(sent, name)
            if name in _NESTED_SITE_PARTS:
                merged[name] = {**merged[name], **_sent_fields(value)}
            else:
                merged[name] = value
        return SiteConditions(**merged)

    @staticmethod
    def _mirror_frost_risk(location: Location, provided: dict[str, Any]) -> None:
        """A changed ``microclimate.frost_risk`` moves the legacy ``frost_exposed`` with it (WP 3.9).

        Only a *change* counts: a patch that sends other site conditions with an untouched risk must not
        reset an override somebody set on the old field. Clearing the whole value (``site_conditions:
        null``) is a change to ``unknown`` when a risk was stored. ``normal`` and ``unknown`` mean "no
        override" and therefore also clear the boolean: the new field is the one that was edited, and the
        site type decides again.
        """
        if "site_conditions" not in provided:
            return
        sent = provided["site_conditions"]
        sent_risk = sent.microclimate.frost_risk if sent is not None else FrostRisk.UNKNOWN
        stored = location.site_conditions.microclimate.frost_risk if location.site_conditions else FrostRisk.UNKNOWN
        if sent_risk is not stored:
            provided["frost_exposed"] = frost_exposed_from_risk(sent_risk)

    def _field_changes(self, location: Location, patch: LocationPatch) -> dict[str, Any]:
        """The document columns the PATCH changes, JSON-shaped; ``None`` removes a stored value."""
        provided = {name: getattr(patch, name) for name in patch.model_fields_set if name in set(_PATCH_COLUMNS)}
        if not provided:
            return {}
        if patch.site_conditions is not None:
            provided["site_conditions"] = self._merged_site_conditions(location.site_conditions, patch.site_conditions)
        self._mirror_frost_risk(location, provided)
        try:
            updated = Location.model_validate({**_dump(location, by_alias=True), **provided})
        except PydanticValidationError as exc:
            raise PlanValidationError(
                [
                    (None, ".".join(str(part) for part in e["loc"]) or "request", "validation.invalid", {})
                    for e in exc.errors()
                ]
            ) from exc
        if "name" in provided:
            parent = (
                self._sites.get_location_by_key(updated.parent_location_key) if updated.parent_location_key else None
            )
            place_in_tree(updated, parent)
        now = _dump(updated, by_alias=True, mode="json")
        before = _dump(location, by_alias=True, mode="json")
        return {column: now.get(column) for column in _PATCH_COLUMNS if now.get(column) != before.get(column)}

    # ── GP-API-018: the status transition ─────────────────────────────────────

    def change_bed_status(
        self,
        key: LocationKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        bed_status: BedStatus,
        reason: str | None,
    ) -> tuple[Location, int]:
        """``planned → active → retired → active`` and ``planned → retired`` (V-10), with a care event (GP-FR-046)."""
        location = self._owned_location(key, tenant_key=tenant_key)
        self._require_editor(role)
        self._require_status_role(location.bed_status, bed_status, role)
        self._check_status_change(location, bed_status, reason, tenant_key=tenant_key)
        self._write_status(location, bed_status, reason, tenant_key=tenant_key, user_key=user_key)
        stored = self._owned_location(key, tenant_key=tenant_key)
        site = self._owned_site(stored.site_key, tenant_key=tenant_key)
        return stored, self._revision_of(site)

    def _check_status_change(
        self, location: Location, target: BedStatus, reason: str | None, *, tenant_key: str
    ) -> None:
        key = location.key or ""
        flags = self._plan.bed_type_flags([location.location_type_key]) if location.location_type_key else {}
        if not flags.get(location.location_type_key, False):
            raise PlanError(
                "bed_status.not_a_bed",
                "Only a location of a bed type has a bed status.",
                status_code=422,
                field="bed_status",
            )
        if not bed_status_transition_allowed(location.bed_status, target):
            raise PlanError(
                ERROR_INVALID_BED_TRANSITION,
                "This status change is not allowed.",
                status_code=422,
                field="bed_status",
                current=location.bed_status.value,
                requested=target.value,
            )
        if target is BedStatus.RETIRED:
            if not reason or not reason.strip():
                raise PlanError(
                    "bed_status.reason_required",
                    "Retiring a bed needs a reason.",
                    status_code=422,
                    field="reason",
                )
            count = self._plan.count_active_plants([key], tenant_key=tenant_key)
            if count:
                raise PlanError(
                    "location.has_active_plants",
                    "A location with active plants cannot be deleted or retired.",
                    status_code=409,
                    active_plant_count=count,
                )

    def _write_status(
        self,
        location: Location,
        target: BedStatus,
        reason: str | None,
        *,
        tenant_key: str,
        user_key: str,
    ) -> None:
        """One transaction: the new status, the care event, the revision and — for ``retired`` — the audit row."""
        key = location.key or ""
        site = self._owned_site(location.site_key, tenant_key=tenant_key)
        basis = self._revision_of(site)
        event = CareEvent(
            tenant_key=tenant_key,
            site_key=location.site_key,
            location_key=key,
            category=CATEGORY_BED_STATUS_CHANGE,
            summary=f"{location.bed_status.value} -> {target.value}",
            performed_at=datetime.now(UTC),
            performed_by_user_key=user_key,
            trigger="manual",
            reason=reason.strip() if reason else None,
            created_by=user_key,
        )
        audit_op = (
            "retire"
            if target is BedStatus.RETIRED
            else "reactivate"
            if location.bed_status is BedStatus.RETIRED
            else ""
        )
        write = PlanBatchWrite(
            site_key=location.site_key,
            tenant_key=tenant_key,
            editor_key=user_key,
            expected_revision=basis,
            basis_revision=basis,
            location_updates=[(key, {"bed_status": target.value})],
            status_from={key: location.bed_status.value},
            audit=[{"op": audit_op, "entity": _ENTITY_LOCATION, "key": key, "summary": location.name[:200]}]
            if audit_op
            else [],
            care_events=[event],
        )
        outcome = self._plan.apply_plan_batch(write)
        logger.info(
            "garden_resource.bed_status_changed",
            location_key=key,
            status=target.value,
            revision=outcome.plan_revision,
        )

    # ── DELETE /locations/{key} (V-09) ────────────────────────────────────────

    def delete_location(self, key: LocationKey, *, tenant_key: str, user_key: str, role: TenantRole) -> None:
        """Delete the location and what is below it; 409 ``location.has_active_plants`` while a plant stands in it."""
        location = self._owned_location(key, tenant_key=tenant_key)
        self._require_lead(role)
        self._plan_service.apply_batch(
            location.site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            expected_revision=None,
            operations=[{"op": "delete", "entity": _ENTITY_LOCATION, "key": key}],
            body_bytes=0,
        )

    # ── GP-API-013: garden objects ────────────────────────────────────────────

    def list_garden_objects(self, site_key: SiteKey, *, tenant_key: str) -> list[GardenObject]:
        self._owned_site(site_key, tenant_key=tenant_key)
        return self._objects.get_garden_objects_by_site(site_key, tenant_key=tenant_key)

    def get_garden_object(self, key: GardenObjectKey, *, tenant_key: str) -> GardenObject:
        return self._objects.get_garden_object_or_raise(key, tenant_key=tenant_key)

    def create_garden_object(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        data: CreateGardenObjectData,
    ) -> GardenObject:
        """Create an object on the path site (T-01: ``site_key`` is never read from the body)."""
        self._owned_site(site_key, tenant_key=tenant_key)
        self._require_editor(role)
        result = self._plan_service.apply_batch(
            site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            expected_revision=None,
            operations=[{"op": "create_garden_object", "temp_key": _NEW, "data": _dump(data, mode="json")}],
            body_bytes=0,
        )
        return self._objects.get_garden_object_or_raise(result.key_map[_NEW], tenant_key=tenant_key)

    def patch_garden_object(
        self,
        key: GardenObjectKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        patch: GardenObjectPatch,
    ) -> GardenObject:
        stored = self._objects.get_garden_object_or_raise(key, tenant_key=tenant_key)
        self._require_editor(role)
        operations = self._object_operations(key, patch)
        self._plan_service.apply_batch(
            stored.site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            expected_revision=None,
            operations=operations,
            body_bytes=0,
        )
        return self._objects.get_garden_object_or_raise(key, tenant_key=tenant_key)

    @staticmethod
    def _object_operations(key: str, patch: GardenObjectPatch) -> list[dict[str, Any]]:
        """The batch operations of a PATCH. The lock is set first when it is lifted and last when it is set,
        so ``{locked: false, geometry}`` moves the object and ``{locked: true, geometry}`` does too."""
        provided = patch.model_fields_set
        operations: list[dict[str, Any]] = []
        lock = (
            {"op": "set_locked", "entity": _ENTITY_OBJECT, "key": key, "locked": patch.locked}
            if "locked" in provided
            else None
        )
        if lock is not None and patch.locked is False:
            operations.append(lock)
        fields = {name: getattr(patch, name) for name in ("label", "notes", "props", "off_site") if name in provided}
        if fields:
            operations.append({"op": "update_fields", "entity": _ENTITY_OBJECT, "key": key, "fields": fields})
        if "geometry" in provided and patch.geometry is not None:
            operations.append(
                {
                    "op": "update_geometry",
                    "entity": _ENTITY_OBJECT,
                    "key": key,
                    "geometry": _dump(patch.geometry, mode="json"),
                }
            )
        if "z_order" in provided:
            operations.append({"op": "set_z_order", "entity": _ENTITY_OBJECT, "key": key, "z_order": patch.z_order})
        if lock is not None and patch.locked is not False:
            operations.append(lock)
        return operations

    def delete_garden_object(self, key: GardenObjectKey, *, tenant_key: str, user_key: str, role: TenantRole) -> None:
        stored = self._objects.get_garden_object_or_raise(key, tenant_key=tenant_key)
        self._require_lead(role)
        self._plan_service.apply_batch(
            stored.site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            expected_revision=None,
            operations=[{"op": "delete", "entity": _ENTITY_OBJECT, "key": key}],
            body_bytes=0,
        )

    # ── GP-API-014: PATCH /slots/{key} ────────────────────────────────────────

    def get_owned_slot(self, key: SlotKey, *, tenant_key: str) -> Slot:
        """The slot ``key`` if its bed belongs to the tenant, else 404 - what a caller reads before it patches."""
        return resolve_owned_slot(self._sites, key, tenant_key)[0]

    def patch_slot(self, key: SlotKey, *, tenant_key: str, role: TenantRole, patch: SlotPatch) -> Slot:
        """Correct a slot's geometry, role or capacity — outside the plan revision (GP-NFR-007).

        V-04 (inside the bed) and V-06 (zones may not overlap, archived slots excepted) are checked on the
        slot as it will be. A slot that is occupied can be corrected: moving a plant's place is the point of
        GP-FR-068.
        """
        slot, location = resolve_owned_slot(self._sites, key, tenant_key)
        self._require_editor(role)
        provided = patch.model_fields_set
        role_after = patch.slot_role if "slot_role" in provided and patch.slot_role is not None else slot.slot_role
        geometry_after = patch.geometry if "geometry" in provided and patch.geometry is not None else slot.geometry
        try:
            updated = Slot.model_validate(
                {
                    **_dump(slot, by_alias=True),
                    "slot_role": role_after,
                    "geometry": geometry_after,
                    "capacity_plants": patch.capacity_plants
                    if "capacity_plants" in provided and patch.capacity_plants is not None
                    else slot.capacity_plants,
                    "geometry_source": "editor" if "geometry" in provided else slot.geometry_source,
                }
            )
        except PydanticValidationError as exc:
            raise PlanValidationError(
                [
                    (None, ".".join(str(part) for part in e["loc"]) or "request", "geometry.invalid", {})
                    for e in exc.errors()
                ]
            ) from exc

        if updated.geometry is not None and ("geometry" in provided or "slot_role" in provided):
            self._check_slot_rules(
                location,
                [(key, updated.geometry)],
                others=[
                    (other.key, other.geometry)
                    for other in self._plan.load_active_slots(
                        location.site_key, [location.key or ""], tenant_key=tenant_key
                    )
                    if other.key and other.key != key and other.geometry is not None
                ],
            )
        # Only the columns that changed, the geometry replaced whole: a document merge would keep the keys of
        # the old geometry kind (``origin`` beside ``points``) and make the slot unreadable.
        now, before = _dump(updated, by_alias=True, mode="json"), _dump(slot, by_alias=True, mode="json")
        fields = {name: now.get(name) for name in _SLOT_PATCH_COLUMNS if now.get(name) != before.get(name)}
        if fields:
            self._plan.update_slot_fields(key, fields)
            self._recompute_adjacency(location.key or "")
        return resolve_owned_slot(self._sites, key, tenant_key)[0]

    # ── GP-API-016: POST /locations/{key}/planting-layout/preview ─────────────

    def preview_planting_layout(
        self,
        key: LocationKey,
        *,
        tenant_key: str,
        entry: EntryLayout,
        max_count: int | None,
    ) -> LayoutResult:
        """The layout an entry would get in the bed, without persisting anything (GP-FR-063).

        Pure compute over the bed's geometry: ownership is resolved first, nothing is written, so a
        reader may call it (all roles, §21.8). The pre-estimate of :func:`compute_layout` refuses an
        oversized request (422 ``layout.too_many_positions``) before a single point is generated.
        """
        location = self._owned_location(key, tenant_key=tenant_key)
        if location.geometry is None:
            raise PlanError(
                "layout.bed_without_geometry",
                "The bed has no geometry yet; draw it on the plan before planning a layout.",
                status_code=422,
                field="geometry",
            )
        result = compute_layout(location.geometry, entry, max_count)
        logger.info(
            "garden_resource.layout_previewed",
            location_key=key,
            strategy=entry.layout_strategy.value,
            count=result.count,
            capacity_max=result.capacity_max,
        )
        return result

    # ── GP-API-015: POST /locations/{key}/slots/batch ─────────────────────────

    def replace_slots(
        self,
        key: LocationKey,
        *,
        tenant_key: str,
        role: TenantRole,
        request: SlotBatchRequest,
    ) -> SlotBatchResult:
        """Replace the unoccupied slots of a bed, or append to them — one transaction, outside the revision.

        ``replace_unoccupied`` removes the slots that are not occupied, not reserved by a run and not
        archived (history); occupied and reserved slots stay and take part in the V-04/V-06 checks as
        neighbours. V-20: a ``slot_id`` may appear once per bed — in the request and against what stays.
        """
        location = self._owned_location(key, tenant_key=tenant_key)
        self._require_editor(role)
        items = request.slots
        if len(items) > MAX_SLOTS_PER_BATCH:
            raise PlanError(
                "layout.too_many_positions",
                f"A slot batch holds at most {MAX_SLOTS_PER_BATCH} positions.",
                status_code=422,
                limit=MAX_SLOTS_PER_BATCH,
                current=len(items),
            )
        existing = self._plan.load_active_slots(location.site_key, [key], tenant_key=tenant_key, include_archived=True)
        active = [slot for slot in existing if slot.archived_at is None and slot.key]
        delete_keys: list[str] = []
        if request.mode == "replace_unoccupied":
            reserved = self._plan.reserved_among([slot.key or "" for slot in active], tenant_key=tenant_key)
            delete_keys = [
                slot.key or "" for slot in active if not slot.currently_occupied and (slot.key or "") not in reserved
            ]
        kept = [slot for slot in existing if (slot.key or "") not in set(delete_keys)]

        findings = self._slot_item_findings(location, items, kept)
        if findings:
            raise PlanValidationError(findings[:50])
        site_slots = self._plan.count_active_slots(location.site_key, tenant_key=tenant_key)
        if site_slots - len(delete_keys) + len(items) > MAX_SLOTS_PER_SITE:
            raise PlanError(
                "plan.quota_exceeded",
                f"A site holds at most {MAX_SLOTS_PER_SITE} slots.",
                status_code=422,
                limit=MAX_SLOTS_PER_SITE,
            )

        inserts = [self._slot_of(key, item) for item in items]
        outcome = self._plan.replace_slots(SlotBatchWrite(location_key=key, delete_keys=delete_keys, inserts=inserts))
        self._recompute_adjacency(key)
        logger.info(
            "garden_resource.slots_replaced",
            location_key=key,
            mode=request.mode,
            created=len(outcome.created_keys),
            deleted=outcome.deleted_count,
        )
        return SlotBatchResult(
            created_keys=outcome.created_keys,
            deleted_count=outcome.deleted_count,
            kept_count=len(kept),
        )

    @staticmethod
    def _slot_of(location_key: str, item: SlotBatchItem) -> Slot:
        return Slot(
            slot_id=item.slot_id,
            location_key=location_key,
            capacity_plants=item.capacity_plants,
            slot_role=item.slot_role,
            geometry=item.geometry,
            row_index=item.row_index,
            sequence=item.sequence,
            geometry_source=item.geometry_source,
            container_volume_l=item.container_volume_l,
            planned_spacing_cm=item.planned_spacing_cm,
        )

    def _slot_item_findings(
        self, location: Location, items: list[SlotBatchItem], kept: list[Slot]
    ) -> list[tuple[int | None, str, str, dict[str, Any]]]:
        """V-20, shape of each slot, V-04 and V-06 for the whole batch against what stays."""
        findings: list[tuple[int | None, str, str, dict[str, Any]]] = []
        taken = {slot.slot_id for slot in kept}
        seen: set[str] = set()
        for index, item in enumerate(items):
            if item.slot_id in taken or item.slot_id in seen:
                findings.append((None, f"slots[{index}].slot_id", "slot.duplicate_id", {"index": index}))
            seen.add(item.slot_id)
            try:
                self._slot_of(location.key or "", item)
            except PydanticValidationError:
                findings.append((None, f"slots[{index}].geometry", "geometry.invalid", {"index": index}))
        if findings:
            return findings
        keyed = [(f"#{index}", item.geometry) for index, item in enumerate(items)]
        neighbours = [(slot.key or "", slot.geometry) for slot in kept if slot.archived_at is None and slot.geometry]
        try:
            self._check_slot_rules(location, keyed, others=neighbours)
        except PlanValidationError as exc:
            for detail in exc.details or []:
                subject = str(detail.get("key", ""))
                slot_index = int(subject[1:]) if subject.startswith("#") and subject[1:].isdigit() else None
                findings.append(
                    (
                        None,
                        f"slots[{slot_index}].geometry" if slot_index is not None else "slots",
                        str(detail["code"]),
                        {"index": slot_index} if slot_index is not None else {"key": subject},
                    )
                )
        return findings

    @staticmethod
    def _check_slot_rules(
        location: Location,
        subjects: list[tuple[str, Geometry]],
        *,
        others: Sequence[tuple[str | None, Geometry | None]],
    ) -> None:
        """V-04 and V-06 for ``subjects`` (key, bed-frame geometry) against the bed and the slots that stay.

        A bed without a geometry has no frame to be outside of (it is unplaced): V-04 is skipped there and
        applies once the bed is drawn — the batch of the plan then checks the slots it holds (V-04 in WP 1.8).
        """
        findings: list[tuple[int | None, str, str, dict[str, Any]]] = []
        if location.geometry is not None:
            for key in slots_outside_bed(location.geometry, subjects):
                findings.append((None, "geometry", ERROR_SLOT_OUTSIDE_BED, {"key": key}))
        neighbours = [(key, geometry) for key, geometry in others if key and geometry is not None]
        subject_keys = {key for key, _ in subjects}
        for first, second in overlapping_zones([*subjects, *neighbours]):
            if first in subject_keys or second in subject_keys:
                findings.append(
                    (None, "geometry", ERROR_SLOT_OVERLAP, {"key": first if first in subject_keys else second})
                )
        if findings:
            raise PlanValidationError(findings)

    def _recompute_adjacency(self, location_key: str) -> None:
        """The adjacency recompute a slot change triggers (GP-API-014, GP-NFR-016)."""
        request_adjacency_recompute(self._dispatch_adjacency, location_key)
