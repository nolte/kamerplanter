"""Port of the per-tenant Home Assistant entity allowlist (MT-015, #2112)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.domain.models.ha_entity_grant import HaEntityGrant, HaEntityGrantSource


class IHaEntityGrantRepository(ABC):
    @abstractmethod
    def list_for_tenant(self, *, tenant_key: str) -> list[HaEntityGrant]:
        """Every grant of one tenant, ordered by entity id."""

    @abstractmethod
    def granted_entity_ids(self, *, tenant_key: str) -> frozenset[str]:
        """The entity ids released for one tenant."""

    @abstractmethod
    def all_granted(self) -> dict[str, frozenset[str]]:
        """Every tenant's granted entity ids — one read for a cross-tenant batch task."""

    @abstractmethod
    def grant(self, tenant_key: str, entity_ids: Iterable[str], *, source: HaEntityGrantSource) -> int:
        """Release ``entity_ids`` for the tenant; returns how many grants were *new*.

        Idempotent: an entity already granted is left as it is.
        """

    @abstractmethod
    def revoke(self, tenant_key: str, entity_id: str) -> bool:
        """Withdraw one grant; ``True`` when a row was removed."""
