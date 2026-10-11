"""In-memory plan catalogue for tests that build quota checks through the production wiring (#2142).

``get_entitlement_service`` reads a tenant's plan from two repositories
(``get_tenant_repo``, ``get_plan_repo``). A test that replaces the provider leaves of
``app.common.dependencies`` (the Valkey client, the knowledge adapter ...) replaces
these two as well with :func:`patch_entitlement_leaves`; the entitlement service itself
stays the production one.
"""

from __future__ import annotations

from typing import Any

from app.common.exceptions import DuplicateError
from app.domain.interfaces.plan_repository import IPlanRepository
from app.domain.models.plan import DEFAULT_PLAN_KEY, Plan, PlanLimits


def standard_plan(**limits: int | None) -> Plan:
    """The seeded default plan; ``limits`` overrides single dimensions."""
    return Plan(_key=DEFAULT_PLAN_KEY, name="Standard", limits=PlanLimits(**limits), is_default=True)


class InMemoryPlanRepository(IPlanRepository):
    """The plan store in a dict; ``tenant_plans`` maps tenant key → plan key for the counts."""

    def __init__(self, plans: list[Plan] | None = None, tenant_plans: dict[str, str] | None = None) -> None:
        self.plans: dict[str, Plan] = {plan.key: plan for plan in (plans if plans is not None else [standard_plan()])}
        self.tenant_plans: dict[str, str] = dict(tenant_plans or {})

    def get(self, key: str) -> Plan | None:
        return self.plans.get(key)

    def get_default(self) -> Plan | None:
        return next((plan for plan in self.plans.values() if plan.is_default), None)

    def list_all(self) -> list[Plan]:
        return [self.plans[key] for key in sorted(self.plans)]

    def create(self, plan: Plan) -> Plan:
        if plan.key in self.plans:
            raise DuplicateError("plans", "key", plan.key)
        self.plans[plan.key] = plan
        return plan

    def store_plan(self, plan: Plan) -> Plan | None:
        stored = self.plans.get(plan.key)
        if stored is None:
            return None
        self.plans[plan.key] = plan.model_copy(update={"is_default": stored.is_default})
        return self.plans[plan.key]

    def make_default(self, key: str) -> Plan | None:
        if key not in self.plans:
            return None
        for name, plan in list(self.plans.items()):
            self.plans[name] = plan.model_copy(update={"is_default": name == key})
        return self.plans[key]

    def delete_unused(self, key: str) -> bool:
        plan = self.plans.get(key)
        if plan is None or plan.is_default or key in self.tenant_plans.values():
            return False
        del self.plans[key]
        return True

    def tenant_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for plan_key in self.tenant_plans.values():
            counts[plan_key] = counts.get(plan_key, 0) + 1
        return counts

    def count_tenants_on(self, key: str) -> int:
        return sum(1 for plan_key in self.tenant_plans.values() if plan_key == key)


def patch_entitlement_leaves(monkeypatch: Any, tenant_repo: Any, plan_repo: IPlanRepository | None = None) -> None:
    """Replace the two repository leaves ``get_entitlement_service`` reads from."""
    import app.common.dependencies as deps

    plans = plan_repo if plan_repo is not None else InMemoryPlanRepository()
    monkeypatch.setattr(deps, "get_tenant_repo", lambda: tenant_repo)
    monkeypatch.setattr(deps, "get_plan_repo", lambda: plans)
