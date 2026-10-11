"""#2142 (REQ-056 §6.2, §7.4-§7.6) — the tenant service decides its limits through the tenant's plan.

* the member limit (REQ-024 AK-64) and the service-account quota (REQ-023 §5b) are the plan's
  (REQ-056 AK-18, AK-20, AK-21) - the existing check-site suites (``test_member_limit_is_enforced``,
  ``test_service_accounts``) stay unchanged and green on the default plan (AK-17);
* the organisations one account may own are ``TENANT_MAX_ORGANIZATIONS_PER_USER``, refused with
  ``422 ORGANIZATION_LIMIT_REACHED`` (AK-14, AK-15);
* a platform admin assigns a plan (audited ``tenant_plan_changed``, no step-up); a tenant's management
  cannot (AK-23); a new tenant gets the plan marked default.

The repositories are doubles; the tenant-count AQL is measured in
``tests/integration/test_v0091_tenant_plan_key.py``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import EntitlementDimension, SecurityAuditAction, TenantStatus
from app.common.exceptions import KamerplanterError, ValidationError
from app.domain.models.plan import Plan, PlanLimits
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService
from tests.support.entitlement_doubles import InMemoryPlanRepository, standard_plan
from tests.support.step_up import STEP_UP_PASSED
from tests.unit.domain.services import test_member_limit_is_enforced as member_world
from tests.unit.domain.services import test_service_accounts as sa_world

ADMIN = User.model_validate({"_key": "admin-1", "email": "admin@example.org", "display_name": "Admin"})
SMALL = Plan(_key="small", name="Small", limits=PlanLimits(members=3, service_accounts=1))


def _on_plan(
    service: Any, tenant: Tenant, *plans: Plan, instance: dict[EntitlementDimension, int] | None = None
) -> InMemoryPlanRepository:
    """Point the service's tenant at *tenant* and resolve its quotas through *plans* over *instance* values."""
    service._tenant_repo.get_by_key.return_value = tenant
    repo = InMemoryPlanRepository([standard_plan(), *plans])
    service._entitlements = EntitlementService(
        plan_repo=repo, tenant_repo=service._tenant_repo, instance_overrides=instance
    )
    return repo


# ── member limit and service-account quota (AK-18, AK-20, AK-21) ──────


def test_the_plans_member_limit_refuses_the_join_below_the_tenants_own_limit() -> None:
    world = member_world._World(max_members=10, members=3)
    _on_plan(world.service, world.tenant.model_copy(update={"plan_key": "small"}), SMALL)

    with pytest.raises(KamerplanterError) as refused:
        world.admin_add()

    assert (refused.value.status_code, refused.value.error_code) == (422, "MEMBER_LIMIT_REACHED")
    world.memberships.create.assert_not_called()


def test_the_default_plan_keeps_the_tenants_own_member_limit() -> None:
    world = member_world._World(max_members=10, members=3)
    _on_plan(world.service, world.tenant)

    assert world.admin_add().key == "m-new"


def test_a_lower_member_limit_removes_nobody_and_refuses_the_next_join() -> None:
    """A tenant with 5 members moved to a plan of 3 keeps all 5; only the 6th is refused (REQ-056 §7.5)."""
    world = member_world._World(max_members=10, members=5)
    _on_plan(world.service, world.tenant.model_copy(update={"plan_key": "small"}), SMALL)

    with pytest.raises(KamerplanterError):
        world.admin_add()

    world.memberships.delete.assert_not_called()


def test_the_plans_service_account_quota_refuses_the_next_account() -> None:
    world = sa_world._World(service_accounts=1)
    tenant = Tenant(_key=sa_world.TENANT, name="Garden", slug="garden", owner_user_key="u-lead", max_members=50)
    _on_plan(world.service, tenant.model_copy(update={"plan_key": "small"}), SMALL)

    with pytest.raises(KamerplanterError) as refused:
        world.create()

    assert (refused.value.status_code, refused.value.error_code) == (422, "SERVICE_ACCOUNT_LIMIT_REACHED")
    assert world.nothing_written()


def test_a_plan_above_the_instance_service_account_quota_admits_more() -> None:
    world = sa_world._World(service_accounts=3)
    tenant = Tenant(_key=sa_world.TENANT, name="Garden", slug="garden", owner_user_key="u-lead", max_members=50)
    big = Plan(_key="big", name="Big", limits=PlanLimits(service_accounts=10))
    instance = {EntitlementDimension.SERVICE_ACCOUNTS: 3}
    _on_plan(world.service, tenant, big, instance=instance)
    with pytest.raises(KamerplanterError):
        world.create()  # on the default plan the instance quota of 3 is full

    _on_plan(world.service, tenant.model_copy(update={"plan_key": "big"}), big, instance=instance)
    created = world.create()

    assert created.key


# ── organisations per account (AK-14, AK-15) ─────────────────────────


