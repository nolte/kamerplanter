"""``POST /api/v1/auth/login`` — a refused correct password mails a fresh verification link (REQ-023 §3.2b, #2046).

Before #2046 the only way to a new link was the anonymous
``POST /auth/resend-verification``. Its per-address budget is reserved for every
caller alike, so anyone could spend it for someone else's address and keep the
owner from ever getting a link. The login refusal ``EMAIL_NOT_VERIFIED`` is
reached only by a caller who has just presented the correct password, so that
branch may issue the link itself — on a budget of its own, keyed by the account,
which an anonymous caller cannot touch. Asserted here on the wire, through the
real routes:

* the refusal (status, body, header names) is unchanged, and one fresh link is
  mailed after the response; the link it replaces stops working;
* a wrong password answers exactly as before and mails nothing;
* an exhausted anonymous budget does not stop the proven path;
* the proven path has its own budget (``verification-resend-proven:<user_key>``,
  three per hour, digested like the others); over it the refusal is the same
  and nothing is mailed;
* a failing mail adapter and a Valkey outage change nothing in the answer, and
  the outage degrades the budget to the in-process tier instead of opening it.

The last class measures the framework behaviour the design rests on: tasks added
to ``BackgroundTasks`` run only when the handler *returns* a response.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
import structlog
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.dependencies import get_auth_service
from app.data_access.external.step_up_throttle import (
    VERIFICATION_RESEND_WINDOW_SECONDS,
    MemoryStepUpThrottleStore,
    RedisStepUpThrottleStore,
)
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import MAX_VERIFICATION_RESENDS_PER_WINDOW, AuthService

PENDING = "pending@example.com"
PENDING_KEY = "3000001"
UNKNOWN = "nobody@example.com"
PASSWORD = "A-Long-Enough-Password-2024!"
WRONG_PASSWORD = "Not-The-Password-2024!"
OLD_TOKEN = "the-token-of-the-lost-first-mail"

_LOGIN = "/api/v1/auth/login"
_RESEND = "/api/v1/auth/resend-verification"

#: ``settings.rate_limit_resend_verification`` ("10/hour"): the whole anonymous
#: allowance of one source, spent on one address.
_ANONYMOUS_REQUESTS = 10

#: Body fields that differ between any two error answers: a fresh id and the clock.
_PER_RESPONSE_FIELDS = frozenset({"error_id", "timestamp"})

#: Headers that differ between any two responses whatever the budget does.
_PER_RESPONSE_HEADERS = frozenset({"date", "x-ratelimit-remaining", "x-ratelimit-reset", "x-request-id"})

#: The refusal as it was before #2046, minus the per-response fields. Pinned
#: literally: the new path must not change one character of it.
_REFUSAL = {
    "error_code": "EMAIL_NOT_VERIFIED",
    "message": (
        "Email address has not been verified. "
        "You can request a new verification email if the link was lost or has expired."
    ),
    "details": [],
    "path": _LOGIN,
    "method": "POST",
}

#: The wrong-password answer as it was before #2046, minus the per-response fields.
_WRONG_PASSWORD = {
    "error_code": "UNAUTHORIZED",
    "message": "Invalid email or password.",
    "details": [],
    "path": _LOGIN,
    "method": "POST",
}

_PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)


def _pending() -> User:
    return User(
        _key=PENDING_KEY,
        email=PENDING,
        display_name="Pending",
        password_hash=_PASSWORD_HASH,
        email_verified=False,
        email_verification_token=OLD_TOKEN,
        email_verification_expires=datetime.now(UTC) + timedelta(hours=1),
    )


class _Repo:
    """The user-repository calls login, resend and verify make, over a dict, recording writes.

    ``get_by_email`` matches like ``ArangoUserRepository.get_by_email`` —
    ``LOWER(doc.email) == LOWER(@email)``, no trimming.
    """

    def __init__(self, order: list[str]) -> None:
        self.users = {PENDING: _pending()}
        self._order = order

    def get_by_email(self, email: str) -> User | None:
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


class _CountingMail(IEmailService):
    """Counts every verification mail as ``(recipient, token)``; a reset mail is not part of this flow."""

    def __init__(self, order: list[str]) -> None:
        self.sent: list[tuple[str, str]] = []
        self._order = order

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self._order.append("send")
        self.sent.append((to_email, token))

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        raise AssertionError("not part of this flow")


class _RecordingBudget(MemoryStepUpThrottleStore):
    """The production in-process tier with the production window, recording each subject reserved."""

    def __init__(self, order: list[str], label: str) -> None:
        super().__init__(ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS)
        self._order = order
        self._label = label
        self.subjects: list[str] = []

    def reserve_attempt(self, subject: str) -> int:
        self._order.append(self._label)
        self.subjects.append(subject)
        return super().reserve_attempt(subject)


class _BrokenPipeline:
    def incr(self, *_: object) -> _BrokenPipeline:
        return self

    def expire(self, *_: object) -> _BrokenPipeline:
        return self

    def execute(self) -> list[object]:
        raise ConnectionError("valkey unreachable")


class _BrokenRedis:
    """Valkey down: every call the store makes raises."""

    def pipeline(self, transaction: bool = True) -> _BrokenPipeline:
        return _BrokenPipeline()

    def get(self, name: str) -> str | None:
        raise ConnectionError("valkey unreachable")

    def ttl(self, name: str) -> int:
        raise ConnectionError("valkey unreachable")

    def delete(self, *names: str) -> object:
        raise ConnectionError("valkey unreachable")


class _RecordingPipeline:
    def __init__(self, redis: _CountingRedis) -> None:
        self._redis = redis
        self._ops: list[tuple[str, str, int]] = []

    def incr(self, key: str) -> _RecordingPipeline:
        self._ops.append(("incr", key, 0))
        return self

    def expire(self, key: str, seconds: int) -> _RecordingPipeline:
        self._ops.append(("expire", key, seconds))
        return self

    def execute(self) -> list[object]:
        results: list[object] = []
        for op, key, seconds in self._ops:
            if op == "incr":
                self._redis.counts[key] = self._redis.counts.get(key, 0) + 1
                results.append(self._redis.counts[key])
            else:
                self._redis.expiries[key] = seconds
                results.append(True)
        return results


class _CountingRedis:
    """The shared tier, up: counts ``INCR`` per key and records each ``EXPIRE``."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.expiries: dict[str, int] = {}

    def pipeline(self, transaction: bool = True) -> _RecordingPipeline:
        return _RecordingPipeline(self)

    def get(self, name: str) -> str | None:
        return None

    def ttl(self, name: str) -> int:
        return -2

    def delete(self, *names: str) -> object:
        return 0


