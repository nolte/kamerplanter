"""#2513 — v0102 measured on a real ArangoDB: what a site delete before the cascade fix left behind goes, nothing else.

The fixture writes the stored shapes directly: a site that is gone with one row of every site-keyed collection, a
bed with a child bed and a slot, and the edges that pointed at them; a live site with the same shapes; and the care
event and plan-audit rows of the gone site, which are history and stay. The #2528 step (unset a ``template_key``
that names no bed template) is measured on beds of the live site seeded per test.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0102_purge_site_orphans.py -v
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.migrations.versions.v0102_purge_site_orphans import _EDGE_ENDS, _SITE_KEYED_ROWS, migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scans and batched REMOVE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0102_purge_site_orphans")
LIVE, GONE = "site_live", "site_gone"

_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.CARE_EVENTS,
    col.GARDEN_PLAN_AUDIT,
    col.IRRIGATION_ZONES,
    *_SITE_KEYED_ROWS,
)
_EDGES = tuple(dict.fromkeys(edge for _, ends in _EDGE_ENDS for edge, _ in ends))


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _edge(db, edge: str, from_id: str, to_id: str) -> str:  # type: ignore[no-untyped-def]
    return str(db.collection(edge).insert({"_from": from_id, "_to": to_id})["_id"])


_HAS_EDGE = {
    col.GARDEN_OBJECTS: col.HAS_GARDEN_OBJECT,
    col.SEASON_STATES: col.HAS_SEASON_STATE,
    col.WEATHER_FORECASTS: col.HAS_FORECAST,
    col.CLIMATE_NORMALS: col.HAS_CLIMATE_NORMAL,
    col.WEATHER_SOURCE_CONFIGS: col.HAS_WEATHER_SOURCE_CONFIG,
    col.IRRIGATION_DEMANDS: col.HAS_IRRIGATION_DEMAND,
    col.IRRIGATION_ZONES: col.HAS_IRRIGATION_ZONE,
}


def _seed_site_shapes(db, site: str) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    """One row per site-keyed collection, a bed with a child and a slot, and their edges; returns ids by kind."""
    site_id = f"{col.SITES}/{site}"
    rows, edges = [], []
    for collection in _SITE_KEYED_ROWS:
        key = f"{collection}_{site}"
        db.collection(collection).insert(
            {"_key": key, "site_key": site, "tenant_key": "t1", "source": site, "run_key": site, "demand_date": site}
        )
        rows.append(f"{collection}/{key}")
        edges.append(_edge(db, _HAS_EDGE[collection], site_id, f"{collection}/{key}"))
    bed, child, slot = f"{col.LOCATIONS}/bed_{site}", f"{col.LOCATIONS}/child_{site}", f"{col.SLOTS}/slot_{site}"
    db.collection(col.LOCATIONS).insert({"_key": f"bed_{site}", "site_key": site, "name": "bed"})
    db.collection(col.LOCATIONS).insert({"_key": f"child_{site}", "parent_location_key": f"bed_{site}"})
    db.collection(col.SLOTS).insert({"_key": f"slot_{site}", "slot_id": f"A1-{site}", "location_key": f"bed_{site}"})
    edges += [
        _edge(db, col.CONTAINS, site_id, bed),
        _edge(db, col.CONTAINS, bed, child),
        _edge(db, col.HAS_SLOT, bed, slot),
        _edge(db, col.PLACED_IN, f"{col.PLANT_INSTANCES}/plant_{site}", slot),
        _edge(db, col.CARE_EVENT_AT, f"{col.CARE_EVENTS}/care_{site}", bed),
        _edge(db, col.RUN_AT_LOCATION, f"{col.PLANTING_RUNS}/run_{site}", child),
        _edge(
            db,
            col.DEMAND_FOR_RUN,
            f"{col.PLANTING_RUNS}/run_{site}",
            f"{col.IRRIGATION_DEMANDS}/{col.IRRIGATION_DEMANDS}_{site}",
        ),
    ]
    db.collection(col.CARE_EVENTS).insert({"_key": f"care_{site}", "site_key": site, "location_key": f"bed_{site}"})
    _edge(db, col.BELONGS_TO_TENANT, f"{col.CARE_EVENTS}/care_{site}", f"{col.TENANTS}/t1")
    db.collection(col.GARDEN_PLAN_AUDIT).insert({"_key": f"audit_{site}", "site_key": site, "op": "delete"})
    return {"rows": rows, "locations": [bed, child], "slots": [slot], "edges": edges}


@pytest.fixture
def seeded(db) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    db.collection(col.SITES).insert({"_key": LIVE, "tenant_key": "t1", "name": "live"})
    _edge(db, col.BELONGS_TO_TENANT, f"{col.SITES}/{LIVE}", f"{col.TENANTS}/t1")
    live = _seed_site_shapes(db, LIVE)
    gone = _seed_site_shapes(db, GONE)
    # Names the gone site but hangs under the live bed: a surviving vertex reaches it, so it stays.
    db.collection(col.LOCATIONS).insert({"_key": "anchored", "site_key": GONE})
    anchored = _edge(db, col.CONTAINS, f"{col.LOCATIONS}/bed_{LIVE}", f"{col.LOCATIONS}/anchored")
    # A row without a site is not an orphan of a site.
    db.collection(col.SEASON_STATES).insert({"_key": "unsited", "site_key": "", "tenant_key": "t1"})
    # The only removed end is a zone that no longer exists.
    zone_edge = _edge(db, col.ZONE_COVERS, f"{col.IRRIGATION_ZONES}/zone_gone", f"{col.LOCATIONS}/bed_{LIVE}")
    return {"live": live, "gone": gone, "anchored": anchored, "zone_edge": zone_edge}


def _state(db) -> tuple[dict[str, Any], dict[str, Any]]:  # type: ignore[no-untyped-def]
    docs = {d["_id"]: d for name in _DOCUMENTS for d in db.collection(name).all()}
    edges = {e["_id"]: e for name in _EDGES for e in db.collection(name).all()}
    return docs, edges


def _matched(report) -> dict[str, int]:  # type: ignore[no-untyped-def]
    return {step: detail["matched"] for step, detail in report.details.items()}


def test_dry_run_reports_and_writes_nothing(db, seeded) -> None:  # type: ignore[no-untyped-def]
    before = _state(db)

    report = migration.up(db, dry_run=True)

    assert _state(db) == before
    assert report.changed == 0
    matched = _matched(report)
    assert all(matched[f"{name}_of_missing_sites"] == 1 for name in _SITE_KEYED_ROWS)
    assert matched["locations_of_missing_sites"] == 2  # the gone bed and the child below it
    assert matched["slots_of_removed_locations"] == 1
    # 7 has_* + contains x2 + has_slot + placed_in + care_event_at + run_at_location + demand_for_run of the gone
    # site, plus the zone edge.
    assert matched["dangling_edges"] == 15


def test_apply_removes_the_orphans_and_matches_the_dry_run(db, seeded) -> None:  # type: ignore[no-untyped-def]
    dry = migration.up(db, dry_run=True)
    docs_before, edges_before = _state(db)

    report = migration.up(db)

    assert _matched(report) == _matched(dry)
    assert report.changed == sum(_matched(dry).values())
    gone = seeded["gone"]
    removed_docs = {*gone["rows"], *gone["locations"], *gone["slots"]}
    removed_edges = {*gone["edges"], seeded["zone_edge"]}
    docs, edges = _state(db)
    assert docs == {doc_id: d for doc_id, d in docs_before.items() if doc_id not in removed_docs}
    assert edges == {edge_id: e for edge_id, e in edges_before.items() if edge_id not in removed_edges}


def test_live_rows_and_history_survive(db, seeded) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    live = seeded["live"]
    for doc_id in (*live["rows"], *live["locations"], *live["slots"], f"{col.LOCATIONS}/anchored"):
        assert db.document(doc_id) is not None, doc_id
    for doc_id in (*live["edges"], seeded["anchored"]):
        assert db.document(doc_id) is not None, doc_id
    for doc_id in (f"{col.CARE_EVENTS}/care_{GONE}", f"{col.GARDEN_PLAN_AUDIT}/audit_{GONE}"):
        assert db.document(doc_id) is not None, doc_id
    assert db.document(f"{col.SEASON_STATES}/unsited") is not None
    care_tenant = [e for e in db.collection(col.BELONGS_TO_TENANT).all() if e["_from"].startswith("care_events/")]
    assert len(care_tenant) == 2


def test_a_second_run_finds_nothing(db, seeded) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    before = _state(db)

    again = migration.up(db)

    assert again.changed == 0
    assert set(_matched(again).values()) == {0}
    assert _state(db) == before


# ── Review follow-ups of #2513 (F1, F2, F4, F5, F7) ──────────────────────────────────────────────────────────────


def test_a_bed_rehomed_to_a_live_site_below_a_gone_bed_stays(db, seeded) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.LOCATIONS).insert({"_key": "rehomed", "site_key": LIVE})
    _edge(db, col.CONTAINS, f"{col.LOCATIONS}/bed_{GONE}", f"{col.LOCATIONS}/rehomed")

    migration.up(db)

    assert db.document(f"{col.LOCATIONS}/rehomed") is not None
    assert [e for e in db.collection(col.CONTAINS).all() if e["_to"] == f"{col.LOCATIONS}/rehomed"] == []


def test_a_slot_reached_only_by_edge_from_a_removed_bed_goes_only_when_unsited(db, seeded) -> None:  # type: ignore[no-untyped-def]
    # Names the live bed; only a stale ``has_slot`` from the gone bed reaches it.
    db.collection(col.SLOTS).insert({"_key": "stray", "slot_id": "S1", "location_key": f"bed_{LIVE}"})
    _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/bed_{GONE}", f"{col.SLOTS}/stray")
    db.collection(col.SLOTS).insert({"_key": "edge_only", "slot_id": "S2", "location_key": ""})
    _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/bed_{GONE}", f"{col.SLOTS}/edge_only")

    report = migration.up(db)

    assert db.document(f"{col.SLOTS}/stray") is not None
    assert db.document(f"{col.SLOTS}/edge_only") is None
    assert report.details["slots_of_removed_locations"]["matched"] == 2  # slot_site_gone and edge_only


def test_an_unsited_garden_object_linked_only_from_a_gone_site_goes(db, seeded) -> None:  # type: ignore[no-untyped-def]
    for key in ("obj_gone_only", "obj_live", "obj_both"):
        db.collection(col.GARDEN_OBJECTS).insert({"_key": key, "site_key": "", "object_type": "water_source"})
    db.collection(col.GARDEN_OBJECTS).insert({"_key": "obj_nofield", "object_type": "water_source"})
    _edge(db, col.HAS_GARDEN_OBJECT, f"{col.SITES}/{GONE}", f"{col.GARDEN_OBJECTS}/obj_gone_only")
    _edge(db, col.HAS_GARDEN_OBJECT, f"{col.SITES}/{GONE}", f"{col.GARDEN_OBJECTS}/obj_nofield")
    _edge(db, col.HAS_GARDEN_OBJECT, f"{col.SITES}/{LIVE}", f"{col.GARDEN_OBJECTS}/obj_live")
    _edge(db, col.HAS_GARDEN_OBJECT, f"{col.SITES}/{GONE}", f"{col.GARDEN_OBJECTS}/obj_both")
    _edge(db, col.HAS_GARDEN_OBJECT, f"{col.SITES}/{LIVE}", f"{col.GARDEN_OBJECTS}/obj_both")

    migration.up(db)

    assert db.collection(col.GARDEN_OBJECTS).get("obj_gone_only") is None
    assert db.collection(col.GARDEN_OBJECTS).get("obj_nofield") is None
    assert db.collection(col.GARDEN_OBJECTS).get("obj_live") is not None
    assert db.collection(col.GARDEN_OBJECTS).get("obj_both") is not None


def test_an_unsited_location_whose_parent_is_gone_goes_with_its_chain(db, seeded) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.LOCATIONS).insert({"_key": "stranded", "site_key": None, "parent_location_key": "long_gone"})
    db.collection(col.LOCATIONS).insert({"_key": "stranded_child", "site_key": "", "parent_location_key": "stranded"})
    db.collection(col.LOCATIONS).insert({"_key": "parentless", "site_key": ""})
    _edge(db, col.CONTAINS, f"{col.LOCATIONS}/long_gone", f"{col.LOCATIONS}/stranded")
    _edge(db, col.CONTAINS, f"{col.LOCATIONS}/stranded", f"{col.LOCATIONS}/stranded_child")

    migration.up(db)

    for key in ("stranded", "stranded_child"):
        assert db.collection(col.LOCATIONS).get(key) is None, key
    assert [e for e in db.collection(col.CONTAINS).all() if e["_to"] == f"{col.LOCATIONS}/stranded"] == []
    # An unsited child whose parent exists stays; so does an unsited location no ``contains`` edge ever reached (R1).
    assert db.collection(col.LOCATIONS).get(f"child_{LIVE}") is not None
    assert db.collection(col.LOCATIONS).get("parentless") is not None


def test_a_standalone_unsited_location_with_slots_and_plants_stays(db, seeded) -> None:  # type: ignore[no-untyped-def]
    """R1: ``create_location`` writes no ``contains`` edge for a location without parent and site, so a legacy
    standalone location has none. Without a dangling ``contains`` edge nothing shows it lost a parent: it stays,
    with its slots and their edges."""
    db.collection(col.LOCATIONS).insert({"_key": "standalone", "name": "Shelf"})
    db.collection(col.LOCATIONS).insert({"_key": "standalone_empty", "site_key": "", "name": "Box"})
    db.collection(col.SLOTS).insert({"_key": "standalone_slot", "slot_id": "S1", "location_key": "standalone"})
    edges = [
        _edge(db, col.HAS_SLOT, f"{col.LOCATIONS}/standalone", f"{col.SLOTS}/standalone_slot"),
        _edge(db, col.PLACED_IN, f"{col.PLANT_INSTANCES}/plant_standalone", f"{col.SLOTS}/standalone_slot"),
    ]

    report = migration.up(db)

    for doc_id in (
        f"{col.LOCATIONS}/standalone",
        f"{col.LOCATIONS}/standalone_empty",
        f"{col.SLOTS}/standalone_slot",
        *edges,
    ):
        assert db.document(doc_id) is not None, doc_id
    detail = report.details["locations_of_missing_sites"]
    assert detail["matched"] == 2  # the gone bed and its child only
    assert {"standalone", "standalone_empty"}.isdisjoint(detail["keys"])
    assert report.details["slots_of_removed_locations"]["matched"] == 1


def test_a_zone_of_a_missing_site_goes_and_a_zone_of_a_live_site_stays(db, seeded) -> None:  # type: ignore[no-untyped-def]
    """R2: ``irrigation_zones`` is a site-keyed row like the other site dependents."""
    zones = db.collection(col.IRRIGATION_ZONES)
    zones.insert({"_key": "zone_of_gone", "site_key": GONE, "tenant_key": "t1", "name": "gone"})
    zones.insert({"_key": "zone_of_live", "site_key": LIVE, "tenant_key": "t1", "name": "live"})
    edge = _edge(db, col.ZONE_COVERS, f"{col.IRRIGATION_ZONES}/zone_of_gone", f"{col.LOCATIONS}/child_{LIVE}")

    report = migration.up(db)

    assert zones.get("zone_of_gone") is None
    assert zones.get("zone_of_live") is not None
    assert db.document(edge) is None
    assert "zone_of_gone" in report.details["irrigation_zones_of_missing_sites"]["keys"]


def test_remove_counts_only_what_was_actually_removed(db, seeded) -> None:  # type: ignore[no-untyped-def]
    from app.migrations.versions.v0102_purge_site_orphans import _remove

    removed = _remove(db, [f"{col.SEASON_STATES}/unsited", f"{col.SEASON_STATES}/not_there"])

    assert removed == 1
    assert db.collection(col.SEASON_STATES).get("unsited") is None


# ── #2528: the nulling step unsets a template_key that names no bed template ─────────────────────────────────────

_STEP = "locations_with_dangling_template_key"


@pytest.fixture
def templated(db, seeded) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Three beds of the live site naming a missing, a live system and a live tenant template; one bed of the gone
    site naming the missing template (the removal takes it, the nulling must not count it)."""
    db.collection(col.BED_TEMPLATES).insert_many(
        [{"_key": "sys_tpl", "name": "System"}, {"_key": "own_tpl", "name": "Own", "tenant_key": "t1"}]
    )
    db.collection(col.LOCATIONS).insert_many(
        [
            {"_key": "tb_missing", "site_key": LIVE, "name": "a", "template_key": "tpl_deleted"},
            {"_key": "tb_system", "site_key": LIVE, "name": "b", "template_key": "sys_tpl"},
            {"_key": "tb_tenant", "site_key": LIVE, "name": "c", "template_key": "own_tpl"},
            {"_key": "tb_gone_site", "site_key": GONE, "name": "d", "template_key": "tpl_deleted"},
        ]
    )
    return {key: db.collection(col.LOCATIONS).get(key)["_rev"] for key in ("tb_system", "tb_tenant")}


