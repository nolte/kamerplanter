"""#1825 / #1843 — who may still join a personal tenant once its owner asked to be erased.

REQ-025 AK-IE-06, AK-IE-07 and the two defects of #1843, each through the
production entry, over in-memory repositories that refuse what the real ones
refuse (a second insert under a taken key, an undeclared field):

* **AK-IE-06** — ``request_erasure`` and ``erase_account_now`` revoke every
  pending invitation into every personal tenant of the subject, and
  ``accept_invitation`` — looked up by token, as the route does — refuses it.
* **AK-IE-07 (a)** — a join between the first membership check and the insert
  of the tenant-erasure record is seen by the re-check after the insert: the
  tenant is kept and the record withdrawn, instead of the joiner being
  deactivated and the tenant erased.
* **AK-IE-07 (b)** — a join whose freeze check preceded the record insert and
  whose membership insert followed it is rolled back and refused.
* **#1843** — two interleaved self-service requests leave one erasure record,
  and a deployment that cannot erase refuses before anything is written.

The interleavings are forced by hooks inside the doubles at the exact write the
race needs, not by running two calls one after the other.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import InvitationStatus, InvitationType, TenantRole, TenantType
from app.common.exceptions import FeatureNotConfiguredError, ForbiddenError, ValidationError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.invitation import Invitation
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureRecord
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService
from tests.conftest import wire_get_or_raise
from tests.support.privacy_doubles import FakeErasureRepo, RecordingErasureExecutor, step_up
from tests.support.tenant_erasure_doubles import FakeTenantErasureRepository

SALT = "s" * 32
LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"
OWNER = "u-owner"
OWNER_EMAIL = "owner@example.org"
OWNER_PASSWORD = "correct-horse-battery-staple"
JOINER = "u-joiner"
PERSONAL = "t-personal"
SHARED = "t-club"
NOW = datetime(2026, 9, 30, 10, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "log_pseudonym_salt", LOG_SALT)


# ── doubles ────────────────────────────────────────────────────────


class FakeTenantRepo:
    def __init__(self, *tenants: Tenant) -> None:
        self.stored = {t.key: t for t in tenants}

    def get_by_key(self, key: str) -> Tenant | None:
        return self.stored.get(key)

    def personal_tenant_keys_by_owner(self, user_key: str) -> list[str]:
        """The real query: by owner **and** type."""
        return [
            key
            for key, t in self.stored.items()
            if t.owner_user_key == user_key and t.tenant_type == TenantType.PERSONAL
        ]


class FakeInvitationRepo:
    """In-memory :class:`IInvitationRepository`; ``update_fields`` re-parses like the driver round-trip."""

    def __init__(self) -> None:
        self.stored: dict[str, Invitation] = {}

    def create(self, invitation: Invitation) -> Invitation:
        invitation.key = invitation.key or f"inv-{len(self.stored) + 1}"
        self.stored[invitation.key] = invitation
        return invitation

    def get_by_key(self, key: str) -> Invitation | None:
        return self.stored.get(key)

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        return next((i for i in self.stored.values() if i.token_hash == token_hash), None)

    def list_by_tenant(self, tenant_key: str) -> list[Invitation]:
        return [i for i in self.stored.values() if i.tenant_key == tenant_key]

    def update_fields(self, key: str, fields: dict[str, Any]) -> Invitation | None:
        current = self.stored.get(key)
        if current is None:
            return None
        for field in fields:
            if field not in Invitation.model_fields:
                raise AttributeError(f"'{field}' is not a field of Invitation")
        merged = Invitation.model_validate({**current.model_dump(by_alias=True), **fields})
        self.stored[key] = merged
        return merged

    def mark_accepted_if_pending(self, key: str, fields: dict[str, Any]) -> Invitation | None:
        """The real conditional write: only from ``pending``."""
        current = self.stored.get(key)
        if current is None or current.status != InvitationStatus.PENDING:
            return None
        return self.update_fields(key, {**fields, "status": InvitationStatus.ACCEPTED})

    def revoke_pending_for_tenant(self, tenant_key: str) -> int:
        """The real statement: one UPDATE over the tenant's ``pending`` invitations."""
        hit = [i for i in self.stored.values() if i.tenant_key == tenant_key and i.status == InvitationStatus.PENDING]
        for invitation in hit:
            invitation.status = InvitationStatus.REVOKED
        return len(hit)


