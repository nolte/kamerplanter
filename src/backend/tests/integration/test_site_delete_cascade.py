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
* a failure after the first write leaves the database as it was (one stream transaction).
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError
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
_DOCUMENT_COLLECTIONS = (*_REMOVED_VERTEX_COLLECTIONS, col.CARE_EVENTS, col.GARDEN_PLAN_AUDIT)


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

        assert ArangoSiteRepository(db).delete_site("site_a", user_key="u1") is True

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

        ArangoSiteRepository(db).delete_site("site_a", user_key="u1")

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

        ArangoSiteRepository(db).delete_site("site_a", user_key="u1")

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

        ArangoSiteRepository(db).delete_site("site_a", user_key="u1")

        assert owned_by_b() == before

    def test_a_failure_after_the_first_write_leaves_everything_in_place(self, db, seeded, monkeypatch) -> None:
        documents, edges = _documents(db), _edges(db)

        def fail(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("injected after the removals")

        # The audit row is written after every edge and row removal and before the site itself goes.
        monkeypatch.setattr(ArangoSiteRepository, "_write_site_delete_audit", staticmethod(fail))

        with pytest.raises(RuntimeError, match="injected"):
            ArangoSiteRepository(db).delete_site("site_a", user_key="u1")

        assert _documents(db) == documents
        assert _edges(db) == edges

    def test_a_site_that_is_gone_is_not_found_and_nothing_is_written(self, db, seeded) -> None:
        documents, edges = _documents(db), _edges(db)

        with pytest.raises(NotFoundError):
            ArangoSiteRepository(db).delete_site("site_missing", user_key="u1")

        assert _documents(db) == documents
        assert _edges(db) == edges
