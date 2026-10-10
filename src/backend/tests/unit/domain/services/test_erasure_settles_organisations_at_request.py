"""#2166 — an organisation is settled when its last management holder **requests** erasure, not 90 days later.

Measured on develop before this change: ``PrivacyService.request_erasure`` closes the
account at once (``is_active=False``, ``password_hash=None``, every session revoked)
and only tells the members of the subject's *personal* tenants. The organisation
settlement of #2134 (``TenantService.settle_organisations_of_erased_account``) ran
inside ``erase_account`` alone — the hard delete, ``RETENTION_SOFT_DELETE_RETENTION_DAYS``
(default 90) after the request. For that whole window an organisation whose only
``management`` holder asked to be erased had nobody who could invite, administer or
delete it (the closed account cannot sign in), and its members were told nothing.

Why settling at request time is safe: an account erasure request has no withdrawal.
There is no cancel route, the password hash is dropped with the request, and the
daily beat hard-deletes every due request whatever ``is_active`` says — so nothing a
request-time hand-over changes would ever have to be restored. The hard delete still
runs the settlement (idempotent): it repairs a request whose settlement failed and an
organisation that lost its management again during the grace.

Each case runs through the production entry (``request_erasure``) over the real
:class:`TenantService` and the in-memory repositories of
``test_erasure_invitations_and_late_join``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, SecurityAuditVia, TenantRole, TenantStatus, TenantType
from app.common.exceptions import ValidationError
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from tests.conftest import wire_get_or_raise
from tests.support.privacy_doubles import FakeErasureRepo, step_up
from tests.unit.domain.services.test_erasure_invitations_and_late_join import (  # noqa: F401 - the autouse salt fixture
    OWNER,
    OWNER_EMAIL,
    OWNER_PASSWORD,
    PasswordEngine,
    Tenants,
    _log_pseudonym_salt,
    _member,
    _personal_tenant,
    _privacy,
)

ORG = "t-org"
LEAD, GROWER = "u-lead", "u-grower"


def _organisation() -> Tenant:
    return Tenant(
        _key=ORG,
        name="Lindenhof",
        slug="lindenhof",
        tenant_type=TenantType.ORGANIZATION,
        owner_user_key=OWNER,
        max_members=10,
    )


def _org_member(user_key: str, role: TenantRole, scopes: list[AdminScope] | None = None) -> Membership:
    return Membership(
        _key=f"m-{user_key}-{ORG}",
        user_key=user_key,
        tenant_key=ORG,
        role=role,
        admin_scopes=scopes or [],
        is_active=True,
        joined_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _users(*keys: str) -> MagicMock:
    accounts = {
        OWNER: User(
            _key=OWNER,
            email=OWNER_EMAIL,
            display_name="Ada Owner",
            password_hash=PasswordEngine().hash_password(OWNER_PASSWORD),
            email_verified=True,
            is_active=True,
        )
    }
    for key in keys:
        accounts[key] = User(_key=key, email=f"{key}@example.org", display_name=key, email_verified=True)
    repo = MagicMock()
    repo.get_by_key.side_effect = accounts.get
    wire_get_or_raise(repo, "User")
    return repo


class _World:
    """The subject's personal tenant plus one organisation, around the real services."""

    def __init__(self, org_members: list[Membership], *, erasure_repo: Any = None) -> None:
        self.tenants = Tenants(_personal_tenant(), _organisation(), members=[_member(OWNER), *org_members])
        self.users = _users(*(m.user_key for m in org_members if m.user_key != OWNER))
        service = self.tenants.service
        # What ``get_tenant_service`` wires and the settlement needs: the real rule, a mailer, the
        # accounts it mails, and the security audit of the hand-over.
        service._membership_engine = MembershipEngine()
        service._email_service = MagicMock()
        service._user_repo = self.users
        service._security_audit = MagicMock()
        self.org_mailer: MagicMock = service._email_service
        self.audit: MagicMock = service._security_audit
        self.privacy, _ = _privacy(self.tenants, erasure_repo or FakeErasureRepo(), user_repo=self.users)

    def request(self) -> Any:
        return self.privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

    def membership(self, user_key: str) -> Membership:
        found = self.tenants.memberships.get_by_user_and_tenant(user_key, ORG)
        assert found is not None
        return found

    def org(self) -> Tenant:
        tenant = self.tenants.tenant_repo.get_by_key(ORG)
        assert tenant is not None
        return tenant

    def org_mailed(self) -> set[str]:
        return {call.kwargs["to_email"] for call in self.org_mailer.send_notification_email.call_args_list}


class TestTheLastManagementHolderHandsOverWhenRequesting:
    def test_the_remaining_lead_holds_management_right_after_the_request(self) -> None:
        world = _World(
            [
                _org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _org_member(LEAD, TenantRole.LEAD),
                _org_member(GROWER, TenantRole.GROWER),
            ]
        )

        world.request()

        assert AdminScope.MANAGEMENT in world.membership(LEAD).admin_scopes, (
            "the organisation must be administrable from the request on, not only after the hard delete"
        )
        assert world.org().status == TenantStatus.ACTIVE
        assert world.tenants.runs == [], "the request erases nothing; it only settles the organisation"

    def test_the_hand_over_is_audited_as_an_account_erasure(self) -> None:
        world = _World(
            [_org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _org_member(LEAD, TenantRole.LEAD)]
        )

        world.request()

        (audit_call,) = world.audit.record_membership_change.call_args_list
        assert audit_call.kwargs["via"] == SecurityAuditVia.ACCOUNT_ERASURE
        assert audit_call.kwargs["target_user_key"] == LEAD

    def test_every_remaining_member_is_told_at_request_time_and_the_subject_is_not(self) -> None:
        world = _World(
            [
                _org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _org_member(LEAD, TenantRole.LEAD),
                _org_member(GROWER, TenantRole.GROWER),
            ]
        )

        world.request()

        assert world.org_mailed() == {f"{LEAD}@example.org", f"{GROWER}@example.org"}
        body = world.org_mailer.send_notification_email.call_args_list[0].kwargs["html_body"]
        # The text must be true at request time, when the account is closed but not yet erased.
        assert "asked" in body and "delete their account" in body
        assert "has deleted their account" not in body


