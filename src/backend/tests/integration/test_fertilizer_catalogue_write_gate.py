"""#2100 (MT-002) — a global seed fertilizer is written only by a platform admin.

``update_fertilizer`` / ``delete_fertilizer`` reloaded the row without a tenant and
knew neither its owner nor a platform admin, so any grower of any tenant could change
the NPK, ``mixing_priority`` or EC of a shared seed product — or delete it, taking
every tenant's stocks with it. Four arms, measured through the real route against a
real ArangoDB (the model is ``substrate_service._authorize_write``):

* a **foreign** tenant's product is 404 — ownership hiding;
* a **global** product is a platform admin's;
* an **own** product needs a writing role (delete: lead only, the REQ-049 §2.3 rule);
* ownership is frozen: an update cannot re-stamp the row.
"""

from __future__ import annotations

import itertools

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env, put

pytestmark = pytest.mark.usefixtures("arango_db")

BASE = "/api/v1/t/alice/fertilizers"
_counter = itertools.count()


@pytest.fixture(scope="module")
def env():
    e = open_env(run_database_name("fert_write_gate"), ("app.api.v1.tenant_scoped.router", "tenant_scoped_router"))
    yield e
    e.close()


def _row(env, tenant: str) -> str:
    """A fresh fertilizer owned by ``tenant`` (``""`` = global seed) and its key."""
    from app.data_access.arango import collections as col
    from app.domain.models.fertilizer import Fertilizer

    key = f"fert-{next(_counter)}"
    put(
        env.db,
        col.FERTILIZERS,
        Fertilizer(
            _key=key, tenant_key=tenant, product_name=f"Original-{key}", fertilizer_type="base", mixing_priority=5
        ),
    )
    return key


def _stored(env, key: str) -> dict | None:
    return env.db.collection("fertilizers").get(key)


def test_a_grower_cannot_update_a_global_fertilizer(env) -> None:
    key = _row(env, "")
    env.caller.as_a("grower")
    response = env.client.put(f"{BASE}/{key}", json={"product_name": "Hijacked", "mixing_priority": 1})
    assert response.status_code == 403, response.text
    assert _stored(env, key)["product_name"] == f"Original-{key}"
    assert _stored(env, key)["mixing_priority"] == 5


def test_a_tenant_lead_cannot_update_or_delete_a_global_fertilizer(env) -> None:
    key = _row(env, "")
    env.caller.as_a("lead")
    assert env.client.put(f"{BASE}/{key}", json={"product_name": "Hijacked"}).status_code == 403
    assert env.client.delete(f"{BASE}/{key}").status_code == 403
    assert _stored(env, key)["product_name"] == f"Original-{key}"


def test_a_platform_admin_can_update_and_delete_a_global_fertilizer(env) -> None:
    key = _row(env, "")
    # The tenant role gate (REQ-049 §2.3) still runs first; the platform admin of the
    # catalogue acts in a tenant they can write in.
    env.caller.as_a("lead", platform_admin=True)
    updated = env.client.put(f"{BASE}/{key}", json={"product_name": "Curated"})
    assert updated.status_code == 200, updated.text
    assert _stored(env, key)["product_name"] == "Curated"
    assert _stored(env, key)["tenant_key"] == ""
    assert env.client.delete(f"{BASE}/{key}").status_code == 204
    assert _stored(env, key) is None


def test_a_foreign_tenants_fertilizer_is_not_found(env) -> None:
    key = _row(env, "tenant-bob")
    env.caller.as_a("lead")
    assert env.client.put(f"{BASE}/{key}", json={"product_name": "Hijacked"}).status_code == 404
    assert env.client.delete(f"{BASE}/{key}").status_code == 404
    assert _stored(env, key)["product_name"] == f"Original-{key}"


def test_a_platform_admin_does_not_reach_a_private_foreign_fertilizer(env) -> None:
    key = _row(env, "tenant-bob")
    env.caller.as_a("lead", platform_admin=True)
    assert env.client.put(f"{BASE}/{key}", json={"product_name": "Hijacked"}).status_code == 404
    assert _stored(env, key)["product_name"] == f"Original-{key}"


def test_the_owner_still_edits_and_deletes_its_own_fertilizer(env) -> None:
    key = _row(env, "tenant-alice")
    env.caller.as_a("grower")
    assert env.client.put(f"{BASE}/{key}", json={"product_name": "Mine"}).status_code == 200
    assert _stored(env, key)["product_name"] == "Mine"
    assert _stored(env, key)["tenant_key"] == "tenant-alice"
    assert env.client.delete(f"{BASE}/{key}").status_code == 403  # lead-only delete
    env.caller.as_a("lead")
    assert env.client.delete(f"{BASE}/{key}").status_code == 204
    assert _stored(env, key) is None
