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
    def heartbeat(
        self, key: str, *, claimed_at_iso: str, now_iso: str, parent_keys: dict[str, list[str]] | None = None
    ) -> bool:
        """Refresh the claim a run holds, atomically; ``False`` when the claim is no longer that run's.

        *claimed_at_iso* is the ``last_attempt_at`` the run's own claim wrote. The
        refresh applies only while the record is still ``in_progress`` under that
        claim — a second worker that claimed it after the heartbeat lapsed
        overwrote ``last_attempt_at``, and the first run's next heartbeat must see
        that instead of extending the other run's claim (#1792). *parent_keys*,
        when given, replaces the persisted parent keys in the same write.
        """

    @abstractmethod
    def update_fields_while_claimed(
        self, key: str, *, claimed_at_iso: str, fields: dict[str, Any]
    ) -> TenantErasureRecord | None:
        """Merge *fields* into the record only while the run's claim still stands; ``None`` when it does not.

        The write a run makes to conclude itself (completed, failed, residue). Same
        condition as :meth:`heartbeat` (``in_progress`` under *claimed_at_iso*): a run
        whose claim a second worker took over must not write its outcome over the
        record that worker now holds (#1792 review SEC-001).
        """

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
