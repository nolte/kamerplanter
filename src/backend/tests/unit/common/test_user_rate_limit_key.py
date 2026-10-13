"""#2109 — the per-user rate-limit key and the 429 ``Retry-After`` header."""

from __future__ import annotations

from limits import parse
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.requests import Request

from app.api.v1.auth.router import user_rate_limit_key
from app.common.rate_limit import retry_after_seconds
from app.domain.models.user import User


def _request(principal: object = None, *, client: str = "203.0.113.7") -> Request:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/x",
            "headers": [],
            "client": (client, 40000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )
    if principal is not None:
        request.state.kp_principal = principal
    return request


def test_a_resolved_principal_buckets_on_the_account() -> None:
    user = User(_key="user_anna", email="anna@example.org", display_name="Anna")

    assert user_rate_limit_key(_request(("Bearer x", user))) == "user:user_anna"


def test_two_accounts_behind_one_address_get_two_buckets() -> None:
    anna = User(_key="user_anna", email="anna@example.org", display_name="Anna")
    ben = User(_key="user_ben", email="ben@example.org", display_name="Ben")

    assert user_rate_limit_key(_request(("a", anna))) != user_rate_limit_key(_request(("b", ben)))


def test_without_a_principal_the_address_is_the_bucket() -> None:
    assert user_rate_limit_key(_request()) == "ip:203.0.113.7"
    # An optional resolution that found nobody is no principal either.
    assert user_rate_limit_key(_request((None, None))) == "ip:203.0.113.7"


def test_retry_after_falls_back_to_the_window_without_statistics() -> None:
    limit = Limit(parse("30/minute"), lambda r: "k", None, False, None, None, None, 1, False)
    request = _request()
    request.scope["app"] = type("App", (), {"state": type("S", (), {})()})()

    assert retry_after_seconds(request, RateLimitExceeded(limit)) == 60
