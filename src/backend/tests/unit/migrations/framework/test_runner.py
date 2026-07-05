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
    ``time`` calls interfering.
    """

    def __init__(self) -> None:
        self.sleeps: list[float] = []
        self.monotonic = _real_time.monotonic

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


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


class TestRunPendingMigrations:
    def test_lock_contention_waits_then_returns_once_head_reached(self, fake_db, monkeypatch):
        # A concurrent replica holds the lock: this runner must WAIT until the
        # winner's applied set reaches head, then complete startup (not serve
        # traffic against un-migrated data).
        monkeypatch.setattr(runner_module, "load_migrations", lambda: [])
        monkeypatch.setattr(
            MigrationRunner,
            "upgrade",
            lambda self, db: (_ for _ in ()).throw(MigrationLockError("held")),
        )

        # runner.migrations is [] → head set empty → barrier satisfied at once.
        assert runner_module.run_pending_migrations(fake_db) == []

    def test_lock_contention_polls_until_winner_finishes(self, fake_db, make_migration, monkeypatch):
        migrations = [make_migration("0001"), make_migration("0002")]
        monkeypatch.setattr(runner_module, "load_migrations", lambda: list(migrations))
        monkeypatch.setattr(
            MigrationRunner,
            "upgrade",
            lambda self, db: (_ for _ in ()).throw(MigrationLockError("held")),
        )

        # Replace only the runner's `time` reference so pytest internals keep the
        # real clock; record sleeps and let monotonic run real (deadline is far).
        fake_time = _FakeTime()
        monkeypatch.setattr(runner_module, "time", fake_time)

        # Head reached on the third applied_versions() poll (winner finishing).
        polls = iter([set(), {"0001"}, {"0001", "0002"}])
        monkeypatch.setattr(tracking, "applied_versions", lambda db: next(polls))

        assert runner_module.run_pending_migrations(fake_db) == []
        assert len(fake_time.sleeps) == 2  # slept between the two not-yet-ready polls

    def test_barrier_timeout_raises_to_fail_readiness(self, fake_db, make_migration, monkeypatch):
        migrations = [make_migration("0001")]
        monkeypatch.setattr(runner_module, "load_migrations", lambda: list(migrations))
        monkeypatch.setattr(
            MigrationRunner,
            "upgrade",
            lambda self, db: (_ for _ in ()).throw(MigrationLockError("held")),
        )
        monkeypatch.setattr(runner_module, "time", _FakeTime())
        # A non-positive budget makes the deadline already-elapsed: the winner
        # never reaches head, so the barrier fails readiness at once.
        monkeypatch.setattr(runner_module, "BARRIER_TIMEOUT_SECONDS", -1.0)
        monkeypatch.setattr(tracking, "applied_versions", lambda db: set())

        with pytest.raises(MigrationBarrierTimeoutError):
            runner_module.run_pending_migrations(fake_db)
