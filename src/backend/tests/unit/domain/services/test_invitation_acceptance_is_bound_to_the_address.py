"""#2115 (MT-018, REQ-024 AK-61): an e-mail invitation is accepted only by the account that holds the invited address.

``accept_invitation`` never compared ``invitation.email`` with the accepting account: a forwarded or
intercepted link granted a membership — up to ``lead`` — to whoever opened it signed in. For an invitation of
type ``email`` the accepting account must now carry the invited address **and** have proven it
(``User.address_proven``, #1948: a verified flag alone proves nothing). A link invitation is meant to be
shared and stays as designed. A refusal is a 403 that writes nothing — the invitation stays pending, no
membership exists, no audit row is written — and does not name the invited address.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import InvitationStatus, InvitationType, TenantRole
from app.common.exceptions import ForbiddenError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.invitation import Invitation
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

INVITED = "friend@example.org"
TENANT = "t-garden"
TOKEN = "invitation-token"


def _account(key: str = "u-friend", email: str = INVITED, *, proven: bool = True, flag_only: bool = False) -> User:
    """An account; ``flag_only`` is the unproven shape: ``email_verified`` set, no ``email_confirmed_at`` (#1948)."""
    return User.model_validate(
        {
            "_key": key,
            "email": email,
            "display_name": key,
            "email_verified": proven or flag_only,
            "email_confirmed_at": datetime.now(UTC).isoformat() if proven and not flag_only else None,
        }
    )


class _World:
    def __init__(self, *, kind: InvitationType = InvitationType.EMAIL, email: str | None = INVITED) -> None:
        self.invitation = Invitation(
            _key="i1",
            tenant_key=TENANT,
            invited_by_user_key="u-lead",
            invitation_type=kind,
            email=email,
            role=TenantRole.GROWER,
            token_hash=InvitationEngine.hash_token(TOKEN),
            expires_at="2999-01-01T00:00:00+00:00",
        )
        self.invitations = MagicMock()
        self.invitations.get_by_token_hash.return_value = self.invitation
        self.invitations.mark_accepted_if_pending.return_value = self.invitation
        self.memberships = MagicMock()
        self.memberships.get_by_user_and_tenant.return_value = None
        self.memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
        tenants = MagicMock()
        tenants.get_by_key.return_value = Tenant(_key=TENANT, name="Garden", slug="garden", owner_user_key="u-lead")
        self.audit = MagicMock()
        self.service = TenantService(
            tenant_repo=tenants,
            membership_repo=self.memberships,
            invitation_repo=self.invitations,
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=self.audit,
        )

    def accept(self, account: User) -> Membership:
        return self.service.accept_invitation(TOKEN, account)

    def nothing_was_written(self) -> bool:
        return (
            not self.invitations.mark_accepted_if_pending.called
            and not self.memberships.create.called
            and not self.audit.record_membership_change.called
        )


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(_account("u-other", "someone.else@example.org"), id="another proven address"),
        pytest.param(_account("u-other", "someone.else@example.org", proven=False), id="another unproven address"),
    ],
)
def test_an_email_invitation_is_not_accepted_by_an_account_with_another_address(account: User) -> None:
    world = _World()

    with pytest.raises(ForbiddenError) as refused:
        world.accept(account)

    assert world.nothing_was_written()
    assert INVITED not in str(refused.value.message)  # the refusal does not name the invited address


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(_account(proven=False), id="no proof at all"),
        pytest.param(_account(flag_only=True), id="the verified flag without a confirmation stamp"),
    ],
)
def test_the_invited_address_must_be_proven_not_just_claimed(account: User) -> None:
    """Registration with ``REQUIRE_EMAIL_VERIFICATION=false`` stamps the flag for an address nobody proved."""
    world = _World()

    with pytest.raises(ForbiddenError):
        world.accept(account)

    assert world.nothing_was_written()


@pytest.mark.parametrize("spelling", [INVITED, INVITED.upper(), "Friend@Example.org"])
def test_the_proven_invited_address_accepts_whatever_its_case(spelling: str) -> None:
    world = _World()

    membership = world.accept(_account(email=spelling))

    assert (membership.user_key, membership.tenant_key, membership.role) == ("u-friend", TENANT, TenantRole.GROWER)
    world.invitations.mark_accepted_if_pending.assert_called_once()
    world.audit.record_membership_change.assert_called_once()


def test_an_email_invitation_without_an_address_is_refused_not_accepted() -> None:
    world = _World(email=None)

    with pytest.raises(ForbiddenError):
        world.accept(_account())

    assert world.nothing_was_written()


@pytest.mark.parametrize("account", [_account("u-any", "any@example.org", proven=False), _account("u-any", "a@b.org")])
def test_a_link_invitation_stays_open_to_any_account(account: User) -> None:
    """The link is meant to be shared (REQ-024 §1a.2); the binding is for the invitation made *for* an address."""
    world = _World(kind=InvitationType.LINK, email=None)

    membership = world.accept(account)

    assert membership.user_key == "u-any"


def test_a_refusal_leaves_the_invitation_pending() -> None:
    world = _World()
    other: dict[str, Any] = {"key": "u-other", "email": "other@example.org"}

    with pytest.raises(ForbiddenError):
        world.accept(_account(**other))

    assert world.invitation.status == InvitationStatus.PENDING
    world.invitations.update_fields.assert_not_called()
