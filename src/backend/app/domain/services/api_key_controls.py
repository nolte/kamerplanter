"""The network controls an API key carries, enforced in one place for REST and MCP (SEC-004, #1850).

An API key may carry two restrictions besides its tenant scope (REQ-023 v1.10):
an ``ip_allowlist`` of CIDR ranges and a ``rate_limit_per_minute`` budget. Until
#1850 only the MCP authenticator read them; on the REST path a ``kp_`` bearer
became its owner's account after the revoked/expiry/active checks, so a key
restricted to ``10.0.0.0/8`` was accepted on every REST route from anywhere and
without its budget — the same one-surface-only shape #1817 fixed for the scope.

:func:`enforce_api_key_controls` is the one implementation both surfaces call
(``AuthService.authenticate_api_key`` and ``McpAuthenticator.authenticate``);
``tests/unit/guards/test_api_key_controls_bind_every_key_surface.py`` holds that
no other code reads the allowlist or builds its own limiter.

**One budget per key.** The counter is keyed on the API key's document key, not
on the surface, so REST and MCP calls of one key draw on the same per-minute
budget — the control is a property of the key.

The limiter fails **closed** on a store outage: a Valkey/Redis blip must not let
one key flood the API unbounded. On any breach — including "counter store
unavailable" — it raises :class:`~app.common.exceptions.RateLimitError` (429).
"""

from __future__ import annotations

import structlog

from app.common.exceptions import RateLimitError, UnauthorizedError
from app.common.log_privacy import loggable_error
from app.domain.models.auth import ApiKey, api_key_ip_admits

logger = structlog.get_logger(__name__)

_WINDOW_SECONDS = 60

#: The one message both surfaces answer for an address outside the allowlist.
IP_NOT_PERMITTED = "Client IP is not permitted for this API key."


class ApiKeyRateLimiter:
    """Redis fixed-window per-minute limiter for API keys (REST and MCP)."""

    def __init__(self, redis_client) -> None:  # noqa: ANN001 - redis client is duck-typed
        self._redis = redis_client

    def check_and_increment(self, *, api_key_key: str, limit: int) -> None:
        """Increment the per-minute counter for ``api_key_key`` and enforce ``limit``.

        Args:
            api_key_key: The API key's ``_key`` — the stable, per-key identity
                the counter is scoped to (never the raw key).
            limit: Maximum allowed calls within the 60s window. ``<= 0`` means
                "no limit configured" and is a no-op.

        Raises:
            RateLimitError: the per-minute limit has been reached, or the counter
                store is unavailable (fail-closed, SEC-004).
        """
        if limit <= 0:
            return

        redis_key = f"api_key_ratelimit:{api_key_key}"
        try:
            current = self._redis.incr(redis_key)
            if current == 1:
                self._redis.expire(redis_key, _WINDOW_SECONDS)
        except Exception as exc:  # noqa: BLE001 - store failure handled fail-closed
            logger.warning("api_key_rate_limit_unavailable", error=loggable_error(exc))
            # Cannot prove the caller is under quota → reject rather than let one
            # key flood the API on a cache outage (SEC-004).
            raise RateLimitError("api_key", retry_after=_WINDOW_SECONDS) from exc

        if current > limit:
            ttl = _WINDOW_SECONDS
            try:
                remaining_ttl = self._redis.ttl(redis_key)
                if isinstance(remaining_ttl, int) and remaining_ttl > 0:
                    ttl = remaining_ttl
            except Exception:  # noqa: BLE001
                pass
            raise RateLimitError("api_key", retry_after=ttl)


def enforce_api_key_controls(
    api_key: ApiKey,
    *,
    client_ip: str | None,
    rate_limiter: ApiKeyRateLimiter | None,
) -> None:
    """Refuse a request the key's ``ip_allowlist`` or ``rate_limit_per_minute`` does not admit.

    Keyword-only without defaults: every caller states the client address it
    resolved and the limiter it holds, so a new key-accepting surface cannot
    skip a control by omission.

    Raises:
        UnauthorizedError: an allowlist is set and the client IP is unresolvable,
            unparsable or outside every listed range — one generic 401, so the
            control cannot be probed.
        RateLimitError: the per-minute budget is spent, or the counter store is
            unavailable (429).
    """
    if not api_key_ip_admits(api_key.ip_allowlist, client_ip):
        raise UnauthorizedError(IP_NOT_PERMITTED)
    limit = api_key.rate_limit_per_minute
    if limit and rate_limiter is not None:
        rate_limiter.check_and_increment(api_key_key=api_key.key or "", limit=limit)
