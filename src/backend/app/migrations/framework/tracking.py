"""Tracking-collection access and the concurrency lock (NFR-016 M-2, M-8).

Every applied migration is recorded as one document in ``schema_migrations``,
keyed by its zero-padded version.  A single reserved ``__lock__`` document serves
as the cross-replica advisory lock: its insert fails while the lock is held, so
exactly one runner wins.  A stale lock (older than :data:`LOCK_TTL_SECONDS`) may
be taken over so a crashed runner cannot wedge the startup forever.

The seed registry runs under the same lock (#2028): one replica seeds while the
others wait. A long holder keeps the lock fresh with :func:`refresh_lock`, and a
reserved ``__seed_run__`` document records the last completed seed run so a
replica that waited out another replica's run can tell that it happened.

All access goes through the python-arango collection API with bound parameters —
no user input is ever interpolated into a query string.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from arango.database import StandardDatabase
from arango.exceptions import (
    DocumentDeleteError,
    DocumentInsertError,
    DocumentReplaceError,
    DocumentRevisionError,
)

from app.common.log_privacy import loggable_error
from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework.report import MigrationLockError

if TYPE_CHECKING:
    from app.migrations.framework.base import Migration

logger = structlog.get_logger()

LOCK_KEY = "__lock__"
LOCK_TTL_SECONDS = 300  # 5 minutes — a lock older than this is treated as orphaned.

#: The last completed seed run (#2028); not a migration record.
SEED_RUN_KEY = "__seed_run__"

#: Reserved documents in ``schema_migrations`` that are not migration records.
RESERVED_KEYS: frozenset[str] = frozenset({LOCK_KEY, SEED_RUN_KEY})


def _collection(db: StandardDatabase) -> Any:
    """Return the ``schema_migrations`` collection handle."""
    return db.collection(SCHEMA_MIGRATIONS)


def _iter_records(db: StandardDatabase) -> Iterator[dict[str, Any]]:
    """Yield every tracked migration document, skipping the reserved documents."""
    for doc in _collection(db).all():
        if doc.get("_key") in RESERVED_KEYS:
            continue
        yield doc


def record(db: StandardDatabase, migration: Migration, duration_ms: float, *, status: str = "applied") -> None:
    """Persist an applied migration in ``schema_migrations`` (M-2).

    Uses ``overwrite=True`` so a re-record of the same version is idempotent.
    """
    doc = {
        "_key": migration.version,
        "version": migration.version,
        "name": migration.name,
        "checksum": migration.checksum(),
        "applied_at": datetime.now(UTC).isoformat(),
        "duration_ms": round(duration_ms, 3),
        "status": status,
    }
    _collection(db).insert(doc, overwrite=True)


def remove(db: StandardDatabase, version: str) -> None:
    """Delete the tracking record for ``version`` (used on downgrade)."""
    col = _collection(db)
    if col.has(version):
        col.delete(version)


def applied_versions(db: StandardDatabase) -> set[str]:
    """Return the set of versions already applied on this database."""
    return {doc["version"] for doc in _iter_records(db)}


def current(db: StandardDatabase) -> str | None:
    """Return the highest applied version, or ``None`` on a virgin database."""
    versions = applied_versions(db)
    return max(versions) if versions else None


def history(db: StandardDatabase) -> list[dict[str, Any]]:
    """Return all tracked migrations, ascending by version."""
    return sorted(_iter_records(db), key=lambda doc: doc["version"])


def checksum_of(db: StandardDatabase, version: str) -> str | None:
    """Return the stored checksum of an applied version, or ``None``."""
    doc = _collection(db).get(version)
    return doc.get("checksum") if doc else None


def _is_stale(lock_doc: dict[str, Any], now: datetime) -> bool:
    """True when the lock's ``acquired_at`` is older than the TTL (orphaned)."""
    raw = lock_doc.get("acquired_at")
    if not raw:
        return True
    try:
        acquired_at = datetime.fromisoformat(raw)
    except (TypeError, ValueError) as exc:
        logger.debug("migration_lock_acquired_at_unparseable", value=raw, error=loggable_error(exc))
        return True
    if acquired_at.tzinfo is None:
        acquired_at = acquired_at.replace(tzinfo=UTC)
    return (now - acquired_at).total_seconds() > LOCK_TTL_SECONDS


