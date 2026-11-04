"""WP 8.2 (#2645) — the daily consistency job measured on a real ArangoDB.

The job runs with the production reader (the scan it shares with the M4 migration) and the production writer over the
unique ``source_ref`` index, on stored shapes: a watering that only knows slots, a feeding a task completion already
logged (its care event carries the same ``source_ref``), a source older than the window.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.care_event_gap_repository import ArangoCareEventGapReader
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.services.care_event_consistency_service import CareEventConsistencyService
from app.migrations.versions import v0104_care_events_backfill as v0104
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the job's scan resolves references in AQL over a real server"),
]

_DB_NAME = run_database_name("care_events_consistency")
NOW = datetime.now(UTC)
RECENT = (NOW - timedelta(days=2)).isoformat()
OLD = (NOW - timedelta(days=30)).isoformat()


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


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    _insert(db.collection(col.SITES), [{"_key": "S1", "tenant_key": "t1"}, {"_key": "S2", "tenant_key": "t2"}])
    _insert(db.collection(col.LOCATIONS), [{"_key": "L1", "site_key": "S1"}, {"_key": "L2", "site_key": "S2"}])
    _insert(db.collection(col.SLOTS), [{"_key": "s1", "slot_id": "SLOT-1", "location_key": "L1"}])
    _insert(
        db.collection(col.PLANT_INSTANCES),
        [
            {"_key": "p1", "instance_id": "P1", "tenant_key": "t1", "location_key": "L1", "site_key": "S1"},
            {"_key": "p2", "instance_id": "P2", "tenant_key": "t2", "location_key": "L2", "site_key": "S2"},
        ],
    )
    _insert(
        db.collection(col.WATERING_EVENTS),
        [
            {"_key": "w_gap", "tenant_key": "t1", "watered_at": RECENT, "volume_liters": 2.0, "slot_keys": ["s1"]},
            {"_key": "w_old", "tenant_key": "t1", "watered_at": OLD, "volume_liters": 2.0, "plant_keys": ["p1"]},
            {"_key": "w_closed", "tenant_key": "t2", "watered_at": RECENT, "volume_liters": 2.0, "plant_keys": ["p2"]},
            {"_key": "w_cross", "tenant_key": "t2", "watered_at": RECENT, "volume_liters": 2.0, "plant_keys": ["p1"]},
        ],
    )
    _insert(
        db.collection(col.FEEDING_EVENTS),
        [{"_key": "f_logged", "tenant_key": "t1", "timestamp": RECENT, "plant_key": "p1"}],
    )
    _insert(
        db.collection(col.CARE_EVENTS),
        [
            {
                "tenant_key": "t1",
                "site_key": "S1",
                "location_key": "L1",
                "category": "feeding",
                "performed_at": RECENT,
                "trigger": "task",
                "source_ref": {"collection": "feeding_events", "key": "f_logged"},
            }
        ],
    )


def _service(db, active: set[str]) -> CareEventConsistencyService:  # type: ignore[no-untyped-def]
    return CareEventConsistencyService(
        ArangoCareEventGapReader(db), ArangoCareEventRepository(db), lambda tenant: tenant in active
    )


def _sources(db) -> set[tuple[str, str]]:  # type: ignore[no-untyped-def]
    return {
        (d["source_ref"]["collection"], d["source_ref"]["key"])
        for d in db.collection(col.CARE_EVENTS).all()
        if d.get("trigger") == "backfill"
    }


def test_a_gap_inside_the_window_is_closed_and_the_next_run_has_zero_hits(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    service = _service(db, {"t1"})

    first = service.run(now=NOW, window_days=7)
    revs = {d["_key"]: d["_rev"] for d in db.collection(col.CARE_EVENTS).all()}
    second = service.run(now=NOW, window_days=7)

    assert _sources(db) == {("watering_events", "w_gap")}
    assert first.hits == 1 and first.backfilled["watering_events"] == 1
    assert first.skipped_inactive_tenant == 1  # w_closed: its tenant is not active
    assert first.without_bed["watering_events"] == 1  # w_cross: the document says t2, the bed's site t1
    assert first.already_present == 1  # f_logged, logged by its task completion
    assert second.hits == 0
    assert {d["_key"]: d["_rev"] for d in db.collection(col.CARE_EVENTS).all()} == revs


def test_the_written_event_is_the_one_the_backfill_mapper_makes(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    _service(db, {"t1"}).run(now=NOW, window_days=7)

    stored = next(d for d in db.collection(col.CARE_EVENTS).all() if d.get("trigger") == "backfill")
    assert (stored["tenant_key"], stored["site_key"], stored["location_key"]) == ("t1", "S1", "L1")
    assert (stored["category"], stored["quantity"], stored["unit"]) == ("watering", 2.0, "l")
    assert "performed_by_user_key" not in stored
    # read back by the production read path
    rows = ArangoCareEventRepository(db).list_events(CareEventFilter(), tenant_key="t1", offset=0, limit=50)
    assert {row.event.trigger for row in rows} == {"task", "backfill"}


def test_a_source_older_than_the_window_is_not_the_jobs_to_repair(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)

    _service(db, {"t1"}).run(now=NOW, window_days=7)
    assert ("watering_events", "w_old") not in _sources(db)

    # counter-case: the same source IS found once the window reaches it
    _service(db, {"t1"}).run(now=NOW, window_days=60)
    assert ("watering_events", "w_old") in _sources(db)


def test_a_tenant_that_becomes_active_again_is_repaired_by_the_next_run(db) -> None:  # type: ignore[no-untyped-def]
    _seed(db)
    _service(db, {"t1"}).run(now=NOW, window_days=7)
    assert ("watering_events", "w_closed") not in _sources(db)

    again = _service(db, {"t1", "t2"}).run(now=NOW, window_days=7)

    assert again.hits == 1
    assert ("watering_events", "w_closed") in _sources(db)


def test_the_job_and_the_migration_read_the_same_scan(db) -> None:  # type: ignore[no-untyped-def]
    """One resolution, not two: the migration's scan and the job's reader return the same rows."""
    _seed(db)
    since = NOW - timedelta(days=60)
    cutoff_ms = int(since.timestamp() * 1000)

    for source in ("watering_events", "feeding_events"):
        from_job = list(ArangoCareEventGapReader(db).candidates(source, since))
        from_migration = list(v0104._scan(db, source, cutoff_ms))
        assert from_job == from_migration
    assert any(row["present"] for row in ArangoCareEventGapReader(db).candidates("feeding_events", since))
