"""Port of the persistent security-audit log (MT-014, #2111)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models.security_audit import SecurityAuditEntry


class ISecurityAuditRepository(ABC):
    @abstractmethod
    def record(self, entry: SecurityAuditEntry) -> str:
        """Append one row; returns its key. Never updates or replaces an existing row."""

    @abstractmethod
    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        """The newest rows first, optionally of one tenant."""

    @abstractmethod
    def delete_expired(self, *, retention_days: int) -> int:
        """Delete the rows older than the retention window; returns how many."""

    @abstractmethod
    def count_undated(self) -> int:
        """Rows without a readable ``created_at`` - never selected by :meth:`delete_expired`."""
