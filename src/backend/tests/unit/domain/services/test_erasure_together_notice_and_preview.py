"""#1824 — erasure together: the notice to the other members and the preview before confirming.

REQ-025 §3.1.3 (Q-E1/Q-E5), NFR-011 AK-PT-03 and AK-FK-06, each through the
production entries (``PrivacyService.request_erasure`` / ``erase_account_now`` /
``erasure_preview``) over the real :class:`TenantService` and the in-memory
repositories of ``test_erasure_invitations_and_late_join`` (which refuse what the
real ones refuse):

* the other active members of a personal tenant are mailed **when the erasure is
  requested** — with the grace still ahead — and the mail names neither the
  subject nor their garden;
* a mail that cannot be sent never keeps the subject from erasing;
* the personal tenant goes with the account whoever else is a member;
* the preview lists the caller's personal tenants with a count of the others,
  and nothing about who they are.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.domain.models.user import User
from tests.conftest import wire_get_or_raise
from tests.support.privacy_doubles import FakeErasureRepo, step_up
from tests.unit.domain.services.test_erasure_invitations_and_late_join import (  # noqa: F401 - the autouse salt fixture
    FRIEND,
    NOW,
    OWNER,
    OWNER_EMAIL,
    OWNER_PASSWORD,
    PERSONAL,
    PasswordEngine,
    Tenants,
    _log_pseudonym_salt,
    _member,
    _personal_tenant,
    _privacy,
)

FRIEND_EMAIL = "friend@example.org"
OTHER, OTHER_EMAIL = "u-other", "other@example.org"


def _users(*extra: tuple[str, str]) -> MagicMock:
    """A user repository that knows the owner and *extra* ``(key, email)`` accounts."""
    password_engine = PasswordEngine()
    accounts = {
        OWNER: User(
            _key=OWNER,
            email=OWNER_EMAIL,
            display_name="Ada Owner",
            password_hash=password_engine.hash_password(OWNER_PASSWORD),
            email_verified=True,
            is_active=True,
        )
    }
    for key, email in extra:
        accounts[key] = User(_key=key, email=email, display_name=key, email_verified=True, is_active=True)
    repo = MagicMock()
    repo.get_by_key.side_effect = accounts.get
    wire_get_or_raise(repo, "User")
    return repo


def _shared() -> tuple[Tenants, Any, MagicMock]:
    """A personal tenant of OWNER with two other members, and the privacy service over it."""
    tenants = Tenants(members=[_member(OWNER), _member(FRIEND), _member(OTHER)])
    user_repo = _users((FRIEND, FRIEND_EMAIL), (OTHER, OTHER_EMAIL))
    privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=user_repo)
    return tenants, privacy, privacy._email_service


def _sent(email_service: MagicMock) -> list[dict[str, Any]]:
    return [call.kwargs for call in email_service.send_notification_email.call_args_list]


class TestTheOtherMembersAreToldWhenTheErasureIsRequested:
    def test_every_other_member_is_mailed_once_before_anything_is_deleted(self):
        tenants, privacy, email_service = _shared()

        erasure = privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert sorted(mail["to_email"] for mail in _sent(email_service)) == [FRIEND_EMAIL, OTHER_EMAIL]
        assert tenants.runs == [], "the tenant must still exist when the members are told"
        due = erasure.hard_delete_scheduled_at
        assert due is not None
        assert all(due.strftime("%Y-%m-%d") in mail["html_body"] for mail in _sent(email_service)), (
            "the notice must say when the garden goes, or there is nothing to act on"
        )

    def test_the_notice_names_neither_the_subject_nor_the_garden(self):
        _, privacy, email_service = _shared()

        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        for mail in _sent(email_service):
            text = mail["subject"] + mail["html_body"]
            # A personal tenant is named after its owner (create_personal_tenant), so its name identifies them.
            assert not any(leak in text for leak in (OWNER_EMAIL, "Ada Owner", "Garden", OWNER))

    def test_the_notice_does_not_offer_the_personal_export_as_a_way_to_keep_the_garden(self):
        """Garden data is not part of a member's personal data export (docs: privacy guide)."""
        _, privacy, email_service = _shared()

        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        body = _sent(email_service)[0]["html_body"]
        assert "not part of the personal data export" in body

    def test_a_subject_nobody_shares_with_sends_nothing(self):
        tenants = Tenants()
        privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users())

        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert _sent(privacy._email_service) == []

    def test_an_account_that_already_left_is_not_told(self):
        tenants = Tenants(members=[_member(OWNER), _member(FRIEND)])
        tenants.memberships.inactive_accounts.add(FRIEND)  # its own erasure closed it
        privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users((FRIEND, FRIEND_EMAIL)))

        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert _sent(privacy._email_service) == []

    def test_asking_again_does_not_mail_the_members_again(self):
        _, privacy, email_service = _shared()
        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        with pytest.raises(Exception, match="already in progress"):
            privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert len(_sent(email_service)) == 2

    def test_a_mail_that_cannot_be_sent_does_not_keep_the_subject_from_erasing(self):
        _, privacy, email_service = _shared()
        email_service.send_notification_email.side_effect = RuntimeError("smtp down")

        erasure = privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert erasure.status == "scheduled"
        assert email_service.send_notification_email.call_count == 2, "one failure must not skip the others"

    def test_two_concurrent_requests_mail_the_members_once(self):
        """#1824 review SEC-005 — only the call that created the request tells them."""
        _, privacy, email_service = _shared()
        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))
        duplicate = privacy._new_erasure_request(OWNER, now=NOW, hard_delete_at=NOW, origin="self_service")

        record, created_here = privacy._create_scheduled_request(OWNER, duplicate)

        assert created_here is False and record.key
        assert len(_sent(email_service)) == 2, "the second request created nothing and must not mail anyone"

    def test_a_failure_reading_the_members_does_not_fail_the_request(self):
        tenants, privacy, email_service = _shared()
        tenants.service.other_active_members_of_personal_tenants_of = MagicMock(side_effect=RuntimeError("db down"))

        erasure = privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert erasure.status == "scheduled"
        assert _sent(email_service) == []

    @pytest.mark.asyncio
    async def test_the_erasure_run_tells_the_tenant_decision_when_the_account_erasure_was_asked_for(self):
        tenants, privacy, _ = _shared()
        seen: list[Any] = []
        inner = tenants.service.erase_personal_tenant_of

        def _erase(user_key: str, tenant_key: str, **kwargs: Any) -> Any:
            seen.append(kwargs.get("requested_at"))
            return inner(user_key, tenant_key, **kwargs)

        tenants.service.erase_personal_tenant_of = _erase  # type: ignore[method-assign]

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        (stored,) = privacy._erasure_repo.stored.values()
        assert seen == [stored.requested_at] and seen[0] is not None

    @pytest.mark.asyncio
    async def test_an_immediate_erasure_tells_them_before_the_tenant_is_erased(self):
        tenants, privacy, email_service = _shared()
        mails_when_erased: list[int] = []
        inner = tenants.service.erase_personal_tenant_of

        def _erase(user_key: str, tenant_key: str, **kwargs: Any) -> Any:
            mails_when_erased.append(email_service.send_notification_email.call_count)
            return inner(user_key, tenant_key, **kwargs)

        tenants.service.erase_personal_tenant_of = _erase  # type: ignore[method-assign]

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        assert mails_when_erased == [2]

    @pytest.mark.asyncio
    async def test_an_immediate_erasure_does_not_promise_a_date_or_time_to_export(self):
        _, privacy, email_service = _shared()

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        body = _sent(email_service)[0]["html_body"]
        assert "no grace period" in body and "(UTC)" not in body

    @pytest.mark.asyncio
    async def test_the_cleanup_of_an_unverified_account_still_tells_the_members_of_its_garden(self):
        """#1992 — the cleanup used to skip the notice ("an unverified account never had a shared garden")."""
        tenants, privacy, email_service = _shared()
        privacy._user_repo.get_by_key.side_effect = lambda key: User(
            _key=key, email=f"{key}@example.org", display_name=key, email_verified=False, is_active=True
        )

        await privacy.erase_account_now(OWNER, origin="unverified_cleanup", now=NOW)

        assert len(_sent(email_service)) == 2, "both other members of the personal garden are told"
        (stored,) = privacy._erasure_repo.stored.values()
        assert stored.members_notified_count == 2

    @pytest.mark.asyncio
    async def test_the_cleanup_never_erases_an_account_an_admin_demoted(self):
        """#1992 — a verified account whose ``email_verified`` an admin lowered is not abandoned."""
        tenants, privacy, email_service = _shared()
        privacy._user_repo.get_by_key.side_effect = lambda key: User(
            _key=key,
            email=f"{key}@example.org",
            display_name=key,
            email_verified=False,
            email_verified_lowered_at=NOW,
            is_active=True,
        )

        result = await privacy.erase_account_now(OWNER, origin="unverified_cleanup", now=NOW)

        assert result is None
        assert tenants.runs == []
        assert _sent(email_service) == []
        assert not privacy._erasure_repo.stored


