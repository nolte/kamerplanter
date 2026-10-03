"""``POST /api/v1/auth/resend-verification`` — REQ-023 §3.2b, #2037.

An account whose first verification link was lost or expired could never sign
in once ``REQUIRE_EMAIL_VERIFICATION`` is on: ``/register`` answers a taken
address with the duplicate branch (a notice, no new token) and nothing else
issued a token. Asserted here on the wire, through the real route:

* the answer — status, full body and header names — is the same for an unknown,
  an unverified and an already verified address;
* the work before the response is the same for all three (one budget
  reservation); the lookup, the token write and the mail run after it;
* an unverified local account gets a fresh token, which invalidates the old one;
* no mail when verification is off, nor for a verified, service or
  federated-only account;
* the per-address budget silently stops the mail after three requests, and the
  per-IP limit answers 429 on the eleventh request;
* the login refusal of an unverified account names the way out.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import structlog
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.data_access.external.step_up_throttle import VERIFICATION_RESEND_WINDOW_SECONDS, MemoryStepUpThrottleStore
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import MAX_VERIFICATION_RESENDS_PER_WINDOW, AuthService

UNKNOWN = "nobody@example.com"
UNVERIFIED = "pending@example.com"
VERIFIED = "verified@example.com"
SERVICE = "robot@example.com"
FEDERATED = "federated@example.com"
PASSWORD = "A-Long-Enough-Password-2024!"
OLD_TOKEN = "the-token-of-the-lost-first-mail"

#: Mirrors ``settings.rate_limit_resend_verification`` ("10/hour"); the 11th call must fail.
_PER_IP_LIMIT = 10

_ROUTE = "/api/v1/auth/resend-verification"

_PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)


def _users() -> dict[str, User]:
    later = datetime.now(UTC) + timedelta(hours=1)
    return {
        UNVERIFIED: User(
            _key="1000001",
            email=UNVERIFIED,
            display_name="Pending",
            password_hash=_PASSWORD_HASH,
            email_verified=False,
            email_verification_token=OLD_TOKEN,
            email_verification_expires=later,
        ),
        VERIFIED: User(
            _key="1000002", email=VERIFIED, display_name="Verified", password_hash=_PASSWORD_HASH, email_verified=True
        ),
        SERVICE: User(
            _key="1000003",
            email=SERVICE,
            display_name="Robot",
            password_hash=_PASSWORD_HASH,
            email_verified=False,
            account_type="service",
        ),
        FEDERATED: User(_key="1000004", email=FEDERATED, display_name="Federated", email_verified=False),
    }


class _Repo:
    """The four user-repository calls the flow makes, over a dict, recording into ``order``."""

    def __init__(self, order: list[str]) -> None:
        self.users = _users()
        self._order = order

    def get_by_email(self, email: str) -> User | None:
        self._order.append("lookup")
        user = self.users.get(email.lower())
        return user.model_copy(deep=True) if user else None

    def get_by_email_verification_token(self, token: str) -> User | None:
        found = [u for u in self.users.values() if u.email_verification_token == token]
        return found[0].model_copy(deep=True) if found else None

    def get_by_key(self, key: str) -> User | None:
        found = [u for u in self.users.values() if u.key == key]
        return found[0].model_copy(deep=True) if found else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self._order.append("write")
        user = next(u for u in self.users.values() if u.key == key)
        updated = user.model_validate({**user.model_dump(by_alias=True), **fields})
        self.users[updated.email] = updated
        return updated.model_copy(deep=True)


class _Mail(IEmailService):
    def __init__(self, order: list[str]) -> None:
        self.sent: list[tuple[str, str]] = []
        self._order = order

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self._order.append("send")
        self.sent.append((to_email, token))

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        raise AssertionError("not part of this flow")


class _RecordingBudget(MemoryStepUpThrottleStore):
    """The production in-process tier with the production window, recording each reservation."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS)
        self._order = order

    def reserve_attempt(self, subject: str) -> int:
        self._order.append("reserve")
        return super().reserve_attempt(subject)


class _OrderRecordingApp:
    """Marks the moment the response body has left the app, in the same log as the work."""

    def __init__(self, app: Any, log: list[str]) -> None:
        self._app = app
        self._log = log

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        async def _send(message: dict) -> None:
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                self._log.append("response-sent")
            await send(message)

        await self._app(scope, receive, _send)


