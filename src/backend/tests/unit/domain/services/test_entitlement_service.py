"""#2142 (REQ-056 §7, AK-17/18/20/21/25) — a tenant's quotas are its plan's, the instance settings by default.

The effective limit of a dimension is the plan's value, or the instance setting when the plan leaves it
``null`` (REQ-056 §7.3). The seeded plan ``standard`` leaves every dimension ``null``, so an installation
on the default plan is held to exactly the limits its settings set before plans existed - the
acceptance criterion "default plan keeps today's behaviour" of #2142.

The plan store and the tenant store are doubles (the I/O boundary); the AQL of the real store is
measured in ``tests/integration/test_v0091_tenant_plan_key.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog

from app.common.enums import EntitlementDimension
from app.common.exceptions import (
    KamerplanterError,
    MemberLimitReachedError,
    NotFoundError,
    PhotoQuotaExceededError,
    ServiceAccountLimitReachedError,
    StorageQuotaExceededError,
    ValidationError,
)
from app.config.settings import Settings
from app.domain.models.plan import Plan, PlanLimits
from app.domain.models.tenant import Tenant
from app.domain.services.ai_call_budget import AiBudgetLimits
from app.domain.services.entitlement_service import (
    INSTANCE_SETTINGS,
    EntitlementService,
    EntitlementUsageSources,
)
from tests.support.entitlement_doubles import InMemoryPlanRepository, standard_plan

TENANT = "t-garden"
MB = 1024 * 1024

#: The instance settings as the ``Settings`` model defaults them (``settings.py``).
DEFAULTS = {name: Settings.model_fields[name].default for name in INSTANCE_SETTINGS.values()}


def _settings(**overrides: int) -> Any:
    return SimpleNamespace(**{**DEFAULTS, **overrides})


def _tenant(plan_key: str = "standard", max_members: int = 50) -> Tenant:
    return Tenant(
        _key=TENANT, name="Garden", slug="garden", owner_user_key="u-1", max_members=max_members, plan_key=plan_key
    )


def _service(
    *plans: Plan, tenant: Tenant | None = None, settings: Any = None, sources: EntitlementUsageSources | None = None
) -> EntitlementService:
    tenants = MagicMock()
    tenants.get_by_key.side_effect = lambda key: (tenant or _tenant()) if key == TENANT else None
    return EntitlementService(
        plan_repo=InMemoryPlanRepository(list(plans) if plans else [standard_plan()]),
        tenant_repo=tenants,
        settings=settings if settings is not None else _settings(),
        usage_sources=sources,
    )


# ── the default plan is today's behaviour (AK-17) ────────────────────


def test_the_default_plan_resolves_every_dimension_to_the_settings_defaults() -> None:
    """``standard`` with unchanged settings gives the limits the check sites read before #2142."""
    service = _service()

    resolved = {dimension: service.limit(TENANT, dimension) for dimension in EntitlementDimension}

    assert resolved == {
        EntitlementDimension.MEMBERS: 50,
        EntitlementDimension.SERVICE_ACCOUNTS: 20,
        EntitlementDimension.STORAGE_MB: 2048,
        EntitlementDimension.PHOTOS_PER_INSTANCE: 50,
        EntitlementDimension.AI_CALLS_PER_USER_DAY: 50,
        EntitlementDimension.AI_CALLS_PER_TENANT_DAY: 500,
        EntitlementDimension.AI_TOKENS_PER_TENANT_DAY: 2_000_000,
    }


def test_the_default_plan_follows_an_operators_environment_override() -> None:
    """``null`` in the plan is the setting *as configured*, not its default (REQ-056 E-01)."""
    service = _service(
        settings=_settings(
            tenant_max_service_accounts=3,
            storage_tenant_quota_mb=10,
            storage_max_photos_per_instance=0,
            ai_budget_tenant_calls_per_day=7,
        )
    )

    assert service.limit(TENANT, EntitlementDimension.SERVICE_ACCOUNTS) == 3
    assert service.limit(TENANT, EntitlementDimension.STORAGE_MB) == 10
    assert service.limit(TENANT, EntitlementDimension.PHOTOS_PER_INSTANCE) is None  # 0 = unlimited, as before
    assert service.ai_budget_limits(TENANT) == AiBudgetLimits(
        user_calls_per_day=50, tenant_calls_per_day=7, tenant_tokens_per_day=2_000_000
    )


def test_every_quota_setting_is_a_settings_field() -> None:
    """The mapping the guard and the resolution read names real settings - a typo would read nothing."""
    assert set(INSTANCE_SETTINGS) == set(EntitlementDimension)
    assert all(name in Settings.model_fields for name in INSTANCE_SETTINGS.values())


