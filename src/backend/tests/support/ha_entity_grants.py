"""In-memory Home Assistant entity allowlist for tests (MT-015, #2112).

``InMemoryHaEntityGrantRepository`` implements the repository port with the same
semantics as the Arango one (idempotent grant, unique per tenant and entity);
``grant_service`` builds the real :class:`HaEntityGrantService` over it, so a test
exercises the production gate rather than a stand-in that always answers yes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from app.domain.interfaces.ha_entity_grant_repository import IHaEntityGrantRepository
from app.domain.models.ha_entity_grant import HaEntityGrant, HaEntityGrantSource
from app.domain.services.ha_entity_grant_service import HaEntityGrantService


class InMemoryHaEntityGrantRepository(IHaEntityGrantRepository):
    def __init__(self, granted: Mapping[str, Iterable[str]] | None = None) -> None:
        self.rows: dict[tuple[str, str], HaEntityGrant] = {}
        for tenant_key, entity_ids in (granted or {}).items():
            self.grant(tenant_key, entity_ids, source=HaEntityGrantSource.ADMIN)

    def list_for_tenant(self, *, tenant_key: str) -> list[HaEntityGrant]:
        return sorted((g for (t, _), g in self.rows.items() if t == tenant_key), key=lambda g: g.entity_id)

    def granted_entity_ids(self, *, tenant_key: str) -> frozenset[str]:
        return frozenset(e for (t, e) in self.rows if t == tenant_key)

    def all_granted(self) -> dict[str, frozenset[str]]:
        result: dict[str, set[str]] = {}
        for t, e in self.rows:
            result.setdefault(t, set()).add(e)
        return {t: frozenset(es) for t, es in result.items()}

    def grant(self, tenant_key: str, entity_ids: Iterable[str], *, source: HaEntityGrantSource) -> int:
        created = 0
        for entity_id in set(entity_ids):
            if (tenant_key, entity_id) in self.rows:
                continue
            self.rows[(tenant_key, entity_id)] = HaEntityGrant(
                tenant_key=tenant_key, entity_id=entity_id, source=source, created_at=datetime.now(UTC)
            )
            created += 1
        return created

    def revoke(self, tenant_key: str, entity_id: str) -> bool:
        return self.rows.pop((tenant_key, entity_id), None) is not None


def grant_service(
    granted: Mapping[str, Iterable[str]] | None = None,
    ha_client_factory: Callable[[], Any] | None = None,
    *,
    grant_on_use: bool = False,
) -> HaEntityGrantService:
    """The real grant service over an in-memory allowlist."""
    return HaEntityGrantService(
        InMemoryHaEntityGrantRepository(granted), ha_client_factory=ha_client_factory, grant_on_use=grant_on_use
    )


class EverythingGrantedTo:
    """A gate under which one tenant holds a grant for every well-formed entity id.

    For tests of behaviour *beside* the allowlist (collapse rules, deadlines,
    error handling) that need the read to happen: the configuration "the platform
    admin released every entity to this garden" is a real one. Still tenant-bound
    and still shape-checked, so it never admits another tenant or a malformed id.
    """

    def __init__(self, tenant_key: str) -> None:
        self._tenant_key = tenant_key

    def is_granted(self, tenant_key: str, entity_id: str | None) -> bool:
        from app.domain.models.ha_entity_grant import is_ha_entity_id

        return bool(tenant_key) and tenant_key == self._tenant_key and is_ha_entity_id(entity_id)

    def granted_entity_ids(self, tenant_key: str) -> frozenset[str]:  # noqa: ARG002
        raise NotImplementedError("EverythingGrantedTo cannot enumerate; use grant_service() for listings")

    def admits_on_use(self) -> bool:
        return False

    def record_use(self, tenant_key: str, entity_ids: list[str]) -> None:  # noqa: ARG002
        raise NotImplementedError("EverythingGrantedTo never admits on use")