class FakeMembershipRepo:
    """In-memory :class:`IMembershipRepository` — the part the join and the erasure decision use.

    ``active_member_user_keys`` applies the real predicate: an active
    membership of an **active account** (``inactive_accounts`` models the
    account an erasure request closed). ``before_create`` runs immediately
    before the insert lands — the point a concurrent writer can slip into.
    """

    def __init__(self, *memberships: Membership, inactive_accounts: set[str] | None = None) -> None:
        self.stored: dict[str, Membership] = {}
        self.inactive_accounts = set(inactive_accounts or ())
        self.before_create: Callable[[], None] | None = None
        for membership in memberships:
            self.create(membership)

    def create(self, membership: Membership) -> Membership:
        if self.before_create is not None:
            hook, self.before_create = self.before_create, None
            hook()
        membership.key = membership.key or f"m-{len(self.stored) + 1}"
        self.stored[membership.key] = membership
        return membership

    def delete(self, key: str) -> bool:
        return self.stored.pop(key, None) is not None

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        return next((m for m in self.stored.values() if (m.user_key, m.tenant_key) == (user_key, tenant_key)), None)

    def active_member_user_keys(self, *, tenant_key: str) -> list[str]:
        return sorted(
            {
                m.user_key
                for m in self.stored.values()
                if m.tenant_key == tenant_key and m.is_active and m.user_key not in self.inactive_accounts
            }
        )

    def deactivate_all_for_tenant(self, tenant_key: str) -> int:
        hit = [m for m in self.stored.values() if m.tenant_key == tenant_key and m.is_active]
        for membership in hit:
            membership.is_active = False
        return len(hit)


class HookedTenantErasureRepo(FakeTenantErasureRepository):
    """The shared faithful double, plus ``after_insert``: runs right after a record landed.

    That is the window between the freeze and whatever the service does next.
    """

    def __init__(self) -> None:
        super().__init__()
        self.after_insert: Callable[[], None] | None = None

    def create_with_key(self, record: TenantErasureRecord, key: str) -> TenantErasureRecord:
        created = super().create_with_key(record, key)
        if self.after_insert is not None:
            hook, self.after_insert = self.after_insert, None
            hook()
        return created


def _personal_tenant(key: str = PERSONAL, owner: str = OWNER) -> Tenant:
    return Tenant(_key=key, name="Garden", slug=f"garden-{key}", tenant_type=TenantType.PERSONAL, owner_user_key=owner)


def _member(user_key: str, tenant_key: str = PERSONAL) -> Membership:
    return Membership(user_key=user_key, tenant_key=tenant_key, role=TenantRole.GROWER, is_active=True)


class Tenants:
    """A real :class:`TenantService` over the doubles; the erasure run itself is recorded, not executed."""

    def __init__(self, *tenants: Tenant, members: list[Membership] | None = None) -> None:
        self.tenant_repo = FakeTenantRepo(*(tenants or (_personal_tenant(),)))
        self.memberships = FakeMembershipRepo(*(members if members is not None else [_member(OWNER)]))
        self.invitations = FakeInvitationRepo()
        self.records = HookedTenantErasureRepo()
        self.runs: list[str] = []
        self.service = TenantService(
            tenant_repo=self.tenant_repo,  # type: ignore[arg-type]
            membership_repo=self.memberships,  # type: ignore[arg-type]
            invitation_repo=self.invitations,  # type: ignore[arg-type]
            assignment_repo=MagicMock(),
            tenant_engine=MagicMock(),
            membership_engine=MagicMock(),
            invitation_engine=InvitationEngine(),
            tenant_erasure_executor=MagicMock(),
            tenant_erasure_repo=self.records,  # type: ignore[arg-type]
            observation_repo=MagicMock(),
            tombstone_salt=SALT,
        )

        def _run(record: TenantErasureRecord, now: datetime, *, raise_on_failure: bool) -> TenantErasureRecord:
            self.runs.append(record.tenant_key)
            record.status = "completed"
            return record

        self.service._run_tenant_erasure = _run  # type: ignore[method-assign]

    def invite(self, tenant_key: str = PERSONAL, *, by_link: bool = True) -> str:
        """An invitation created through the service; returns the raw token the invitee holds."""
        link = (
            self.service.create_link_invitation(tenant_key, OWNER)
            if by_link
            else self.service.create_email_invitation(tenant_key, OWNER, "friend@example.org")
        )
        return link.token

    def open_record(self, tenant_key: str = PERSONAL) -> None:
        FakeTenantErasureRepository.create_with_key(
            self.records,
            TenantErasureRecord(
                tenant_key=tenant_key, tenant_type="personal", origin="account_erasure", requested_at=NOW
            ),
            TenantErasureEngine.record_key(tenant_key),
        )