class TestThePersonalTenantGoesWithTheAccountWhoeverIsMember:
    @pytest.mark.asyncio
    async def test_the_shared_tenant_is_erased_and_the_request_says_so(self):
        tenants, privacy, _ = _shared()

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        assert tenants.runs == [PERSONAL]
        (stored,) = privacy._erasure_repo.stored.values()
        assert [(t.tenant_key, t.outcome) for t in stored.personal_tenants] == [(PERSONAL, "erased")]

    @pytest.mark.asyncio
    async def test_the_confirmation_text_no_longer_promises_a_garden_kept_for_other_members(self):
        _, privacy, _ = _shared()

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        (stored,) = privacy._erasure_repo.stored.values()
        assert "unless another active member" not in (stored.retained_reason or "")
        assert "also when other people are members" in (stored.retained_reason or "")


class TestThePreviewShowsWhatConfirmingWouldDelete:
    def test_it_lists_the_callers_personal_tenant_with_a_count_of_the_others(self):
        _, privacy, _ = _shared()

        preview = privacy.erasure_preview(OWNER)

        assert [(item.name, item.other_member_count) for item in preview] == [("Garden", 2)]

    def test_it_counts_only_active_accounts_and_never_the_subject(self):
        tenants = Tenants(members=[_member(OWNER), _member(FRIEND), _member(OTHER)])
        tenants.memberships.inactive_accounts.add(OTHER)
        privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users((FRIEND, FRIEND_EMAIL)))

        assert [i.other_member_count for i in privacy.erasure_preview(OWNER)] == [1]

    def test_a_tenant_of_somebody_else_is_not_listed(self):
        tenants = Tenants(_personal_tenant("t-foreign", owner="u-else"), members=[_member("u-else", "t-foreign")])
        privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users())

        assert privacy.erasure_preview(OWNER) == []

    def test_it_carries_no_identity_of_the_other_members(self):
        _, privacy, _ = _shared()

        shown = repr(privacy.erasure_preview(OWNER))

        assert not any(leak in shown for leak in (FRIEND, OTHER, FRIEND_EMAIL, OTHER_EMAIL))
