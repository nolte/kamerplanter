"""A failing mail adapter must not tell an anonymous caller which addresses have an account (#1890).

``POST /auth/password-reset/request`` answers an unknown address with the generic
200 straight away, but a known one only after a synchronous mail send - and a send
that raises (SMTP outage; with the Resend adapter a provider 429 an attacker can
provoke by flooding the sending limit) used to surface as a 500. Registration with
``require_email_verification`` is the same oracle read from the other side: the
*free* address sends the verification mail, the taken one never does.

Asserted on the wire, per failure type the adapters raise:

* status and body of the known / new address equal those of the unknown / taken one;
* the send happens after the response body has left the app, so it cannot be timed
  (observed through the ASGI ``send`` events, not through a clock);
* the failure is logged, and the log line carries no address.
"""

from __future__ import annotations

import smtplib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import structlog
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import EmailUndeliverableError, IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

KNOWN = "owner@example.com"
UNKNOWN = "nobody@example.com"
PASSWORD = "A-Long-Enough-Password-2024!"
_VOLATILE = frozenset({"key", "created_at", "email"})  # email is the submitted address, echoed back

FAILURES = [
    pytest.param(EmailUndeliverableError("provider refused"), id="undeliverable"),
    pytest.param(smtplib.SMTPRecipientsRefused({KNOWN: (550, b"no such user")}), id="smtp-refused"),
    pytest.param(ConnectionRefusedError("smtp down"), id="connection"),
    pytest.param(RuntimeError("adapter bug"), id="unexpected"),
]


class _FailingMail(IEmailService):
    """An adapter whose every send raises, recording the order against the response."""

    def __init__(self, error: Exception, order: list[str]) -> None:
        self._error = error
        self._order = order

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self._order.append("send")
        raise self._error

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self._order.append("send")
        raise self._error


class _OrderRecordingApp:
    def __init__(self, app: Any, log: list[str]) -> None:
        self._app = app
        self._log = log

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        async def _send(message: dict) -> None:
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                self._log.append("response-sent")
            await send(message)

        await self._app(scope, receive, _send)


def _service(mail: IEmailService, order: list[str], *, require_verification: bool) -> AuthService:
    repo = MagicMock()
    stored = User(
        _key="8271634",
        email=KNOWN,
        display_name="Owner",
        password_hash=PasswordEngine().hash_password("The-Owners-Real-Password-2024!"),
        email_verified=True,
        created_at=datetime.now(UTC),
    )
    repo.get_by_email.side_effect = lambda email: stored.model_copy(deep=True) if email.lower() == KNOWN else None

    def _create(user: User) -> User:
        created = user.model_copy(deep=True)
        created.key = "9137450"
        created.created_at = datetime.now(UTC)
        return created

    repo.create.side_effect = _create
    repo.update_fields.side_effect = lambda *a, **k: order.append("write")
    return AuthService(
        user_repo=repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=mail,
        frontend_url="http://localhost:5173",
        tenant_service=MagicMock(),
        require_email_verification=require_verification,
    )


@pytest.fixture
def order() -> list[str]:
    return []


def _client(order: list[str], error: Exception, *, require_verification: bool) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: _service(
            _FailingMail(error, order), order, require_verification=require_verification
        )
        try:
            yield TestClient(_OrderRecordingApp(app, order), raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


def _reset(client: TestClient, email: str):  # noqa: ANN202 - httpx Response
    return client.post("/api/v1/auth/password-reset/request", json={"email": email})


def _register(client: TestClient, email: str):  # noqa: ANN202 - httpx Response
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Chosen Name"},
    )


class TestPasswordResetRequest:
    @pytest.mark.parametrize("error", FAILURES)
    def test_known_address_answers_exactly_like_an_unknown_one(self, order: list[str], error: Exception) -> None:
        for client in _client(order, error, require_verification=False):
            known = _reset(client, KNOWN)
            unknown = _reset(client, UNKNOWN)

        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()
        assert dict(known.headers).keys() == dict(unknown.headers).keys()

    def test_the_send_runs_after_the_response_has_been_written(self, order: list[str]) -> None:
        for client in _client(order, RuntimeError("down"), require_verification=False):
            _reset(client, KNOWN)

        assert order == ["response-sent", "write", "send"]

    def test_a_failing_token_write_answers_like_an_unknown_address(self, order: list[str]) -> None:
        """The write is deferred with the mail; a database error must not answer 5xx for a known address only."""
        with patch("app.domain.services.auth_service._iso", side_effect=RuntimeError("db down")):
            for client in _client(order, RuntimeError("down"), require_verification=False):
                known = _reset(client, KNOWN)
                unknown = _reset(client, UNKNOWN)

        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()

    def test_unknown_address_triggers_no_write_and_no_send(self, order: list[str]) -> None:
        for client in _client(order, RuntimeError("down"), require_verification=False):
            _reset(client, UNKNOWN)

        assert order == ["response-sent"]

    @pytest.mark.parametrize("error", FAILURES)
    def test_failure_is_logged_without_the_address(self, order: list[str], error: Exception) -> None:
        with structlog.testing.capture_logs() as logs:
            for client in _client(order, error, require_verification=False):
                _reset(client, KNOWN)

        failed = [entry for entry in logs if entry["event"] == "auth_mail_send_failed"]
        assert len(failed) == 1
        assert failed[0]["kind"] == "password_reset"
        assert failed[0]["error_type"] == type(error).__name__
        assert KNOWN not in repr(logs)
        assert "owner" not in repr(logs)


class TestRegistrationWithVerification:
    @pytest.mark.parametrize("error", FAILURES)
    def test_free_address_answers_like_a_taken_one(self, order: list[str], error: Exception) -> None:
        for client in _client(order, error, require_verification=True):
            free = _register(client, UNKNOWN)
            taken = _register(client, KNOWN)

        assert free.status_code == taken.status_code == 201
        strip = lambda body: {k: v for k, v in body.items() if k not in _VOLATILE}  # noqa: E731
        assert strip(free.json()) == strip(taken.json())

    def test_the_send_runs_after_the_response_has_been_written(self, order: list[str]) -> None:
        for client in _client(order, RuntimeError("down"), require_verification=True):
            _register(client, UNKNOWN)

        assert order == ["response-sent", "send"]

    def test_failure_is_logged_without_the_address(self, order: list[str]) -> None:
        with structlog.testing.capture_logs() as logs:
            for client in _client(
                order, smtplib.SMTPRecipientsRefused({UNKNOWN: (550, b"x")}), require_verification=True
            ):
                _register(client, UNKNOWN)

        failed = [entry for entry in logs if entry["event"] == "auth_mail_send_failed"]
        assert [entry["kind"] for entry in failed] == ["verification"]
        assert "nobody@example.com" not in repr(logs)
