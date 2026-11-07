"""WP 8.1 (#2644) — v0104 ``M4_care_events_backfill`` measured on a real ArangoDB (prod point P-6).

Rows: GP-FR-105 (the backfill half), GP-NFR-015 (migration M4 with its dry-run report).

The scan resolves ``plant / slot -> location -> site`` in AQL and the writer is the production
:class:`ArangoCareEventRepository` over the unique-sparse ``source_ref`` index — both are exercised here on the
stored shapes (a task completion's own ``care_event`` with ``source_ref``, a watering that only knows slots, a
treatment with an account reference and one with a typed name). The run reads back through the production read path
(``list_events``) so a document the reads cannot see would fail here, not in production.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0104_care_events_backfill.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.migrations.versions import v0104_care_events_backfill as v0104
from app.migrations.versions.v0104_care_events_backfill import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan resolves references in AQL over a real server"),
]

_DB_NAME = run_database_name("v0104_care_events_backfill")

NOW = datetime.now(UTC)
RECENT = (NOW - timedelta(days=30)).isoformat()
SIX_YEARS = (NOW - timedelta(days=6 * 366)).isoformat()


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


def _insert(collection, docs: list[dict]) -> None:  # type: ignore[no-untyped-def]
    refused = [r for r in collection.insert_many(docs) if isinstance(r, Exception)]
    assert not refused, refused


def _seed_beds(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db.collection(col.SITES),
        [{"_key": "S1", "tenant_key": "t1"}, {"_key": "S2", "tenant_key": "t2"}, {"_key": "S0"}],  # S0: legacy
    )
    _insert(
        db.collection(col.LOCATIONS),
        [
            {"_key": "L1", "site_key": "S1"},
            {"_key": "L1b", "site_key": "S1"},
            {"_key": "L2", "site_key": "S2"},
            {"_key": "L0", "site_key": "S0"},
        ],
    )
    _insert(
        db.collection(col.SLOTS),
        [
            {"_key": "s1", "slot_id": "SLOT-1", "location_key": "L1"},
            {"_key": "s0", "slot_id": "SLOT-0", "location_key": "L0"},
        ],
    )
    _insert(
        db.collection(col.PLANT_INSTANCES),
        [
            {"_key": "p1", "instance_id": "P1", "tenant_key": "t1", "location_key": "L1", "site_key": "S1"},
            # written before v0100: only the slot says where it stands
            {"_key": "p2", "instance_id": "P2", "tenant_key": "t1", "slot_key": "s1"},
            {"_key": "p3", "instance_id": "P3", "tenant_key": "t2", "location_key": "L2", "site_key": "S2"},
            {"_key": "p4", "instance_id": "P4", "tenant_key": "t1", "location_key": "L1b", "site_key": "S1"},
            {"_key": "p0", "instance_id": "P0", "tenant_key": "t1", "slot_key": "s0"},
        ],
    )


def _seed_sources(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db.collection(col.WATERING_EVENTS),
        [
            {"_key": "w_slot", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 2.0, "slot_keys": ["s1"]},
            {"_key": "w_plant", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]},
            # stamped with another tenant than the bed's site
            {"_key": "w_cross", "tenant_key": "t2", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]},
            {"_key": "w_nostamp", "tenant_key": "", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]},
            # a plant of t2 named by a t1 document
            {
                "_key": "w_foreign_plant",
                "tenant_key": "t1",
                "watered_at": RECENT,
                "volume_liters": 1.0,
                "plant_keys": ["p3"],
            },
            {
                "_key": "w_two_beds",
                "tenant_key": "t1",
                "watered_at": RECENT,
                "volume_liters": 1.0,
                "plant_keys": ["p1", "p4"],
            },
            {"_key": "w_nobed", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0},
            {"_key": "w_ghost", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["gone"]},
            {
                "_key": "w_half",
                "tenant_key": "t1",
                "watered_at": RECENT,
                "volume_liters": 1.0,
                "plant_keys": ["p1", "gone"],
            },
            {
                "_key": "w_legacy_site",
                "tenant_key": "t1",
                "watered_at": RECENT,
                "volume_liters": 1.0,
                "plant_keys": ["p0"],
            },
            {"_key": "w_old", "tenant_key": "t1", "watered_at": SIX_YEARS, "volume_liters": 1.0, "plant_keys": ["p1"]},
            {"_key": "w_nodate", "tenant_key": "t1", "volume_liters": 1.0, "plant_keys": ["p1"]},
            {
                "_key": "w_baddate",
                "tenant_key": "t1",
                "watered_at": "not a date",
                "volume_liters": 1.0,
                "plant_keys": ["p1"],
            },
        ],
    )
    _insert(
        db.collection(col.FEEDING_EVENTS),
        [
            # logged by a task completion: its care event carries the same source_ref already
            {"_key": "f_task", "tenant_key": "t1", "timestamp": RECENT, "plant_key": "p1", "plant_keys": ["p1"]},
            {
                "_key": "f_bed",
                "tenant_key": "t1",
                "timestamp": RECENT,
                "plant_key": "",
                "location_key": "L1",
                "dose_quantity": 30,
                "dose_unit": "g_per_m2",
            },
            {
                "_key": "f_plant",
                "tenant_key": "t1",
                "timestamp": RECENT,
                "plant_key": "p2",
                "volume_applied_liters": 1.5,
            },
        ],
    )
    _insert(
        db.collection(col.TREATMENT_APPLICATIONS),
        [
            {
                "_key": "tr_account",
                "tenant_key": "t1",
                "applied_at": RECENT,
                "plant_key": "p1",
                "dosage": 5.0,
                "applied_by": "Anna Beispiel",
                "applied_by_key": "u1",
                "notes": "call 0123",
            },
            {
                "_key": "tr_text",
                "tenant_key": "t1",
                "applied_at": RECENT,
                "plant_key": "p1",
                "dosage": 5.0,
                "applied_by": "Anna Beispiel",
                "applied_by_key": None,
            },
        ],
    )
    _insert(
        db.collection(col.HARVEST_BATCHES),
        [
            {
                "_key": "h_plant",
                "tenant_key": "t1",
                "harvest_date": RECENT,
                "plant_key": "p2",
                "wet_weight_g": 80.0,
                "harvested_by_key": "u2",
                "harvester": "Bob",
            },
            {"_key": "h_bed_level", "tenant_key": "t1", "harvest_date": RECENT, "plant_key": "", "wet_weight_g": 10.0},
        ],
    )
    # the line a task completion wrote together with ``f_task`` (WP 4.3) and two lines that are no backfill of ours
    _insert(
        db.collection(col.CARE_EVENTS),
        [
            {
                "_key": "ce_task",
                "tenant_key": "t1",
                "site_key": "S1",
                "location_key": "L1",
                "category": "feeding",
                "performed_at": RECENT,
                "trigger": "task",
                "source_ref": {"collection": "feeding_events", "key": "f_task"},
            },
            {
                "_key": "ce_manual",
                "tenant_key": "t1",
                "site_key": "S1",
                "location_key": "L1",
                "category": "note",
                "performed_at": RECENT,
                "trigger": "manual",
                "summary": "mine",
            },
            # the crop-rotation backfill of WP 3.4: trigger backfill, but no source_ref — never ours to touch
            {
                "_key": "ce_rotation",
                "tenant_key": "t1",
                "site_key": "S1",
                "location_key": "L1",
                "category": "planting",
                "performed_at": RECENT,
                "trigger": "backfill",
                "summary": "Backfill 2024",
            },
        ],
    )


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    _seed_beds(db)
    _seed_sources(db)


#: What the seeded volume must yield, per source: written / already present / without bed (by reason) / window.
_WRITTEN = {
    "watering_events": ["w_plant", "w_slot"],
    "feeding_events": ["f_bed", "f_plant"],
    "treatment_applications": ["tr_account", "tr_text"],
    "harvest_batches": ["h_plant"],
}

_WITHOUT_BED = {
    "watering_events": {
        "tenant_mismatch": ["w_cross", "w_foreign_plant", "w_nostamp"],
        "multiple_beds": ["w_two_beds"],
        "no_reference": ["w_nobed"],
        "unresolved": ["w_ghost"],
        "partly_unresolved": ["w_half"],
        "site_without_tenant": ["w_legacy_site"],
    },
    "harvest_batches": {"no_reference": ["h_bed_level"]},
}


def _events(db) -> list[dict[str, Any]]:  # type: ignore[no-untyped-def]
    return sorted(db.collection(col.CARE_EVENTS).all(), key=lambda d: d["_key"])


def _backfilled(db) -> dict[tuple[str, str], dict[str, Any]]:  # type: ignore[no-untyped-def]
    return {
        (d["source_ref"]["collection"], d["source_ref"]["key"]): d
        for d in _events(db)
        if d.get("trigger") == "backfill" and d.get("source_ref")
    }


def test_the_dry_run_writes_nothing_and_its_counts_add_up(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    before = {d["_key"]: d["_rev"] for d in _events(db)}

    report = migration.up(db, dry_run=True)

    assert {d["_key"]: d["_rev"] for d in _events(db)} == before
    assert db.collection(col.CARE_EVENT_AT).count() == 0
    assert report.dry_run is True and report.changed == 0
    sources = report.details["sources"]
    for name, written in _WRITTEN.items():
        assert sources[name]["will_write"] == len(written), name
        assert sources[name]["written"] == 0
    for name, entry in sources.items():
        assert entry["read"] == (
            entry["will_write"]
            + entry["already_present"]
            + entry["without_bed"]
            + entry["outside_r25"]
            + entry["no_timestamp"]
        ), name
    totals = report.details["totals"]
    assert totals["counts_add_up"] is True
    assert report.scanned == totals["read"] == 13 + 3 + 2 + 2
    assert sources["watering_events"]["outside_r25"] == 1
    assert sources["watering_events"]["no_timestamp"] == 2  # no date at all, and "not a date"
    assert sources["feeding_events"]["already_present"] == 1  # f_task, logged by the task completion
    for name, reasons in _WITHOUT_BED.items():
        assert {r: b["listed"] for r, b in sources[name]["without_bed_reasons"].items()} == reasons, name
        assert sources[name]["without_bed"] == sum(len(keys) for keys in reasons.values())


class _PinnedClock(datetime):
    """``datetime`` whose ``now()`` is NOW, so two runs derive the same retention window."""

    @classmethod
    def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
        return NOW if tz is None else NOW.astimezone(tz)


def test_the_real_run_writes_what_the_dry_run_reported(db, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Both runs read the wall clock for the window start; across a second boundary the reports
    # differed in `window_start` alone (CI run 42090507688). The comparison is about the counts.
    monkeypatch.setattr(v0104, "datetime", _PinnedClock)
    _seed(db)

    dry = migration.up(db, dry_run=True)
    real = migration.up(db)

    assert real.dry_run is False
    assert real.changed == real.details["totals"]["written"] == dry.details["totals"]["will_write"] == 7
    for source in v0104.SOURCE_COLLECTIONS:
        assert real.details["sources"][source]["will_write"] == real.details["sources"][source]["written"]
    # everything but the writes themselves is the dry run's report
    for report in (dry, real):
        for entry in report.details["sources"].values():
            entry.pop("written")
            entry.pop("will_write")
        report.details["totals"].pop("written")
        report.details["totals"].pop("will_write")
    assert dry.details == real.details
    stored = _backfilled(db)
    assert sorted(f"{c}/{k}" for c, k in stored) == sorted(
        f"{source}/{key}" for source, keys in _WRITTEN.items() for key in keys
    )


def test_a_second_run_writes_zero_rows(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    migration.up(db)
    revs = {d["_key"]: d["_rev"] for d in _events(db)}
    edges = db.collection(col.CARE_EVENT_AT).count()

    second = migration.up(db)

    assert second.changed == 0
    assert second.details["totals"]["will_write"] == 0
    assert second.details["totals"]["already_present"] == 7 + 1  # our seven and the task completion's line
    assert second.details["totals"]["counts_add_up"] is True
    assert {d["_key"]: d["_rev"] for d in _events(db)} == revs
    assert db.collection(col.CARE_EVENT_AT).count() == edges


def test_the_tenant_comes_from_the_beds_site_and_never_from_the_document(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    migration.up(db)

    stored = _backfilled(db)
    for key in (
        "w_cross",
        "w_nostamp",
        "w_foreign_plant",
        "w_two_beds",
        "w_nobed",
        "w_ghost",
        "w_half",
        "w_legacy_site",
    ):
        assert ("watering_events", key) not in stored, key
    assert {d["tenant_key"] for d in stored.values()} == {"t1"}
    assert {d["site_key"] for d in stored.values()} == {"S1"}
    # the foreign-stamped document is still there and untouched: the migration only reads sources
    assert db.collection(col.WATERING_EVENTS).get("w_cross")["tenant_key"] == "t2"


def test_the_events_carry_the_marker_the_source_and_only_what_the_source_states(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    migration.up(db)

    stored = _backfilled(db)
    slot = stored[("watering_events", "w_slot")]
    assert (slot["trigger"], slot["category"], slot["location_key"], slot["quantity"], slot["unit"]) == (
        "backfill",
        "watering",
        "L1",
        2.0,
        "l",
    )
    assert slot["plant_keys"] == []  # a slot reference names no plant
    assert slot["performed_at"][:19] == RECENT[:19]
    plant = stored[("watering_events", "w_plant")]
    assert plant["plant_keys"] == ["p1"]
    # a plant that only knows its slot is found through the slot
    assert stored[("feeding_events", "f_plant")]["location_key"] == "L1"
    assert stored[("harvest_batches", "h_plant")]["location_key"] == "L1"
    # a feeding names its bed itself
    bed = stored[("feeding_events", "f_bed")]
    assert (bed["location_key"], bed["quantity"], bed["unit"]) == ("L1", 30.0, "g_per_m2")
    # performer: only from an account reference
    assert stored[("treatment_applications", "tr_account")]["performed_by_user_key"] == "u1"
    assert "performed_by_user_key" not in stored[("treatment_applications", "tr_text")]
    assert stored[("harvest_batches", "h_plant")]["performed_by_user_key"] == "u2"
    assert "performed_by_user_key" not in slot
    # no unit in the source, no quantity; no free text copied
    assert "quantity" not in stored[("treatment_applications", "tr_account")]
    assert "Anna" not in str(stored[("treatment_applications", "tr_account")])
    assert "0123" not in str(stored[("treatment_applications", "tr_account")])


def test_the_window_is_the_retention_window_of_the_care_log(db) -> None:  # type: ignore[no-untyped-def]
    """The edge of R-25: a source just inside is written, one just outside is counted and not written."""
    _seed_beds(db)
    cutoff = v0104.window_start(datetime.now(UTC), v0104._window_years()) + timedelta(days=v0104._WINDOW_MARGIN_DAYS)
    inside = (cutoff + timedelta(hours=2)).isoformat()
    outside = (cutoff - timedelta(hours=2)).isoformat()
    _insert(
        db.collection(col.WATERING_EVENTS),
        [
            {"_key": "in", "tenant_key": "t1", "watered_at": inside, "volume_liters": 1.0, "plant_keys": ["p1"]},
            {"_key": "out", "tenant_key": "t1", "watered_at": outside, "volume_liters": 1.0, "plant_keys": ["p1"]},
        ],
    )

    report = migration.up(db)

    assert set(_backfilled(db)) == {("watering_events", "in")}
    assert report.details["sources"]["watering_events"]["outside_r25"] == 1


def test_what_the_migration_wrote_is_read_back_by_the_production_reads(db) -> None:  # type: ignore[no-untyped-def]
    """The same path the bed history uses: a document its reads cannot validate would not show up here."""
    _seed(db)
    migration.up(db)
    repo = ArangoCareEventRepository(db)

    rows = repo.list_events(CareEventFilter(location_key="L1"), tenant_key="t1", offset=0, limit=100)

    backfilled = [row.event for row in rows if row.event.trigger == "backfill" and row.event.source_ref]
    assert len(backfilled) == 7
    assert {e.category for e in backfilled} == {"watering", "feeding", "pest_control", "harvest"}
    # the other tenant sees none of it
    assert repo.list_events(CareEventFilter(), tenant_key="t2", offset=0, limit=100) == []
    # the edges the production writer makes: the bed and one edge per plant
    assert db.collection(col.CARE_EVENT_AT).count() == 7
    assert db.collection(col.CARE_EVENT_FOR).count() == sum(len(e.plant_keys) for e in backfilled)


def test_a_volume_over_one_batch_is_written_whole_and_only_once(db) -> None:  # type: ignore[no-untyped-def]
    _seed_beds(db)
    count = v0104._BATCH_SIZE * 2 + 37
    _insert(
        db.collection(col.WATERING_EVENTS),
        [
            {"_key": f"w{i:05d}", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]}
            for i in range(count)
        ],
    )

    first = migration.up(db)
    second = migration.up(db)

    assert first.changed == count
    assert len(_backfilled(db)) == count
    assert second.changed == 0 and second.details["totals"]["already_present"] == count


def test_a_line_logged_between_scan_and_write_is_present_not_a_failure_and_not_a_duplicate(db) -> None:  # type: ignore[no-untyped-def]
    """The unique index decides: a concurrent writer's line makes the batch fall back and count it as present."""
    _seed_beds(db)
    _insert(
        db.collection(col.WATERING_EVENTS),
        [
            {"_key": "a", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]},
            {"_key": "b", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 1.0, "plant_keys": ["p1"]},
        ],
    )
    original_scan = v0104._scan

    def scan_then_log(database, source, cutoff_ms):  # type: ignore[no-untyped-def]
        cursor = original_scan(database, source, cutoff_ms)
        if source == "watering_events":  # a task completion logs ``b`` after the scan fixed its result
            database.collection(col.CARE_EVENTS).insert(
                {
                    "tenant_key": "t1",
                    "site_key": "S1",
                    "location_key": "L1",
                    "category": "watering",
                    "performed_at": RECENT,
                    "trigger": "task",
                    "source_ref": {"collection": "watering_events", "key": "b"},
                }
            )
        return cursor

    v0104._scan = scan_then_log
    try:
        report = migration.up(db)
    finally:
        v0104._scan = original_scan

    assert report.details["sources"]["watering_events"]["will_write"] == 1
    assert report.details["sources"]["watering_events"]["already_present"] == 1
    assert report.details["totals"]["counts_add_up"] is True
    refs = [d["source_ref"]["key"] for d in _events(db) if d.get("source_ref")]
    assert sorted(refs) == ["a", "b"]