class _OrderRecordingApp:
    """Marks the moment the response body has left the app, in the same log as the work."""

    def __init__(self, app: ASGIApp, log: list[str]) -> None:
        self._app = app
        self._log = log

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def _send(message: Message) -> None:
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                self._log.append("response-sent")
            await send(message)

        await self._app(scope, receive, _send)


class _World:
    """One service per request over shared doubles, like ``get_auth_service``.

    ``proven`` is passed to the service only when given: without it the service
    falls back to its own process-wide default store — the production default,
    which ``tests/conftest.py`` clears around every test.
    """

    def __init__(self, proven: Any = None) -> None:
        self.order: list[str] = []
        self.repo = _Repo(self.order)
        self.mail = _CountingMail(self.order)
        self.anonymous = _RecordingBudget(self.order, "reserve-anonymous")
        self.proven = proven

    def service(self) -> AuthService:
        extra: dict[str, Any] = {} if self.proven is None else {"verification_resend_proven_store": self.proven}
        return AuthService(
            user_repo=self.repo,  # type: ignore[arg-type]
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="http://localhost:5173",
            require_email_verification=True,
            verification_resend_store=self.anonymous,
            **extra,
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


def _login(client: TestClient, email: str = PENDING, password: str = PASSWORD) -> httpx.Response:
    response: httpx.Response = client.post(_LOGIN, json={"email": email, "password": password})
    return response


def _stable_body(response: httpx.Response) -> dict[str, Any]:
    body: dict[str, Any] = response.json()
    assert body.keys() >= _PER_RESPONSE_FIELDS
    return {k: v for k, v in body.items() if k not in _PER_RESPONSE_FIELDS}


def _stable_headers(response: httpx.Response) -> list[tuple[str, str]]:
    return sorted((k.lower(), v) for k, v in response.headers.items() if k.lower() not in _PER_RESPONSE_HEADERS)


def _header_names(response: httpx.Response) -> set[str]:
    return {k.lower() for k in response.headers}


class TestTheProvenRefusalMailsAFreshLink:
    def test_the_refusal_is_unchanged_and_one_fresh_link_is_mailed(self, world: _World, client: TestClient) -> None:
        answer = _login(client)

        assert answer.status_code == 403
        assert _stable_body(answer) == _REFUSAL
        assert world.mail.sent and len(world.mail.sent) == 1
        recipient, token = world.mail.sent[0]
        assert recipient == PENDING
        assert token != OLD_TOKEN
        stored = world.repo.users[PENDING]
        assert stored.email_verification_token == token
        assert stored.email_verification_expires is not None
        assert stored.email_verification_expires > datetime.now(UTC) + timedelta(hours=23)

    def test_the_new_link_replaces_the_old_one(self, world: _World, client: TestClient) -> None:
        _login(client)
        (_, token), *_ = world.mail.sent

        assert client.post("/api/v1/auth/verify-email", json={"token": OLD_TOKEN}).status_code == 401
        verified = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert verified.status_code == 200
        assert verified.json()["email_verified"] is True

    def test_the_token_write_and_the_mail_run_after_the_response(self, world: _World, client: TestClient) -> None:
        _login(client)

        assert world.order == ["response-sent", "write", "send"]

    def test_the_mail_goes_to_the_stored_spelling_not_the_typed_one(self, world: _World, client: TestClient) -> None:
        _login(client, email="Pending@Example.COM")

        assert [recipient for recipient, _ in world.mail.sent] == [PENDING]

    def test_a_mailed_refusal_carries_the_headers_of_a_refusal_that_mails_nothing(self, client: TestClient) -> None:
        answers = [_login(client) for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW + 1)]
        mailed, silent = answers[0], answers[-1]

        assert _stable_body(mailed) == _stable_body(silent) == _REFUSAL
        assert _stable_headers(mailed) == _stable_headers(silent)

    def test_the_returned_refusal_has_the_header_names_of_a_raised_error(self, client: TestClient) -> None:
        """The wrong-password answer still leaves through the exception handler; the refusal must look the same."""
        refusal = _login(client)
        wrong = _login(client, password=WRONG_PASSWORD)

        assert _header_names(refusal) == _header_names(wrong)
        assert "set-cookie" not in _header_names(refusal)


