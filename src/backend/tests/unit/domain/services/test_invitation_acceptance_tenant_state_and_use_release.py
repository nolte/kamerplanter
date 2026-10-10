"""#2182 review I-2 and I-4 - what a failed or impossible acceptance leaves behind.

**I-4 - only into an active tenant.** ``accept_invitation`` read the erasure freeze, the rank rule
and the member limit, but not the tenant's lifecycle state: an invitation into a ``suspended``,
``orphaned`` or ``pending_deletion`` tenant was accepted and wrote a membership the suspension was
meant to stop (a suspension revokes no invitation, so they stay usable after a reactivation).
Refused now with 422 before anything is written; the invitation stays pending.

**I-2 - a use goes back only when the join provably did not happen.** An exception out of the
membership insert does not say whether the membership stands (the insert may have committed before
a later step raised). Handing the use back then admits one account more than ``max_uses``. The use
is released only when the membership read afterwards says there is none; an unknown state keeps it
consumed. The acceptance's own error is what the caller sees either way.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import InvitationType, TenantRole, TenantStatus, TenantType
from app.common.exceptions import ValidationError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.invitation import Invitation
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

TENANT = "t-club"
TOKEN = "link-token"
JOINER = User.model_validate({"_key": "u-anna", "email": "anna@example.org", "display_name": "Anna"})


class _World:
    def __init__(self, *, status: TenantStatus = TenantStatus.ACTIVE) -> None:
        self.invitation = Invitation(
            _key="i1",
            tenant_key=TENANT,
            invited_by_user_key="u-lead",
            invitation_type=InvitationType.LINK,
            role=TenantRole.VIEWER,
            token_hash=InvitationEngine.hash_token(TOKEN),
            expires_at="2999-01-01T00:00:00+00:00",
            max_uses=5,
        )
        self.invitations = MagicMock()
        self.invitations.get_by_token_hash.return_value = self.invitation
        self.invitations.consume_use_if_pending.return_value = self.invitation
        self.memberships = MagicMock()
        #: What ``get_by_user_and_tenant`` answers: before the insert (the already-member check) and after a failure.
        self.memberships.get_by_user_and_tenant.side_effect = [None, None]
        self.memberships.count_active_members.return_value = 1
        self.tenants = MagicMock()
        self.tenants.get_by_key.return_value = Tenant(
            _key=TENANT,
            name="Club",
            slug="club",
            owner_user_key="u-lead",
            tenant_type=TenantType.ORGANIZATION,
            status=status,
            max_members=50,
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
        )

    def accept(self) -> Membership:
        return self.service.accept_invitation(TOKEN, JOINER)


# ── I-4: the tenant's lifecycle state ────────────────────────────────────────


@pytest.mark.parametrize("status", [TenantStatus.SUSPENDED, TenantStatus.ORPHANED, TenantStatus.PENDING_DELETION])
def test_an_invitation_into_a_tenant_that_is_not_active_is_refused_and_nothing_is_written(
    status: TenantStatus,
) -> None:
    world = _World(status=status)

    with pytest.raises(ValidationError, match="not active"):
        world.accept()

    world.invitations.consume_use_if_pending.assert_not_called()
    world.memberships.create.assert_not_called()
    world.audit.record_membership_change.assert_not_called()


def test_an_invitation_whose_tenant_is_gone_is_refused_and_nothing_is_written() -> None:
    world = _World()
    world.tenants.get_by_key.return_value = None

    with pytest.raises(ValidationError):
        world.accept()

    world.invitations.consume_use_if_pending.assert_not_called()
    world.memberships.create.assert_not_called()


def test_an_invitation_into_an_active_tenant_is_accepted() -> None:
    world = _World()
    world.memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})

    joined = world.accept()

    assert (joined.user_key, joined.tenant_key, joined.role) == ("u-anna", TENANT, TenantRole.VIEWER)


# ── I-2: the release of a use after a failed join ────────────────────────────


def test_a_use_goes_back_when_the_failed_join_left_no_membership() -> None:
    world = _World()
    world.memberships.create.side_effect = RuntimeError("write conflict")

    with pytest.raises(RuntimeError, match="write conflict"):
        world.accept()

    world.invitations.release_use.assert_called_once_with("i1", "u-anna")


def test_a_use_stays_consumed_when_the_membership_stands_after_all() -> None:
    """The insert committed, a later step raised: releasing would admit max_uses + 1 accounts."""
    world = _World()
    world.memberships.create.side_effect = RuntimeError("reply lost after the commit")
    standing = Membership(_key="m-new", user_key="u-anna", tenant_key=TENANT, role=TenantRole.VIEWER, is_active=True)
    world.memberships.get_by_user_and_tenant.side_effect = [None, standing]

    with pytest.raises(RuntimeError, match="reply lost"):
        world.accept()

    world.invitations.release_use.assert_not_called()


def test_a_use_stays_consumed_when_the_membership_state_cannot_be_read() -> None:
    world = _World()
    world.memberships.create.side_effect = RuntimeError("database down")
    world.memberships.get_by_user_and_tenant.side_effect = [None, RuntimeError("still down")]

    with pytest.raises(RuntimeError, match="database down"):
        world.accept()

    world.invitations.release_use.assert_not_called()


def test_a_failing_release_does_not_hide_the_acceptances_own_error() -> None:
    world = _World()
    world.memberships.create.side_effect = RuntimeError("write conflict")
    world.invitations.release_use.side_effect = RuntimeError("release failed")

    with pytest.raises(RuntimeError, match="write conflict"):
        world.accept()
