"""#2180 (REQ-024 AK-58): ``accept_invitation`` asks the rank rule again, with the issuer as actor.

An invitation created before #2084 never met the rule at issuance. A ``lead`` invitation into the
platform tenant whose issuer is not - or no longer - the platform tenant's active lead is refused at
acceptance: 403, nothing written, the invitation stays pending. The end-to-end measurement on a real
database is in ``tests/integration/test_member_role_escalation_reach.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import InvitationType, TenantRole
from app.common.exceptions import ForbiddenError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.invitation import Invitation
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

TOKEN = "invitation-token"
NEWCOMER = User.model_validate({"_key": "u-new", "email": "new@example.org", "display_name": "new"})


def _world(*, platform: bool, role: TenantRole, issuer: Membership | None) -> tuple[TenantService, MagicMock]:
    invitation = Invitation(
        _key="i1",
        tenant_key="t1",
        invited_by_user_key="u-issuer",
        invitation_type=InvitationType.LINK,
        role=role,
        token_hash=InvitationEngine.hash_token(TOKEN),
        expires_at="2999-01-01T00:00:00+00:00",
    )
    invitations = MagicMock()
    invitations.get_by_token_hash.return_value = invitation
    invitations.mark_accepted_if_pending.return_value = invitation
    memberships = MagicMock()
    memberships.get_by_user_and_tenant.side_effect = lambda user, _tenant: issuer if user == "u-issuer" else None
    memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
    memberships.count_active_members.return_value = 1
    tenants = MagicMock()
    tenants.get_by_key.return_value = Tenant(
        _key="t1", name="t1", slug="t1", owner_user_key="u-issuer", is_platform=platform, max_members=50
    )
    service = TenantService(
        tenant_repo=tenants,
        membership_repo=memberships,
        invitation_repo=invitations,
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )
    return service, memberships


def _issuer(role: TenantRole, *, active: bool = True) -> Membership:
    return Membership(_key="m-issuer", user_key="u-issuer", tenant_key="t1", role=role, is_active=active)


@pytest.mark.parametrize(
    "issuer",
    [
        pytest.param(_issuer(TenantRole.VIEWER), id="issuer is the secretary (viewer)"),
        pytest.param(_issuer(TenantRole.GROWER), id="issuer is a grower"),
        pytest.param(_issuer(TenantRole.LEAD, active=False), id="issuer's lead membership is inactive"),
        pytest.param(None, id="issuer left the tenant"),
    ],
)
def test_a_platform_lead_invitation_without_a_lead_behind_it_is_refused(issuer: Membership | None) -> None:
    service, memberships = _world(platform=True, role=TenantRole.LEAD, issuer=issuer)

    with pytest.raises(ForbiddenError):
        service.accept_invitation(TOKEN, NEWCOMER)

    memberships.create.assert_not_called()
    service._invitation_repo.mark_accepted_if_pending.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("platform", "role", "issuer"),
    [
        pytest.param(True, TenantRole.LEAD, _issuer(TenantRole.LEAD), id="platform lead from its lead"),
        pytest.param(True, TenantRole.GROWER, _issuer(TenantRole.VIEWER), id="platform below lead from anyone"),
        pytest.param(False, TenantRole.LEAD, _issuer(TenantRole.VIEWER), id="ordinary tenant lead (REQ-049 2.4)"),
    ],
)
def test_what_the_rule_allows_is_still_accepted(platform: bool, role: TenantRole, issuer: Membership) -> None:
    service, _ = _world(platform=platform, role=role, issuer=issuer)

    membership = service.accept_invitation(TOKEN, NEWCOMER)

    assert (membership.user_key, membership.role) == ("u-new", role)
