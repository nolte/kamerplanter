"""REQ-056 §7 (#2142, MT-049) — the one source of every tenant quota.

Before #2142 each limit read its own setting: the member ceiling and the
service-account quota in ``TenantService``, the storage quota in
``AttachmentService``, the gallery limit in ``PlantPhotoService`` and the KI
budgets in ``AiCallBudget``. Every check now asks this service, which resolves
the **effective limit** of a tenant (REQ-056 §7.3)::

    effective(tenant, d)       = plan(tenant).limits[d]   if not None
                                 instance setting of d    otherwise
    effective(tenant, members) = min(tenant.max_members, plan.limits.members ?? CEILING, CEILING)

The default plan ``standard`` has every limit ``None``, so it resolves each
dimension to exactly the setting the check read before — the same code, status
and threshold of every refusal (REQ-056 AK-17), including every limit an
operator set by environment variable.

**Fresh on every decision.** The plan is read per call (no cache), so a plan
change or an assignment applies from the next check (REQ-056 §7.5); the
instance settings are read per call too, as the KI budgets always were.

**Never open by a data error.** A tenant pointing at a plan that does not exist
gets the default plan and an ``entitlement.plan_missing`` log event (REQ-056
AK-25); the default plan missing as well, the instance settings apply. Neither
path is "unlimited" unless the instance setting itself says so.

**The guard (REQ-056 AK-19).** No module under ``app/`` other than this one and
``config/settings.py`` reads a setting of :data:`INSTANCE_SETTINGS`
(``tests/unit/guards/test_quota_settings_are_read_by_the_entitlement_service.py``).

Source code is English only (NFR-003).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import structlog

from app.common.enums import EntitlementDimension
from app.common.exceptions import (
    MemberLimitReachedError,
    NotFoundError,
    PhotoQuotaExceededError,
    ServiceAccountLimitReachedError,
    StorageQuotaExceededError,
)
from app.common.log_privacy import log_tenant, loggable_error
from app.domain.interfaces.plan_repository import IPlanRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.plan import DEFAULT_PLAN_KEY, EntitlementUsage, Plan, PlanLimits, TenantEntitlements
from app.domain.services.ai_call_budget import AiBudgetLimits

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.domain.models.tenant import Tenant

logger = structlog.get_logger(__name__)

#: The instance setting each dimension falls back to - the setting the check read before plans existed.
#: The single list of the quota settings; the AK-19 guard reads it from here.
INSTANCE_SETTINGS: Mapping[EntitlementDimension, str] = {
    EntitlementDimension.MEMBERS: "tenant_max_members_ceiling",
    EntitlementDimension.SERVICE_ACCOUNTS: "tenant_max_service_accounts",
    EntitlementDimension.STORAGE_MB: "storage_tenant_quota_mb",
    EntitlementDimension.PHOTOS_PER_INSTANCE: "storage_max_photos_per_instance",
    EntitlementDimension.AI_CALLS_PER_USER_DAY: "ai_budget_user_calls_per_day",
    EntitlementDimension.AI_CALLS_PER_TENANT_DAY: "ai_budget_tenant_calls_per_day",
    EntitlementDimension.AI_TOKENS_PER_TENANT_DAY: "ai_budget_tenant_tokens_per_day",
}

#: Dimensions where ``0`` - in a plan or in the setting - means "no limit" (storage, photos) or
#: "budget off" (KI); either way the check does not refuse (REQ-056 §7.2).
ZERO_MEANS_UNLIMITED: frozenset[EntitlementDimension] = frozenset(
    {
        EntitlementDimension.STORAGE_MB,
        EntitlementDimension.PHOTOS_PER_INSTANCE,
        EntitlementDimension.AI_CALLS_PER_USER_DAY,
        EntitlementDimension.AI_CALLS_PER_TENANT_DAY,
        EntitlementDimension.AI_TOKENS_PER_TENANT_DAY,
    }
)

#: The KI budgets are charged by ``AiCallBudget`` against Valkey counters; this service only names their limits.
_AI_DIMENSIONS: frozenset[EntitlementDimension] = frozenset(
    {
        EntitlementDimension.AI_CALLS_PER_USER_DAY,
        EntitlementDimension.AI_CALLS_PER_TENANT_DAY,
        EntitlementDimension.AI_TOKENS_PER_TENANT_DAY,
    }
)

#: Dimensions only a ``lead`` sees in the usage view (REQ-056 §7.7): service accounts are managed by
#: lead ∧ technical, token counts are an operating figure.
LEAD_ONLY_DIMENSIONS: frozenset[EntitlementDimension] = frozenset(
    {EntitlementDimension.SERVICE_ACCOUNTS, EntitlementDimension.AI_TOKENS_PER_TENANT_DAY}
)

_BYTES_PER_MB = 1024 * 1024


class AiUsageReader(Protocol):
    """The read side of the KI counters (``AiCallBudget``) the usage view needs."""

    def tenant_calls_and_tokens(self, tenant_key: str) -> tuple[int, int]: ...

    def user_calls(self, *, tenant_key: str, user_key: str) -> int: ...


@dataclass(frozen=True)
class EntitlementUsageSources:
    """Where :meth:`EntitlementService.usage` counts what a tenant uses; a missing source reports ``None``."""

    active_members: Callable[[str], int] | None = None
    active_service_accounts: Callable[[str], int] | None = None
    stored_bytes: Callable[[str], int] | None = None
    #: A factory, so the KI budget (which itself asks this service for its limits) is built only when read.
    ai_usage: Callable[[], AiUsageReader] | None = None


def _standard_plan() -> Plan:
    """The default plan as seeded: every limit = the instance setting."""
    return Plan(key=DEFAULT_PLAN_KEY, name="Standard", limits=PlanLimits(), is_default=True)


class EntitlementService:
    """Resolves and enforces the quota of a tenant per :class:`EntitlementDimension` (REQ-056 §7.4)."""

    def __init__(
        self,
        *,
        plan_repo: IPlanRepository | None,
        tenant_repo: ITenantRepository | None,
        settings: Settings | None = None,
        instance_overrides: Mapping[EntitlementDimension, int] | None = None,
        usage_sources: EntitlementUsageSources | None = None,
    ) -> None:
        """Wire the plan and tenant stores.

        ``plan_repo`` ``None`` resolves every tenant to the default plan (all limits = instance settings):
        the shape a service built without the catalogue had before #2142. ``get_entitlement_service`` always
        wires it. ``settings`` ``None`` reads the process settings per call; ``instance_overrides`` replaces
        single instance values (a service constructed with an explicit limit, e.g. a test double's ceiling).
        """
        self._plans = plan_repo
        self._tenants = tenant_repo
        self._settings = settings
        self._overrides = dict(instance_overrides or {})
        self._usage_sources = usage_sources or EntitlementUsageSources()

    # ── instance values ──────────────────────────────────────────────

    def instance_value(self, dimension: EntitlementDimension) -> int:
        """The instance setting of *dimension* (REQ-056 §3 "Instanzwert"), read now."""
        if dimension in self._overrides:
            return self._overrides[dimension]
        settings = self._settings
        if settings is None:
            from app.config.settings import settings as process_settings

            settings = process_settings
        value: int = getattr(settings, INSTANCE_SETTINGS[dimension])
        return value

    def members_ceiling(self) -> int:
        """``TENANT_MAX_MEMBERS_CEILING`` - the hard upper bound of every member limit (REQ-024 AK-64)."""
        return self.instance_value(EntitlementDimension.MEMBERS)

    # ── plan resolution ──────────────────────────────────────────────

    def plan_of(self, tenant: Tenant | None) -> Plan:
        """The plan whose limits apply to *tenant* (REQ-056 §7.3), never ``None``.

        **The platform tenant is held to the instance settings, whatever plan it names** (SEC-006 of the
        #2142 review): its ``lead`` members are the platform admins, and a restrictive plan - an assigned
        one or a default made restrictive - must not stop the operator from adding another admin.
        """
        if self._plans is None or (tenant is not None and tenant.is_platform):
            return _standard_plan()
        wanted = tenant.plan_key if tenant is not None else DEFAULT_PLAN_KEY
        plan = self._plans.get(wanted)
        if plan is not None:
            return plan
        logger.warning(
            "entitlement.plan_missing",
            tenant=log_tenant(tenant.key if tenant is not None else None),
            plan_key=wanted,
        )
        default = self._plans.get_default()
        return default if default is not None else _standard_plan()

    def default_plan_key(self) -> str:
        """The key a new tenant gets: the plan marked default, ``standard`` when none is (REQ-056 §7.1)."""
        if self._plans is None:
            return DEFAULT_PLAN_KEY
        default = self._plans.get_default()
        return default.key if default is not None else DEFAULT_PLAN_KEY

    def assign_plan(self, tenant_key: str, plan_key: str) -> bool:
        """Point the tenant at *plan_key* in one write that happens only while the plan exists (SEC-004).

        ``False`` when nothing was written - the plan is gone or the tenant is unknown or being erased.
        Without a catalogue only ``standard`` can be assigned.
        """
        if self._plans is not None:
            return self._plans.assign_to_tenant(tenant_key, plan_key)
        if plan_key != DEFAULT_PLAN_KEY or self._tenants is None:
            return False
        return self._tenants.update_fields(tenant_key, {"plan_key": plan_key}) is not None

    def get_plan(self, plan_key: str) -> Plan | None:
        """The stored plan *plan_key*, ``None`` when there is none (or no catalogue is wired)."""
        if self._plans is None:
            return _standard_plan() if plan_key == DEFAULT_PLAN_KEY else None
        return self._plans.get(plan_key)

    def _tenant(self, tenant_key: str, *, required: bool) -> Tenant | None:
        tenant = self._tenants.get_by_key(tenant_key) if self._tenants is not None else None
        if tenant is None and required:
            raise NotFoundError("Tenant", tenant_key)
        return tenant

    # ── limits ───────────────────────────────────────────────────────

    def limit(self, tenant_key: str, dimension: EntitlementDimension) -> int | None:
        """The effective limit of *dimension* for the tenant (REQ-056 §7.3); ``None`` = unlimited / off.

        ``members`` needs the tenant (its own ``max_members``) and raises :class:`NotFoundError` for an
        unknown key; every other dimension resolves an unknown tenant to the default plan.
        """
        tenant = self._tenant(tenant_key, required=dimension == EntitlementDimension.MEMBERS)
        return self._effective(tenant, dimension, self.plan_of(tenant))

    def _effective(self, tenant: Tenant | None, dimension: EntitlementDimension, plan: Plan) -> int | None:
        own = plan.limits.of(dimension)
        if dimension == EntitlementDimension.MEMBERS:
            ceiling = self.members_ceiling()
            tenant_limit = tenant.max_members if tenant is not None else ceiling
            return min(tenant_limit, own if own is not None else ceiling, ceiling)
        value = own if own is not None else self.instance_value(dimension)
        if dimension in ZERO_MEANS_UNLIMITED and value <= 0:
            return None
        return value

    def require(
        self,
        tenant_key: str,
        dimension: EntitlementDimension,
        *,
        projected: int | Callable[[], int],
        subject: str | None = None,
    ) -> int | None:
        """Refuse when *projected* exceeds the effective limit; return the limit otherwise.

        ``projected`` is the count **after** the action: the members, service accounts or photos there
        would be, or - for ``storage_mb`` - the tenant's stored **bytes** including the upload (the limit is
        in MB). A callable is evaluated only when a limit applies, so an unlimited dimension costs no count.
        The refusal is the dimension's own, unchanged by #2142 (REQ-056 E-06):
        ``422 MEMBER_LIMIT_REACHED``, ``422 SERVICE_ACCOUNT_LIMIT_REACHED``, ``409 STORAGE_QUOTA_EXCEEDED``,
        ``409 PHOTO_QUOTA_EXCEEDED`` (``subject`` names the plant). The KI budgets are not decided here:
        ``AiCallBudget`` charges its Valkey counters against :meth:`ai_budget_limits`.
        """
        if dimension in _AI_DIMENSIONS:
            raise ValueError(f"{dimension} is charged by AiCallBudget against ai_budget_limits(), not require()")
        limit = self.limit(tenant_key, dimension)
        if limit is None:
            return None
        if callable(projected):
            projected = projected()
        if dimension == EntitlementDimension.STORAGE_MB:
            if projected > limit * _BYTES_PER_MB:
                raise StorageQuotaExceededError(tenant_key, float(limit))
            return limit
        if projected <= limit:
            return limit
        logger.info("entitlement_limit_reached", dimension=dimension.value, tenant=log_tenant(tenant_key), limit=limit)
        if dimension == EntitlementDimension.MEMBERS:
            raise MemberLimitReachedError(limit)
        if dimension == EntitlementDimension.SERVICE_ACCOUNTS:
            raise ServiceAccountLimitReachedError(limit)
        raise PhotoQuotaExceededError(subject or "unknown", limit)

    def ai_budget_limits(self, tenant_key: str) -> AiBudgetLimits:
        """The three daily KI budgets of the tenant for ``AiCallBudget`` (``0`` = off, REQ-031 §3)."""
        tenant = self._tenant(tenant_key, required=False)
        plan = self.plan_of(tenant)

        budgets = {dimension: self._effective(tenant, dimension, plan) or 0 for dimension in _AI_DIMENSIONS}
        return AiBudgetLimits(
            user_calls_per_day=budgets[EntitlementDimension.AI_CALLS_PER_USER_DAY],
            tenant_calls_per_day=budgets[EntitlementDimension.AI_CALLS_PER_TENANT_DAY],
            tenant_tokens_per_day=budgets[EntitlementDimension.AI_TOKENS_PER_TENANT_DAY],
        )

    def refuse_members_above_ceiling(self, limits: PlanLimits) -> None:
        """A plan's ``members`` above ``TENANT_MAX_MEMBERS_CEILING`` is refused when stored (REQ-056 AK-20)."""
        from app.common.exceptions import ValidationError

        ceiling = self.members_ceiling()
        if limits.members is not None and limits.members > ceiling:
            raise ValidationError(
                f"members may not exceed the platform ceiling of {ceiling}.",
                details=[{"field": "limits.members", "reason": f"At most {ceiling}.", "code": "members_above_ceiling"}],
            )

    # ── usage view (REQ-056 §7.7) ────────────────────────────────────

    def usage(
        self, tenant_key: str, *, user_key: str | None = None, include_lead_only: bool = False
    ) -> TenantEntitlements:
        """The tenant's plan and, per dimension, the effective limit and what is used of it.

        ``ai_calls_per_user_day.used`` is *user_key*'s own count, never another member's. The
        dimensions of :data:`LEAD_ONLY_DIMENSIONS` are left out unless ``include_lead_only``.
        """
        tenant = self._tenant(tenant_key, required=True)
        plan = self.plan_of(tenant)
        sources = self._usage_sources
        ai_calls: tuple[int, int] | None = None
        own_calls: int | None = None
        ai_usage = sources.ai_usage
        if ai_usage is not None:
            try:
                reader = ai_usage()
                ai_calls = reader.tenant_calls_and_tokens(tenant_key)
                if user_key is not None:
                    own_calls = reader.user_calls(tenant_key=tenant_key, user_key=user_key)
            except Exception as exc:  # noqa: BLE001 — the counters are best effort in a read-only view
                logger.warning(
                    "entitlement_usage_ai_unavailable", tenant=log_tenant(tenant_key), error=loggable_error(exc)
                )
                ai_calls, own_calls = None, None

        def count(source: Callable[[str], int] | None) -> int | None:
            return source(tenant_key) if source is not None else None

        stored = count(sources.stored_bytes)
        used: dict[EntitlementDimension, int | None] = {
            EntitlementDimension.MEMBERS: count(sources.active_members),
            EntitlementDimension.SERVICE_ACCOUNTS: count(sources.active_service_accounts),
            EntitlementDimension.STORAGE_MB: math.ceil(stored / _BYTES_PER_MB) if stored is not None else None,
            EntitlementDimension.PHOTOS_PER_INSTANCE: None,
            EntitlementDimension.AI_CALLS_PER_USER_DAY: own_calls,
            EntitlementDimension.AI_CALLS_PER_TENANT_DAY: ai_calls[0] if ai_calls is not None else None,
            EntitlementDimension.AI_TOKENS_PER_TENANT_DAY: ai_calls[1] if ai_calls is not None else None,
        }
        rows = [
            EntitlementUsage(dimension=dimension, limit=self._effective(tenant, dimension, plan), used=used[dimension])
            for dimension in EntitlementDimension
            if include_lead_only or dimension not in LEAD_ONLY_DIMENSIONS
        ]
        return TenantEntitlements(plan_key=plan.key, plan_name=plan.name, limits=rows)
