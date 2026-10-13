"""REQ-056 §7.6 (#2142) — the platform admin keeps the plan catalogue.

List (with the number of tenants per plan), create, change, delete and choose
the default plan. Every change of the catalogue writes a security-audit row
(``plan_created`` / ``plan_changed`` with the changed field names / ``plan_deleted``),
which together with ``tenant_plan_changed`` is the record a later billing module
reads (REQ-056 §11). No step-up: a plan change locks nobody out and deletes
nothing - a lower limit refuses only the next creation (§7.5, REQ-056 E-07).

The routes are platform-admin only and full mode only (``app/api/v1/router.py``
mounts the platform-admin router in full mode); a tenant's management cannot
reach any of this.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from typing import Any, Literal

import structlog

from app.common.enums import SecurityAuditAction
from app.common.exceptions import NotFoundError, ResourceInUseError, ValidationError
from app.domain.interfaces.plan_repository import IPlanRepository
from app.domain.models.plan import ZERO_IS_UNLIMITED_FIELDS, Plan, PlanLimitChange, PlanLimits, PlanWithUsage
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.security_audit_service import SecurityAuditService

logger = structlog.get_logger(__name__)

#: The fields a change may name besides ``limits`` (whose dimensions are listed one by one).
_PLAIN_FIELDS = ("name", "description")


class PlanService:
    def __init__(
        self,
        *,
        plan_repo: IPlanRepository,
        entitlements: EntitlementService,
        security_audit: SecurityAuditService | None,
    ) -> None:
        self._plans = plan_repo
        self._entitlements = entitlements
        # ``None`` only for doubles; ``get_plan_service`` always wires it.
        self._security_audit = security_audit

    def list_plans(self) -> list[PlanWithUsage]:
        """Every plan with how many tenants point at it, ordered by key."""
        counts = self._plans.tenant_counts()
        return [PlanWithUsage(plan=plan, tenant_count=counts.get(plan.key, 0)) for plan in self._plans.list_all()]

    def get_plan(self, plan_key: str) -> Plan:
        plan = self._plans.get(plan_key)
        if plan is None:
            raise NotFoundError("Plan", plan_key)
        return plan

    def create_plan(
        self, *, key: str, name: str, description: str | None, limits: PlanLimits, actor: User
    ) -> PlanWithUsage:
        """Store a new plan (409 for a taken key, 422 for ``members`` above the ceiling). Never the default."""
        self._entitlements.refuse_members_above_ceiling(limits)
        created = self._plans.create(Plan(key=key, name=name, description=description, limits=limits))
        self._audit(SecurityAuditAction.PLAN_CREATED, actor, created.key, None)
        logger.info("plan_created", plan_key=created.key)
        return PlanWithUsage(plan=created, tenant_count=0)

    def update_plan(self, plan_key: str, changes: dict[str, Any], *, actor: User) -> PlanWithUsage:
        """Apply a partial change: ``name``, ``description``, single ``limits`` dimensions, ``is_default``.

        ``changes`` holds only the fields the request set (``model_dump(exclude_unset=True)``); inside
        ``limits`` an explicit ``null`` means "the instance setting". ``is_default: true`` makes the plan the
        one default (the previous default loses the mark in the same statement); ``is_default: false`` is
        422 - a default is replaced by marking another plan. The change applies to every tenant on the plan
        from its next check (§7.5). A change that changes nothing writes nothing.
        """
        stored = self.get_plan(plan_key)
        changed: list[str] = []
        updates: dict[str, Any] = {}
        for field in _PLAIN_FIELDS:
            if field in changes and changes[field] != getattr(stored, field):
                updates[field] = changes[field]
                changed.append(field)
        limits = stored.limits
        limit_changes: dict[str, int | None] = {}
        if "limits" in changes and changes["limits"] is not None:
            merged = {**{name: getattr(stored.limits, name) for name in PlanLimits.model_fields}, **changes["limits"]}
            limits = PlanLimits(**merged)
            limit_changes = {
                name: getattr(limits, name)
                for name in PlanLimits.model_fields
                if getattr(limits, name) != getattr(stored.limits, name)
            }
        limit_audit = [
            PlanLimitChange(
                field=f"limits.{name}",
                old=getattr(stored.limits, name),
                new=new,
                flag=_relaxing_flag(name, new),
            )
            for name, new in limit_changes.items()
        ]
        changed.extend(change.field for change in limit_audit)
        make_default = changes.get("is_default")
        if make_default is False and stored.is_default:
            raise ValidationError(
                "A default plan is replaced by marking another plan as default.",
                details=[
                    {"field": "is_default", "reason": "Mark another plan as default.", "code": "default_required"}
                ],
            )
        if limit_changes:
            self._entitlements.refuse_members_above_ceiling(limits)
        result = stored
        if updates or limit_changes:
            # SEC-003 — one UPDATE of the changed fields; is_default and created_at are never written here.
            applied = self._plans.apply_plan_change(plan_key, fields=updates, limit_changes=limit_changes)
            if applied is None:
                raise NotFoundError("Plan", plan_key)
            result = applied
        if make_default is True and not stored.is_default:
            defaulted = self._plans.make_default(plan_key)
            if defaulted is None:
                raise NotFoundError("Plan", plan_key)
            result = defaulted
            changed.append("is_default")
        if changed:
            self._audit(SecurityAuditAction.PLAN_CHANGED, actor, plan_key, changed, limit_audit or None)
            logger.info(
                "plan_changed",
                plan_key=plan_key,
                fields=changed,
                lifted=[change.field for change in limit_audit if change.flag is not None],
            )
        return PlanWithUsage(plan=result, tenant_count=self._plans.count_tenants_on(plan_key))

    def delete_plan(self, plan_key: str, *, actor: User) -> None:
        """Remove a plan; 409 while it is the default or any tenant points at it, 404 when unknown."""
        stored = self.get_plan(plan_key)
        if stored.is_default:
            raise ResourceInUseError("Plan", "it is the default plan")
        if not self._plans.delete_unused(plan_key):
            if self._plans.get(plan_key) is None:
                raise NotFoundError("Plan", plan_key)
            raise ResourceInUseError("Plan", "tenants are assigned to it")
        self._audit(SecurityAuditAction.PLAN_DELETED, actor, plan_key, None)
        logger.info("plan_deleted", plan_key=plan_key)

    def _audit(
        self,
        action: SecurityAuditAction,
        actor: User,
        plan_key: str,
        changed: list[str] | None,
        limit_changes: list[PlanLimitChange] | None = None,
    ) -> None:
        if self._security_audit is None:
            return
        self._security_audit.record_plan_change(
            action=action,
            actor_user_key=actor.key or "",
            plan_key=plan_key,
            changed_fields=changed,
            limit_changes=limit_changes,
        )


def _relaxing_flag(name: str, new: int | None) -> Literal["to_unlimited", "to_instance_setting"] | None:
    """SEC-005 — mark a change that lifts a limit: to ``0`` where ``0`` is unlimited, or to ``null``."""
    if new is None:
        return "to_instance_setting"
    if new == 0 and name in ZERO_IS_UNLIMITED_FIELDS:
        return "to_unlimited"
    return None
