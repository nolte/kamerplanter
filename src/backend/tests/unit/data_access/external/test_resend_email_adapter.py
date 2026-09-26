"""#1821 — ``EMAIL_ADAPTER=resend`` delivers through the Resend HTTP API.

Until #1821 the value was documented but had no implementation:
``get_email_service`` returned the console adapter for it (and for any typo),
so no verification, password-reset or step-up mail was ever delivered. These
tests drive the adapter through ``httpx.MockTransport`` (no network) with the
same checks the SMTP adapter has: what is sent, what is logged, what a failure
does — and the settings that select it.
"""

from __future__ import annotations

import json

import httpx
import pytest
import structlog.testing
from pydantic import SecretStr, ValidationError

from app.common.decoys import email_digest
from app.config.settings import Settings, settings
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.resend_email_adapter import (
    RESEND_EMAILS_URL,
    ResendDeliveryError,
    ResendEmailAdapter,
)
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter
from app.domain.interfaces.email_service import EmailUndeliverableError

RECIPIENT = "recipient-1821@example.com"
SENDER = "noreply@mail.example.org"
# Shaped like a Resend key; assembled at run time so no scanner reads it as a credential (BACKEND.md §16.3).
API_KEY = "_".join(("re", "probe", "1821", "not", "a", "key"))
CODE = "".join(str(n % 10) for n in range(3, 11))


class _Resend:
    """A ``MockTransport`` handler that records every request and answers with ``status``."""

    def __init__(self, status: int = 200, body: dict | None = None) -> None:
        self.status = status
        self.body = body if body is not None else {"id": "email-id-1821"}
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)

    def adapter(self) -> ResendEmailAdapter:
        return ResendEmailAdapter(api_key=API_KEY, from_email=SENDER, transport=httpx.MockTransport(self))


def test_a_mail_is_posted_to_the_emails_endpoint_with_the_key_as_bearer() -> None:
    resend = _Resend()

    resend.adapter().send_notification_email(RECIPIENT, "Subject 1821", "<p>body</p>")

    (request,) = resend.requests
    assert str(request.url) == RESEND_EMAILS_URL
    assert request.method == "POST"
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert json.loads(request.content) == {
        "from": SENDER,
        "to": [RECIPIENT],
        "subject": "Subject 1821",
        "html": "<p>body</p>",
    }


@pytest.mark.parametrize(
    ("send", "subject", "needle"),
    [
        (
            lambda a: a.send_verification_email(RECIPIENT, "tok-1821", "https://app.test"),
            "Verification",
            "https://app.test/verify-email/tok-1821",
        ),
        (
            lambda a: a.send_password_reset_email(RECIPIENT, "tok-1821", "https://app.test"),
            "Password Reset",
            "https://app.test/password-reset/tok-1821",
        ),
        (
            lambda a: a.send_email_change_email(RECIPIENT, "tok-1848", "https://app.test"),
            "Confirm your new email address",
            "https://app.test/email-change/tok-1848",
        ),
        (
            lambda a: a.send_step_up_code_email(RECIPIENT, "Erika <b>", CODE, "delete your account"),
            "Confirmation code",
            CODE,
        ),
    ],
    ids=["verification", "password-reset", "email-change", "step-up-code"],
)
def test_the_system_mails_are_the_smtp_adapters_texts(send, subject: str, needle: str) -> None:
    resend = _Resend()

    send(resend.adapter())

    payload = json.loads(resend.requests[0].content)
    assert subject in payload["subject"]
    assert needle in payload["html"]
    if needle == CODE:
        assert "Erika &lt;b&gt;" in payload["html"]  # escaped, like the SMTP adapter's


def test_both_delivering_adapters_render_from_one_template() -> None:
    """One source for the texts: the SMTP and Resend adapters do not define the bodies themselves."""
    for adapter in (SmtpEmailAdapter, ResendEmailAdapter):
        for method in (
            "send_verification_email",
            "send_password_reset_email",
            "send_email_change_email",
            "send_step_up_code_email",
        ):
            assert method not in vars(adapter), f"{adapter.__name__} redefines {method}"


