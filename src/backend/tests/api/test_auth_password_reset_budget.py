"""``POST /api/v1/auth/password-reset/request`` — the per-address budget (REQ-023, #2043).

Anonymous, and the caller chooses the recipient. Before #2043 the only bound
was the per-IP ``rate_limit_auth`` (20/minute): one source could mail a fresh
reset link to one inbox twenty times a minute, and every further source added
twenty more. Asserted here on the wire, through the real route:

* after ``MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW`` requests for one address the
  mail stops, while status, body and headers stay exactly those of an accepted
  request — the budget is no oracle;
* the budget is reserved before the account lookup and for every submitted
  address alike, so an unknown address spends it the same way a real one does;
* case variants (and the whitespace ``EmailStr`` strips) of one address share
  one budget; a second address keeps its own;
* a Valkey outage degrades the budget to the in-process tier, it never opens it.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.dependencies import get_auth_service, get_password_reset_store
from app.data_access.external.step_up_throttle import (
    DEFAULT_PASSWORD_RESET_STORE,
    PASSWORD_RESET_WINDOW_SECONDS,
    MemoryStepUpThrottleStore,
    RedisStepUpThrottleStore,
)
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW, AuthService

OWNER = "owner@example.com"
SECOND = "second@example.com"
UNKNOWN = "nobody@example.com"
SERVICE = "robot@example.com"

_ROUTE = "/api/v1/auth/password-reset/request"

#: Requests past the budget in the flood tests — enough to show the mail stays
#: stopped, well below the per-IP ``rate_limit_auth`` (20/minute), so only the
#: per-address budget can be what stops it.
_OVER = 4

#: Headers that differ between any two responses whatever the budget does: the
#: clock, and the per-IP limiter's own countdown. Everything else must match.
_PER_RESPONSE_HEADERS = frozenset({"date", "x-ratelimit-remaining", "x-ratelimit-reset", "x-request-id"})

_PASSWORD_HASH = PasswordEngine().hash_password("A-Long-Enough-Password-2024!")


def _users() -> dict[str, User]:
    return {
        OWNER: User(_key="2000001", email=OWNER, display_name="Owner", password_hash=_PASSWORD_HASH),
        SECOND: User(_key="2000002", email=SECOND, display_name="Second", password_hash=_PASSWORD_HASH),
        SERVICE: User(
            _key="2000003",
            email=SERVICE,
            display_name="Robot",
            password_hash=_PASSWORD_HASH,
            account_type="service",
        ),
    }


class _Repo:
    """The two user-repository calls the flow makes, over a dict, recording into ``order``.

    The lookup matches like ``ArangoUserRepository.get_by_email`` does —
    ``LOWER(doc.email) == LOWER(@email)``, no trimming — so the double accepts
    no address the real query would refuse.
    """

    def __init__(self, order: list[str]) -> None:
        self.users = _users()
        self._order = order

    def get_by_email(self, email: str) -> User | None:
        self._order.append("lookup")
        user = self.users.get(email.lower())
        return user.model_copy(deep=True) if user else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self._order.append("write")
        user = next(u for u in self.users.values() if u.key == key)
        updated = user.model_validate({**user.model_dump(by_alias=True), **fields})
        self.users[updated.email] = updated
        return updated.model_copy(deep=True)


class _CountingMail(IEmailService):
    """Counts every reset mail by recipient; any other mail is not part of this flow."""

    def __init__(self, order: list[str]) -> None:
        self.sent: list[str] = []
        self._order = order

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        raise AssertionError("not part of this flow")

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self._order.append("send")
        self.sent.append(to_email.lower())

    def count(self, email: str) -> int:
        return self.sent.count(email.lower())


class _RecordingBudget(MemoryStepUpThrottleStore):
    """The production in-process tier with the production window, recording each reservation."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(ttl_seconds=PASSWORD_RESET_WINDOW_SECONDS)
        self._order = order

    def reserve_attempt(self, subject: str) -> int:
        self._order.append("reserve")
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
    def __init__(self, budget: Any = None) -> None:
        self.order: list[str] = []
        self.repo = _Repo(self.order)
        self.mail = _CountingMail(self.order)
        self.budget = budget if budget is not None else _RecordingBudget(self.order)

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
            password_reset_store=self.budget,
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


def _request(client: TestClient, email: str) -> httpx.Response:
    response: httpx.Response = client.post(_ROUTE, json={"email": email})
    return response


def _stable_headers(response: httpx.Response) -> list[tuple[str, str]]:
    return sorted((k.lower(), v) for k, v in response.headers.items() if k.lower() not in _PER_RESPONSE_HEADERS)


