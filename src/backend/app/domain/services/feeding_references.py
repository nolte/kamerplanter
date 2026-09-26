"""The references a feeding, watering event or watering log stores (#1872 C6, C7).

**Tank fill events (C6).** A fill event belongs to the tenant of its tank.

``TankFillEvent`` carries no ``tenant_key``; its tenant is the tank's. Feeding
events, watering events and watering logs store a caller-supplied
``tank_fill_event_key``; before #1872 it was stored verbatim, and the MCP feeding
tool said so in a comment. :func:`require_owned_fill_event` resolves the key
through the owning tank. A fill event that is unknown, has no tank, or whose tank
is another tenant's answers the same 404, so the key's existence is not disclosed.

**Nutrient plans (C7).** Watering events and logs stored a body
``nutrient_plan_key`` verbatim. Plans are a hybrid catalogue: a global plan
(empty ``tenant_key``) or one of the caller's own may be referenced, as the plan
read routes allow (:func:`require_readable_nutrient_plan`).
"""

from __future__ import annotations

from typing import Protocol

from app.common.exceptions import NotFoundError
from app.common.tenant_guard import verify_tenant_read_access
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.tank import Tank, TankFillEvent


class FillEventAnchors(Protocol):
    """What the resolution reads — ``ITankRepository`` satisfies it."""

    def get_fill_event(self, key: str) -> TankFillEvent | None: ...

    def get_by_key(self, key: str) -> Tank | None: ...


def require_owned_fill_event(anchors: FillEventAnchors | None, key: str, tenant_key: str) -> TankFillEvent:
    """The fill event *key*, when its tank belongs to *tenant_key*; else 404.

    Fails closed without anchors or without a tenant: an unresolvable reference is
    refused, never stored.
    """
    if anchors is None or not tenant_key:
        raise NotFoundError("TankFillEvent", key)
    event = anchors.get_fill_event(key)
    tank = anchors.get_by_key(event.tank_key) if event is not None and event.tank_key else None
    if event is None or tank is None or tank.tenant_key != tenant_key:
        raise NotFoundError("TankFillEvent", key)
    return event


class NutrientPlanSource(Protocol):
    def get_by_key(self, key: str) -> NutrientPlan | None: ...


def require_readable_nutrient_plan(plans: NutrientPlanSource | None, key: str, tenant_key: str) -> NutrientPlan:
    """The plan *key*, when it is global or *tenant_key*'s own; else 404 (#1872 C7)."""
    if plans is None or not tenant_key:
        raise NotFoundError("NutrientPlan", key)
    plan = plans.get_by_key(key)
    if plan is None:
        raise NotFoundError("NutrientPlan", key)
    verify_tenant_read_access(plan, tenant_key, "NutrientPlan")
    return plan