class TestAWrongPasswordIsUnchanged:
    def test_the_answer_is_the_one_before_the_change_and_nothing_is_mailed(
        self, world: _World, client: TestClient
    ) -> None:
        wrong = _login(client, password=WRONG_PASSWORD)
        unknown = _login(client, email=UNKNOWN, password=WRONG_PASSWORD)

        assert wrong.status_code == unknown.status_code == 401
        assert _stable_body(wrong) == _stable_body(unknown) == _WRONG_PASSWORD
        assert _stable_headers(wrong) == _stable_headers(unknown)
        assert world.mail.sent == []
        assert world.repo.users[PENDING].email_verification_token == OLD_TOKEN


class TestTheAnonymousBudgetCannotLockTheOwnerOut:
    def test_an_exhausted_anonymous_budget_does_not_stop_the_proven_path(
        self, world: _World, client: TestClient
    ) -> None:
        resends = [client.post(_RESEND, json={"email": PENDING}) for _ in range(_ANONYMOUS_REQUESTS)]
        assert {r.status_code for r in resends} == {202}
        anonymous_mails = len(world.mail.sent)
        assert anonymous_mails == MAX_VERIFICATION_RESENDS_PER_WINDOW
        assert world.anonymous.reserve_attempt(f"verification-resend:{PENDING}") > MAX_VERIFICATION_RESENDS_PER_WINDOW

        answer = _login(client)

        assert _stable_body(answer) == _REFUSAL
        assert len(world.mail.sent) == anonymous_mails + 1

    def test_the_proven_path_does_not_spend_the_anonymous_budget(self, world: _World, client: TestClient) -> None:
        _login(client)

        assert "reserve-anonymous" not in world.order


