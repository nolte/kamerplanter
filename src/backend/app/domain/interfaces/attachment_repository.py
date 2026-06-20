"""NFR-013 §2.2 — repository interface for the ``attachments`` collection."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Final

from app.common.enums import AttachmentCategory
from app.domain.models.attachment import Attachment


class _Unset:
    """Sentinel distinguishing "field absent" from an explicit ``None``.

    REQ-034 §2.1 v1.2 — the photo-metadata PATCH must tell "do not touch this
    field" apart from "clear this field". ``UNSET`` means leave the stored value
    untouched; an explicit ``None`` clears it. A dedicated singleton type keeps
    the distinction explicit and type-checkable rather than overloading ``None``.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "UNSET"


UNSET: Final[_Unset] = _Unset()


class IAttachmentRepository(ABC):
    @abstractmethod
    def create(self, attachment: Attachment) -> Attachment: ...

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> Attachment | None: ...

    @abstractmethod
    def delete(self, key: str, tenant_key: str) -> bool: ...

    @abstractmethod
    def update_metadata(
        self,
        key: str,
        tenant_key: str,
        *,
        caption: str | None | _Unset = UNSET,
        taken_on: date | None | _Unset = UNSET,
    ) -> Attachment | None:
        """REQ-034 §2.1 v1.2 — patch the user-editable photo metadata.

        Tenant-scoped: only an attachment whose ``tenant_key`` matches is
        touched (cross-tenant updates surface as ``None``). Only the fields that
        are **not** :data:`UNSET` are written, so this is a true PATCH —
        passing ``caption=None`` clears the caption while omitting it leaves the
        stored value intact. Returns the updated attachment, or ``None`` when no
        matching attachment exists. Does not change any other field.
        """

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
