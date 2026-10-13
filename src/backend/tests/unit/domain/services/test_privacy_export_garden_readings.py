"""#2165 — the export walk reads the personal garden's sensor readings from the time-series store.

What the walk must do with the three TimescaleDB sources:

* bound them by the personal tenants the subject **owns** (never a membership);
* hand over the garden's sensor keys — the ``_key``s of the ``sensors`` section it
  collected before — so the pre-#2076 Home Assistant rows (empty tenant key) are matched
  to exactly the sensors the bundle lists;
* cap each section at ``TIME_SERIES_SECTION_MAX_ROWS`` and write the difference into the
  bundle, never into silence;
* fail visibly when a garden exists and no time-series reader is wired.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.domain.interfaces.personal_data_repository import IPersonalDataRepository, IPersonalTimeSeriesRepository
from app.domain.models.membership import Membership
from app.domain.models.privacy import DataExportRequest, DataSourceDefinition, TimeSeriesSlice
from tests.unit.domain.services.test_privacy_export_bundle import (
    FIXTURE_ROWS,
    USER,
    _download_text,
    _InMemoryStorage,
    _make_service,
)

PERSONAL = "t-personal-owned"
ORG = "t-org-member"
SENSOR_KEYS = ["s-ec", "s-temp"]


class _DocumentRepo(IPersonalDataRepository):
    """The garden has two sensors and one watering log; account sources answer from the shared fixture."""

    def collect_for_user(
        self, source: DataSourceDefinition, user_key: str, tenant_keys, *, tombstone=None
    ) -> list[dict[str, Any]]:
        if source.time_series is not None:
            raise AssertionError(f"the document reader was asked for the time series '{source.collection}'")
        if source.personal_tenant_scope is not None and source.collection == "sensors":
            return [{"_key": key, "name": key} for key in SENSOR_KEYS]
        if source.personal_tenant_scope is not None and source.collection == "watering_logs":
            return [{"_key": "wl-1", "volume_liters": 2.5}]
        return [dict(row) for row in FIXTURE_ROWS.get(source.collection, [])]


class _SeriesRepo(IPersonalTimeSeriesRepository):
    """Holds *totals* rows per table and returns at most ``max_rows`` of them, as the real reader does."""

    def __init__(self, totals: dict[str, int]) -> None:
        self.totals = totals
        self.calls: list[tuple[str, list[str], list[str], int]] = []

    def collect_personal_tenant_series(
        self,
        source: DataSourceDefinition,
        tenant_keys: Sequence[str],
        series_keys: Sequence[str],
        *,
        max_rows: int,
    ) -> TimeSeriesSlice:
        self.calls.append((source.collection, list(tenant_keys), list(series_keys), max_rows))
        total = self.totals.get(source.collection, 0)
        column = source.time_series.time_column  # type: ignore[union-attr]
        records = [{column: f"2026-10-0{i % 9 + 1}", "sensor_key": "s-ec"} for i in range(min(total, max_rows))]
        return TimeSeriesSlice(records=records, total=total)


def _service(series: IPersonalTimeSeriesRepository | None, personal: list[str]):  # type: ignore[no-untyped-def]
    memberships = MagicMock()
    memberships.list_by_user.return_value = [
        Membership(user_key=USER, tenant_key=PERSONAL),
        Membership(user_key=USER, tenant_key=ORG),
    ]
    tenants = MagicMock()
    tenants.personal_tenant_keys_of.return_value = personal
    export = DataExportRequest(key="exp-1", user_key=USER, status="pending", requested_at=datetime.now(UTC))
    overrides: dict[str, Any] = {"membership_repo": memberships, "tenant_service": tenants}
    if series is not None:
        overrides["time_series_repo"] = series
    return _make_service(export, _InMemoryStorage(), _DocumentRepo(), **overrides)


@pytest.mark.asyncio
async def test_the_readings_are_bounded_by_the_owned_garden_and_its_sensors() -> None:
    series = _SeriesRepo({"sensor_readings": 3, "sensor_hourly": 2, "sensor_daily": 1})
    svc = _service(series, [PERSONAL])

    done = await svc.process_data_export("exp-1")

    assert done is not None and done.status == "completed", done
    assert [c[0] for c in series.calls] == ["sensor_readings", "sensor_hourly", "sensor_daily"]
    for _table, tenant_keys, series_keys, max_rows in series.calls:
        assert tenant_keys == [PERSONAL]  # not the organisation the subject is a member of
        assert series_keys == SENSOR_KEYS
        assert max_rows == svc._data_export_engine.TIME_SERIES_SECTION_MAX_ROWS


@pytest.mark.asyncio
async def test_the_bundle_carries_the_readings_and_the_logs() -> None:
    svc = _service(_SeriesRepo({"sensor_readings": 3, "sensor_hourly": 2, "sensor_daily": 1}), [PERSONAL])

    await svc.process_data_export("exp-1")
    bundle = json.loads(await _download_text(svc))
    sections = {s["collection"]: s for s in bundle["sections"] if s["label"].startswith("Your personal garden")}

    assert sections["sensor_readings"]["record_count"] == 3
    assert sections["sensor_hourly"]["record_count"] == 2
    assert sections["sensor_daily"]["record_count"] == 1
    assert sections["sensors"]["records"] == [{"_key": "s-ec", "name": "s-ec"}, {"_key": "s-temp", "name": "s-temp"}]
    assert sections["watering_logs"]["records"] == [{"_key": "wl-1", "volume_liters": 2.5}]
    assert all(sections[name]["records_omitted"] == 0 for name in ("sensor_readings", "sensor_hourly"))


@pytest.mark.asyncio
async def test_a_section_over_the_cap_carries_the_newest_rows_and_states_the_rest(monkeypatch) -> None:
    from app.domain.engines.data_export_engine import DataExportEngine

    monkeypatch.setattr(DataExportEngine, "TIME_SERIES_SECTION_MAX_ROWS", 4)
    svc = _service(_SeriesRepo({"sensor_readings": 10}), [PERSONAL])

    await svc.process_data_export("exp-1")
    bundle = json.loads(await _download_text(svc))
    (readings,) = [s for s in bundle["sections"] if s["collection"] == "sensor_readings"]

    assert readings["record_count"] == 4
    assert readings["records_omitted"] == 6
    assert "10 records" in readings["omission_note"]


@pytest.mark.asyncio
async def test_without_a_personal_garden_the_reader_is_not_asked() -> None:
    series = _SeriesRepo({"sensor_readings": 3})
    svc = _service(series, [])

    done = await svc.process_data_export("exp-1")

    assert done is not None and done.status == "completed"
    assert series.calls == []


@pytest.mark.asyncio
async def test_a_garden_without_a_wired_reader_fails_visibly() -> None:
    """An empty readings section would read as "no sensor data" — the silence #1645 removes."""
    svc = _service(None, [PERSONAL])

    done = await svc.process_data_export("exp-1")

    assert done is not None and done.status == "failed"
    assert "time-series reader is not configured" in (done.error_message or "")
