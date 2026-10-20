"""In-memory doubles of the garden-plan service's collaborators (REQ-053 WP 1.8).

``FakePlanRepo`` is a faithful stand-in for the transaction: it holds the structure, applies a write
set the way ``ArangoGardenPlanRepository.apply_plan_batch`` does (revision check first, then the
writes) and records what it was handed, so a test can assert both what the service decided and what
reached the repository at all. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from datetime import datetime

from app.common.exceptions import DuplicateError, PlanError, PlanRevisionConflictError, WriteConflictError
from app.domain.interfaces.garden_object_repository import IGardenObjectRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository, PlanReadData
from app.domain.models.care_event import CareEvent
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BedCounters,
    PlanAuditEntry,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlantShortInfo,
    SlotBatchOutcome,
    SlotBatchWrite,
    SlotSpeciesHint,
    TaskCounter,
)
from app.domain.models.irrigation_zone import IrrigationZone
from app.domain.models.site import Location, Site, SitePlan, Slot

TENANT = "ten_own"
OTHER_TENANT = "ten_other"
SITE = "site_1"
USER = "u_sabine"

_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


def rect(x: float, y: float, w: float = 2, h: float = 1, rotation: float = 0) -> dict:
    return {"kind": "rect", "origin": [x, y], "width_m": w, "length_m": h, "rotation_deg": rotation}


class FakeSites:
    """The site reads the services need (``location_ownership``, location and slot lists), over a repo's documents.

    The sites are keyed by ``_key``; locations and slots are the ones of the :class:`FakePlanRepo` that
    adopted this object, so a test arranges the world in one place.
    """

    def __init__(self, *sites: Site) -> None:
        self.sites = {site.key: site for site in sites}
        self.repo: FakePlanRepo | None = None

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_site_or_raise(self, key):
        from app.common.exceptions import NotFoundError

        site = self.sites.get(key)
        if site is None:
            raise NotFoundError("Site", key)
        return site

    def get_location_by_key(self, key):
        return self.repo.locations.get(key) if self.repo is not None else None

    def get_locations_by_keys(self, keys):
        return [
            self.repo.locations[key] for key in sorted(keys) if self.repo is not None and key in self.repo.locations
        ]

    def get_slot_by_key(self, key):
        if self.repo is None:
            return None
        return next((slot for slot in self.repo.slots if slot.key == key), None)

    def get_locations_by_site(self, site_key):
        return [loc for loc in (self.repo.locations.values() if self.repo else []) if loc.site_key == site_key]

    def get_slots_by_location(self, location_key):
        return [slot for slot in (self.repo.slots if self.repo else []) if slot.location_key == location_key]


class FakeObjects(IGardenObjectRepository):
    """Strict reads over the :class:`FakePlanRepo`'s objects: a foreign site's object is ``None``."""

    def __init__(self, repo: FakePlanRepo) -> None:
        self._repo = repo

    def _owned(self, garden_object: GardenObject, tenant_key: str) -> bool:
        site = self._repo._sites.get_site_by_key(garden_object.site_key)
        return bool(tenant_key) and site is not None and site.tenant_key == tenant_key

    def get_garden_objects_by_site(self, site_key, *, tenant_key):
        return [o for o in self._repo.objects.values() if o.site_key == site_key and self._owned(o, tenant_key)]

    def get_garden_object_by_key(self, key, *, tenant_key):
        found = self._repo.objects.get(key)
        return found if found is not None and self._owned(found, tenant_key) else None

    def get_garden_object_or_raise(self, key, *, tenant_key):
        from app.common.exceptions import NotFoundError

        found = self.get_garden_object_by_key(key, tenant_key=tenant_key)
        if found is None:
            raise NotFoundError("GardenObject", key)
        return found

    def create_garden_object(self, garden_object):  # pragma: no cover - the batch writes objects
        raise NotImplementedError

    def update_garden_object(self, key, garden_object):  # pragma: no cover
        raise NotImplementedError

    def delete_garden_object(self, key):  # pragma: no cover
        raise NotImplementedError


class FakePlanRepo(IGardenPlanRepository):
    def __init__(self, sites: FakeSites) -> None:
        self._sites = sites
        self.locations: dict[str, Location] = {}
        self.objects: dict[str, GardenObject] = {}
        self.slots: list[Slot] = []
        self.plants: list[PlantShortInfo] = []
        self.bed_types = {"bed": True, "raised_bed": True, "greenhouse": False}
        self.active_plants = 0
        #: Locations in which a plant stands (the import's V-09 set); ``active_plants`` stays the delete-check count.
        self.planted: set[str] = set()
        self.snapshots: list[dict] = []
        self.applied: list[PlanBatchWrite] = []
        self.audit: list[PlanAuditEntry] = []
        self.editor_name: str | None = "Sabine"
        self.task_counters: dict[str, TaskCounter] = {}
        self.object_task_counters: dict[str, TaskCounter] = {}
        self.counters: dict[str, BedCounters] = {}
        self.care_events: list[CareEvent] = []
        #: Newest watering per bed (WP 7.3), what ``load_read_model`` hands the plan with the task counters.
        self.last_watered: dict[str, datetime] = {}
        self.zones: dict[str, tuple[str, str]] = {"zone_1": (TENANT, SITE)}
        #: What the import wrote (WP 7.2): the zones it created by their new key, and the zone keys it deleted.
        self.imported_zones: dict[str, IrrigationZone] = {}
        self.deleted_zones: list[str] = []
        self.substrates: dict[str, str] = {"sub_global": "", "sub_own": TENANT, "sub_foreign": OTHER_TENANT}
        self.reserved: set[str] = set()
        self.field_updates: list[tuple[str, dict]] = []
        self.slot_writes: list[SlotBatchWrite] = []
        self.slot_field_updates: list[tuple[str, dict]] = []
        self.species_hints: list[SlotSpeciesHint] = []
        self._next = 100
        sites.repo = self

    # reads ---------------------------------------------------------------
    def load_structure(self, site_key, *, tenant_key):
        site = self._sites.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key:
            return [], []
        return list(self.locations.values()), list(self.objects.values())

    def load_read_model(self, site_key, *, tenant_key, include_plants, include_tasks):
        locations, objects = self.load_structure(site_key, tenant_key=tenant_key)
        return PlanReadData(
            locations=locations,
            garden_objects=objects,
            slots=list(self.slots),
            plants=list(self.plants) if include_plants else [],
            task_counters=dict(self.task_counters) if include_tasks else {},
            object_task_counters=dict(self.object_task_counters) if include_tasks else {},
            last_watered=dict(self.last_watered) if include_tasks else {},
            plan_updated_by_name=self.editor_name,
        )

    def load_active_slots(self, site_key, location_keys, *, tenant_key, include_archived=False):
        site = self._sites.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key:
            return []
        return [
            slot
            for slot in self.slots
            if slot.location_key in location_keys and (include_archived or slot.archived_at is None)
        ]

    def load_slot_species_hints(self, location_key, *, tenant_key):
        location = self.locations.get(location_key)
        site = self._sites.get_site_by_key(location.site_key) if location is not None else None
        if site is None or not tenant_key or site.tenant_key != tenant_key:
            return []
        in_bed = {slot.key for slot in self.slots if slot.location_key == location_key and slot.archived_at is None}
        return [hint for hint in self.species_hints if hint.slot_key in in_bed]

    def bed_type_flags(self, location_type_keys):
        return {key: self.bed_types[key] for key in location_type_keys if key in self.bed_types}

    def count_active_plants(self, location_keys, *, tenant_key):
        return self.active_plants

    def locations_with_active_plants(self, location_keys, *, tenant_key):
        return {key for key in location_keys if key in self.planted}

    def list_audit(self, site_key, *, tenant_key, offset, limit):
        return self.audit[offset : offset + limit]

    def purge_audit_before(self, cutoff, *, batch):
        due = [entry for entry in self.audit if entry.at < cutoff][:batch]
        self.audit = [entry for entry in self.audit if entry not in due]
        return len(due)

    # the transaction ---------------------------------------------------
    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        site = self._sites.sites[write.site_key]
        revision = site.plan.plan_revision if site.plan else 0
        if revision != write.expected_revision or revision != write.basis_revision:
            raise PlanRevisionConflictError(
                current_revision=revision, changed_by=self.editor_name, changed_at="2026-10-17T09:00:00+00:00"
            )
        for key, expected in write.status_from.items():
            if self.locations[key].bed_status.value != expected:
                raise PlanError("bed_status.changed", "The bed status was changed.", status_code=409, current="x")
        self.applied.append(write)
        key_map: dict[str, str] = {}
        self.deleted_zones.extend(write.zone_deletes)
        for temp, zone in write.zone_inserts:
            self._next += 1
            key_map[temp] = f"zone_{self._next}"
            self.imported_zones[key_map[temp]] = zone.model_copy(update={"key": key_map[temp]})
        for temp, location in write.location_inserts:
            self._next += 1
            key_map[temp] = f"loc_{self._next}"
            parent = key_map.get(location.parent_location_key or "", location.parent_location_key)
            self.locations[key_map[temp]] = location.model_copy(
                update={
                    "key": key_map[temp],
                    "parent_location_key": parent,
                    "irrigation_zone_key": key_map.get(
                        location.irrigation_zone_key or "", location.irrigation_zone_key
                    ),
                }
            )
        for key, fields in write.location_updates:
            self.locations[key] = Location(**{**self.locations[key].model_dump(by_alias=True), **fields})
        self.care_events.extend(write.care_events)
        for key in write.location_deletes:
            self.locations.pop(key, None)
            self.slots = [slot for slot in self.slots if slot.location_key != key]
        for temp, slot in write.slot_inserts:
            self._next += 1
            self.slots.append(slot.model_copy(update={"key": f"slot_{self._next}", "location_key": key_map[temp]}))
        if write.snapshot is not None:
            self.snapshots.append(write.snapshot)
        for temp, garden_object in write.object_inserts:
            self._next += 1
            key_map[temp] = f"go_{self._next}"
            self.objects[key_map[temp]] = garden_object.model_copy(update={"key": key_map[temp]})
        for key, fields in write.object_updates:
            self.objects[key] = GardenObject(**{**self.objects[key].model_dump(by_alias=True), **fields})
        for key in write.object_deletes:
            self.objects.pop(key, None)
        plan = site.plan or SitePlan()
        plan.plan_revision = revision + 1
        if write.boundary is not None:
            plan.boundary = write.boundary
        site.plan = plan
        return PlanBatchOutcome(plan_revision=revision + 1, key_map=key_map)

    # single resources (WP 1.9) -------------------------------------------
    def load_bed_counters(self, location_keys, *, tenant_key):
        return {key: self.counters[key] for key in location_keys if key in self.counters}

    def count_active_slots(self, site_key, *, tenant_key):
        site = self._sites.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key:
            return 0
        in_site = {key for key, loc in self.locations.items() if loc.site_key == site_key}
        return sum(1 for slot in self.slots if slot.location_key in in_site and slot.archived_at is None)

    def update_location_fields(self, location_key, fields):
        self.field_updates.append((location_key, dict(fields)))
        merged = {**self.locations[location_key].model_dump(by_alias=True), **fields}
        self.locations[location_key] = Location(**{k: v for k, v in merged.items() if v is not None})

    def set_site_underlay(self, site_key, *, tenant_key, underlay):
        site = self._sites.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key or site.plan is None:
            return False, None
        previous = site.plan.underlay.attachment_key if site.plan.underlay is not None else None
        site.plan = site.plan.model_copy(update={"underlay": underlay})
        return True, previous

    def update_slot_fields(self, slot_key, fields):
        self.slot_field_updates.append((slot_key, dict(fields)))
        self.slots = [
            Slot(**{**slot.model_dump(by_alias=True), **fields}) if slot.key == slot_key else slot
            for slot in self.slots
        ]

    def irrigation_zone_site_key(self, zone_key, *, tenant_key):
        zone = self.zones.get(zone_key)
        return zone[1] if zone is not None and zone[0] == tenant_key else None

    def substrate_visible(self, substrate_key, *, tenant_key):
        return substrate_key in self.substrates and self.substrates[substrate_key] in ("", tenant_key)

    def reserved_among(self, candidates, *, tenant_key):
        return {key for key in candidates if key in self.reserved}

    def replace_slots(self, write: SlotBatchWrite) -> SlotBatchOutcome:
        self.slot_writes.append(write)
        by_key = {slot.key: slot for slot in self.slots}
        for key in write.delete_keys:
            slot = by_key.get(key)
            if slot is None or slot.currently_occupied or key in self.reserved:
                raise WriteConflictError("slots", "a slot to replace was occupied or reserved concurrently")
        remaining = [slot for slot in self.slots if slot.key not in set(write.delete_keys)]
        taken = {slot.slot_id for slot in remaining if slot.location_key == write.location_key}
        created: list[str] = []
        for slot in write.inserts:
            if slot.slot_id in taken:
                raise DuplicateError("Slot", "slot_id", slot.slot_id)
            taken.add(slot.slot_id)
            self._next += 1
            key = f"slot_{self._next}"
            created.append(key)
            remaining.append(slot.model_copy(update={"key": key, "location_key": write.location_key}))
        self.slots = remaining
        return SlotBatchOutcome(created_keys=created, deleted_count=len(write.delete_keys))


def make_site(*, boundary: bool = True, revision: int = 5, tenant: str = TENANT) -> Site:
    plan = (
        SitePlan(boundary=_BOUNDARY if boundary else None, plan_revision=revision) if (boundary or revision) else None
    )
    return Site(_key=SITE, tenant_key=tenant, name="Garten", type="outdoor", plan=plan)


def make_location(key: str, name: str = "Bed", geometry: dict | None = None, **kwargs) -> Location:
    return Location(
        _key=key,
        name=name,
        site_key=SITE,
        area_m2=0.0,
        location_type_key=kwargs.pop("location_type_key", "bed"),
        geometry=geometry,
        **kwargs,
    )
