"""``POST /plant-instances`` with the ``slot_key`` of a taken planting position answers 409 (REQ-053 GP-UX-071, V-25).

Before: the route answered 201 and stored a second plant on a position that already carried one (#2913). Now the
envelope carries the published codes the slot flows already use - ``slot.occupied`` (thinning: plants stand in the
slot) and ``slot.already_planned`` (V-08: a live run reserves it) - with ``details[0].field == "slot_key"``.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plants_router
from app.common import auth as auth_mod
from app.common.dependencies import get_plant_instance_service
from app.common.enums import SlotRole, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.models.tenant_context import TenantContext
from tests.support.single_plant_fakes import (
    BED,
    SITE,
    TENANT,
    build_service,
    make_plant,
    make_reservation,
    make_slot,
)


def _client(service) -> TestClient:  # type: ignore[no-untyped-def]
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(plants_router, prefix="/api/v1/t/{tenant_slug}")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1", account_type="human")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[auth_mod.get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT, tenant_slug="own", user_key="u1", role=TenantRole.GROWER, admin_scopes=[]
    )
    return TestClient(app)


@pytest.fixture
def world() -> Iterator[SimpleNamespace]:
    service, plants, sites, reservations = build_service(
        {
            "s_taken": make_slot("s_taken"),
            "s_reserved": make_slot("s_reserved"),
            "s_free": make_slot("s_free"),
            "r_row": make_slot("r_row", SlotRole.ROW, capacity=30),
        },
        standing=[
            make_plant(_key="p_tomato", instance_id="TOM-1", slot_key="s_taken"),
            make_plant(_key="p_carrot", instance_id="CAR-1", slot_key="r_row"),
        ],
        reservations=[make_reservation("s_reserved")],
    )
    yield SimpleNamespace(client=_client(service), plants=plants, sites=sites)


def _body(slot_key: str) -> dict:
    return {
        "instance_id": "LACTU-1113-ABC",
        "species_key": "sp-lettuce",
        "planted_on": "2026-11-13",
        "site_key": SITE,
        "location_key": BED,
        "slot_key": slot_key,
    }


def test_a_free_position_answers_201(world: SimpleNamespace) -> None:
    response = world.client.post("/api/v1/t/own/plant-instances", json=_body("s_free"))
    assert response.status_code == 201, response.text
    assert response.json()["slot_key"] == "s_free"


def test_a_position_with_a_plant_answers_409_slot_occupied(world: SimpleNamespace) -> None:
    response = world.client.post("/api/v1/t/own/plant-instances", json=_body("s_taken"))
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["error_code"] == "slot.occupied"
    assert body["details"][0]["field"] == "slot_key"
    assert body["details"][0]["code"] == "slot.occupied"
    assert world.plants.created == []
    assert world.sites.occupied == []


def test_a_reserved_position_answers_409_slot_already_planned(world: SimpleNamespace) -> None:
    response = world.client.post("/api/v1/t/own/plant-instances", json=_body("s_reserved"))
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["error_code"] == "slot.already_planned"
    assert body["details"][0]["conflicting_run_key"] == "run-7"
    assert world.plants.created == []


def test_a_row_with_plants_still_takes_one_more(world: SimpleNamespace) -> None:
    response = world.client.post("/api/v1/t/own/plant-instances", json=_body("r_row"))
    assert response.status_code == 201, response.text
