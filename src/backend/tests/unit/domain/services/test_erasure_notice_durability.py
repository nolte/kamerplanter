"""#1960 — the notice to the other members of a personal tenant is durable.

REQ-025 §3.1.3, NFR-011 AK-PT-03, each through the production entries over the
real :class:`TenantService` and the in-memory repositories of
``test_erasure_invitations_and_late_join``:

* a request scheduled before #1824 carries no marker: the daily beat sends the
  notice when it first sees it, and the hard delete waits a grace interval
  after it instead of erasing at once;
* a notice that failed is retried by the beat before the hard delete, and the
  request records that (value-free counter, no address);
* a request that was told at request time is not told again and is not delayed.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from app.domain.models.privacy import ErasureRequest
from tests.support.privacy_doubles import FakeErasureRepo, step_up
from tests.unit.domain.services.test_erasure_invitations_and_late_join import (  # noqa: F401 - the autouse salt fixture
    FRIEND,
    NOW,
    OWNER,
    OWNER_EMAIL,
    OWNER_PASSWORD,
    PERSONAL,
    Tenants,
    _log_pseudonym_salt,
    _member,
    _privacy,
)
from tests.unit.domain.services.test_erasure_together_notice_and_preview import (
    FRIEND_EMAIL,
    OTHER,
    OTHER_EMAIL,
    _sent,
    _users,
)

WAIT = timedelta(days=7)


def _legacy_request(*, due: Any = None) -> ErasureRequest:
    """A scheduled self-service request as it was stored before #1960: no notice marker at all."""
    return ErasureRequest(
        user_key=OWNER,
        status="scheduled",
        origin="self_service",
        requested_at=NOW - timedelta(days=91),
        soft_deleted_at=NOW - timedelta(days=91),
        hard_delete_scheduled_at=due if due is not None else NOW - timedelta(days=1),
    )


def _legacy_shared() -> tuple[Tenants, Any, Any, FakeErasureRepo]:
    tenants = Tenants(members=[_member(OWNER), _member(FRIEND), _member(OTHER)])
    repo = FakeErasureRepo(_legacy_request())
    privacy, _ = _privacy(tenants, repo, user_repo=_users((FRIEND, FRIEND_EMAIL), (OTHER, OTHER_EMAIL)))
    return tenants, privacy, privacy._email_service, repo