class _World:
    def __init__(self, *, require_verification: bool = True) -> None:
        self.order: list[str] = []
        self.repo = _Repo(self.order)
        self.mail = _Mail(self.order)
        self.budget = _RecordingBudget(self.order)
        self.require_verification = require_verification

    def service(self) -> AuthService:
        return AuthService(
            user_repo=self.repo,  # type: ignore[arg-type]
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="http://localhost:5173",
            require_email_verification=self.require_verification,
            verification_resend_store=self.budget,
        )


def _client(world: _World) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = world.service
        try:
            yield TestClient(_OrderRecordingApp(app, world.order), raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


@pytest.fixture
def world() -> _World:
    return _World()


@pytest.fixture
def client(world: _World) -> Iterator[TestClient]:
    yield from _client(world)


def _resend(client: TestClient, email: str):  # noqa: ANN202 - httpx Response
    return client.post(_ROUTE, json={"email": email})


class TestOneAnswerForEveryAddress:
    def test_status_body_and_headers_are_identical_for_unknown_unverified_and_verified(
        self, client: TestClient
    ) -> None:
        answers = {email: _resend(client, email) for email in (UNKNOWN, UNVERIFIED, VERIFIED)}

        statuses = {email: r.status_code for email, r in answers.items()}
        bodies = {email: r.json() for email, r in answers.items()}
        assert statuses == {UNKNOWN: 202, UNVERIFIED: 202, VERIFIED: 202}
        assert bodies[UNKNOWN] == bodies[UNVERIFIED] == bodies[VERIFIED]
        assert UNVERIFIED not in str(bodies[UNVERIFIED])
        header_names = {email: sorted(dict(r.headers).keys()) for email, r in answers.items()}
        assert header_names[UNKNOWN] == header_names[UNVERIFIED] == header_names[VERIFIED]

    def test_the_request_path_does_the_same_work_for_every_address(self, world: _World, client: TestClient) -> None:
        """Before the response: one reservation, for all three. Lookup, write and send come after it."""
        before_response: dict[str, list[str]] = {}
        for email in (UNKNOWN, UNVERIFIED, VERIFIED):
            world.order.clear()
            _resend(client, email)
            before_response[email] = world.order[: world.order.index("response-sent")]

        assert before_response == {UNKNOWN: ["reserve"], UNVERIFIED: ["reserve"], VERIFIED: ["reserve"]}

    def test_the_lookup_write_and_send_run_after_the_response(self, world: _World, client: TestClient) -> None:
        _resend(client, UNVERIFIED)

        assert world.order == ["reserve", "response-sent", "lookup", "write", "send"]

    def test_a_service_and_a_federated_only_account_answer_like_an_unknown_address(self, client: TestClient) -> None:
        unknown = _resend(client, UNKNOWN)
        for email in (SERVICE, FEDERATED):
            answer = _resend(client, email)
            assert (answer.status_code, answer.json()) == (unknown.status_code, unknown.json())


class TestTheMail:
    def test_an_unverified_account_gets_a_fresh_token_that_replaces_the_old_one(
        self, world: _World, client: TestClient
    ) -> None:
        _resend(client, UNVERIFIED)

        assert len(world.mail.sent) == 1
        recipient, new_token = world.mail.sent[0]
        assert recipient == UNVERIFIED
        assert new_token != OLD_TOKEN
        stored = world.repo.users[UNVERIFIED]
        assert stored.email_verification_token == new_token
        assert stored.email_verification_expires is not None
        assert stored.email_verification_expires > datetime.now(UTC) + timedelta(hours=23)

        old = client.post("/api/v1/auth/verify-email", json={"token": OLD_TOKEN})
        assert old.status_code == 401
        new = client.post("/api/v1/auth/verify-email", json={"token": new_token})
        assert new.status_code == 200
        assert new.json()["email_verified"] is True

    def test_each_request_issues_a_new_token_and_only_the_last_one_verifies(
        self, world: _World, client: TestClient
    ) -> None:
        _resend(client, UNVERIFIED)
        _resend(client, UNVERIFIED)

        first, second = (token for _, token in world.mail.sent)
        assert first != second
        assert client.post("/api/v1/auth/verify-email", json={"token": first}).status_code == 401
        assert client.post("/api/v1/auth/verify-email", json={"token": second}).status_code == 200
        # Single use: the link that just worked does not work twice.
        assert client.post("/api/v1/auth/verify-email", json={"token": second}).status_code == 401

    @pytest.mark.parametrize("email", [UNKNOWN, VERIFIED, SERVICE, FEDERATED])
    def test_no_mail_and_no_write_for_an_address_that_needs_no_link(
        self, world: _World, client: TestClient, email: str
    ) -> None:
        _resend(client, email)

        assert world.mail.sent == []
        assert "write" not in world.order

    def test_an_inactive_account_gets_no_mail(self, world: _World, client: TestClient) -> None:
        world.repo.users[UNVERIFIED] = world.repo.users[UNVERIFIED].model_copy(update={"is_active": False})

        _resend(client, UNVERIFIED)

        assert world.mail.sent == []

    def test_nothing_is_sent_or_counted_when_verification_is_not_required(self) -> None:
        world = _World(require_verification=False)
        for client in _client(world):
            answers = [_resend(client, email) for email in (UNKNOWN, UNVERIFIED, VERIFIED)]

        assert {r.status_code for r in answers} == {202}
        assert len({r.text for r in answers}) == 1
        assert world.mail.sent == []
        assert world.order == ["response-sent"] * 3

    def test_a_failing_send_answers_like_any_other_request_and_logs_no_address(
        self, world: _World, client: TestClient
    ) -> None:
        reference = _resend(client, UNKNOWN)

        def _boom(**_: object) -> None:
            raise ConnectionRefusedError(f"smtp down for {UNVERIFIED}")

        with (
            patch.object(world.mail, "send_verification_email", side_effect=_boom),
            structlog.testing.capture_logs() as logs,
        ):
            failing = _resend(client, UNVERIFIED)

        assert (failing.status_code, failing.json()) == (reference.status_code, reference.json())
        failed = [entry for entry in logs if entry["event"] == "auth_mail_send_failed"]
        assert [entry["kind"] for entry in failed] == ["verification_resend"]
        assert UNVERIFIED not in repr(logs)


class TestLimits:
    def test_the_per_address_budget_stops_the_mail_without_changing_the_answer(
        self, world: _World, client: TestClient
    ) -> None:
        answers = [_resend(client, UNVERIFIED) for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW + 1)]

        assert len(world.mail.sent) == MAX_VERIFICATION_RESENDS_PER_WINDOW
        assert len({(r.status_code, r.text) for r in answers}) == 1

    def test_the_per_address_budget_counts_unknown_addresses_alike(self, world: _World, client: TestClient) -> None:
        """A budget counted only for real accounts would itself tell which addresses are real."""
        for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW):
            _resend(client, UNKNOWN)

        assert world.budget.reserve_attempt(f"verification-resend:{UNKNOWN}") == MAX_VERIFICATION_RESENDS_PER_WINDOW + 1

    def test_case_variants_of_an_address_share_one_budget(self, world: _World, client: TestClient) -> None:
        """Otherwise every capitalisation of the local part would buy three more mails to the same inbox."""
        variants = [UNVERIFIED, UNVERIFIED.upper(), "Pending@Example.com", "pENDING@example.COM"]
        for email in variants:
            _resend(client, email)

        assert len(world.mail.sent) == MAX_VERIFICATION_RESENDS_PER_WINDOW

    def test_a_variant_that_reaches_the_service_unstripped_still_shares_the_budget(self, world: _World) -> None:
        """The route's ``EmailStr`` strips; the budget does not rely on it (R-9).

        Like ``AuthService.request_password_reset``, the service strips and
        lowercases the address before it puts the prefix in front. The store's
        own normalisation would not carry a leading space: it strips the whole
        subject, so a space between the prefix and the address would survive.
        """
        service = world.service()
        for email in ["a@x.com", " a@x.com", "A@x.com", "a@x.com "]:
            service.resend_verification_email(email)

        assert world.budget.reserve_attempt("verification-resend:a@x.com") == 5

    def test_the_route_is_rate_limited_per_ip(self, client: TestClient) -> None:
        """Distinct addresses, so only the per-IP limit can answer 429."""
        statuses = [_resend(client, f"probe-{i}@example.com").status_code for i in range(_PER_IP_LIMIT + 1)]

        assert statuses[:_PER_IP_LIMIT] == [202] * _PER_IP_LIMIT
        assert statuses[-1] == 429


class TestLoginNamesTheWayOut:
    def test_an_unverified_login_is_refused_with_a_hint_at_the_resend(self, client: TestClient) -> None:
        answer = client.post("/api/v1/auth/login", json={"email": UNVERIFIED, "password": PASSWORD})

        assert answer.status_code == 403
        assert answer.json()["error_code"] == "EMAIL_NOT_VERIFIED"
        assert "request a new verification email" in answer.json()["message"]
