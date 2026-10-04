"""Remove pre-#2076 Home Assistant readings of deleted sensors (#2077). Operator-run, never scheduled.

Until #2076 the Home Assistant poll stored every reading under ``tenant_key = ''``;
no tenant or sensor erasure matches that key, so the rows of a sensor that was
deleted since still sit in ``sensor_readings`` and in the hourly/daily aggregates.
This command measures them, and deletes the ones whose sensor document no longer
exists. Rows of sensors that still exist are counted and never touched.

Usage (inside the backend container / with the backend settings in the environment)::

    python -m app.migrations.purge_orphan_ha_readings                                # dry run: counts only
    python -m app.migrations.purge_orphan_ha_readings --confirm-delete-orphans <N>

The second form deletes; N is the orphan row count the dry run printed.

Exit codes: 0 done / dry run / nothing to do / not applicable, 1 an infrastructure
error (nothing deleted that the output does not say), 2 usage, 4 the confirmation
did not match the count now measured (nothing deleted).
"""

from __future__ import annotations

import argparse
import sys

import structlog

from app.domain.interfaces.legacy_reading_store import ILegacyReadingStore
from app.domain.services.legacy_reading_cleanup import (
    CleanupResult,
    CleanupStatus,
    LegacyReadingCleanup,
    LegacyReadingReport,
    SensorDirectory,
)

logger = structlog.get_logger(__name__)

EXIT_ERROR = 1
EXIT_REFUSED = 4
EXIT_UNAVAILABLE = EXIT_ERROR

EXIT_CODES: dict[CleanupStatus, int] = {
    CleanupStatus.NOT_APPLICABLE: 0,
    CleanupStatus.UNAVAILABLE: EXIT_UNAVAILABLE,
    CleanupStatus.DRY_RUN: 0,
    CleanupStatus.NOTHING_TO_DO: 0,
    CleanupStatus.REFUSED: EXIT_REFUSED,
    CleanupStatus.DELETED: 0,
}


class _ArangoSensorDirectory:
    """Existence and owner derivability of a sensor, read from ArangoDB."""

    def __init__(self) -> None:
        from app.common.dependencies import get_observation_service, get_sensor_repo

        self._sensor_repo = get_sensor_repo()
        self._observation_service = get_observation_service()

    def exists(self, sensor_key: str) -> bool:
        return self._sensor_repo.get(sensor_key) is not None

    def owner_is_derivable(self, sensor_key: str) -> bool:
        return self._observation_service.owning_tenant_key(sensor_key) is not None


def _build() -> tuple[ILegacyReadingStore | None, SensorDirectory]:
    """The store (``None`` without TimescaleDB: light mode) and the sensor directory."""
    from app.common.dependencies import get_timescale_connection

    connection = get_timescale_connection()
    if connection is None:
        return None, _NoSensors()
    from app.data_access.timescale.legacy_reading_store import TimescaleLegacyReadingStore

    return TimescaleLegacyReadingStore(connection.pool), _ArangoSensorDirectory()


class _NoSensors:
    def exists(self, sensor_key: str) -> bool:
        return True  # never asked: without a store there is nothing to classify

    def owner_is_derivable(self, sensor_key: str) -> bool:
        return False


def _print_report(label: str, report: LegacyReadingReport) -> None:
    print(f"{label}")
    for name, group in (
        ("orphan (sensor deleted)", report.orphan),
        ("live (sensor exists)", report.live),
        ("unattributable (key unusable)", report.unattributable),
    ):
        c = group.counts
        print(f"  {name:<32} series={group.series:<6} raw={c.raw:<9} hourly={c.hourly:<9} daily={c.daily:<9}")
    print(f"  live series whose owner is derivable from the sensor's parent: {report.live_series_with_derivable_owner}")
    print(f"  orphan rows in total (the number to confirm): {report.orphan_rows}")


def _print_result(result: CleanupResult) -> None:
    status = result.status
    if status is CleanupStatus.NOT_APPLICABLE:
        print("Not applicable: TimescaleDB is not enabled in this deployment, there is no readings store to clean.")
        return
    if status is CleanupStatus.UNAVAILABLE:
        print(
            "TimescaleDB is unreachable: nothing was measured and nothing was deleted. Check the connection settings."
        )
        return
    assert result.before is not None  # noqa: S101 — every other status carries a measurement
    _print_report("Measured:", result.before)
    if status is CleanupStatus.DRY_RUN:
        print()
        if result.before.orphan_rows:
            print("Dry run: nothing was deleted. To delete the orphan class only, run:")
            command = "python -m app.migrations.purge_orphan_ha_readings --confirm-delete-orphans"
            print(f"  {command} {result.before.orphan_rows}")
        else:
            print("Dry run: no orphan rows. Nothing to delete.")
        print("Live and unattributable rows are never deleted by this command.")
    elif status is CleanupStatus.NOTHING_TO_DO:
        print()
        print("No orphan rows: nothing was deleted.")
    elif status is CleanupStatus.REFUSED:
        print()
        print("Refused: the confirmed count differs from the orphan row count measured now. Nothing was deleted.")
        print("Re-run the dry run, check the new count, and confirm that one.")
    elif status is CleanupStatus.DELETED:
        d = result.deleted
        print()
        print(
            f"Deleted: raw={d.raw} hourly={d.hourly} daily={d.daily} "
            f"(series skipped because the sensor exists: {result.skipped_series})"
        )
        assert result.after is not None  # noqa: S101
        _print_report("Measured again:", result.after)
        if result.after.orphan_rows:
            print("Orphan rows remain (a policy refresh can re-materialise hot-window buckets): run the dry run again.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--confirm-delete-orphans",
        type=int,
        metavar="N",
        help="delete the orphan class; N must equal the orphan row count the dry run printed",
    )
    args = parser.parse_args(argv)
    if args.confirm_delete_orphans is not None and args.confirm_delete_orphans < 0:
        parser.error("--confirm-delete-orphans takes the non-negative count a dry run printed")

    from app.config.logging import setup_logging

    setup_logging()
    try:
        store, sensors = _build()
        result = LegacyReadingCleanup(store, sensors).run(confirm_delete_orphans=args.confirm_delete_orphans)
    except Exception as exc:  # noqa: BLE001 — an operator tool reports and exits non-zero
        from app.common.log_privacy import loggable_error

        logger.error("legacy_readings_cleanup_failed", error=loggable_error(exc))
        print(
            f"Failed: {type(exc).__name__}. Partial deletes are committed per window; "
            "re-run the dry run before confirming again."
        )
        return EXIT_ERROR
    _print_result(result)
    return EXIT_CODES[result.status]


if __name__ == "__main__":
    sys.exit(main())
