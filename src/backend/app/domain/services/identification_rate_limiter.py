"""REQ-029 §7 — Redis-backed per-user daily rate limiter for identification.

Implements a fixed 24h window counter. When Redis is unavailable the limiter
degrades gracefully (fails open) rather than blocking the feature — the
external service still enforces its own free-tier quota (NFR-007 graceful
degradation).
"""

import structlog

from app.common.exceptions import RateLimitError

logger = structlog.get_logger()

_DAY_SECONDS = 86_400


class IdentificationRateLimiter:
    """Counts identification calls per user per day in Redis."""

    def __init__(self, redis_client) -> None:  # noqa: ANN001 - redis client is duck-typed
        self._redis = redis_client

    def check_and_increment(self, *, key: str, limit: int, window_seconds: int = _DAY_SECONDS) -> None:
        """Increment the daily counter and raise when the limit is exceeded.

        Args:
            key: Stable per-user/per-adapter key (e.g. ``identify:plantnet:<user>``).
            limit: Maximum allowed calls within the window.
            window_seconds: Window length in seconds (default 24h).

        Raises:
            RateLimitError: when the limit for the window has been reached.
        """
        if limit <= 0:
            return

        redis_key = f"ident_ratelimit:{key}"
        try:
            current = self._redis.incr(redis_key)
            if current == 1:
                self._redis.expire(redis_key, window_seconds)
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades open
            logger.warning("identification_rate_limit_unavailable", error=str(exc))
            return

        if current > limit:
            ttl = window_seconds
            try:
                remaining_ttl = self._redis.ttl(redis_key)
                if isinstance(remaining_ttl, int) and remaining_ttl > 0:
                    ttl = remaining_ttl
            except Exception:  # noqa: BLE001
                pass
            raise RateLimitError(key.split(":")[0], retry_after=ttl)