def _privacy(
    tenants: Tenants | None,
    erasure_repo: Any,
    *,
    executor: Any = "default",
    user_repo: MagicMock | None = None,
) -> tuple[PrivacyService, MagicMock]:
    password_engine = PasswordEngine()
    owner = User(
        _key=OWNER,
        email=OWNER_EMAIL,
        display_name="Owner",
        password_hash=password_engine.hash_password(OWNER_PASSWORD),
        email_verified=True,
        is_active=True,
    )
    if user_repo is None:
        user_repo = MagicMock()
        user_repo.get_by_key.return_value = owner
        wire_get_or_raise(user_repo, "User")
    export_repo = MagicMock()
    export_repo.list_by_user.return_value = []
    service = PrivacyService(
        export_repo=export_repo,
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=erasure_repo,
        email_change_repo=MagicMock(),
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=password_engine,
        token_engine=TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=RecordingErasureExecutor() if executor == "default" else executor,
        tenant_service=tenants.service if tenants is not None else None,
        tombstone_salt=SALT,
    )
    return service, user_repo


# ── AK-IE-06 ───────────────────────────────────────────────────────


class TestInvitationsAreRevokedWhenTheErasureIsRequested:
    def test_a_self_service_request_revokes_link_and_email_invitations_into_the_personal_tenant(self):
        tenants = Tenants()
        link_token = tenants.invite(by_link=True)
        email_token = tenants.invite(by_link=False)
        privacy, _ = _privacy(tenants, FakeErasureRepo())

        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert {i.invitation_type for i in tenants.invitations.stored.values()} == {
            InvitationType.LINK,
            InvitationType.EMAIL,
        }
        assert [i.status for i in tenants.invitations.stored.values()] == [InvitationStatus.REVOKED] * 2
        # Through the token, as the route does — during the grace, no tenant-erasure record exists yet.
        assert tenants.records.records == {}
        for token in (link_token, email_token):
            with pytest.raises(ValidationError, match="no longer pending"):
                tenants.service.accept_invitation(token, JOINER)
        assert tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL) is None

    @pytest.mark.asyncio
    async def test_an_immediate_erasure_revokes_them_before_the_tenant_decision(self):
        tenants = Tenants()
        token = tenants.invite()
        seen: list[InvitationStatus] = []
        inner = tenants.service.erase_personal_tenant_of

        def _erase(user_key: str, tenant_key: str, *, now: datetime | None = None) -> Any:
            seen.extend(i.status for i in tenants.invitations.stored.values())
            return inner(user_key, tenant_key, now=now)

        tenants.service.erase_personal_tenant_of = _erase  # type: ignore[method-assign]
        privacy, user_repo = _privacy(tenants, FakeErasureRepo())
        user_repo.get_by_key.return_value = None  # the account plan removed it

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        assert seen == [InvitationStatus.REVOKED], "revoked at request time, not by the tenant erasure"
        with pytest.raises((ValidationError, ForbiddenError)):
            tenants.service.accept_invitation(token, JOINER)

    def test_only_pending_invitations_into_the_subjects_personal_tenants_are_touched(self):
        club = Tenant(_key=SHARED, name="Club", slug="club", tenant_type=TenantType.ORGANIZATION, owner_user_key=OWNER)
        tenants = Tenants(_personal_tenant(), club, _personal_tenant("t-other", owner="u-else"))
        tenants.invite(PERSONAL)
        accepted_token = tenants.invite(PERSONAL)
        tenants.service.accept_invitation(accepted_token, "u-early")
        club_token = tenants.invite(SHARED)
        foreign_token = tenants.invite("t-other")

        revoked = tenants.service.revoke_invitations_into_personal_tenants_of(OWNER)

        assert revoked == 1
        by_tenant = {(i.tenant_key, i.status) for i in tenants.invitations.stored.values()}
        assert by_tenant == {
            (PERSONAL, InvitationStatus.REVOKED),
            (PERSONAL, InvitationStatus.ACCEPTED),
            (SHARED, InvitationStatus.PENDING),
            ("t-other", InvitationStatus.PENDING),
        }
        assert tenants.service.accept_invitation(club_token, JOINER).tenant_key == SHARED
        assert tenants.service.accept_invitation(foreign_token, JOINER).tenant_key == "t-other"

    def test_the_hard_delete_revokes_again_as_a_backstop(self):
        """An invitation created during the grace (by another manager) is void before the decision."""
        tenants = Tenants()
        tenants.memberships.inactive_accounts.add(OWNER)
        token = tenants.invite()

        outcome = tenants.service.erase_personal_tenant_of(OWNER, PERSONAL, now=NOW)

        assert outcome.outcome == "erased"
        assert [i.status for i in tenants.invitations.stored.values()] == [InvitationStatus.REVOKED]
        assert token


