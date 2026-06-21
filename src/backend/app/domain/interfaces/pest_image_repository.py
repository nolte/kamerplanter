"""REQ-010 — repository interface for ``pest_image_contributions``."""

from abc import ABC, abstractmethod

from app.domain.models.pest_image import PestImageContribution


class IPestImageRepository(ABC):
    """Persistence boundary for user-contributed pest reference images.

    Every read/delete is tenant-scoped: a contribution is only ever returned
    or removed for its owning ``tenant_key`` (cross-tenant access surfaces as
    ``None`` / no-op), enforcing the Phase-1 tenant-private gallery.
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
    def delete(self, key: str, tenant_key: str) -> bool:
        """Delete a tenant's contribution. Returns ``False`` if absent/foreign."""
