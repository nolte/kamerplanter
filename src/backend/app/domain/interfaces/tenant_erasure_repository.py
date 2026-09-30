"""Persistence of the tenant-deletion proof and its retry state (#1769)."""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.tenant_erasure import TenantErasureRecord


class ITenantErasureRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> TenantErasureRecord | None: ...

    @abstractmethod
    def create_with_key(self, record: TenantErasureRecord, key: str) -> TenantErasureRecord:
        """Insert under a deterministic key; a second insert raises ``DuplicateError`` / ``WriteConflictError``.

        One record per tenant, so two deletions of one tenant collide.
        """

    @abstractmethod
    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> TenantErasureRecord | None:
        """Atomically mark an open record ``in_progress``; ``None`` when another run holds it or it is complete."""

    @abstractmethod
    def delete_unclaimed(self, key: str) -> bool:
        """Remove the account-erasure record *key* if no run ever claimed it; ``True`` when it was removed.

        The withdrawal of a deletion that was opened and then decided against
        before it started (REQ-025 AK-IE-07). Conditional in one statement: a
        record a run has claimed (``last_attempt_at`` set) or finished, and one
        another origin (a person's ``delete_tenant``) opened, is never removed — it is the proof of a deletion that ran.
        """
        ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantErasureRecord: ...

    @abstractmethod
    def list_due(self, *, stale_before_iso: str) -> list[TenantErasureRecord]:
        """Open records a retry run should look at: ``partially_completed``, or ``in_progress`` gone stale."""
