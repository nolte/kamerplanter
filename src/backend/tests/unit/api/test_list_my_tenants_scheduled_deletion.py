"""#2166 — ``GET /tenants`` can list the tenants whose deletion is scheduled, so their management can cancel it.

A ``pending_deletion`` tenant resolves for nobody (#2105), and ``list_my_tenants``
filtered on ``tenant.is_active`` — so the tenant vanished from every list the
member could see, and the lead holding ``management`` had no surface from which to
reach ``POST /tenants/{slug}/erasure/cancel`` (#2123). The default listing must
stay what the tenant switcher and the MCP authenticator stand on (only tenants one
can act in); ``include_scheduled_deletion=true`` adds the scheduled ones with their
``status`` and ``deletion_scheduled_at``.

Driven through the real router and the real :class:`TenantService` with in-memory
repositories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole, TenantStatus
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

CALLER = "lead-2166"
DUE = datetime(2027, 1, 3, 9, 0, tzinfo=UTC)

#: One tenant per lifecycle state, each with an active membership of the caller.
_STATES: dict[str, TenantStatus] = {
    "t-active": TenantStatus.ACTIVE,
    "t-pending": TenantStatus.PENDING_DELETION,
    "t-orphaned": TenantStatus.ORPHANED,
    "t-suspended": TenantStatus.SUSPENDED,
    "t-deleted": TenantStatus.DELETED,
}


def _tenant(key: str, status: TenantStatus) -> Tenant:
    scheduled = status in (TenantStatus.PENDING_DELETION, TenantStatus.ORPHANED)
    return Tenant.model_validate(
        {
            "_key": key,
            "name": key,
            "slug": key.removeprefix("t-"),
            "tenant_type": "organization",
            "owner_user_key": CALLER,
            "status": status,
            "deletion_scheduled_at": DUE if scheduled else None,
            "max_members": 10,
        }
    )


def _service(memberships: list[Membership]) -> TenantService:
    tenants = {key: _tenant(key, status) for key, status in _STATES.items()}
    tenant_repo = MagicMock()
    tenant_repo.get_by_key.side_effect = tenants.get
    membership_repo = MagicMock()
    membership_repo.list_by_user.side_effect = lambda user_key: [m for m in memberships if m.user_key == user_key]
    return TenantService(
        tenant_repo=tenant_repo,
        membership_repo=membership_repo,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
    )


def _client() -> TestClient:
    service = _service(
        [
            Membership(user_key=CALLER, tenant_key=key, role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT])
            for key in _STATES
        ]
    )
    user = User.model_validate({"_key": CALLER, "email": "lead@example.org", "display_name": "Lead"})
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app)


def _by_key(body: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["key"]: row for row in body}


def test_the_default_listing_holds_only_the_tenants_one_can_act_in() -> None:
    resp = _client().get("/api/v1/tenants")

    assert resp.status_code == 200, resp.text
    rows = _by_key(resp.json())
    assert list(rows) == ["t-active"]
    assert rows["t-active"]["status"] == "active"
    assert rows["t-active"]["is_active"] is True
    assert rows["t-active"]["deletion_scheduled_at"] is None


def test_the_opt_in_lists_the_scheduled_deletions_with_their_state_and_date() -> None:
    resp = _client().get("/api/v1/tenants", params={"include_scheduled_deletion": "true"})

    assert resp.status_code == 200, resp.text
    rows = _by_key(resp.json())
    # Suspended and deleted tenants stay out: nothing there for a member to cancel.
    assert sorted(rows) == ["t-active", "t-orphaned", "t-pending"]
    assert rows["t-pending"]["status"] == "pending_deletion"
    assert rows["t-pending"]["is_active"] is False
    assert rows["t-pending"]["deletion_scheduled_at"].startswith("2027-01-03T09:00:00")
    assert rows["t-pending"]["role"] == "lead"
    assert rows["t-pending"]["admin_scopes"] == ["management"]
    assert rows["t-orphaned"]["status"] == "orphaned"
    assert rows["t-orphaned"]["deletion_scheduled_at"] is not None


def test_an_ended_membership_lists_no_scheduled_tenant() -> None:
    service = _service(
        [
            Membership(user_key=CALLER, tenant_key="t-pending", role=TenantRole.LEAD, is_active=False),
            # Another member's membership does not list the tenant for the caller.
            Membership(user_key="someone-else", tenant_key="t-orphaned", role=TenantRole.LEAD),
        ]
    )

    assert service.list_my_tenants(CALLER, include_scheduled_deletion=True) == []
