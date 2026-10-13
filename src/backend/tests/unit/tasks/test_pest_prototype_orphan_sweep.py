"""Issue #1771 — the sweep deletes contributed pest prototypes whose contribution is gone.

Before #1766 deleting a pest-image contribution left its prototype in the
inference-service's ``pest_embeddings``. The row names the contribution (key +
tenant) but no user, and the Art. 17 erasure finds prototypes only through the
user's contribution documents, so nothing but a tenant deletion reaches it.

These tests run the Celery task body the beat sends — through the DI provider,
the real ``InferenceServicePestPrototypeStore`` and the real HTTP client — against
an in-memory inference-service (``tests/support/fake_pest_inference_service.py``)
and in-memory contribution documents, and read the outcome off the service's
rows:

* orphaned prototypes (active and deactivated, any tenant) are deleted; a live
  contribution's prototype and a curated row sharing an orphan's record id stay;
* a second run removes nothing;
* the counts land in the sweep record and the log, never a key;
* an unreachable index, or a process that cannot reach it once a prototype may
  exist, fails the task and records nothing;
* many keys are listed and erased in bounded requests.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
import structlog.testing

from app.common import dependencies
from app.common.exceptions import ExternalSourceError, FeatureNotConfiguredError
from app.config.settings import settings
from app.tasks.pest_image_tasks import sweep_orphaned_pest_prototypes_task
from tests.support.fake_pest_inference_service import FakePestInferenceService, route_pest_requests_to

TOKEN = "svc-token-1771"


class _Contributions:
    """In-memory ``pest_image_contributions``: only the lookup the sweep makes."""

    def __init__(self, keys: set[str]) -> None:
        self.keys = set(keys)
        self.lookups: list[list[str]] = []

    def existing_keys(self, keys: list[str]) -> set[str]:
        self.lookups.append(list(keys))
        return {key for key in keys if key in self.keys}


class _SettingsRepo:
    """In-memory ``system_settings`` singleton: the marker and the sweep record."""

    def __init__(self, since: datetime | None = None) -> None:
        self.since = since
        self.runs: list[dict[str, Any]] = []

    def pest_prototype_contributions_since(self) -> datetime | None:
        return self.since

    def record_pest_prototype_orphan_sweep(self, **run: Any) -> None:
        self.runs.append(run)


@pytest.fixture
def index(monkeypatch) -> FakePestInferenceService:
    monkeypatch.setattr(settings, "pest_detection_enabled", True)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(settings, "inference_service_url", "http://recognition.test:8000")
    monkeypatch.setattr(settings, "internal_service_token", TOKEN)
    fake = FakePestInferenceService(token=TOKEN)
    # Live contributions: a promoted (active) and a demoted (deactivated) row.
    fake.add_contribution(label="spider_mite", tenant_key="t-a", contribution_key="c-live")
    fake.add_contribution(label="aphid", tenant_key="t-a", contribution_key="c-live-demoted", active=False)
    # Orphans left by pre-#1766 deletes: active, deactivated, another tenant,
    # and one key with rows under two labels.
    fake.add_contribution(label="spider_mite", tenant_key="t-a", contribution_key="c-gone-1")
    fake.add_contribution(label="aphid", tenant_key="t-a", contribution_key="c-gone-2", active=False)
    fake.add_contribution(label="aphid", tenant_key="t-b", contribution_key="c-gone-3")
    fake.add_contribution(label="thrips", tenant_key="t-b", contribution_key="c-gone-3")
    # A curated row sharing an orphan's record id.
    fake.add_curated(label="spider_mite", record="c-gone-1")
    route_pest_requests_to(monkeypatch, fake)
    return fake


def _wire(monkeypatch, contributions: _Contributions, settings_repo: _SettingsRepo) -> None:
    monkeypatch.setattr(dependencies, "get_pest_image_repo", lambda: contributions)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", lambda: settings_repo)


def _rows(fake: FakePestInferenceService) -> list[tuple[str, str, str]]:
    return sorted((r["source"], r["source_record_id"], r["label"]) for r in fake.rows)


def test_the_sweep_deletes_only_prototypes_without_a_contribution(monkeypatch, index):
    settings_repo = _SettingsRepo()
    _wire(monkeypatch, _Contributions({"c-live", "c-live-demoted"}), settings_repo)

    outcome = sweep_orphaned_pest_prototypes_task()

    assert _rows(index) == [
        ("gbif", "c-gone-1", "spider_mite"),
        ("user_contributed", "c-live", "spider_mite"),
        ("user_contributed", "c-live-demoted", "aphid"),
    ]
    assert outcome == {
        "status": "completed",
        "examined": 5,
        "orphaned": 3,
        "removed": 4,
        "binding": "inference_service",
    }
    ((run,),) = [settings_repo.runs]
    assert {k: v for k, v in run.items() if k != "now"} == {
        "examined": 5,
        "orphaned": 3,
        "removed": 4,
        "binding": "inference_service",
    }


def test_a_second_run_removes_nothing(monkeypatch, index):
    settings_repo = _SettingsRepo()
    _wire(monkeypatch, _Contributions({"c-live", "c-live-demoted"}), settings_repo)
    sweep_orphaned_pest_prototypes_task()
    rows_after_first = _rows(index)

    second = sweep_orphaned_pest_prototypes_task()

    assert _rows(index) == rows_after_first
    assert second["examined"] == 2
    assert second["orphaned"] == 0
    assert second["removed"] == 0
    erase_calls = [r for r in index.requests if r.url.path.endswith("/erase")]
    assert len(erase_calls) == 1  # the first run's only; the second sends none


def test_the_log_and_the_requests_carry_counts_not_keys(monkeypatch, index):
    _wire(monkeypatch, _Contributions({"c-live", "c-live-demoted"}), _SettingsRepo())

    with structlog.testing.capture_logs() as logs:
        sweep_orphaned_pest_prototypes_task()

    assert "c-gone" not in json.dumps(logs, default=str)
    assert "c-live" not in json.dumps(logs, default=str)
    (done,) = [e for e in logs if e["event"] == "pest_prototype_orphan_sweep_completed"]
    assert (done["examined"], done["orphaned"], done["removed"]) == (5, 3, 4)
    assert all("c-" not in str(r.url) for r in index.requests)


@pytest.mark.parametrize("status", [502, 503])
def test_an_unreachable_index_fails_the_task_and_records_nothing(monkeypatch, index, status):
    settings_repo = _SettingsRepo()
    _wire(monkeypatch, _Contributions(set()), settings_repo)
    index.failure_status = status

    with structlog.testing.capture_logs() as logs, pytest.raises(ExternalSourceError):
        sweep_orphaned_pest_prototypes_task()

    assert settings_repo.runs == []
    (failed,) = [e for e in logs if e["event"] == "pest_prototype_orphan_sweep_failed"]
    assert failed["log_level"] == "error"
    assert f"HTTP {status}" in failed["reason"]


def test_a_process_without_the_service_refuses_once_a_prototype_may_exist(monkeypatch):
    monkeypatch.setattr(settings, "pest_detection_enabled", False)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    settings_repo = _SettingsRepo(since=datetime(2026, 7, 1))
    _wire(monkeypatch, _Contributions(set()), settings_repo)

    with pytest.raises(FeatureNotConfiguredError):
        sweep_orphaned_pest_prototypes_task()

    assert settings_repo.runs == []


def test_a_process_without_the_service_and_no_marker_skips_and_records_nothing(monkeypatch):
    # v0061 does not mark a deployment whose contribution documents were all
    # deleted — the #1771 residue itself — so "no marker" must not read as "swept".
    monkeypatch.setattr(settings, "pest_detection_enabled", False)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    settings_repo = _SettingsRepo(since=None)
    _wire(monkeypatch, _Contributions(set()), settings_repo)

    with structlog.testing.capture_logs() as logs:
        outcome = sweep_orphaned_pest_prototypes_task()

    assert outcome == {"status": "skipped", "examined": 0, "orphaned": 0, "removed": 0, "binding": "noop"}
    assert settings_repo.runs == []
    assert [e["event"] for e in logs if e["log_level"] == "warning"] == ["pest_prototype_orphan_sweep_skipped"]
    assert not [e for e in logs if e["event"] == "pest_prototype_orphan_sweep_completed"]


def test_many_keys_are_listed_and_erased_in_bounded_requests(monkeypatch, index):
    for n in range(1203):
        index.add_contribution(label="aphid", tenant_key="t-c", contribution_key=f"c-bulk-{n:04d}")
    contributions = _Contributions({"c-live", "c-live-demoted"} | {f"c-bulk-{n:04d}" for n in range(0, 1203, 2)})
    _wire(monkeypatch, contributions, _SettingsRepo())

    outcome = sweep_orphaned_pest_prototypes_task()

    listing = [json.loads(r.content) for r in index.requests if r.url.path.endswith("/keys")]
    erases = [json.loads(r.content)["contribution_keys"] for r in index.requests if r.url.path.endswith("/erase")]
    assert all(page["limit"] <= 1000 for page in listing)
    assert len(listing) >= 3
    assert all(0 < len(batch) <= 1000 for batch in erases)
    assert all(len(lookup) <= 1000 for lookup in contributions.lookups)
    assert outcome["examined"] == 1208
    assert outcome["orphaned"] == 3 + 601
    remaining = {r["source_record_id"] for r in index.rows if r["source"] == "user_contributed"}
    assert remaining == contributions.keys


def test_the_beat_runs_the_sweep_daily_after_the_erasures():
    from app.tasks import celery_app

    entry = celery_app.conf.beat_schedule["retention-sweep-orphaned-pest-prototypes-daily"]
    erasures = celery_app.conf.beat_schedule["retention-execute-erasures-daily"]["schedule"]
    assert entry["task"] == sweep_orphaned_pest_prototypes_task.name
    assert entry["schedule"].hour == {4} and entry["schedule"].minute == {30}
    assert erasures.hour == {4} and erasures.minute == {0}


def test_a_key_blank_to_the_erase_route_is_not_sent_and_does_not_stop_the_run(monkeypatch, index):
    # U+00A0 is not whitespace to the index's regex under glibc/C locales but is
    # to Python's ``strip`` — the erase route would refuse it with 422 every day.
    index.add_contribution(label="aphid", tenant_key="t-a", contribution_key="\xa0")
    _wire(monkeypatch, _Contributions({"c-live", "c-live-demoted"}), _SettingsRepo())

    outcome = sweep_orphaned_pest_prototypes_task()

    assert outcome["status"] == "completed"
    assert outcome["orphaned"] == 3
    erased = [json.loads(r.content)["contribution_keys"] for r in index.requests if r.url.path.endswith("/erase")]
    assert all(key.strip() for batch in erased for key in batch)