# ── AK-IE-07 (a) ───────────────────────────────────────────────────


class TestTheMembershipIsRecheckedAfterTheFreeze:
    def test_a_join_between_the_first_check_and_the_record_insert_keeps_the_tenant(self):
        tenants = Tenants()
        tenants.memberships.inactive_accounts.add(OWNER)
        tenants.records.after_insert = lambda: tenants.memberships.create(_member(JOINER))

        outcome = tenants.service.erase_personal_tenant_of(OWNER, PERSONAL, now=NOW)

        assert outcome.outcome == "retained_other_members"
        assert tenants.runs == [], "the tenant inventory ran over a tenant someone had just joined"
        joined = tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL)
        assert joined is not None and joined.is_active, "the late joiner was silently deactivated"
        assert tenants.records.get(TenantErasureEngine.record_key(PERSONAL)) is None, (
            "the withdrawn deletion must not keep the tenant frozen or be resumed by the beat"
        )

    def test_without_a_late_join_the_tenant_is_erased_as_before(self):
        tenants = Tenants()
        tenants.memberships.inactive_accounts.add(OWNER)

        outcome = tenants.service.erase_personal_tenant_of(OWNER, PERSONAL, now=NOW)

        assert outcome.outcome == "erased"
        assert tenants.runs == [PERSONAL]
        owner = tenants.memberships.get_by_user_and_tenant(OWNER, PERSONAL)
        assert owner is not None and not owner.is_active

    def test_a_retry_over_a_record_no_run_claimed_rechecks_too(self):
        """A crash between the insert and the re-check left the record; the joiner of that window is still seen."""
        tenants = Tenants(members=[_member(OWNER), _member(JOINER)])
        tenants.memberships.inactive_accounts.add(OWNER)
        tenants.open_record()

        outcome = tenants.service.erase_personal_tenant_of(OWNER, PERSONAL, now=NOW)

        assert outcome.outcome == "retained_other_members"
        assert tenants.runs == []

    def test_a_claimed_deletion_is_resumed_whatever_the_frozen_memberships_say(self):
        tenants = Tenants(members=[_member(OWNER), _member(JOINER)])
        tenants.open_record()
        tenants.records.update_fields(
            TenantErasureEngine.record_key(PERSONAL),
            {"status": "partially_completed", "last_attempt_at": (NOW - timedelta(days=1)).isoformat()},
        )

        outcome = tenants.service.erase_personal_tenant_of(OWNER, PERSONAL, now=NOW)

        assert outcome.outcome == "erased"
        assert tenants.runs == [PERSONAL]


# ── AK-IE-07 (b) ───────────────────────────────────────────────────


class TestAJoinIntoAFreezingTenantIsRolledBack:
    def test_a_record_inserted_between_the_check_and_the_membership_insert_refuses_the_join(self):
        tenants = Tenants()
        token = tenants.invite()
        tenants.memberships.before_create = tenants.open_record

        with pytest.raises(ForbiddenError, match="being deleted"):
            tenants.service.accept_invitation(token, JOINER)

        assert tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL) is None, (
            "an active membership was left in a tenant that is being erased"
        )
        (invitation,) = tenants.invitations.stored.values()
        assert invitation.status == InvitationStatus.PENDING, "a refused join must not consume the invitation"

    def test_a_join_without_a_deletion_still_lands(self):
        tenants = Tenants()
        token = tenants.invite()

        membership = tenants.service.accept_invitation(token, JOINER)

        assert membership.is_active
        assert tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL) is not None


# ── #1843 ──────────────────────────────────────────────────────────


class InterleavedErasureRepo(FakeErasureRepo):
    """Both callers finish their "is one open?" read before either writes — the #1843 interleave.

    Inserts are serialised as the database serialises them; the auto-key insert
    hands out distinct keys (as ArangoDB does), the keyed insert refuses the
    second one (as the primary key does).
    """

    def __init__(self) -> None:
        super().__init__()
        self._both_read = threading.Barrier(2, timeout=10)
        self._write = threading.Lock()

    def find_active_for_user(self, user_key: str) -> Any:
        found = super().find_active_for_user(user_key)
        self._both_read.wait()
        return found

    def create(self, erasure: Any) -> Any:
        with self._write:
            return super().create(erasure)

    def create_with_key(self, erasure: Any, key: str) -> Any:
        with self._write:
            return super().create_with_key(erasure, key)


