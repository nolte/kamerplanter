"""#1834 — reconcile the object store against the attachment catalogue.

Every deletion path decides about a stored object by asking the ``attachments``
catalogue. Nothing walked the object store itself, so an object whose last record
was gone without its bytes (a storage call that failed after the record was
removed, a record created inside an erasure's window, a pest reference uploaded
in a tenant the user later left) stayed for good: outside the quota, which counts
records, and outside every Art. 17 erasure.

This service walks ``t/`` through the adapter interface — paged, resumable, never
the whole key list in memory — and for every object no record holds:

* counts it (``found``);
* skips it while it is younger than the safety floor (an upload writes the object
  *before* its record, so a fresh unheld object is legitimate in flight);
* in report-only mode counts it as ``would_delete``; with deletion enabled removes
  it after re-asking the catalogue once more.

The catalogue question is fail-closed: a database error aborts the run rather than
reading as "nothing holds this". A catalogue that answers *empty* is caught by a
brake instead: a page in which more than ``max_orphan_fraction`` of the objects are
unheld is reported (``brake_tripped``) and never deleted from.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.common.exceptions import NotFoundError
from app.domain.engines.storage.reconciliation_keys import TENANT_NAMESPACE, holder_candidates, is_reconcilable
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter

logger = structlog.get_logger()

#: A page smaller than this is not judged by its orphan share: a small store may
#: legitimately be mostly orphans, and the brake exists for the installation-wide
#: "the catalogue is empty" signature, which fills every page.
_BRAKE_MIN_PAGE_OBJECTS = 20


class IReconciliationCursorStore(Protocol):
    """Where a truncated run leaves the listing token for the next one."""

    def get(self) -> str | None: ...

    def set(self, token: str) -> None: ...

    def clear(self) -> None: ...


@dataclass
class ReconciliationReport:
    """Counts of one run. Carries no key, tenant or user identifier by design."""

    delete_enabled: bool
    min_age_hours: float
    scanned: int = 0
    found: int = 0
    young: int = 0
    undated: int = 0
    eligible: int = 0
    deleted: int = 0
    failed: int = 0
    freed_bytes: int = 0
    truncated: bool = False
    brake_tripped: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scanned": self.scanned,
            "found": self.found,
            "young": self.young,
            "undated": self.undated,
            "eligible": self.eligible,
            # Report-only (the shipped default): what a deleting run would remove.
            "would_delete": 0 if self.delete_enabled else self.eligible,
            "deleted": self.deleted,
            "failed": self.failed,
            "freed_bytes": self.freed_bytes,
            "truncated": self.truncated,
            "brake_tripped": self.brake_tripped,
            "delete_enabled": self.delete_enabled,
            "report_only": not self.delete_enabled,
            "min_age_hours": self.min_age_hours,
        }


def _parse_modified(value: str | None) -> datetime | None:
    """The adapters report ``last_modified`` as an epoch float (local-fs) or ISO-8601 (S3)."""
    if not value:
        return None
    try:
        return datetime.fromtimestamp(float(value), UTC)
    except ValueError, OverflowError, OSError:
        # ``inf`` / absurd epochs: unreadable, so the object is kept as undated rather
        # than aborting the run on the same page every night.
        pass
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class StorageReconciliationService:
    """Find, and optionally delete, stored objects no attachment record holds."""

    def __init__(
        self,
        *,
        storage: IObjectStorageAdapter,
        attachment_repo: IAttachmentRepository,
        min_age: timedelta,
        delete_enabled: bool,
        max_objects_per_run: int,
        max_orphan_fraction: float = 0.5,
        cursor_store: IReconciliationCursorStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._storage = storage
        self._repo = attachment_repo
        self._min_age = min_age
        self._delete_enabled = delete_enabled
        self._max_objects = max_objects_per_run
        self._max_orphan_fraction = max_orphan_fraction
        self._cursor = cursor_store
        self._clock = clock or (lambda: datetime.now(UTC))

    async def run(self) -> ReconciliationReport:
        report = ReconciliationReport(
            delete_enabled=self._delete_enabled, min_age_hours=self._min_age.total_seconds() / 3600
        )
        cutoff = self._clock() - self._min_age
        token = self._cursor.get() if self._cursor is not None else None
        resumed = token is not None
        while True:
            try:
                page = await self._storage.list_objects(TENANT_NAMESPACE, token)
            except Exception:
                if resumed and self._cursor is not None:
                    # A stale or foreign token (the backend changed since it was
                    # stored) must not fail every night: the retry starts over.
                    self._cursor.clear()
                raise
            resumed = False
            raw_keys: list[str] = page.get("keys", [])
            report.scanned += len(raw_keys)
            keys = [key for key in raw_keys if is_reconcilable(key)]
            await self._judge_page(keys, cutoff, report)
            token = page.get("next_page_token")
            if token is None:
                if self._cursor is not None:
                    self._cursor.clear()
                return report
            if report.scanned >= self._max_objects:
                report.truncated = True
                if self._cursor is not None:
                    self._cursor.set(token)
                return report

    async def _judge_page(self, keys: list[str], cutoff: datetime, report: ReconciliationReport) -> None:
        if not keys:
            return
        # One catalogue query per page, not per object. A failure here propagates:
        # an unanswered question must never read as "nothing holds it".
        held = self._repo.held_storage_keys(sorted({c for key in keys for c in holder_candidates(key)}))
        unheld = [key for key in keys if not (holder_candidates(key) & held)]
        # A catalogue that answers, but answers *empty* — a wrong database over this
        # bucket, a restore older than the store, two installations on one bucket —
        # makes every object look unheld, and no failed query signals it. A page whose
        # unheld share is implausible is counted but never deleted from.
        page_braked = (
            self._delete_enabled
            and len(keys) >= _BRAKE_MIN_PAGE_OBJECTS
            and len(unheld) / len(keys) > self._max_orphan_fraction
        )
        if page_braked:
            report.brake_tripped = True
        for key in unheld:
            report.found += 1
            try:
                meta = await self._storage.head_object(key)
            except NotFoundError:
                report.found -= 1  # deleted since the listing — nothing to judge
                continue
            except Exception as exc:  # noqa: BLE001 — one unreadable object must not stop the walk
                report.failed += 1
                logger.warning("storage_reconcile_head_failed", error_type=type(exc).__name__)
                continue
            modified = _parse_modified(meta.last_modified)
            if modified is None:
                # No readable age: the floor cannot judge it, so it is kept (#1806 class).
                report.undated += 1
                continue
            if modified > cutoff:
                report.young += 1
                continue
            report.eligible += 1
            if not self._delete_enabled or page_braked:
                continue
            try:
                # Asked again right before the delete: a record may have appeared
                # since the page was judged.
                if holder_candidates(key) & self._repo.held_storage_keys(sorted(holder_candidates(key))):
                    report.eligible -= 1
                    continue
                await self._storage.delete_object(key)
            except Exception as exc:  # noqa: BLE001 — keep the batch draining
                report.failed += 1
                # The exception type only: a filesystem or S3 error text embeds the object
                # path, which embeds the tenant (and the log has no retention rule).
                logger.warning("storage_reconcile_delete_failed", error_type=type(exc).__name__)
                continue
            report.deleted += 1
            report.freed_bytes += meta.size_bytes