class TestDown:
    def test_it_deletes_the_backfilled_lines_and_their_edges_and_nothing_else(self, db) -> None:  # type: ignore[no-untyped-def]
        _seed(db)
        migration.up(db)
        assert len(_backfilled(db)) == 7

        report = migration.down(db)

        assert report.details["removed"] == report.changed == 7
        remaining = {d["_key"] for d in _events(db)}
        # the task completion's line, the manual note and the rotation backfill (no source_ref) stay
        assert remaining == {"ce_task", "ce_manual", "ce_rotation"}
        assert db.collection(col.CARE_EVENT_AT).count() == 0
        assert db.collection(col.CARE_EVENT_FOR).count() == 0
        # and the sources are as they were
        assert db.collection(col.WATERING_EVENTS).count() == 13

    def test_a_dry_run_removes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        _seed(db)
        migration.up(db)
        revs = {d["_key"]: d["_rev"] for d in _events(db)}

        report = migration.down(db, dry_run=True)

        assert report.details["will_remove"] == 7
        assert {d["_key"]: d["_rev"] for d in _events(db)} == revs

    def test_a_line_a_person_corrected_voided_or_redacted_since_stays(self, db) -> None:  # type: ignore[no-untyped-def]
        _seed(db)
        migration.up(db)
        stored = _backfilled(db)
        events = db.collection(col.CARE_EVENTS)
        events.update({"_key": stored[("watering_events", "w_slot")]["_key"], "voided_at": RECENT})
        events.update({"_key": stored[("watering_events", "w_plant")]["_key"], "superseded_by_key": "x"})
        events.update({"_key": stored[("feeding_events", "f_bed")]["_key"], "redacted_at": RECENT})

        report = migration.down(db)

        assert report.details["kept_edited"] == 3
        assert report.details["removed"] == 4
        kept = {(d["source_ref"]["collection"], d["source_ref"]["key"]) for d in _events(db) if d.get("source_ref")}
        assert {("watering_events", "w_slot"), ("watering_events", "w_plant"), ("feeding_events", "f_bed")} <= kept

    def test_up_after_down_restores_the_same_lines(self, db) -> None:  # type: ignore[no-untyped-def]
        _seed(db)
        migration.up(db)
        before = sorted(_backfilled(db))
        migration.down(db)

        again = migration.up(db)

        assert again.changed == 7
        assert sorted(_backfilled(db)) == before


def test_a_treatment_keeps_the_longer_pflschg_window_like_the_retention_sweep(db, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R-17 longer than R-25: a six-year-old treatment is still retained, so it is backfilled; a watering is not."""
    monkeypatch.setattr(v0104.settings, "retention_treatment_min_retention_years", 8)
    _seed_beds(db)
    _insert(
        db.collection(col.TREATMENT_APPLICATIONS),
        [{"_key": "tr_old", "tenant_key": "t1", "applied_at": SIX_YEARS, "plant_key": "p1", "dosage": 1.0}],
    )
    _insert(
        db.collection(col.WATERING_EVENTS),
        [{"_key": "w_old", "tenant_key": "t1", "watered_at": SIX_YEARS, "volume_liters": 1.0, "plant_keys": ["p1"]}],
    )

    report = migration.up(db)

    assert set(_backfilled(db)) == {("treatment_applications", "tr_old")}
    assert report.details["sources"]["watering_events"]["outside_r25"] == 1
