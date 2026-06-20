"""REQ-029 §7 — Redis-backed per-user daily rate limiter for identification.

Implements a fixed 24h window counter. When Redis is unavailable the limiter's
behaviour depends on the call site:

- the *local* (self-hosted, no third-party cost) path degrades gracefully and
  fails **open** — blocking the feature on a cache outage would be a worse
  trade-off than briefly skipping a free, in-cluster rate limit (NFR-007);
- the *external* (third-party, cost-bearing) path fails **closed** (SEC-003):
  a Redis outage must not let a single account hammer a paid/quota'd third-party
  API unbounded. Callers opt into this via ``fail_closed=True``.
"""

import structlog

from app.common.exceptions import RateLimitError

logger = structlog.get_logger()

_DAY_SECONDS = 86_400


class IdentificationRateLimiter:
    """Counts identification calls per user per day in Redis."""

    def __init__(self, redis_client) -> None:  # noqa: ANN001 - redis client is duck-typed
        self._redis = redis_client

    def check_and_increment(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int = _DAY_SECONDS,
        fail_closed: bool = False,
    ) -> None:
        """Increment the daily counter and raise when the limit is exceeded.

        Args:
            key: Stable per-user/per-adapter key (e.g. ``identify:plantnet:<user>``).
            limit: Maximum allowed calls within the window.
            window_seconds: Window length in seconds (default 24h).
            fail_closed: SEC-003 — when ``True`` a Redis outage raises
                :class:`RateLimitError` (reject) instead of degrading open. Used
                for the external, cost-bearing recognition path so a cache outage
                cannot let one account flood a third-party API unbounded. The
                local self-hosted path keeps the default ``False`` (fail-open).

        Raises:
            RateLimitError: when the limit for the window has been reached, or —
                with ``fail_closed=True`` — when the rate-limit store is
                unavailable and the check cannot be performed.
        """
        if limit <= 0:
            return

        redis_key = f"ident_ratelimit:{key}"
        try:
            current = self._redis.incr(redis_key)
            if current == 1:
                self._redis.expire(redis_key, window_seconds)
        except Exception as exc:  # noqa: BLE001 - Redis failure handled per fail_closed
            logger.warning(
                "identification_rate_limit_unavailable",
                error=str(exc),
                fail_closed=fail_closed,
            )
            if fail_closed:
                # Cannot prove the user is under quota → reject rather than risk
                # unbounded third-party calls. 429 signals "retry later".
                raise RateLimitError(key.split(":")[0], retry_after=window_seconds) from exc
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
