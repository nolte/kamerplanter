"""#2137 (MT-041, audit finding ID-14) — a service account neither founds an organisation nor accepts an invitation.

A service account (``account_type == "service"``, REQ-023 §5b) is a machine
identity: Home Assistant, Grafana, CI/CD, placed in **one** tenant by that
tenant's lead. Its unscoped key passed ``require_account_principal`` (that gate
refuses *tenant-scoped* keys only, #1851), so ``POST /tenants`` founded an
organisation for it — with it as ``lead`` holding both administrative scopes —
and ``POST /tenants/invitations/accept`` joined it to any tenant whose link it
held. Both are acts of a person choosing where to belong; the account type says
there is none.

Both doors now ask :func:`~app.domain.models.user.allows_interactive_auth` in the
service (403, nothing written). The routes run the real router and
``TenantService`` over repository doubles; the principal is the resolved
account, as ``get_current_user`` hands it over for an unscoped key.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user
from app.common.dependencies import get_tenant_service
from app.common.enums import InvitationType, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.invitation import Invitation
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

TENANT = "t-garden"
TOKEN = "link-invitation-token"


def _account(account_type: str) -> User:
    return User.model_validate(
        {
            "_key": f"u-{account_type}",
            "email": f"{account_type}@example.org",
            "display_name": account_type,
            "account_type": account_type,
        }
    )


class _World:
    def __init__(self, principal: User) -> None:
        self.principal = principal
        self.tenants = MagicMock()
        self.tenants.get_by_key.return_value = Tenant(
            _key=TENANT, name="Garden", slug="garden", owner_user_key="u-lead", max_members=50
        )
        self.tenants.get_by_slug.return_value = None
        self.tenants.count_organizations_by_owner.return_value = 0
        self.tenants.create_with_lead_membership.side_effect = lambda tenant, membership, audit=None: (
            tenant.model_copy(update={"key": "t-new"}),
            membership.model_copy(update={"key": "m-founder", "tenant_key": "t-new"}),
        )
        self.memberships = MagicMock()
        self.memberships.get_by_user_and_tenant.return_value = None
        self.memberships.count_active_members.return_value = 1
        self.memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
        self.invitations = MagicMock()
        self.invitations.get_by_token_hash.return_value = Invitation(
            _key="i1",
            tenant_key=TENANT,
            invited_by_user_key="u-lead",
            invitation_type=InvitationType.LINK,
            role=TenantRole.GROWER,
            token_hash=InvitationEngine.hash_token(TOKEN),
            expires_at="2999-01-01T00:00:00+00:00",
        )
        self.invitations.mark_accepted_if_pending.side_effect = lambda key, fields: (
            self.invitations.get_by_token_hash.return_value
        )
        self.audit = MagicMock()
        self.service = TenantService(
            tenant_repo=self.tenants,
            membership_repo=self.memberships,
            invitation_repo=self.invitations,
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=self.audit,
            task_repo=MagicMock(),
        )

    def post(self, path: str, body: dict[str, Any]) -> Any:
        app = FastAPI()
        app.include_router(tenants_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[get_current_user] = lambda: self.principal
        app.dependency_overrides[get_tenant_service] = lambda: self.service
        return TestClient(app, raise_server_exceptions=False).post(path, json=body)

    def found(self) -> Any:
        return self.post("/api/v1/tenants", {"name": "Machine Club"})

    def accept(self) -> Any:
        return self.post("/api/v1/tenants/invitations/accept", {"token": TOKEN})


def test_a_service_account_cannot_found_an_organisation() -> None:
    world = _World(_account("service"))

    response = world.found()

    assert response.status_code == 403, response.text
    assert not world.tenants.create_with_lead_membership.called


def test_a_service_account_cannot_accept_an_invitation() -> None:
    world = _World(_account("service"))

    response = world.accept()

    assert response.status_code == 403, response.text
    assert not world.invitations.mark_accepted_if_pending.called
    assert not world.memberships.create.called
    assert not world.audit.record_membership_change.called


@pytest.mark.parametrize("door", ["found", "accept"])
def test_the_control_a_person_passes_both_doors(door: str) -> None:
    """Without this the 403s above are equally consistent with doors that refuse everybody."""
    world = _World(_account("human"))

    response = world.found() if door == "found" else world.accept()

    assert response.status_code in (200, 201), response.text
