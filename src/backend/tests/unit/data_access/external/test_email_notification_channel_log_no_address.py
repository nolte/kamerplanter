"""The e-mail notification channel logs a digest of the recipient, never the address (#1781).

``EmailNotificationChannel`` logged ``to=<address>`` on every send and failure,
and on a failure ``error=str(exc)`` plus ``exc_info=True`` — an
``SMTPRecipientsRefused`` names the refused address in its text and again in the
traceback. It was off the #1773 guard's path selector (#1781 widened it). The
channel is driven through its public ``send`` / ``send_batch`` with a fake
``IEmailService``; what structlog receives is asserted.
"""

from __future__ import annotations

import asyncio
import smtplib
from typing import Any

import pytest
import structlog.testing

from app.common.decoys import UNAVAILABLE_EMAIL_DIGEST, email_digest
from app.config.settings import settings
from app.data_access.external.email_notification_channel import EmailNotificationChannel
from app.domain.models.notification import Notification

RECIPIENT = "recipient-7f3a90@example.com"


class _FakeEmailService:
    def __init__(self, *, refuse: bool) -> None:
        self.refuse = refuse

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        if self.refuse:
            raise smtplib.SMTPRecipientsRefused({to_email: (550, f"5.1.1 <{to_email}>: rejected".encode())})


@pytest.fixture(autouse=True)
def _salted(monkeypatch: pytest.MonkeyPatch) -> None:
    # The digest's key since #1812. With the tombstone salt set instead, both sides
    # of the digest comparison were the constant "unavailable" — a vacuous pass.
    monkeypatch.setattr(settings, "log_pseudonym_salt", "s" * 40)


def _notification() -> Notification:
    return Notification(notification_type="care_due", title="Water", body="Water the basil")


def _drive(*, refuse: bool, batch: bool) -> list[dict[str, Any]]:
    channel = EmailNotificationChannel(_FakeEmailService(refuse=refuse))  # type: ignore[arg-type]
    with structlog.testing.capture_logs() as logs:
        if batch:
            asyncio.run(channel.send_batch([_notification(), _notification()], {"email": RECIPIENT}))
        else:
            asyncio.run(channel.send(_notification(), {"email": RECIPIENT}))
    return logs


@pytest.mark.parametrize("batch", [False, True], ids=["send", "send_batch"])
@pytest.mark.parametrize("refuse", [False, True], ids=["delivered", "refused"])
def test_channel_log_names_no_recipient_address(refuse: bool, batch: bool) -> None:
    logs = _drive(refuse=refuse, batch=batch)

    assert logs, "no log line captured — the assertion below would hold over nothing"
    for entry in logs:
        assert RECIPIENT not in str(entry), entry
        assert "exc_info" not in entry, "a traceback repeats the refused address"
    assert logs[-1]["to_sha256"] == email_digest(RECIPIENT)
    assert logs[-1]["to_sha256"] != UNAVAILABLE_EMAIL_DIGEST, "a keyed digest, not the no-salt constant"
