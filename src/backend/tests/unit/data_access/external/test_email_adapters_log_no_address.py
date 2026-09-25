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
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter

RECIPIENT = "recipient-9d2c41@example.com"


class _FakeSmtp:
    """Stands in for ``smtplib.SMTP``; refuses the recipient when told to."""

    refuse = False

    def __init__(self, host: str, port: int) -> None:
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
            lambda a: a.send_verification_email(RECIPIENT, "Name", "tok", "https://app.test"),
            lambda a: a.send_password_reset_email(RECIPIENT, "Name", "tok", "https://app.test"),
            lambda a: a.send_notification_email(RECIPIENT, "Subject", "<p>body</p>"),
        ],
        ids=["verification", "password-reset", "notification"],
    )
    def test_every_mail_logs_the_digest(self, send: Any) -> None:
        with structlog.testing.capture_logs() as logs:
            send(ConsoleEmailAdapter())

        assert len(logs) == 1
        assert logs[0]["to_sha256"] == email_digest(RECIPIENT)
        assert RECIPIENT not in repr(logs)
