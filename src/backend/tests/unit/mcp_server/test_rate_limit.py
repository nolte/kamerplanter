"""SEC-004 — MCP per-key rate limiter (fixed 60s window, fail-closed)."""

from __future__ import annotations

import pytest

from app.common.exceptions import RateLimitError
from app.mcp_server.rate_limit import McpRateLimiter


class _FakeRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.counters: dict = {}
        self.expired: list = []

    def incr(self, key: str) -> int:
        if self.fail:
            raise ConnectionError("redis down")
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int) -> None:
        self.expired.append((key, seconds))

    def ttl(self, key: str) -> int:
        return 42


def test_under_limit_is_allowed_and_sets_expiry():
    limiter = McpRateLimiter(_FakeRedis())
    limiter.check_and_increment(api_key_key="ak-1", limit=3)  # first call, no raise


def test_over_limit_raises_rate_limit_error():
    redis = _FakeRedis()
    limiter = McpRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=2)
    limiter.check_and_increment(api_key_key="ak-1", limit=2)
    with pytest.raises(RateLimitError):
        limiter.check_and_increment(api_key_key="ak-1", limit=2)


def test_zero_limit_is_noop():
    redis = _FakeRedis()
    limiter = McpRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=0)
    assert redis.counters == {}


def test_store_outage_fails_closed():
    # SEC-004: a Redis outage must not degrade open on the external M2M surface.
    limiter = McpRateLimiter(_FakeRedis(fail=True))
    with pytest.raises(RateLimitError):
        limiter.check_and_increment(api_key_key="ak-1", limit=100)


def test_counter_is_scoped_per_key():
    redis = _FakeRedis()
    limiter = McpRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=1)
    # A different key has its own window and is unaffected.
    limiter.check_and_increment(api_key_key="ak-2", limit=1)
    assert redis.counters == {"mcp_ratelimit:ak-1": 1, "mcp_ratelimit:ak-2": 1}