# ── a plan's own value (AK-18) ───────────────────────────────────────


def _plan(**limits: int | None) -> Plan:
    return Plan(_key="small", name="Small", limits=PlanLimits(**limits))


@pytest.mark.parametrize(
    ("dimension", "limit", "projected", "error"),
    [
        (EntitlementDimension.MEMBERS, 3, 4, MemberLimitReachedError),
        (EntitlementDimension.SERVICE_ACCOUNTS, 2, 3, ServiceAccountLimitReachedError),
        (EntitlementDimension.STORAGE_MB, 5, 5 * MB + 1, StorageQuotaExceededError),
        (EntitlementDimension.PHOTOS_PER_INSTANCE, 4, 5, PhotoQuotaExceededError),
    ],
)
def test_the_creation_past_a_plan_limit_is_refused_with_the_dimensions_own_code(
    dimension: EntitlementDimension, limit: int, projected: int, error: type[KamerplanterError]
) -> None:
    service = _service(standard_plan(), _plan(**{dimension.value: limit}), tenant=_tenant("small"))

    # The n-th is admitted ...
    assert service.require(TENANT, dimension, projected=projected - 1) == limit
    # ... the (n+1)-th is refused with the code and status the check had before plans (REQ-056 E-06).
    with pytest.raises(error) as refused:
        service.require(TENANT, dimension, projected=projected, subject="p-1")
    assert refused.value.status_code in (409, 422)


def test_the_refusals_keep_their_codes_and_statuses() -> None:
    service = _service(
        standard_plan(),
        _plan(members=1, service_accounts=1, storage_mb=1, photos_per_instance=1),
        tenant=_tenant("small"),
    )

    codes = {}
    for dimension, projected in (
        (EntitlementDimension.MEMBERS, 2),
        (EntitlementDimension.SERVICE_ACCOUNTS, 2),
        (EntitlementDimension.STORAGE_MB, MB + 1),
        (EntitlementDimension.PHOTOS_PER_INSTANCE, 2),
    ):
        with pytest.raises(KamerplanterError) as refused:
            service.require(TENANT, dimension, projected=projected)
        codes[dimension] = (refused.value.error_code, refused.value.status_code)

    assert codes == {
        EntitlementDimension.MEMBERS: ("MEMBER_LIMIT_REACHED", 422),
        EntitlementDimension.SERVICE_ACCOUNTS: ("SERVICE_ACCOUNT_LIMIT_REACHED", 422),
        EntitlementDimension.STORAGE_MB: ("STORAGE_QUOTA_EXCEEDED", 409),
        EntitlementDimension.PHOTOS_PER_INSTANCE: ("PHOTO_QUOTA_EXCEEDED", 409),
    }


def test_a_plan_may_lie_above_the_instance_value_except_for_members() -> None:
    """The instance setting is a default, not a ceiling - but the member ceiling stays hard (§7.3)."""
    service = _service(
        standard_plan(), _plan(members=500, storage_mb=99_999, service_accounts=99), tenant=_tenant("small", 500)
    )

    assert service.limit(TENANT, EntitlementDimension.STORAGE_MB) == 99_999
    assert service.limit(TENANT, EntitlementDimension.SERVICE_ACCOUNTS) == 99
    assert service.limit(TENANT, EntitlementDimension.MEMBERS) == 50


@pytest.mark.parametrize(
    ("max_members", "plan_members", "ceiling", "effective"),
    [(10, None, 50, 10), (40, 20, 50, 20), (40, 30, 25, 25), (5, 30, 50, 5)],
)
def test_the_member_limit_is_the_smallest_of_tenant_plan_and_ceiling(
    max_members: int, plan_members: int | None, ceiling: int, effective: int
) -> None:
    """``min(max_members, plan.members ?? CEILING, CEILING)`` (REQ-056 AK-20)."""
    service = _service(
        standard_plan(),
        _plan(members=plan_members),
        tenant=_tenant("small", max_members),
        settings=_settings(tenant_max_members_ceiling=ceiling),
    )

    assert service.limit(TENANT, EntitlementDimension.MEMBERS) == effective


def test_a_plan_with_members_above_the_ceiling_is_refused() -> None:
    service = _service(settings=_settings(tenant_max_members_ceiling=30))

    with pytest.raises(ValidationError):
        service.refuse_members_above_ceiling(PlanLimits(members=31))
    service.refuse_members_above_ceiling(PlanLimits(members=30))
    service.refuse_members_above_ceiling(PlanLimits())