class TestARequestWithoutMarkerIsToldFirstAndDeletedLater:
    @pytest.mark.asyncio
    async def test_the_beat_does_not_erase_a_shared_personal_tenant_it_has_not_told_anybody_about(self):
        tenants, privacy, email_service, repo = _legacy_shared()

        await privacy.execute_scheduled_erasures(NOW)

        assert tenants.runs == [], "the tenant of a marker-less request was erased in the run that first saw it"
        assert sorted(m["to_email"] for m in _sent(email_service)) == [FRIEND_EMAIL, OTHER_EMAIL]
        # The marker is on the record, with the recipient count, and carries no address.
        (stored,) = repo.stored.values()
        assert stored.members_notified_at == NOW and stored.members_notified_count == 2
        assert not any(leak in repr(stored.model_dump()) for leak in (FRIEND, OTHER, FRIEND_EMAIL, OTHER_EMAIL))

    @pytest.mark.asyncio
    async def test_the_hard_delete_runs_one_grace_interval_after_the_notice_and_not_before(self):
        tenants, privacy, email_service, _ = _legacy_shared()
        await privacy.execute_scheduled_erasures(NOW)

        await privacy.execute_scheduled_erasures(NOW + WAIT - timedelta(hours=2))
        assert tenants.runs == [], "erased before the members had their interval"
        assert len(_sent(email_service)) == 2, "the held request must not be mailed again"

        finalised = await privacy.execute_scheduled_erasures(NOW + WAIT + timedelta(hours=2))
        assert tenants.runs == [PERSONAL] and finalised == 1

    @pytest.mark.asyncio
    async def test_the_notice_names_the_date_the_garden_goes_when_the_due_date_already_passed(self):
        _, privacy, email_service, _ = _legacy_shared()

        await privacy.execute_scheduled_erasures(NOW)

        expected = (NOW + WAIT).strftime("%Y-%m-%d")
        assert all(expected in mail["html_body"] for mail in _sent(email_service))

    @pytest.mark.asyncio
    async def test_a_request_still_in_its_grace_is_told_at_once_and_erased_on_its_own_date(self):
        tenants = Tenants(members=[_member(OWNER), _member(FRIEND)])
        due = NOW + timedelta(days=40)
        repo = FakeErasureRepo(_legacy_request(due=due))
        privacy, _ = _privacy(tenants, repo, user_repo=_users((FRIEND, FRIEND_EMAIL)))

        await privacy.execute_scheduled_erasures(NOW)
        assert [m["to_email"] for m in _sent(privacy._email_service)] == [FRIEND_EMAIL]
        assert due.strftime("%Y-%m-%d") in _sent(privacy._email_service)[0]["html_body"]
        assert tenants.runs == []

        await privacy.execute_scheduled_erasures(due + timedelta(hours=1))
        assert tenants.runs == [PERSONAL], "told long ago: no extra wait on top of the grace"

    @pytest.mark.asyncio
    async def test_a_marker_less_request_nobody_shares_with_is_erased_without_a_wait(self):
        tenants = Tenants()
        privacy, _ = _privacy(tenants, FakeErasureRepo(_legacy_request()), user_repo=_users())

        finalised = await privacy.execute_scheduled_erasures(NOW)

        assert finalised == 1 and tenants.runs == [PERSONAL]
        assert _sent(privacy._email_service) == []


class TestAFailingMailIsVisibleAndRetriedBeforeTheHardDelete:
    @pytest.mark.asyncio
    async def test_the_failure_is_counted_on_the_request_and_retried_by_the_next_run(self):
        tenants, privacy, email_service, repo = _legacy_shared()
        email_service.send_notification_email.side_effect = RuntimeError("smtp down")

        await privacy.execute_scheduled_erasures(NOW)

        (stored,) = repo.stored.values()
        assert stored.members_notified_at is None and stored.members_notice_failures == 1
        assert stored.members_notice_first_attempt_at == NOW
        assert tenants.runs == []

        email_service.send_notification_email.side_effect = None
        await privacy.execute_scheduled_erasures(NOW + timedelta(days=1))
        assert stored.members_notified_at == NOW + timedelta(days=1) and stored.members_notified_count == 2
        assert tenants.runs == [], "told only now: the interval counts from that notice"

    @pytest.mark.asyncio
    async def test_a_retry_does_not_mail_the_members_who_already_got_the_notice(self):
        tenants, privacy, email_service, repo = _legacy_shared()
        calls = {"n": 0}

        def _flaky(**kwargs: Any) -> None:
            calls["n"] += 1
            if kwargs["to_email"] == OTHER_EMAIL and calls["n"] <= 2:
                raise RuntimeError("mailbox full")

        email_service.send_notification_email.side_effect = _flaky
        await privacy.execute_scheduled_erasures(NOW)
        await privacy.execute_scheduled_erasures(NOW + timedelta(days=1))

        to = [mail["to_email"] for mail in _sent(email_service)]
        assert sorted(to) == [FRIEND_EMAIL, OTHER_EMAIL, OTHER_EMAIL], "FRIEND must be mailed once, OTHER retried"
        (stored,) = repo.stored.values()
        assert stored.members_notified_count == 2

    @pytest.mark.asyncio
    async def test_the_failure_log_carries_no_address(self):
        _, privacy, email_service, _ = _legacy_shared()
        email_service.send_notification_email.side_effect = RuntimeError("smtp down")

        with capture_logs() as logs:
            await privacy.execute_scheduled_erasures(NOW)

        failures = [entry for entry in logs if entry["event"] == "personal_tenant_erasure_notice_failed"]
        assert failures, "a failing mail must be visible to the operator"
        assert not any(leak in repr(logs) for leak in (FRIEND_EMAIL, OTHER_EMAIL, OWNER_EMAIL, FRIEND, OTHER))

    @pytest.mark.asyncio
    async def test_a_notice_that_never_gets_through_does_not_hold_the_erasure_for_ever(self):
        tenants, privacy, email_service, _ = _legacy_shared()
        email_service.send_notification_email.side_effect = NotImplementedError
        await privacy.execute_scheduled_erasures(NOW)
        await privacy.execute_scheduled_erasures(NOW + WAIT - timedelta(hours=2))
        assert tenants.runs == []

        finalised = await privacy.execute_scheduled_erasures(NOW + WAIT + timedelta(hours=1))

        assert finalised == 1 and tenants.runs == [PERSONAL]

    def test_a_failure_at_request_time_is_recorded_on_the_request(self):
        tenants, privacy, email_service = _fresh()
        email_service.send_notification_email.side_effect = RuntimeError("smtp down")

        erasure = privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        assert erasure.members_notified_at is None and erasure.members_notice_failures == 1
        assert privacy._erasure_repo.stored[erasure.key].members_notice_failures == 1


