"""Every Valkey client of the request paths waits one short socket timeout, not redis-py's five seconds (#2062).

``_get_redis_client()`` and ``RedisOAuthStateStore`` built their client with the
redis-py defaults: **5 s** per connect and per socket read. The clients behind the
anonymous password-reset, resend and login-refusal budgets were bounded in #2045;
the remaining ones sit on request paths as well — the device-pairing throttle and
code store (anonymous ``POST /auth/device-pairing/redeem``), the OAuth state
store (anonymous OAuth login/callback), the API-key limiter (every API-key
request), the MCP session store, the identification limiter. A Valkey that
accepts TCP and never answers therefore held each of those requests for about
five seconds on a thread-pool thread, per Valkey call.

Asserted against a loopback socket that accepts and never answers, through the
production dependency functions and one real route.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from typing import Any

import pytest

from app.common import dependencies
from app.common.exceptions import RateLimitError
from tests.api.test_auth_budget_stores_bounded_wait import (
    _client,
    _post,
    blackhole_url,  # noqa: F401 - the fixture
)

#: One 0.5 s socket timeout, plus generous slack for a loaded CI runner. The
#: redis-py default this replaces is 5 s per socket operation.
_BOUND_S = 2.0

_PAIRING_REDEEM = "/api/v1/auth/device-pairing/redeem"


def _swallow(call: Callable[[], Any]) -> None:
    """Run ``call``; a store that fails closed or loud may raise — only the time it took is measured."""
    with contextlib.suppress(Exception):  # the duration is the subject
        call()


_CALLERS: dict[str, Callable[[], None]] = {
    "default-client": lambda: _swallow(lambda: dependencies._get_redis_client().get("k")),
    "device-pairing-throttle": lambda: dependencies.get_device_pairing_throttle_store().get_failure_state(
        "203.0.113.7"
    ),
    "device-pairing-code-store": lambda: _swallow(lambda: dependencies.get_device_pairing_code_store().consume("c")),
    "oauth-state-store": lambda: _swallow(lambda: dependencies.get_oauth_state_store().get_and_delete("state")),
    "api-key-limiter": lambda: _swallow(
        lambda: dependencies.get_api_key_rate_limiter().check_and_increment(api_key_key="k", limit=10)
    ),
    "mcp-session-store": lambda: dependencies.get_mcp_session_store().is_valid("s", account_key="a"),
}


@pytest.mark.allow_db_connection(
    "connects to a loopback socket this test opens itself, which accepts and never answers — "
    "the hanging-Valkey case needs redis-py's real socket timeouts"
)
class TestAHangingValkeyOnTheOtherRequestPaths:
    @pytest.mark.parametrize("name", sorted(_CALLERS))
    def test_one_call_waits_one_short_timeout(self, blackhole_url: str, name: str) -> None:  # noqa: F811
        started = time.monotonic()
        _CALLERS[name]()
        elapsed = time.monotonic() - started

        print(f"\n{name}: one call against a hanging Valkey took {elapsed:.2f}s")
        assert elapsed < _BOUND_S, f"{name} took {elapsed:.2f}s"

    def test_the_api_key_limiter_still_fails_closed(self, blackhole_url: str) -> None:  # noqa: F811
        """The bound shortens the wait, it does not open the limiter (SEC-004)."""
        with pytest.raises(RateLimitError):
            dependencies.get_api_key_rate_limiter().check_and_increment(api_key_key="k", limit=10)

    def test_the_anonymous_pairing_redemption_answers_within_the_bound(self, blackhole_url: str) -> None:  # noqa: F811
        """The real route: throttle read + code consume both meet the hanging Valkey."""
        from unittest.mock import MagicMock

        from app.common.dependencies import get_auth_service
        from app.domain.services.auth_service import AuthService

        for client in _client(wired=False):
            from app.main import app

            def _service() -> AuthService:
                return AuthService(
                    user_repo=MagicMock(),
                    auth_provider_repo=MagicMock(),
                    refresh_token_repo=MagicMock(),
                    password_engine=MagicMock(),
                    token_engine=MagicMock(),
                    throttle_engine=MagicMock(),
                    email_service=MagicMock(),
                    frontend_url="http://localhost:5173",
                    device_pairing_code_store=dependencies.get_device_pairing_code_store(),
                    device_pairing_throttle_store=dependencies.get_device_pairing_throttle_store(),
                )

            app.dependency_overrides[get_auth_service] = _service
            response, elapsed = _post(client, _PAIRING_REDEEM, {"code": "ABCD-EFGH"})

        print(f"\n{_PAIRING_REDEEM}: one request against a hanging Valkey took {elapsed:.2f}s ({response.status_code})")
        assert elapsed < _BOUND_S, f"the redemption took {elapsed:.2f}s"
        assert response.status_code == 401
