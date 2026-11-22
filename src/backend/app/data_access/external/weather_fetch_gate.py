"""REQ-046 §3.6a (#2934) — Valkey-backed running lock and manual-fetch cooldown.

Both are a single ``SET key value NX EX ttl`` (the claim shape of
``step_up_code_store.py`` / ``rendition_dispatch_claims.py``): check and take in
one round trip, so two racing callers cannot both see "free". The lock carries a
random token and is released by a compare-and-delete script, so a run whose lock
already expired never deletes the lock of the run that took over.

There is deliberately **no** in-process fallback: the API process and the Celery
worker are different processes, a local tier would tell each of them "free". A
Valkey error surfaces as :class:`WeatherFetchGateUnavailableError`; the caller
decides (the fetch task runs unlocked, the manual trigger answers 503).
"""

import secrets
from typing import Protocol

import structlog
from redis.exceptions import RedisError

from app.common.log_privacy import loggable_error
from app.domain.interfaces.weather_fetch import IWeatherFetchGate, WeatherFetchGateUnavailableError

logger = structlog.get_logger(__name__)

_PREFIX = "kp:weather:fetch:"
RUN_LOCK_KEY = f"{_PREFIX}running"
MANUAL_COOLDOWN_KEY = f"{_PREFIX}manual-cooldown"

#: Delete the lock only while it still carries our token.
_RELEASE_SCRIPT = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


class _GateRedis(Protocol):
    """The Redis calls this gate makes, typed so a fake can stand in."""

    def set(self, name: str, value: str, ex: int | None = ..., nx: bool = ...) -> object: ...

    def exists(self, *names: str) -> int: ...

    def ttl(self, name: str) -> int: ...

    def delete(self, *names: str) -> int: ...

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> object: ...


class RedisWeatherFetchGate(IWeatherFetchGate):
    """Running lock + cooldown in Valkey, shared by the API and every worker."""

    def __init__(self, redis_client: _GateRedis) -> None:
        self._redis = redis_client

    def _unavailable(self, operation: str, exc: Exception) -> WeatherFetchGateUnavailableError:
        logger.warning("weather_fetch_gate_unavailable", operation=operation, error=loggable_error(exc))
        return WeatherFetchGateUnavailableError(operation)

    def acquire_run_lock(self, ttl_seconds: int) -> str | None:
        token = secrets.token_hex(16)
        try:
            claimed = self._redis.set(RUN_LOCK_KEY, token, ex=ttl_seconds, nx=True)
        except (RedisError, OSError) as exc:
            raise self._unavailable("acquire_run_lock", exc) from exc
        return token if claimed else None

    def release_run_lock(self, token: str) -> None:
        try:
            self._redis.eval(_RELEASE_SCRIPT, 1, RUN_LOCK_KEY, token)
        except (RedisError, OSError) as exc:
            # The lock expires on its own; a failed release only delays the next run.
            logger.warning("weather_fetch_lock_release_failed", error=loggable_error(exc))

    def is_running(self) -> bool:
        try:
            return bool(self._redis.exists(RUN_LOCK_KEY))
        except (RedisError, OSError) as exc:
            raise self._unavailable("is_running", exc) from exc

    def claim_manual_cooldown(self, seconds: int) -> int:
        try:
            if self._redis.set(MANUAL_COOLDOWN_KEY, "1", ex=seconds, nx=True):
                return 0
            return max(1, int(self._redis.ttl(MANUAL_COOLDOWN_KEY)))
        except (RedisError, OSError) as exc:
            raise self._unavailable("claim_manual_cooldown", exc) from exc

    def release_manual_cooldown(self) -> None:
        try:
            self._redis.delete(MANUAL_COOLDOWN_KEY)
        except (RedisError, OSError) as exc:
            logger.warning("weather_fetch_cooldown_release_failed", error=loggable_error(exc))

    def manual_cooldown_remaining(self) -> int:
        try:
            remaining = int(self._redis.ttl(MANUAL_COOLDOWN_KEY))
        except (RedisError, OSError) as exc:
            raise self._unavailable("manual_cooldown_remaining", exc) from exc
        # -2: no key, -1: key without expiry (never written by this gate).
        return max(0, remaining)
