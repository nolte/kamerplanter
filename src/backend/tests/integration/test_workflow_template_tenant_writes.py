"""#2027 review — tenant workflow writes through the real routes, and the seed boot beside them.

Run through the **real routes, DI factories, services, repositories and error handler**
against a real ArangoDB; only the caller's identity is overridden. Two tenants act
through the same client, switched per request. Covered here:

* **SEC-A** — the seed's task-template cleanup grouped every task template of the
  installation by ``(name, workflow_template_key)`` and deleted all but one per group at
  every boot: two tenants' standalone "Gießen" (no workflow, so one group) lost one, and
  a tenant's second "Gießen" (day 10 beside day 3) in its own workflow was deleted. It now
  touches only global duplicates of a seed task template under its seed workflow — which
  it still removes.
* **SEC-B** — ``is_system`` was accepted on create: the row was then locked against
  its owner and kept by the tenant erasure.
* **SEC-C** — a name collision inside one tenant (create, rename, duplicate, fork) was a
  raw driver error and a 500; it is a ``409 DUPLICATE_ENTRY`` naming the field.
* **The copy-on-write fork** (#1003) with the ``(tenant_key, name)`` index of v0077: the
  fork keeps the shared plan's name, which the old collection-wide ``name`` index refused.
* A workflow name listed twice in the seed YAML updates the row just created.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the routes and the seed write workflow rows to a real server"),
]

_DB_NAME = run_database_name("workflow_template_tenant_writes")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUGS = {TENANT_A: "alice", TENANT_B: "bob"}
WATERING = "Gießen"


@pytest.fixture
def env() -> Iterator[tuple[Any, Any, dict[str, str]]]:
    """The real tenant router over a throwaway database; ``acting["tenant"]`` picks the caller."""
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


def _call(client: Any, acting: dict[str, str], tenant: str, method: str, path: str, **kwargs: Any) -> Any:
    acting["tenant"] = tenant
    return client.request(method, f"/api/v1/t/{SLUGS[tenant]}{path}", **kwargs)


def _created(response: Any) -> str:
    assert response.status_code == 201, response.text
    return str(response.json()["key"])


def _assert_duplicate_on_name(response: Any, *foreign: str) -> None:
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["error_code"] == "DUPLICATE_ENTRY", response.text
    assert body["details"][0]["field"] == "name", response.text
    for value in foreign:
        assert value not in response.text, f"the 409 names {value!r} of another tenant: {response.text}"


# ── SEC-A: the seed cleanup never deletes a tenant's task template ──────────


def test_tenant_task_templates_survive_a_seed_boot(env) -> None:
    from app.migrations.seed_data import run_seed

    client, db, acting = env
    standalone_a = _created(_call(client, acting, TENANT_A, "POST", "/tasks/templates", json={"name": WATERING}))
    standalone_b = _created(_call(client, acting, TENANT_B, "POST", "/tasks/templates", json={"name": WATERING}))
    own_wf = _created(_call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": "Mein Plan"}))
    day_3 = _created(
        _call(
            client,
            acting,
            TENANT_A,
            "POST",
            "/tasks/templates",
            json={"name": WATERING, "days_offset": 3, "workflow_template_key": own_wf},
        )
    )
    day_10 = _created(
        _call(
            client,
            acting,
            TENANT_A,
            "POST",
            "/tasks/templates",
            json={"name": WATERING, "days_offset": 10, "workflow_template_key": own_wf},
        )
    )
    planted = [standalone_a, standalone_b, day_3, day_10]
    before = [db.collection("task_templates").get(key) for key in planted]

    run_seed()

    assert [db.collection("task_templates").get(key) for key in planted] == before


def test_a_duplicate_of_a_seed_task_template_is_still_removed(env) -> None:
    from app.migrations.seed_data import remove_duplicate_seed_task_templates, run_seed
    from app.migrations.yaml_loader import load_yaml

    _client, db, _acting = env
    run_seed()
    seed = load_yaml("workflows.yaml")["task_templates"][0]
    (wf,) = db.aql.execute(
        'FOR w IN workflow_templates FILTER w.name == @n AND (w.tenant_key == "" OR w.tenant_key == null) RETURN w',
        bind_vars={"n": seed["workflow_name"]},
    )
    (original,) = db.aql.execute(
        "FOR t IN task_templates FILTER t.workflow_template_key == @k AND t.name == @n RETURN t",
        bind_vars={"k": wf["_key"], "n": seed["name"]},
    )
    copy = {k: v for k, v in original.items() if k not in ("_key", "_id", "_rev")}
    duplicate = db.collection("task_templates").insert(copy)["_key"]

    removed = remove_duplicate_seed_task_templates(db, load_yaml("workflows.yaml"))

    assert removed == [duplicate]
    assert db.collection("task_templates").get(original["_key"]) is not None
    assert db.collection("task_templates").get(duplicate) is None


# ── SEC-B: a tenant cannot create a system workflow ─────────────────────────


def test_is_system_from_a_tenant_is_ignored_and_the_row_stays_editable(env) -> None:
    client, db, acting = env
    key = _created(
        _call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": "Systemplan", "is_system": True})
    )

    assert db.collection("workflow_templates").get(key)["is_system"] is False
    renamed = _call(client, acting, TENANT_A, "PUT", f"/tasks/workflows/{key}", json={"name": "Mein Systemplan"})
    assert renamed.status_code == 200, renamed.text
    deleted = _call(client, acting, TENANT_A, "DELETE", f"/tasks/workflows/{key}")
    assert deleted.status_code == 204, deleted.text


# ── SEC-C: a name collision inside one tenant is a 409, not a 500 ───────────


def test_a_tenant_reusing_its_own_workflow_name_gets_a_409(env) -> None:
    client, _db, acting = env
    foreign = _created(_call(client, acting, TENANT_B, "POST", "/tasks/workflows", json={"name": "Plan"}))
    _created(_call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": "Plan"}))
    other = _created(_call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": "Anderer Plan"}))

    _assert_duplicate_on_name(
        _call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": "Plan"}), TENANT_B, foreign
    )
    _assert_duplicate_on_name(
        _call(client, acting, TENANT_A, "PUT", f"/tasks/workflows/{other}", json={"name": "Plan"}), TENANT_B, foreign
    )
    _assert_duplicate_on_name(
        _call(client, acting, TENANT_A, "POST", f"/tasks/workflows/{other}/duplicate", params={"name": "Plan"}),
        TENANT_B,
        foreign,
    )


# ── The copy-on-write fork keeps the shared plan's name, per tenant ─────────


def _shared_generated_plan(db: Any, name: str = "Tomate – Aktivitätsplan") -> tuple[str, str]:
    """A global generated plan as ``ActivityPlanService`` persists it, with one task template."""
    plan = db.collection("workflow_templates").insert(
        {
            "name": name,
            "tenant_key": "",
            "is_system": False,
            "auto_generated": True,
            "species_key": "species-tomato",
            "target_entity_types": ["plant_instance"],
        }
    )["_key"]
    template = db.collection("task_templates").insert(
        {
            "name": WATERING,
            "tenant_key": "",
            "workflow_template_key": plan,
            "days_offset": 3,
            "trigger_type": "manual",
            "category": "maintenance",
        }
    )["_key"]
    return plan, template


def _plans_named(db: Any, name: str) -> list[str]:
    return sorted(
        db.aql.execute("FOR w IN workflow_templates FILTER w.name == @n RETURN w.tenant_key", bind_vars={"n": name})
    )


def test_two_tenants_fork_the_same_shared_plan_and_a_second_edit_reuses_the_copy(env) -> None:
    client, db, acting = env
    plan, template = _shared_generated_plan(db)
    shared_before = db.collection("task_templates").get(template)
    name = db.collection("workflow_templates").get(plan)["name"]

    for tenant, days in ((TENANT_A, 5), (TENANT_B, 7), (TENANT_A, 9)):
        edit = _call(
            client, acting, tenant, "PATCH", f"/activity-plans/templates/{template}", json={"days_offset": days}
        )
        assert edit.status_code == 200, edit.text
        assert edit.json()["days_offset"] == days

    assert _plans_named(db, name) == ["", TENANT_A, TENANT_B]
    assert db.collection("task_templates").get(template) == shared_before


def test_a_fork_onto_a_name_the_tenant_already_holds_is_a_409(env) -> None:
    client, db, acting = env
    plan, template = _shared_generated_plan(db)
    name = db.collection("workflow_templates").get(plan)["name"]
    _created(_call(client, acting, TENANT_A, "POST", "/tasks/workflows", json={"name": name}))

    edit = _call(client, acting, TENANT_A, "PATCH", f"/activity-plans/templates/{template}", json={"days_offset": 5})

    _assert_duplicate_on_name(edit)


# ── A workflow name the YAML lists twice ────────────────────────────────────


def test_a_workflow_name_listed_twice_in_the_seed_updates_the_row_just_created(env, monkeypatch) -> None:
    from app.migrations import seed_data
    from app.migrations.yaml_loader import load_yaml

    _client, db, _acting = env
    data = load_yaml("workflows.yaml")
    first = data["workflow_templates"][0]
    data["workflow_templates"].append({**first, "description": "listed twice"})
    monkeypatch.setattr(seed_data, "_load_workflow_data", lambda: data)

    seed_data.run_seed()

    rows = list(
        db.aql.execute(
            'FOR w IN workflow_templates FILTER w.name == @n AND w.tenant_key == "" RETURN w',
            bind_vars={"n": first["name"]},
        )
    )
    assert [row["description"] for row in rows] == ["listed twice"]
