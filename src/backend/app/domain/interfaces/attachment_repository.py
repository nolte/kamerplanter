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
