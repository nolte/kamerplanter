"""#2120 (MT-024 §5) — equipment, actuators and print, probed with another tenant's keys.

The audit counted the cross-tenant tests per area: equipment **0**, actuators **1**,
export/print **unit only**. Each handler there resolves its document through the
service under ``ctx.tenant_key`` (``verify_tenant_ownership``), so these are not
fixes — they are the permanent negative probes the other areas already have,
through the **real** routers, services and repositories against a real ArangoDB.

Every probe is pinned in both directions: tenant B's key answers **404** to tenant A
(never 403 — that would confirm the key exists elsewhere) and B's row is left
unchanged, while the same request with A's own key succeeds. A guard that refused
everything would fail the second half; one that admitted everything the first.
"""

from __future__ import annotations

import pytest

from app.common.enums import AdminScope, TenantRole
from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import TENANT_A, TENANT_B, open_env, put

pytestmark = pytest.mark.usefixtures("arango_db")

BASE = "/api/v1/t/alice"


@pytest.fixture(scope="module")
def env():
    from app.common.auth import get_current_tenant
    from app.data_access.arango import collections as col
    from app.domain.models.actuator import Actuator
    from app.domain.models.inventree import Equipment
    from app.domain.models.nutrient_plan import NutrientPlan
    from app.domain.models.site import Location, Site
    from app.domain.models.tenant_context import TenantContext

    e = open_env(run_database_name("xt_equipment"), ("app.api.v1.tenant_scoped.router", "tenant_scoped_router"))
    # Actuator writes need the technical administrative scope (REQ-049 §2.4); the
    # harness context carries none, so the caller gets it here — the probe is about
    # ownership, and a 403 for a missing scope would hide whether ownership held.
    caller = e.caller
    e.client.app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=caller.tenant_key,
        tenant_slug=caller.slug,
        user_key=caller.user_key,
        role=TenantRole(caller.role),
        admin_scopes=[AdminScope.TECHNICAL, AdminScope.MANAGEMENT],
    )
    for tenant, suffix in ((TENANT_A, "a"), (TENANT_B, "b")):
        put(e.db, col.SITES, Site(_key=f"site-{suffix}", tenant_key=tenant, name=f"Site {suffix}", type="indoor"))
        put(
            e.db,
            col.LOCATIONS,
            Location(_key=f"loc-{suffix}", name=f"Loc {suffix}", site_key=f"site-{suffix}", area_m2=1),
        )
        put(
            e.db,
            col.EQUIPMENT,
            Equipment(_key=f"eq-{suffix}", tenant_key=tenant, name=f"Pump {suffix}", equipment_type="tool"),
        )
        put(
            e.db,
            col.ACTUATORS,
            Actuator(
                _key=f"act-{suffix}",
                tenant_key=tenant,
                location_key=f"loc-{suffix}",
                name=f"Light {suffix}",
                actuator_type="light",
                protocol="manual",
            ),
        )
        put(e.db, col.NUTRIENT_PLANS, NutrientPlan(_key=f"plan-{suffix}", tenant_key=tenant, name=f"Plan {suffix}"))
    yield e
    e.close()


@pytest.fixture(autouse=True)
def _as_lead_of_a(env) -> None:
    env.caller.as_a("lead")


# ── Equipment (REQ-016) ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/equipment/{key}", None),
        ("put", "/equipment/{key}", {"name": "Hijacked"}),
        ("delete", "/equipment/{key}", None),
    ],
)
def test_foreign_equipment_is_not_found_and_own_equipment_is(env, method: str, path: str, body) -> None:
    kwargs = {"json": body} if body is not None else {}

    foreign = getattr(env.client, method)(BASE + path.format(key="eq-b"), **kwargs)
    assert foreign.status_code == 404, foreign.text
    stored = env.db.collection("equipment").get("eq-b")
    assert stored is not None and stored["name"] == "Pump b"

    if method != "delete":
        own = getattr(env.client, method)(BASE + path.format(key="eq-a"), **kwargs)
        assert own.status_code == 200, own.text


def test_the_equipment_list_shows_only_own_items(env) -> None:
    response = env.client.get(f"{BASE}/equipment")
    assert response.status_code == 200, response.text
    assert {item["key"] for item in response.json()} == {"eq-a"}


def test_equipment_cannot_be_moved_into_a_foreign_location(env) -> None:
    response = env.client.put(f"{BASE}/equipment/eq-a", json={"location_key": "loc-b"})
    assert response.status_code == 404, response.text
    assert env.db.collection("equipment").get("eq-a").get("location_key") in (None, "")


# ── Actuators (REQ-018) ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/actuators/{key}", None),
        ("get", "/actuators/{key}/state", None),
        ("get", "/actuators/{key}/schedules", None),
        ("get", "/actuators/{key}/rules", None),
        ("put", "/actuators/{key}", {"name": "Hijacked"}),
        ("delete", "/actuators/{key}", None),
    ],
)
def test_a_foreign_actuator_is_not_found_and_an_own_one_is(env, method: str, path: str, body) -> None:
    kwargs = {"json": body} if body is not None else {}

    foreign = getattr(env.client, method)(BASE + path.format(key="act-b"), **kwargs)
    assert foreign.status_code == 404, foreign.text
    stored = env.db.collection("actuators").get("act-b")
    assert stored is not None and stored["name"] == "Light b"

    if method != "delete":
        own = getattr(env.client, method)(BASE + path.format(key="act-a"), **kwargs)
        assert own.status_code == 200, own.text


def test_an_actuator_cannot_be_created_in_a_foreign_location(env) -> None:
    body = {"name": "Planted", "actuator_type": "light", "protocol": "manual"}
    response = env.client.post(f"{BASE}/locations/loc-b/actuators", json=body)
    assert response.status_code == 404, response.text
    assert env.db.collection("actuators").find({"name": "Planted"}).count() == 0


def test_the_actuator_list_shows_only_own_items(env) -> None:
    response = env.client.get(f"{BASE}/actuators")
    assert response.status_code == 200, response.text
    assert {item.get("key") or item.get("_key") for item in response.json()} == {"act-a"}


# ── Print / export (REQ-019) ─────────────────────────────────────────────────


def test_a_foreign_nutrient_plan_cannot_be_printed(env) -> None:
    foreign = env.client.get(f"{BASE}/print/nutrient-plan/plan-b")
    assert foreign.status_code == 404, foreign.text
    assert b"Plan b" not in foreign.content

    own = env.client.get(f"{BASE}/print/nutrient-plan/plan-a")
    assert own.status_code == 200, own.text
    assert own.headers["content-type"] == "application/pdf"
