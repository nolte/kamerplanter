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


def test_redis_failure_fail_open_default_for_local_path():
    """SEC-003 — the local (no-cost) path keeps the graceful fail-open default."""
    redis = MagicMock()
    redis.incr.side_effect = ConnectionError("redis down")
    # fail_closed defaults to False → no raise on a Redis outage.
    IdentificationRateLimiter(redis).check_and_increment(key="assess:local_embedding:u1", limit=5, fail_closed=False)


def test_redis_failure_fail_closed_blocks_external_path():
    """SEC-003 — the external (cost-bearing) path fails closed on a Redis outage."""
    redis = MagicMock()
    redis.incr.side_effect = ConnectionError("redis down")
    limiter = IdentificationRateLimiter(redis)
    with pytest.raises(RateLimitError) as exc:
        limiter.check_and_increment(key="assess:plantnet:u1", limit=5, fail_closed=True)
    # The retry hint falls back to the full window when the store is unreachable.
    assert exc.value.retry_after == 86_400


def test_fail_closed_noop_when_limit_zero():
    """An unlimited (0) configuration is a no-op even with fail_closed=True."""
    redis = MagicMock()
    IdentificationRateLimiter(redis).check_and_increment(key="k", limit=0, fail_closed=True)
    redis.incr.assert_not_called()