class TestTheProvenBudget:
    def test_three_mails_an_hour_then_the_same_refusal_without_mail(self, world: _World, client: TestClient) -> None:
        answers = [_login(client) for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW + 2)]

        assert len(world.mail.sent) == MAX_VERIFICATION_RESENDS_PER_WINDOW == 3
        assert {r.status_code for r in answers} == {403}
        assert all(_stable_body(r) == _REFUSAL for r in answers)

    def test_the_budget_is_keyed_by_the_account_under_its_own_prefix(self) -> None:
        world = _World()
        world.proven = _RecordingBudget(world.order, "reserve-proven")
        for client in _client(world):
            _login(client)
            _login(client, email="PENDING@example.com")

        assert world.proven.subjects == [f"verification-resend-proven:{PENDING_KEY}"] * 2
        assert world.order[0] == "reserve-proven"
        assert world.order.index("reserve-proven") < world.order.index("response-sent")

    def test_over_the_budget_nothing_after_the_reservation_runs(self) -> None:
        world = _World()
        world.proven = _RecordingBudget(world.order, "reserve-proven")
        for client in _client(world):
            for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW):
                _login(client)
            world.order.clear()
            _login(client)

        assert world.order == ["reserve-proven", "response-sent"]

    def test_a_wrong_password_reserves_nothing(self) -> None:
        world = _World()
        world.proven = _RecordingBudget(world.order, "reserve-proven")
        for client in _client(world):
            answer = _login(client, password=WRONG_PASSWORD)

        assert (answer.status_code, _stable_body(answer)) == (401, _WRONG_PASSWORD)
        assert world.proven.subjects == []

    def test_the_shared_tier_stores_a_digest_with_a_one_hour_window(self) -> None:
        redis = _CountingRedis()
        world = _World(
            proven=RedisStepUpThrottleStore(
                redis,
                ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS,
                fallback=MemoryStepUpThrottleStore(ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS),
            )
        )
        for client in _client(world):
            _login(client)

        digest = hashlib.sha256(f"verification-resend-proven:{PENDING_KEY}".encode()).hexdigest()
        assert redis.counts == {f"kp:auth:stepup:count:{digest}": 1}
        assert set(redis.expiries.values()) == {3_600}
        assert PENDING not in repr(redis.counts) and PENDING_KEY not in repr(redis.counts)

    def test_the_wired_store_degrades_to_its_own_in_process_tier(self) -> None:
        from app.common.dependencies import get_verification_resend_proven_store
        from app.data_access.external.step_up_throttle import (
            DEFAULT_VERIFICATION_RESEND_PROVEN_STORE,
            DEFAULT_VERIFICATION_RESEND_STORE,
        )

        assert DEFAULT_VERIFICATION_RESEND_PROVEN_STORE is not DEFAULT_VERIFICATION_RESEND_STORE
        subject = f"verification-resend-proven:{PENDING_KEY}"
        with patch("app.common.dependencies._get_redis_client", return_value=_BrokenRedis()):
            store = get_verification_resend_proven_store()
        before = DEFAULT_VERIFICATION_RESEND_PROVEN_STORE.reserve_attempt(subject)

        assert store.reserve_attempt(subject) == before + 1

    def test_the_wired_store_counts_in_the_shared_tier_with_a_one_hour_window(self) -> None:
        from app.common.dependencies import get_verification_resend_proven_store

        redis = _CountingRedis()
        with patch("app.common.dependencies._get_redis_client", return_value=redis):
            store = get_verification_resend_proven_store()

        counts = [store.reserve_attempt(f"verification-resend-proven:{PENDING_KEY}") for _ in range(2)]

        assert counts == [1, 2]
        assert set(redis.expiries.values()) == {VERIFICATION_RESEND_WINDOW_SECONDS} == {3_600}

    def test_the_production_wiring_passes_the_proven_store(self) -> None:
        from app.common import dependencies

        sentinel = MemoryStepUpThrottleStore()
        with (
            patch.object(dependencies, "get_verification_resend_proven_store", return_value=sentinel),
            patch.object(dependencies, "get_db"),
            patch.object(dependencies, "_get_redis_client"),
        ):
            service = dependencies.get_auth_service()

        assert service._verification_resend_proven_store is sentinel


