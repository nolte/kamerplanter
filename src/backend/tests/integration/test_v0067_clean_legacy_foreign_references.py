"""#1878 — v0067 and its count queries, driven against a real ArangoDB.

Each class is seeded with the shape a volume written before #1871 carries, **next
to** the rows that must survive: the tenant's own legitimate rows, global-catalogue
targets, granted species, and rows whose tenant cannot be established. The
operator's pre-deploy count queries (``COUNT_QUERIES``) are the very strings the
migration's predicates are built from, so they are run here and compared with
what the migration then does.

What this cannot say: how many such rows a real installation holds. Nothing in the
issue was measured against production; the numbers below are synthetic.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.support.legacy_foreign_references import COUNT_QUERIES
from app.migrations.versions.v0067_clean_legacy_foreign_references import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("v0067_legacy_refs")
pytestmark = pytest.mark.usefixtures("arango_db")

_DOCS = [
    col.TENANTS, col.SITES, col.LOCATIONS, col.SLOTS, col.SPECIES, col.WORKFLOW_TEMPLATES, col.EQUIPMENT,
    col.LOCATION_ASSIGNMENTS, col.WATERING_LOGS, col.TANKS, col.PLANTING_RUNS, col.PLANTING_RUN_ENTRIES,
]  # fmt: skip
_EDGES = [
    col.HAS_SLOT, col.EQUIPMENT_AT, col.ASSIGNED_TO_LOCATION, col.LOG_SLOT, col.FEEDS_FROM,
    col.ENTRY_FOR_SPECIES, col.TENANT_HAS_ACCESS,
]  # fmt: skip


#: Before #1876 merged (2026-09-26): the only time a hole could have produced a row.
_OLD = "2026-09-01T10:00:00.000000+00:00"
_NEW = "2026-10-01T10:00:00.000000+00:00"


def _edge(db: Any, collection: str, source: str, target: str, created_at: str | None = _OLD) -> str:
    doc: dict[str, Any] = {"_from": source, "_to": target}
    if created_at is not None:
        doc["created_at"] = created_at
    return db.collection(collection).insert(doc)["_key"]


@pytest.fixture(scope="module")
def _database():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in _DOCS:
            database.create_collection(name)
        for name in _EDGES:
            database.create_collection(name, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def legacy(_database):
    """The synthetic legacy volume. Returns the db and the keys of the edges the tests name."""
    db = _database
    for name in (*_DOCS, *_EDGES):
        db.collection(name).truncate()

    def put(collection: str, *docs: dict[str, Any]) -> None:
        db.collection(collection).insert_many(list(docs))

    put(col.SITES, {"_key": "siteA", "tenant_key": "A"}, {"_key": "siteB", "tenant_key": "B"})
    put(
        col.LOCATIONS,
        {"_key": "locA1", "site_key": "siteA"},
        {"_key": "locA2", "site_key": "siteA"},
        {"_key": "locB1", "site_key": "siteB"},
        {"_key": "locOrphan", "site_key": "no-such-site"},
    )
    # -- slots (class 2) --
    put(
        col.SLOTS,
        {"_key": "s_ok", "location_key": "locA1"},
        {"_key": "s_moved", "location_key": "locA2"},  # edge still on locA1, same tenant
        {"_key": "s_foreign", "location_key": "locB1"},  # field points into another tenant
        {"_key": "s_noedge", "location_key": "locA1"},
    )
    e: dict[str, str] = {}
    e["s_ok"] = _edge(db, col.HAS_SLOT, "locations/locA1", "slots/s_ok")
    e["s_moved"] = _edge(db, col.HAS_SLOT, "locations/locA1", "slots/s_moved")
    e["s_foreign"] = _edge(db, col.HAS_SLOT, "locations/locA1", "slots/s_foreign")
    # -- species / templates (class 1) --
    put(
        col.SPECIES,
        {"_key": "spG", "tenant_key": ""},
        {"_key": "spLegacy"},  # no attribute at all: global by the #324 union rule
        {"_key": "spA", "tenant_key": "A"},
        {"_key": "spB", "tenant_key": "B"},
        {"_key": "spB2", "tenant_key": "B"},
        {"_key": "spA2", "tenant_key": "A"},
        {"_key": "spGr", "tenant_key": "A"},  # granted to B
        {"_key": "spD", "tenant_key": "A"},  # A already holds a generated plan for it
    )
    put(
        col.WORKFLOW_TEMPLATES,
        {"_key": "wt_private", "auto_generated": True, "tenant_key": "", "species_key": "spA", "is_system": False},
        {"_key": "wt_global", "auto_generated": True, "tenant_key": "", "species_key": "spG", "is_system": False},
        {"_key": "wt_legacy", "auto_generated": True, "tenant_key": "", "species_key": "spLegacy"},
        {"_key": "wt_own", "auto_generated": True, "tenant_key": "A", "species_key": "spA2"},
        {"_key": "wt_system", "auto_generated": True, "tenant_key": "", "species_key": "spA", "is_system": True},
        {"_key": "wt_manual", "auto_generated": False, "tenant_key": "", "species_key": "spA"},
        {"_key": "wt_orphan", "auto_generated": True, "tenant_key": "", "species_key": "gone"},
        {"_key": "wt_granted", "auto_generated": True, "tenant_key": "", "species_key": "spGr"},
        {"_key": "wt_dup", "auto_generated": True, "tenant_key": "", "species_key": "spD"},
        {"_key": "wt_dup_owner", "auto_generated": True, "tenant_key": "A", "species_key": "spD"},
    )
    db.collection(col.TENANT_HAS_ACCESS).insert({"_from": "tenants/B", "_to": "species/spGr"})
    # -- equipment (3a) --
    put(
        col.EQUIPMENT,
        {"_key": "eqA", "tenant_key": "A"},
        {"_key": "eqNone"},  # no tenant stamp: unclassifiable
    )
    e["eq_ok"] = _edge(db, col.EQUIPMENT_AT, "equipment/eqA", "locations/locA1")
    e["eq_foreign"] = _edge(db, col.EQUIPMENT_AT, "equipment/eqA", "locations/locB1")
    e["eq_unstamped"] = _edge(db, col.EQUIPMENT_AT, "equipment/eqNone", "locations/locB1")
    e["eq_siteless"] = _edge(db, col.EQUIPMENT_AT, "equipment/eqA", "locations/locOrphan")
    # -- location assignments (3b) --
    put(col.LOCATION_ASSIGNMENTS, {"_key": "laA", "tenant_key": "A"})
    e["la_ok"] = _edge(db, col.ASSIGNED_TO_LOCATION, "location_assignments/laA", "locations/locA2")
    e["la_foreign"] = _edge(db, col.ASSIGNED_TO_LOCATION, "location_assignments/laA", "locations/locB1")
    # -- watering logs (3c) --
    put(col.WATERING_LOGS, {"_key": "wlA", "tenant_key": "A"}, {"_key": "wlB", "tenant_key": "B"})
    e["log_ok"] = _edge(db, col.LOG_SLOT, "watering_logs/wlA", "slots/s_ok")
    e["log_foreign"] = _edge(db, col.LOG_SLOT, "watering_logs/wlB", "slots/s_ok")
    e["log_missing_slot"] = _edge(db, col.LOG_SLOT, "watering_logs/wlA", "slots/gone")
    # A's own history on a slot whose field was walked into B's location: field and edge
    # disagree, so neither tenant is established and the edge is not judged.
    e["log_on_hole_slot"] = _edge(db, col.LOG_SLOT, "watering_logs/wlA", "slots/s_foreign")
    e["log_on_edgeless_slot"] = _edge(db, col.LOG_SLOT, "watering_logs/wlB", "slots/s_noedge")
    # -- tanks (3d) --
    put(
        col.TANKS,
        {"_key": "tkA", "tenant_key": "A"},
        {"_key": "tkA2", "tenant_key": "A"},
        {"_key": "tkB", "tenant_key": "B"},
        {"_key": "tkGlobal", "tenant_key": ""},
    )
    e["feed_ok"] = _edge(db, col.FEEDS_FROM, "tanks/tkA", "tanks/tkA2")
    e["feed_foreign"] = _edge(db, col.FEEDS_FROM, "tanks/tkA", "tanks/tkB")
    e["feed_global"] = _edge(db, col.FEEDS_FROM, "tanks/tkA", "tanks/tkGlobal")
    # -- planting-run entries (3e) --
    put(col.PLANTING_RUNS, {"_key": "runA", "tenant_key": "A"}, {"_key": "runB", "tenant_key": "B"})
    put(
        col.PLANTING_RUN_ENTRIES,
        {"_key": "enA", "run_key": "runA", "tenant_key": ""},  # pre-#1112 row: unstamped, the run decides
        {"_key": "enB", "run_key": "runB", "tenant_key": "B"},
        {"_key": "enLost", "run_key": "gone", "tenant_key": ""},
    )
    db.collection(col.TENANT_HAS_ACCESS).insert({"_from": "tenants/A", "_to": "species/spB2"})
    e["en_global"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spG")
    e["en_own"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spA")
    e["en_legacy_global"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spLegacy")
    e["en_granted"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spB2")
    e["en_foreign"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spB")
    e["en_foreign_b"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enB", "species/spA")
    e["en_lost_run"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enLost", "species/spB")
    # A grant is revocable: an edge created after #1876 that fails the grant test may have
    # been legitimate under a grant B later withdrew. Neither it nor an undated edge is judged.
    e["en_post_fix"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spB", _NEW)
    e["en_undated"] = _edge(db, col.ENTRY_FOR_SPECIES, "planting_run_entries/enA", "species/spB", None)
    return db, e


def _counts(db: Any) -> dict[str, dict[str, int]]:
    return {name: {row["verdict"]: row["n"] for row in db.aql.execute(query)} for name, query in COUNT_QUERIES.items()}


def _snapshot(db: Any) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        name: {d["_key"]: {k: v for k, v in d.items() if k != "_rev"} for d in db.collection(name).all()}
        for name in (*_DOCS, *_EDGES)
    }


def _exists(db: Any, collection: str, key: str) -> bool:
    return bool(db.collection(collection).has(key))


EXPECTED = {
    "workflow_templates_of_private_species": {
        "reown": 1,
        "unclassified": 1,
        "left_granted": 1,
        "left_owner_has_plan": 1,
    },
    "slot_field_edge_disagreement": {"move_edge": 1, "unclassified": 2},
    "equipment_at_foreign": {"drop": 1, "unclassified": 2},
    "assigned_to_location_foreign": {"drop": 1},
    "log_slot_foreign": {"drop": 1, "unclassified": 3},
    "feeds_from_foreign": {"drop": 1, "unclassified": 1},
    "entry_for_species_foreign": {"drop": 2, "unclassified": 3},
}


def test_the_count_queries_measure_each_class(legacy) -> None:
    db, _ = legacy

    assert _counts(db) == EXPECTED


def test_a_dry_run_reports_the_same_numbers_and_writes_nothing(legacy) -> None:
    db, _ = legacy
    before = _snapshot(db)

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert _snapshot(db) == before
    assert report.details["workflow_templates_of_private_species__reown"] == 1
    assert report.details["slot_field_edge_disagreement__move_edge"] == 1
    assert report.details["entry_for_species_foreign__drop"] == 2
    assert report.details["slot_field_edge_disagreement__left_unclassified"] == 2


def test_the_migration_repairs_only_what_it_can_classify(legacy) -> None:
    db, e = legacy
    before = _snapshot(db)

    report = migration.up(db)

    assert report.changed == 1 + 1 + 1 + 1 + 1 + 1 + 2
    # class 1: re-owned to the species owner, nothing else touched
    assert db.collection(col.WORKFLOW_TEMPLATES).get("wt_private")["tenant_key"] == "A"
    for key in (
        "wt_global", "wt_legacy", "wt_own", "wt_system", "wt_manual", "wt_orphan", "wt_granted", "wt_dup",
    ):  # fmt: skip
        assert db.collection(col.WORKFLOW_TEMPLATES).get(key) == before[col.WORKFLOW_TEMPLATES][key] | {
            "_rev": db.collection(col.WORKFLOW_TEMPLATES).get(key)["_rev"]
        }
    # class 2: the edge followed the field, the ambiguous rows were left
    assert db.collection(col.HAS_SLOT).get(e["s_moved"])["_from"] == "locations/locA2"
    assert db.collection(col.HAS_SLOT).get(e["s_foreign"])["_from"] == "locations/locA1"
    assert db.collection(col.HAS_SLOT).get(e["s_ok"])["_from"] == "locations/locA1"
    assert db.collection(col.SLOTS).count() == 4
    # class 3: exactly the foreign edges are gone
    dropped = {
        col.EQUIPMENT_AT: ["eq_foreign"],
        col.ASSIGNED_TO_LOCATION: ["la_foreign"],
        col.LOG_SLOT: ["log_foreign"],
        col.FEEDS_FROM: ["feed_foreign"],
        col.ENTRY_FOR_SPECIES: ["en_foreign", "en_foreign_b"],
    }
    for collection, names in dropped.items():
        for name in names:
            assert not _exists(db, collection, e[name]), name
    for collection, names in {
        col.EQUIPMENT_AT: ["eq_ok", "eq_unstamped", "eq_siteless"],
        col.ASSIGNED_TO_LOCATION: ["la_ok"],
        col.LOG_SLOT: ["log_ok", "log_missing_slot", "log_on_hole_slot", "log_on_edgeless_slot"],
        col.FEEDS_FROM: ["feed_ok", "feed_global"],
        col.ENTRY_FOR_SPECIES: [
            "en_global",
            "en_own",
            "en_legacy_global",
            "en_granted",
            "en_lost_run",
            "en_post_fix",
            "en_undated",
        ],  # fmt: skip
    }.items():
        for name in names:
            assert _exists(db, collection, e[name]), name
    # no document of any vertex collection was touched except the re-owned template
    after = _snapshot(db)
    for name in _DOCS:
        if name == col.WORKFLOW_TEMPLATES:
            continue
        assert {k: {x: y for x, y in v.items() if x != "_rev"} for k, v in after[name].items()} == before[name]


def test_a_second_run_changes_nothing_and_the_residue_is_only_unclassified(legacy) -> None:
    db, _ = legacy
    migration.up(db)
    settled = _snapshot(db)

    report = migration.up(db)

    assert report.changed == 0
    assert _snapshot(db) == settled
    residue = _counts(db)
    for verdicts in residue.values():
        assert set(verdicts) <= {"unclassified", "left_granted", "left_owner_has_plan"}


def test_the_report_carries_counts_only(legacy) -> None:
    db, _ = legacy

    report = migration.up(db)

    assert all(isinstance(v, int) for v in report.details.values())


def test_a_database_without_the_collections_is_a_no_op(_database) -> None:
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    name = TEST_DATABASE + "_empty"
    if system.has_database(name):
        system.delete_database(name)
    system.create_database(name)
    try:
        empty = client.db(name, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        report = migration.up(empty)
        assert report.changed == 0
    finally:
        system.delete_database(name)
        client.close()
