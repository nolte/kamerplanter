"""Integration test for migration v0061 — the pest-prototype marker backfill (#1759).

Measured against a server: the "any promoted" read, the conditional ``UPSERT``
that keeps an existing timestamp and the other settings, and the repository
read the no-op pest-prototype store relies on.

Run with::

    docker run -d --rm -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0061_mark_pest_prototype_contributions.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from app.migrations.versions.v0061_mark_pest_prototype_contributions import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the promoted read and the conditional UPSERT are the SUT"),
]

_DB_NAME = run_database_name("v0061_migration")


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
    monkeypatch.setattr(settings, "pest_detection_enabled", True)


def _contributions(db, *, promoted: bool) -> None:  # type: ignore[no-untyped-def]
    # Both exist on every initialised database; the schema bootstrap creates them.
    db.create_collection(col.SYSTEM_SETTINGS)
    db.create_collection(col.PEST_IMAGE_CONTRIBUTIONS)
    db.collection(col.PEST_IMAGE_CONTRIBUTIONS).insert({"_key": "private", "promoted_at": None})
    if promoted:
        db.collection(col.PEST_IMAGE_CONTRIBUTIONS).insert({"_key": "p", "promoted_at": "2026-05-01T00:00:00+00:00"})


def test_marks_when_a_contribution_was_promoted(db, enabled) -> None:
    _contributions(db, promoted=True)
    db.collection(col.SYSTEM_SETTINGS).insert({"_key": "default", "home_assistant": {"ha_url": "http://ha.local"}})

    report = migration.up(db)

    assert report.changed == 1
    repo = ArangoSystemSettingsRepository(db)
    assert repo.pest_prototype_contributions_since() is not None
    assert db.collection(col.SYSTEM_SETTINGS).get("default")["home_assistant"] == {"ha_url": "http://ha.local"}


def test_does_not_mark_without_a_promoted_contribution(db, enabled) -> None:
    _contributions(db, promoted=False)

    report = migration.up(db)

    assert report.details["reason"] == "no_promoted_contribution"
    assert ArangoSystemSettingsRepository(db).pest_prototype_contributions_since() is None


def test_keeps_an_existing_marker_and_the_repository_write_is_idempotent(db, enabled) -> None:
    _contributions(db, promoted=True)
    repo = ArangoSystemSettingsRepository(db)
    first = datetime(2026, 3, 1, tzinfo=UTC)
    repo.record_pest_prototype_contributions(first)
    repo.record_pest_prototype_contributions(datetime(2026, 9, 1, tzinfo=UTC))

    report = migration.up(db)

    assert report.details["reason"] == "marker_present"
    assert repo.pest_prototype_contributions_since() == first
