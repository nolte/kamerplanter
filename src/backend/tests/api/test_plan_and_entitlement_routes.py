"""#2142 (REQ-056 §7.6, §7.7, AK-23, AK-24) — the plan routes and the entitlements view over HTTP.

* ``/admin/platform/plans`` is platform-admin only (403 for a member); create 201, taken key 409,
  ``members`` above the ceiling 422, delete of a plan in use 409, of an unused one 204;
* ``PATCH /admin/platform/tenants/{key}`` with ``plan_key`` assigns the plan without a step-up and
  answers with it; an unknown plan is 422;
* ``GET /tenants/{slug}/entitlements`` lists the plan and the usage for every member, without the
  service-account and token dimensions for a member who is not ``lead``, and the KI count of the
  caller only.

Through the production routers and services; the stores are the in-memory doubles, the gate
``require_platform_admin`` runs for real on its ``get_is_platform_admin`` flag.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as admin_router
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_tenant, get_current_user, get_is_platform_admin
from app.common.dependencies import get_entitlement_service, get_plan_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.plan import Plan, PlanLimits
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService, EntitlementUsageSources
from app.domain.services.plan_service import PlanService
from app.domain.services.tenant_service import TenantService
from tests.support.entitlement_doubles import InMemoryPlanRepository, standard_plan

ADMIN = User.model_validate({"_key": "admin-1", "email": "admin@example.org", "display_name": "Admin"})
TENANT = "t-1"


class _AiCounters:
    def tenant_calls_and_tokens(self, tenant_key: str) -> tuple[int, int]:
        return (41, 9000)

    def user_calls(self, *, tenant_key: str, user_key: str) -> int:
        return {"u-anna": 3, "u-lead": 7}.get(user_key, 0)


@pytest.fixture
def world() -> SimpleNamespace:
    tenant = Tenant(_key=TENANT, name="Garden", slug="garden", owner_user_key="u-lead", max_members=40)
    tenants = MagicMock()
    tenants.get_by_key.side_effect = lambda key: state.tenant if key == TENANT else None
    tenants.update_fields.side_effect = lambda key, data: (
        setattr(  # type: ignore[func-returns-value]
            state, "tenant", state.tenant.model_copy(update=data)
        )
        or state.tenant
    )
    plans = InMemoryPlanRepository(
        [standard_plan(), Plan(_key="club", name="Club", limits=PlanLimits(storage_mb=5))],
        tenant_plans={TENANT: "standard"},
    )
    entitlements = EntitlementService(
        plan_repo=plans,
        tenant_repo=tenants,
        usage_sources=EntitlementUsageSources(
            active_members=lambda _t: 12,
            active_service_accounts=lambda _t: 1,
            stored_bytes=lambda _t: 0,
            ai_usage=_AiCounters,
        ),
    )
    audit = MagicMock()
    memberships = MagicMock()
    memberships.count_active_members.return_value = 12
    tenant_service = TenantService(
        tenant_repo=tenants,
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        security_audit=audit,
        entitlements=entitlements,
    )
    state = SimpleNamespace(
        tenant=tenant,
        plans=plans,
        audit=audit,
        admin=True,
        ctx=TenantContext(tenant_key=TENANT, tenant_slug="garden", user_key="u-anna", role=TenantRole.GROWER),
    )

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    app.dependency_overrides[get_is_platform_admin] = lambda: state.admin
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    app.dependency_overrides[get_entitlement_service] = lambda: entitlements
    app.dependency_overrides[get_plan_service] = lambda: PlanService(
        plan_repo=plans, entitlements=entitlements, security_audit=audit
    )
    app.dependency_overrides[get_current_tenant] = lambda: state.ctx
    state.client = TestClient(app)
    return state


def _plans(world: SimpleNamespace) -> Any:
    return world.client.get("/api/v1/admin/platform/plans")


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/api/v1/admin/platform/plans", None),
        ("post", "/api/v1/admin/platform/plans", {"key": "pro", "name": "Pro"}),
        ("patch", "/api/v1/admin/platform/plans/club", {"name": "x"}),
        ("delete", "/api/v1/admin/platform/plans/club", None),
        ("get", f"/api/v1/admin/platform/tenants/{TENANT}", None),
    ],
)
def test_the_plan_routes_refuse_a_member_who_is_no_platform_admin(
    world: SimpleNamespace, method: str, path: str, body: dict[str, Any] | None
) -> None:
    world.admin = False

    response = world.client.request(method, path, json=body)

    assert response.status_code == 403
    assert {plan.key for plan in world.plans.list_all()} == {"standard", "club"}
    world.audit.record_plan_change.assert_not_called()


def test_the_listing_names_each_plan_with_its_tenants(world: SimpleNamespace) -> None:
    response = _plans(world)

    assert response.status_code == 200
    assert [(row["key"], row["is_default"], row["tenant_count"]) for row in response.json()] == [
        ("club", False, 0),
        ("standard", True, 1),
    ]
    assert response.json()[1]["limits"] == dict.fromkeys(PlanLimits.model_fields)


def test_a_plan_is_created_and_a_taken_key_is_a_conflict(world: SimpleNamespace) -> None:
    created = world.client.post(
        "/api/v1/admin/platform/plans", json={"key": "pro", "name": "Pro", "limits": {"storage_mb": 9000}}
    )
    again = world.client.post("/api/v1/admin/platform/plans", json={"key": "pro", "name": "Pro"})

    assert created.status_code == 201
    assert (created.json()["limits"]["storage_mb"], created.json()["is_default"]) == (9000, False)
    assert again.status_code == 409


@pytest.mark.parametrize(
    "body",
    [
        {"key": "big", "name": "Big", "limits": {"members": 51}},  # above TENANT_MAX_MEMBERS_CEILING
        {"key": "big", "name": "Big", "limits": {"storage_mb": -1}},
        {"key": "Big!", "name": "Big"},
        {"key": "big", "name": "Big", "limits": {"sensors": 3}},  # no such dimension (REQ-056 §7.2)
        {"key": "big", "name": "Big", "is_default": True},  # the default is set with PATCH only
    ],
)
def test_an_out_of_range_plan_is_422_and_nothing_is_stored(world: SimpleNamespace, body: dict[str, Any]) -> None:
    response = world.client.post("/api/v1/admin/platform/plans", json=body)

    assert response.status_code == 422
    assert world.plans.get("big") is None


def test_a_plan_in_use_is_not_deleted_an_unused_one_is(world: SimpleNamespace) -> None:
    world.plans.tenant_plans[TENANT] = "club"

    in_use = world.client.delete("/api/v1/admin/platform/plans/club")
    world.plans.tenant_plans[TENANT] = "standard"
    unused = world.client.delete("/api/v1/admin/platform/plans/club")
    default = world.client.delete("/api/v1/admin/platform/plans/standard")

    assert (in_use.status_code, unused.status_code, default.status_code) == (409, 204, 409)
    assert world.plans.get("club") is None


def test_a_plan_change_is_partial_and_audited(world: SimpleNamespace) -> None:
    response = world.client.patch("/api/v1/admin/platform/plans/club", json={"limits": {"members": 20}})

    assert response.status_code == 200
    assert response.json()["limits"]["storage_mb"] == 5
    assert response.json()["limits"]["members"] == 20
    assert world.audit.record_plan_change.call_args.kwargs["changed_fields"] == ["limits.members"]


def test_a_platform_admin_assigns_a_plan_without_a_step_up(world: SimpleNamespace) -> None:
    response = world.client.patch(f"/api/v1/admin/platform/tenants/{TENANT}", json={"plan_key": "club"})
    unknown = world.client.patch(f"/api/v1/admin/platform/tenants/{TENANT}", json={"plan_key": "nope"})

    assert response.status_code == 200
    assert response.json()["plan_key"] == "club"
    assert unknown.status_code == 422
    assert world.tenant.plan_key == "club"


def test_the_admin_tenant_view_carries_every_dimension(world: SimpleNamespace) -> None:
    response = world.client.get(f"/api/v1/admin/platform/tenants/{TENANT}")

    assert response.status_code == 200
    body = response.json()
    assert body["plan_key"] == "standard"
    assert [row["dimension"] for row in body["entitlements"]["limits"]] == [
        "members",
        "service_accounts",
        "storage_mb",
        "photos_per_instance",
        "ai_calls_per_user_day",
        "ai_calls_per_tenant_day",
        "ai_tokens_per_tenant_day",
    ]
    by_dimension = {row["dimension"]: row for row in body["entitlements"]["limits"]}
    assert by_dimension["ai_calls_per_user_day"]["used"] is None  # no member's own count for the admin


def test_a_member_sees_the_plan_and_the_usage_without_the_lead_only_rows(world: SimpleNamespace) -> None:
    response = world.client.get("/api/v1/tenants/garden/entitlements")

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == {"key": "standard", "name": "Standard"}
    rows = {row["dimension"]: (row["limit"], row["used"]) for row in body["limits"]}
    assert rows == {
        "members": (40, 12),
        "storage_mb": (2048, 0),
        "photos_per_instance": (50, None),
        "ai_calls_per_user_day": (50, 3),  # the caller's own count
        "ai_calls_per_tenant_day": (500, 41),
    }


def test_a_lead_also_sees_service_accounts_and_tokens(world: SimpleNamespace) -> None:
    world.ctx = TenantContext(tenant_key=TENANT, tenant_slug="garden", user_key="u-lead", role=TenantRole.LEAD)

    body = world.client.get("/api/v1/tenants/garden/entitlements").json()

    rows = {row["dimension"]: row["used"] for row in body["limits"]}
    assert (rows["service_accounts"], rows["ai_tokens_per_tenant_day"], rows["ai_calls_per_user_day"]) == (1, 9000, 7)


def test_the_entitlements_route_hangs_on_the_tenant_resolver() -> None:
    """A tenant that is not active answers like an unknown slug: the route depends on ``get_current_tenant``."""
    route = next(r for r in tenants_router.routes if getattr(r, "path", "") == "/tenants/{tenant_slug}/entitlements")
    calls = [dependency.call for dependency in route.dependant.dependencies]  # type: ignore[attr-defined]

    assert get_current_tenant in calls


def test_founding_past_the_accounts_organisation_limit_is_422_with_its_own_code(world: SimpleNamespace) -> None:
    """REQ-056 AK-14 over HTTP: ``POST /tenants`` answers ``422 ORGANIZATION_LIMIT_REACHED``, nothing founded."""
    from app.common.auth import require_account_principal

    service: TenantService = world.client.app.dependency_overrides[get_tenant_service]()
    service._max_organizations_per_user = 2
    service._tenant_repo.count_organizations_by_owner.return_value = 2  # one of them suspended: still counted
    world.client.app.dependency_overrides[require_account_principal] = lambda: ADMIN

    response = world.client.post("/api/v1/tenants", json={"name": "Third Garden"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "ORGANIZATION_LIMIT_REACHED"
    service._tenant_repo.create_with_lead_membership.assert_not_called()
