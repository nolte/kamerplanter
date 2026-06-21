"""REQ-010 — repository interface for ``pest_image_contributions``."""

from abc import ABC, abstractmethod

from app.common.enums import PestImageStatus
from app.domain.models.pest_image import PestImageContribution


class IPestImageRepository(ABC):
    """Persistence boundary for user-contributed pest reference images.

    Tenant-scoped reads/deletes (``get`` / ``list_for_pest`` / ``delete``)
    enforce the per-tenant gallery: a contribution is only ever returned or
    removed for its owning ``tenant_key``. Cross-tenant methods
    (``list_all_for_pest`` / ``get_by_key`` / ``set_status``) are for platform-
    admin moderation and the global promoted-image content endpoint and must
    never be exposed behind a tenant gate.
    """

    @abstractmethod
    def create(self, contribution: PestImageContribution) -> PestImageContribution:
        """Persist a new contribution and return it with its assigned key."""

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> PestImageContribution | None:
        """Return the contribution in ``tenant_key``, or ``None`` if absent/foreign."""

    @abstractmethod
    def list_for_pest(self, tenant_key: str, pest_key: str) -> list[PestImageContribution]:
        """Return the tenant's contributions for a pest, newest first."""

    @abstractmethod
    def list_for_tenant(self, tenant_key: str) -> list[PestImageContribution]:
        """Return all of a tenant's contributions (DSGVO erasure lookup)."""

    @abstractmethod
    def list_for_user(self, user_key: str) -> list[PestImageContribution]:
        """Return all contributions a user authored, across tenants (DSGVO erasure)."""

    @abstractmethod
    def get_by_key(self, key: str) -> PestImageContribution | None:
        """Return a contribution by key irrespective of tenant (moderation / global content)."""

    @abstractmethod
    def list_all_for_pest(self, pest_key: str) -> list[PestImageContribution]:
        """Return *all* tenants' contributions for a pest (platform-admin moderation)."""

    @abstractmethod
    def list_promoted_for_pest(self, pest_key: str) -> list[PestImageContribution]:
        """Return all ``PROMOTED`` contributions for a pest (cross-tenant gallery)."""

    @abstractmethod
    def set_status(self, key: str, status: PestImageStatus, promoted_by: str | None) -> PestImageContribution | None:
        """Set a contribution's status + promotion audit (cross-tenant). ``None`` if absent."""

    @abstractmethod
    def delete(self, key: str, tenant_key: str) -> bool:
        """Delete a tenant's contribution. Returns ``False`` if absent/foreign."""

    @abstractmethod
    def delete_for_tenant(self, tenant_key: str) -> int:
        """Hard-delete every contribution of a tenant. Returns the count removed (DSGVO)."""
