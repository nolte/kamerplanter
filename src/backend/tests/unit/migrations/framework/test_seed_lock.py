"""#2028 — the seed registry runs under the migration lock: one replica seeds, the others wait.

Driven against the in-memory ``schema_migrations`` fake whose ``_rev`` fencing matches
the driver (``conftest.py``). Time is faked: ``sleep`` advances the clock and runs a
hook, which is where "the other replica" finishes its run, releases its lock or dies.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import structlog.testing

from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework import tracking
from app.migrations.framework.report import SeedBarrierTimeoutError, SeedLockLostError
from app.migrations.seeds import registry
from app.migrations.seeds.registry import SeedJob, run_seeds, seed_fingerprint


class _FakeTime:
    def __init__(self, on_sleep: Callable[[int], None] | None = None) -> None:
        self.now = 0.0
        self.sleeps = 0
        self._on_sleep = on_sleep

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps += 1
        self.now += seconds
        if self._on_sleep is not None:
            self._on_sleep(self.sleeps)


def _jobs(calls: list[str], *names: str) -> list[SeedJob]:
    return [SeedJob(name, lambda _db, n=name: calls.append(n)) for name in names]


def _hold_lock(fake_db, owner: str = "other-replica", *, age_seconds: float = 0.0) -> None:
    acquired = datetime.now(UTC) - timedelta(seconds=age_seconds)
    fake_db.collection(SCHEMA_MIGRATIONS).insert(
        {"_key": tracking.LOCK_KEY, "owner": owner, "acquired_at": acquired.isoformat()}
    )


def _release_other(fake_db) -> None:
    fake_db.collection(SCHEMA_MIGRATIONS).delete(tracking.LOCK_KEY)


@pytest.fixture
def fake_time(monkeypatch):
    clock = _FakeTime()
    monkeypatch.setattr(registry, "time", clock)
    return clock


class TestUncontended:
    def test_runs_every_job_records_the_run_and_releases_the_lock(self, fake_db, fake_time) -> None:
        calls: list[str] = []
        jobs = _jobs(calls, "a", "b")

        run_seeds(fake_db, jobs=jobs)

        assert calls == ["a", "b"]
        marker = tracking.seed_run_marker(fake_db)
        assert marker is not None
        assert marker["fingerprint"] == seed_fingerprint(["a", "b"])
        assert marker["failed_jobs"] == []
        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is None
        assert fake_time.sleeps == 0

    def test_a_failed_non_fatal_job_is_recorded(self, fake_db, fake_time) -> None:
        def boom(_db) -> None:
            raise RuntimeError("bad seed file")

        run_seeds(fake_db, jobs=[SeedJob("bad", boom), SeedJob("ok", lambda _db: None)])

        assert tracking.seed_run_marker(fake_db)["failed_jobs"] == ["bad"]

    def test_a_fatal_failure_releases_the_lock_and_records_no_run(self, fake_db, fake_time) -> None:
        def boom(_db) -> None:
            raise RuntimeError("structural")

        with pytest.raises(RuntimeError, match="structural"):
            run_seeds(fake_db, jobs=[SeedJob("location_types", boom, fatal=True)])

        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is None
        assert tracking.seed_run_marker(fake_db) is None


class TestWaitingForAnotherReplica:
    def test_a_run_completed_while_waiting_is_not_repeated(self, fake_db, monkeypatch) -> None:
        """The waiter gets the lock after the other replica's complete run and does not seed."""
        calls: list[str] = []
        jobs = _jobs(calls, "a", "b")
        _hold_lock(fake_db)

        def other_replica_finishes(sleeps: int) -> None:
            if sleeps == 3:
                tracking.record_seed_run(
                    fake_db, run_id="run-other", fingerprint=seed_fingerprint(["a", "b"]), failed_jobs=[]
                )
                _release_other(fake_db)

        monkeypatch.setattr(registry, "time", _FakeTime(other_replica_finishes))

        with structlog.testing.capture_logs() as logs:
            run_seeds(fake_db, jobs=jobs)

        assert calls == []
        assert any(e["event"] == "seeds_completed_by_other_replica" for e in logs)
        assert tracking.seed_run_marker(fake_db)["run_id"] == "run-other"
        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is None

    def test_a_marker_older_than_the_wait_does_not_make_the_waiter_skip(self, fake_db, monkeypatch) -> None:
        """Contended on a lock held for something else (migrations): no run completed, so seed."""
        calls: list[str] = []
        tracking.record_seed_run(fake_db, run_id="last-boot", fingerprint=seed_fingerprint(["a"]), failed_jobs=[])
        _hold_lock(fake_db)
        monkeypatch.setattr(
            registry, "time", _FakeTime(lambda sleeps: _release_other(fake_db) if sleeps == 2 else None)
        )

        run_seeds(fake_db, jobs=_jobs(calls, "a"))

        assert calls == ["a"]
        assert tracking.seed_run_marker(fake_db)["run_id"] != "last-boot"

    @pytest.mark.parametrize(
        ("fingerprint", "failed"),
        [("another-image", []), (None, ["core_data"])],
        ids=["other-seed-inputs", "other-run-had-a-failed-job"],
    )
    def test_a_run_that_does_not_stand_for_this_one_is_repeated(
        self, fake_db, monkeypatch, fingerprint, failed
    ) -> None:
        calls: list[str] = []
        _hold_lock(fake_db)

        def other_replica_finishes(sleeps: int) -> None:
            if sleeps == 1:
                tracking.record_seed_run(
                    fake_db,
                    run_id="run-other",
                    fingerprint=fingerprint or seed_fingerprint(["a"]),
                    failed_jobs=failed,
                )
                _release_other(fake_db)

        monkeypatch.setattr(registry, "time", _FakeTime(other_replica_finishes))

        run_seeds(fake_db, jobs=_jobs(calls, "a"))

        assert calls == ["a"]

    def test_the_wait_is_bounded_and_fails_startup_loudly(self, fake_db, monkeypatch) -> None:
        calls: list[str] = []
        _hold_lock(fake_db)
        clock = _FakeTime()
        monkeypatch.setattr(registry, "time", clock)

        with pytest.raises(SeedBarrierTimeoutError):
            run_seeds(fake_db, jobs=_jobs(calls, "a"))

        assert calls == []
        assert clock.now >= registry.BARRIER_TIMEOUT_SECONDS
        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY)["owner"] == "other-replica"

    def test_a_crashed_holder_s_stale_lock_is_taken_over_and_the_seeds_run(self, fake_db, fake_time) -> None:
        calls: list[str] = []
        _hold_lock(fake_db, "crashed-replica", age_seconds=tracking.LOCK_TTL_SECONDS + 60)

        run_seeds(fake_db, jobs=_jobs(calls, "a", "b"))

        assert calls == ["a", "b"]
        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is None


