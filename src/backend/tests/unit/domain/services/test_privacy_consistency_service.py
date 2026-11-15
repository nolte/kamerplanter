"""spec/privacy PRIV-206 / DEC-28 — the minimal privacy consistency beat counts, never corrects."""

from __future__ import annotations

from collections.abc import Sequence

from celery.schedules import crontab

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.tombstone_census import ITombstoneCensus
from app.domain.models.privacy import TOMBSTONE_REGEX
from app.domain.services.privacy_consistency_service import PrivacyConsistencyService
from app.observability.privacy_metrics import PRIVACY_UNDECLARED_TOMBSTONES
from app.tasks import celery_app


class _Census(ITombstoneCensus):
    def __init__(self, found: dict[str, int]) -> None:
        self.found = found
        self.asked: list[tuple[tuple[tuple[str, str], ...], str]] = []

    def count_tombstones(self, fields: Sequence[tuple[str, str]], pattern: str) -> dict[str, int]:
        self.asked.append((tuple(fields), pattern))
        return {f"{c}.{f}": self.found.get(f"{c}.{f}", 0) for c, f in fields}


class TestTheService:
    def test_it_asks_for_the_live_watch_cells_and_both_generations(self) -> None:
        census = _Census({})

        PrivacyConsistencyService(census).run()

        assert census.asked == [(ErasureEngine.tombstone_watch_fields(), TOMBSTONE_REGEX)]

    def test_the_watch_cells_never_include_the_allowlist(self) -> None:
        assert not set(ErasureEngine.tombstone_watch_fields()) & ErasureEngine.tombstone_allowlist()
        assert ("garden_plan_audit", "user_key") in ErasureEngine.tombstone_watch_fields()
        assert ("harvest_batches", "harvested_by_key") not in ErasureEngine.tombstone_watch_fields()

    def test_findings_are_reported_and_set_on_the_gauge(self) -> None:
        report = PrivacyConsistencyService(_Census({"care_events.performed_by_user_key": 2})).run()

        assert report.total == 2
        assert report.findings == {"care_events.performed_by_user_key": 2}
        gauge = PRIVACY_UNDECLARED_TOMBSTONES.labels(cell="care_events.performed_by_user_key")
        assert gauge._value.get() == 2

    def test_a_clean_installation_sets_every_cell_to_zero(self) -> None:
        PrivacyConsistencyService(_Census({"care_events.performed_by_user_key": 2})).run()

        report = PrivacyConsistencyService(_Census({})).run()

        assert report.total == 0
        assert PRIVACY_UNDECLARED_TOMBSTONES.labels(cell="care_events.performed_by_user_key")._value.get() == 0


class TestTheBeat:
    def test_the_task_is_registered_and_on_the_beat_clock(self) -> None:
        from app.tasks import privacy_consistency  # noqa: F401

        assert "privacy.consistency" in celery_app.tasks
        entries = [e for e in celery_app.conf.beat_schedule.values() if e["task"] == "privacy.consistency"]
        assert len(entries) == 1
        assert isinstance(entries[0]["schedule"], crontab)

    def test_the_module_is_on_the_include_list(self) -> None:
        assert "app.tasks.privacy_consistency" in celery_app.conf.include

    def test_the_task_wires_the_census(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        from app.common import dependencies
        from app.tasks.privacy_consistency import run_privacy_consistency

        census = _Census({"tasks.assigned_to_user_key": 1})
        monkeypatch.setattr(dependencies, "get_tombstone_census", lambda: census)

        assert run_privacy_consistency.run() == {"total": 1, "findings": {"tasks.assigned_to_user_key": 1}}
        assert len(census.asked) == 1
