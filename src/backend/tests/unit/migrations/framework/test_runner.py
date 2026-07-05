"""NFR-016 M-1/M-4/M-7/M-8 — runner ordering, tracking, drift, lock, rollback."""

from __future__ import annotations

import time as _real_time

import pytest

from app.migrations.framework import runner as runner_module
from app.migrations.framework import tracking
from app.migrations.framework.report import (
    IrreversibleMigrationError,
    MigrationBarrierTimeoutError,
    MigrationLockError,
    NonLinearHistoryError,
)
from app.migrations.framework.runner import MigrationRunner


class _FakeTime:
    """Stand-in for the runner's ``time`` module: real monotonic, recorded sleep.

    Substituted for ``runner_module.time`` (not the global module) so the barrier
    can be driven deterministically without a real sleep and without pytest's own
    ``time`` calls interfering.  An optional ``on_sleep`` hook fires each round so
    a test can advance the simulated world (e.g. release the winner's lock) while
    the losing runner "waits".
    """

    def __init__(self, on_sleep=None) -> None:
        self.sleeps: list[float] = []
        self.monotonic = _real_time.monotonic
        self.perf_counter = _real_time.perf_counter  # the real upgrade() times itself with this
        self._on_sleep = on_sleep

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        if self._on_sleep is not None:
            self._on_sleep(len(self.sleeps))