def test_the_nulling_dry_run_matches_one_and_writes_nothing(db, templated) -> None:  # type: ignore[no-untyped-def]
    before = _state(db)

    report = migration.up(db, dry_run=True)

    assert report.details[_STEP] == {"matched": 1, "nulled": 0, "keys": ["tb_missing"]}
    assert list(report.details)[-1] == _STEP
    assert _state(db) == before


def test_the_nulling_unsets_only_the_dangling_key_and_a_second_run_matches_nothing(db, templated) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.details[_STEP] == {"matched": 1, "nulled": 1, "keys": ["tb_missing"]}
    locations = db.collection(col.LOCATIONS)
    assert "template_key" not in locations.get("tb_missing")
    assert {key: locations.get(key)["_rev"] for key in templated} == templated
    assert locations.get("tb_gone_site") is None  # removed with its site, not nulled
    again = migration.up(db)
    assert again.details[_STEP]["matched"] == 0 and again.changed == 0


def test_a_volume_without_bed_templates_nulls_nothing(db, templated) -> None:  # type: ignore[no-untyped-def]
    # An older volume without the collection. It sits in an edge definition of the named graph, which the migration
    # does not use; the per-test database is dropped afterwards, so the graph goes first.
    db.delete_graph(col.GRAPH_NAME)
    db.delete_collection(col.BED_TEMPLATES)

    report = migration.up(db)

    assert report.details[_STEP] == {"matched": 0, "nulled": 0, "keys": []}
    assert db.collection(col.LOCATIONS).get("tb_missing")["template_key"] == "tpl_deleted"


