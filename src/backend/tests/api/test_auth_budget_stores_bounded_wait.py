"""A hanging Valkey costs the anonymous mail budgets one short socket timeout, not five seconds (SEC-001).

The per-address and per-account mail budgets of the sign-in routes — the
password reset (#2043), the anonymous verification resend (#2037) and the
password-proven resend of the unverified login refusal (#2046) — and the
unknown-account lockout counter count in Valkey and fall back to an in-process
tier when it fails. Their client used to come from ``_get_redis_client()``:
redis-py defaults, five seconds per socket read and per connect. A Valkey that
accepts TCP and never answers therefore held **every** reset request and every
unverified-login refusal for about five seconds on a thread-pool thread — the
reset route had not touched Valkey at all before #2043.

Asserted here through the real routes, with the stores built by the production
dependency functions against a loopback socket that accepts and never answers:

* one request, and eight concurrent ones, each answer within a bound far below
  the redis-py default (one 0.5 s socket timeout plus CI slack);
* the answer is byte-identical to the answer with a healthy store — status,
  body (minus the per-response fields) and header names;
* the budget still holds: the store degrades to its in-process tier.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.common import dependencies
from app.common.dependencies import get_auth_service
from app.config.settings import settings
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

OWNER = "owner@example.com"
PENDING = "pending@example.com"
PASSWORD = "A-Long-Enough-Password-2024!"

_RESET = "/api/v1/auth/password-reset/request"
_LOGIN = "/api/v1/auth/login"

#: One 0.5 s socket timeout, plus generous slack for a loaded CI runner. The
#: redis-py default this replaces is 5 s per socket operation.
_BOUND_S = 2.0

#: Concurrent requests in the burst — below the per-IP ``rate_limit_auth``
#: (20/minute) together with the single request, so only the store can slow them.
_CONCURRENT = 8

#: Fields and headers that differ between any two answers whatever the store does.
_PER_RESPONSE_FIELDS = frozenset({"error_id", "timestamp"})
_PER_RESPONSE_HEADERS = frozenset({"date", "x-ratelimit-remaining", "x-ratelimit-reset", "x-request-id"})

_PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)


class _Repo:
    """The user lookups and writes the reset and login flows make, over a dict."""

    def __init__(self) -> None:
        self.users = {
            OWNER: User(_key="4000001", email=OWNER, display_name="Owner", password_hash=_PASSWORD_HASH),
            PENDING: User(
                _key="4000002",
                email=PENDING,
                display_name="Pending",
                password_hash=_PASSWORD_HASH,
                email_verified=False,
            ),
        }

    def get_by_email(self, email: str) -> User | None:
        user = self.users.get(email.lower())
        return user.model_copy(deep=True) if user else None

    def get_by_key(self, key: str) -> User | None:
        found = [u for u in self.users.values() if u.key == key]
        return found[0].model_copy(deep=True) if found else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        user = next(u for u in self.users.values() if u.key == key)
        updated = user.model_validate({**user.model_dump(by_alias=True), **fields})
        self.users[updated.email] = updated
        return updated.model_copy(deep=True)


class _QuietMail(IEmailService):
    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        return None

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        return None


def _service(*, wired: bool) -> AuthService:
    """One service per request, like ``get_auth_service``.

    ``wired``: the budget stores come from the production dependency functions
    (and so from whatever Valkey ``settings.redis_url`` names); otherwise the
    service uses its in-process default stores — the healthy reference.
    """
    stores: dict[str, Any] = {}
    if wired:
        stores = {
            "password_reset_store": dependencies.get_password_reset_store(),
            "verification_resend_store": dependencies.get_verification_resend_store(),
            "verification_resend_proven_store": dependencies.get_verification_resend_proven_store(),
            "unknown_account_store": dependencies.get_unknown_account_store(),
        }
    return AuthService(
        user_repo=_Repo(),  # type: ignore[arg-type]
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=_QuietMail(),
        frontend_url="http://localhost:5173",
        require_email_verification=True,
        **stores,
    )


def _client(*, wired: bool) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: _service(wired=wired)
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


@pytest.fixture
def blackhole_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """``settings.redis_url`` pointing at a loopback port that accepts and never answers."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(64)
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept_and_hold() -> None:
        server.settimeout(0.05)
        while not stop.is_set():
            try:
                connection, _ = server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            held.append(connection)

    acceptor = threading.Thread(target=accept_and_hold, daemon=True)
    acceptor.start()
    url = f"redis://127.0.0.1:{server.getsockname()[1]}/0"
    monkeypatch.setattr(settings, "redis_url", url)
    try:
        yield url
    finally:
        stop.set()
        acceptor.join(timeout=1)
        for connection in held:
            connection.close()
        server.close()


def _post(client: TestClient, path: str, body: dict[str, str]) -> tuple[httpx.Response, float]:
    started = time.monotonic()
    response = client.post(path, json=body)
    return response, time.monotonic() - started