def acquire_lock(db: StandardDatabase) -> str:
    """Acquire the migration lock, or raise :class:`MigrationLockError` (M-8).

    Returns the caller's *owner token* — a per-runner uuid stored in the lock
    document — which MUST be passed back to :func:`release_lock` so only the
    holder can free the lock (fencing).

    A fresh lock held by another runner blocks this one.  A stale lock (older
    than the TTL) is taken over so a crashed runner cannot wedge startup — but
    the takeover is a *revision-checked* replace, so when two replicas race to
    adopt the same stale lock the loser's replace fails its `_rev` check and is
    surfaced as :class:`MigrationLockError` rather than both proceeding to
    migrate concurrently.
    """
    col = _collection(db)
    now = datetime.now(UTC)
    owner = str(uuid.uuid4())
    lock_doc = {"_key": LOCK_KEY, "owner": owner, "acquired_at": now.isoformat()}

    try:
        col.insert(lock_doc)
        return owner
    except DocumentInsertError as exc:
        existing = col.get(LOCK_KEY)
        if existing is None:
            # Released between our failed insert and this read — retry once.
            try:
                col.insert(lock_doc)
            except DocumentInsertError as retry_exc:
                raise MigrationLockError("Migration lock is held by another runner") from retry_exc
            return owner
        if _is_stale(existing, now):
            logger.warning(
                "migration_lock_taken_over",
                acquired_at=existing.get("acquired_at"),
                previous_owner=existing.get("owner"),
            )
            # Compare-and-swap on the revision we just read: if another replica
            # already replaced this stale lock, the `_rev` mismatch raises and
            # we treat the lock as held (single-runner guarantee, M-8).
            takeover = {**lock_doc, "_rev": existing.get("_rev")}
            try:
                col.replace(takeover)
            except (DocumentReplaceError, DocumentRevisionError) as replace_exc:
                raise MigrationLockError("Migration lock is held by another runner") from replace_exc
            return owner
        raise MigrationLockError("Migration lock is held by another runner") from exc


def release_lock(db: StandardDatabase, owner: str) -> None:
    """Release the migration lock iff this runner still owns it (idempotent).

    Only the holder whose ``owner`` token matches the stored one may delete the
    lock, and only while the revision is unchanged since it was read.  A lock
    that has been taken over by another replica (because this runner's migration
    outran the TTL) is left intact, and a delete/replace race is swallowed —
    never crashing the caller's ``finally: release_lock(...)``.
    """
    col = _collection(db)
    existing = col.get(LOCK_KEY)
    if existing is None:
        return  # already released
    if existing.get("owner") != owner:
        logger.warning(
            "migration_lock_not_owned_on_release",
            stored_owner=existing.get("owner"),
            our_owner=owner,
        )
        return
    try:
        col.delete({"_key": LOCK_KEY, "_rev": existing.get("_rev")})
    except (DocumentDeleteError, DocumentRevisionError) as exc:
        # Raced with a concurrent takeover between our read and delete — the
        # lock is no longer ours to free.
        logger.debug("migration_lock_release_race", error=loggable_error(exc))


def refresh_lock(db: StandardDatabase, owner: str) -> bool:
    """Renew ``acquired_at`` of a lock this runner holds; ``False`` when it no longer does.

    A holder that works longer than :data:`LOCK_TTL_SECONDS` in total (the seed
    registry, #2028) calls this between its steps, so the lock only goes stale when
    the holder stops making progress — not merely because the whole run is long. The
    renewal is a revision-checked replace like the takeover: a replica that has
    taken the lock over in the meantime (or released it) makes this return ``False``
    instead of the caller writing on as if it were still the only runner.
    """
    col = _collection(db)
    existing = col.get(LOCK_KEY)
    if existing is None or existing.get("owner") != owner:
        logger.warning(
            "migration_lock_lost",
            stored_owner=existing.get("owner") if existing else None,
            our_owner=owner,
        )
        return False
    renewed = {
        "_key": LOCK_KEY,
        "_rev": existing.get("_rev"),
        "owner": owner,
        "acquired_at": datetime.now(UTC).isoformat(),
    }
    try:
        col.replace(renewed)
    except (DocumentReplaceError, DocumentRevisionError) as exc:
        logger.warning("migration_lock_lost", our_owner=owner, error=loggable_error(exc))
        return False
    return True


def seed_run_marker(db: StandardDatabase) -> dict[str, Any] | None:
    """The record of the last completed seed run, or ``None`` before the first (#2028)."""
    doc: dict[str, Any] | None = _collection(db).get(SEED_RUN_KEY)
    return doc


def record_seed_run(db: StandardDatabase, *, run_id: str, fingerprint: str, failed_jobs: list[str]) -> None:
    """Record a completed seed run: its id, the seed-input fingerprint and the jobs that failed.

    Written by the lock holder before it releases the lock, so a replica that waited
    for the lock reads either the previous record or this one, never a half-written
    run.
    """
    _collection(db).insert(
        {
            "_key": SEED_RUN_KEY,
            "run_id": run_id,
            "fingerprint": fingerprint,
            "failed_jobs": list(failed_jobs),
            "completed_at": datetime.now(UTC).isoformat(),
        },
        overwrite=True,
    )
