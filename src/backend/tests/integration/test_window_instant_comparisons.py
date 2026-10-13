"""#1784 — date windows and other clock reads compare instants, against a real ArangoDB.

The companion of ``test_retention_instant_comparisons.py`` (read its docstring
for the defect class: ICU collation orders ``.`` before ``+`` and ``Z``, so a
timestamp compared as text can land on the wrong side of a cutoff). This module
covers the selectors that do not fit its one-cutoff table:

* **range reads** (``>= @start AND <= @end``) — the calendar sources and the tank
  fill statistics. Four records per range, one per edge and side, each 0.5 s
  from its bound and spelled differently from it;
* **selectors that read the wall clock themselves** (``datetime.now`` inside the
  method) — overdue tasks, yield statistics, recent IPM applications. Their
  cutoff cannot be pinned, so they are
  measured with a spelling whose error is **hours**, not half a second: the same
  instant written with a non-UTC offset. ``T+1h`` written as ``-05:00`` reads as
  ``T-4h`` to a string comparison;
* the diary overview's lease and the orphaned task-photo age floor, whose
  cutoff is a parameter.

Two neighbouring defects are deliberately **not** covered here and are tracked
separately: the Karenz list (``DATE_ADD(…) > DATE_NOW()`` compares a string with
a number) and the crop-rotation history (a ``date`` field against a datetime
string).

No personal data: every value is synthetic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.calendar_source_repository import ArangoCalendarSourceRepository
from app.data_access.arango.harvest_repository import ArangoHarvestRepository
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("window_cmp")
TENANT = "tenant-window"

#: Offsets that move the *text* of an instant by hours while the instant stays put.
EAST = timezone(timedelta(hours=5))
WEST = timezone(timedelta(hours=-5))

_DOCUMENT_COLLECTIONS = (
    col.TASKS,
    col.WATERING_LOGS,
    col.MAINTENANCE_LOGS,
    col.TANKS,
    col.TANK_FILL_EVENTS,
    col.PLANT_INSTANCES,
    col.HARVEST_BATCHES,
    col.YIELD_METRICS,
    col.TREATMENTS,
    col.TREATMENT_APPLICATIONS,
    col.PLANT_DIARY_ENTRIES,
    col.ATTACHMENTS,
)


pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The attachment sweep reads every photo carrier; which ones is the
    # repository's business, not this test's (the carrier cases live in
    # ``test_orphaned_task_photo_query.py``).
    carriers = {
        name
        for bind, name in ArangoAttachmentRepository(db)._reference_bind_vars().items()  # noqa: SLF001
        if bind.startswith("@")
    }
    for name in dict.fromkeys([*_DOCUMENT_COLLECTIONS, *sorted(carriers)]):
        if not db.has_collection(name):
            db.create_collection(name)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    for collection in database.collections():
        if not collection["system"]:
            database.collection(collection["name"]).truncate()
    return database


# ── range reads ───────────────────────────────────────────────────────────────

#: ``(record, start, end, inside)`` — each record 0.5 s from one bound, spelled
#: differently from that bound. The far bound is far enough not to matter.
RANGE_CASES = [
    pytest.param(
        "2025-09-25T04:30:00.500000Z",
        "2025-09-25T04:30:00+00:00",
        "2025-09-26T00:00:00+00:00",
        True,
        id="0.5s-after-start-is-inside",
    ),
    pytest.param(
        "2025-09-25T04:29:59Z",
        "2025-09-25T04:29:59.5Z",
        "2025-09-26T00:00:00+00:00",
        False,
        id="0.5s-before-start-is-outside",
    ),
    pytest.param(
        "2025-09-25T04:59:59+00:00",
        "2025-09-24T00:00:00+00:00",
        "2025-09-25T04:59:59.5Z",
        True,
        id="0.5s-before-end-is-inside",
    ),
    pytest.param(
        "2025-09-25T05:00:00.5Z",
        "2025-09-24T00:00:00+00:00",
        "2025-09-25T05:00:00+00:00",
        False,
        id="0.5s-after-end-is-outside",
    ),
]


class TestCalendarSources:
    """``ArangoCalendarSourceRepository`` — the binds are ``isoformat()`` of the window (CalendarService)."""

    @pytest.mark.parametrize(("record", "start", "end", "inside"), RANGE_CASES)
    def test_watering_logs(self, db, record: str, start: str, end: str, inside: bool):
        db.collection(col.WATERING_LOGS).insert({"_key": "w1", "tenant_key": TENANT, "logged_at": record})

        rows = ArangoCalendarSourceRepository(db).list_watering_logs(start, end, tenant_key=TENANT)

        assert (len(rows) == 1) is inside

    @pytest.mark.parametrize(("record", "start", "end", "inside"), RANGE_CASES)
    def test_tasks_due(self, db, record: str, start: str, end: str, inside: bool):
        db.collection(col.TASKS).insert({"_key": "t1", "tenant_key": TENANT, "name": "Giessen", "due_date": record})

        rows = ArangoCalendarSourceRepository(db).list_tasks_due(start, end, tenant_key=TENANT)

        assert (len(rows) == 1) is inside

    @pytest.mark.parametrize(("record", "start", "end", "inside"), RANGE_CASES)
    def test_maintenance_logs(self, db, record: str, start: str, end: str, inside: bool):
        db.collection(col.TANKS).insert({"_key": "tank1", "tenant_key": TENANT})
        db.collection(col.MAINTENANCE_LOGS).insert({"_key": "m1", "tank_key": "tank1", "performed_at": record})

        rows = ArangoCalendarSourceRepository(db).list_maintenance_logs(start, end, tenant_key=TENANT)

        assert (len(rows) == 1) is inside


class TestTankFillStatistics:
    @pytest.mark.parametrize(("record", "start", "end", "inside"), RANGE_CASES)
    def test_a_fill_event_is_counted_by_its_instant(self, db, record: str, start: str, end: str, inside: bool):
        db.collection(col.TANK_FILL_EVENTS).insert(
            {"tank_key": "tank1", "fill_type": "full_change", "volume_liters": 10.0, "filled_at": record}
        )

        stats = ArangoTankRepository(db).get_fill_event_stats("tank1", start, end)

        assert stats["total_count"] == (1 if inside else 0), stats

    def test_an_undated_fill_event_is_not_counted_inside_a_window(self, db):
        db.collection(col.TANK_FILL_EVENTS).insert(
            {"tank_key": "tank1", "fill_type": "full_change", "volume_liters": 10.0}
        )

        stats = ArangoTankRepository(db).get_fill_event_stats(
            "tank1", "2025-09-24T00:00:00+00:00", "2025-09-26T00:00:00+00:00"
        )

        assert stats["total_count"] == 0, stats


# ── selectors that read the wall clock themselves ─────────────────────────────


def _offset_spelling(instant: datetime, zone: timezone) -> str:
    return instant.astimezone(zone).isoformat()


class TestOverdueTasks:
    def test_a_task_due_in_an_hour_is_not_overdue_whatever_its_offset(self, db):
        due = _offset_spelling(datetime.now(UTC) + timedelta(hours=1), WEST)
        db.collection(col.TASKS).insert(
            {"_key": "t1", "tenant_key": TENANT, "name": "Giessen", "status": "pending", "due_date": due}
        )

        overdue = ArangoTaskRepository(db).get_overdue_tasks(tenant_key=TENANT)

        assert [task.key for task in overdue] == [], f"{due} is an hour ahead; as text it reads 4 h ago"

    def test_a_task_due_an_hour_ago_is_overdue_whatever_its_offset(self, db):
        due = _offset_spelling(datetime.now(UTC) - timedelta(hours=1), EAST)
        db.collection(col.TASKS).insert(
            {"_key": "t1", "tenant_key": TENANT, "name": "Giessen", "status": "pending", "due_date": due}
        )

        overdue = ArangoTaskRepository(db).get_overdue_tasks(tenant_key=TENANT)

        assert [task.key for task in overdue] == ["t1"], f"{due} is an hour ago; as text it reads 4 h ahead"


class TestYieldStatistics:
    def _seed(self, db: StandardDatabase, harvest_date: str) -> None:
        db.collection(col.PLANT_INSTANCES).insert({"_key": "p1", "tenant_key": TENANT, "species_key": "s1"})
        db.collection(col.HARVEST_BATCHES).insert(
            {"_key": "hb1", "tenant_key": TENANT, "plant_key": "p1", "harvest_date": harvest_date}
        )
        db.collection(col.YIELD_METRICS).insert({"batch_key": "hb1", "total_yield_g": 100.0})

    def test_a_harvest_just_inside_the_window_counts(self, db):
        cutoff = datetime.now(UTC) - timedelta(days=1)
        self._seed(db, _offset_spelling(cutoff + timedelta(hours=1), WEST))

        stats = ArangoHarvestRepository(db).get_yield_statistics_for_species("s1", days_back=1, tenant_key=TENANT)

        assert stats["batch_count"] == 1

    def test_a_harvest_just_outside_the_window_does_not(self, db):
        cutoff = datetime.now(UTC) - timedelta(days=1)
        self._seed(db, _offset_spelling(cutoff - timedelta(hours=1), EAST))

        stats = ArangoHarvestRepository(db).get_yield_statistics_for_species("s1", days_back=1, tenant_key=TENANT)

        assert stats["batch_count"] == 0


class TestRecentIpmApplications:
    def _seed(self, db: StandardDatabase, applied_at: str) -> None:
        db.collection(col.TREATMENTS).insert({"_key": "tr1", "name": "Neem", "treatment_type": "biological"})
        db.collection(col.TREATMENT_APPLICATIONS).insert(
            {"plant_key": "p1", "treatment_key": "tr1", "applied_at": applied_at}
        )

    def test_an_application_just_inside_the_window_counts(self, db):
        cutoff = datetime.now(UTC) - timedelta(days=1)
        self._seed(db, _offset_spelling(cutoff + timedelta(hours=1), WEST))

        assert len(ArangoIpmRepository(db).get_recent_applications("p1", days_window=1)) == 1

    def test_an_application_just_outside_the_window_does_not(self, db):
        cutoff = datetime.now(UTC) - timedelta(days=1)
        self._seed(db, _offset_spelling(cutoff - timedelta(hours=1), EAST))

        assert ArangoIpmRepository(db).get_recent_applications("p1", days_window=1) == []


# ── the diary work queue's lease, through the overview ────────────────────────


class TestDiaryOverviewLease:
    """The overview's displayed state reads the same lease as the queue (``_overview_body``)."""

    NOW = datetime(2025, 9, 25, 4, 30, tzinfo=UTC)

    def _entry(self, db: StandardDatabase, lease: str) -> None:
        db.collection(col.PLANT_DIARY_ENTRIES).insert(
            {
                "_key": "d1",
                "tenant_key": TENANT,
                "plant_key": "p1",
                "entry_type": "observation",
                "text": "Blatt gelb",
                "analysis_state": "in_progress",
                "analysis_lease_expires_at": lease,
            }
        )

    def test_a_lease_running_half_a_second_longer_is_still_in_progress(self, db):
        self._entry(db, "2025-09-25T04:30:00.500000Z")

        _, waiting = ArangoPlantDiaryRepository(db).list_overview(
            TENANT, DiaryOverviewFilter(analysis_states=("requested",)), now=self.NOW
        )

        assert waiting == 0

    def test_a_lease_ended_half_a_second_ago_is_back_in_the_queue(self, db):
        self._entry(db, "2025-09-25T04:29:59Z")

        _, waiting = ArangoPlantDiaryRepository(db).list_overview(
            TENANT,
            DiaryOverviewFilter(analysis_states=("requested",)),
            now=datetime(2025, 9, 25, 4, 29, 59, 500000, tzinfo=UTC),
        )

        assert waiting == 1


