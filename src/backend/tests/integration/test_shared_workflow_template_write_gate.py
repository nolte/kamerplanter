"""#2101 (MT-003) — a shared workflow template (``tenant_key == ""``) is not edited in place.

``ActivityPlanService`` persists generated plans as shared rows (``tenant_key ""``,
``is_system False``) and every generic write guard of the tasks router looked at
``is_system`` only, so any tenant could rename, re-time or delete the plan every
tenant of that species reads. A shared plan is now forked on ``PUT`` (the same
copy the activity-plan editor makes, #1003) and refused on every other write.
Measured through the real routes against a real ArangoDB.
"""

from __future__ import annotations

import itertools

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env, put

pytestmark = pytest.mark.usefixtures("arango_db")

BASE = "/api/v1/t/bob/tasks"
_n = itertools.count()


@pytest.fixture(scope="module")
def env():
    e = open_env(
        run_database_name("shared_workflow_write_gate"), ("app.api.v1.tenant_scoped.router", "tenant_scoped_router")
    )
    yield e
    e.close()


def _plan(env, tenant: str = "") -> tuple[str, str, str]:
    """A workflow with one phase and one task template; returns their keys."""
    from app.data_access.arango import collections as col
    from app.domain.models.task import TaskTemplate, WorkflowPhase, WorkflowTemplate

    i = next(_n)
    wf, ph, tt = f"wf-{i}", f"ph-{i}", f"tt-{i}"
    put(
        env.db,
        col.WORKFLOW_TEMPLATES,
        WorkflowTemplate(_key=wf, tenant_key=tenant, name=f"Plan {i}", auto_generated=True, species_key="sp-1"),
    )
    put(env.db, col.WORKFLOW_PHASES, WorkflowPhase(_key=ph, workflow_template_key=wf, name="Phase", phase_order=1))
    put(
        env.db,
        col.TASK_TEMPLATES,
        TaskTemplate(_key=tt, tenant_key=tenant, workflow_template_key=wf, workflow_phase_key=ph, name="Water"),
    )
    return wf, ph, tt


def _doc(env, collection: str, key: str) -> dict | None:
    return env.db.collection(collection).get(key)


def test_a_put_on_a_shared_plan_forks_it_for_the_caller(env) -> None:
    wf, _, _ = _plan(env)
    env.caller.as_b()
    response = env.client.put(f"{BASE}/workflows/{wf}", json={"name": "Bobs Plan"})
    assert response.status_code == 200, response.text
    fork = response.json()
    assert fork["key"] != wf
    assert _doc(env, "workflow_templates", fork["key"])["tenant_key"] == "tenant-bob"
    shared = _doc(env, "workflow_templates", wf)
    assert shared["name"].startswith("Plan ") and shared["tenant_key"] == ""


def test_a_delete_on_a_shared_plan_is_forbidden(env) -> None:
    wf, _, _ = _plan(env)
    env.caller.as_b()
    assert env.client.delete(f"{BASE}/workflows/{wf}").status_code == 403
    assert _doc(env, "workflow_templates", wf) is not None


def test_the_phase_and_template_routes_do_not_write_into_a_shared_plan(env) -> None:
    wf, ph, tt = _plan(env)
    env.caller.as_b()
    assert env.client.put(f"{BASE}/phases/{ph}", json={"name": "Hijacked"}).status_code == 403
    assert env.client.delete(f"{BASE}/phases/{ph}").status_code == 403
    assert env.client.put(f"{BASE}/templates/{tt}", json={"name": "Hijacked"}).status_code == 403
    assert env.client.delete(f"{BASE}/templates/{tt}").status_code == 403
    assert env.client.post(f"{BASE}/workflows/{wf}/phases", json={"name": "Extra", "phase_order": 2}).status_code == 403
    assert _doc(env, "workflow_phases", ph)["name"] == "Phase"
    assert _doc(env, "task_templates", tt)["name"] == "Water"


def test_a_standalone_global_template_is_not_editable(env) -> None:
    from app.data_access.arango import collections as col
    from app.domain.models.task import TaskTemplate

    put(env.db, col.TASK_TEMPLATES, TaskTemplate(_key="tt-orphan", tenant_key="", name="Orphan"))
    env.caller.as_b()
    assert env.client.put(f"{BASE}/templates/tt-orphan", json={"name": "Hijacked"}).status_code == 403
    assert env.client.delete(f"{BASE}/templates/tt-orphan").status_code == 403
    assert _doc(env, "task_templates", "tt-orphan")["name"] == "Orphan"


def test_a_foreign_tenants_plan_is_not_found(env) -> None:
    wf, _, _ = _plan(env, "tenant-alice")
    env.caller.as_b()
    assert env.client.put(f"{BASE}/workflows/{wf}", json={"name": "Hijacked"}).status_code == 404
    assert env.client.delete(f"{BASE}/workflows/{wf}").status_code == 404


def test_the_owners_own_plan_is_still_edited_in_place(env) -> None:
    wf, ph, tt = _plan(env, "tenant-bob")
    env.caller.as_b()
    renamed = env.client.put(f"{BASE}/workflows/{wf}", json={"name": "Renamed"})
    assert renamed.status_code == 200 and renamed.json()["key"] == wf
    assert env.client.put(f"{BASE}/phases/{ph}", json={"name": "P2"}).status_code == 200
    assert env.client.put(f"{BASE}/templates/{tt}", json={"name": "T2"}).status_code == 200
    assert env.client.delete(f"{BASE}/templates/{tt}").status_code == 204
    assert env.client.delete(f"{BASE}/workflows/{wf}").status_code == 204
