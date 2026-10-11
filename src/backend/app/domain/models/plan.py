"""The plan catalogue: named sets of quotas a tenant points at (REQ-056 §7, §13.2, #2142).

A plan is a **global** document (collection ``plans``, not tenant-scoped), kept by the
platform admin. Every tenant carries exactly one ``plan_key``. A limit of ``None``
means "the instance setting" (the environment variable that decided the limit before
plans existed), so the seeded default plan ``standard`` - every limit ``None`` - keeps
each installation exactly as it was, including every override an operator set.

A plan holds quotas only. Which modules a tenant sees stays with REQ-042 (REQ-056 E-05);
there are no prices, terms or trials (REQ-056 §11).

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import EntitlementDimension

#: REQ-056 §7.6 — the key of a plan: lower-case, starts with a letter, 2-40 characters.
PLAN_KEY_PATTERN = r"^[a-z][a-z0-9_-]{1,39}$"

#: The plan every tenant gets unless a platform admin assigns another (REQ-056 §7.1, E-01).
#: Seeded, renameable, never deletable; the migration v0091 stamps it on every stored tenant.
DEFAULT_PLAN_KEY = "standard"


#: SEC-006 (#2142 review) — the upper bound of every limit, far above any instance default, so a typo
#: (an extra digit, a byte count where MB was meant) is refused instead of stored as a de-facto "unlimited".
LIMIT_MAXIMA: dict[str, int] = {
    "members": 1_000_000,
    "service_accounts": 100_000,
    "storage_mb": 10_000_000,
    "photos_per_instance": 100_000,
    "ai_calls_per_user_day": 10_000_000,
    "ai_calls_per_tenant_day": 100_000_000,
    "ai_tokens_per_tenant_day": 10**12,
}


class PlanLimits(BaseModel):
    """The quotas of one plan, one field per :class:`EntitlementDimension`; ``None`` = instance setting.

    The bounds are the ones REQ-056 §7.2 names, capped above by :data:`LIMIT_MAXIMA`. ``members`` is
    additionally bounded by the platform ceiling ``TENANT_MAX_MEMBERS_CEILING`` - checked by the service
    when a plan is stored, because the ceiling is an instance value the model does not know.

    **``0`` means unlimited** for ``storage_mb`` and ``photos_per_instance`` and **budget off** (= no
    limit) for the three KI budgets (REQ-056 §7.2, decision SEC-002 of the #2142 review). A plan cannot
    express "none at all" for these.

    **Tolerant when read (SEC-001):** a stored plan may carry a limit field a newer build wrote; it is
    ignored rather than failing every quota decision of every tenant on that plan. Request bodies use
    :class:`PlanLimitsRequest` (``app/api/v1/admin/platform/schemas.py``), which refuses unknown fields.
    """

    model_config = ConfigDict(extra="ignore")

    members: int | None = Field(
        default=None, ge=1, le=LIMIT_MAXIMA["members"], description="null = TENANT_MAX_MEMBERS_CEILING; never above it."
    )
    service_accounts: int | None = Field(
        default=None, ge=1, le=LIMIT_MAXIMA["service_accounts"], description="null = TENANT_MAX_SERVICE_ACCOUNTS."
    )
    storage_mb: int | None = Field(
        default=None,
        ge=0,
        le=LIMIT_MAXIMA["storage_mb"],
        description="null = STORAGE_TENANT_QUOTA_MB; 0 = UNLIMITED (no storage quota at all).",
    )
    photos_per_instance: int | None = Field(
        default=None,
        ge=0,
        le=LIMIT_MAXIMA["photos_per_instance"],
        description="null = STORAGE_MAX_PHOTOS_PER_INSTANCE; 0 = UNLIMITED (no photo limit at all).",
    )
    ai_calls_per_user_day: int | None = Field(
        default=None,
        ge=0,
        le=LIMIT_MAXIMA["ai_calls_per_user_day"],
        description="null = AI_BUDGET_USER_CALLS_PER_DAY; 0 = budget OFF (unlimited calls).",
    )
    ai_calls_per_tenant_day: int | None = Field(
        default=None,
        ge=0,
        le=LIMIT_MAXIMA["ai_calls_per_tenant_day"],
        description="null = AI_BUDGET_TENANT_CALLS_PER_DAY; 0 = budget OFF (unlimited calls).",
    )
    ai_tokens_per_tenant_day: int | None = Field(
        default=None,
        ge=0,
        le=LIMIT_MAXIMA["ai_tokens_per_tenant_day"],
        description="null = AI_BUDGET_TENANT_TOKENS_PER_DAY; 0 = budget OFF (unlimited tokens).",
    )

    def of(self, dimension: EntitlementDimension) -> int | None:
        """The plan's own value for *dimension* (``None`` = the instance setting)."""
        value: int | None = getattr(self, dimension.value)
        return value


class Plan(BaseModel):
    """A named set of quotas (REQ-056 §13.2). ``key`` is the document ``_key`` and immutable."""

    key: str = Field(alias="_key", pattern=PLAN_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    limits: PlanLimits = Field(default_factory=PlanLimits)
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(populate_by_name=True)


#: The dimensions where ``0`` - in a plan - lifts the limit entirely (REQ-056 §7.2, SEC-002).
ZERO_IS_UNLIMITED_FIELDS: tuple[str, ...] = (
    "storage_mb",
    "photos_per_instance",
    "ai_calls_per_user_day",
    "ai_calls_per_tenant_day",
    "ai_tokens_per_tenant_day",
)


class PlanLimitChange(BaseModel):
    """One changed limit of a ``plan_changed`` audit row (SEC-005): the old and the new value.

    ``flag`` marks the changes that lift a limit: ``to_unlimited`` (the new value is ``0`` on a dimension
    where ``0`` means unlimited) and ``to_instance_setting`` (the new value is ``null``).
    """

    field: str
    old: int | None
    new: int | None
    flag: Literal["to_unlimited", "to_instance_setting"] | None = None


class PlanWithUsage(BaseModel):
    """A plan and how many tenants point at it (the platform-admin listing, REQ-056 §7.6)."""

    plan: Plan
    tenant_count: int = Field(ge=0)


class EntitlementUsage(BaseModel):
    """One dimension's effective limit and what the tenant uses of it (REQ-056 §7.7).

    ``limit`` ``None`` = unlimited. ``used`` ``None`` = not counted per tenant (photos are counted per
    plant) or not readable right now (the KI counters live in Valkey).
    """

    dimension: EntitlementDimension
    limit: int | None
    used: int | None


class TenantEntitlements(BaseModel):
    """A tenant's plan with every dimension it may see (REQ-056 §7.7)."""

    plan_key: str
    plan_name: str
    limits: list[EntitlementUsage]
