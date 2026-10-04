"""#2077 — the operator-run cleanup of pre-#2076 Home Assistant readings stored under ``tenant_key = ''``.

The cleanup classifies every legacy series by its sensor (deleted / still there /
cannot be judged) and may delete only the series of **deleted** sensors, only after
the operator passes back the count a dry run printed. These tests pin the
decisions with injected doubles; the integration test measures the same against a
real TimescaleDB and ArangoDB.
"""

from __future__ import annotations

import pytest

from app.domain.interfaces.legacy_reading_store import ILegacyReadingStore, LegacySeriesCounts
from app.domain.services.legacy_reading_cleanup import CleanupStatus, LegacyReadingCleanup


class FakeStore(ILegacyReadingStore):
    """An in-memory legacy store; ``series`` maps sensor key to its row counts per table."""

    def __init__(self, series: dict[str, LegacySeriesCounts], *, available: bool = True) -> None:
        self.series = dict(series)
        self.available = available
        self.purged: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def legacy_series(self) -> dict[str, LegacySeriesCounts]:
        return dict(self.series)

    def purge_legacy_series(self, sensor_key: str) -> LegacySeriesCounts:
        self.purged.append(sensor_key)
        return self.series.pop(sensor_key, LegacySeriesCounts())


class FakeSensors:
    """The sensor directory: which keys still exist, and which of those have a derivable owner."""

    def __init__(self, live: set[str], derivable: set[str] | None = None) -> None:
        self.live = set(live)
        self.derivable = set(derivable or ())

    def exists(self, sensor_key: str) -> bool:
        return sensor_key in self.live

    def owner_is_derivable(self, sensor_key: str) -> bool:
        return sensor_key in self.derivable


def _world() -> tuple[FakeStore, FakeSensors]:
    store = FakeStore(
        {
            "gone-1": LegacySeriesCounts(raw=10, hourly=4, daily=1),
            "gone-2": LegacySeriesCounts(raw=0, hourly=6, daily=2),
            "live-1": LegacySeriesCounts(raw=50, hourly=9, daily=3),
            "live-2": LegacySeriesCounts(raw=7, hourly=0, daily=0),
            "": LegacySeriesCounts(raw=2),
            "bad key/with slash": LegacySeriesCounts(hourly=1),
        }
    )
    return store, FakeSensors(live={"live-1", "live-2"}, derivable={"live-1"})


def test_a_dry_run_classifies_per_class_and_per_table_and_writes_nothing() -> None:
    store, sensors = _world()

    result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=None)

    assert result.status is CleanupStatus.DRY_RUN
    before = result.before
    assert before is not None
    assert (before.orphan.series, before.orphan.counts) == (2, LegacySeriesCounts(raw=10, hourly=10, daily=3))
    assert (before.live.series, before.live.counts) == (2, LegacySeriesCounts(raw=57, hourly=9, daily=3))
    assert (before.unattributable.series, before.unattributable.counts) == (2, LegacySeriesCounts(raw=2, hourly=1))
    assert before.live_series_with_derivable_owner == 1
    assert before.orphan_rows == 23
    assert store.purged == []
    assert result.deleted == LegacySeriesCounts()


def test_a_confirmation_that_differs_from_the_dry_run_count_deletes_nothing() -> None:
    store, sensors = _world()

    for wrong in (0, 22, 24, 10_000):
        result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=wrong)
        assert result.status is CleanupStatus.REFUSED

    assert store.purged == []


def test_the_right_confirmation_deletes_only_the_orphan_series() -> None:
    store, sensors = _world()

    result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=23)

    assert result.status is CleanupStatus.DELETED
    assert sorted(store.purged) == ["gone-1", "gone-2"]
    assert result.deleted == LegacySeriesCounts(raw=10, hourly=10, daily=3)
    assert set(store.series) == {"live-1", "live-2", "", "bad key/with slash"}
    assert result.after is not None
    assert result.after.orphan_rows == 0
    assert result.after.live.counts == LegacySeriesCounts(raw=57, hourly=9, daily=3)


def test_a_rerun_is_idempotent() -> None:
    store, sensors = _world()
    LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=23)
    purged_after_first = list(store.purged)

    result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=23)

    assert result.status is CleanupStatus.NOTHING_TO_DO
    assert store.purged == purged_after_first


def test_a_sensor_that_exists_again_at_delete_time_is_not_deleted() -> None:
    store, sensors = _world()

    class Reappearing(FakeSensors):
        """``exists`` answers False for the classification and True for the pre-delete re-check."""

        def __init__(self) -> None:
            super().__init__(live={"live-1", "live-2"})
            self.asked: dict[str, int] = {}

        def exists(self, sensor_key: str) -> bool:
            self.asked[sensor_key] = self.asked.get(sensor_key, 0) + 1
            if sensor_key == "gone-1" and self.asked[sensor_key] >= 2:
                return True
            return super().exists(sensor_key)

    result = LegacyReadingCleanup(store, Reappearing()).run(confirm_delete_orphans=23)

    assert "gone-1" not in store.purged
    assert result.skipped_series == 1


def test_a_live_sensor_is_never_purged_whatever_the_confirmation() -> None:
    store = FakeStore({"live-1": LegacySeriesCounts(raw=5, hourly=2, daily=1)})
    sensors = FakeSensors(live={"live-1"}, derivable={"live-1"})

    for confirm in (None, 0, 8):
        result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=confirm)
        assert result.status in {CleanupStatus.DRY_RUN, CleanupStatus.NOTHING_TO_DO}

    assert store.purged == []
    assert "live-1" in store.series


def test_an_unattributable_series_is_counted_and_never_deleted() -> None:
    store = FakeStore({"": LegacySeriesCounts(raw=3), "a b": LegacySeriesCounts(daily=2)})

    result = LegacyReadingCleanup(store, FakeSensors(live=set())).run(confirm_delete_orphans=0)

    assert result.status is CleanupStatus.NOTHING_TO_DO
    assert store.purged == []
    assert result.before is not None
    assert result.before.unattributable.series == 2


def test_a_missing_store_is_not_applicable() -> None:
    """Light mode / no TimescaleDB: the null repository is in place and there is nothing to measure."""
    result = LegacyReadingCleanup(None, FakeSensors(live=set())).run(confirm_delete_orphans=5)

    assert result.status is CleanupStatus.NOT_APPLICABLE
    assert result.before is None


def test_an_outage_touches_nothing_and_says_so() -> None:
    store = FakeStore({"gone": LegacySeriesCounts(raw=1)}, available=False)

    result = LegacyReadingCleanup(store, FakeSensors(live=set())).run(confirm_delete_orphans=1)

    assert result.status is CleanupStatus.UNAVAILABLE
    assert store.purged == []


def test_a_directory_failure_aborts_before_any_deletion() -> None:
    store, _ = _world()

    class Broken(FakeSensors):
        def exists(self, sensor_key: str) -> bool:
            msg = "arango down"
            raise ConnectionError(msg)

    with pytest.raises(ConnectionError):
        LegacyReadingCleanup(store, Broken(live=set())).run(confirm_delete_orphans=23)

    assert store.purged == []


def test_the_report_names_no_sensor_key() -> None:
    store, sensors = _world()

    result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=None)

    rendered = repr(result) + str(result.before)
    assert "gone-1" not in rendered
    assert "live-1" not in rendered
