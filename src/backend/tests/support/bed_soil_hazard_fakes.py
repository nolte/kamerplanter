"""Doubles for the soil hazards of a bed (REQ-054 §5.2, #2888 F-20).

:class:`FakeBedSoilHazardRepo` applies the rules of ``ArangoBedSoilHazardRepository`` over a
:class:`~tests.support.garden_plan_fakes.FakePlanRepo`'s locations: the bed is read **through its site's tenant**
(a foreign and an absent bed are both ``location_not_found``), the change is applied to the stored entries and
written back only when it changed something. The transaction itself is measured against ArangoDB in
``tests/integration/test_bed_soil_hazard_repository.py``.

The service built by :func:`soil_hazard_service` is the real ``BedSoilHazardService`` with the real knowledge table
(the shipped seed YAML), the real ownership walk and these doubles - only persistence is replaced.
"""

from __future__ import annotations

from datetime import datetime

from app.common.enums import SoilHazard
from app.common.exceptions import NotFoundError
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.interfaces.bed_soil_hazard_repository import (
    IBedSoilHazardRepository,
    SoilHazardChange,
    SoilHazardRemoval,
    SoilHazardWrite,
)
from app.domain.models.bed_soil_hazard import AUDIT_ENTITY_SOIL_HAZARD, removal_audit_summary
from app.domain.models.garden_plan import PlanAuditRecord
from app.domain.models.location_type import LocationType
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.bed_soil_hazard_service import BedSoilHazardService
from tests.support.garden_plan_fakes import FakePlanRepo

#: The seeded location types the rules distinguish: beds, the vessel ``planter`` (a bed type) and ``tent`` /
#: ``shelf`` (no beds), and a type that is no bed at all.
LOCATION_TYPES: dict[str, bool] = {
    "bed": True,
    "raised_bed": True,
    "planter": True,
    "tent": False,
    "shelf": False,
    "greenhouse": False,
}


class FakeLocationTypes:
    """``get_by_key`` over :data:`LOCATION_TYPES`; an unknown key is ``None`` like in the catalogue."""

    def __init__(self, types: dict[str, bool] | None = None) -> None:
        self._types = LOCATION_TYPES if types is None else types

    def get_by_key(self, key: str) -> LocationType | None:
        if key not in self._types:
            return None
        return LocationType(_key=key, name=key, is_bed=self._types[key])


class FakePlants:
    """The plant reads the service needs; every plant is stored as the test wrote it."""

    def __init__(self, *plants: PlantInstance) -> None:
        self.rows: dict[str, PlantInstance] = {plant.key or "": plant for plant in plants}

    def get_by_key(self, key: str) -> PlantInstance | None:
        return self.rows.get(key)

    def get_or_raise(self, key: str) -> PlantInstance:
        plant = self.rows.get(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant


class FakeBedSoilHazardRepo(IBedSoilHazardRepository):
    def __init__(self, repo: FakePlanRepo) -> None:
        self._repo = repo
        #: Every write that reached the store: ``(location_key, entries)``.
        self.writes: list[tuple[str, tuple]] = []
        #: The ``garden_plan_audit`` rows the removals wrote (O6), as ``ArangoBedSoilHazardRepository`` builds them.
        self.audit_rows: list[PlanAuditRecord] = []

    def _owned(self, location_key: str, tenant_key: str):  # type: ignore[no-untyped-def]
        location = self._repo.locations.get(location_key)
        site = self._repo._sites.get_site_by_key(location.site_key) if location is not None else None
        if location is None or site is None or site.tenant_key != tenant_key:
            return None, None
        return location, site

    def change_soil_hazards(self, location_key: str, *, tenant_key: str, change: SoilHazardChange) -> SoilHazardWrite:
        if not tenant_key:
            raise ValueError("change_soil_hazards needs a tenant_key")
        location, _site = self._owned(location_key, tenant_key)
        if location is None:
            return SoilHazardWrite("location_not_found")
        stored = tuple(location.soil_hazards)
        changed = change(stored)
        if changed == stored:
            return SoilHazardWrite("unchanged", stored)
        self._repo.locations[location_key] = location.model_copy(update={"soil_hazards": list(changed)})
        self.writes.append((location_key, changed))
        return SoilHazardWrite("written", changed)

    def remove_soil_hazard(
        self, location_key: str, hazard: SoilHazard, *, tenant_key: str, user_key: str, at: datetime
    ) -> SoilHazardRemoval:
        if not tenant_key:
            raise ValueError("remove_soil_hazard needs a tenant_key")
        location, site = self._owned(location_key, tenant_key)
        if location is None:
            return SoilHazardRemoval("location_not_found")
        removed = next((entry for entry in location.soil_hazards if entry.hazard is hazard), None)
        if removed is None:
            return SoilHazardRemoval("not_held")
        kept = tuple(entry for entry in location.soil_hazards if entry.hazard is not hazard)
        self._repo.locations[location_key] = location.model_copy(update={"soil_hazards": list(kept)})
        self.writes.append((location_key, kept))
        revision = site.plan.plan_revision if site.plan is not None else 0
        self.audit_rows.append(
            PlanAuditRecord(
                tenant_key=tenant_key,
                site_key=site.key or "",
                revision=revision,
                user_key=user_key,
                op="delete",
                entity=AUDIT_ENTITY_SOIL_HAZARD,
                key=location_key,
                summary=removal_audit_summary(removed),
                at=at,
            )
        )
        return SoilHazardRemoval("removed", removed)


def soil_hazard_service(
    repo: FakePlanRepo,
    *plants: PlantInstance,
    hazards: FakeBedSoilHazardRepo | None = None,
    plant_store: object | None = None,
) -> BedSoilHazardService:
    """The real service over ``repo``'s sites and locations, the plants and the shipped knowledge table.

    ``plant_store`` replaces ``plants`` with a store another service writes too (``get_by_key`` is all it needs).
    """
    return BedSoilHazardService(
        repo._sites,  # type: ignore[arg-type]
        FakeLocationTypes(),  # type: ignore[arg-type]
        plant_store if plant_store is not None else FakePlants(*plants),  # type: ignore[arg-type]
        hazards if hazards is not None else FakeBedSoilHazardRepo(repo),
        YamlSoilHazardKnowledgeSource(),
    )
