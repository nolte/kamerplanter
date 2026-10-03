"""#2029 — a tank name is unique per tenant, and a 409 names nothing of another tenant.

``tanks`` carried a collection-wide unique index on ``name``. Tenant B creating a
tank named like one of tenant A's was refused with ``409 DUPLICATE_ENTRY`` — the
refusal itself told B that some other tenant holds a tank of that name, and denied
B the name. The identity is now ``(tenant_key, name)``.

Run through the **real route, DI factory, service, repository and error handler**
against a real ArangoDB; only the caller's identity is overridden. Both tenants act
through the same client, switched per request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the route writes tanks to a real server"),
]

_DB_NAME = run_database_name("tank_name_tenant_scope")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUGS = {TENANT_A: "alice", TENANT_B: "bob"}
NAME = "Tank 1"


@pytest.fixture
def env() -> Iterator[tuple[Any, Any, dict[str, str]]]:
    """The real tank router over a throwaway database; ``acting["tenant"]`` picks the caller."""
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


def _create(client: Any, acting: dict[str, str], tenant: str, name: str = NAME) -> Any:
    acting["tenant"] = tenant
    return client.post(
        f"/api/v1/t/{SLUGS[tenant]}/tanks",
        json={"name": name, "tank_type": "nutrient", "volume_liters": 50},
    )


def test_two_tenants_can_each_name_a_tank_the_same(env) -> None:
    client, db, acting = env

    first = _create(client, acting, TENANT_A)
    second = _create(client, acting, TENANT_B)

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    owners = sorted(d["tenant_key"] for d in db.collection("tanks").find({"name": NAME}))
    assert owners == [TENANT_A, TENANT_B]


def test_the_same_tenant_is_still_refused_and_the_409_names_no_other_tenant(env) -> None:
    client, _db, acting = env
    other = _create(client, acting, TENANT_B)
    assert other.status_code == 201, other.text
    own = _create(client, acting, TENANT_A)
    assert own.status_code == 201, own.text

    again = _create(client, acting, TENANT_A)

    assert again.status_code == 409, again.text
    body = again.json()
    assert body["error_code"] == "DUPLICATE_ENTRY"
    text = again.text
    for foreign in (TENANT_B, SLUGS[TENANT_B], other.json()["key"]):
        assert foreign not in text, f"the 409 names {foreign!r} of the other tenant: {text}"
    # The conflicting field is the name, not the tenant scope of the index: the
    # client maps ``details[].field`` onto its form, and the internal tenant key
    # is nothing the caller sent.
    assert body["details"][0]["field"] == "name", text
    assert f"name='{NAME}'" in body["message"], text
    assert TENANT_A not in text, text