class TestTheBudgetStopsTheMail:
    def test_one_address_gets_no_more_mails_than_the_budget(self, world: _World, client: TestClient) -> None:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + _OVER):
            _request(client, OWNER)

        assert world.mail.count(OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW

    def test_a_request_over_the_budget_answers_byte_identically_to_an_accepted_one(
        self, world: _World, client: TestClient
    ) -> None:
        answers = [_request(client, OWNER) for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1)]
        accepted, refused = answers[0], answers[-1]

        assert world.mail.count(OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW
        assert refused.status_code == accepted.status_code == 200
        assert refused.content == accepted.content
        assert _stable_headers(refused) == _stable_headers(accepted)
        # The per-IP countdown is present and simply one lower: the budget adds no header.
        assert {k.lower() for k in refused.headers} == {k.lower() for k in accepted.headers}

    def test_the_budget_is_reserved_before_the_lookup_and_before_the_response(
        self, world: _World, client: TestClient
    ) -> None:
        _request(client, OWNER)

        # Two reservations since #2059: per address and source, then per address.
        assert world.order == ["reserve", "reserve", "lookup", "response-sent", "write", "send"]

    def test_over_the_budget_nothing_after_the_reservation_runs(self, world: _World, client: TestClient) -> None:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW):
            _request(client, OWNER)
        world.order.clear()

        _request(client, OWNER)

        assert world.order == ["reserve", "response-sent"]


class TestEveryAddressSpendsTheBudgetAlike:
    def test_an_unknown_address_spends_it_like_a_registered_one(self, world: _World, client: TestClient) -> None:
        """A budget counted only for real accounts would itself tell which addresses are real."""
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW):
            _request(client, UNKNOWN)

        assert world.budget.reserve_attempt(f"password-reset:{UNKNOWN}") == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1

    def test_unknown_service_and_registered_addresses_answer_alike_inside_and_over_the_budget(
        self, client: TestClient
    ) -> None:
        answers = [
            _request(client, email)
            for email in (UNKNOWN, SERVICE, OWNER)
            for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1)
        ]

        assert answers[0].status_code == 200
        assert {(r.status_code, r.content) for r in answers} == {(answers[0].status_code, answers[0].content)}
        assert len({tuple(_stable_headers(r)) for r in answers}) == 1


class TestOneBudgetPerAddress:
    def test_case_and_whitespace_variants_share_one_budget(self, world: _World, client: TestClient) -> None:
        """Otherwise every capitalisation of the local part would buy three more mails to the same inbox."""
        variants = [OWNER, OWNER.upper(), "Owner@Example.com", f"  {OWNER}  ", "oWNER@example.COM", f"\t{OWNER}"]
        for email in variants:
            _request(client, email)

        assert world.mail.count(OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW

    def test_a_variant_that_reaches_the_service_unstripped_still_shares_the_budget(self, world: _World) -> None:
        """The route's ``EmailStr`` strips; the budget does not rely on it.

        The service strips and lowercases the address before it puts the prefix in
        front (``AuthService.request_password_reset``). The store's own
        normalisation would not carry this: it strips the whole subject, so a space
        between the prefix and the address would survive it.
        """
        service = world.service()
        for email in (f" {OWNER.upper()} ", OWNER, "Owner@Example.com"):
            service.request_password_reset(email, client_ip="testclient")

        assert world.budget.reserve_attempt(f"password-reset:{OWNER}") == 4

    def test_a_second_address_keeps_its_own_budget(self, world: _World, client: TestClient) -> None:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + _OVER):
            _request(client, OWNER)

        _request(client, SECOND)

        assert world.mail.count(OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW
        assert world.mail.count(SECOND) == 1

    def test_the_budget_is_not_the_resend_budget(self, world: _World, client: TestClient) -> None:
        """Own subject prefix: an exhausted resend budget does not spend the reset budget."""
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + _OVER):
            world.budget.reserve_attempt(f"verification-resend:{OWNER}")

        _request(client, OWNER)

        assert world.mail.count(OWNER) == 1


class TestAStorageOutage:
    def test_the_route_stays_bounded_when_valkey_is_down(self) -> None:
        fallback = MemoryStepUpThrottleStore(ttl_seconds=PASSWORD_RESET_WINDOW_SECONDS)
        world = _World(budget=RedisStepUpThrottleStore(_BrokenRedis(), ttl_seconds=60, fallback=fallback))
        for client in _client(world):
            answers = [_request(client, OWNER) for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + _OVER)]

        assert {r.status_code for r in answers} == {200}
        assert world.mail.count(OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW
        # Every request counted in the per-source stage (#2059); only the admitted
        # ones reached the per-address stage.
        assert (
            fallback.reserve_attempt(f"password-reset-source:{OWNER}|testclient")
            == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + _OVER + 1
        )
        assert fallback.reserve_attempt(f"password-reset:{OWNER}") == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1

    def test_the_wired_store_degrades_to_its_own_in_process_tier(self) -> None:
        subject = "password-reset:outage-probe-2043@example.com"
        with patch("app.common.dependencies._get_throttle_redis_client", return_value=_BrokenRedis()):
            store = get_password_reset_store()
        before = DEFAULT_PASSWORD_RESET_STORE.reserve_attempt(subject)

        assert store.reserve_attempt(subject) == before + 1
        DEFAULT_PASSWORD_RESET_STORE.clear(subject)

    def test_the_wired_store_counts_in_the_shared_tier_with_a_one_hour_window(self) -> None:
        redis = _CountingRedis()
        with patch("app.common.dependencies._get_throttle_redis_client", return_value=redis):
            store = get_password_reset_store()

        counts = [store.reserve_attempt(f"password-reset:{OWNER}") for _ in range(2)]

        assert counts == [1, 2]
        assert set(redis.expiries.values()) == {PASSWORD_RESET_WINDOW_SECONDS} == {3_600}
