"""REQ-053 GP-FR-074 — succession batches reserve their slots, as it reads on the wire.

``app.main`` with the real tenant gate and the real succession, run and reservation services over the in-memory
doubles of ``tests/support/planting_reservation_fakes.py``: ``POST …/generate`` stores one ``run_planned_at``
reservation per batch, an overlap answers the 409 body of V-08 and stores nothing, another tenant's plan is a 404,
and ``GET /sites/{key}/plan`` carries the first reserved day of a slot as ``planned_from``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_garden_plan_service, get_succession_plan_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.slot_reservation_engine import Reservation
from app.domain.models.site import Slot
from app.domain.models.user import User
from app.domain.services import succession_plan_service as succession_module
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.succession_plan_service import SuccessionPlanService
from tests.support.garden_plan_fakes import OTHER_TENANT, SITE, TENANT
from tests.support.planting_reservation_fakes import build_world
from tests.unit.domain.services.test_succession_plan_service import _FakeSuccessionRepo

_OWN = "/api/v1/t/own/succession-plans"
_OTHER = "/api/v1/t/other/succession-plans"
D = date

_BODY = {
    "name": "Lettuce bed 3",
    "species_key": "sp_tomato",
    "interval_days": 21,
    "start_date": "2027-04-01",
    "end_date": "2027-05-13",
    "plants_per_batch": 2,
    "batch_duration_days": 21,
    "location_key": "bed",
}


class _Tenants:
    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def world(monkeypatch) -> SimpleNamespace:
    world = build_world()
    world.plan.slots = [
        Slot(
            _key=f"s{n}",
            slot_id=f"BED3_00{n}",
            location_key="bed",
            sequence=n,
            geometry={"kind": "point", "origin": [n * 0.5, 1]},
        )
        for n in range(1, 5)
    ]
    monkeypatch.setattr(succession_module, "today_utc", lambda: D(2027, 1, 10))
    world.succession = SuccessionPlanService(
        _FakeSuccessionRepo(),
        world.service,
        site_repo=world.sites,
        species_resolver=lambda key, *, tenant_key: world.species[key],
        reservations=world.reservations,
    )
    return world


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
    app.dependency_overrides[get_succession_plan_service] = lambda: world.succession
    app.dependency_overrides[get_garden_plan_service] = lambda: GardenPlanService(world.sites, world.plan)
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _create(client: Callable[..., TestClient], **overrides) -> str:
    response = client().post(_OWN, json={**_BODY, **overrides})
    assert response.status_code == 201, response.text
    assert response.json()["batch_duration_days"] == overrides.get("batch_duration_days", 21)
    return response.json()["key"]


def test_generate_reserves_the_slots_of_every_batch(client, world) -> None:
    key = _create(client)

    response = client().post(f"{_OWN}/{key}/generate")

    assert response.status_code == 201, response.text
    runs = response.json()["runs"]
    assert len(runs) == 3
    windows = {(r.run_key, r.slot_key): (r.planned_from, r.planned_until) for r in world.repo.reservations}
    first = runs[0]["run_key"]
    assert windows[(first, "s1")] == (D(2027, 4, 1), D(2027, 4, 21))
    assert {slot for run_key, slot in windows if run_key == runs[2]["run_key"]} == {"s1", "s2"}


def test_an_overlap_is_409_with_the_v08_body_and_stores_nothing(client, world) -> None:
    for sequence, slot_key in enumerate(["s1", "s2", "s3"], start=1):
        world.repo.reservations.append(
            Reservation(slot_key, "run_tomato", "e_t", "sp", sequence, D(2027, 3, 1), D(2027, 6, 30))
        )
    key = _create(client)

    response = client().post(f"{_OWN}/{key}/generate")

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "slot.already_planned"
    detail = body["details"][0]
    assert detail["conflicting_run_key"] == "run_tomato"
    assert detail["overlap_from"] == "2027-04-01"
    assert world.runs.runs == {}


def test_another_tenants_plan_is_a_404_and_releases_nothing(client, world) -> None:
    key = _create(client)
    assert client().post(f"{_OWN}/{key}/generate").status_code == 201
    before = list(world.repo.reservations)

    assert client().post(f"{_OTHER}/{key}/generate").status_code == 404
    assert client().put(f"{_OTHER}/{key}", json={"interval_days": 7}).status_code == 404
    assert client(TenantRole.LEAD).delete(f"{_OTHER}/{key}").status_code == 404

    assert world.repo.reservations == before


def test_a_schedule_change_releases_the_future_batches(client, world) -> None:
    key = _create(client)
    assert client().post(f"{_OWN}/{key}/generate").status_code == 201

    response = client().put(f"{_OWN}/{key}", json={"interval_days": 28})

    assert response.status_code == 200, response.text
    assert world.repo.reservations == []


def test_the_plan_read_model_carries_the_first_reserved_day(client, world) -> None:
    world.plan.slot_planned_from = {"s1": D(2027, 4, 1)}

    response = client().get(f"/api/v1/t/own/sites/{SITE}/plan")

    assert response.status_code == 200, response.text
    slots = {slot["key"]: slot for slot in response.json()["slots"]}
    assert slots["s1"]["planned_from"] == "2027-04-01"
    assert slots["s2"].get("planned_from") is None
