"""NFR-016 S-2/S-4 — seed registry fatal propagation and error isolation."""

from __future__ import annotations

import pytest

from app.migrations.seeds.registry import SeedJob, run_seeds


class TestSeedRegistry:
    def test_non_fatal_failure_is_isolated(self):
        calls: list[str] = []

        def _fail(_db):
            calls.append("failing")
            raise RuntimeError("boom")

        def _ok(_db):
            calls.append("ok")

        jobs = [SeedJob("failing", _fail, fatal=False), SeedJob("ok", _ok, fatal=False)]

        # Must not raise: a bad reference-data seed is isolated and the next runs.
        run_seeds(object(), jobs=jobs)

        assert calls == ["failing", "ok"]

    def test_fatal_failure_propagates(self):
        def _fail(_db):
            raise RuntimeError("structural seed failed")

        jobs = [SeedJob("structural", _fail, fatal=True)]

        with pytest.raises(RuntimeError):
            run_seeds(object(), jobs=jobs)

    def test_fatal_failure_stops_before_later_jobs(self):
        calls: list[str] = []

        def _fail(_db):
            calls.append("structural")
            raise RuntimeError("stop")

        def _later(_db):
            calls.append("later")

        jobs = [SeedJob("structural", _fail, fatal=True), SeedJob("later", _later, fatal=False)]

        with pytest.raises(RuntimeError):
            run_seeds(object(), jobs=jobs)

        assert calls == ["structural"]

    def test_all_success_runs_every_job(self):
        calls: list[str] = []
        jobs = [
            SeedJob("a", lambda _db: calls.append("a")),
            SeedJob("b", lambda _db: calls.append("b")),
            SeedJob("c", lambda _db: calls.append("c")),
        ]

        run_seeds(object(), jobs=jobs)

        assert calls == ["a", "b", "c"]

    def test_default_registry_builds_with_location_types_fatal(self):
        # The default registry is well-formed and marks location_types fatal.
        from app.migrations.seeds.registry import _build_jobs

        jobs = _build_jobs()
        by_name = {job.name: job for job in jobs}

        assert by_name["location_types"].fatal is True
        assert by_name["core_data"].fatal is False
        # The lifecycle reconcile is the last data step (post-seed).
        assert jobs[-1].name == "lifecycle_to_phase_sequence_reconcile"
        # The overwintering seed (REQ-022, #371) is registered between
        # plant_info_extended and fertilizers, matching the pre-framework order.
        assert "overwintering_profiles" in by_name