def _fresh() -> tuple[Tenants, Any, Any]:
    tenants = Tenants(members=[_member(OWNER), _member(FRIEND)])
    privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users((FRIEND, FRIEND_EMAIL)))
    return tenants, privacy, privacy._email_service


class TestTheCompletedRecordKeepsNoPseudonymOfAMember:
    @pytest.mark.asyncio
    async def test_the_member_references_are_dropped_once_everybody_is_told_and_the_count_stays(self):
        tenants, privacy, _, repo = _legacy_shared()
        await privacy.execute_scheduled_erasures(NOW)
        (stored,) = repo.stored.values()
        assert stored.members_notified_pseudonyms == [], "told: the retry aid is not kept"

        await privacy.execute_scheduled_erasures(NOW + WAIT + timedelta(hours=1))

        assert stored.status == "completed" and tenants.runs == [PERSONAL]
        assert stored.members_notified_pseudonyms == [] and stored.members_notified_count == 2


class TestARequestToldAtRequestTimeIsNotDelayed:
    @pytest.mark.asyncio
    async def test_the_marker_is_written_and_the_hard_delete_stays_on_its_own_date(self):
        tenants, privacy, email_service = _fresh()
        erasure = privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))
        assert erasure.members_notified_at is not None and erasure.members_notified_count == 1
        due = erasure.hard_delete_scheduled_at
        assert due is not None

        await privacy.execute_scheduled_erasures(due - timedelta(days=1))
        assert tenants.runs == []
        await privacy.execute_scheduled_erasures(due + timedelta(hours=1))

        assert tenants.runs == [PERSONAL]
        assert len(_sent(email_service)) == 1, "told at request time, not again by the beat"


class TestAnAdministratorsErasureWaitsForNobody:
    @pytest.mark.asyncio
    async def test_a_marker_less_request_pulled_forward_tells_them_it_happens_now_and_erases_at_once(self):
        tenants, privacy, email_service, _ = _legacy_shared()

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        assert tenants.runs == [PERSONAL]
        assert len(_sent(email_service)) == 2 and all("no grace period" in m["html_body"] for m in _sent(email_service))

    @pytest.mark.asyncio
    async def test_a_request_told_a_later_date_is_told_again_when_an_administrator_pulls_it_forward(self):
        tenants, privacy, email_service = _fresh()
        privacy.request_erasure(OWNER, **step_up(OWNER_EMAIL, OWNER_PASSWORD))

        await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)

        bodies = [m["html_body"] for m in _sent(email_service)]
        assert len(bodies) == 2 and "no grace period" in bodies[1]

    @pytest.mark.asyncio
    async def test_the_beats_retry_of_a_failed_administrator_run_is_not_held_for_the_notice_wait(self):
        tenants, privacy, email_service, repo = _legacy_shared()
        failing = {"on": True}
        inner = tenants.service.erase_personal_tenant_of

        def _erase(user_key: str, tenant_key: str, **kwargs: Any) -> Any:
            if failing["on"]:
                raise RuntimeError("tenant erasure down")
            return inner(user_key, tenant_key, **kwargs)

        tenants.service.erase_personal_tenant_of = _erase  # type: ignore[method-assign]
        with pytest.raises(RuntimeError):
            await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)
        failing["on"] = False

        finalised = await privacy.execute_scheduled_erasures(NOW + timedelta(days=2))

        assert finalised == 1 and tenants.runs == [PERSONAL]


