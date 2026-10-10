"""The e-mail adapters log a digest of the recipient, never the address (#1773 review GDPR-004).

``SmtpEmailAdapter`` logged ``to=<address>`` on every send and on every failure,
with ``exc_info`` on the failure — and an ``SMTPRecipientsRefused`` traceback
names the refused address again. ``ConsoleEmailAdapter`` logged ``to=`` as
well. A log stream has no retention rule of its own (NFR-011), and the recipient
of a duplicate-registration notice is a third party who never asked for it.

Both adapters are driven through their public methods; the SMTP connection is a
fake, so no mail server is contacted.
"""

from __future__ import annotations

import smtplib
from typing import Any

import pytest
import structlog.testing

from app.common.decoys import email_digest
from app.config.settings import settings
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.interfaces.email_service import EmailUndeliverableError

RECIPIENT = "recipient-9d2c41@example.com"
DISPLAY_NAME = "Erika Mustermann-9d2c41"
TOKEN = "reset-token-9d2c41"


@pytest.fixture(autouse=True)
def _keyed_digests(monkeypatch: pytest.MonkeyPatch) -> None:
    """A log salt, so ``to_sha256 == email_digest(...)`` compares keyed digests, not two no-salt constants (#1812)."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "digest-test-salt-not-a-secret-0123456789")


class _FakeSmtp:
    """Stands in for ``smtplib.SMTP``; refuses the recipient when told to."""

    refuse = False

    def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
        self.timeout = timeout
        self.host = host

    def __enter__(self) -> _FakeSmtp:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        return None

    def sendmail(self, sender: str, to: str, message: str) -> dict[str, Any]:
        if self.refuse:
            raise smtplib.SMTPRecipientsRefused({to: (550, f"5.1.1 <{to}>: Recipient address rejected".encode())})
        return {}


def _smtp(monkeypatch: pytest.MonkeyPatch, *, refuse: bool) -> SmtpEmailAdapter:
    monkeypatch.setattr(_FakeSmtp, "refuse", refuse)
    monkeypatch.setattr("app.data_access.external.smtp_email_adapter.smtplib.SMTP", _FakeSmtp)
    return SmtpEmailAdapter(host="smtp.invalid", port=587, username="u", password="p", from_email="noreply@example.com")


class TestSmtpAdapter:
    def test_a_sent_mail_logs_the_digest(self, monkeypatch: pytest.MonkeyPatch) -> None:
        adapter = _smtp(monkeypatch, refuse=False)

        with structlog.testing.capture_logs() as logs:
            adapter.send_notification_email(RECIPIENT, "Subject", "<p>body</p>")

        sent = next(entry for entry in logs if entry["event"] == "email_sent")
        assert sent["to_sha256"] == email_digest(RECIPIENT)
        assert RECIPIENT not in repr(logs)

    def test_a_refused_recipient_logs_the_digest_and_the_type_and_still_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = _smtp(monkeypatch, refuse=True)

        with structlog.testing.capture_logs() as logs, pytest.raises(smtplib.SMTPRecipientsRefused):
            adapter.send_notification_email(RECIPIENT, "Subject", "<p>body</p>")

        failed = next(entry for entry in logs if entry["event"] == "email_send_failed")
        assert failed["to_sha256"] == email_digest(RECIPIENT)
        assert failed["error_type"] == "SMTPRecipientsRefused"
        assert "exc_info" not in failed, "the traceback would name the refused address again"
        assert RECIPIENT not in repr(logs)


class TestConsoleAdapter:
    @pytest.mark.parametrize(
        "send",
        [
            lambda a: a.send_verification_email(RECIPIENT, "tok", "https://app.test"),
            lambda a: a.send_email_change_email(RECIPIENT, "tok", "https://app.test"),
            lambda a: a.send_password_reset_email(RECIPIENT, "tok", "https://app.test"),
            lambda a: a.send_notification_email(RECIPIENT, "Subject", "<p>body</p>"),
        ],
        ids=["verification", "email-change", "password-reset", "notification"],
    )
    def test_every_mail_logs_the_digest(self, send: Any) -> None:
        with structlog.testing.capture_logs() as logs:
            send(ConsoleEmailAdapter())

        assert len(logs) == 1
        assert logs[0]["to_sha256"] == email_digest(RECIPIENT)
        assert RECIPIENT not in repr(logs)


_LINK_MAILS = [
    pytest.param(
        lambda a: a.send_verification_email(RECIPIENT, TOKEN, "https://app.test"),
        "email_verification",
        "verification_url",
        "https://app.test/verify-email/" + TOKEN,
        id="verification",
    ),
    pytest.param(
        lambda a: a.send_email_change_email(RECIPIENT, TOKEN, "https://app.test"),
        "email_change",
        "email_change_url",
        "https://app.test/email-change/" + TOKEN,
        id="email-change",
    ),
    pytest.param(
        lambda a: a.send_password_reset_email(RECIPIENT, TOKEN, "https://app.test"),
        "email_password_reset",
        "reset_url",
        "https://app.test/password-reset/" + TOKEN,
        id="password-reset",
    ),
]


class TestConsoleAdapterLinks:
    """#1795: the link's token takes over the account; it is logged only in debug, the name never."""

    @pytest.mark.parametrize(("send", "event", "url_field", "url"), _LINK_MAILS)
    def test_outside_debug_the_link_is_not_logged(
        self, monkeypatch: pytest.MonkeyPatch, send: Any, event: str, url_field: str, url: str
    ) -> None:
        monkeypatch.setattr(settings, "debug", False)

        with structlog.testing.capture_logs() as logs:
            send(ConsoleEmailAdapter())

        (entry,) = logs
        assert entry["event"] == event
        assert entry["url_logged"] is False
        assert entry["to_sha256"] == email_digest(RECIPIENT)
        assert url_field not in entry
        assert TOKEN not in repr(logs)
        assert DISPLAY_NAME not in repr(logs)

    @pytest.mark.parametrize(("send", "event", "url_field", "url"), _LINK_MAILS)
    def test_in_debug_the_link_is_logged_for_the_local_operator(
        self, monkeypatch: pytest.MonkeyPatch, send: Any, event: str, url_field: str, url: str
    ) -> None:
        monkeypatch.setattr(settings, "debug", True)

        with structlog.testing.capture_logs() as logs:
            send(ConsoleEmailAdapter())

        (entry,) = logs
        assert entry["event"] == event
        assert entry["url_logged"] is True
        assert entry[url_field] == url
        assert DISPLAY_NAME not in repr(logs)


