"""v0104 (WP 8.1, #2644): the write path of the M4 backfill, with the scan fed as rows.

The real AQL (reference resolution, ``source_ref`` presence, the window) is measured on an ArangoDB in
``tests/integration/test_v0104_care_events_backfill.py``; this suite pins what happens *around* the scan: the dry
run never reaches the writer, the real run writes exactly the planned events in bounded batches per (source,
tenant), what the unique index reports moves from ``will_write`` to ``already_present``, and ``down`` is honest.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.domain.models.care_event import CareEvent
from app.migrations.framework.report import MigrationReport
from app.migrations.versions import v0104_care_events_backfill as v0104
from app.migrations.versions.v0104_care_events_backfill import migration

RECENT = (datetime.now(UTC) - timedelta(days=10)).isoformat()


def _row(key: str, *, tenant: str = "t1", plant: str | None = "p1", site_tenant: str = "t1", **doc: Any) -> dict:
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


class _Repo:
    """Records what the migration hands the production writer; ``present`` keys are 'logged meanwhile'."""

    instances: list[_Repo] = []
    present: set[str] = set()

    def __init__(self, db: Any) -> None:
        self.calls: list[tuple[str, list[CareEvent]]] = []
        _Repo.instances.append(self)

    def insert_backfilled(self, events: list[CareEvent], *, tenant_key: str) -> tuple[int, int]:
        self.calls.append((tenant_key, events))
        already = sum(1 for e in events if (e.source_ref or {}).get("key") in _Repo.present)
        return len(events) - already, already


class _Db:
    def has_collection(self, name: str) -> bool:
        return True


@pytest.fixture
def feed(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Feed ``rows`` as the watering scan; the other three sources are empty."""
    _Repo.instances = []
    _Repo.present = set()
    state: dict[str, Any] = {"rows": []}
    monkeypatch.setattr(v0104, "ArangoCareEventRepository", _Repo)
    monkeypatch.setattr(
        v0104, "_count_window", lambda db, source, cutoff: {"outside_r25": 2} if source == "watering_events" else {}
    )
    monkeypatch.setattr(
        v0104, "_scan", lambda db, source, cutoff: iter(state["rows"] if source == "watering_events" else [])
    )
    return state


def _written(report: MigrationReport) -> int:
    return int(report.details["totals"]["written"])


def test_the_dry_run_never_reaches_the_writer_and_reports_the_plan(feed) -> None:  # type: ignore[no-untyped-def]
    feed["rows"] = [_row("a"), _row("b"), _row("c", plant=None)]

    report = migration.up(_Db(), dry_run=True)

    assert not any(repo.calls for repo in _Repo.instances)
    assert report.changed == 0 and report.dry_run is True
    entry = report.details["sources"]["watering_events"]
    assert (entry["will_write"], entry["without_bed"], entry["outside_r25"], entry["read"]) == (2, 1, 2, 5)
    assert report.details["totals"]["counts_add_up"] is True
    assert report.scanned == 5


def test_the_real_run_hands_the_writer_exactly_what_the_dry_run_planned(feed) -> None:  # type: ignore[no-untyped-def]
    feed["rows"] = [_row("a"), _row("b"), _row("x", tenant="t2"), _row("c", plant=None)]
    planned = migration.up(_Db(), dry_run=True).details["sources"]["watering_events"]["listed_keys"]

    report = migration.up(_Db())

    handed = [e for repo in _Repo.instances for _, events in repo.calls for e in events]
    assert [e.source_ref["key"] for e in handed] == planned == ["a", "b"]
    assert report.changed == _written(report) == 2
    # the foreign-stamped document reached no call at all
    assert all(e.tenant_key == "t1" for e in handed)
    assert report.details["sources"]["watering_events"]["without_bed_reasons"]["tenant_mismatch"]["listed"] == ["x"]


def test_a_volume_over_the_batch_is_written_in_bounded_transactions(feed) -> None:  # type: ignore[no-untyped-def]
    count = v0104._BATCH_SIZE * 2 + 5
    feed["rows"] = [_row(f"w{i:04d}") for i in range(count)]

    report = migration.up(_Db())

    calls = [events for repo in _Repo.instances for _, events in repo.calls]
    assert [len(events) for events in calls] == [v0104._BATCH_SIZE, v0104._BATCH_SIZE, 5]
    assert report.changed == count


def test_what_the_index_reports_present_moves_from_will_write_to_already_present(feed) -> None:  # type: ignore[no-untyped-def]
    feed["rows"] = [_row("a"), _row("b")]
    _Repo.present = {"b"}

    report = migration.up(_Db())

    entry = report.details["sources"]["watering_events"]
    assert (entry["will_write"], entry["already_present"]) == (1, 1)
    assert report.changed == 1
    assert report.details["totals"]["counts_add_up"] is True


def test_a_row_the_scan_marks_present_is_counted_and_never_mapped(feed) -> None:  # type: ignore[no-untyped-def]
    feed["rows"] = [{**_row("a"), "present": True}]

    report = migration.up(_Db())

    assert not any(repo.calls for repo in _Repo.instances)
    assert report.details["sources"]["watering_events"]["already_present"] == 1


def test_the_migration_is_reversible_and_down_without_the_collection_is_a_noop() -> None:
    class _NoCollection:
        def has_collection(self, name: str) -> bool:
            return False

    assert migration.reversible is True
    assert migration.down(_NoCollection()).changed == 0  # type: ignore[arg-type]
    assert migration.up(_NoCollection()).changed == 0  # type: ignore[arg-type]
