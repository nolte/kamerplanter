"""Tracking-collection access and the concurrency lock (NFR-016 M-2, M-8).

Every applied migration is recorded as one document in ``schema_migrations``,
keyed by its zero-padded version.  A single reserved ``__lock__`` document serves
as the cross-replica advisory lock: its insert fails while the lock is held, so
exactly one runner wins.  A stale lock (older than :data:`LOCK_TTL_SECONDS`) may
be taken over so a crashed runner cannot wedge the startup forever.

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

from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework.report import MigrationLockError

if TYPE_CHECKING:
    from app.migrations.framework.base import Migration

logger = structlog.get_logger()

LOCK_KEY = "__lock__"
LOCK_TTL_SECONDS = 300  # 5 minutes — a lock older than this is treated as orphaned.


def _collection(db: StandardDatabase) -> Any:
    """Return the ``schema_migrations`` collection handle."""
    return db.collection(SCHEMA_MIGRATIONS)


def _iter_records(db: StandardDatabase) -> Iterator[dict[str, Any]]:
    """Yield every tracked migration document, skipping the lock sentinel."""
    for doc in _collection(db).all():
        if doc.get("_key") == LOCK_KEY:
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
        logger.debug("migration_lock_acquired_at_unparseable", value=raw, error=str(exc))
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
        logger.debug("migration_lock_release_race", error=str(exc))