def _founding_world(*, owned: int, limit: int) -> member_world._World:
    world = member_world._World(max_members=10, members=1)
    world.tenants.count_organizations_by_owner.return_value = owned
    world.service._max_organizations_per_user = limit
    return world


def test_the_organisation_past_the_accounts_limit_is_refused_with_its_own_code() -> None:
    world = _founding_world(owned=2, limit=2)

    with pytest.raises(KamerplanterError) as refused:
        world.service.create_organization(member_world._founder("u-lead"), "Third Garden")

    assert (refused.value.status_code, refused.value.error_code) == (422, "ORGANIZATION_LIMIT_REACHED")
    world.tenants.create_with_lead_membership.assert_not_called()


def test_a_limit_of_zero_closes_self_service_founding() -> None:
    world = _founding_world(owned=0, limit=0)

    with pytest.raises(KamerplanterError) as refused:
        world.service.create_organization(member_world._founder("u-lead"), "First Garden")

    assert refused.value.error_code == "ORGANIZATION_LIMIT_REACHED"


def test_below_the_limit_an_organisation_is_founded() -> None:
    world = _founding_world(owned=1, limit=2)

    tenant = world.service.create_organization(member_world._founder("u-lead"), "Second Garden")

    assert tenant.key == "t-new"


def test_the_organisation_limit_defaults_to_ten() -> None:
    """The setting default and the service default are both 10 - the number the engine hard-coded."""
    from app.config.settings import Settings

    world = member_world._World(max_members=10, members=1)
    assert world.service._max_organizations_per_user == 10
    assert Settings.model_fields["tenant_max_organizations_per_user"].default == 10


def test_a_new_tenant_gets_the_plan_marked_default() -> None:
    world = member_world._World(max_members=10, members=1)
    repo = _on_plan(world.service, world.tenant, Plan(_key="basic", name="Basic"))
    repo.make_default("basic")

    tenant = world.service.create_organization(member_world._founder("u-lead"), "Garden Two")

    assert tenant.plan_key == "basic"


# ── plan assignment (AK-23) ──────────────────────────────────────────


def _assign(world: member_world._World, plan_key: str) -> Tenant:
    return world.service.admin_update_tenant(
        member_world.TENANT,
        {"plan_key": plan_key},
        requester=ADMIN,
        client_ip=None,
        **STEP_UP_PASSED,
    )


def test_a_platform_admin_assigns_a_plan_without_a_step_up_and_it_is_audited() -> None:
    world = member_world._World(max_members=10, members=1)
    _on_plan(world.service, world.tenant, SMALL)
    world.step_up = MagicMock()
    world.service._step_up_verifier = world.step_up

    updated = _assign(world, "small")

    assert updated.plan_key == "small"
    world.step_up.verify.assert_not_called()
    world.audit.record_tenant_change.assert_called_once()
    row = world.audit.record_tenant_change.call_args.kwargs
    assert (row["action"], row["old_plan_key"], row["plan_key"]) == (
        SecurityAuditAction.TENANT_PLAN_CHANGED,
        "standard",
        "small",
    )


def test_an_unknown_plan_is_refused_and_nothing_is_written() -> None:
    world = member_world._World(max_members=10, members=1)
    _on_plan(world.service, world.tenant)

    with pytest.raises(ValidationError):
        _assign(world, "nope")

    world.tenants.update_fields.assert_not_called()
    world.audit.record_tenant_change.assert_not_called()


def test_a_suspended_tenant_can_be_assigned_a_plan_a_deleted_one_cannot() -> None:
    world = member_world._World(max_members=10, members=1)
    _on_plan(world.service, world.tenant.model_copy(update={"status": TenantStatus.SUSPENDED}), SMALL)
    assert _assign(world, "small").plan_key == "small"

    _on_plan(world.service, world.tenant.model_copy(update={"status": TenantStatus.DELETED}), SMALL)
    with pytest.raises(ValidationError):
        _assign(world, "small")


def test_re_sending_the_current_plan_writes_nothing() -> None:
    world = member_world._World(max_members=10, members=1)
    _on_plan(world.service, world.tenant)

    _assign(world, "standard")

    world.tenants.update_fields.assert_not_called()
    world.audit.record_tenant_change.assert_not_called()


def test_a_tenants_management_cannot_set_its_plan() -> None:
    """``update_tenant`` (``PATCH /tenants/{slug}``) refuses the field outright (REQ-056 §7.6)."""
    world = member_world._World(max_members=10, members=1)

    with pytest.raises(ValueError, match="platform admin"):
        world.service.update_tenant(member_world.TENANT, {"plan_key": "small"})


def test_the_tenant_update_request_has_no_plan_field() -> None:
    from app.api.v1.tenants.schemas import TenantUpdateRequest

    assert "plan_key" not in TenantUpdateRequest.model_fields
