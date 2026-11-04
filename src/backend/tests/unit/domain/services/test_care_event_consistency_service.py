"""WP 8.2 (#2645) — the consistency job's rules around the shared scan, with the scan fed as rows.

The real AQL (reference resolution, ``present`` through the unique ``source_ref`` index) and the real writer are
measured on an ArangoDB in ``tests/integration/test_care_events_consistency.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from prometheus_client import REGISTRY as _DEFAULT_REGISTRY  # noqa: F401  (the metric lives on the app registry)
from structlog.testing import capture_logs

from app.domain.engines.care_event_backfill_mapper import SOURCE_COLLECTIONS
from app.domain.interfaces.care_event_gap_reader import ICareEventGapReader
from app.domain.services.care_event_consistency_service import ALERT_THRESHOLD, CareEventConsistencyService
from app.observability.metrics import REGISTRY
from tests.support.care_event_fakes import FakeCareEventRepo

NOW = datetime(2026, 11, 3, 5, 10, tzinfo=UTC)
RECENT = (NOW - timedelta(days=1)).isoformat()


def _row(key: str, *, tenant: str = "t1", site_tenant: str = "t1", plant: str | None = "p1", **doc: Any) -> dict:
    refs = [] if plant is None else [{"ref": plant, "kind": "plant", "location_key": "L1", "plant_tenant": site_tenant}]
    return {
        "doc": {"_key": key, "tenant_key": tenant, "watered_at": RECENT, "volume_liters": 1.0, **doc},
        "refs": refs,
        "own_location_key": None,
        "locations": []
        if plant is None
        else [{"key": "L1", "found": True, "site_key": "S1", "site_found": True, "site_tenant": site_tenant}],
        "present": False,
    }


class _Gaps(ICareEventGapReader):
    def __init__(self, rows: dict[str, list[dict]]) -> None:
        self.rows = rows
        self.asked: list[tuple[str, datetime]] = []

    def candidates(self, source: str, since: datetime):  # type: ignore[no-untyped-def]
        self.asked.append((source, since))
        yield from self.rows.get(source, [])


def _service(rows: dict[str, list[dict]], *, active: set[str] | None = None):  # type: ignore[no-untyped-def]
    gaps, events = _Gaps(rows), FakeCareEventRepo()
    open_tenants = {"t1"} if active is None else active
    return CareEventConsistencyService(gaps, events, lambda tenant: tenant in open_tenants), gaps, events


def _count(source: str) -> float:
    return REGISTRY.get_sample_value("care_events_consistency_backfilled_total", {"source": source}) or 0.0


def test_a_gap_is_closed_with_a_backfill_event_and_the_next_run_has_none() -> None:
    service, _, events = _service({"watering_events": [_row("w1"), _row("w2")]})

    first = service.run(now=NOW, window_days=7)
    stored = [e for e in events.events.values()]
    second = service.run(now=NOW, window_days=7)

    assert first.hits == 2
    assert {(e.trigger, e.source_ref["key"]) for e in stored} == {("backfill", "w1"), ("backfill", "w2")}
    assert second.hits == 0
    assert len(events.events) == 2  # nothing written twice
    assert second.already_present == 2


def test_the_window_is_the_last_n_days_for_every_source() -> None:
    service, gaps, _ = _service({})

    service.run(now=NOW, window_days=3)

    assert [source for source, _ in gaps.asked] == list(SOURCE_COLLECTIONS)
    assert {since for _, since in gaps.asked} == {NOW - timedelta(days=3)}


def test_the_counter_is_incremented_per_source() -> None:
    before = {s: _count(s) for s in SOURCE_COLLECTIONS}
    rows = {
        "watering_events": [_row("w1"), _row("w2")],
        "harvest_batches": [_row("h1", harvest_date=RECENT, watered_at=None)],
    }
    rows["harvest_batches"][0]["doc"].pop("watered_at")
    service, _, _ = _service(rows)

    report = service.run(now=NOW, window_days=7)

    assert report.backfilled["watering_events"] == 2 and report.backfilled["harvest_batches"] == 1
    assert _count("watering_events") - before["watering_events"] == 2
    assert _count("harvest_batches") - before["harvest_batches"] == 1
    assert _count("feeding_events") == before["feeding_events"]


@pytest.mark.parametrize(("hits", "warns"), [(ALERT_THRESHOLD, False), (ALERT_THRESHOLD + 1, True)])
def test_the_warning_is_logged_at_101_hits_and_not_at_100(hits: int, warns: bool) -> None:
    service, _, _ = _service({"watering_events": [_row(f"w{i:04d}") for i in range(hits)]})

    with capture_logs() as logs:
        report = service.run(now=NOW, window_days=7)

    assert report.hits == hits
    events = [entry["event"] for entry in logs if entry["log_level"] == "warning"]
    assert ("care_events_consistency.threshold_exceeded" in events) is warns
    completed = next(entry for entry in logs if entry["event"] == "care_events_consistency.completed")
    assert completed["hits"] == hits and "duration_seconds" in completed


def test_a_tenant_that_is_not_active_is_left_alone() -> None:
    rows = {"watering_events": [_row("open"), _row("closed", tenant="t2", site_tenant="t2")]}
    service, _, events = _service(rows, active={"t1"})

    report = service.run(now=NOW, window_days=7)

    assert [e.source_ref["key"] for e in events.events.values()] == ["open"]
    assert report.skipped_inactive_tenant == 1
    # counter-case: the same row of the same tenant IS written once the tenant is active
    service, _, events = _service(rows, active={"t1", "t2"})
    assert service.run(now=NOW, window_days=7).hits == 2


def test_a_source_without_a_resolvable_bed_is_counted_and_never_written() -> None:
    rows = {"watering_events": [_row("nobed", plant=None), _row("cross", tenant="t2")]}
    service, _, events = _service(rows, active={"t1", "t2"})

    report = service.run(now=NOW, window_days=7)

    assert events.events == {}
    assert report.without_bed["watering_events"] == 2
    assert report.hits == 0


def test_a_volume_over_one_batch_is_written_whole() -> None:
    from app.domain.services import care_event_consistency_service as module

    count = module._BATCH_SIZE * 2 + 3
    service, _, events = _service({"watering_events": [_row(f"w{i:04d}") for i in range(count)]})

    assert service.run(now=NOW, window_days=7).hits == count
    assert len(events.events) == count


def test_a_document_the_mapper_refuses_does_not_stop_the_run() -> None:
    bad = _row("bad")
    del bad["doc"]["_key"]  # no key, so no ``source_ref`` can name it: the mapper refuses it
    rows = {"watering_events": [bad, _row("good")], "harvest_batches": [_row("h1", harvest_date=RECENT)]}
    rows["harvest_batches"][0]["doc"].pop("watered_at")
    service, _, events = _service(rows)

    with capture_logs() as logs:
        report = service.run(now=NOW, window_days=7)

    assert {e.source_ref["key"] for e in events.events.values()} == {"good", "h1"}  # the later source is repaired too
    assert report.errors == 1 and report.hits == 2
    assert any(entry["event"] == "care_events_consistency.document_refused" for entry in logs)


def test_a_failed_batch_is_counted_and_the_other_sources_go_on() -> None:
    rows = {"watering_events": [_row("w1")], "harvest_batches": [_row("h1", harvest_date=RECENT)]}
    rows["harvest_batches"][0]["doc"].pop("watered_at")
    service, _, events = _service(rows)
    real = events.insert_backfilled
    calls: list[str] = []

    def flaky(batch, *, tenant_key):  # type: ignore[no-untyped-def]
        calls.append(batch[0].source_ref["collection"])
        if batch[0].source_ref["collection"] == "watering_events":
            raise RuntimeError("the transaction aborted")
        return real(batch, tenant_key=tenant_key)

    events.insert_backfilled = flaky  # type: ignore[method-assign]

    with capture_logs() as logs:
        report = service.run(now=NOW, window_days=7)

    assert calls == ["watering_events", "harvest_batches"]
    assert report.errors == 1 and report.hits == 1
    assert any(entry["event"] == "care_events_consistency.batch_failed" for entry in logs)
    # counter-case: without the failure the same input writes both
    service, _, events = _service(rows)
    assert service.run(now=NOW, window_days=7).hits == 2


def test_a_document_without_a_readable_instant_is_counted() -> None:
    row = _row("nodate")
    row["doc"]["watered_at"] = "not a date"
    service, _, events = _service({"watering_events": [row]})

    report = service.run(now=NOW, window_days=7)

    assert report.no_timestamp == 1 and events.events == {}
