"""#2513 — deleting a site removes its structure and keeps its history, atomically, against a real ArangoDB.

What no double can decide, measured here:

* the locations go at every depth — the ``contains`` tree below the site (a nested location need not carry
  ``site_key``) **and** a location that names the site without hanging under it;
* slots, garden objects, irrigation zones and the five site-keyed dependents (season state, forecasts, climate
  normals, weather-source config, irrigation demands) go; a dependent stamped with another tenant does not, whatever
  its ``site_key`` says;
* no edge of any collection the graph lets end at a removed vertex survives on one — the edge set is derived here
  from the graph definitions, independently of the repository's own write set;
* ``care_events`` and the earlier ``garden_plan_audit`` rows stay (REQ-053 GP-FR-101, §20.13 SR-011), and exactly one
  new audit row records the delete;
* every other row and edge is byte-identical afterwards — tenant B's site of the same shape is the positive control;
* a failure after the first write leaves the database as it was (one stream transaction);
* a plant not yet removed on the site, one of its locations or one of their slots refuses the whole delete with
  409 ``site.has_active_plants`` and nothing is written; a removed plant and another tenant's plant never block (WP-3).
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.site_repository import ArangoSiteRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("site_delete_cascade")
A, B = "ten_a", "ten_b"

#: Vertex collections whose rows the delete removes; the edges checked are derived from these.
_REMOVED_VERTEX_COLLECTIONS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.GARDEN_OBJECTS,
    col.IRRIGATION_ZONES,
    col.SEASON_STATES,
    col.WEATHER_FORECASTS,
    col.CLIMATE_NORMALS,
    col.WEATHER_SOURCE_CONFIGS,
    col.IRRIGATION_DEMANDS,
)
_EDGE_COLLECTIONS = tuple(
    dict.fromkeys(edge for name in _REMOVED_VERTEX_COLLECTIONS for edge, _ in edges_touching(name))
)
_DOCUMENT_COLLECTIONS = (*_REMOVED_VERTEX_COLLECTIONS, col.CARE_EVENTS, col.GARDEN_PLAN_AUDIT, col.PLANT_INSTANCES)


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


def _edge(db, edge: str, from_id: str, to_id: str) -> None:
    db.collection(edge).insert({"_from": from_id, "_to": to_id})


def _seed_site(db, site: str, tenant: str) -> dict[str, list[str]]:
    """One site of every shape the delete has to handle; returns the ids that must go and those that must stay."""
    s = site
    site_id = f"{col.SITES}/{s}"
    db.collection(col.SITES).insert(
        {
            "_key": s,
            "tenant_key": tenant,
            "name": f"Garden {s}",
            "type": "outdoor",
            "timezone": "UTC",
            "plan": {"plan_revision": 3},
        }
    )
    _edge(db, col.BELONGS_TO_TENANT, site_id, f"{col.TENANTS}/{tenant}")
    _edge(db, col.LOCATED_AT, f"{col.SENSORS}/sensor_{s}", site_id)

    bed, child, loose = f"bed_{s}", f"child_{s}", f"loose_{s}"
    db.collection(col.LOCATIONS).insert({"_key": bed, "site_key": s, "name": bed})
    # Nested under the bed and carrying no ``site_key``: reachable only through the ``contains`` tree.
    db.collection(col.LOCATIONS).insert({"_key": child, "parent_location_key": bed, "name": child})
    # Names the site but hangs under nothing: reachable only through ``site_key``.
    db.collection(col.LOCATIONS).insert({"_key": loose, "site_key": s, "name": loose})
    _edge(db, col.CONTAINS, site_id, f"{col.LOCATIONS}/{bed}")
    _edge(db, col.CONTAINS, f"{col.LOCATIONS}/{bed}", f"{col.LOCATIONS}/{child}")
    _edge(db, col.RUN_AT_LOCATION, f"{col.PLANTING_RUNS}/run_{s}", f"{col.LOCATIONS}/{child}")
    _edge(db, col.LOCATED_AT, f"{col.SENSORS}/sensor_{s}", f"{col.LOCATIONS}/{loose}")

    slot = f"slot_{s}"
    db.collection(col.SLOTS).insert({"_key": slot, "slot_id": "A1", "location_key": child})
    _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/{child}", f"{col.SLOTS}/{slot}")
    _edge(db, col.PLACED_IN, f"{col.PLANT_INSTANCES}/plant_{s}", f"{col.SLOTS}/{slot}")

    obj = f"obj_{s}"
    db.collection(col.GARDEN_OBJECTS).insert({"_key": obj, "site_key": s, "object_type": "water_source"})
    _edge(db, col.HAS_GARDEN_OBJECT, site_id, f"{col.GARDEN_OBJECTS}/{obj}")

    zone = f"zone_{s}"
    db.collection(col.IRRIGATION_ZONES).insert({"_key": zone, "tenant_key": tenant, "site_key": s, "name": zone})
    _edge(db, col.HAS_IRRIGATION_ZONE, site_id, f"{col.IRRIGATION_ZONES}/{zone}")
    _edge(db, col.ZONE_COVERS, f"{col.IRRIGATION_ZONES}/{zone}", f"{col.LOCATIONS}/{child}")
    _edge(db, col.ZONE_SUPPLIED_BY, f"{col.IRRIGATION_ZONES}/{zone}", f"{col.GARDEN_OBJECTS}/{obj}")
    # Edges whose only removed endpoint is the zone: cut by the zone's own edge set, by nothing else.
    _edge(db, col.ZONE_ACTUATED_BY, f"{col.IRRIGATION_ZONES}/{zone}", f"{col.ACTUATORS}/valve_{s}")
    _edge(db, col.BELONGS_TO_TENANT, f"{col.IRRIGATION_ZONES}/{zone}", f"{col.TENANTS}/{tenant}")

    dependents = (
        (col.SEASON_STATES, col.HAS_SEASON_STATE),
        (col.WEATHER_FORECASTS, col.HAS_FORECAST),
        (col.CLIMATE_NORMALS, col.HAS_CLIMATE_NORMAL),
        (col.WEATHER_SOURCE_CONFIGS, col.HAS_WEATHER_SOURCE_CONFIG),
        (col.IRRIGATION_DEMANDS, col.HAS_IRRIGATION_DEMAND),
    )
    gone = [
        site_id,
        f"{col.LOCATIONS}/{bed}",
        f"{col.LOCATIONS}/{child}",
        f"{col.LOCATIONS}/{loose}",
        f"{col.SLOTS}/{slot}",
        f"{col.GARDEN_OBJECTS}/{obj}",
        f"{col.IRRIGATION_ZONES}/{zone}",
    ]
    for collection, edge in dependents:
        key = f"{collection}_{s}"
        db.collection(collection).insert({"_key": key, "site_key": s, "tenant_key": tenant})
        _edge(db, edge, site_id, f"{collection}/{key}")
        gone.append(f"{collection}/{key}")
    # An unstamped dependent (``tenant_key`` defaults to ``""``) belongs to the site that names it.
    db.collection(col.WEATHER_FORECASTS).insert({"_key": f"unstamped_{s}", "site_key": s, "tenant_key": ""})
    gone.append(f"{col.WEATHER_FORECASTS}/unstamped_{s}")
    _edge(
        db, col.DEMAND_FOR_RUN, f"{col.PLANTING_RUNS}/run_{s}", f"{col.IRRIGATION_DEMANDS}/{col.IRRIGATION_DEMANDS}_{s}"
    )

    care = f"care_{s}"
    db.collection(col.CARE_EVENTS).insert(
        {"_key": care, "tenant_key": tenant, "site_key": s, "location_key": child, "category": "watering"}
    )
    _edge(db, col.CARE_EVENT_AT, f"{col.CARE_EVENTS}/{care}", f"{col.LOCATIONS}/{child}")
    _edge(db, col.BELONGS_TO_TENANT, f"{col.CARE_EVENTS}/{care}", f"{col.TENANTS}/{tenant}")
    audit = f"audit_{s}"
    db.collection(col.GARDEN_PLAN_AUDIT).insert(
        {
            "_key": audit,
            "tenant_key": tenant,
            "site_key": s,
            "revision": 3,
            "user_key": "u0",
            "op": "delete",
            "entity": "location",
            "key": "old_bed",
            "summary": "old bed",
            "at": "2026-10-01T00:00:00+00:00",
        }
    )
    return {"gone": gone, "kept": [f"{col.CARE_EVENTS}/{care}", f"{col.GARDEN_PLAN_AUDIT}/{audit}"]}


@pytest.fixture
def db(database):
    for name in (*_DOCUMENT_COLLECTIONS, *_EDGE_COLLECTIONS):
        database.collection(name).truncate()
    return database


@pytest.fixture
def seeded(db) -> dict[str, dict[str, list[str]]]:
    seeds = {"site_a": _seed_site(db, "site_a", A), "site_b": _seed_site(db, "site_b", B)}
    # Names site_a but is stamped with tenant B: never taken by site_a's delete.
    db.collection(col.SEASON_STATES).insert({"_key": "foreign_claim", "site_key": "site_a", "tenant_key": B})
    return seeds


def _documents(db) -> dict[str, dict[str, Any]]:
    return {doc["_id"]: doc for name in _DOCUMENT_COLLECTIONS for doc in db.collection(name).all()}


def _edges(db) -> dict[str, dict[str, Any]]:
    return {doc["_id"]: doc for name in _EDGE_COLLECTIONS for doc in db.collection(name).all()}


def _audit_rows_beyond(db, known: set[str]) -> list[dict[str, Any]]:
    return [doc for doc in db.collection(col.GARDEN_PLAN_AUDIT).all() if doc["_id"] not in known]


class TestDeletingASiteRemovesItsStructureAndKeepsItsHistory:
    def test_the_structure_goes_and_nothing_else_changes(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)
        gone = set(seeded["site_a"]["gone"])
        assert gone <= set(documents)  # the seed holds what the assertions below claim is removed

        assert ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1") is True

        after = _documents(db)
        new_rows = [doc_id for doc_id in after if doc_id not in documents]
        assert {doc_id: doc for doc_id, doc in after.items() if doc_id not in new_rows} == {
            doc_id: doc for doc_id, doc in documents.items() if doc_id not in gone
        }
        # Every surviving edge is one that touched no removed vertex, unchanged; every such edge survives.
        assert _edges(db) == {
            edge_id: edge for edge_id, edge in edges.items() if edge["_from"] not in gone and edge["_to"] not in gone
        }

    def test_no_edge_of_a_derived_collection_points_at_a_removed_vertex(self, db, seeded) -> None:
        gone = seeded["site_a"]["gone"]
        touching_before = sum(
            len(
                list(
                    db.aql.execute(
                        "FOR e IN @@edge FILTER e._from IN @ids OR e._to IN @ids RETURN 1",
                        bind_vars={"@edge": edge, "ids": gone},
                    )
                )
            )
            for edge in _EDGE_COLLECTIONS
        )
        assert touching_before >= 18  # the seed carries an edge on every removed shape

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        for edge in _EDGE_COLLECTIONS:
            left = list(
                db.aql.execute(
                    "FOR e IN @@edge FILTER e._from IN @ids OR e._to IN @ids RETURN e._id",
                    bind_vars={"@edge": edge, "ids": gone},
                )
            )
            assert left == [], edge

    def test_the_history_stays_and_one_audit_row_records_the_delete(self, db, seeded) -> None:
        known_audit = {doc["_id"] for doc in db.collection(col.GARDEN_PLAN_AUDIT).all()}

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        for doc_id in seeded["site_a"]["kept"]:
            assert db.document(doc_id) is not None, doc_id
        assert db.collection(col.SEASON_STATES).get("foreign_claim") is not None
        rows = _audit_rows_beyond(db, known_audit)
        assert len(rows) == 1
        row = rows[0]
        assert {k: row[k] for k in ("op", "entity", "key", "tenant_key", "site_key", "user_key", "summary")} == {
            "op": "delete",
            "entity": "site",
            "key": "site_a",
            "tenant_key": A,
            "site_key": "site_a",
            "user_key": "u1",
            "summary": "Garden site_a",
        }
        assert row["revision"] == 4  # the stored plan revision + 1

    def test_tenant_b_is_untouched(self, db, seeded) -> None:
        def owned_by_b() -> tuple[dict[str, Any], dict[str, Any]]:
            ids = set(seeded["site_b"]["gone"]) | set(seeded["site_b"]["kept"])
            docs = {doc_id: doc for doc_id, doc in _documents(db).items() if doc_id in ids}
            edges = {
                edge_id: edge for edge_id, edge in _edges(db).items() if edge["_from"] in ids or edge["_to"] in ids
            }
            return docs, edges

        before = owned_by_b()
        assert len(before[0]) == len(seeded["site_b"]["gone"]) + len(seeded["site_b"]["kept"])

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        assert owned_by_b() == before

    def test_a_failure_after_the_first_write_leaves_everything_in_place(self, db, seeded, monkeypatch) -> None:
        documents, edges = _documents(db), _edges(db)

        def fail(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("injected after the removals")

        # The audit row is written after every edge and row removal and before the site itself goes.
        monkeypatch.setattr(ArangoSiteRepository, "_write_site_delete_audit", staticmethod(fail))

        with pytest.raises(RuntimeError, match="injected"):
            ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        assert _documents(db) == documents
        assert _edges(db) == edges

    def test_a_site_that_is_gone_is_not_found_and_nothing_is_written(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)

        with pytest.raises(NotFoundError):
            ArangoSiteRepository(db).delete_site("site_missing", tenant_key=A, user_key="u1")

        assert _documents(db) == documents
        assert _edges(db) == edges


def _plant(db, key: str, tenant: str, **placement: Any) -> None:
    db.collection(col.PLANT_INSTANCES).insert(
        {"_key": key, "instance_id": key, "tenant_key": tenant, "removed_on": None, **placement}
    )


class TestASiteWithActivePlantsIsNotDeleted:
    """V-09 one level up (#2513 WP-3): the refusal fires inside the transaction, before the first write."""

    @staticmethod
    def _assert_refused_and_untouched(db, count: int) -> None:
        documents, edges = _documents(db), _edges(db)

        with pytest.raises(PlanError) as refused:
            ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        assert refused.value.status_code == 409
        assert refused.value.error_code == "site.has_active_plants"
        assert refused.value.details[0]["code"] == "site.has_active_plants"
        assert refused.value.details[0]["active_plant_count"] == count
        # Site, beds, slots, objects, zones, dependents, plants, audit rows (no new one) and every edge as before.
        assert _documents(db) == documents
        assert _edges(db) == edges

    def test_a_plant_naming_the_site_refuses_the_delete(self, db, seeded) -> None:
        _plant(db, "p_site", A, site_key="site_a")
        self._assert_refused_and_untouched(db, 1)
        for doc_id in seeded["site_a"]["gone"]:
            assert db.document(doc_id) is not None, doc_id

    def test_a_pre_v0100_plant_on_a_nested_location_refuses_the_delete(self, db, seeded) -> None:
        # No ``site_key`` (written before v0100), on the bed reachable only through the ``contains`` tree.
        _plant(db, "p_loc", A, location_key="child_site_a")
        self._assert_refused_and_untouched(db, 1)

    def test_a_plant_in_a_slot_refuses_the_delete(self, db, seeded) -> None:
        _plant(db, "p_slot", A, slot_key="slot_site_a")
        self._assert_refused_and_untouched(db, 1)

    def test_every_matching_plant_is_counted_once(self, db, seeded) -> None:
        _plant(db, "p_all", A, site_key="site_a", location_key="child_site_a", slot_key="slot_site_a")
        _plant(db, "p_loose", A, location_key="loose_site_a")
        self._assert_refused_and_untouched(db, 2)

    def test_a_plant_without_a_removed_on_field_refuses_the_delete(self, db, seeded) -> None:
        # No ``removed_on`` key at all (not ``None``): AQL's ``== null`` matches a missing attribute.
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "p_no_field", "instance_id": "p_no_field", "tenant_key": A, "location_key": "loose_site_a"}
        )
        assert "removed_on" not in db.collection(col.PLANT_INSTANCES).get("p_no_field")
        self._assert_refused_and_untouched(db, 1)

    def test_a_removed_plant_does_not_block(self, db, seeded) -> None:
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p_gone",
                "instance_id": "p_gone",
                "tenant_key": A,
                "site_key": "site_a",
                "location_key": "child_site_a",
                "slot_key": "slot_site_a",
                "removed_on": "2026-09-01",
            }
        )

        assert ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1") is True

        assert db.collection(col.SITES).get("site_a") is None
        assert db.collection(col.PLANT_INSTANCES).get("p_gone") is not None  # the plant's history stays

    def test_tenant_b_plants_on_tenant_b_site_do_not_block_site_a(self, db, seeded) -> None:
        _plant(db, "p_b_site", B, site_key="site_b")
        _plant(db, "p_b_loc", B, location_key="child_site_b")
        _plant(db, "p_b_slot", B, slot_key="slot_site_b")

        assert ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1") is True

        assert db.collection(col.SITES).get("site_a") is None
        assert db.collection(col.SITES).get("site_b") is not None
        with pytest.raises(PlanError) as refused:
            ArangoSiteRepository(db).delete_site("site_b", tenant_key=B, user_key="u1")
        assert refused.value.details[0]["active_plant_count"] == 3  # positive control: they do block their own site