# ── the orphaned task-photo sweep ─────────────────────────────────────────────


class TestOrphanedTaskPhotoAge:
    """The age floor of ``find_orphaned_task_photos`` (#1393) is an instant comparison."""

    def _photo(self, db: StandardDatabase, created_at: str) -> None:
        db.collection(col.ATTACHMENTS).insert(
            {
                "_key": "orphan",
                "tenant_key": TENANT,
                "mime_type": "image/jpeg",
                "byte_size": 1000,
                "sha256": "sha-orphan",
                "original_filename": "orphan.jpg",
                "created_by": "user-1",
                "category": "task",
                "storage_key": f"{TENANT}/task/orphan.jpg",
                "created_at": created_at,
            }
        )

    def test_a_photo_half_a_second_younger_than_the_floor_survives(self, db):
        self._photo(db, "2025-09-25T04:30:00.500000Z")

        found = ArangoAttachmentRepository(db).find_orphaned_task_photos(
            older_than=datetime(2025, 9, 25, 4, 30, tzinfo=UTC)
        )

        assert found == []

    def test_a_photo_half_a_second_older_than_the_floor_is_found(self, db):
        self._photo(db, "2025-09-25T04:29:59Z")

        found = ArangoAttachmentRepository(db).find_orphaned_task_photos(
            older_than=datetime(2025, 9, 25, 4, 29, 59, 500000, tzinfo=UTC)
        )

        assert [attachment.key for attachment in found] == ["orphan"]
