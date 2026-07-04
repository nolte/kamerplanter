"""The :class:`MigrationRunner` — plan / upgrade / downgrade / inspect.

Coordinates discovery, tracking and the concurrency lock into the operations the
CLI and the startup path use.  Upgrades and downgrades run under the lock (M-8);
a failing pending migration propagates (M-4 — fatal startup); checksum drift on an
already-applied version is logged as a warning (M-7).
"""

from __future__ import annotations

import time

import structlog
from arango.database import StandardDatabase

from app.migrations.framework import tracking
from app.migrations.framework.base import Migration
from app.migrations.framework.discovery import load_migrations, normalize_version, validate_sequence
from app.migrations.framework.report import MigrationLockError, MigrationReport, NonLinearHistoryError

logger = structlog.get_logger()


class MigrationRunner:
    """Orchestrates versioned migrations against an ArangoDB database.

    ``migrations`` may be injected (primarily for tests); when omitted the runner
    discovers the ``versions/`` package.
    """

    def __init__(self, migrations: list[Migration] | None = None) -> None:
        self._migrations: list[Migration] = migrations if migrations is not None else load_migrations()
        self._migrations.sort(key=lambda m: m.version)
        validate_sequence(self._migrations)

    @property
    def migrations(self) -> list[Migration]:
        return list(self._migrations)

    def _check_linear(self, applied: set[str]) -> None:
        """Raise if an applied version follows an unapplied one (M-1)."""
        seen_pending = False
        for migration in self._migrations:
            if migration.version in applied:
                if seen_pending:
                    raise NonLinearHistoryError(
                        f"Applied version {migration.version} follows an unapplied version — "
                        "history must be strictly linear (no out-of-order apply)"
                    )
            else:
                seen_pending = True

    def _warn_checksum_drift(self, db: StandardDatabase, applied: set[str]) -> None:
        """Log a warning for any applied migration whose source changed (M-7)."""
        for migration in self._migrations:
            if migration.version not in applied:
                continue
            stored = tracking.checksum_of(db, migration.version)
            current_checksum = migration.checksum()
            if stored is not None and stored != current_checksum:
                logger.warning(
                    "migration_checksum_drift",
                    version=migration.version,
                    name=migration.name,
                    stored_checksum=stored,
                    current_checksum=current_checksum,
                )

    def plan(self, db: StandardDatabase) -> list[Migration]:
        """Return the ordered pending migrations, validating linear history (M-1)."""
        applied = tracking.applied_versions(db)
        self._check_linear(applied)
        return [m for m in self._migrations if m.version not in applied]

    def upgrade(
        self,
        db: StandardDatabase,
        target: str | None = None,
        *,
        dry_run: bool = False,
    ) -> list[MigrationReport]:
        """Apply all pending migrations (optionally up to ``target``) under the lock."""
        normalized_target = normalize_version(target) if target is not None else None

        tracking.acquire_lock(db)
        try:
            applied = tracking.applied_versions(db)
            self._check_linear(applied)
            self._warn_checksum_drift(db, applied)

            pending = [m for m in self._migrations if m.version not in applied]
            if normalized_target is not None:
                pending = [m for m in pending if m.version <= normalized_target]

            reports: list[MigrationReport] = []
            for migration in pending:
                start = time.perf_counter()
                report = migration.up(db, dry_run=dry_run)
                duration_ms = (time.perf_counter() - start) * 1000.0
                report.duration_ms = round(duration_ms, 3)
                if not dry_run:
                    tracking.record(db, migration, duration_ms)
                logger.info(
                    "migration_applied",
                    version=migration.version,
                    name=migration.name,
                    scanned=report.scanned,
                    changed=report.changed,
                    duration_ms=report.duration_ms,
                    dry_run=dry_run,
                )
                reports.append(report)
            return reports
        finally:
            tracking.release_lock(db)

    def downgrade(
        self,
        db: StandardDatabase,
        target: str,
        *,
        dry_run: bool = False,
    ) -> list[MigrationReport]:
        """Roll back applied migrations above ``target``, newest first, under the lock."""
        normalized_target = normalize_version(target)

        tracking.acquire_lock(db)
        try:
            applied = tracking.applied_versions(db)
            to_rollback = sorted(
                (m for m in self._migrations if m.version in applied and m.version > normalized_target),
                key=lambda m: m.version,
                reverse=True,
            )

            reports: list[MigrationReport] = []
            for migration in to_rollback:
                start = time.perf_counter()
                report = migration.down(db, dry_run=dry_run)
                duration_ms = (time.perf_counter() - start) * 1000.0
                report.duration_ms = round(duration_ms, 3)
                if not dry_run:
                    tracking.remove(db, migration.version)
                logger.info(
                    "migration_reverted",
                    version=migration.version,
                    name=migration.name,
                    duration_ms=report.duration_ms,
                    dry_run=dry_run,
                )
                reports.append(report)
            return reports
        finally:
            tracking.release_lock(db)

    def current(self, db: StandardDatabase) -> str | None:
        """Return the highest applied version, or ``None``."""
        return tracking.current(db)

    def history(self, db: StandardDatabase) -> list[dict]:
        """Return the ordered tracked history."""
        return tracking.history(db)


def run_pending_migrations(db: StandardDatabase) -> list[MigrationReport]:
    """Startup entrypoint: apply every pending migration — FATAL on failure (M-4).

    A held lock (a concurrent replica already migrating) is NOT fatal: this runner
    skips gracefully and the winning runner applies the pending set exactly once
    (M-8).  Any other exception propagates and aborts the startup (M-4).
    """
    runner = MigrationRunner()
    try:
        return runner.upgrade(db)
    except MigrationLockError:
        logger.info("migrations_locked_by_other_runner_skipping")
        return []
