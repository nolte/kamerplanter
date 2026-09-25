"""Integration test for migration v0060 — the contribution-marker backfill (#1753).

The "only when absent" rule lives in the ``UPSERT … OLD.… == null`` statement,
so it is measured against a server: a present marker keeps its timestamp, the
other settings on the singleton survive, the marker lands on an empty database,
and the repository the no-op store reads sees what the migration wrote.

Run with::

    docker run -d --rm -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0060_mark_reference_contributions.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from app.migrations.versions.v0060_mark_reference_contributions import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the conditional UPSERT semantics are the SUT"),
]

_DB_NAME = run_database_name("v0060_migration")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    yield client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(_DB_NAME)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)


def test_marks_an_empty_database(db, enabled) -> None:
    report = migration.up(db)

    assert report.changed == 1
    assert ArangoSystemSettingsRepository(db).reference_contributions_since() is not None


def test_marks_the_existing_singleton_without_touching_other_settings(db, enabled) -> None:
    db.create_collection(col.SYSTEM_SETTINGS)
    db.collection(col.SYSTEM_SETTINGS).insert({"_key": "default", "home_assistant": {"ha_url": "http://ha.local"}})

    migration.up(db)

    doc = db.collection(col.SYSTEM_SETTINGS).get("default")
    assert doc["home_assistant"] == {"ha_url": "http://ha.local"}
    assert doc["reference_contributions_since"]


def test_a_present_marker_keeps_its_timestamp_and_a_rerun_changes_nothing(db, enabled) -> None:
    first = datetime(2026, 1, 1, tzinfo=UTC)
    db.create_collection(col.SYSTEM_SETTINGS)
    ArangoSystemSettingsRepository(db).record_reference_contributions(first)

    reports = [migration.up(db), migration.up(db)]

    assert [r.changed for r in reports] == [0, 0]
    assert ArangoSystemSettingsRepository(db).reference_contributions_since() == first


def test_the_statement_itself_never_overwrites_a_marker(db, enabled) -> None:
    """The pre-read is an optimisation; the UPSERT alone must keep a raced-in marker."""
    first = datetime(2026, 1, 1, tzinfo=UTC)
    db.create_collection(col.SYSTEM_SETTINGS)
    ArangoSystemSettingsRepository(db).record_reference_contributions(first)

    db.aql.execute(
        migration._MARK_QUERY,
        bind_vars={"@collection": col.SYSTEM_SETTINGS, "key": "default", "now": datetime.now(UTC).isoformat()},
    )

    assert ArangoSystemSettingsRepository(db).reference_contributions_since() == first


def test_a_flagless_backend_marks_nothing(db, monkeypatch) -> None:
    monkeypatch.setattr(settings, "inference_service_enabled", False)

    report = migration.up(db)

    assert report.changed == 0
    assert not db.has_collection(col.SYSTEM_SETTINGS)


def test_dry_run_writes_nothing(db, enabled) -> None:
    report = migration.up(db, dry_run=True)

    assert report.details["marked"] is True
    assert not db.has_collection(col.SYSTEM_SETTINGS)
