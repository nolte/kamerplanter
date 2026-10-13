"""#2082 — ``GET /planting-runs/{key}/plants`` names a plant's species under the caller's tenant.

A plant a *legacy* planting run created can carry a foreign tenant's private
``species_key`` (before #2081 the run service followed a foreign entry key). The route
used to resolve the label through the unscoped ``species_repo.get_by_key``. This drives
the real route over a real ArangoDB, with the legacy plant seeded straight into the
collection, next to the rows that must keep working (global, own, granted species).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

_DB_NAME = run_database_name("run_plants_species")
TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SLUG = "anna"
BASE = f"/api/v1/t/{SLUG}"

#: Exists only on tenant B's private species; any occurrence in a body is a leak.
FOREIGN_NAME = "Foreign private species"


@pytest.fixture(scope="module")
def client():
    from app.common import dependencies as deps
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection

    settings = Settings(arangodb_database=_DB_NAME)
    conn = ArangoConnection(settings)
    db = conn.connect()
    col.ensure_collections(db)
    previous_connection = deps._connection
    deps._connection = conn

    def put(collection: str, **doc) -> None:
        db.collection(collection).insert(doc, overwrite=True)

    put(col.TENANTS, _key=TENANT_A)
    put(col.PLANTING_RUNS, _key="run-a", tenant_key=TENANT_A, name="Run A", run_type="monoculture", status="active")
    species = {
        "spGlobal": ("", "Global species"),
        "spOwn": (TENANT_A, "Own species"),
        "spGranted": (TENANT_B, "Granted species"),
        "spForeign": (TENANT_B, FOREIGN_NAME),
    }
    for key, (tenant, name) in species.items():
        put(col.SPECIES, _key=key, tenant_key=tenant, scientific_name=name, scientific_name_normalized=name.lower())
        put(col.PLANT_INSTANCES, _key=f"p-{key}", tenant_key=TENANT_A, instance_id=f"P-{key}", species_key=key,
            planted_on="2026-01-01")  # fmt: skip
        put(col.RUN_CONTAINS, _from=f"{col.PLANTING_RUNS}/run-a", _to=f"{col.PLANT_INSTANCES}/p-{key}")
    put(col.PLANT_INSTANCES, _key="p-gone", tenant_key=TENANT_A, instance_id="P-gone", species_key="missing",
        planted_on="2026-01-01")  # fmt: skip
    put(col.RUN_CONTAINS, _from=f"{col.PLANTING_RUNS}/run-a", _to=f"{col.PLANT_INSTANCES}/p-gone")
    put(col.TENANT_HAS_ACCESS, _from=f"{col.TENANTS}/{TENANT_A}", _to=f"{col.SPECIES}/spGranted")

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common.auth import get_current_tenant
    from app.common.enums import TenantRole
    from app.common.exceptions import KamerplanterError
    from app.domain.models.tenant_context import TenantContext

    app = FastAPI()
    app.include_router(tenant_scoped_router, prefix="/api/v1")

    @app.exception_handler(KamerplanterError)
    def _handler(_request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": str(exc)})

    def _ctx() -> TenantContext:
        return TenantContext(tenant_key=TENANT_A, tenant_slug=SLUG, user_key="user-a", role=TenantRole.LEAD)

    app.dependency_overrides[get_current_tenant] = _ctx
    yield TestClient(app, raise_server_exceptions=False)

    deps._connection = previous_connection
    sysdb = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if sysdb.has_database(_DB_NAME):
        sysdb.delete_database(_DB_NAME)
    conn.close()


def _by_plant(client) -> dict[str, dict]:
    response = client.get(f"{BASE}/planting-runs/run-a/plants")
    assert response.status_code == 200, response.text
    return {p["key"]: p for p in response.json()}


def test_a_legacy_plant_with_a_foreign_species_key_does_not_return_the_foreign_name(client) -> None:
    response = client.get(f"{BASE}/planting-runs/run-a/plants")

    assert response.status_code == 200, response.text
    assert FOREIGN_NAME not in response.text
    plants = {p["key"]: p for p in response.json()}
    assert plants["p-spForeign"]["species"] is None


def test_the_readable_species_keep_their_name(client) -> None:
    plants = _by_plant(client)

    assert plants["p-spGlobal"]["species"]["scientific_name"] == "Global species"
    assert plants["p-spOwn"]["species"]["scientific_name"] == "Own species"
    assert plants["p-spGranted"]["species"]["scientific_name"] == "Granted species"


def test_an_unknown_species_key_stays_nameless_not_an_error(client) -> None:
    assert _by_plant(client)["p-gone"]["species"] is None
