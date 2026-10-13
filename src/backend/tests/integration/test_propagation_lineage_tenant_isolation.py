"""Integration test for REQ-017 SEC-B4 (a): lineage graph traversals must not
cross tenant boundaries even when a ``descended_from`` edge links two tenants.

Builds a real three-vertex chain ``pup (tenant-a) -> mother (tenant-a) ->
grandmother (tenant-b)`` and asserts every traversal (ancestors / descendants /
ancestor-paths) is pruned at the tenant boundary — the foreign grandmother is
never returned. Needs a real ArangoDB (see ``conftest.py`` for the contract).

Because every assertion here *executes* a real graph traversal, it also proves
the AQL parses — the ``PRUNE``-before-``OPTIONS`` clause order (#571). A second, static guard for the
clause order lives in ``tests/unit/data_access/test_lineage_aql_clause_order.py``,
which runs in every tier that needs no server.

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")


_DB_NAME = run_database_name("lineage_isolation")


def _plant_doc(key: str, tenant_key: str) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant_key,
        "instance_id": f"P-{key}",
        "species_key": "tomato",
        "plant_name": f"Plant {key}",
        "planted_on": "2026-01-01",
        # A sensitive field that must never leak through a lineage projection.
        "location_key": "secret-bed-7",
    }


@pytest.fixture
def repo():
    from app.config.settings import Settings
    from app.data_access.arango.collections import (
        DESCENDED_FROM,
        PLANT_INSTANCES,
        ensure_collections,
    )
    from app.data_access.arango.connection import ArangoConnection
    from app.data_access.repositories.propagation_repository import PropagationRepository

    settings = Settings(arangodb_database=_DB_NAME)
    conn = ArangoConnection(settings)
    db = conn.connect()
    ensure_collections(db)

    plants = db.collection(PLANT_INSTANCES)
    edges = db.collection(DESCENDED_FROM)
    for doc in (
        _plant_doc("pup", "tenant-a"),
        _plant_doc("mother", "tenant-a"),
        _plant_doc("grandmother", "tenant-b"),  # foreign tenant across the boundary
    ):
        plants.insert(doc, overwrite=True)
    # child -> mother edges: pup -> mother (same tenant), mother -> grandmother (cross-tenant)
    edges.insert(
        {"_key": "e_pup_mother", "_from": f"{PLANT_INSTANCES}/pup", "_to": f"{PLANT_INSTANCES}/mother"},
        overwrite=True,
    )
    edges.insert(
        {"_key": "e_mother_gm", "_from": f"{PLANT_INSTANCES}/mother", "_to": f"{PLANT_INSTANCES}/grandmother"},
        overwrite=True,
    )

    yield PropagationRepository(db)

    db_sys = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if db_sys.has_database(_DB_NAME):
        db_sys.delete_database(_DB_NAME)
    conn.close()


def test_list_ancestors_stops_at_tenant_boundary(repo) -> None:
    ancestors = repo.list_ancestors("pup", "tenant-a", max_depth=10)
    keys = {a.key for a in ancestors}

    assert keys == {"mother"}
    assert "grandmother" not in keys  # foreign vertex pruned


def test_list_ancestors_projection_omits_sensitive_fields(repo) -> None:
    ancestors = repo.list_ancestors("pup", "tenant-a", max_depth=10)

    # The hardened projection returns no location_key, only lineage-relevant fields.
    assert all(a.location_key is None for a in ancestors)


def test_trace_ancestor_paths_stops_at_tenant_boundary(repo) -> None:
    paths = repo.trace_ancestor_paths("pup", "tenant-a", max_depth=10)
    reachable = {key for path in paths for key in path}

    assert "grandmother" not in reachable
    assert reachable == {"mother"}


def test_list_descendants_stops_at_tenant_boundary(repo) -> None:
    # From the foreign grandmother's own tenant, the same-tenant clone-tree walk
    # inbound must not step into tenant-a's mother/pup.
    descendants = repo.list_descendants("grandmother", "tenant-b", max_depth=10)
    keys = {d.key for d in descendants}

    assert "mother" not in keys
    assert "pup" not in keys
