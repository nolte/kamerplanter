"""Operator-run cleanup of Home Assistant readings stored under ``tenant_key = ''`` (#2077).

Until #2076 the poll stamped every reading with an empty tenant key (a sensor
document carries none), so ``delete_by_tenant`` and ``delete_by_sensor`` — which
match on the key — never reached the rows. #2076 stopped new ones; this removes
the old ones whose sensor is gone, and **only** those:

* **orphan** — the sensor document does not exist. Nothing can claim the series;
  it is the personal-data residue of an erasure that could not reach it.
* **live** — the sensor exists. The series is somebody's data. It is counted (and,
  as a count only, whether its owner is derivable from the sensor's parent) and
  never touched.
* **unattributable** — the sensor key is empty or cannot be a key at all, so the
  series cannot be judged. Counted, never touched.

Deletion needs the operator to pass back the orphan row count a dry run printed.
A count that moved since (rows arrived, an earlier run partly finished, a sensor
was created) refuses: the operator looks again. Nothing here is scheduled.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Protocol

import structlog

from app.domain.interfaces.legacy_reading_store import ILegacyReadingStore, LegacySeriesCounts

logger = structlog.get_logger(__name__)

#: What an ArangoDB document key can be (the characters the server allows, at most 254 bytes).
#: A key outside it cannot name a sensor document, so its existence cannot be asked.
_ARANGO_KEY = re.compile(r"[A-Za-z0-9_\-:.@()+,=;$!*'%]{1,254}")


class SensorDirectory(Protocol):
    """What the classification asks about a sensor key."""

    def exists(self, sensor_key: str) -> bool: ...

    def owner_is_derivable(self, sensor_key: str) -> bool: ...


class CleanupStatus(enum.StrEnum):
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"
    DRY_RUN = "dry_run"
    NOTHING_TO_DO = "nothing_to_do"
    REFUSED = "refused"
    DELETED = "deleted"


@dataclass(frozen=True)
class ClassCounts:
    series: int = 0
    counts: LegacySeriesCounts = field(default_factory=LegacySeriesCounts)


@dataclass(frozen=True)
class LegacyReadingReport:
    """Counts only. The orphan keys are carried for the deletion and kept out of ``repr``."""

    orphan: ClassCounts
    live: ClassCounts
    unattributable: ClassCounts
    live_series_with_derivable_owner: int
    orphan_keys: tuple[str, ...] = field(default=(), repr=False, compare=False)

    @property
    def orphan_rows(self) -> int:
        return self.orphan.counts.total


@dataclass(frozen=True)
class CleanupResult:
    status: CleanupStatus
    before: LegacyReadingReport | None = None
    after: LegacyReadingReport | None = None
    deleted: LegacySeriesCounts = field(default_factory=LegacySeriesCounts)
    #: Orphans that turned out to exist when asked again right before their delete.
    skipped_series: int = 0


class LegacyReadingCleanup:
    def __init__(self, store: ILegacyReadingStore | None, sensors: SensorDirectory) -> None:
        self._store = store
        self._sensors = sensors

    def report(self) -> LegacyReadingReport:
        assert self._store is not None  # noqa: S101 — callers check applicability first
        orphan = live = unattributable = ClassCounts()
        orphan_keys: list[str] = []
        derivable = 0
        for sensor_key, counts in sorted(self._store.legacy_series().items()):
            if not _ARANGO_KEY.fullmatch(sensor_key):
                unattributable = _plus(unattributable, counts)
            elif self._sensors.exists(sensor_key):
                live = _plus(live, counts)
                derivable += 1 if self._sensors.owner_is_derivable(sensor_key) else 0
            else:
                orphan = _plus(orphan, counts)
                orphan_keys.append(sensor_key)
        return LegacyReadingReport(orphan, live, unattributable, derivable, tuple(orphan_keys))

    def run(self, *, confirm_delete_orphans: int | None) -> CleanupResult:
        """Measure, and delete the orphan class only when ``confirm_delete_orphans`` equals what was measured."""
        if self._store is None:
            return CleanupResult(CleanupStatus.NOT_APPLICABLE)
        if not self._store.is_available():
            return CleanupResult(CleanupStatus.UNAVAILABLE)
        before = self.report()
        if confirm_delete_orphans is None:
            return CleanupResult(CleanupStatus.DRY_RUN, before=before)
        if before.orphan_rows == 0:
            return CleanupResult(CleanupStatus.NOTHING_TO_DO, before=before, after=before)
        if confirm_delete_orphans != before.orphan_rows:
            return CleanupResult(CleanupStatus.REFUSED, before=before)

        deleted = LegacySeriesCounts()
        skipped = 0
        for sensor_key in before.orphan_keys:
            if self._sensors.exists(sensor_key):  # asked again: a delete is the one step that cannot be undone
                skipped += 1
                continue
            removed = self._store.purge_legacy_series(sensor_key)
            deleted += removed
            logger.info(
                "legacy_readings_series_purged",
                raw=removed.raw,
                hourly=removed.hourly,
                daily=removed.daily,
            )
        after = self.report()
        logger.info(
            "legacy_readings_cleanup_done",
            raw=deleted.raw,
            hourly=deleted.hourly,
            daily=deleted.daily,
            skipped_series=skipped,
            orphan_rows_left=after.orphan_rows,
        )
        return CleanupResult(CleanupStatus.DELETED, before=before, after=after, deleted=deleted, skipped_series=skipped)


def _plus(total: ClassCounts, counts: LegacySeriesCounts) -> ClassCounts:
    return ClassCounts(total.series + 1, total.counts + counts)
