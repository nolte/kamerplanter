"""The question every Home Assistant read, write and dispatch asks (MT-015, #2112).

*May this tenant use this entity of the operator's one Home Assistant instance?*
Answered by the per-tenant allowlist (``HaEntityGrantService`` for a request, a
``HaEntityGrantSnapshot`` for a cross-tenant batch task). A port, so the adapter
layer (the Home Assistant notification channel) can ask it without importing a
service.
"""

from __future__ import annotations

from typing import Protocol


class HaEntityGate(Protocol):
    """Anything that can say whether a tenant may use a Home Assistant entity."""

    def is_granted(self, tenant_key: str, entity_id: str | None) -> bool: ...

    def granted_entity_ids(self, tenant_key: str) -> frozenset[str]: ...

    def admits_on_use(self) -> bool:
        """Whether binding an entity *grants* it instead of being refused (light mode)."""
        ...

    def record_use(self, tenant_key: str, entity_ids: list[str]) -> None:
        """Grant ``entity_ids`` because they were bound — only called when :meth:`admits_on_use`."""
        ...


class DenyAllHaEntityGate:
    """The gate of a component assembled without the allowlist: it grants nothing.

    A sensor, actuator or channel that reads Home Assistant on a tenant's behalf
    must be able to tell whether the tenant may — "cannot tell" is not a reason to
    proceed, so the absent gate refuses rather than passes.
    """

    def is_granted(self, tenant_key: str, entity_id: str | None) -> bool:  # noqa: ARG002 — refuses every pair
        return False

    def granted_entity_ids(self, tenant_key: str) -> frozenset[str]:  # noqa: ARG002 — grants nothing
        return frozenset()

    def admits_on_use(self) -> bool:
        return False

    def record_use(self, tenant_key: str, entity_ids: list[str]) -> None:  # noqa: ARG002 — never admits
        raise RuntimeError("DenyAllHaEntityGate admits nothing on use")
