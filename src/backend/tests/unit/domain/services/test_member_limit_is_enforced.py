"""#2133 (MT-037, REQ-024 AK-64): a tenant takes no member beyond its limit, and no limit exceeds the ceiling.

``Tenant.max_members`` was stored and shown but read by no decision: a personal tenant (``max_members=1``)
took a second, third, ... member through an invitation, and a lead could set any number. Now:

* the **effective limit** of a tenant is ``min(tenant.max_members, TENANT_MAX_MEMBERS_CEILING)``;
* every way that adds an account to an *existing* tenant - accepting an invitation, the platform admin's
  add - is refused with 422 ``MEMBER_LIMIT_REACHED`` once the tenant's active memberships reach it, and
  writes nothing (the invitation stays pending, no step-up is asked for);
* ``max_members`` is set to at most the ceiling, on creation and on every update;
* a tenant that already holds more members than its limit keeps every one of them - the check applies
  to *new* memberships only.

The repositories are the owned I/O boundary (doubles); the real collections are exercised in
``tests/integration/test_member_limit_reach.py``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import InvitationStatus, InvitationType, TenantRole, TenantType
from app.common.exceptions import KamerplanterError, ValidationError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.invitation import Invitation
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

TENANT = "t-garden"
TOKEN = "invitation-token"
_ADMIN = User.model_validate({"_key": "admin-1", "email": "admin@example.org", "display_name": "Admin"})
_JOINER = User.model_validate({"_key": "u-joiner", "email": "joiner@example.org", "display_name": "Joiner"})


class _World:
    """A tenant with ``members`` active memberships and a limit of ``max_members``, behind the ceiling."""

    def __init__(
        self,
        *,
        max_members: int,
        members: int,
        ceiling: int = 50,
        tenant_type: TenantType = TenantType.ORGANIZATION,
        after_insert: int | None = None,
    ) -> None:
        self.tenant = Tenant(
            _key=TENANT,
            name="Garden",
            slug="garden",
            owner_user_key="u-lead",
            tenant_type=tenant_type,
            max_members=max_members,
        )
        self.tenants = MagicMock()
        self.tenants.get_by_key.return_value = self.tenant
        self.tenants.get_by_slug.return_value = None
        self.tenants.update_fields.side_effect = lambda key, data: self.tenant.model_copy(update=data)
        self.tenants.count_organizations_by_owner.return_value = 0
        self.tenants.create_with_lead_membership.side_effect = lambda tenant, membership, audit=None: (
            tenant.model_copy(update={"key": "t-new"}),
            membership,
        )
        self.memberships = MagicMock()
        self.memberships.get_by_user_and_tenant.return_value = None
        # Before the insert the tenant holds ``members``; after it, ``after_insert`` (default: one more).
        after = members + 1 if after_insert is None else after_insert
        self.memberships.count_active_members.side_effect = lambda *, tenant_key: (
            after if self.memberships.create.called else members
        )
        self.memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
        self.memberships.delete.return_value = True
        self.invitation = Invitation(
            _key="i1",
            tenant_key=TENANT,
            invited_by_user_key="u-lead",
            invitation_type=InvitationType.LINK,
            role=TenantRole.GROWER,
            token_hash=InvitationEngine.hash_token(TOKEN),
            expires_at="2999-01-01T00:00:00+00:00",
        )
        self.invitations = MagicMock()
        self.invitations.get_by_token_hash.return_value = self.invitation
        self.invitations.mark_accepted_if_pending.return_value = self.invitation
        self.audit = MagicMock()
        self.step_up = PassedStepUpVerifier()
        kwargs: dict[str, Any] = {
            "tenant_repo": self.tenants,
            "membership_repo": self.memberships,
            "invitation_repo": self.invitations,
            "assignment_repo": MagicMock(),
            "tenant_engine": TenantEngine(),
            "membership_engine": MembershipEngine(),
            "invitation_engine": InvitationEngine(),
            "security_audit": self.audit,
            "step_up_verifier": self.step_up,
            "task_repo": MagicMock(),
            "max_members_ceiling": ceiling,
        }
        self.service = TenantService(**kwargs)

    def accept(self) -> Any:
        return self.service.accept_invitation(TOKEN, _JOINER)

    def admin_add(self) -> Any:
        return self.service.admin_add_membership(
            TENANT, _JOINER.key or "", TenantRole.VIEWER, requester=_ADMIN, client_ip=None, **STEP_UP_PASSED
        )

    def nothing_stands(self) -> bool:
        """No membership is left, no audit row written, no invitation consumed."""
        created = self.memberships.create.called
        taken_back = self.memberships.delete.called
        consumed = self.invitations.mark_accepted_if_pending.called and not any(
            call.args[1].get("status") == InvitationStatus.PENDING
            for call in self.invitations.update_fields.call_args_list
        )
        return (not created or taken_back) and not self.audit.record_membership_change.called and not consumed


def _limit_refusal(exc: KamerplanterError) -> tuple[int, str]:
    return exc.status_code, exc.error_code


# ── the limit holds on every way in ─────────────────────────────────────────


def test_the_third_acceptance_into_a_tenant_of_two_is_refused_with_member_limit_reached() -> None:
    world = _World(max_members=2, members=2)

    with pytest.raises(KamerplanterError) as refused:
        world.accept()

    assert _limit_refusal(refused.value) == (422, "MEMBER_LIMIT_REACHED")
    assert world.nothing_stands()


def test_a_personal_tenant_of_one_takes_no_second_member_by_invitation() -> None:
    """The measured hole: ``max_members=1`` on every personal tenant, and the second member got in."""
    world = _World(max_members=1, members=1, tenant_type=TenantType.PERSONAL)

    with pytest.raises(KamerplanterError) as refused:
        world.accept()

    assert _limit_refusal(refused.value) == (422, "MEMBER_LIMIT_REACHED")


def test_the_admin_add_into_a_full_tenant_is_refused_before_the_step_up() -> None:
    world = _World(max_members=2, members=2)

    with pytest.raises(KamerplanterError) as refused:
        world.admin_add()

    assert _limit_refusal(refused.value) == (422, "MEMBER_LIMIT_REACHED")
    assert world.step_up.actions == []  # what cannot succeed is not asked for a password
    assert not world.memberships.create.called


def test_a_tenant_below_its_limit_still_takes_the_member() -> None:
    world = _World(max_members=3, members=2)

    membership = world.accept()

    assert (membership.user_key, membership.tenant_key) == ("u-joiner", TENANT)
    world.audit.record_membership_change.assert_called_once()
    assert not world.memberships.delete.called


def test_the_ceiling_caps_a_stored_limit_above_it() -> None:
    """A tenant written before the ceiling existed (the seeded platform tenant stores 999) is held to it."""
    world = _World(max_members=999, members=3, ceiling=3)

    with pytest.raises(KamerplanterError) as refused:
        world.admin_add()

    assert _limit_refusal(refused.value) == (422, "MEMBER_LIMIT_REACHED")


def test_a_join_that_a_concurrent_join_pushed_over_the_limit_is_taken_back() -> None:
    """Count and insert are two statements: re-counted after the insert, an overshoot is undone, never kept."""
    world = _World(max_members=2, members=1, after_insert=3)

    with pytest.raises(KamerplanterError) as refused:
        world.accept()

    assert _limit_refusal(refused.value) == (422, "MEMBER_LIMIT_REACHED")
    world.memberships.delete.assert_called_once_with("m-new")
    assert world.nothing_stands()


def test_a_tenant_already_above_its_limit_keeps_every_member() -> None:
    """No member is removed: the check refuses the next join and touches nobody who is in."""
    world = _World(max_members=1, members=4, tenant_type=TenantType.PERSONAL)

    with pytest.raises(KamerplanterError):
        world.accept()

    assert not world.memberships.delete.called
    assert not world.memberships.update_fields.called


# ── the ceiling holds on every way the limit is set ─────────────────────────


def test_an_update_above_the_ceiling_is_refused() -> None:
    world = _World(max_members=5, members=1, ceiling=10)

    with pytest.raises(ValidationError):
        world.service.update_tenant(TENANT, {"max_members": 11})

    assert not world.tenants.update_fields.called


def test_an_update_up_to_the_ceiling_is_written() -> None:
    world = _World(max_members=5, members=1, ceiling=10)

    tenant = world.service.update_tenant(TENANT, {"max_members": 10})

    assert tenant.max_members == 10


def test_an_update_may_lower_the_limit_below_the_current_member_count() -> None:
    """Lowering keeps every member (nobody is removed) and only stops the next join."""
    world = _World(max_members=5, members=4, ceiling=10)

    tenant = world.service.update_tenant(TENANT, {"max_members": 2})

    assert tenant.max_members == 2
    assert not world.memberships.delete.called


def test_the_admin_update_is_held_to_the_same_ceiling() -> None:
    world = _World(max_members=5, members=1, ceiling=10)

    with pytest.raises(ValidationError):
        world.service.admin_update_tenant(
            TENANT, {"max_members": 11}, requester=_ADMIN, client_ip=None, **STEP_UP_PASSED
        )


def test_an_organisation_is_founded_with_at_most_the_ceiling() -> None:
    world = _World(max_members=1, members=0, ceiling=10)

    with pytest.raises(ValidationError):
        world.service.create_organization("u-lead", "Club", max_members=11)


def test_an_organisation_founded_without_a_limit_takes_the_ceiling() -> None:
    world = _World(max_members=1, members=0, ceiling=10)

    tenant = world.service.create_organization("u-lead", "Club")

    assert tenant.max_members == 10


def test_a_personal_tenant_is_founded_with_a_limit_of_one() -> None:
    world = _World(max_members=1, members=0, ceiling=10)

    tenant = world.service.create_personal_tenant("u-new", "New Gardener")

    assert tenant.max_members == 1
