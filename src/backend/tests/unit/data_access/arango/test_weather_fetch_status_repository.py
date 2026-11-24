"""N2 (security review 2026-11-22) — a corrupt status document reads as "no status".

Measured through the production path: the repository's ``get_status`` feeds
``WeatherFetchService.is_due``; before the fix a document that did not validate
raised on every hourly tick and no fetch ever ran again.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.weather_fetch_status_repository import ArangoWeatherFetchStatusRepository
from app.domain.services.weather_fetch_service import WeatherFetchService
from tests.support.weather_fetch_doubles import FakeWeatherFetchGate, StaticWeatherFetchSettings


def _repo(doc: dict | None) -> ArangoWeatherFetchStatusRepository:
    db = MagicMock()
    db.collection.return_value.get.return_value = doc
    return ArangoWeatherFetchStatusRepository(db)


@pytest.mark.parametrize(
    "doc",
    [
        {"_key": "weather_fetch_status", "last_success": {"started_at": "not-a-date"}},
        {"_key": "weather_fetch_status", "last_run": "garbage"},
        {"_key": "weather_fetch_status", "consecutive_failures": -4},
    ],
)
def test_a_corrupt_document_reads_as_no_status_and_the_fetch_is_due(doc) -> None:  # noqa: ANN001
    repo = _repo(doc)

    status = repo.get_status()
    service = WeatherFetchService(repo, FakeWeatherFetchGate(), StaticWeatherFetchSettings())

    assert (status.last_run, status.last_success, status.consecutive_failures) == (None, None, 0)
    assert service.is_due()


def test_a_missing_document_is_no_status() -> None:
    assert _repo(None).get_status().last_success is None


def test_record_run_returns_the_count_the_statement_returned() -> None:
    from datetime import UTC, datetime

    from app.common.enums import WeatherFetchTrigger
    from app.domain.models.weather_fetch import WeatherFetchRun

    db = MagicMock()
    db.aql.execute.return_value = iter([3])
    now = datetime(2026, 11, 22, 6, tzinfo=UTC)

    failures = ArangoWeatherFetchStatusRepository(db).record_run(
        WeatherFetchRun(trigger=WeatherFetchTrigger.SCHEDULED, started_at=now, finished_at=now, success=False)
    )

    assert failures == 3
    assert db.aql.execute.call_args.kwargs["bind_vars"]["success"] is False
