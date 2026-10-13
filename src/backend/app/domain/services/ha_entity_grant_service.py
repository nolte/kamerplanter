"""The per-tenant Home Assistant entity allowlist (MT-015, #2112, operator decision model A).

Kamerplanter runs against **one** Home Assistant instance with **one** token — the
operator's — for every tenant (REQ-005 §1.3, REQ-018 §1.3). Before #2112 every
member of every tenant could list that instance's whole inventory and bind any
``entity_id`` to a sensor, which the backend then read with the operator's token:
a door contact or a presence sensor of the operator's household became readable by
whoever typed its id.

This service is the one place that answers *may this tenant use this entity?*:

* **Writes** call :meth:`HaEntityGrantService.require_granted` — a sensor, an
  actuator, a weather source or a notification destination that names an entity
  the tenant has not been granted is refused with 422 before anything is stored.
* **Reads and dispatches** ask :meth:`is_granted` (one tenant) or a
  :class:`HaEntityGrantSnapshot` (a cross-tenant batch task, one database read per
  run) and *skip* an entity without a grant — nothing is asked of Home Assistant on
  its behalf. That covers rows stored before the allowlist existed and rows whose
  grant the admin has since withdrawn.
* **Listings** for the tenant's entity pickers are filtered to the granted ids
  (:meth:`only_granted`).

The allowlist is maintained by the platform admin (``/admin/ha-entity-grants``);
:meth:`inventory` gives the admin the instance's full inventory with the grant
state per entity. Existing references were seeded by migration v0084, so the
upgrade stops nothing that worked before it.

Fail-closed by construction: an entity id that is not a well-formed Home Assistant
id is never granted, and an empty tenant key has no grants.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

import structlog

from app.common.exceptions import ValidationError
from app.common.log_privacy import log_tenant, loggable_error
from app.domain.interfaces.ha_entity_gate import DenyAllHaEntityGate, HaEntityGate
from app.domain.interfaces.ha_entity_grant_repository import IHaEntityGrantRepository
from app.domain.models.ha_entity_grant import HaEntityGrant, HaEntityGrantSource, is_ha_entity_id

logger = structlog.get_logger(__name__)

__all__ = [
    "HA_ENTITY_NOT_GRANTED",
    "DenyAllHaEntityGate",
    "HaEntityGate",
    "HaEntityGrantService",
    "HaEntityGrantSnapshot",
    "only_granted",
    "require_granted",
]

#: The ``code`` of the 422 detail — stable, so a client can explain it in its own words.
HA_ENTITY_NOT_GRANTED = "HA_ENTITY_NOT_GRANTED"

#: Upper bound of one grant request (the admin panel grants a selection at once).
MAX_GRANTS_PER_REQUEST = 500


class HaEntityGrantSnapshot:
    """Every tenant's grants, read once — for a batch task that walks all tenants."""

    def __init__(self, granted: Mapping[str, frozenset[str]]) -> None:
        self._granted = dict(granted)

    def is_granted(self, tenant_key: str, entity_id: str | None) -> bool:
        if not tenant_key or not is_ha_entity_id(entity_id):
            return False
        return entity_id in self._granted.get(tenant_key, frozenset())

    def granted_entity_ids(self, tenant_key: str) -> frozenset[str]:
        return self._granted.get(tenant_key, frozenset()) if tenant_key else frozenset()

    def admits_on_use(self) -> bool:
        return False  # a batch task reads; it never binds

    def record_use(self, tenant_key: str, entity_ids: list[str]) -> None:  # noqa: ARG002
        raise RuntimeError("a snapshot admits nothing on use")


def require_granted(gate: HaEntityGate, tenant_key: str, references: Mapping[str, str | None]) -> None:
    """Refuse any named Home Assistant entity the tenant has not been granted.

    Args:
        gate: The allowlist to ask.
        tenant_key: The tenant on whose behalf the entity would be used.
        references: ``field name -> entity id`` of the request; ``None`` and ``""``
            mean "unset" and are accepted.

    A gate that *admits on use* (light mode: one household, one tenant, and the
    only user is the platform admin) grants a well-formed entity instead of
    refusing it, so the binding is recorded as an ordinary grant — the same rows a
    later switch to full mode is checked against.

    Raises:
        ValidationError: 422 with one detail per refused field, code
            ``HA_ENTITY_NOT_GRANTED``. Value-free: the entity id is not echoed, and
            "not granted" is the answer whether or not the entity exists in Home
            Assistant — nothing about the operator's inventory is revealed.
    """
    refused = [
        field for field, entity_id in references.items() if entity_id and not gate.is_granted(tenant_key, entity_id)
    ]
    if refused and tenant_key and gate.admits_on_use():
        admissible = [f for f in refused if is_ha_entity_id(references[f])]
        gate.record_use(tenant_key, [str(references[f]) for f in admissible])
        refused = [f for f in refused if f not in admissible]
    if not refused:
        return
    raise ValidationError(
        "A Home Assistant entity is not released for this tenant. Ask the platform administrator to grant it.",
        details=[
            {
                "field": field,
                "reason": "This Home Assistant entity is not released for this tenant.",
                "code": HA_ENTITY_NOT_GRANTED,
            }
            for field in refused
        ],
    )


