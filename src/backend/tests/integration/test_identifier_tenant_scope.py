"""#2065 — instance_id, slot_id and batch_id are unique within their owner, not across tenants.

``plant_instances.instance_id``, ``slots.slot_id`` and ``harvest_batches.batch_id``
carried collection-wide unique indexes. Onboarding derives the instance id from the
global species (``onb-<species_key>-<n>``), so the second tenant to onboard a species
had its plants skipped; a caller-chosen slot or lot label another tenant used was
refused with ``409`` — which told the caller that some other tenant holds it.

The scopes now: ``(tenant_key, instance_id)``, ``(tenant_key, batch_id)`` (sparse,
an unlabelled batch stays outside the constraint) and ``(location_key, slot_id)`` — a
slot carries no tenant of its own (``Slot.tenant_key`` is empty, #1397); its location
is the parent that belongs to exactly one tenant.

Run through the **real routes, DI factories, services, repositories and error
handler** against a real ArangoDB; only the caller's identity is overridden.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the routes write plants, slots and batches to a real server"),
]

_DB_NAME = run_database_name("identifier_tenant_scope")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUGS = {TENANT_A: "alice", TENANT_B: "bob"}
SPECIES_KEY = "ocimum-basilicum"


@pytest.fixture
def env() -> Iterator[tuple[Any, Any, dict[str, str]]]:
    """The real tenant-scoped routers over a throwaway database; ``acting["tenant"]`` picks the caller."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common import dependencies as deps
    from app.common.auth import get_active_tenant_context, get_active_tenant_key, get_current_tenant, get_current_user
    from app.common.enums import TenantRole
    from app.common.error_handlers import app_error_handler
    from app.common.exceptions import KamerplanterError
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection
    from app.domain.models.tenant_context import TenantContext
    from app.domain.models.user import User

    settings = Settings(arangodb_database=_DB_NAME)
    sysdb = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if sysdb.has_database(_DB_NAME):
        sysdb.delete_database(_DB_NAME)
    conn = ArangoConnection(settings)
    db = conn.connect()
    col.ensure_collections(db)
    db.collection(col.SPECIES).insert(
        {
            "_key": SPECIES_KEY,
            "tenant_key": "",
            "scientific_name": "Ocimum basilicum",
            "scientific_name_normalized": "ocimum basilicum",
            "common_names": ["Basilikum"],
        }
    )
    for tenant in (TENANT_A, TENANT_B):
        slug = SLUGS[tenant]
        db.collection(col.SITES).insert({"_key": f"site-{slug}", "tenant_key": tenant, "name": f"Garden {slug}"})
        db.collection(col.LOCATIONS).insert(
            {"_key": f"loc-{slug}", "name": "Tent", "site_key": f"site-{slug}", "area_m2": 1.0}
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": f"plant-{slug}", "tenant_key": tenant, "instance_id": f"P-{slug}", "species_key": SPECIES_KEY}
        )
    previous_connection = deps._connection
    deps._connection = conn

    acting = {"tenant": TENANT_A}

    def ctx() -> TenantContext:
        tenant = acting["tenant"]
        return TenantContext(
            tenant_key=tenant, tenant_slug=SLUGS[tenant], user_key=f"user-{tenant}", role=TenantRole.LEAD
        )

    app = FastAPI()
    app.include_router(tenant_scoped_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_tenant] = ctx
    app.dependency_overrides[get_active_tenant_context] = ctx
    app.dependency_overrides[get_active_tenant_key] = lambda: acting["tenant"]
    app.dependency_overrides[get_current_user] = lambda: User(
        _key=f"user-{acting['tenant']}", email=f"{SLUGS[acting['tenant']]}@example.com", display_name="Grower"
    )

    yield TestClient(app, raise_server_exceptions=False), db, acting

    deps._connection = previous_connection
    if sysdb.has_database(_DB_NAME):
        sysdb.delete_database(_DB_NAME)
    conn.close()


def _as(acting: dict[str, str], tenant: str) -> str:
    acting["tenant"] = tenant
    return f"/api/v1/t/{SLUGS[tenant]}"


def _onboard(client: Any, acting: dict[str, str], tenant: str) -> Any:
    return client.post(
        f"{_as(acting, tenant)}/onboarding/complete",
        json={"plant_configs": [{"species_key": SPECIES_KEY, "count": 2}]},
    )


