"""REQ-029 §7 — per-user daily rate limiter (Redis mocked)."""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import RateLimitError
from app.domain.services.identification_rate_limiter import IdentificationRateLimiter


def test_first_call_sets_expiry():
    redis = MagicMock()
    redis.incr.return_value = 1
    limiter = IdentificationRateLimiter(redis)

    limiter.check_and_increment(key="identify:plantnet:u1", limit=5)

    redis.incr.assert_called_once_with("ident_ratelimit:identify:plantnet:u1")
    redis.expire.assert_called_once()


def test_within_limit_does_not_raise():
    redis = MagicMock()
    redis.incr.return_value = 3
    IdentificationRateLimiter(redis).check_and_increment(key="k", limit=5)


def test_over_limit_raises():
    redis = MagicMock()
    redis.incr.return_value = 6
    redis.ttl.return_value = 1200
    limiter = IdentificationRateLimiter(redis)

    with pytest.raises(RateLimitError) as exc:
        limiter.check_and_increment(key="identify:plantnet:u1", limit=5)
    assert exc.value.retry_after == 1200


def test_zero_limit_is_noop():
    redis = MagicMock()
    IdentificationRateLimiter(redis).check_and_increment(key="k", limit=0)
    redis.incr.assert_not_called()


def test_redis_failure_degrades_open():
    redis = MagicMock()
    redis.incr.side_effect = ConnectionError("redis down")
    # Must not raise — feature stays usable, external quota still applies.
    IdentificationRateLimiter(redis).check_and_increment(key="k", limit=5)
