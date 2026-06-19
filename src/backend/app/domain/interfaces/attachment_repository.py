"""NFR-013 §2.2 — repository interface for the ``attachments`` collection."""

from abc import ABC, abstractmethod

from app.common.enums import AttachmentCategory
from app.domain.models.attachment import Attachment


class IAttachmentRepository(ABC):
    @abstractmethod
    def create(self, attachment: Attachment) -> Attachment: ...

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> Attachment | None: ...

    @abstractmethod
    def delete(self, key: str, tenant_key: str) -> bool: ...

    @abstractmethod
    def find_by_user(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> list[Attachment]:
        """Return all attachments owned by a user (DSGVO erasure lookup).

        When ``categories`` is given, only attachments of those categories are
        returned; otherwise every attachment for the user is returned.
        """

    @abstractmethod
    def anonymize_user_metadata(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> int:
        """REQ-025 Phase 0 — anonymise ``created_by`` on a user's attachments.

        Sets ``created_by = '_anonymized'`` for every attachment owned by
        ``user_key`` within ``tenant_key`` (optionally restricted to
        ``categories``). The file itself is left in place — it belongs to the
        tenant record (NFR-013 §6.2 item 3). Returns the number of metadata
        documents updated. Idempotent: already-anonymised documents are skipped.
        """

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int:
        """REQ-024/-025 — delete every attachment metadata document of a tenant.

        Removes only the ArangoDB metadata; the binary objects are purged
        separately via ``storage_adapter.delete_prefix`` (NFR-013 §6.1).
        Returns the number of documents deleted.
        """

    @abstractmethod
    def find_by_sha256(self, tenant_key: str, sha256: str) -> Attachment | None:
        """Return an existing attachment with a matching content hash (dedup)."""

    @abstractmethod
    def count_by_tenant(self, tenant_key: str) -> int:
        """Return the number of attachments belonging to a tenant."""

    @abstractmethod
    def sum_bytes_by_tenant(self, tenant_key: str) -> int:
        """Return the total stored byte size of a tenant's attachments (quota)."""

    @abstractmethod
    def list_by_tenant(
        self,
        tenant_key: str,
        category: AttachmentCategory | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Attachment], int]:
        """Return a paginated, newest-first attachment listing for a tenant.

        When ``category`` is given the listing is restricted to that category.
        Returns ``(items, total)`` where ``total`` ignores pagination.
        """
