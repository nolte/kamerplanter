"""#1856 / #1848 — the account mails carry no markup a requester chose, and the e-mail change has its own link.

``SmtpEmailAdapter.send_verification_email`` and ``send_password_reset_email``
interpolated ``display_name`` and the link unescaped. ``PrivacyService.request_email_change``
sends a mail to any address the requester names; with a display name such as an
``<a href>`` "confirm your account" link, a registered attacker had a genuine
Kamerplanter mail carry their markup into a stranger's inbox (#1856). The mail to
a not-yet-verified address — the registration verification and the e-mail change
— now carries no requester-chosen text at all; every other placeholder is escaped.

The e-mail change mailed the account-verification link (``/verify-email/{token}``),
whose page calls ``POST /auth/verify-email`` — the wrong endpoint — so a user who
followed it got an invalid-token error (#1848). It now has its own link,
``/email-change/{token}``.
"""

from __future__ import annotations

import email
from typing import Any

import pytest
import structlog.testing

from app.config.settings import settings
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter

RECIPIENT = "new-owner-7a1c@example.org"
MARKUP = '<a href="https://evil.example/confirm">Confirm your account</a>'
TOKEN = "tok" + "-".join(["a1", "b2", "c3"])
FRONTEND = "https://app.test"


class _FakeSmtp:
    sent: list[tuple[str, str, str]] = []

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
        _FakeSmtp.sent.append((sender, to, message))
        return {}


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> SmtpEmailAdapter:
    monkeypatch.setattr(_FakeSmtp, "sent", [])
    monkeypatch.setattr("app.data_access.external.smtp_email_adapter.smtplib.SMTP", _FakeSmtp)
    return SmtpEmailAdapter(host="smtp.invalid", port=587, username="", password="", from_email="noreply@x.org")


def _html() -> str:
    ((_sender, _to, raw),) = _FakeSmtp.sent
    part = next(p for p in email.message_from_string(raw).walk() if p.get_content_type() == "text/html")
    return part.get_payload(decode=True).decode()


def test_the_password_reset_mail_escapes_the_display_name(smtp: SmtpEmailAdapter) -> None:
    smtp.send_password_reset_email(RECIPIENT, MARKUP, TOKEN, FRONTEND)

    html = _html()
    assert '<a href="https://evil.example' not in html
    assert "&lt;a href=" in html


def test_the_verification_mail_carries_no_display_name(smtp: SmtpEmailAdapter) -> None:
    # Sent to an address nobody has verified yet: no requester-chosen text at all.
    smtp.send_verification_email(RECIPIENT, TOKEN, FRONTEND)

    html = _html()
    assert "evil.example" not in html
    assert f"{FRONTEND}/verify-email/{TOKEN}" in html


def test_the_email_change_mail_has_its_own_link_and_no_display_name(smtp: SmtpEmailAdapter) -> None:
    smtp.send_email_change_email(RECIPIENT, TOKEN, FRONTEND)

    html = _html()
    assert f"{FRONTEND}/email-change/{TOKEN}" in html
    assert "/verify-email/" not in html


def test_a_link_is_escaped_inside_its_attribute(smtp: SmtpEmailAdapter) -> None:
    smtp.send_password_reset_email(RECIPIENT, "Erika", 'x"><script>', FRONTEND)

    html = _html()
    assert "<script>" not in html
    assert "&quot;&gt;&lt;script&gt;" in html


def test_the_console_adapter_logs_the_email_change_link_only_under_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", False)
    with structlog.testing.capture_logs() as quiet:
        ConsoleEmailAdapter().send_email_change_email(RECIPIENT, TOKEN, FRONTEND)
    monkeypatch.setattr(settings, "debug", True)
    with structlog.testing.capture_logs() as loud:
        ConsoleEmailAdapter().send_email_change_email(RECIPIENT, TOKEN, FRONTEND)

    assert TOKEN not in repr(quiet)
    assert quiet[0]["url_logged"] is False
    assert loud[0]["email_change_url"] == f"{FRONTEND}/email-change/{TOKEN}"
    assert RECIPIENT not in repr(loud)
