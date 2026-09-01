"""Integration test for migration v0045 — reconcile duplicates, then constrain (#1301).

There is a running instance with real data, and it predates the constraint, so it
may well already hold duplicate open care tasks. Creating a unique index over a
key space that still contains collisions **fails**, which would take the deploy
down at startup. The migration therefore has to close the surplus first — and it
has to *materialise* the ``care_dedup_key`` computed value on the documents that
predate it, because configuring a computed value does not rewrite stored
documents. Skipping that backfill would leave an index that exists, reports
success and is inert for exactly the pre-existing data.

Both of those are properties of real ArangoDB behaviour (unique-index creation
refusing collisions; computed values not being retroactive), so a fake database
cannot certify either. This runs against a real server on the pre-#1301
collection shape, reconstructed by stripping the constraint that
``ensure_collections`` installs.

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

ARANGO_AVAILABLE = False
try:
    from arango import ArangoClient

    _probe = ArangoClient(hosts="http://localhost:8529")
    _probe.db("_system", username="root", password="rootpassword").version()
    ARANGO_AVAILABLE = True
    _probe.close()
except Exception:
    pass


pytestmark = [
    pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available"),
    pytest.mark.allow_db_connection("v0045 reconciles a real volume; index and computed-value semantics are the SUT"),
]

_DB_NAME = "kamerplanter_v0045_migration_test"
_TENANT = "tenant-alpha"
_PLANT = "plant-basil-1"


def _connect():
    from app.config.settings import Settings
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    return conn, conn.connect()


def _care_task(key: str, *, plant: str, reminder: str, status: str, due: datetime, created: datetime) -> dict:
    """A care-reminder task document in the exact shape ``build_care_reminder_task`` writes."""
    from app.common.enums import TaskCategory
    from app.data_access.arango import collections as col

    return {
        "_key": key,
        "tenant_key": _TENANT,
        "name": f"Basil{col.CARE_TASK_NAME_SEPARATOR}{reminder}",
        "category": TaskCategory.CARE_REMINDER.value,
        "entity_key": plant,
        "entity_type": "plant_instance",
        "status": status,
        "due_date": due.isoformat(),
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
    }


@pytest.fixture
def legacy_db():
    """A bootstrapped database rolled back to the **pre-v0045** ``tasks`` shape.

    ``ensure_collections`` now installs the computed value and the index, so the
    fixture strips both — otherwise the test would set up the very state the
    migration is supposed to reach and prove nothing about reaching it.
    """
    from app.data_access.arango import collections as col
    from app.data_access.arango.collections import ensure_collections

    conn, db = _connect()
    ensure_collections(db)

    handle = db.collection(col.TASKS)
    for idx in handle.indexes():
        if isinstance(idx, dict) and idx.get("fields") == col.CARE_TASK_DEDUP_INDEX_FIELDS:
            handle.delete_index(idx["id"], ignore_missing=True)
    handle.configure(computed_values=[])
    handle.truncate()

    assert not col.has_care_task_dedup_computed_value(handle)

    yield db

    conn.close()
    system = ArangoClient(hosts="http://localhost:8529").db("_system", username="root", password="rootpassword")
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


@pytest.fixture
def duplicated(legacy_db):
    """Seed the shape a live volume is assumed to be in: duplicates already present.

    Three open watering tasks for one plant (what four racing producers leave
    behind), one open *fertilizing* task for the same plant (a different reminder
    type — must survive untouched), one open watering task for a **second** plant
    (must survive), and two completed watering tasks for the first plant (normal
    history — a constraint that touched these would break watering a plant twice).
    """
    from app.common.enums import TaskStatus
    from app.data_access.arango import collections as col

    now = datetime.now(UTC)
    docs = [
        _care_task(
            "dup-oldest",
            plant=_PLANT,
            reminder="watering",
            status=TaskStatus.PENDING.value,
            due=now + timedelta(days=1),
            created=now - timedelta(minutes=5),
        ),
        _care_task(
            "dup-newest-due",
            plant=_PLANT,
            reminder="watering",
            status=TaskStatus.PENDING.value,
            due=now + timedelta(days=3),
            created=now - timedelta(minutes=4),
        ),
        _care_task(
            "dup-in-progress",
            plant=_PLANT,
            reminder="watering",
            status=TaskStatus.IN_PROGRESS.value,
            due=now + timedelta(days=2),
            created=now - timedelta(minutes=3),
        ),
        _care_task(
            "other-type",
            plant=_PLANT,
            reminder="fertilizing",
            status=TaskStatus.PENDING.value,
            due=now + timedelta(days=1),
            created=now,
        ),
        _care_task(
            "other-plant",
            plant="plant-mint-2",
            reminder="watering",
            status=TaskStatus.PENDING.value,
            due=now + timedelta(days=1),
            created=now,
        ),
        _care_task(
            "history-1",
            plant=_PLANT,
            reminder="watering",
            status=TaskStatus.COMPLETED.value,
            due=now - timedelta(days=6),
            created=now - timedelta(days=6),
        ),
        _care_task(
            "history-2",
            plant=_PLANT,
            reminder="watering",
            status=TaskStatus.COMPLETED.value,
            due=now - timedelta(days=3),
            created=now - timedelta(days=3),
        ),
    ]
    legacy_db.collection(col.TASKS).import_bulk(docs)
    return legacy_db


def _status(db, key: str) -> str:
    from app.data_access.arango import collections as col

    return db.collection(col.TASKS).get(key)["status"]


def _has_dedup_index(db) -> bool:
    from app.data_access.arango import collections as col

    return any(
        isinstance(idx, dict)
        and idx.get("fields") == col.CARE_TASK_DEDUP_INDEX_FIELDS
        and idx.get("unique")
        and idx.get("sparse")
        for idx in db.collection(col.TASKS).indexes()
    )


# ── the precondition the migration exists for ────────────────────────────────


def test_unique_index_creation_fails_on_the_unreconciled_volume(duplicated):
    """Without the reconciliation, creating the index on a live volume **fails**.

    This is the whole reason step 1 exists, and it is measured rather than
    assumed: the same ``add_persistent_index`` the migration ends with is rejected
    while the duplicates are still open. A migration that skipped the reconcile
    would break the production deploy exactly here.
    """
    from arango.exceptions import IndexCreateError

    from app.data_access.arango import collections as col

    handle = duplicated.collection(col.TASKS)
    col.configure_care_task_dedup_computed_value(handle)
    duplicated.aql.execute(
        f"FOR d IN {col.TASKS} FILTER d.{col.CARE_TASK_DEDUP_FIELD} == null UPDATE d WITH {{}} IN {col.TASKS}"
    )

    with pytest.raises(IndexCreateError):
        handle.add_persistent_index(
            fields=col.CARE_TASK_DEDUP_INDEX_FIELDS,
            unique=True,
            sparse=True,
            name=col.CARE_TASK_DEDUP_INDEX_NAME,
        )


# ── the migration ────────────────────────────────────────────────────────────


def test_dry_run_writes_nothing(duplicated):
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    report = migration.up(duplicated, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.scanned == 2  # three open watering tasks in one group → two losers
    assert report.details["duplicate_losers"] == 2
    assert report.details["will_create_unique_index"] is True
    # Nothing touched.
    assert _status(duplicated, "dup-oldest") == "pending"
    assert not col.has_care_task_dedup_computed_value(duplicated.collection(col.TASKS))
    assert not _has_dedup_index(duplicated)


def test_migration_reconciles_duplicates_and_creates_the_index(duplicated):
    from app.common.enums import TaskStatus
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    report = migration.up(duplicated)

    assert report.dry_run is False
    assert report.details["closed_duplicate_losers"] == 2
    assert report.details["computed_value_configured"] is True
    assert report.details["unique_index_created"] is True

    # The survivor is the one ``find_open_care_task`` would have returned: newest
    # due_date. The two losers are closed as SKIPPED, not deleted.
    assert _status(duplicated, "dup-newest-due") == TaskStatus.PENDING.value
    assert _status(duplicated, "dup-oldest") == TaskStatus.SKIPPED.value
    assert _status(duplicated, "dup-in-progress") == TaskStatus.SKIPPED.value

    # Untouched: a different reminder type, a different plant, and the completed
    # history that a non-sparse "care tasks are unique" index would have broken.
    assert _status(duplicated, "other-type") == TaskStatus.PENDING.value
    assert _status(duplicated, "other-plant") == TaskStatus.PENDING.value
    assert _status(duplicated, "history-1") == TaskStatus.COMPLETED.value
    assert _status(duplicated, "history-2") == TaskStatus.COMPLETED.value

    assert _has_dedup_index(duplicated)


def test_migration_backfills_so_the_index_is_not_inert_on_pre_existing_data(duplicated):
    """The surviving legacy task must actually occupy its index slot afterwards.

    Configuring a computed value does not rewrite stored documents, so without the
    backfill the survivor would carry no ``care_dedup_key``, a sparse index would
    skip it, and the very next producer would happily create a second open
    watering task for it — an index that exists and constrains nothing.
    """
    from arango.exceptions import DocumentInsertError

    from app.data_access.arango import collections as col
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    migration.up(duplicated)

    handle = duplicated.collection(col.TASKS)
    assert handle.get("dup-newest-due")[col.CARE_TASK_DEDUP_FIELD] == f"{_TENANT}/{_PLANT}/watering"
    assert col.CARE_TASK_DEDUP_FIELD not in handle.get("history-1")
    assert col.CARE_TASK_DEDUP_FIELD not in handle.get("dup-oldest")  # closed → slot released

    now = datetime.now(UTC)
    with pytest.raises(DocumentInsertError) as excinfo:
        handle.insert(
            _care_task(
                "would-duplicate",
                plant=_PLANT,
                reminder="watering",
                status="pending",
                due=now,
                created=now,
            )
        )
    assert excinfo.value.error_code == 1210


def test_migration_is_idempotent(duplicated):
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    migration.up(duplicated)
    second = migration.up(duplicated)

    assert second.scanned == 0
    assert second.changed == 0
    assert second.details["closed_duplicate_losers"] == 0
    assert second.details["computed_value_configured"] is False
    assert second.details["backfilled_dedup_keys"] == 0
    assert second.details["unique_index_created"] is False


def test_migration_on_a_clean_volume_only_installs_the_constraint(legacy_db):
    """A volume with no duplicates still gets the computed value and the index."""
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    report = migration.up(legacy_db)

    assert report.scanned == 0
    assert report.details["closed_duplicate_losers"] == 0
    assert report.details["unique_index_created"] is True
    assert _has_dedup_index(legacy_db)


def test_down_refuses(duplicated):
    from app.migrations.framework.report import IrreversibleMigrationError
    from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import migration

    with pytest.raises(IrreversibleMigrationError):
        migration.down(duplicated)