@pytest.mark.parametrize(
    "dimension",
    [EntitlementDimension.STORAGE_MB, EntitlementDimension.PHOTOS_PER_INSTANCE],
)
def test_zero_in_a_plan_means_unlimited_storage_and_photos(dimension: EntitlementDimension) -> None:
    service = _service(standard_plan(), _plan(**{dimension.value: 0}), tenant=_tenant("small"))

    assert service.limit(TENANT, dimension) is None
    assert service.require(TENANT, dimension, projected=10**12) is None


def test_zero_in_a_plan_switches_a_ki_budget_off() -> None:
    service = _service(
        standard_plan(), _plan(ai_calls_per_user_day=0, ai_tokens_per_tenant_day=1000), tenant=_tenant("small")
    )

    assert service.ai_budget_limits(TENANT) == AiBudgetLimits(
        user_calls_per_day=0, tenant_calls_per_day=500, tenant_tokens_per_day=1000
    )


def test_the_ki_budgets_are_not_decided_by_require() -> None:
    """The KI counters live in Valkey and are charged by ``AiCallBudget``; ``require`` refuses to guess."""
    with pytest.raises(ValueError, match="AiCallBudget"):
        _service().require(TENANT, EntitlementDimension.AI_CALLS_PER_USER_DAY, projected=1)


def test_an_unlimited_dimension_does_not_count() -> None:
    """``projected`` as a callable is evaluated only when a limit applies (no sum per upload when ``0``)."""
    service = _service(settings=_settings(storage_tenant_quota_mb=0))
    count = MagicMock(return_value=0)

    service.require(TENANT, EntitlementDimension.STORAGE_MB, projected=count)

    count.assert_not_called()


# ── plan changes apply from the next check, nothing is removed (AK-21) ──


def test_a_plan_change_applies_from_the_next_decision() -> None:
    plans = InMemoryPlanRepository([standard_plan(), _plan(service_accounts=5)])
    tenants = MagicMock()
    tenants.get_by_key.return_value = _tenant("small")
    service = EntitlementService(plan_repo=plans, tenant_repo=tenants, settings=_settings())
    assert service.limit(TENANT, EntitlementDimension.SERVICE_ACCOUNTS) == 5

    plans.apply_plan_change("small", fields={}, limit_changes={"service_accounts": 2})

    # A tenant at 4 keeps them (nothing here removes anything); the next creation is refused.
    with pytest.raises(ServiceAccountLimitReachedError):
        service.require(TENANT, EntitlementDimension.SERVICE_ACCOUNTS, projected=5)


# ── a missing plan never opens (AK-25) ───────────────────────────────


def test_a_tenant_on_a_missing_plan_gets_the_default_plan_and_a_log_event() -> None:
    default = Plan(_key="basic", name="Basic", limits=PlanLimits(storage_mb=100), is_default=True)
    service = _service(default, tenant=_tenant("gone"))

    with structlog.testing.capture_logs() as logs:
        limit = service.limit(TENANT, EntitlementDimension.STORAGE_MB)

    assert limit == 100
    assert [entry["event"] for entry in logs if entry["log_level"] == "warning"] == ["entitlement.plan_missing"]


def test_a_missing_plan_without_any_default_falls_back_to_the_instance_settings_not_to_unlimited() -> None:
    service = _service(_plan(storage_mb=1), tenant=_tenant("gone"))

    assert service.limit(TENANT, EntitlementDimension.STORAGE_MB) == 2048
    assert service.limit(TENANT, EntitlementDimension.MEMBERS) == 50


def test_the_member_dimension_of_an_unknown_tenant_is_404() -> None:
    with pytest.raises(NotFoundError):
        _service().limit("t-unknown", EntitlementDimension.MEMBERS)


def test_the_default_plan_key_is_the_marked_default() -> None:
    other = Plan(_key="basic", name="Basic", is_default=True)
    assert _service(other).default_plan_key() == "basic"
    assert EntitlementService(plan_repo=None, tenant_repo=None).default_plan_key() == "standard"


# ── usage view (REQ-056 §7.7, AK-24) ─────────────────────────────────


class _AiCounters:
    def __init__(self) -> None:
        self.asked_for: list[str] = []

    def tenant_calls_and_tokens(self, tenant_key: str) -> tuple[int, int]:
        return (41, 12_000)

    def user_calls(self, *, tenant_key: str, user_key: str) -> int:
        self.asked_for.append(user_key)
        return 3