class TestOneOpenRecordPerAccount:
    def test_two_interleaved_requests_leave_one_open_record(self):
        tenants = Tenants()
        repo = InterleavedErasureRepo()
        privacy, _ = _privacy(tenants, repo)
        results: list[Any] = []
        errors: list[BaseException] = []

        def _request() -> None:
            try:
                results.append(privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD)))
            except BaseException as exc:  # noqa: BLE001 - reported below
                errors.append(exc)

        threads = [threading.Thread(target=_request) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert not errors, errors
        open_records = [r for r in repo.stored.values() if r.user_key == OWNER and r.status != "completed"]
        assert len(open_records) == 1, f"{len(open_records)} open erasure records for one account"
        assert {r.key for r in results} == {open_records[0].key}, "the second caller is answered with the same request"

    def test_a_request_after_an_open_one_is_still_refused(self):
        tenants = Tenants()
        repo = FakeErasureRepo()
        privacy, _ = _privacy(tenants, repo)
        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        with pytest.raises(ValidationError):
            privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))
        assert len(repo.stored) == 1


class TestADeploymentThatCannotEraseRefusesUpFront:
    @pytest.mark.parametrize(
        "broken",
        ["no_executor", "no_tenant_service"],
    )
    def test_nothing_is_written_and_the_account_stays_open(self, broken: str):
        tenants = Tenants()
        tenants.invite()
        repo = FakeErasureRepo()
        privacy, user_repo = _privacy(
            tenants if broken != "no_tenant_service" else None,
            repo,
            executor=None if broken == "no_executor" else "default",
        )
        privacy._step_up_verifier = MagicMock()

        with pytest.raises(FeatureNotConfiguredError) as refused:
            privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert refused.value.status_code == 503
        assert refused.value.error_code == "FEATURE_NOT_CONFIGURED"
        assert repo.stored == {}
        user_repo.update_fields.assert_not_called()
        privacy._refresh_token_repo.revoke_all_for_user.assert_not_called()
        privacy._step_up_verifier.verify.assert_not_called()
        assert [i.status for i in tenants.invitations.stored.values()] == [InvitationStatus.PENDING]


# ── security-review follow-ups (pre-PR) ────────────────────────────


class TestARevocationRacingAnAcceptWins:
    def test_an_invitation_revoked_between_the_read_and_the_membership_insert_is_not_accepted(self):
        """SEC-001: the request-time revocation lands while an accept is already past its status check."""
        tenants = Tenants()
        token = tenants.invite()
        tenants.memberships.before_create = lambda: tenants.invitations.revoke_pending_for_tenant(PERSONAL)

        with pytest.raises(ValidationError, match="no longer pending"):
            tenants.service.accept_invitation(token, JOINER)

        assert tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL) is None
        (invitation,) = tenants.invitations.stored.values()
        assert invitation.status == InvitationStatus.REVOKED, "the revocation was overwritten with accepted"


class TestTheDailyTenantBeatLeavesTheRecheckToTheAccountErasure:
    def test_an_unclaimed_account_erasure_record_is_not_run_by_the_beat(self):
        """SEC-003: a record whose account erasure stopped before its re-check is not erased blind."""
        tenants = Tenants(members=[_member(OWNER), _member(JOINER)])
        tenants.memberships.inactive_accounts.add(OWNER)
        tenants.open_record()

        result = tenants.service.resume_tenant_erasures(NOW + timedelta(days=2))

        assert tenants.runs == []
        joined = tenants.memberships.get_by_user_and_tenant(JOINER, PERSONAL)
        assert joined is not None and joined.is_active
        assert result["candidates"] == 1


class TestARepeatedRequestRevokesAgain:
    def test_a_request_refused_as_already_in_progress_still_revokes(self):
        """SEC-004: a failed request-time revocation is repeated when the subject asks again."""
        tenants = Tenants()
        repo = FakeErasureRepo()
        privacy, _ = _privacy(tenants, repo)
        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))
        tenants.invite()  # e.g. one the first revocation missed

        with pytest.raises(ValidationError):
            privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert [i.status for i in tenants.invitations.stored.values()] == [InvitationStatus.REVOKED]
