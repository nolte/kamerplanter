"""In-memory doubles of the garden-plan service's collaborators (REQ-053 WP 1.8).

``FakePlanRepo`` is a faithful stand-in for the transaction: it holds the structure, applies a write
set the way ``ArangoGardenPlanRepository.apply_plan_batch`` does (revision check first, then the
writes) and records what it was handed, so a test can assert both what the service decided and what
reached the repository at all. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from app.common.exceptions import PlanRevisionConflictError
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository, PlanReadData
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    PlanAuditEntry,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlantShortInfo,
    TaskCounter,
)
from app.domain.models.site import Location, Site, SitePlan, Slot

TENANT = "ten_own"
OTHER_TENANT = "ten_other"
SITE = "site_1"
USER = "u_sabine"

_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


def rect(x: float, y: float, w: float = 2, h: float = 1, rotation: float = 0) -> dict:
    return {"kind": "rect", "origin": [x, y], "width_m": w, "length_m": h, "rotation_deg": rotation}


class FakeSites:
    """The three reads ``location_ownership`` needs, over sites keyed by ``_key``."""

    def __init__(self, *sites: Site) -> None:
        self.sites = {site.key: site for site in sites}

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_location_by_key(self, key):  # pragma: no cover - not reached by the plan service
        return None

    def get_slot_by_key(self, key):  # pragma: no cover
        return None


class FakePlanRepo(IGardenPlanRepository):
    def __init__(self, sites: FakeSites) -> None:
        self._sites = sites
        self.locations: dict[str, Location] = {}
        self.objects: dict[str, GardenObject] = {}
        self.slots: list[Slot] = []
        self.plants: list[PlantShortInfo] = []
        self.bed_types = {"bed": True, "raised_bed": True, "greenhouse": False}
        self.active_plants = 0
        self.applied: list[PlanBatchWrite] = []
        self.audit: list[PlanAuditEntry] = []
        self.editor_name: str | None = "Sabine"
        self.task_counters: dict[str, TaskCounter] = {}
        self._next = 100

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
            plan_updated_by_name=self.editor_name,
        )

    def load_active_slots(self, site_key, location_keys, *, tenant_key):
        site = self._sites.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key:
            return []
        return [slot for slot in self.slots if slot.location_key in location_keys and slot.archived_at is None]

    def bed_type_flags(self, location_type_keys):
        return {key: self.bed_types[key] for key in location_type_keys if key in self.bed_types}

    def count_active_plants(self, location_keys, *, tenant_key):
        return self.active_plants

    def list_audit(self, site_key, *, tenant_key, offset, limit):
        return self.audit[offset : offset + limit]

    # the transaction ---------------------------------------------------
    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        site = self._sites.sites[write.site_key]
        revision = site.plan.plan_revision if site.plan else 0
        if revision != write.expected_revision or revision != write.basis_revision:
            raise PlanRevisionConflictError(
                current_revision=revision, changed_by=self.editor_name, changed_at="2026-10-17T09:00:00+00:00"
            )
        self.applied.append(write)
        key_map: dict[str, str] = {}
        for temp, location in write.location_inserts:
            self._next += 1
            key_map[temp] = f"loc_{self._next}"
            parent = key_map.get(location.parent_location_key or "", location.parent_location_key)
            self.locations[key_map[temp]] = location.model_copy(
                update={"key": key_map[temp], "parent_location_key": parent}
            )
        for key, fields in write.location_updates:
            self.locations[key] = Location(**{**self.locations[key].model_dump(by_alias=True), **fields})
        for key in write.location_deletes:
            self.locations.pop(key, None)
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