class TestPlan:
    def test_plan_returns_pending_in_order(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0002"), make_migration("0001"), make_migration("0003")])
        tracking.record(fake_db, make_migration("0001"), 1.0)

        pending = runner.plan(fake_db)
        assert [m.version for m in pending] == ["0002", "0003"]

    def test_gap_before_head_raises(self, fake_db, make_migration):
        # Declared 0001..0003; applied {0001, 0003} — 0002 is an unapplied gap
        # before the applied head 0003.
        runner = MigrationRunner([make_migration("0001"), make_migration("0002"), make_migration("0003")])
        tracking.record(fake_db, make_migration("0001"), 1.0)
        tracking.record(fake_db, make_migration("0003"), 1.0)

        with pytest.raises(NonLinearHistoryError):
            runner.plan(fake_db)


class TestUpgrade:
    def test_applies_all_pending_and_tracks(self, fake_db, make_migration):
        m1 = make_migration("0001", up_changed=1)
        m2 = make_migration("0002", up_changed=2)
        runner = MigrationRunner([m1, m2])

        reports = runner.upgrade(fake_db)

        assert [r.version for r in reports] == ["0001", "0002"]
        assert tracking.applied_versions(fake_db) == {"0001", "0002"}
        assert m1.up_calls == [False] and m2.up_calls == [False]
        # Duration is filled in by the runner.
        assert all(r.duration_ms >= 0.0 for r in reports)

    def test_rerun_is_noop(self, fake_db, make_migration):
        m1, m2 = make_migration("0001"), make_migration("0002")
        runner = MigrationRunner([m1, m2])
        runner.upgrade(fake_db)

        reports = runner.upgrade(fake_db)
        assert reports == []
        # up() was only ever called once per migration.
        assert m1.up_calls == [False] and m2.up_calls == [False]

    def test_dry_run_does_not_track(self, fake_db, make_migration):
        m1 = make_migration("0001", up_changed=5)
        runner = MigrationRunner([m1])

        reports = runner.upgrade(fake_db, dry_run=True)

        assert reports[0].dry_run is True
        assert m1.up_calls == [True]
        # Nothing recorded — a subsequent real upgrade still sees it as pending.
        assert tracking.applied_versions(fake_db) == set()

    def test_target_limits_applied_set(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0001"), make_migration("0002"), make_migration("0003")])

        runner.upgrade(fake_db, target="2")

        assert tracking.applied_versions(fake_db) == {"0001", "0002"}

    def test_lock_held_blocks_second_runner(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0001")])
        tracking.acquire_lock(fake_db)  # a concurrent runner holds the lock

        with pytest.raises(MigrationLockError):
            runner.upgrade(fake_db)

    def test_checksum_drift_logs_warning(self, fake_db, make_migration, monkeypatch):
        runner = MigrationRunner([make_migration("0001")])
        runner.upgrade(fake_db)

        # Simulate the source of an applied migration having changed.
        from app.data_access.arango.collections import SCHEMA_MIGRATIONS

        col = fake_db.collection(SCHEMA_MIGRATIONS)
        doc = col.get("0001")
        doc["checksum"] = "drifted-checksum"
        col.replace(doc)

        warnings: list[tuple] = []
        monkeypatch.setattr(
            runner_module.logger,
            "warning",
            lambda event, **kw: warnings.append((event, kw)),
        )

        runner.upgrade(fake_db)  # no pending, but drift is checked

        assert any(event == "migration_checksum_drift" and kw.get("version") == "0001" for event, kw in warnings)


class TestDowngrade:
    def test_reversible_rollback_removes_tracking(self, fake_db, make_migration):
        m1 = make_migration("0001", reversible=True)
        m2 = make_migration("0002", reversible=True)
        runner = MigrationRunner([m1, m2])
        runner.upgrade(fake_db)

        reports = runner.downgrade(fake_db, target="1")

        assert [r.version for r in reports] == ["0002"]
        assert m2.down_calls == [False]
        assert tracking.applied_versions(fake_db) == {"0001"}

    def test_irreversible_rollback_raises(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0001", reversible=True), make_migration("0002", reversible=False)])
        runner.upgrade(fake_db)

        with pytest.raises(IrreversibleMigrationError):
            runner.downgrade(fake_db, target="1")

    def test_downgrade_releases_lock_after_error(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0001", reversible=True), make_migration("0002", reversible=False)])
        runner.upgrade(fake_db)

        with pytest.raises(IrreversibleMigrationError):
            runner.downgrade(fake_db, target="1")

        # The lock must be released even though down() raised.
        tracking.acquire_lock(fake_db)


class TestInspection:
    def test_current_and_history(self, fake_db, make_migration):
        runner = MigrationRunner([make_migration("0001"), make_migration("0002")])
        runner.upgrade(fake_db)

        assert runner.current(fake_db) == "0002"
        assert [row["version"] for row in runner.history(fake_db)] == ["0001", "0002"]


class TestPreconditionUnmet:
    def test_unmet_precondition_leaves_migration_and_successors_pending(self, fake_db, make_migration):
        # 0002 reports its precondition unmet — it and 0003 must stay pending,
        # and 0002 must NOT be recorded (M-1 keeps history linear).
        m1 = make_migration("0001", up_changed=1)
        m2 = make_migration("0002", precondition_unmet=True)
        m3 = make_migration("0003", up_changed=1)
        runner = MigrationRunner([m1, m2, m3])

        reports = runner.upgrade(fake_db)

        assert [r.version for r in reports] == ["0001", "0002"]
        assert reports[-1].precondition_unmet is True
        # Only 0001 recorded; 0002/0003 remain pending for a later boot.
        assert tracking.applied_versions(fake_db) == {"0001"}
        assert m3.up_calls == []  # successor never ran

    def test_precondition_met_on_retry_records_applied(self, fake_db, make_migration):
        # First boot: precondition unmet → pending. Second boot: same version now
        # succeeds → recorded, and the successor applies too.
        runner1 = MigrationRunner([make_migration("0001", precondition_unmet=True), make_migration("0002")])
        runner1.upgrade(fake_db)
        assert tracking.applied_versions(fake_db) == set()

        runner2 = MigrationRunner([make_migration("0001"), make_migration("0002")])
        runner2.upgrade(fake_db)
        assert tracking.applied_versions(fake_db) == {"0001", "0002"}


class _FlakyUpgrade:
    """MigrationRunner.upgrade stub: raise MigrationLockError N times, then succeed."""

    def __init__(self, lock_errors: int, result=None) -> None:
        self.remaining = lock_errors
        self.result = result if result is not None else []
        self.calls = 0

    def __call__(self, db):
        # Assigned onto the class but not a descriptor, so it is invoked unbound:
        # ``runner.upgrade(db)`` calls this with ``db`` as the only argument.
        self.calls += 1
        if self.remaining > 0:
            self.remaining -= 1
            raise MigrationLockError("held")
        return self.result


class TestRunPendingMigrations:
    def test_no_contention_returns_upgrade_result(self, fake_db, monkeypatch):
        monkeypatch.setattr(runner_module, "load_migrations", lambda: [])
        monkeypatch.setattr(MigrationRunner, "upgrade", _FlakyUpgrade(lock_errors=0))
        # Lock free on the first attempt → returns immediately, no waiting.
        assert runner_module.run_pending_migrations(fake_db) == []

    def test_lock_contention_retries_until_lock_released(self, fake_db, monkeypatch):
        # The winner holds the lock for two rounds, then releases; this runner
        # re-attempts upgrade each round and completes once it wins the lock.
        monkeypatch.setattr(runner_module, "load_migrations", lambda: [])
        flaky = _FlakyUpgrade(lock_errors=2)
        monkeypatch.setattr(MigrationRunner, "upgrade", flaky)
        fake_time = _FakeTime()
        monkeypatch.setattr(runner_module, "time", fake_time)

        assert runner_module.run_pending_migrations(fake_db) == []
        assert flaky.calls == 3  # two blocked attempts + the successful retry
        assert len(fake_time.sleeps) == 2  # waited between the blocked attempts

    def test_barrier_timeout_raises_when_lock_never_released(self, fake_db, monkeypatch):
        # The winner never releases: the runner fails readiness rather than serve
        # un-migrated data.
        monkeypatch.setattr(runner_module, "load_migrations", lambda: [])
        monkeypatch.setattr(MigrationRunner, "upgrade", _FlakyUpgrade(lock_errors=99))
        monkeypatch.setattr(runner_module, "time", _FakeTime())
        monkeypatch.setattr(runner_module, "BARRIER_TIMEOUT_SECONDS", -1.0)  # deadline already elapsed

        with pytest.raises(MigrationBarrierTimeoutError):
            runner_module.run_pending_migrations(fake_db)

    def test_loser_does_not_crash_when_winner_leaves_v0004_pending(self, fake_db, make_migration, monkeypatch):
        # Regression (D2 x D3): the winning replica legitimately leaves a
        # precondition-unmet migration pending, so the applied set never reaches
        # head.  The losing replica must NOT block forever / crash-loop — it
        # re-runs upgrade itself, also leaves the migration pending, and returns.
        migrations = [make_migration("0001", up_changed=1), make_migration("0002", precondition_unmet=True)]
        monkeypatch.setattr(runner_module, "load_migrations", lambda: list(migrations))

        # The winner holds the lock; releasing it happens while the loser "waits".
        winner = tracking.acquire_lock(fake_db)

        def _release_on_wait(_round):
            tracking.release_lock(fake_db, winner)

        monkeypatch.setattr(runner_module, "time", _FakeTime(on_sleep=_release_on_wait))

        reports = runner_module.run_pending_migrations(fake_db)

        # Completed normally (no MigrationBarrierTimeoutError): 0001 applied,
        # 0002 left pending for a later tenant-bearing boot.
        assert [r.version for r in reports] == ["0001", "0002"]
        assert reports[-1].precondition_unmet is True
        assert tracking.applied_versions(fake_db) == {"0001"}
