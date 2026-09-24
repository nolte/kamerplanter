"""#1713 — a stored fertilizer key must be one the writing tenant can see.

#1708 scoped the *read* side: a fertilizer name inside a watering log resolves
only against fertilizers visible to the requesting tenant. The write side still
accepted any key, so a record of tenant A could carry a reference to tenant B's
**private** product. The read filter then showed the bare key instead of the
name, but the dangling cross-tenant reference was stored — and whether a write
naming a key was accepted, and how the record rendered afterwards, answered
"does this key exist in some other tenant?".

Every path that stores a fertilizer key was measured by grepping the domain
models for ``fertilizer_key`` / ``product_key`` fields and following each model
to its writers (see
``tests/unit/guards/test_fertilizer_references_are_verified_on_write.py`` for
the derived inventory). Each is run here through the **real route, real DI
factory, real service and real repository** against a real ArangoDB, with only
the caller's identity overridden — so a service that the DI factory forgot to
hand the fertilizer repository fails here instead of passing on a double.

Each path is exercised four ways, because a refusal alone proves nothing:

* **foreign** (tenant B's private product) — refused, and nothing naming it is
  stored anywhere in the database;
* **unknown** (a key that exists nowhere) — refused with the *same* status and
  error code, so the answer is no existence oracle;
* **own** and **global** (the catalogue's seed rows, ``tenant_key == ""``) —
  still accepted. A fix that hid the global catalogue would be the #324
  regression.

Two paths already answered an unknown key with 404 (a channel assignment and an
incompatibility each resolve the product up front); they keep that contract and
now answer a foreign key the same way. Every other path accepted an unknown key
silently and now answers both with 422.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

_DB_NAME = run_database_name("fertilizer_reference_visibility")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUG = "alice"
BASE = f"/api/v1/t/{SLUG}"

FOREIGN = "fert-b"
UNKNOWN = "fert-nowhere"
OWN = "fert-a"
GLOBAL = "fert-global"


@pytest.fixture(scope="module")
def env():
    """The real routers over a throwaway database, acting as a lead of tenant A."""
    from app.common import dependencies as deps
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection
    from app.domain.models.fertilizer import Fertilizer
    from app.domain.models.nutrient_plan import DeliveryChannel, NutrientPlan, NutrientPlanPhaseEntry
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.models.planting_run import PlantingRun
    from app.domain.models.site import Site
    from app.domain.models.tank import Tank

    settings = Settings(arangodb_database=_DB_NAME)
    conn = ArangoConnection(settings)
    db = conn.connect()
    col.ensure_collections(db)
    # The routers resolve every repository through ``dependencies.get_db()``;
    # without this they would answer out of the developer's own database.
    previous_connection = deps._connection
    deps._connection = conn

    def put(collection, model) -> None:
        doc = {k: v for k, v in model.model_dump(by_alias=True, mode="json").items() if v is not None}
        db.collection(collection).insert(doc, overwrite=True)

    for key, tenant, name in (
        (GLOBAL, "", "Global Grow"),
        (OWN, TENANT_A, "Alice Mix"),
        (FOREIGN, TENANT_B, "Bob Secret"),
    ):
        put(col.FERTILIZERS, Fertilizer(_key=key, tenant_key=tenant, product_name=name, fertilizer_type="base"))
    for tenant, suffix in ((TENANT_A, "a"), (TENANT_B, "b")):
        put(
            col.SITES,
            Site(
                _key=f"site-{suffix}",
                tenant_key=tenant,
                name=f"Garden {suffix}",
                type="outdoor",
                climate_zone="7a",
                hardiness_zone="7a",
            ),
        )
        put(
            col.PLANT_INSTANCES,
            PlantInstance(
                _key=f"plant-{suffix}",
                tenant_key=tenant,
                instance_id=f"P-{suffix}",
                species_key="tomato",
                plant_name=f"Plant {suffix}",
                planted_on="2026-01-01",
                site_key=f"site-{suffix}",
            ),
        )
        put(
            col.TANKS,
            Tank(
                _key=f"tank-{suffix}", tenant_key=tenant, name=f"Tank {suffix}", tank_type="nutrient", volume_liters=50
            ),
        )
        put(
            col.PLANTING_RUNS,
            PlantingRun(_key=f"run-{suffix}", tenant_key=tenant, name=f"Run {suffix}", run_type="monoculture"),
        )
        put(col.NUTRIENT_PLANS, NutrientPlan(_key=f"plan-{suffix}", tenant_key=tenant, name=f"Plan {suffix}"))
        put(
            col.NUTRIENT_PLAN_PHASE_ENTRIES,
            NutrientPlanPhaseEntry(
                _key=f"entry-{suffix}",
                plan_key=f"plan-{suffix}",
                phase_name="vegetative",
                sequence_order=1,
                week_start=1,
                week_end=4,
                delivery_channels=[DeliveryChannel(channel_id="c1", application_method="drench")],
            ),
        )

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from app.api.v1.care_reminders.router import router as care_router
    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common.auth import (
        get_active_tenant_context,
        get_active_tenant_key,
        get_current_tenant,
        get_current_user,
    )
    from app.common.enums import TenantRole
    from app.common.exceptions import KamerplanterError
    from app.domain.models.tenant_context import TenantContext
    from app.domain.models.user import User

    app = FastAPI()
    app.include_router(tenant_scoped_router, prefix="/api/v1")
    app.include_router(care_router, prefix="/api/v1")

    @app.exception_handler(KamerplanterError)
    def _handler(_request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": str(exc)})

    ctx = TenantContext(tenant_key=TENANT_A, tenant_slug=SLUG, user_key="user-a", role=TenantRole.LEAD)
    user = User(_key="user-a", email="alice@example.com", display_name="Alice")
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_active_tenant_context] = lambda: ctx
    app.dependency_overrides[get_active_tenant_key] = lambda: TENANT_A
    app.dependency_overrides[get_current_user] = lambda: user

    yield TestClient(app, raise_server_exceptions=False), db

    deps._connection = previous_connection
    sysdb = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if sysdb.has_database(_DB_NAME):
        sysdb.delete_database(_DB_NAME)
    conn.close()


def _mentions(db, key: str) -> list[str]:
    """Every stored document or edge, outside the catalogue itself, that names ``key``."""
    hits = []
    for info in db.collections():
        name = info["name"]
        if info["system"] or name == "fertilizers":
            continue
        cursor = db.aql.execute(
            "FOR d IN @@c FILTER CONTAINS(TO_STRING(d), @needle) RETURN d._id",
            bind_vars={"@c": name, "needle": f'"{key}"'},
        )
        hits.extend(cursor)
    for edge_collection in ("log_fertilizer", "feeding_used", "fert_incompatible", "plan_uses_fertilizer"):
        if db.has_collection(edge_collection):
            cursor = db.aql.execute(
                "FOR e IN @@c FILTER e._from == @id OR e._to == @id RETURN e._id",
                bind_vars={"@c": edge_collection, "id": f"fertilizers/{key}"},
            )
            hits.extend(cursor)
    return sorted(set(hits))


def _channel(key: str) -> dict:
    return {
        "channel_id": "c1",
        "application_method": "drench",
        "fertilizer_dosages": [{"fertilizer_key": key, "ml_per_liter": 1.0}],
    }


#: ``name -> (method, url, body(key), refusal status)``. One row per measured
#: write path; the name is what a failure prints.
WRITE_PATHS: dict[str, tuple[str, str, Callable[[str], dict], int]] = {
    "watering-log create": (
        "POST",
        f"{BASE}/watering-logs",
        lambda k: {
            "volume_liters": 1.0,
            "plant_keys": ["plant-a"],
            "fertilizers_used": [{"fertilizer_key": k, "ml_per_liter": 1.0}],
        },
        422,
    ),
    "watering-log confirm": (
        "POST",
        f"{BASE}/watering-logs/confirm",
        lambda k: {
            "run_key": "run-a",
            "task_key": "task-none",
            "overrides": {"fertilizers": [{"fertilizer_key": k, "ml_per_liter": 1.0}]},
        },
        422,
    ),
    "care-reminder confirm": (
        "POST",
        "/api/v1/care-reminders/plants/plant-a/confirm",
        lambda k: {"reminder_type": "fertilizing", "fertilizers_used": [{"fertilizer_key": k, "ml_applied": 1.0}]},
        422,
    ),
    "feeding-event create": (
        "POST",
        f"{BASE}/feeding-events",
        lambda k: {
            "plant_key": "plant-a",
            "volume_applied_liters": 1.0,
            "fertilizers_used": [{"fertilizer_key": k, "ml_applied": 1.0}],
        },
        422,
    ),
    "watering-event create": (
        "POST",
        f"{BASE}/watering-events",
        lambda k: {
            "volume_liters": 1.0,
            "plant_keys": ["plant-a"],
            "fertilizers_used": [{"product_key": k, "product_name": "Mix", "ml_per_liter": 1.0}],
        },
        422,
    ),
    "tank fill": (
        "POST",
        f"{BASE}/tanks/tank-a/fills",
        lambda k: {
            "fill_type": "full_change",
            "volume_liters": 10.0,
            "fertilizers_used": [{"product_key": k, "product_name": "Mix", "ml_per_liter": 1.0}],
        },
        422,
    ),
    "nutrient-plan entry create": (
        "POST",
        f"{BASE}/nutrient-plans/plan-a/entries",
        lambda k: {
            "phase_name": "flowering",
            "sequence_order": 2,
            "week_start": 5,
            "week_end": 8,
            "delivery_channels": [_channel(k)],
        },
        422,
    ),
    "nutrient-plan entry update": (
        "PUT",
        f"{BASE}/nutrient-plans/plan-a/entries/entry-a",
        lambda k: {"delivery_channels": [_channel(k)]},
        422,
    ),
    "channel fertilizer assign": (
        "POST",
        f"{BASE}/nutrient-plans/entries/entry-a/channels/c1/fertilizers",
        lambda k: {"fertilizer_key": k, "ml_per_liter": 1.0},
        404,
    ),
    "fertilizer incompatibility": (
        "POST",
        f"{BASE}/fertilizers/{OWN}/incompatibilities",
        lambda k: {"other_key": k},
        404,
    ),
}


def _send(client, path: str, key: str):
    method, url, body, _status = WRITE_PATHS[path]
    return client.request(method, url, json=body(key))


@pytest.mark.parametrize("path", sorted(WRITE_PATHS))
class TestEveryFertilizerWriteIsVisibilityChecked:
    def test_a_foreign_key_is_refused_like_an_unknown_one_and_nothing_is_stored(self, env, path) -> None:
        client, db = env
        refusal = WRITE_PATHS[path][3]

        unknown = _send(client, path, UNKNOWN)
        foreign = _send(client, path, FOREIGN)

        assert unknown.status_code == refusal, (path, unknown.text)
        assert (foreign.status_code, foreign.json().get("error_code")) == (
            unknown.status_code,
            unknown.json().get("error_code"),
        ), (path, foreign.text)
        assert "Bob Secret" not in foreign.text
        assert _mentions(db, FOREIGN) == [], path

    @pytest.mark.parametrize("key", [OWN, GLOBAL])
    def test_an_own_or_global_key_is_still_accepted(self, env, path, key) -> None:
        client, _db = env

        response = _send(client, path, key)

        assert response.status_code in (200, 201), (path, key, response.text)