class TestConsoleAdapterInvitation:
    """#2162: the invitation link joins a tenant - the #1795 rule, and outside debug no claim of delivery."""

    def test_outside_debug_the_link_is_not_logged_and_the_mail_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "debug", False)

        with structlog.testing.capture_logs() as logs, pytest.raises(EmailUndeliverableError):
            ConsoleEmailAdapter().send_invitation_email(RECIPIENT, TOKEN, "https://app.test")

        (entry,) = logs
        assert (entry["event"], entry["url_logged"], entry["delivered"]) == ("email_invitation", False, False)
        assert entry["to_sha256"] == email_digest(RECIPIENT)
        assert TOKEN not in repr(logs)
        assert RECIPIENT not in repr(logs)

    def test_in_debug_the_link_is_logged_for_the_local_operator(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", True)

        with structlog.testing.capture_logs() as logs:
            ConsoleEmailAdapter().send_invitation_email(RECIPIENT, TOKEN, "https://app.test")

        (entry,) = logs
        assert entry["url_logged"] is True
        assert entry["invitation_url"] == InvitationEngine.accept_url("https://app.test", TOKEN)
        assert RECIPIENT not in repr(logs)


class TestConsoleAdapterStartupWarning:
    @pytest.mark.parametrize(
        ("adapter", "debug", "warns"),
        [("console", False, True), ("resend", False, False), ("console", True, False), ("smtp", False, False)],
    )
    def test_the_api_warns_when_mail_goes_to_the_console_outside_debug(
        self, monkeypatch: pytest.MonkeyPatch, adapter: str, debug: bool, warns: bool
    ) -> None:
        from app.main import warn_if_console_email_adapter

        monkeypatch.setattr(settings, "email_adapter", adapter)
        monkeypatch.setattr(settings, "debug", debug)

        with structlog.testing.capture_logs() as logs:
            warned = warn_if_console_email_adapter()

        assert warned is warns
        events = [(entry["event"], entry["log_level"]) for entry in logs]
        assert events == ([("email_adapter_console_in_production", "warning")] if warns else [])

    @pytest.mark.parametrize("required", [True, False])
    def test_the_warning_names_the_verification_switch_only_while_it_is_on(
        self, monkeypatch: pytest.MonkeyPatch, required: bool
    ) -> None:
        """#1948: with verification on by default, a console-adapter install locks
        new self-registered accounts out — the warning says how to switch it off."""
        from app.main import warn_if_console_email_adapter

        monkeypatch.setattr(settings, "email_adapter", "console")
        monkeypatch.setattr(settings, "debug", False)
        monkeypatch.setattr(settings, "require_email_verification", required)

        with structlog.testing.capture_logs() as logs:
            warn_if_console_email_adapter()

        (entry,) = logs
        assert entry["require_email_verification"] is required
        assert ("REQUIRE_EMAIL_VERIFICATION=false" in entry["detail"]) is required


def test_the_smtp_connection_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """``smtplib.SMTP`` has no default timeout: a hung server would hold a worker thread for good (#1890 review)."""
    seen: list[float | None] = []

    class _Probe(_FakeSmtp):
        def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
            super().__init__(host, port, timeout)
            seen.append(timeout)

    monkeypatch.setattr("app.data_access.external.smtp_email_adapter.smtplib.SMTP", _Probe)
    adapter = SmtpEmailAdapter(host="smtp.invalid", port=587, username="u", password="p", from_email="a@example.com")

    adapter.send_notification_email("to@example.org", "subject", "<p>body</p>")

    assert seen == [10]


class TestEmailChannelWithoutVerificationWarning:
    """#1948 — a configured sender plus REQUIRE_EMAIL_VERIFICATION=false is named at startup."""

    @pytest.mark.parametrize(
        ("adapter", "required", "warns"),
        [
            ("smtp", False, True),
            ("resend", False, True),
            ("smtp", True, False),
            ("console", False, False),
        ],
    )
    def test_the_api_warns_only_when_a_sender_meets_unverified_registration(
        self, monkeypatch: pytest.MonkeyPatch, adapter: str, required: bool, warns: bool
    ) -> None:
        from app.main import warn_if_email_channel_without_verification

        monkeypatch.setattr(settings, "email_adapter", adapter)
        monkeypatch.setattr(settings, "require_email_verification", required)

        with structlog.testing.capture_logs() as logs:
            warned = warn_if_email_channel_without_verification()

        assert warned is warns
        events = [(entry["event"], entry["log_level"]) for entry in logs]
        assert events == ([("email_channel_without_verification", "warning")] if warns else [])
