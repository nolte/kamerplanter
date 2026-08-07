"""The REQ-023 §3.2 notice: sent once per recipient per window, and never loudly.

Two failure modes are what this task exists to avoid, and both are asserted here
rather than left to the reader of the docstrings:

* **It must not be able to fail a request.** The dispatch helper swallows a
  broker outage; the task swallows a delivery failure. If either escaped, the
  duplicate branch would answer 500 where a genuine registration answers 201 —
  a sharper enumeration oracle than the one #957 closed.
* **It must not be able to run unbounded.** ``/auth/register`` is anonymous, so
  without the per-recipient window an attacker owns somebody else's inbox.
"""

from unittest.mock import MagicMock

import pytest
import structlog

from app.data_access.external.registration_notice_store import MemoryRegistrationNoticeStore
from app.domain.models.user import User
from app.tasks import auth_tasks

USER_KEY = "8271634"
RECIPIENT = "victim@example.com"


def _user(**overrides: object) -> User:
    defaults: dict = {
        "_key": USER_KEY,
        "email": RECIPIENT,
        "display_name": "Victim Realname",
        "locale": "de",
    }
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def email_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def store() -> MemoryRegistrationNoticeStore:
    return MemoryRegistrationNoticeStore()


@pytest.fixture
def wired(
    monkeypatch: pytest.MonkeyPatch,
    email_service: MagicMock,
    store: MemoryRegistrationNoticeStore,
) -> MagicMock:
    """Wire the task's three lazy dependencies to fakes; return the user repo."""
    user_repo = MagicMock()
    user_repo.get_by_key.return_value = _user()
    monkeypatch.setattr("app.common.dependencies.get_user_repo", lambda: user_repo)
    monkeypatch.setattr("app.common.dependencies.get_email_service", lambda: email_service)
    monkeypatch.setattr("app.common.dependencies.get_registration_notice_store", lambda: store)
    return user_repo


class TestSending:
    def test_sends_one_notice_to_the_existing_account(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        result = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert result == {"status": "sent"}
        email_service.send_notification_email.assert_called_once()
        assert email_service.send_notification_email.call_args.kwargs["to_email"] == RECIPIENT

    def test_resolves_the_recipient_from_the_key_not_from_the_payload(
        self,
        wired: MagicMock,
    ) -> None:
        """The broker carries an opaque key, so a queue reader learns no address."""
        auth_tasks.send_duplicate_registration_notice(USER_KEY)

        wired.get_by_key.assert_called_once_with(USER_KEY)

    def test_uses_the_recipients_locale(self, wired: MagicMock, email_service: MagicMock) -> None:
        wired.get_by_key.return_value = _user(locale="en")

        auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert "second account" in email_service.send_notification_email.call_args.kwargs["html_body"]

    def test_body_carries_nothing_from_the_stored_account(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        """No display name, no dates: the mail must not read an account out of an inbox."""
        auth_tasks.send_duplicate_registration_notice(USER_KEY)

        body = email_service.send_notification_email.call_args.kwargs["html_body"]
        assert "Victim Realname" not in body
        assert RECIPIENT not in body


class TestSuppressionWindow:
    def test_second_attempt_inside_the_window_sends_nothing(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        first = auth_tasks.send_duplicate_registration_notice(USER_KEY)
        second = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert first == {"status": "sent"}
        assert second == {"status": "suppressed"}
        assert email_service.send_notification_email.call_count == 1

    def test_a_burst_of_attempts_produces_exactly_one_mail(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        for _ in range(50):
            auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert email_service.send_notification_email.call_count == 1

    def test_one_notice_again_once_the_window_has_passed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        elapsed = MemoryRegistrationNoticeStore(ttl_seconds=0)
        monkeypatch.setattr("app.common.dependencies.get_registration_notice_store", lambda: elapsed)

        auth_tasks.send_duplicate_registration_notice(USER_KEY)
        auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert email_service.send_notification_email.call_count == 2

    def test_window_is_per_recipient_not_global(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        """One target's notice must not silence everybody else's."""
        wired.get_by_key.side_effect = [
            _user(),
            _user(_key="9137450", email="other@example.com"),
        ]

        auth_tasks.send_duplicate_registration_notice(USER_KEY)
        auth_tasks.send_duplicate_registration_notice("9137450")

        assert email_service.send_notification_email.call_count == 2


class TestQuietPaths:
    def test_account_erased_between_request_and_pickup(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        wired.get_by_key.return_value = None

        result = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert result == {"status": "skipped", "reason": "account_gone"}
        email_service.send_notification_email.assert_not_called()

    def test_inactive_account_is_not_mailed(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        wired.get_by_key.return_value = _user(is_active=False)

        result = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert result == {"status": "skipped", "reason": "inactive_account"}
        email_service.send_notification_email.assert_not_called()

    def test_delivery_failure_is_reported_not_raised(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        """``SmtpEmailAdapter._send`` re-raises; nothing above may pass that on."""
        email_service.send_notification_email.side_effect = ConnectionError("SMTP down")

        result = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert result == {"status": "failed", "reason": "delivery_error"}

    def test_adapter_without_notification_support_is_reported_not_raised(
        self,
        wired: MagicMock,
        email_service: MagicMock,
    ) -> None:
        email_service.send_notification_email.side_effect = NotImplementedError

        result = auth_tasks.send_duplicate_registration_notice(USER_KEY)

        assert result == {"status": "skipped", "reason": "adapter_unsupported"}

    def test_never_logs_the_raw_recipient(self, wired: MagicMock) -> None:
        """The probed address belongs to somebody who never consented (NFR-011)."""
        with structlog.testing.capture_logs() as logs:
            auth_tasks.send_duplicate_registration_notice(USER_KEY)
            auth_tasks.send_duplicate_registration_notice(USER_KEY)

        events = [entry for entry in logs if entry["event"].startswith("duplicate_registration_notice")]
        assert {entry["event"] for entry in events} == {
            "duplicate_registration_notice_sent",
            "duplicate_registration_notice_suppressed",
        }
        assert RECIPIENT not in str(events)
        assert all(entry["email_sha256"] for entry in events)


class TestDispatchHelper:
    def test_enqueues_the_task(self, monkeypatch: pytest.MonkeyPatch) -> None:
        delay = MagicMock()
        monkeypatch.setattr(auth_tasks.send_duplicate_registration_notice, "delay", delay)

        auth_tasks.dispatch_duplicate_registration_notice(USER_KEY)

        delay.assert_called_once_with(USER_KEY)

    def test_broker_outage_does_not_propagate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The caller is a request handler; an exception here would be a 500."""

        def _broker_down(*_args: object, **_kwargs: object) -> None:
            raise ConnectionError("broker unreachable")

        monkeypatch.setattr(auth_tasks.send_duplicate_registration_notice, "delay", _broker_down)

        with structlog.testing.capture_logs() as logs:
            auth_tasks.dispatch_duplicate_registration_notice(USER_KEY)

        assert any(entry["event"] == "duplicate_registration_notice_dispatch_failed" for entry in logs)

    def test_is_a_registered_celery_task(self) -> None:
        """An unregistered task would enqueue a message no worker can execute."""
        from app.tasks import celery_app

        assert "app.tasks.auth_tasks.send_duplicate_registration_notice" in celery_app.tasks