class TestAnOrganisationNobodyCouldAdministerIsOrphanedWhenRequesting:
    def test_without_a_lead_left_it_is_orphaned_and_scheduled_from_the_request(self) -> None:
        world = _World(
            [_org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _org_member(GROWER, TenantRole.GROWER)]
        )
        before = datetime.now(UTC)

        world.request()

        org = world.org()
        assert org.status == TenantStatus.ORPHANED
        record = world.tenants.records.get(TenantErasureEngine.record_key(ORG))
        assert record is not None
        assert (record.status, record.origin) == ("scheduled", "orphaned_organisation")
        grace = world.tenants.service._tenant_erasure_grace
        assert record.scheduled_for is not None
        assert before + grace <= record.scheduled_for <= datetime.now(UTC) + grace
        assert f"{GROWER}@example.org" in world.org_mailed()

    def test_another_management_holder_leaves_the_organisation_alone(self) -> None:
        world = _World(
            [
                _org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _org_member(LEAD, TenantRole.VIEWER, [AdminScope.MANAGEMENT]),
            ]
        )

        world.request()

        assert world.org().status == TenantStatus.ACTIVE
        world.audit.record_membership_change.assert_not_called()
        assert world.org_mailed() == set()


class TestASettlementThatFailsNeverUndoesTheRequest:
    def test_the_request_stands_and_the_hard_delete_settles_later(self) -> None:
        world = _World(
            [_org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _org_member(LEAD, TenantRole.LEAD)]
        )
        service = world.tenants.service

        def _fail(user_key: str, **_kwargs: Any) -> list[Any]:
            raise RuntimeError("database unavailable")

        service.settle_organisations_of_erased_account = _fail  # type: ignore[method-assign]

        erasure = world.request()

        assert erasure.status == "scheduled"
        world.users.update_fields.assert_called_once_with(OWNER, {"is_active": False, "password_hash": None})
        assert AdminScope.MANAGEMENT not in world.membership(LEAD).admin_scopes
        # The hard delete runs the same idempotent settlement before its plan (#2134).
        del service.settle_organisations_of_erased_account
        outcomes = service.settle_organisations_of_erased_account(OWNER, now=datetime.now(UTC) + timedelta(days=90))
        assert [o.outcome for o in outcomes] == ["management_passes_to_lead"]
        assert AdminScope.MANAGEMENT in world.membership(LEAD).admin_scopes


class _ReadBeforeTheOtherWrote(FakeErasureRepo):
    """Two concurrent requests: each read finds no open request; the second insert hits the first's key."""

    def find_active_for_user(self, user_key: str) -> Any:  # noqa: ARG002 - the race: nothing visible yet
        return None


def _spy_settlement(world: _World) -> list[str]:
    service = world.tenants.service
    real = service.settle_organisations_of_erased_account
    calls: list[str] = []

    def _spy(user_key: str, **kwargs: Any) -> list[Any]:
        calls.append(user_key)
        return real(user_key, **kwargs)

    service.settle_organisations_of_erased_account = _spy  # type: ignore[method-assign]
    return calls


class TestASecondRequestCatchesUpOnlyWhatFailed:
    def test_asking_again_settles_an_organisation_the_first_request_could_not(self) -> None:
        # #2166 S1 — the settlement is best effort; the repeated request repeats it, like the invitation revocation.
        world = _World(
            [_org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _org_member(LEAD, TenantRole.LEAD)]
        )
        service = world.tenants.service

        def _fail(user_key: str, **_kwargs: Any) -> list[Any]:
            raise RuntimeError("database unavailable")

        service.settle_organisations_of_erased_account = _fail  # type: ignore[method-assign]
        world.request()
        assert AdminScope.MANAGEMENT not in world.membership(LEAD).admin_scopes
        del service.settle_organisations_of_erased_account

        with pytest.raises(ValidationError, match="already in progress"):
            world.request()

        assert AdminScope.MANAGEMENT in world.membership(LEAD).admin_scopes
        (audit_call,) = world.audit.record_membership_change.call_args_list
        assert audit_call.kwargs["target_user_key"] == LEAD

    def test_asking_again_after_a_settled_request_hands_nothing_over_twice(self) -> None:
        world = _World(
            [
                _org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _org_member(LEAD, TenantRole.LEAD),
                _org_member(GROWER, TenantRole.GROWER),
            ]
        )
        world.request()
        mails = world.org_mailer.send_notification_email.call_count

        with pytest.raises(ValidationError):
            world.request()

        assert len(world.audit.record_membership_change.call_args_list) == 1
        assert world.org_mailer.send_notification_email.call_count == mails

    def test_only_the_call_that_created_the_request_settles(self) -> None:
        # #2166 S2 — the concurrent second call is answered with the first's record and settles nothing:
        # both would read the organisation before either wrote and hand management over twice.
        world = _World(
            [_org_member(OWNER, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _org_member(LEAD, TenantRole.LEAD)],
            erasure_repo=_ReadBeforeTheOtherWrote(),
        )
        settled = _spy_settlement(world)

        first = world.request()
        second = world.request()

        assert second.key == first.key
        assert settled == [OWNER]
