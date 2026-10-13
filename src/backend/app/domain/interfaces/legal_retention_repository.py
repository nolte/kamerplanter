"""NFR-011 R-16/R-17/R-18 and R-06a — the purge side of the rows a tenant deletion keeps (#1789, #1793)."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.models.legal_retention import LegalRetentionPurgeCount, LegalRetentionRule


class ILegalRetentionRepository(ABC):
    """Removes retained rows and the tenant-deletion proofs once their periods have run out."""

    @abstractmethod
    def delete_expired_rows_of_deleted_tenants(
        self, rule: LegalRetentionRule, *, cutoff_iso: str
    ) -> LegalRetentionPurgeCount:
        """Hard-delete the *rule* rows whose tenant no longer exists and whose period ended before *cutoff_iso*.

        A row is selected only when all hold:

        * its ``tenant_key`` is a non-empty string naming no ``tenants`` document —
          the rows of a living tenant are that tenant's records, not retention residue;
        * its ``rule.date_field`` is a readable instant strictly before the cutoff,
          compared with ``DATE_TIMESTAMP`` on both sides (NFR-011 §3.2) — a row
          whose age is not established is never destroyed.

        Its ``rule.children`` (rows whose ``parent_field`` names it) and every edge
        touching the row or a child go in the same transaction.
        """

    @abstractmethod
    def delete_expired_tenant_erasure_records(self, *, cap_before_iso: str, retained_collections: Sequence[str]) -> int:
        """Hard-delete ``completed`` tenant-erasure records past NFR-011 R-06a; return how many.

        A record goes when its ``completed_at`` lies before *cap_before_iso* (the
        five-year cap), or when its own outcomes show it kept rows in one of
        *retained_collections* and none of them still carries the tenant's key —
        the longest R-16..R-18 period of that tenant has then run out. A record
        that kept no such row stays until the cap. ``in_progress`` and
        ``partially_completed`` records are never selected: they are a deletion
        still owed.
        """