class TestTheDeleteTakesOnlyWhatIsTheSitesOwn:
    """Review follow-ups of #2513: a stale edge or a foreign row never widens the delete (F1, F2, F3, F6)."""

    @staticmethod
    def _second_site(db, key: str = "site_c", tenant: str = A) -> None:
        db.collection(col.SITES).insert({"_key": key, "tenant_key": tenant, "name": key, "type": "outdoor"})

    def test_a_bed_rehomed_to_another_site_stays_with_its_subtree_and_slots(self, db, seeded) -> None:
        # ``update_location`` rewrites ``site_key`` S1 -> S2 and leaves the ``contains`` edge from S1 in place.
        self._second_site(db)
        db.collection(col.LOCATIONS).insert({"_key": "moved", "site_key": "site_c", "name": "moved"})
        db.collection(col.LOCATIONS).insert({"_key": "moved_child", "parent_location_key": "moved", "name": "mc"})
        db.collection(col.SLOTS).insert({"_key": "moved_slot", "slot_id": "M1", "location_key": "moved"})
        _edge(db, col.CONTAINS, f"{col.SITES}/site_a", f"{col.LOCATIONS}/moved")
        _edge(db, col.CONTAINS, f"{col.LOCATIONS}/moved", f"{col.LOCATIONS}/moved_child")
        _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/moved", f"{col.SLOTS}/moved_slot")

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        for doc_id in (f"{col.LOCATIONS}/moved", f"{col.LOCATIONS}/moved_child", f"{col.SLOTS}/moved_slot"):
            assert db.document(doc_id) is not None, doc_id
        # The stale edge from the removed site is cut; the bed's own structure is not.
        contains = {(e["_from"], e["_to"]) for e in db.collection(col.CONTAINS).all()}
        assert (f"{col.SITES}/site_a", f"{col.LOCATIONS}/moved") not in contains
        assert (f"{col.LOCATIONS}/moved", f"{col.LOCATIONS}/moved_child") in contains

    def test_a_slot_reached_only_by_edge_that_names_another_location_stays(self, db, seeded) -> None:
        # A stale ``has_slot`` from site_a's bed to a slot of tenant B's bed.
        _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/bed_site_a", f"{col.SLOTS}/slot_site_b")
        # An edge-only slot with no ``location_key`` belongs to the location the edge comes from.
        db.collection(col.SLOTS).insert({"_key": "edge_only", "slot_id": "E1", "location_key": ""})
        _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/bed_site_a", f"{col.SLOTS}/edge_only")

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        assert db.document(f"{col.SLOTS}/slot_site_b") is not None
        assert db.document(f"{col.SLOTS}/edge_only") is None
        assert [e["_from"] for e in db.collection(col.HAS_SLOT).all() if e["_to"] == f"{col.SLOTS}/slot_site_b"] == [
            f"{col.LOCATIONS}/child_site_b"
        ]

    def test_another_tenants_key_deletes_nothing(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)

        with pytest.raises(NotFoundError):
            ArangoSiteRepository(db).delete_site("site_a", tenant_key=B, user_key="u1")

        assert _documents(db) == documents
        assert _edges(db) == edges

    def test_an_unstamped_zone_goes_and_a_foreign_zone_stays(self, db, seeded) -> None:
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_unstamped", "tenant_key": "", "site_key": "site_a", "name": "u"}
        )
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_foreign", "tenant_key": B, "site_key": "site_a", "name": "f"}
        )

        ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key="u1")

        assert db.collection(col.IRRIGATION_ZONES).get("zone_unstamped") is None
        assert db.collection(col.IRRIGATION_ZONES).get("zone_foreign") is not None
