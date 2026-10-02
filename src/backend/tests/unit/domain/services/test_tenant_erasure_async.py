"""#1792 — a tenant deletion is accepted by the request and erased by a worker, with a claim heartbeat.

``delete_tenant`` used to authorise, freeze and then run the whole erasure inside
the HTTP handler. Now it records the deletion, freezes the tenant and dispatches
the Celery task; the task (:meth:`TenantService.run_tenant_erasure_task`, the body
of ``app.tasks.tenant_tasks.run_tenant_erasure``) claims the record atomically and
runs it. These tests drive that split, the heartbeat between batches, the lost
claim and the escalation. What the ArangoDB run removes in batches is measured
against a real server in ``tests/integration/test_tenant_erasure_batches.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest

from app.common.exceptions import TenantErasureClaimLostError, WriteConflictError
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.tenant_erasure import TenantErasureReport
from tests.support.tenant_erasure_doubles import (
    FakeTenantErasureRepository,
    RecordingTenantErasureExecutor,
    authorized,
    delete_and_run,
    tenant_service_for_deletion,
)

NOW = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)
KEY = "t-1"
RECORD = TenantErasureEngine.record_key(KEY)


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


class _Beating(RecordingTenantErasureExecutor):
    """An executor that reports progress the way the Arango one does: parents first, then a beat per batch."""

    def __init__(self, *, batches: int = 3, parent_keys: dict[str, list[str]] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._batches = batches
        self._parent_keys = parent_keys or {"sites": ["site-1"]}
        self.beats = 0

    def run_tenant_erasure(self, plan, *, pseudonymize, on_progress=None):  # type: ignore[no-untyped-def]
        self.plans.append(plan)
        if on_progress is not None:
            on_progress(self._parent_keys)  # before the first parent row goes
            for _ in range(self._batches):
                on_progress(self._parent_keys)
                self.beats += 1
        return TenantErasureReport(tenant_document_removed=True, parent_keys=self._parent_keys)


class TestTheRequestAcceptsTheWorkerErases:
    def test_the_request_records_freezes_and_dispatches_but_erases_nothing(self) -> None:
        executor = RecordingTenantErasureExecutor()
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)

        accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "in_progress"
        assert accepted.attempt_count == 0
        assert executor.plans == []  # nothing ran in the request
        assert repo.records[RECORD]["last_attempt_at"] is None  # and no claim was taken
        service._membership_repo.deactivate_all_for_tenant.assert_called_once_with(KEY)
        assert service.dispatched == [RECORD]

    def test_the_real_dispatch_enqueues_the_task_with_the_record_key(self) -> None:
        service = tenant_service_for_deletion()
        del service._dispatch_tenant_erasure  # the unit double replaced it on the instance

        with patch("app.tasks.tenant_tasks.run_tenant_erasure") as task:
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        task.delay.assert_called_once_with(RECORD)

    def test_a_broker_outage_keeps_the_freeze_and_the_record_for_the_beat(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)
        del service._dispatch_tenant_erasure

        with patch("app.tasks.tenant_tasks.run_tenant_erasure") as task:
            task.delay.side_effect = ConnectionError("broker down")
            accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "in_progress"
        assert RECORD in repo.records
        service._membership_repo.deactivate_all_for_tenant.assert_called_once_with(KEY)

    def test_the_beat_picks_up_a_never_dispatched_record_once_it_is_stale(self) -> None:
        executor = RecordingTenantErasureExecutor()
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        repo.records[RECORD]["updated_at"] = NOW.isoformat()

        fresh = service.resume_tenant_erasures(NOW + timedelta(hours=1))
        stale = service.resume_tenant_erasures(NOW + timedelta(hours=7))

        assert fresh["candidates"] == 0
        assert stale["completed"] == 1
        assert [plan.tenant_key for plan in executor.plans] == [KEY]

    def test_a_repeated_request_for_an_open_deletion_only_redispatches_it(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        again = service.delete_tenant(KEY, **authorized(KEY), now=NOW + timedelta(minutes=1))

        assert again.status == "in_progress"
        assert service.dispatched == [RECORD, RECORD]

    def test_a_repeated_request_while_a_run_is_alive_is_a_conflict(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        assert service.run_tenant_erasure_task(RECORD, NOW)["outcome"] == "completed"
        repo.records[RECORD].update(status="in_progress", completed_at=None)  # a run is mid-flight

        with pytest.raises(WriteConflictError):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW + timedelta(minutes=1))


class TestTheTaskClaimsAtomically:
    def test_two_tasks_for_one_record_run_the_erasure_once(self) -> None:
        executor = RecordingTenantErasureExecutor()
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        # The first task is mid-run: it claimed the record and its heartbeat is fresh.
        claimed = repo.claim_for_run(
            RECORD, now_iso=NOW.isoformat(), stale_before_iso=(NOW - timedelta(hours=6)).isoformat()
        )
        assert claimed is not None

        second = service.run_tenant_erasure_task(RECORD, NOW + timedelta(minutes=5))

        assert second == {"record_key": RECORD, "outcome": "not_claimed"}
        assert executor.plans == []

    def test_a_completed_or_unknown_record_is_nothing_to_do(self) -> None:
        service = tenant_service_for_deletion()

        assert service.run_tenant_erasure_task("ter_ghost", NOW)["outcome"] == "nothing_to_do"

    def test_a_deployment_that_cannot_erase_holds_the_record_untouched(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        service._tenant_erasure_executor = None

        outcome = service.run_tenant_erasure_task(RECORD, NOW)

        assert outcome["outcome"] == "held"
        assert repo.records[RECORD]["attempt_count"] == 0
        assert repo.records[RECORD]["last_attempt_at"] is None


class TestTheClaimIsRefreshedBetweenBatches:
    def test_every_batch_refreshes_the_claim_and_the_parents_are_persisted_once(self) -> None:
        repo = FakeTenantErasureRepository()
        executor = _Beating(batches=3)
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        beats: list[dict[str, Any]] = []
        real = repo.heartbeat

        def spying(key: str, **kwargs: Any) -> bool:
            beats.append(kwargs)
            return real(key, **kwargs)

        repo.heartbeat = spying  # type: ignore[method-assign]

        delete_and_run(service, KEY, **authorized(KEY), now=NOW)

        # after the external phase + before-parent beat + 3 batches + after the executor
        assert len(beats) == 6
        with_parents = [beat for beat in beats if beat["parent_keys"] is not None]
        assert len(with_parents) == 1  # unchanged parents are not rewritten on every batch
        assert with_parents[0]["parent_keys"] == {"sites": ["site-1"]}
        assert all(beat["claimed_at_iso"] == NOW.isoformat() for beat in beats)

    def test_a_long_run_is_not_claimed_a_second_time(self) -> None:
        """The reason for the heartbeat: a run longer than STALE_AFTER_HOURS used to be claimable by the beat."""
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=_Beating(), record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        claimed = service._claim_tenant_erasure(RECORD, NOW)
        assert claimed is not None
        # Seven hours into the run its heartbeat said "alive" five minutes ago.
        later = NOW + timedelta(hours=7)
        assert repo.heartbeat(
            RECORD, claimed_at_iso=NOW.isoformat(), now_iso=(later - timedelta(minutes=5)).isoformat()
        )

        assert service._claim_tenant_erasure(RECORD, later) is None
        # A crashed worker stops beating: its claim IS taken over once stale.
        assert service._claim_tenant_erasure(RECORD, later + timedelta(hours=7)) is not None

    def test_a_run_that_lost_its_claim_stops_without_writing_a_failure(self) -> None:
        repo = FakeTenantErasureRepository()
        executor = _Beating(batches=2)
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        real = repo.heartbeat
        calls = {"n": 0}

        def stolen(key: str, **kwargs: Any) -> bool:
            calls["n"] += 1
            if calls["n"] == 2:  # a second worker re-claimed it after the first run's beat lapsed
                repo.records[key]["last_attempt_at"] = (NOW + timedelta(hours=7)).isoformat()
            return real(key, **kwargs)

        repo.heartbeat = stolen  # type: ignore[method-assign]

        outcome = service.run_tenant_erasure_task(RECORD, NOW)

        record = repo.records[RECORD]
        assert outcome["outcome"] == "in_progress"  # still the other run's
        assert record["status"] == "in_progress"
        assert record["attempt_count"] == 0  # no failure was written onto the other run's record
        assert record["last_attempt_at"] == (NOW + timedelta(hours=7)).isoformat()

    def test_the_lost_claim_surfaces_to_a_synchronous_caller(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=_Beating(), record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        claimed = service._claim_tenant_erasure(RECORD, NOW)
        assert claimed is not None
        repo.records[RECORD]["last_attempt_at"] = (NOW + timedelta(hours=1)).isoformat()

        with pytest.raises(TenantErasureClaimLostError):
            service._run_tenant_erasure(claimed, NOW, raise_on_failure=True)


class TestARunThatKeepsFailingEscalates:
    def _failing(self, repo: FakeTenantErasureRepository) -> Any:
        executor = RecordingTenantErasureExecutor(raises=RuntimeError("transaction too large"))
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        return service

    def test_the_nth_failed_attempt_escalates_once_on_the_record_and_loudly_in_the_log(self) -> None:
        import structlog

        repo = FakeTenantErasureRepository()
        service = self._failing(repo)
        limit = TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS
        now = NOW
        with structlog.testing.capture_logs() as logs:
            for attempt in range(1, limit + 2):
                service.run_tenant_erasure_task(RECORD, now)
                if attempt < limit:
                    assert repo.records[RECORD].get("escalated_at") is None
                    assert not [e for e in logs if e["event"] == "tenant_erasure.escalated"]
                now += timedelta(days=8)  # past every backoff and stale window

        escalations = [e for e in logs if e["event"] == "tenant_erasure.escalated"]
        assert [e["attempt"] for e in escalations] == [limit, limit + 1]  # every failing run past the limit alerts
        assert escalations[0]["log_level"] == "error"
        assert repo.records[RECORD]["escalated_at"] is not None
        assert repo.records[RECORD]["attempt_count"] == limit + 1

    def test_escalated_at_is_stamped_once(self) -> None:
        repo = FakeTenantErasureRepository()
        service = self._failing(repo)
        now = NOW
        stamps = []
        for _ in range(TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS + 2):
            service.run_tenant_erasure_task(RECORD, now)
            stamps.append(repo.records[RECORD].get("escalated_at"))
            now += timedelta(days=8)

        first = next(stamp for stamp in stamps if stamp)
        assert [stamp for stamp in stamps if stamp] == [first] * (
            len(stamps) - (TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS - 1)
        )

    def test_the_beat_counts_the_escalated_deletions(self) -> None:
        repo = FakeTenantErasureRepository()
        service = self._failing(repo)
        now = NOW
        for _ in range(TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS - 1):
            service.run_tenant_erasure_task(RECORD, now)
            now += timedelta(days=8)

        result = service.resume_tenant_erasures(now)

        assert result["open"] == 1
        assert result["escalated"] == 1


def test_a_second_claim_cannot_extend_the_first_runs_heartbeat() -> None:
    """The double refuses what the real heartbeat refuses: a stamp that is not the record's."""
    repo = FakeTenantErasureRepository()
    service = tenant_service_for_deletion(record_repo=repo)
    service.delete_tenant(KEY, **authorized(KEY), now=NOW)
    service._claim_tenant_erasure(RECORD, NOW)

    assert (
        repo.heartbeat(RECORD, claimed_at_iso=(NOW - timedelta(hours=1)).isoformat(), now_iso=NOW.isoformat()) is False
    )
    assert repo.heartbeat("ter_ghost", claimed_at_iso=NOW.isoformat(), now_iso=NOW.isoformat()) is False
