"""#1815 — the step-up code mail, per adapter, and the wiring of the shared code tier.

* The SMTP adapter sends the code to the account's address with its validity and
  what to do if the owner did not ask for it.
* The console adapter follows the #1795 rule of the reset link exactly: the code
  reaches the log only under ``settings.debug``; otherwise the line says the mail
  was not delivered and carries no code.
* An adapter that does not implement the mail refuses loudly (``NotImplementedError``),
  as for the notification mail — a silently dropped code would lock a federated
  account out of its own step-ups without a trace.
* ``get_step_up_verifier`` wires the Valkey-backed code tier, so a code mailed by
  one replica is accepted by another.
"""

from __future__ import annotations

from typing import Any

import pytest
import structlog.testing

from app.common.decoys import email_digest
from app.config.settings import settings
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter
from app.domain.interfaces.email_service import IEmailService

RECIPIENT = "owner-5e1f@example.com"
# Shaped like a code; assembled at runtime so no scanner reads it as a credential (#1838).
CODE = "".join(str(n % 10) for n in range(3, 11))


@pytest.fixture(autouse=True)
def _keyed_digests(monkeypatch: pytest.MonkeyPatch) -> None:
    """A log salt, so ``to_sha256 == email_digest(...)`` compares keyed digests, not two no-salt constants (#1812)."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "digest-test-salt-not-a-secret-0123456789")


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


def test_the_smtp_adapter_mails_the_code_with_its_validity(monkeypatch: pytest.MonkeyPatch) -> None:
    import email

    monkeypatch.setattr(_FakeSmtp, "sent", [])
    monkeypatch.setattr("app.data_access.external.smtp_email_adapter.smtplib.SMTP", _FakeSmtp)
    adapter = SmtpEmailAdapter(host="smtp.invalid", port=587, username="", password="", from_email="noreply@x.org")

    with structlog.testing.capture_logs() as logs:
        adapter.send_step_up_code_email(RECIPIENT, "Erika <b>", CODE, "delete your Kamerplanter account")

    ((_sender, to, raw),) = _FakeSmtp.sent
    assert to == RECIPIENT
    body = next(part for part in email.message_from_string(raw).walk() if part.get_content_type() == "text/html")
    html = body.get_payload(decode=True).decode()
    assert CODE in html
    assert "10 minutes" in html
    assert "did not request" in html
    assert "Erika &lt;b&gt;" in html  # the display name is escaped
    assert "delete your Kamerplanter account" in html  # the act the code confirms (review SEC-003)
    assert CODE not in repr(logs)


def test_the_console_adapter_logs_no_code_without_debug_and_says_it_was_not_delivered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """/code-review of #1862: the route answered 202 for a code nobody received — now the adapter refuses."""
    from app.domain.interfaces.email_service import EmailUndeliverableError

    monkeypatch.setattr(settings, "debug", False)

    with structlog.testing.capture_logs() as logs, pytest.raises(EmailUndeliverableError):
        ConsoleEmailAdapter().send_step_up_code_email(RECIPIENT, "Erika", CODE, "delete your Kamerplanter account")

    (entry,) = logs
    assert entry["event"] == "email_step_up_code"
    assert entry["delivered"] is False
    assert entry["to_sha256"] == email_digest(RECIPIENT)
    assert CODE not in repr(logs)
    assert RECIPIENT not in repr(logs)


def test_the_console_adapter_logs_the_code_under_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)

    with structlog.testing.capture_logs() as logs:
        ConsoleEmailAdapter().send_step_up_code_email(RECIPIENT, "Erika", CODE, "delete your Kamerplanter account")

    (entry,) = logs
    assert entry["step_up_code"] == CODE
    assert RECIPIENT not in repr(logs)


def test_an_adapter_without_the_mail_refuses_loudly() -> None:
    class _Minimal(IEmailService):
        def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
            return None

        def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
            return None

    with pytest.raises(NotImplementedError):
        _Minimal().send_step_up_code_email(RECIPIENT, "Erika", CODE, "delete your Kamerplanter account")


def test_the_di_provider_wires_the_shared_code_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    """``redis.Redis.from_url`` connects lazily — building the provider touches no server."""
    from unittest.mock import MagicMock

    from app.common import dependencies
    from app.data_access.external.step_up_code_store import RedisStepUpCodeStore
    from app.data_access.external.step_up_throttle import RedisStepUpThrottleStore
    from app.domain.services.step_up_service import FederatedReauthPolicy

    # The re-authentication policy reads provider links and configurations (#1815);
    # a unit test must not open ArangoDB for them.
    monkeypatch.setattr(dependencies, "get_auth_provider_repo", MagicMock)
    monkeypatch.setattr(dependencies, "get_oidc_config_repo", MagicMock)

    verifier = dependencies.get_step_up_verifier()

    assert isinstance(verifier._reauth_store, RedisStepUpCodeStore)
    assert verifier._reauth_store._code_prefix == "kp:auth:stepup:reauth:"
    assert isinstance(verifier._reauth_policy, FederatedReauthPolicy)
    assert isinstance(verifier._code_store, RedisStepUpCodeStore)
    assert isinstance(verifier._store, RedisStepUpThrottleStore)


def _provider_keywords(function: str) -> set[str]:
    """The keyword arguments the provider *function* in ``dependencies.py`` passes to the service it builds."""
    import ast
    from pathlib import Path

    import app.common.dependencies as deps

    tree = ast.parse(Path(deps.__file__).read_text(encoding="utf-8"))
    (node,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function]
    return {kw.arg for call in ast.walk(node) if isinstance(call, ast.Call) for kw in call.keywords if kw.arg}


def test_the_auth_service_is_wired_with_what_the_follow_ups_need() -> None:
    """Unwired, the pending e-mail change would survive a reset and light mode would issue codes.

    Read off the provider's source: building ``get_auth_service`` for real opens
    repositories against ArangoDB, which a unit test must not touch.
    """
    assert {"email_change_repo", "light_mode", "step_up_verifier"} <= _provider_keywords("get_auth_service")


def test_the_verifier_is_wired_with_the_server_secret() -> None:
    assert "code_secret" in _provider_keywords("get_step_up_verifier")