class TestNoStateHoldsAnErasureForEver:
    @pytest.mark.asyncio
    async def test_a_stale_in_progress_request_without_marker_is_told_and_then_erased_one_wait_later(self):
        """A crashed worker's pre-#1960 run is selected by the due list; the notice pass must reach it too."""
        tenants = Tenants(members=[_member(OWNER), _member(FRIEND)])
        stale = _legacy_request()
        stale.status = "in_progress"
        stale.updated_at = NOW - timedelta(days=2)
        repo = FakeErasureRepo(stale)
        privacy, _ = _privacy(tenants, repo, user_repo=_users((FRIEND, FRIEND_EMAIL)))

        await privacy.execute_scheduled_erasures(NOW)
        assert tenants.runs == [] and len(_sent(privacy._email_service)) == 1

        finalised = await privacy.execute_scheduled_erasures(NOW + WAIT + timedelta(hours=1))

        assert finalised == 1 and tenants.runs == [PERSONAL]

    @pytest.mark.asyncio
    async def test_a_failing_notice_query_neither_stops_the_beat_nor_erases_a_never_told_garden(self):
        tenants, privacy, email_service, repo = _legacy_shared()

        def _boom() -> list[ErasureRequest]:
            raise RuntimeError("aql down")

        repo.list_open_without_member_notice = _boom  # type: ignore[method-assign]

        await privacy.execute_scheduled_erasures(NOW)
        assert tenants.runs == [] and _sent(email_service) == []
        (stored,) = repo.stored.values()
        assert stored.members_notice_first_attempt_at == NOW and stored.members_notice_failures == 1

        finalised = await privacy.execute_scheduled_erasures(NOW + WAIT + timedelta(hours=1))
        assert finalised == 1 and tenants.runs == [PERSONAL], "bounded: the query never came back for a whole wait"

    @pytest.mark.asyncio
    async def test_an_unexpected_error_for_one_request_does_not_let_it_be_erased_unattempted(self):
        tenants, privacy, _, repo = _legacy_shared()
        privacy._deliver_member_notice = MagicMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]

        await privacy.execute_scheduled_erasures(NOW)

        assert tenants.runs == []
        (stored,) = repo.stored.values()
        assert stored.members_notice_first_attempt_at == NOW


class TestAnAdministratorRunThatFailsBeforeTheNoticeIsStillTold:
    @pytest.mark.asyncio
    async def test_the_beat_does_not_erase_without_a_word_after_a_failure_before_the_notice(self):
        tenants, privacy, email_service, repo = _legacy_shared()
        calls = {"n": 0}
        original = privacy._revoke_personal_tenant_invitations

        def _fail_once(user_key: str) -> None:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient")
            original(user_key)

        privacy._revoke_personal_tenant_invitations = _fail_once  # type: ignore[method-assign]
        with pytest.raises(RuntimeError):
            await privacy.erase_account_now(OWNER, origin="platform_admin", now=NOW)
        assert _sent(email_service) == []

        await privacy.execute_scheduled_erasures(NOW + timedelta(hours=1))

        assert tenants.runs == [], "nobody was told yet: the beat tells them and holds the garden"
        assert len(_sent(email_service)) == 2
