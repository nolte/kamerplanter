"""Whether a beat may still write into or notify about a tenant (#2166).

A tenant that is ``suspended``, ``pending_deletion``, ``orphaned`` or ``deleted``
resolves for nobody (#2105), while its memberships stay active on purpose — a
cancelled deletion restores them unchanged (#2123). A beat that asks only for the
membership therefore went on writing care tasks into such a tenant and notifying its
members of plants and due dates they cannot open. The stored tenant decides.
"""

from __future__ import annotations

from app.domain.interfaces.tenant_repository import ITenantRepository


class ActiveTenants:
    """``Tenant.is_active`` of each tenant, read once per beat run.

    ``is_active`` is ``status == active`` and nothing else. A tenant that cannot be
    found (its erasure already removed the document) is not active either.
    """

    def __init__(self, tenant_repo: ITenantRepository) -> None:
        self._repo = tenant_repo
        self._answers: dict[str, bool] = {}

    def __call__(self, tenant_key: str) -> bool:
        if not tenant_key:
            return False
        if tenant_key not in self._answers:
            tenant = self._repo.get_by_key(tenant_key)
            self._answers[tenant_key] = tenant is not None and bool(tenant.is_active)
        return self._answers[tenant_key]
