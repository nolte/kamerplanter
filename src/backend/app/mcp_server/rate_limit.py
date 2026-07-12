"""REQ-033 §4.3 / REQ-023 v1.10 — per-API-key rate limiting for MCP (SEC-004).

Service-account API keys may carry a ``rate_limit_per_minute`` control
(:class:`app.domain.models.auth.ApiKey`). The MCP authenticator enforces it on
every request via a Redis fixed-window counter, mirroring the pattern of
:class:`app.domain.services.identification_rate_limiter.IdentificationRateLimiter`
(the same INCR + EXPIRE window primitive) but scoped per API key and per minute.

The MCP surface is an *external, machine-to-machine* attack surface, so the
limiter fails **closed** on a store outage (SEC-004): a Valkey/Redis blip must
not let one service account flood the tool dispatcher unbounded. On any breach —
including "counter store unavailable" — it raises
:class:`app.common.exceptions.RateLimitError` (HTTP 429).
"""

from __future__ import annotations

import structlog

from app.common.exceptions import RateLimitError

logger = structlog.get_logger(__name__)

_WINDOW_SECONDS = 60


class McpRateLimiter:
    """Redis fixed-window per-minute limiter for MCP service-account keys."""

    def __init__(self, redis_client) -> None:  # noqa: ANN001 - redis client is duck-typed
        self._redis = redis_client

    def check_and_increment(self, *, api_key_key: str, limit: int) -> None:
        """Increment the per-minute counter for ``api_key_key`` and enforce ``limit``.

        Args:
            api_key_key: The service-account API key's ``_key`` — the stable,
                per-key identity the counter is scoped to (never the raw key).
            limit: Maximum allowed MCP calls within the 60s window. ``<= 0``
                means "no limit configured" and is a no-op.

        Raises:
            RateLimitError: the per-minute limit has been reached, or the counter
                store is unavailable (fail-closed — the external M2M surface must
                not degrade open, SEC-004).
        """
        if limit <= 0:
            return

        redis_key = f"mcp_ratelimit:{api_key_key}"
        try:
            current = self._redis.incr(redis_key)
            if current == 1:
                self._redis.expire(redis_key, _WINDOW_SECONDS)
        except Exception as exc:  # noqa: BLE001 - store failure handled fail-closed
            logger.warning("mcp_rate_limit_unavailable", error=str(exc))
            # Cannot prove the caller is under quota → reject rather than let one
            # account flood the tool dispatcher on a cache outage (SEC-004).
            raise RateLimitError("mcp", retry_after=_WINDOW_SECONDS) from exc

        if current > limit:
            ttl = _WINDOW_SECONDS
            try:
                remaining_ttl = self._redis.ttl(redis_key)
                if isinstance(remaining_ttl, int) and remaining_ttl > 0:
                    ttl = remaining_ttl
            except Exception:  # noqa: BLE001
                pass
            raise RateLimitError("mcp", retry_after=ttl)
