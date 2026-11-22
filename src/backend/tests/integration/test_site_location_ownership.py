"""#2561 (D1) — a location's ``site_key`` decides which site it belongs to; tree, top level and delete agree.

Measured against ArangoDB because the defect lived in the difference between three AQL definitions:

* the tree view walked ``1..10 OUTBOUND contains`` — a bed at depth 11 or one hanging only on its ``site_key`` was
  removed by the site delete but never shown; a re-homed bed was shown under its old site through a stale edge;
* ``update_location`` rewrote ``site_key``/``parent_location_key`` and left the ``contains`` edge where it was;
* deleting an unsited root cut the edge of a child naming a site and left its ``parent_location_key`` dangling.

The positive control in every case is the other site: its rows and edges are not touched.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Location
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("site_location_ownership")
TENANT = "ten_a"
SITE_A, SITE_B = "site_a", "site_b"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def db(database):
    for name in (col.SITES, col.LOCATIONS, col.SLOTS, col.CONTAINS, col.HAS_SLOT, col.GARDEN_PLAN_AUDIT):
        database.collection(name).truncate()
    for site in (SITE_A, SITE_B):
        database.collection(col.SITES).insert({"_key": site, "tenant_key": TENANT, "name": site, "type": "outdoor"})
    return database


@pytest.fixture
def repo(db) -> ArangoSiteRepository:
    return ArangoSiteRepository(db)


def _location(db, key: str, *, site: str = "", parent: str | None = None, depth: int = 0) -> str:
    db.collection(col.LOCATIONS).insert(
        {"_key": key, "name": key, "site_key": site, "parent_location_key": parent, "depth": depth, "area_m2": 1.0}
    )
    return f"{col.LOCATIONS}/{key}"


def _contains(db, from_id: str, to_id: str) -> None:
    db.collection(col.CONTAINS).insert({"_from": from_id, "_to": to_id})


def _contains_into(db, key: str) -> list[str]:
    return sorted(e["_from"] for e in db.collection(col.CONTAINS).find({"_to": f"{col.LOCATIONS}/{key}"}))


def _tree(repo: ArangoSiteRepository, site: str) -> set[str]:
    return {loc.key or "" for loc in repo.get_location_tree(site, tenant_key=TENANT)}


class TestTreeAndDeleteReadOneDefinition:
    def test_a_deep_bed_and_a_field_only_bed_are_shown_and_removed(self, db, repo) -> None:
        parent = _location(db, "root", site=SITE_A)
        _contains(db, f"{col.SITES}/{SITE_A}", parent)
        chain = ["root"]
        for depth in range(1, 12):  # depth 11 is beyond the old ``1..10`` traversal
            child = f"deep{depth}"
            _contains(db, parent, _location(db, child, site=SITE_A, parent=chain[-1], depth=depth))
            parent, chain = f"{col.LOCATIONS}/{child}", [*chain, child]
        _location(db, "field_only", site=SITE_A)  # no ``contains`` edge at all
        _contains(db, f"{col.SITES}/{SITE_B}", _location(db, "other", site=SITE_B))

        shown = _tree(repo, SITE_A)

        assert shown == {*chain, "field_only"}
        repo.delete_site(SITE_A, tenant_key=TENANT, user_key="u1")
        assert {doc["_key"] for doc in db.collection(col.LOCATIONS).all()} == {"other"}

    def test_a_foreign_tenant_sees_no_tree(self, db, repo) -> None:
        _location(db, "bed", site=SITE_A)

        assert repo.get_location_tree(SITE_A, tenant_key="ten_other") == []


class TestReHomingABedMovesItsEdge:
    def test_update_location_moves_the_contains_edge_to_the_new_site(self, db, repo) -> None:
        created = repo.create_location(Location(name="bed", site_key=SITE_A, area_m2=1.0))
        key = created.key or ""
        assert _contains_into(db, key) == [f"{col.SITES}/{SITE_A}"]

        moved = Location(name="bed", site_key=SITE_B, area_m2=1.0)
        repo.update_location(key, moved, untouched=())

        assert _contains_into(db, key) == [f"{col.SITES}/{SITE_B}"]
        assert key not in _tree(repo, SITE_A)
        assert key in _tree(repo, SITE_B)
        assert [loc.key for loc in repo.get_locations_by_site(SITE_B)] == [key]
        assert repo.get_locations_by_site(SITE_A) == []

    def test_update_location_moves_the_edge_to_a_new_parent(self, db, repo) -> None:
        first = repo.create_location(Location(name="first", site_key=SITE_A, area_m2=1.0)).key or ""
        second = repo.create_location(Location(name="second", site_key=SITE_A, area_m2=1.0)).key or ""
        bed = repo.create_location(Location(name="bed", site_key=SITE_A, parent_location_key=first, area_m2=1.0))
        bed_key = bed.key or ""

        repo.update_location(
            bed_key, Location(name="bed", site_key=SITE_A, parent_location_key=second, area_m2=1.0), untouched=()
        )

        assert _contains_into(db, bed_key) == [f"{col.LOCATIONS}/{second}"]
        assert [loc.key for loc in repo.get_location_children(first)] == []

    def test_an_unchanged_placement_keeps_its_edge(self, db, repo) -> None:
        key = repo.create_location(Location(name="bed", site_key=SITE_A, area_m2=1.0)).key or ""
        edge_ids = [e["_id"] for e in db.collection(col.CONTAINS).all()]

        repo.update_location(key, Location(name="renamed", site_key=SITE_A, area_m2=2.0), untouched=())

        assert [e["_id"] for e in db.collection(col.CONTAINS).all()] == edge_ids

    def test_a_bed_re_homed_before_the_fix_is_neither_shown_nor_removed_with_its_old_site(self, db, repo) -> None:
        # The pre-#2561 shape: the field names B, the stale edge still comes from A.
        _contains(db, f"{col.SITES}/{SITE_A}", _location(db, "rehomed", site=SITE_B))
        _contains(db, f"{col.SITES}/{SITE_A}", _location(db, "stays_a", site=SITE_A))

        assert _tree(repo, SITE_A) == {"stays_a"}
        assert _tree(repo, SITE_B) == {"rehomed"}
        assert [loc.key for loc in repo.get_locations_by_site(SITE_A)] == ["stays_a"]

        repo.delete_site(SITE_A, tenant_key=TENANT, user_key="u1")

        assert db.collection(col.LOCATIONS).get("rehomed") is not None
        assert _contains_into(db, "rehomed") == []  # the stale edge went with site A


class TestDeletingAParentSettlesASurvivingChild:
    def test_a_child_naming_a_site_survives_an_unsited_root_as_a_root_of_its_site(self, db, repo) -> None:
        root = _location(db, "unsited_root")
        _contains(db, root, _location(db, "unsited_child", parent="unsited_root", depth=1))
        _contains(db, root, _location(db, "sited_child", site=SITE_B, parent="unsited_root", depth=1))

        assert repo.delete_location("unsited_root") is True

        assert db.collection(col.LOCATIONS).get("unsited_child") is None
        survivor = db.collection(col.LOCATIONS).get("sited_child")
        assert survivor is not None
        assert survivor.get("parent_location_key") is None
        assert survivor["depth"] == 0
        assert _contains_into(db, "sited_child") == [f"{col.SITES}/{SITE_B}"]
        assert "sited_child" in _tree(repo, SITE_B)
