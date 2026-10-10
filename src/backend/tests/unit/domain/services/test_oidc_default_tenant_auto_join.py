"""#2182 / REQ-024 AK-09 — a new account of an OIDC provider joins the provider's ``default_tenant_key``.

The measured gap (before the fix): ``OidcProviderConfig.default_tenant_key`` was stored, settable
behind the platform admin's step-up (#1883) and described in the user guide, but no code path read
it - a new federated account landed in its personal garden only.

Two halves, each driven through the real code:

* **the callback** (``AuthService.complete_oauth``) asks the tenant service to join *only* on the
  account-creating branch and only when the provider names a tenant - an existing account that is
  linked to the provider never joins;
* **the decision** (``TenantService.join_provider_default_tenant``) is safe by default: always
  ``viewer``, never the ``platform`` tenant or a personal one, never a tenant that is not active, full
  or already the account's - refused quietly, so the sign-in itself never fails over the join.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    AuthProviderType,
    SecurityAuditAction,
    SecurityAuditVia,
    TenantRole,
    TenantStatus,
    TenantType,
)
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.auth import OAuthUserInfo
from app.domain.models.membership import Membership
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.tenant_service import TenantService

CLUB = "t-club"
NEW_ADDRESS = "anna@club.example"

# ── the callback: who is asked to join ──────────────────────────────────────


def _oauth_user() -> OAuthUserInfo:
    return OAuthUserInfo(
        provider=AuthProviderType.OIDC,
        provider_user_id="anna-subject",
        email=NEW_ADDRESS,
        display_name="Anna",
        email_verified=True,
    )


def _auth(*, default_tenant_key: str | None, existing: User | None) -> tuple[AuthService, MagicMock]:
    """An AuthService over doubles with a real OAuth engine; returns it and its tenant-service double."""
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = existing
    user_repo.create.side_effect = lambda user: user.model_copy(update={"key": "u-anna"})
    auth_provider_repo = MagicMock()
    auth_provider_repo.list_by_provider.return_value = []
    oauth_engine = MagicMock(wraps=OAuthEngine())
    oauth_engine.exchange_code_for_tokens.return_value = {"access_token": "t", "id_token": ""}
    oauth_engine.authenticate_login.return_value = _oauth_user()
    state_store = MagicMock()
    state_store.get_and_delete.return_value = {
        "provider_slug": "club",
        "code_verifier": "v",
        "redirect_uri": "https://app.example/api/v1/auth/oauth/club/callback",
    }
    config_repo = MagicMock()
    config_repo.get_by_slug.return_value = OidcProviderConfig(
        _key="cfg-club",
        slug="club",
        display_name="Club",
        issuer_url="https://sso.club.example",
        client_id="cid",
        client_secret_encrypted="secret",
        enabled=True,
        default_tenant_key=default_tenant_key,
    )
    token_engine = MagicMock()
    token_engine.create_refresh_token.return_value = ("raw-refresh", "refresh-hash")
    tenant_service = MagicMock()
    tenant_service.email_invitation_pending_for.return_value = False
    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=MagicMock(),
        password_engine=MagicMock(),
        token_engine=token_engine,
        throttle_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://kamerplanter.example",
        oauth_engine=oauth_engine,
        oauth_state_store=state_store,
        oidc_config_repo=config_repo,
        encryption_engine=None,
        tenant_service=tenant_service,
    )
    return service, tenant_service


def test_a_new_account_of_a_provider_with_a_default_tenant_is_asked_to_join_it() -> None:
    service, tenants = _auth(default_tenant_key=CLUB, existing=None)

    service.complete_oauth("club", "code", "state")

    tenants.create_personal_tenant.assert_called_once()
    tenants.join_provider_default_tenant.assert_called_once_with(
        user_key="u-anna", tenant_key=CLUB, provider_slug="club"
    )


@pytest.mark.parametrize("unset", [None, "", "   "])
def test_a_provider_without_a_default_tenant_joins_nobody(unset: str | None) -> None:
    service, tenants = _auth(default_tenant_key=unset, existing=None)

    service.complete_oauth("club", "code", "state")

    tenants.create_personal_tenant.assert_called_once()
    tenants.join_provider_default_tenant.assert_not_called()


def test_an_existing_account_linked_to_the_provider_does_not_join() -> None:
    """Only a NEW account joins: the auto-link of an existing verified account is not a registration."""
    existing = User(
        key="u-existing",
        email=NEW_ADDRESS,
        display_name="Anna",
        email_verified=True,
        email_confirmed_at=datetime(2026, 1, 1, tzinfo=UTC),
        is_active=True,
    )
    service, tenants = _auth(default_tenant_key=CLUB, existing=existing)

    service.complete_oauth("club", "code", "state")

    tenants.create_personal_tenant.assert_not_called()
    tenants.join_provider_default_tenant.assert_not_called()


# ── the decision: what joining means ────────────────────────────────────────


class _Tenants:
    """A real TenantService over doubles, with one tenant shaped by the test."""

    def __init__(self, tenant: Tenant | None, *, members: int = 1, existing: Membership | None = None) -> None:
        self.tenant_repo = MagicMock()
        self.tenant_repo.get_by_key.return_value = tenant
        self.memberships = MagicMock()
        self.memberships.get_by_user_and_tenant.return_value = existing
        self.memberships.count_active_members.side_effect = lambda *, tenant_key: (
            members + 1 if self.memberships.create.called else members
        )
        self.memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
        self.audit = MagicMock()
        self.service = TenantService(
            tenant_repo=self.tenant_repo,
            membership_repo=self.memberships,
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=self.audit,
            task_repo=MagicMock(),
        )

    def join(self) -> Membership | None:
        return self.service.join_provider_default_tenant(user_key="u-anna", tenant_key=CLUB, provider_slug="club")


def _club(**overrides: object) -> Tenant:
    fields: dict[str, object] = {
        "_key": CLUB,
        "name": "Club",
        "slug": "club",
        "owner_user_key": "u-lead",
        "tenant_type": TenantType.ORGANIZATION,
        "max_members": 50,
    }
    fields.update(overrides)
    return Tenant.model_validate(fields)


def test_the_new_account_joins_an_active_organisation_as_viewer_and_the_join_is_audited() -> None:
    world = _Tenants(_club())

    joined = world.join()

    assert joined is not None
    assert (joined.user_key, joined.tenant_key, joined.role, joined.admin_scopes) == (
        "u-anna",
        CLUB,
        TenantRole.VIEWER,
        [],
    )
    world.memberships.create.assert_called_once()
    recorded = world.audit.record_membership_change.call_args.kwargs
    assert recorded["action"] == SecurityAuditAction.MEMBERSHIP_ADDED
    assert recorded["via"] == SecurityAuditVia.OIDC_AUTO_JOIN


@pytest.mark.parametrize(
    ("tenant", "why"),
    [
        (None, "an unknown tenant"),
        (_club(is_platform=True), "the platform tenant - a seat there is the platform role"),
        (_club(tenant_type=TenantType.PERSONAL), "somebody's personal garden"),
        (_club(status=TenantStatus.SUSPENDED), "a suspended tenant"),
        (_club(status=TenantStatus.PENDING_DELETION), "a tenant whose deletion is scheduled"),
        (_club(status=TenantStatus.ORPHANED), "an orphaned tenant"),
    ],
)
def test_no_join_into(tenant: Tenant | None, why: str) -> None:
    world = _Tenants(tenant)

    assert world.join() is None, why
    world.memberships.create.assert_not_called()
    world.audit.record_membership_change.assert_not_called()


def test_no_second_membership_for_an_account_that_already_is_one() -> None:
    existing = Membership(user_key="u-anna", tenant_key=CLUB, role=TenantRole.GROWER, is_active=True)
    world = _Tenants(_club(), existing=existing)

    assert world.join() is None
    world.memberships.create.assert_not_called()


def test_a_full_tenant_refuses_the_join_without_failing_the_sign_in() -> None:
    world = _Tenants(_club(max_members=3), members=3)

    assert world.join() is None
    world.memberships.create.assert_not_called()
    world.audit.record_membership_change.assert_not_called()


def test_a_join_a_concurrent_join_pushed_over_the_limit_is_taken_back_quietly() -> None:
    world = _Tenants(_club(max_members=2), members=1)
    world.memberships.count_active_members.side_effect = lambda *, tenant_key: (
        3 if world.memberships.create.called else 1
    )

    assert world.join() is None
    world.memberships.delete.assert_called_once_with("m-new")
    world.audit.record_membership_change.assert_not_called()