def test_a_sent_mail_logs_the_digest_and_never_the_key() -> None:
    resend = _Resend()

    with structlog.testing.capture_logs() as logs:
        resend.adapter().send_notification_email(RECIPIENT, "Subject", "<p>body</p>")

    (sent,) = [entry for entry in logs if entry["event"] == "email_sent"]
    assert sent["to_sha256"] == email_digest(RECIPIENT)
    assert RECIPIENT not in repr(logs) and API_KEY not in repr(logs)


@pytest.mark.parametrize("status", [401, 422, 429, 500])
def test_a_refused_mail_raises_and_logs_the_status_but_not_the_body(status: int) -> None:
    # Resend's error message can quote the recipient; it must not reach the log or the exception.
    resend = _Resend(status=status, body={"name": "validation_error", "message": f"Invalid `to`: {RECIPIENT}"})

    with structlog.testing.capture_logs() as logs, pytest.raises(ResendDeliveryError) as caught:
        resend.adapter().send_notification_email(RECIPIENT, "Subject", "<p>body</p>")

    (failed,) = [entry for entry in logs if entry["event"] == "email_send_failed"]
    assert failed["status_code"] == status
    assert failed["error_type"] == "ResendDeliveryError"
    assert caught.value.status_code == status
    for text in (repr(logs), str(caught.value)):
        assert RECIPIENT not in text and API_KEY not in text


def test_a_network_failure_raises_an_undeliverable_error_and_logs_the_type() -> None:
    """No answer is an undeliverable mail too (#1888 review): the step-up caller withdraws its code on it."""

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = ResendEmailAdapter(api_key=API_KEY, from_email=SENDER, transport=httpx.MockTransport(refuse))

    with structlog.testing.capture_logs() as logs, pytest.raises(ResendDeliveryError) as caught:
        adapter.send_notification_email(RECIPIENT, "Subject", "<p>body</p>")

    assert isinstance(caught.value, EmailUndeliverableError)
    assert caught.value.status_code is None
    # Not chained: httpx's frames hold the Authorization header and the payload (#1888 SEC-002).
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    (failed,) = [entry for entry in logs if entry["event"] == "email_send_failed"]
    assert failed["error_type"] == "ResendDeliveryError"
    assert API_KEY not in repr(logs)


def test_the_adapter_refuses_to_exist_without_a_key() -> None:
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        ResendEmailAdapter(api_key="", from_email=SENDER)


# ── selection through the settings ────────────────────────────────────────────


def test_resend_is_selected_by_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.common.dependencies import get_email_service

    monkeypatch.setattr(settings, "email_adapter", "resend")
    monkeypatch.setattr(settings, "resend_api_key", SecretStr(API_KEY))

    assert isinstance(get_email_service(), ResendEmailAdapter)
    monkeypatch.setattr(settings, "email_adapter", "console")
    assert isinstance(get_email_service(), ConsoleEmailAdapter)


@pytest.mark.parametrize("value", ["smtpp", "sendgrid", "SMTP-typo", ""])
def test_an_unknown_email_adapter_is_refused_when_the_settings_load(value: str) -> None:
    with pytest.raises(ValidationError, match="email_adapter"):
        Settings(email_adapter=value)


def test_resend_without_a_key_is_refused_when_the_settings_load_without_echoing_other_values() -> None:
    other_secret = "-".join(("jwt", "secret", "1821", "probe"))

    with pytest.raises(ValidationError) as caught:
        Settings(email_adapter="resend", jwt_secret_key=other_secret)

    assert "RESEND_API_KEY" in str(caught.value)
    assert other_secret not in str(caught.value)


def test_resend_with_a_key_loads() -> None:
    assert Settings(email_adapter="resend", resend_api_key=API_KEY).email_adapter == "resend"


def test_the_api_key_is_a_secret_in_the_settings() -> None:
    """``SecretStr`` (#1888 SEC-006): ``repr(settings)`` / ``model_dump()`` must not print the key."""
    loaded = Settings(email_adapter="resend", resend_api_key=API_KEY)

    assert API_KEY not in repr(loaded)
    assert API_KEY not in str(loaded.model_dump())
    assert loaded.resend_api_key.get_secret_value() == API_KEY