def test_the_nulling_counts_only_what_the_update_returned(db, templated) -> None:  # type: ignore[no-untyped-def]
    from app.migrations.versions.v0102_purge_site_orphans import _unset_template_key

    nulled = _unset_template_key(db, [f"{col.LOCATIONS}/tb_missing", f"{col.LOCATIONS}/not_there"])

    assert nulled == 1
    assert "template_key" not in db.collection(col.LOCATIONS).get("tb_missing")


def test_a_bed_retemplated_between_plan_and_apply_is_not_nulled(db, templated, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The write re-checks the template (#2528 G2): a bed whose key names a live template by the time the ``UPDATE``
    runs keeps it, and ``nulled`` counts only what the statement changed."""
    from app.migrations.versions import v0102_purge_site_orphans as v0102

    db.collection(col.LOCATIONS).insert({"_key": "tb_late", "site_key": LIVE, "name": "e", "template_key": "tpl_late"})
    real_plan = v0102._locations_with_dangling_template_key

    def plan_then_retemplate(database, gone):  # type: ignore[no-untyped-def]
        ids = real_plan(database, gone)
        database.collection(col.BED_TEMPLATES).insert({"_key": "tpl_late", "name": "Late"})
        return ids

    monkeypatch.setattr(v0102, "_NULLING_STEPS", ((_STEP, plan_then_retemplate),))

    detail = migration.up(db).details[_STEP]

    assert detail["matched"] == 2
    assert detail["nulled"] == detail["matched"] - 1
    locations = db.collection(col.LOCATIONS)
    assert "template_key" not in locations.get("tb_missing")
    assert locations.get("tb_late")["template_key"] == "tpl_late"
