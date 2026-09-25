"""Integration test for the ArangoDB side of the pest-prototype orphan sweep (#1771).

Measured against a server: the tenant-agnostic key lookup that decides which
prototypes are orphaned, and the ``UPSERT`` that records a run's counts on the
settings singleton without touching its other fields.

Run with::

    docker run -d --rm -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_pest_prototype_orphan_sweep_arango.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the key lookup and the record UPSERT are the SUT"),
]

_DB_NAME = run_database_name("pest_orphan_sweep")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.PEST_IMAGE_CONTRIBUTIONS)
    database.create_collection(col.SYSTEM_SETTINGS)
    yield database
    system.delete_database(_DB_NAME)


def test_existing_keys_answers_across_tenants_and_only_for_present_documents(db) -> None:
    contributions = db.collection(col.PEST_IMAGE_CONTRIBUTIONS)
    contributions.insert({"_key": "c-live-a", "tenant_key": "t-a"})
    contributions.insert({"_key": "c-live-b", "tenant_key": "t-b"})
    repo = ArangoPestImageRepository(db)

    assert repo.existing_keys(["c-live-a", "c-gone", "c-live-b", "c-live-a2"]) == {"c-live-a", "c-live-b"}
    assert repo.existing_keys([]) == set()


def test_the_record_accumulates_removals_and_keeps_the_other_settings(db) -> None:
    db.collection(col.SYSTEM_SETTINGS).insert(
        {"_key": "default", "pest_prototype_contributions_since": "2026-07-01T00:00:00+00:00", "storage": {"x": 1}}
    )
    repo = ArangoSystemSettingsRepository(db)
    first = datetime(2026, 9, 26, 4, 30, tzinfo=UTC)
    second = datetime(2026, 9, 27, 4, 30, tzinfo=UTC)

    repo.record_pest_prototype_orphan_sweep(now=first, examined=5, orphaned=3, removed=4, binding="inference_service")
    repo.record_pest_prototype_orphan_sweep(now=second, examined=2, orphaned=0, removed=0, binding="inference_service")

    doc = db.collection(col.SYSTEM_SETTINGS).get("default")
    assert doc["pest_prototype_contributions_since"] == "2026-07-01T00:00:00+00:00"
    assert doc["storage"] == {"x": 1}
    record = repo.get().pest_prototype_orphan_sweep
    assert record is not None
    assert (record.first_run_at, record.last_run_at) == (first, second)
    assert (record.last_examined, record.last_orphaned, record.last_removed, record.total_removed) == (2, 0, 0, 4)
    assert record.binding == "inference_service"


def test_the_record_creates_the_singleton_when_absent(db) -> None:
    repo = ArangoSystemSettingsRepository(db)
    now = datetime(2026, 9, 26, 4, 30, tzinfo=UTC)

    repo.record_pest_prototype_orphan_sweep(now=now, examined=1, orphaned=1, removed=2, binding="inference_service")

    record = repo.get().pest_prototype_orphan_sweep
    assert (record.first_run_at, record.last_removed, record.total_removed) == (now, 2, 2)


def test_an_admin_settings_save_does_not_reset_a_run_recorded_meanwhile(db) -> None:
    repo = ArangoSystemSettingsRepository(db)
    repo.record_pest_prototype_orphan_sweep(
        now=datetime(2026, 9, 26, 4, 30, tzinfo=UTC), examined=5, orphaned=3, removed=4, binding="inference_service"
    )
    stale = repo.get()  # the admin read-modify-write starts here ...
    repo.record_pest_prototype_orphan_sweep(  # ... the next run lands in between ...
        now=datetime(2026, 9, 27, 4, 30, tzinfo=UTC), examined=3, orphaned=1, removed=2, binding="inference_service"
    )

    repo.upsert(stale)  # ... and the admin write must not carry the old record back

    record = repo.get().pest_prototype_orphan_sweep
    assert (record.last_removed, record.total_removed) == (2, 6)
    assert record.last_run_at == datetime(2026, 9, 27, 4, 30, tzinfo=UTC)


def test_an_admin_settings_save_after_a_run_keeps_it(db) -> None:
    repo = ArangoSystemSettingsRepository(db)
    repo.record_pest_prototype_orphan_sweep(
        now=datetime(2026, 9, 26, 4, 30, tzinfo=UTC), examined=5, orphaned=3, removed=4, binding="inference_service"
    )
    current = repo.get()

    repo.upsert(current)

    assert repo.get().pest_prototype_orphan_sweep.total_removed == 4
