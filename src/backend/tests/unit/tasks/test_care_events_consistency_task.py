"""WP 8.2 (#2645; GP-NFR-016) — the beat entry and the task that wires the consistency service."""

from __future__ import annotations

from types import SimpleNamespace

from celery.schedules import crontab

from app.common.enums import TenantStatus, TenantType
from app.domain.engines.care_event_backfill_mapper import SOURCE_COLLECTIONS
from app.domain.models.tenant import Tenant
from app.tasks import celery_app


def test_the_task_is_registered_and_on_the_beat_clock() -> None:
    from app.tasks import care_events_consistency  # noqa: F401

    assert "care_events.consistency" in celery_app.tasks
    entries = [e for e in celery_app.conf.beat_schedule.values() if e["task"] == "care_events.consistency"]
    assert len(entries) == 1
    assert isinstance(entries[0]["schedule"], crontab)  # a clock time, not a restartable interval


def test_the_module_is_on_the_celery_include_list() -> None:
    assert "app.tasks.care_events_consistency" in celery_app.conf.include


def test_the_task_asks_the_tenant_gate_and_uses_the_window_setting(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.common import dependencies
    from app.tasks import care_events_consistency as module

    class _Tenants:
        def get_by_key(self, key: str) -> Tenant | None:
            status = TenantStatus.ACTIVE if key == "open" else TenantStatus.SUSPENDED
            return Tenant(
                _key=key, name=key, slug=key, tenant_type=TenantType.ORGANIZATION, owner_user_key="o", status=status
            )

    class _Gaps:
        asked: list = []

        def candidates(self, source, since):  # type: ignore[no-untyped-def]
            _Gaps.asked.append(since)
            if source != "watering_events":
                return
            for key, tenant in (("a", "open"), ("b", "closed")):
                yield {
                    "doc": {
                        "_key": key,
                        "tenant_key": tenant,
                        "watered_at": "2026-11-02T10:00:00+00:00",
                        "volume_liters": 1,
                    },
                    "refs": [{"ref": "p", "kind": "plant", "location_key": "L", "plant_tenant": tenant}],
                    "own_location_key": None,
                    "locations": [
                        {"key": "L", "found": True, "site_key": "S", "site_found": True, "site_tenant": tenant}
                    ],
                    "present": False,
                }

    _Gaps.asked = []
    written: list = []

    class _Events:
        def insert_backfilled(self, events, *, tenant_key):  # type: ignore[no-untyped-def]
            written.extend(e.source_ref["key"] for e in events)
            return len(events), 0

    monkeypatch.setattr(dependencies, "get_care_event_gap_reader", lambda: _Gaps())
    monkeypatch.setattr(dependencies, "get_care_event_repo", lambda: _Events())
    monkeypatch.setattr(dependencies, "get_tenant_repo", lambda: _Tenants())
    monkeypatch.setattr(module, "settings", SimpleNamespace(care_events_consistency_window_days=3))

    result = module.run_care_events_consistency()

    assert written == ["a"]  # the suspended tenant's gap is not written
    assert result["hits"] == 1 and result["skipped_inactive_tenant"] == 1
    assert len(_Gaps.asked) == len(SOURCE_COLLECTIONS)  # one scan per source, all asked for the same window
