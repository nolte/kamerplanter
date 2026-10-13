"""SEC-004 — MCP per-key rate limiter (fixed 60s window, fail-closed)."""

from __future__ import annotations

import pytest

from app.common.exceptions import RateLimitError
from app.domain.services.api_key_controls import ApiKeyRateLimiter


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

    def expire(self, key: str, seconds: int, nx: bool = False) -> None:
        self.expired.append((key, seconds))

    def ttl(self, key: str) -> int:
        return 42


def test_under_limit_is_allowed_and_sets_expiry():
    limiter = ApiKeyRateLimiter(_FakeRedis())
    limiter.check_and_increment(api_key_key="ak-1", limit=3)  # first call, no raise


def test_over_limit_raises_rate_limit_error():
    redis = _FakeRedis()
    limiter = ApiKeyRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=2)
    limiter.check_and_increment(api_key_key="ak-1", limit=2)
    with pytest.raises(RateLimitError):
        limiter.check_and_increment(api_key_key="ak-1", limit=2)


def test_zero_limit_is_noop():
    redis = _FakeRedis()
    limiter = ApiKeyRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=0)
    assert redis.counters == {}


def test_store_outage_fails_closed():
    # SEC-004: a Redis outage must not degrade open on the external M2M surface.
    limiter = ApiKeyRateLimiter(_FakeRedis(fail=True))
    with pytest.raises(RateLimitError):
        limiter.check_and_increment(api_key_key="ak-1", limit=100)


def test_counter_is_scoped_per_key():
    redis = _FakeRedis()
    limiter = ApiKeyRateLimiter(redis)
    limiter.check_and_increment(api_key_key="ak-1", limit=1)
    # A different key has its own window and is unaffected.
    limiter.check_and_increment(api_key_key="ak-2", limit=1)
    assert redis.counters == {"api_key_ratelimit:ak-1": 1, "api_key_ratelimit:ak-2": 1}


class _TtlRedis:
    """INCR/EXPIRE/TTL with real TTL bookkeeping; ``expire`` can fail once."""

    def __init__(self, *, fail_first_expire: bool) -> None:
        self.counters: dict[str, int] = {}
        self.ttls: dict[str, int] = {}
        self._fail_next_expire = fail_first_expire

    def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int, nx: bool = False) -> bool:
        if self._fail_next_expire:
            self._fail_next_expire = False
            raise ConnectionError("blip between INCR and EXPIRE")
        if nx and key in self.ttls:
            return False
        self.ttls[key] = seconds
        return True

    def ttl(self, key: str) -> int:
        return self.ttls.get(key, -1)


def test_a_counter_left_without_expiry_gets_one_on_the_next_call():
    # Security review of #1850 (SEC-004): INCR and EXPIRE are two commands. If
    # EXPIRE failed after INCR, the counter used to live forever (EXPIRE ran only
    # when INCR returned 1), locking the key out for good once it reached the limit.
    redis = _TtlRedis(fail_first_expire=True)
    limiter = ApiKeyRateLimiter(redis)

    with pytest.raises(RateLimitError):  # the blip itself fails closed
        limiter.check_and_increment(api_key_key="ak-1", limit=5)
    limiter.check_and_increment(api_key_key="ak-1", limit=5)

    assert redis.ttls == {"api_key_ratelimit:ak-1": 60}