def _burst(client: TestClient, path: str, body: dict[str, str]) -> list[tuple[httpx.Response, float]]:
    start = threading.Barrier(_CONCURRENT)
    results: list[tuple[httpx.Response, float]] = []
    lock = threading.Lock()

    def one() -> None:
        start.wait()
        result = _post(client, path, body)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=one) for _ in range(_CONCURRENT)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return results


def _shape(response: httpx.Response) -> tuple[int, Any, list[str]]:
    try:
        body: Any = response.json()
    except ValueError:
        body = response.content
    if isinstance(body, dict):
        body = {k: v for k, v in body.items() if k not in _PER_RESPONSE_FIELDS}
    headers = sorted(k.lower() for k in response.headers if k.lower() not in _PER_RESPONSE_HEADERS)
    return response.status_code, body, headers


_CASES = [
    pytest.param(_RESET, {"email": OWNER}, id="password-reset-request"),
    pytest.param(_LOGIN, {"email": PENDING, "password": PASSWORD}, id="unverified-login-refusal"),
]


@pytest.mark.allow_db_connection(
    "connects to a loopback socket this test opens itself, which accepts and never answers — "
    "the hanging-Valkey case needs redis-py's real socket timeouts"
)
@pytest.mark.parametrize(("path", "body"), _CASES)
class TestAHangingValkey:
    def test_one_request_waits_one_short_timeout_and_answers_as_if_healthy(
        self, blackhole_url: str, path: str, body: dict[str, str]
    ) -> None:
        for healthy_client in _client(wired=False):
            healthy, _ = _post(healthy_client, path, body)

        for client in _client(wired=True):
            hanging, elapsed = _post(client, path, body)

        print(f"\n{path}: one request against a hanging Valkey took {elapsed:.2f}s")
        assert elapsed < _BOUND_S, f"one request took {elapsed:.2f}s"
        assert _shape(hanging) == _shape(healthy)

    def test_concurrent_requests_each_wait_one_short_timeout(
        self, blackhole_url: str, path: str, body: dict[str, str]
    ) -> None:
        for healthy_client in _client(wired=False):
            healthy, _ = _post(healthy_client, path, body)

        for client in _client(wired=True):
            results = _burst(client, path, body)

        times = sorted(round(elapsed, 2) for _, elapsed in results)
        print(f"\n{path}: {_CONCURRENT} concurrent requests against a hanging Valkey took {times}")
        assert len(results) == _CONCURRENT
        assert max(times) < _BOUND_S, f"slowest request took {max(times):.2f}s"
        assert {_shape(response) == _shape(healthy) for response, _ in results} == {True}


@pytest.mark.allow_db_connection(
    "connects to a loopback socket this test opens itself, which accepts and never answers — "
    "the hanging-Valkey case needs redis-py's real socket timeouts"
)
def test_a_failed_login_for_an_unknown_address_waits_one_short_timeout_per_store_call(blackhole_url: str) -> None:
    """The unknown-account counter makes two store calls per failed login (read the state, record the failure).

    Measured with the redis-py defaults: 10.6 s for one request. The bound is two
    0.5 s timeouts plus the dummy password hash and CI slack.
    """
    body = {"email": "nobody@example.com", "password": "Not-The-Password-2024!"}
    for healthy_client in _client(wired=False):
        healthy, _ = _post(healthy_client, _LOGIN, body)

    for client in _client(wired=True):
        hanging, elapsed = _post(client, _LOGIN, body)

    print(f"\n{_LOGIN} (unknown address): one request against a hanging Valkey took {elapsed:.2f}s")
    assert elapsed < 3.0, f"one request took {elapsed:.2f}s"
    assert _shape(hanging) == _shape(healthy)


#: A store call that does not touch the socket at all — the latch answers it.
_NO_WAIT_S = 0.25


@pytest.mark.allow_db_connection(
    "connects to a loopback socket this test opens itself, which accepts and never answers — "
    "the hanging-Valkey case needs redis-py's real socket timeouts"
)
def test_after_one_request_noticed_the_hang_the_next_ones_do_not_wait(blackhole_url: str) -> None:
    """The throttle client latches like the IP limiter (#2062).

    Measured before: every reset request waited one timeout per store call —
    1.0 s each with the two reservations of #2059 — for as long as Valkey hung.
    Now the first call that meets the hang marks Valkey down for this process,
    and every call until the next probe (1 s later) falls back at once.
    """
    dependencies._throttle_redis_client_for.cache_clear()
    try:
        for client in _client(wired=True):
            first = _post(client, _RESET, {"email": OWNER})
            following = [_post(client, _RESET, {"email": f"other-{i}@example.com"}) for i in range(3)]
    finally:
        dependencies._throttle_redis_client_for.cache_clear()

    times = [round(elapsed, 2) for _, elapsed in following]
    print(f"\n{_RESET}: first {first[1]:.2f}s, then {times}")
    assert first[1] < _BOUND_S
    assert max(times) < _NO_WAIT_S, f"requests after the first still waited: {times}"
    assert {response.status_code for response, _ in [first, *following]} == {200}
