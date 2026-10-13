"""MT-054 (#2144) against a real ArangoDB: companion traversals show only species the caller can see.

The unit tier pins the query shape; this pins that the AQL runs and filters:
two tenant-filtered grant subqueries in one FILTER (counts) are valid AQL, the
union admits own + global + granted and drops a foreign tenant's species, and
the system context (``None``) still reads every edge.

Fixture: a global anchor (tomato) with admin-era edges to a global basil, to
tenant A's private species and to tenant B's private species — the shape the
write path now refuses, but which a database written before #2144 may hold.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.graph_repository import ArangoGraphRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("companion_visibility")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(database)
    species = database.collection(col.SPECIES)
    for key, tenant in [("tomato", ""), ("basil", ""), ("private_a", "t-a"), ("private_b", "t-b")]:
        species.insert({"_key": key, "scientific_name": key, "scientific_name_normalized": key, "tenant_key": tenant})
    database.collection(col.TENANTS).insert({"_key": "t-a", "slug": "a", "name": "A"})
    repo = ArangoGraphRepository(database)
    # Written directly: the service refuses a tenant species since #2144, a legacy
    # database may still hold such an edge.
    for other in ("basil", "private_a", "private_b"):
        repo.set_compatibility("tomato", other, 0.8)
    repo.set_incompatibility("tomato", "private_b", "shade")
    yield database
    system.delete_database(TEST_DATABASE)


def _keys(rows: list[dict]) -> set[str]:
    return {row["species"]["_key"] for row in rows}


def test_a_tenant_sees_global_and_own_companions_only(db) -> None:
    repo = ArangoGraphRepository(db)

    assert _keys(repo.get_compatible_species("tomato", tenant_key="t-a")) == {"basil", "private_a"}
    assert _keys(repo.get_incompatible_species("tomato", tenant_key="t-a")) == set()


def test_a_granted_species_is_visible_like_in_the_species_list(db) -> None:
    db.collection(col.TENANT_HAS_ACCESS).insert({"_from": f"{col.TENANTS}/t-a", "_to": f"{col.SPECIES}/private_b"})
    try:
        repo = ArangoGraphRepository(db)
        assert "private_b" in _keys(repo.get_compatible_species("tomato", tenant_key="t-a"))
    finally:
        db.collection(col.TENANT_HAS_ACCESS).truncate()


def test_the_counts_count_only_edges_between_visible_species(db) -> None:
    counts = ArangoGraphRepository(db).get_companion_counts(tenant_key="t-a")

    # tomato -> basil, tomato -> private_a (and their reverse edges); nothing of t-b.
    assert counts["tomato"] == {"compatible": 2, "incompatible": 0}
    assert "private_b" not in counts


def test_the_system_context_reads_every_edge(db) -> None:
    repo = ArangoGraphRepository(db)

    assert _keys(repo.get_compatible_species("tomato", tenant_key=None)) == {"basil", "private_a", "private_b"}
    assert repo.get_companion_counts(tenant_key=None)["tomato"] == {"compatible": 3, "incompatible": 1}
