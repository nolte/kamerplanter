"""Equipment, location assignments and tank feed links point only at the caller's own objects — #1871 B2, B3, B5.

* **B2** — ``Equipment.location_key`` was stored as given with an
  ``EQUIPMENT_AT`` edge to the named location (any tenant's).
* **B3** — a location assignment checked the membership, not the location, and
  wrote an ``ASSIGNED_TO_LOCATION`` edge to any (even unknown) location.
* **B5** — ``POST /tanks/{key}/feeds-from`` resolved ``source_tank_key`` without a
  tenant: a ``FEEDS_FROM`` edge to a foreign tank, and 201 vs. 404 revealed
  whether that tank existed.

Locations are resolved through their site (#1397); the repository double is the
shared one where only sites carry a ``tenant_key``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import TankType
from app.common.exceptions import NotFoundError
from app.domain.models.inventree import Equipment
from app.domain.models.tank import Tank
from app.domain.services.inventree_service import InvenTreeService
from app.domain.services.tank_service import TankService
from app.domain.services.tenant_service import TenantService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo

# ── B2 equipment ──────────────────────────────────────────────────────────


class _EquipmentRepo:
    def __init__(self) -> None:
        self.created: list[Equipment] = []
        self.updated: list[tuple] = []
        self.item = Equipment(_key="eq_own", tenant_key=OWN, name="Pumpe", equipment_type="pump")

    def create_equipment(self, equipment: Equipment) -> Equipment:
        self.created.append(equipment)
        return equipment

    def get_equipment_or_raise(self, key: str) -> Equipment:
        if key != "eq_own":
            raise NotFoundError("Equipment", key)
        return self.item

    def update_equipment(self, key, equipment, *, location_changed):
        self.updated.append((key, equipment.location_key))
        return equipment


def _inventree(repo: _EquipmentRepo) -> InvenTreeService:
    return InvenTreeService(repo, MagicMock(), site_anchors=FakeSiteRepo())  # type: ignore[arg-type]


@pytest.mark.parametrize("location", ["loc_foreign", "no-such-location"], ids=["foreign", "unknown"])
def test_equipment_cannot_be_placed_at_another_tenants_location(location: str) -> None:
    repo = _EquipmentRepo()
    service = _inventree(repo)

    with pytest.raises(NotFoundError):
        service.create_equipment(OWN, Equipment(name="Lampe", equipment_type="lighting", location_key=location))
    with pytest.raises(NotFoundError):
        service.update_equipment("eq_own", OWN, {"location_key": location})

    assert repo.created == [] and repo.updated == []


def test_equipment_at_an_own_location_is_stored() -> None:
    repo = _EquipmentRepo()
    service = _inventree(repo)

    service.create_equipment(OWN, Equipment(name="Lampe", equipment_type="lighting", location_key="loc_own"))
    service.update_equipment("eq_own", OWN, {"location_key": "loc_own"})

    assert [e.location_key for e in repo.created] == ["loc_own"]
    assert repo.updated == [("eq_own", "loc_own")]


# ── B3 location assignments ───────────────────────────────────────────────


def _tenant_service() -> tuple[TenantService, MagicMock]:
    membership_repo = MagicMock()
    membership_repo.get_by_key.return_value = SimpleNamespace(tenant_key=OWN)
    assignment_repo = MagicMock()
    assignment_repo.get_by_membership_and_location.return_value = None
    assignment_repo.create.side_effect = lambda a: a
    service = TenantService(
        MagicMock(),
        membership_repo,
        MagicMock(),
        assignment_repo,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        site_anchors=FakeSiteRepo(),
    )
    return service, assignment_repo


@pytest.mark.parametrize("location", ["loc_foreign", "no-such-location"], ids=["foreign", "unknown"])
def test_a_member_cannot_be_assigned_to_another_tenants_location(location: str) -> None:
    service, assignments = _tenant_service()

    with pytest.raises(NotFoundError):
        service.create_assignment(OWN, "m1", location)

    assignments.create.assert_not_called()


def test_a_member_is_assigned_to_an_own_location() -> None:
    service, assignments = _tenant_service()

    service.create_assignment(OWN, "m1", "loc_own")

    assignments.create.assert_called_once()


# ── B5 tank feed links ────────────────────────────────────────────────────


class _Tanks:
    def __init__(self) -> None:
        self.links: list[tuple[str, str]] = []
        self.tanks = {
            key: Tank(_key=key, tenant_key=tenant, name=key, tank_type=TankType.NUTRIENT, volume_liters=10)
            for key, tenant in (("tank_a", OWN), ("tank_a2", OWN), ("tank_b", "t_b"))
        }

    def get_or_raise(self, key: str) -> Tank:
        if key not in self.tanks:
            raise NotFoundError("Tank", key)
        return self.tanks[key]

    def link_feeds_from(self, key: str, source: str) -> None:
        self.links.append((key, source))


@pytest.mark.parametrize("source", ["tank_b", "no-such-tank"], ids=["foreign", "unknown"])
def test_a_tank_cannot_be_fed_from_another_tenants_tank(source: str) -> None:
    repo = _Tanks()

    with pytest.raises(NotFoundError) as refused:
        TankService(repo, MagicMock()).link_feeds_from("tank_a", source, tenant_key=OWN)  # type: ignore[arg-type]

    assert repo.links == []
    assert refused.value.status_code == 404


def test_a_tank_is_fed_from_an_own_tank() -> None:
    repo = _Tanks()

    TankService(repo, MagicMock()).link_feeds_from("tank_a", "tank_a2", tenant_key=OWN)  # type: ignore[arg-type]

    assert repo.links == [("tank_a", "tank_a2")]