def _usage_service() -> tuple[EntitlementService, _AiCounters]:
    counters = _AiCounters()
    sources = EntitlementUsageSources(
        active_members=lambda _t: 12,
        active_service_accounts=lambda _t: 2,
        stored_bytes=lambda _t: 731 * MB - 5,
        ai_usage=lambda: counters,
    )
    return _service(sources=sources), counters


def test_the_usage_view_of_a_member_leaves_out_the_lead_only_dimensions() -> None:
    service, counters = _usage_service()

    view = service.usage(TENANT, user_key="u-anna", include_lead_only=False)

    assert view.plan_key == "standard"
    assert [(row.dimension.value, row.limit, row.used) for row in view.limits] == [
        ("members", 50, 12),
        ("storage_mb", 2048, 731),
        ("photos_per_instance", 50, None),
        ("ai_calls_per_user_day", 50, 3),
        ("ai_calls_per_tenant_day", 500, 41),
    ]
    assert counters.asked_for == ["u-anna"]


def test_the_usage_view_of_a_lead_lists_every_dimension() -> None:
    service, _ = _usage_service()

    view = service.usage(TENANT, user_key="u-lead", include_lead_only=True)

    used = {row.dimension: row.used for row in view.limits}
    assert set(used) == set(EntitlementDimension)
    assert used[EntitlementDimension.SERVICE_ACCOUNTS] == 2
    assert used[EntitlementDimension.AI_TOKENS_PER_TENANT_DAY] == 12_000


def test_an_unreadable_ki_counter_leaves_the_usage_open_instead_of_failing_the_view() -> None:
    def down() -> Any:
        raise ConnectionError("valkey down")

    service = _service(sources=EntitlementUsageSources(ai_usage=down))

    view = service.usage(TENANT, user_key="u-1", include_lead_only=True)

    used = {row.dimension: row.used for row in view.limits}
    assert used[EntitlementDimension.AI_CALLS_PER_TENANT_DAY] is None
    assert used[EntitlementDimension.AI_CALLS_PER_USER_DAY] is None


# ── security review of #2142 ─────────────────────────────────────────


def test_the_platform_tenant_is_held_to_the_instance_settings_whatever_its_plan(  # SEC-006
) -> None:
    tight = Plan(_key="tight", name="Tight", limits=PlanLimits(members=1), is_default=True)
    platform = _tenant("tight", 50).model_copy(update={"is_platform": True})
    service = _service(tight, tenant=platform)

    assert service.limit(TENANT, EntitlementDimension.MEMBERS) == 50


@pytest.mark.parametrize(
    ("field", "too_big"),
    [
        ("members", 1_000_001),
        ("service_accounts", 100_001),
        ("storage_mb", 10_000_001),
        ("photos_per_instance", 100_001),
        ("ai_calls_per_user_day", 10_000_001),
        ("ai_calls_per_tenant_day", 100_000_001),
        ("ai_tokens_per_tenant_day", 10**12 + 1),
    ],
)
def test_every_limit_has_an_upper_bound_far_above_the_defaults(field: str, too_big: int) -> None:  # SEC-006
    from pydantic import ValidationError as PydanticValidationError

    from app.domain.models.plan import LIMIT_MAXIMA

    with pytest.raises(PydanticValidationError):
        PlanLimits(**{field: too_big})
    assert PlanLimits(**{field: too_big - 1}).of(EntitlementDimension(field)) == too_big - 1
    instance_default = DEFAULTS[INSTANCE_SETTINGS[EntitlementDimension(field)]]
    assert LIMIT_MAXIMA[field] >= 100 * instance_default


def test_the_seed_schema_bounds_are_the_model_bounds() -> None:  # SEC-006: one bound, two spellings
    from pathlib import Path

    import yaml

    import app.migrations
    from app.domain.models.plan import LIMIT_MAXIMA

    schema = yaml.safe_load(
        (Path(app.migrations.__file__).parent / "seed_data" / "schemas" / "plans.schema.yaml").read_text()
    )
    fields = schema["$defs"]["plan"]["properties"]["limits"]["properties"]

    assert {name: spec["maximum"] for name, spec in fields.items()} == LIMIT_MAXIMA
    assert {name: spec["minimum"] for name, spec in fields.items()} == {
        name: (PlanLimits.model_fields[name].metadata[0].ge) for name in fields
    }


def test_the_read_model_ignores_an_unknown_limit_field() -> None:  # SEC-001
    assert PlanLimits.model_validate({"storage_mb": 7, "sensors": 3}).storage_mb == 7