class TestFailuresChangeNothing:
    def test_a_failing_mail_adapter_leaves_the_refusal_unchanged_and_logs_no_address(
        self, world: _World, client: TestClient
    ) -> None:
        def _boom(**_: object) -> None:
            raise ConnectionRefusedError(f"smtp down for {PENDING}")

        with (
            patch.object(world.mail, "send_verification_email", side_effect=_boom),
            structlog.testing.capture_logs() as logs,
        ):
            failing = _login(client)
        working = _login(client)

        assert failing.status_code == working.status_code == 403
        assert _stable_body(failing) == _stable_body(working) == _REFUSAL
        assert _stable_headers(failing) == _stable_headers(working)
        failed = [entry for entry in logs if entry["event"] == "auth_mail_send_failed"]
        assert [entry["kind"] for entry in failed] == ["verification_resend_proven"]
        assert PENDING not in repr(logs)

    def test_a_valkey_outage_keeps_the_budget_in_the_in_process_tier(self) -> None:
        fallback = MemoryStepUpThrottleStore(ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS)
        world = _World(
            proven=RedisStepUpThrottleStore(
                _BrokenRedis(),
                ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS,
                fallback=fallback,
            )
        )
        for client in _client(world):
            answers = [_login(client) for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW + 2)]

        assert {r.status_code for r in answers} == {403}
        assert all(_stable_body(r) == _REFUSAL for r in answers)
        assert len(world.mail.sent) == MAX_VERIFICATION_RESENDS_PER_WINDOW
        subject = f"verification-resend-proven:{PENDING_KEY}"
        assert fallback.reserve_attempt(subject) == MAX_VERIFICATION_RESENDS_PER_WINDOW + 2 + 1


class TestBackgroundTasksRunOnlyOnAReturnedResponse:
    """The measurement the route's shape rests on (#2046 hypothesis 2).

    The login route used to let ``EmailNotVerifiedError`` propagate to the
    exception handler. A task added to the injected ``BackgroundTasks`` before
    such a raise is dropped: FastAPI attaches the tasks only to a response the
    handler *returns*. So the route returns the refusal it would otherwise raise.
    """

    @staticmethod
    def _app(ran: list[str]) -> FastAPI:
        class _RefusedError(Exception):
            pass

        app = FastAPI()

        @app.exception_handler(_RefusedError)
        async def _handler(request: Request, exc: _RefusedError) -> JSONResponse:
            return JSONResponse(status_code=403, content={"error_code": "X"})

        @app.post("/raises")
        def _raises(tasks: BackgroundTasks) -> None:
            tasks.add_task(ran.append, "raises")
            raise _RefusedError

        @app.post("/returns")
        def _returns(tasks: BackgroundTasks) -> JSONResponse:
            tasks.add_task(ran.append, "returns")
            return JSONResponse(status_code=403, content={"error_code": "X"})

        return app

    def test_a_task_added_before_a_raise_never_runs(self) -> None:
        ran: list[str] = []
        answer = TestClient(self._app(ran)).post("/raises")

        assert (answer.status_code, answer.json()) == (403, {"error_code": "X"})
        assert ran == []

    def test_a_task_added_before_a_returned_error_response_runs(self) -> None:
        ran: list[str] = []
        answer = TestClient(self._app(ran)).post("/returns")

        assert (answer.status_code, answer.json()) == (403, {"error_code": "X"})
        assert ran == ["returns"]
