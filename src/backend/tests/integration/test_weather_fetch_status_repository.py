"""Integration test of the weather fetch status document (REQ-046 §3.6a, #2934).

The "a failed run keeps the last success" rule lives in the ``UPSERT … OLD.…``
statement, so it is measured against a server; so is the claim that the status
document sits next to the ``default`` settings singleton without touching it
(operator decision 2026-11-17 — the admin PUT rewrites the singleton whole).

Run with::

    docker run -d --rm -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_weather_fetch_status_repository.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.enums import WeatherFetchTrigger
from app.data_access.arango import collections as col
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from app.data_access.arango.weather_fetch_status_repository import STATUS_KEY, ArangoWeatherFetchStatusRepository
from app.domain.models.system_settings import SystemSettings, WeatherProviderSettings
from app.domain.models.weather_fetch import WeatherFetchRun
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the conditional UPSERT of the status document is the SUT"),
]

_DB_NAME = run_database_name("weather_fetch_status")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.SYSTEM_SETTINGS)
    yield database
    system.delete_database(_DB_NAME)


def _run(started_at: datetime, *, success: bool, trigger: WeatherFetchTrigger = WeatherFetchTrigger.SCHEDULED):
    return WeatherFetchRun(
        trigger=trigger,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=30),
        success=success,
        sites=2,
        sites_written=2 if success else 0,
        sites_failed=0 if success else 2,
        forecasts_written=14 if success else 0,
    )


def test_an_empty_database_has_an_empty_status(db) -> None:
    status = ArangoWeatherFetchStatusRepository(db).get_status()

    assert status.last_run is None
    assert status.last_success is None


def test_a_failed_run_keeps_the_last_success(db) -> None:
    repo = ArangoWeatherFetchStatusRepository(db)
    first = datetime(2026, 11, 22, 6, 0, tzinfo=UTC)
    succeeded = _run(first, success=True)
    failed = _run(first + timedelta(hours=6), success=False, trigger=WeatherFetchTrigger.MANUAL)

    repo.record_run(succeeded)
    repo.record_run(failed)
    status = repo.get_status()

    assert status.last_run == failed
    assert status.last_success == succeeded


def test_a_successful_run_replaces_both(db) -> None:
    repo = ArangoWeatherFetchStatusRepository(db)
    first = datetime(2026, 11, 22, 6, 0, tzinfo=UTC)
    repo.record_run(_run(first, success=True))
    newer = _run(first + timedelta(hours=6), success=True, trigger=WeatherFetchTrigger.MANUAL)

    repo.record_run(newer)
    status = repo.get_status()

    assert status.last_run == newer
    assert status.last_success == newer


def test_the_status_document_leaves_the_settings_singleton_alone(db) -> None:
    settings_repo = ArangoSystemSettingsRepository(db)
    settings_repo.upsert(SystemSettings(weather_providers=WeatherProviderSettings(fetch_interval_hours=12)))
    status_repo = ArangoWeatherFetchStatusRepository(db)

    status_repo.record_run(_run(datetime(2026, 11, 22, 6, 0, tzinfo=UTC), success=True))
    # An admin PUT after the run rewrites the singleton whole; the status survives it.
    settings_repo.upsert(SystemSettings(weather_providers=WeatherProviderSettings(fetch_interval_hours=8)))

    stored = settings_repo.get()
    assert stored is not None
    assert stored.weather_providers.fetch_interval_hours == 8
    assert status_repo.get_status().last_success is not None
    assert db.collection(col.SYSTEM_SETTINGS).has(STATUS_KEY)


def test_failed_runs_are_counted_in_a_row_and_a_success_resets_them(db) -> None:
    repo = ArangoWeatherFetchStatusRepository(db)
    start = datetime(2026, 11, 22, 6, 0, tzinfo=UTC)

    counts = [repo.record_run(_run(start + timedelta(hours=i), success=False)) for i in range(3)]
    after_success = repo.record_run(_run(start + timedelta(hours=3), success=True))
    after_next_failure = repo.record_run(_run(start + timedelta(hours=4), success=False))

    assert counts == [1, 2, 3]
    assert after_success == 0
    assert after_next_failure == 1
    assert repo.get_status().consecutive_failures == 1


def test_a_corrupt_stored_document_reads_as_no_status_and_the_next_run_repairs_it(db) -> None:
    db.collection(col.SYSTEM_SETTINGS).insert(
        {"_key": STATUS_KEY, "last_success": {"started_at": "not-a-date"}, "consecutive_failures": "x"}
    )
    repo = ArangoWeatherFetchStatusRepository(db)

    assert repo.get_status().last_success is None

    succeeded = _run(datetime(2026, 11, 22, 6, 0, tzinfo=UTC), success=True)
    assert repo.record_run(succeeded) == 0
    assert repo.get_status().last_success == succeeded


def test_a_corrupt_counter_and_a_failed_run_count_one(db) -> None:
    db.collection(col.SYSTEM_SETTINGS).insert(
        {"_key": STATUS_KEY, "last_success": {"started_at": "not-a-date"}, "consecutive_failures": "x"}
    )
    repo = ArangoWeatherFetchStatusRepository(db)

    assert repo.record_run(_run(datetime(2026, 11, 22, 6, 0, tzinfo=UTC), success=False)) == 1
