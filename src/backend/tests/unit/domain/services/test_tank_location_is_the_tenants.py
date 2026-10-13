"""A tank may only be placed at a location of its own tenant — #1864 sweep (L3).

``POST``/``PUT /t/{slug}/tanks`` stored ``location_key`` as given and wrote a
``HAS_TANK`` edge from that location. ``GET …/tanks/{key}/active-nutrient-plans``
then matched runs by ``location_key`` without a tenant and returned another
tenant's runs, nutrient plans, fertilizers and plant counts. The location is now
resolved through its site under the tank's tenant; the read also filters runs by
the tank's tenant (defence for rows written before this change), pinned against
a real server in ``tests/integration/test_tank_active_plans_tenant_scope.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import TankType
from app.common.exceptions import NotFoundError
from app.domain.models.tank import Tank
from app.domain.services.tank_service import TankService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


class _TankRepo:
    def __init__(self) -> None:
        self.created: list[Tank] = []
        self.tank = Tank(_key="tank_own", tenant_key=OWN, name="T", tank_type=TankType.NUTRIENT, volume_liters=10)
        self.location_moves: list[tuple] = []

    def create(self, tank: Tank) -> Tank:
        self.created.append(tank)
        return tank.model_copy(update={"key": "tank_new"})

    def get_or_raise(self, key: str) -> Tank:
        if key != "tank_own":
            raise NotFoundError("Tank", key)
        return self.tank

    def update(self, key: str, tank: Tank) -> Tank:
        return tank

    def update_location(self, key, old, new) -> None:
        self.location_moves.append((key, old, new))


def _service(repo: _TankRepo, anchors=None) -> TankService:
    engine = MagicMock()
    engine.get_default_schedules.return_value = []
    return TankService(repo, engine, site_anchors=FakeSiteRepo() if anchors is None else anchors)  # type: ignore[arg-type]


def _tank(location: str | None) -> Tank:
    return Tank(tenant_key=OWN, name="Neu", tank_type=TankType.NUTRIENT, volume_liters=20, location_key=location)


@pytest.mark.parametrize("location", ["loc_foreign", "no-such-location"], ids=["foreign", "unknown"])
def test_a_tank_cannot_be_created_at_another_tenants_location(location: str) -> None:
    repo = _TankRepo()

    with pytest.raises(NotFoundError):
        _service(repo).create_tank(_tank(location), tenant_key=OWN)

    assert repo.created == []


@pytest.mark.parametrize("location", ["loc_foreign", "no-such-location"], ids=["foreign", "unknown"])
def test_a_tank_cannot_be_moved_to_another_tenants_location(location: str) -> None:
    repo = _TankRepo()

    with pytest.raises(NotFoundError):
        _service(repo).update_tank("tank_own", {"location_key": location}, tenant_key=OWN)

    assert repo.location_moves == []
    assert repo.tank.location_key is None


def test_the_tenants_own_location_is_accepted_on_create_and_update() -> None:
    repo = _TankRepo()
    service = _service(repo)

    service.create_tank(_tank("loc_own"), tenant_key=OWN)
    service.update_tank("tank_own", {"location_key": "loc_own"}, tenant_key=OWN)

    assert repo.created[0].location_key == "loc_own"
    assert repo.location_moves == [("tank_own", None, "loc_own")]


def test_without_site_anchors_a_location_is_refused() -> None:
    repo = _TankRepo()
    engine = MagicMock()

    with pytest.raises(NotFoundError):
        TankService(repo, engine).create_tank(_tank("loc_own"), tenant_key=OWN)  # type: ignore[arg-type]
