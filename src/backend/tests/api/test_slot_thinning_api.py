"""REQ-053 W-015 (Anhang A 60) — sowing and thinning a row/zone slot through the deployed app.

``app.main`` with the real tenant gate and the real :class:`SlotThinningService` over the in-memory world of
``tests/support/planting_reservation_fakes.py``. The unit tier shows what the service decides; this tier shows the
wire: the gate (a viewer gets 403 on every write), the cross-tenant negative test of every route (another
tenant's slug answers 404 and names nothing of the slot), the dotted codes and the response shapes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.datetimes import today_utc
from app.common.dependencies import get_plant_state_service, get_slot_thinning_service, get_tenant_service
from app.common.enums import TenantRole
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, SownSlotSource
from app.domain.models.user import User
from app.domain.services.plant_state_service import PlantStateService
from tests.api.test_planting_reservation_api import _Tenants
from tests.support.slot_thinning_world import sown_world

_OWN = "/api/v1/t/own"
_OTHER = "/api/v1/t/other"


@pytest.fixture
def world():
    return sown_world()


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_slot_thinning_service] = lambda: world.thinning
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestThinningRoute:
    def test_a_grower_thins_the_sown_row_into_its_plants(self, client, world) -> None:
        response = client().post(f"{_OWN}/slots/row1/thinning", json={})
        assert response.status_code == 201, response.text
        body = response.json()
        assert len(body["plant_keys"]) == 24
        assert len(body["instance_ids"]) == 24
        assert body["care_event_key"]
        assert next(slot for slot in world.plan.slots if slot.key == "row1").sown_at is None

    def test_the_plan_shows_the_runs_spacing_to_every_member(self, client) -> None:
        response = client(TenantRole.VIEWER).get(f"{_OWN}/slots/row1/thinning")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["slot_role"] == "row"
        assert body["thinning_to_cm"] == 5.0
        assert body["suggested_count"] == 24
        assert body["max_count"] == 500

    def test_a_viewer_may_not_thin(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(f"{_OWN}/slots/row1/thinning", json={"count": 3})
        assert response.status_code == 403
        assert world.repo.thinning_writes == []

    def test_without_a_spacing_the_grower_is_asked_for_one(self, client) -> None:
        world = sown_world(thinning_to_cm=None)
        from app.main import app

        app.dependency_overrides[get_slot_thinning_service] = lambda: world.thinning
        response = client().post(f"{_OWN}/slots/row1/thinning", json={})
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "thinning.spacing_required"

    def test_a_body_with_an_unknown_field_is_refused(self, client) -> None:
        response = client().post(f"{_OWN}/slots/row1/thinning", json={"tenant_key": "x"})
        assert response.status_code == 422

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("get", "/slots/row1/thinning", None),
            ("post", "/slots/row1/thinning", {"count": 3}),
            ("put", "/slots/row1/sowing", {"sown_at": "2026-04-01"}),
        ],
    )
    def test_another_tenants_slot_answers_404(self, client, world, method: str, path: str, body) -> None:
        kwargs = {} if body is None else {"json": body}
        response = getattr(client(), method)(f"{_OTHER}{path}", **kwargs)
        assert response.status_code == 404, response.text
        assert "site_a" not in response.text
        assert world.repo.thinning_writes == []
        assert world.repo.sowings == []


class TestSowingRoute:
    def test_a_grower_records_the_sowing(self, client, world) -> None:
        world.plan.slots[0] = world.plan.slots[0].model_copy(update={"sown_at": None})
        day = (today_utc() - timedelta(days=2)).isoformat()
        response = client().put(f"{_OWN}/slots/row1/sowing", json={"sown_at": day})
        assert response.status_code == 200, response.text
        assert response.json()["sown_at"] == day
        assert world.repo.sowings == [("row1", day)]

    def test_a_viewer_may_not_sow(self, client, world) -> None:
        response = client(TenantRole.VIEWER).put(f"{_OWN}/slots/row1/sowing", json={"sown_at": today_utc().isoformat()})
        assert response.status_code == 403
        assert world.repo.sowings == []

    def test_a_day_in_the_future_is_refused(self, client) -> None:
        day = (today_utc() + timedelta(days=3)).isoformat()
        response = client().put(f"{_OWN}/slots/row1/sowing", json={"sown_at": day})
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "slot.sown_in_future"


class _SownOnly(IPlantStateRepository):
    """The bed ``bed`` holds one sown row and no plant."""

    def list_sown_slots(self, location_key, *, tenant_key):
        return [
            SownSlotSource(
                slot_key="row1",
                slot_id="BED3_R01",
                sown_at=date(2026, 4, 12),
                species_key="sp_carrot",
                run_key="run_1",
                species_name="Carrot",
            )
        ]

    def list_bed_plants(self, location_key, *, tenant_key, now, offset, limit):
        return []

    def list_plants_in_beds(self, bed_keys, *, tenant_key, now, offset, limit):
        return []


class TestPlantStatesCarryTheSownSlot:
    def test_a_sown_row_is_an_entry_of_kind_sown(self, client, world) -> None:
        from app.main import app

        app.dependency_overrides[get_plant_state_service] = lambda: PlantStateService(world.sites, _SownOnly())
        response = client(TenantRole.VIEWER).get(f"{_OWN}/locations/bed/plant-states")
        assert response.status_code == 200, response.text
        (entry,) = response.json()
        assert entry["kind"] == "sown"
        assert entry["lifecycle"] == "sown"
        assert entry["plant_key"] is None
        assert entry["slot_key"] == "row1"
        assert entry["instance_id"] == "BED3_R01"
        assert entry["planted_on"] == "2026-04-12"
        assert entry["attention"] == []