def _create_plant(client: Any, acting: dict[str, str], tenant: str, instance_id: str) -> Any:
    return client.post(
        f"{_as(acting, tenant)}/plant-instances",
        json={"instance_id": instance_id, "species_key": SPECIES_KEY, "planted_on": "2026-05-01"},
    )


def _create_slot(client: Any, acting: dict[str, str], tenant: str, slot_id: str, location_key: str = "") -> Any:
    location_key = location_key or f"loc-{SLUGS[tenant]}"
    return client.post(f"{_as(acting, tenant)}/slots", json={"slot_id": slot_id, "location_key": location_key})


def _create_batch(client: Any, acting: dict[str, str], tenant: str, batch_id: str | None) -> Any:
    return client.post(
        f"{_as(acting, tenant)}/harvest/plants/plant-{SLUGS[tenant]}/batches",
        json={"batch_id": batch_id, "wet_weight_g": 100.0},
    )


def _assert_names_nothing_foreign(response: Any, foreign: list[str]) -> None:
    for value in (TENANT_B, SLUGS[TENANT_B], *foreign):
        assert value not in response.text, f"the 409 names {value!r} of the other tenant: {response.text}"


def test_two_tenants_onboard_the_same_species(env) -> None:
    client, db, acting = env

    first = _onboard(client, acting, TENANT_A)
    second = _onboard(client, acting, TENANT_B)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json().get("skipped") in (None, []), second.text
    rows = sorted(
        (d["tenant_key"], d["instance_id"])
        for d in db.collection("plant_instances").all()
        if d["instance_id"].startswith("onb-")
    )
    ids = [f"onb-{SPECIES_KEY}-1", f"onb-{SPECIES_KEY}-2"]
    assert rows == [(t, i) for t in (TENANT_A, TENANT_B) for i in ids]


def test_two_tenants_choose_the_same_instance_id_and_one_tenant_does_not(env) -> None:
    client, _db, acting = env

    other = _create_plant(client, acting, TENANT_B, "BASIL-001")
    own = _create_plant(client, acting, TENANT_A, "BASIL-001")
    again = _create_plant(client, acting, TENANT_A, "BASIL-001")

    assert other.status_code == 201, other.text
    assert own.status_code == 201, own.text
    assert again.status_code == 409, again.text
    assert again.json()["details"][0]["field"] == "instance_id", again.text
    _assert_names_nothing_foreign(again, [other.json()["key"]])


def test_two_tenants_choose_the_same_slot_id_and_one_location_does_not(env) -> None:
    client, db, acting = env

    other = _create_slot(client, acting, TENANT_B, "TENT01_A1")
    own = _create_slot(client, acting, TENANT_A, "TENT01_A1")
    again = _create_slot(client, acting, TENANT_A, "TENT01_A1")

    assert other.status_code == 201, other.text
    assert own.status_code == 201, own.text
    assert again.status_code == 409, again.text
    assert again.json()["details"][0]["field"] == "slot_id", again.text
    _assert_names_nothing_foreign(again, [other.json()["key"], "loc-bob", "site-bob"])
    assert sorted(d["location_key"] for d in db.collection("slots").find({"slot_id": "TENT01_A1"})) == [
        "loc-alice",
        "loc-bob",
    ]


def test_two_tenants_label_a_batch_the_same_and_one_tenant_does_not(env) -> None:
    client, _db, acting = env

    other = _create_batch(client, acting, TENANT_B, "LOT-2026-01")
    own = _create_batch(client, acting, TENANT_A, "LOT-2026-01")
    again = _create_batch(client, acting, TENANT_A, "LOT-2026-01")

    assert other.status_code == 201, other.text
    assert own.status_code == 201, own.text
    assert again.status_code == 409, again.text
    assert again.json()["details"][0]["field"] == "batch_id", again.text
    _assert_names_nothing_foreign(again, [other.json()["key"]])


def test_unlabelled_batches_stay_outside_the_constraint(env) -> None:
    client, _db, acting = env

    responses = [_create_batch(client, acting, TENANT_A, None) for _ in range(2)]

    assert [r.status_code for r in responses] == [201, 201], [r.text for r in responses]