def only_granted(gate: HaEntityGate, tenant_key: str, entities: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The entries of a Home Assistant listing whose ``entity_id`` the tenant has been granted.

    A gate that admits on use (light mode) lists everything: picking an entry grants it.
    """
    if tenant_key and gate.admits_on_use():
        return [dict(entity) for entity in entities]
    granted = gate.granted_entity_ids(tenant_key)
    return [dict(entity) for entity in entities if entity.get("entity_id") in granted]


class HaEntityGrantService:
    """Reads and maintains the per-tenant Home Assistant entity allowlist."""

    def __init__(
        self,
        repo: IHaEntityGrantRepository,
        ha_client_factory: Callable[[], Any] | None = None,
        *,
        grant_on_use: bool = False,
    ) -> None:
        self._repo = repo
        self._ha_client_factory = ha_client_factory
        # Light mode (REQ-027): one household, one tenant, and the only user is the
        # platform admin — there is no other tenant to keep anything from, and no
        # admin panel to grant in. Binding an entity grants it (source
        # ``light_mode``), so reads stay gated by real rows.
        self._grant_on_use = grant_on_use

    # ── The gate ──────────────────────────────────────────────────────

    def granted_entity_ids(self, tenant_key: str) -> frozenset[str]:
        if not tenant_key:
            return frozenset()
        return self._repo.granted_entity_ids(tenant_key=tenant_key)

    def is_granted(self, tenant_key: str, entity_id: str | None) -> bool:
        if not tenant_key or not is_ha_entity_id(entity_id):
            return False
        return entity_id in self._repo.granted_entity_ids(tenant_key=tenant_key)

    def snapshot(self) -> HaEntityGrantSnapshot:
        """Every tenant's grants in one read, for a cross-tenant batch task."""
        return HaEntityGrantSnapshot(self._repo.all_granted())

    def admits_on_use(self) -> bool:
        return self._grant_on_use

    def record_use(self, tenant_key: str, entity_ids: list[str]) -> None:
        if not self._grant_on_use:
            raise RuntimeError("this allowlist admits nothing on use")
        wanted = [entity_id for entity_id in entity_ids if is_ha_entity_id(entity_id)]
        created = self._repo.grant(tenant_key, wanted, source=HaEntityGrantSource.LIGHT_MODE) if wanted else 0
        logger.info("ha_entity_grants_recorded_on_use", tenant=log_tenant(tenant_key), created=created)

    def require_granted(self, tenant_key: str, references: Mapping[str, str | None]) -> None:
        """See :func:`require_granted`."""
        require_granted(self, tenant_key, references)

    def only_granted(self, tenant_key: str, entities: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """See :func:`only_granted`."""
        return only_granted(self, tenant_key, entities)

    # ── Administration (platform admin) ───────────────────────────────

    def list_grants(self, tenant_key: str) -> list[HaEntityGrant]:
        return self._repo.list_for_tenant(tenant_key=tenant_key)

    def grant(self, tenant_key: str, entity_ids: Iterable[str]) -> int:
        """Release ``entity_ids`` for the tenant; returns how many grants are new.

        Raises:
            ValidationError: an id that is not a Home Assistant entity id, or more
                than :data:`MAX_GRANTS_PER_REQUEST` ids at once.
        """
        wanted = list(dict.fromkeys(entity_ids))
        if len(wanted) > MAX_GRANTS_PER_REQUEST:
            raise ValidationError(f"At most {MAX_GRANTS_PER_REQUEST} entities can be granted at once.")
        malformed = [entity_id for entity_id in wanted if not is_ha_entity_id(entity_id)]
        if malformed:
            raise ValidationError(
                "Every entry must be a Home Assistant entity id such as sensor.tent_temperature.",
                details=[
                    {"field": "entity_ids", "reason": "Not a Home Assistant entity id.", "code": "INVALID_FORMAT"}
                ],
            )
        created = self._repo.grant(tenant_key, wanted, source=HaEntityGrantSource.ADMIN)
        logger.info("ha_entity_grants_added", tenant=log_tenant(tenant_key), requested=len(wanted), created=created)
        return created

    def revoke(self, tenant_key: str, entity_id: str) -> bool:
        removed = self._repo.revoke(tenant_key, entity_id)
        logger.info("ha_entity_grant_revoked", tenant=log_tenant(tenant_key), removed=removed)
        return removed

    def inventory(self, tenant_key: str) -> tuple[bool, list[dict[str, Any]]]:
        """The instance's whole entity inventory, each entry marked ``granted`` for the tenant.

        Returns:
            ``(ha_configured, entries)``. Entities granted to the tenant but no
            longer present in Home Assistant are listed too (``present: False``),
            so the admin can see and withdraw a stale grant. An unreachable Home
            Assistant yields the grants alone — never a 500.
        """
        granted = self.granted_entity_ids(tenant_key)
        client = self._ha_client_factory() if self._ha_client_factory is not None else None
        live: list[dict[str, Any]] = []
        if client is not None:
            try:
                live = list(client.list_entities())
            except Exception as exc:  # noqa: BLE001 — the admin view degrades on an HA outage
                logger.warning("ha_entity_inventory_failed", error=loggable_error(exc))
        seen: set[str] = set()
        entries: list[dict[str, Any]] = []
        for entity in live:
            entity_id = entity.get("entity_id")
            if not isinstance(entity_id, str) or not is_ha_entity_id(entity_id) or entity_id in seen:
                continue
            seen.add(entity_id)
            entries.append({**entity, "granted": entity_id in granted, "present": True})
        entries.extend(
            {
                "entity_id": entity_id,
                "domain": entity_id.split(".", 1)[0],
                "friendly_name": None,
                "granted": True,
                "present": False,
            }
            for entity_id in sorted(granted - seen)
        )
        entries.sort(key=lambda entry: entry["entity_id"])
        return client is not None, entries
