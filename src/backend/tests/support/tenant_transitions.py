"""The compare-and-set of ``ITenantRepository.transition_status`` for in-memory tenant doubles (REQ-056).

Mirrors the AQL of ``ArangoTenantRepository.transition_status`` rule by rule, so a double refuses
what the real statement refuses: a state outside ``expected`` matches nothing (``None``), the
remembered state is taken from the stored tenant, and a restore without a remembered state and
without a fallback matches nothing. ``tests/integration/test_tenant_erasure_cancel_keeps_suspension.py``
drives the real statement.
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import Any, Literal

from app.common.enums import TenantStatus
from app.domain.models.tenant import Tenant

_REMEMBERABLE = (TenantStatus.ACTIVE, TenantStatus.SUSPENDED)


def apply_transition(
    stored: Tenant | None,
    *,
    expected: Collection[TenantStatus],
    status: TenantStatus | None,
    deletion_scheduled_at: datetime | None | Literal["keep"],
    previous: Literal["remember", "clear", "keep"],
    restore_fallback: TenantStatus | None = None,
) -> Tenant | None:
    if stored is None or stored.status not in expected:
        return None
    if status is None:
        target = stored.status_before_deletion if stored.status_before_deletion in _REMEMBERABLE else restore_fallback
    else:
        target = status
    if target is None:
        return None
    update: dict[str, Any] = {"status": target}
    if deletion_scheduled_at != "keep":
        update["deletion_scheduled_at"] = deletion_scheduled_at
    if previous == "remember":
        update["status_before_deletion"] = (
            stored.status if stored.status in _REMEMBERABLE else stored.status_before_deletion
        )
    elif previous == "clear":
        update["status_before_deletion"] = None
    return Tenant.model_validate({**stored.model_dump(by_alias=True), **update})


def attach_transition(repo: Any, tenants: dict[str, Tenant]) -> None:
    """Give a ``MagicMock`` tenant repo a ``transition_status`` over the stored *tenants* (keyed by ``_key``)."""

    def transition_status(key: str, **kwargs: Any) -> Tenant | None:
        moved = apply_transition(tenants.get(key), **kwargs)
        if moved is not None:
            tenants[key] = moved
        return moved

    repo.transition_status.side_effect = transition_status