class TestHolding:
    def test_the_lock_is_renewed_after_every_job(self, fake_db, fake_time) -> None:
        seen: list[str] = []

        def look(_db) -> None:
            seen.append(fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY)["_rev"])

        run_seeds(fake_db, jobs=[SeedJob("a", look), SeedJob("b", look), SeedJob("c", look)])

        assert len(set(seen)) == 3, "each job saw a lock revision renewed after the previous job"

    def test_a_lock_taken_over_between_jobs_stops_the_run(self, fake_db, fake_time) -> None:
        calls: list[str] = []

        def taken_over(_db) -> None:
            calls.append("a")
            col = fake_db.collection(SCHEMA_MIGRATIONS)
            col.replace({**col.get(tracking.LOCK_KEY), "owner": "new-holder"})

        with pytest.raises(SeedLockLostError):
            run_seeds(fake_db, jobs=[SeedJob("a", taken_over), SeedJob("b", lambda _db: calls.append("b"))])

        assert calls == ["a"]
        assert fake_db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY)["owner"] == "new-holder"
        assert tracking.seed_run_marker(fake_db) is None


class TestTrackingStaysAMigrationRecord:
    def test_the_seed_run_marker_is_not_an_applied_version(self, fake_db) -> None:
        tracking.record_seed_run(fake_db, run_id="r", fingerprint="f", failed_jobs=[])

        assert tracking.applied_versions(fake_db) == set()
        assert tracking.history(fake_db) == []

    def test_refresh_lock_renews_only_the_holder_s_lock(self, fake_db) -> None:
        owner = tracking.acquire_lock(fake_db)
        col = fake_db.collection(SCHEMA_MIGRATIONS)
        col.replace({**col.get(tracking.LOCK_KEY), "acquired_at": "2000-01-01T00:00:00+00:00"})

        assert tracking.refresh_lock(fake_db, owner) is True
        assert col.get(tracking.LOCK_KEY)["acquired_at"] > "2026"
        assert tracking.refresh_lock(fake_db, "not-the-owner") is False
        tracking.release_lock(fake_db, owner)
        assert tracking.refresh_lock(fake_db, owner) is False


class TestFingerprint:
    def _tree(self, tmp_path: Path) -> Path:
        (tmp_path / "seeds").mkdir()
        (tmp_path / "seed_data").mkdir()
        (tmp_path / "seed_x.py").write_text("LOADER = 1\n")
        (tmp_path / "seeds" / "registry.py").write_text("JOBS = []\n")
        (tmp_path / "seed_data" / "x.yaml").write_text("rows: [1]\n")
        return tmp_path

    def test_same_inputs_same_fingerprint(self, tmp_path: Path) -> None:
        root = self._tree(tmp_path)
        assert seed_fingerprint(["a"], root) == seed_fingerprint(["a"], root)

    @pytest.mark.parametrize(
        "change",
        [
            lambda root: (root / "seed_data" / "x.yaml").write_text("rows: [1, 2]\n"),
            lambda root: (root / "seed_x.py").write_text("LOADER = 2\n"),
            lambda root: (root / "seeds" / "registry.py").write_text("JOBS = [1]\n"),
        ],
        ids=["seed-data", "loader", "registry"],
    )
    def test_a_changed_seed_input_changes_the_fingerprint(self, tmp_path: Path, change) -> None:
        root = self._tree(tmp_path)
        before = seed_fingerprint(["a"], root)
        change(root)
        assert seed_fingerprint(["a"], root) != before

    def test_the_job_list_is_part_of_the_fingerprint(self, tmp_path: Path) -> None:
        root = self._tree(tmp_path)
        assert seed_fingerprint(["a"], root) != seed_fingerprint(["a", "light_mode"], root)
