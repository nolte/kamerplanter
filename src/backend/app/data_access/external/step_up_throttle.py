"""Two-tier store for the password step-up throttle (#1816).

See :mod:`app.domain.interfaces.step_up_throttle` for why the step-up has its own
counters and why they reserve an attempt before the password is tested.

The shape of the other lockout stores (``device_pairing_throttle``,
``unknown_account_store``):

* :class:`MemoryStepUpThrottleStore` — a bounded, TTL'd map inside the worker
  process, and the degradation target, so the guard is never silently inert.
* :class:`RedisStepUpThrottleStore` — the shared tier (Valkey in production), so
  replicas share one counter. On a Redis error it degrades to the in-process map
  rather than fail open: failing open would reopen the unthrottled password
  oracle this store exists to close.

Its own key namespace (``kp:auth:stepup:``): sharing the pairing or unknown-account
keys would let one guard's traffic overwrite the other's state.

Subjects are never stored in the clear — the key is a sha256 digest (NFR-011); a
subject carries an account key and a client address.
"""

import hashlib
import threading
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.domain.interfaces.step_up_throttle import IStepUpThrottleStore

logger = structlog.get_logger()

_COUNT_PREFIX = "kp:auth:stepup:count:"
_LOCK_PREFIX = "kp:auth:stepup:lock:"

#: Window of one subject's attempt counter, renewed on every attempt. 24 h, above
#: the 4 h maximum lockout (``login_throttle_engine.MAX_LOCKOUT_MINUTES``), so the
#: backoff keeps growing across consecutive lockouts instead of restarting.
DEFAULT_TTL_SECONDS = 86_400

#: Entry cap of the in-process tier. Subjects are derived from authenticated
#: accounts, so the map cannot be flooded anonymously; the cap bounds memory when
#: Redis is down during a sweep across many sessions.
_FALLBACK_CAPACITY = 4096


class _StringRedis(Protocol):
    """The Redis calls this store makes, typed so a fake can stand in."""

    def incr(self, name: str) -> int: ...

    def expire(self, name: str, time: int) -> object: ...

    def set(self, name: str, value: str, ex: int | None = ...) -> object: ...

    def ttl(self, name: str) -> int: ...

    def delete(self, *names: str) -> object: ...


def _digest(subject: str) -> str:
    """Full sha256 of the normalised subject; full length so two subjects never share a lock."""
    return hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()


class MemoryStepUpThrottleStore(IStepUpThrottleStore):
    """Bounded, TTL'd in-process counters, safe under concurrent request threads.

    Correct on a single replica (the common self-hosted shape); with several
    replicas and Redis down it counts per replica, which weakens the bound by the
    replica count but does not remove it.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS, capacity: int = _FALLBACK_CAPACITY) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._capacity = capacity
        self._mutex = threading.Lock()
        # digest -> (count, count_expires_at, locked_until)
        self._entries: OrderedDict[str, tuple[int, datetime, datetime | None]] = OrderedDict()

    def _live(self, key: str, now: datetime) -> tuple[int, datetime, datetime | None] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        count, expires_at, locked_until = entry
        if expires_at <= now and (locked_until is None or locked_until <= now):
            self._entries.pop(key, None)
            return None
        if expires_at <= now:
            return 0, expires_at, locked_until
        return entry

    def lock_remaining_seconds(self, subject: str) -> int:
        now = datetime.now(UTC)
        with self._mutex:
            entry = self._live(_digest(subject), now)
        if entry is None or entry[2] is None or entry[2] <= now:
            return 0
        return max(1, int((entry[2] - now).total_seconds()))

    def reserve_attempt(self, subject: str) -> int:
        key = _digest(subject)
        now = datetime.now(UTC)
        with self._mutex:
            entry = self._live(key, now)
            count = (entry[0] if entry else 0) + 1
            locked_until = entry[2] if entry else None
            self._entries.pop(key, None)
            self._entries[key] = (count, now + self._ttl, locked_until)
            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)
        return count

    def lock(self, subject: str, seconds: int) -> None:
        key = _digest(subject)
        now = datetime.now(UTC)
        with self._mutex:
            entry = self._live(key, now)
            count, expires_at = (entry[0], entry[1]) if entry else (0, now + self._ttl)
            self._entries[key] = (count, expires_at, now + timedelta(seconds=seconds))

    def clear(self, subject: str) -> None:
        with self._mutex:
            self._entries.pop(_digest(subject), None)


#: Process-wide default. Services are built per request; a map created there would
#: start empty on every call and never reach the threshold — a guard that looks
#: implemented and counts nothing. The module-level instance makes the local tier real.
DEFAULT_STEP_UP_THROTTLE_STORE = MemoryStepUpThrottleStore()


class RedisStepUpThrottleStore(IStepUpThrottleStore):
    """Valkey/Redis-backed counters shared across replicas, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _StringRedis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        fallback: IStepUpThrottleStore | None = None,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        self._fallback = fallback if fallback is not None else DEFAULT_STEP_UP_THROTTLE_STORE

    def _unavailable(self, operation: str, exc: Exception) -> None:
        logger.warning("step_up_throttle_store_unavailable", operation=operation, error=str(exc))

    def lock_remaining_seconds(self, subject: str) -> int:
        try:
            remaining = int(self._redis.ttl(f"{_LOCK_PREFIX}{_digest(subject)}"))
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            self._unavailable("ttl", exc)
            return self._fallback.lock_remaining_seconds(subject)
        # -2: no key, -1: a key without expiry (never written by this store) — not a lock.
        return remaining if remaining > 0 else 0

    def reserve_attempt(self, subject: str) -> int:
        key = f"{_COUNT_PREFIX}{_digest(subject)}"
        try:
            count = int(self._redis.incr(key))
            self._redis.expire(key, self._ttl_seconds)
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("incr", exc)
            return self._fallback.reserve_attempt(subject)
        return count

    def lock(self, subject: str, seconds: int) -> None:
        try:
            self._redis.set(f"{_LOCK_PREFIX}{_digest(subject)}", "1", ex=max(1, seconds))
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("set", exc)
            self._fallback.lock(subject, seconds)

    def clear(self, subject: str) -> None:
        """Drop counter and lock in **both** tiers (an outage must not resurrect a cleared lock)."""
        digest = _digest(subject)
        try:
            self._redis.delete(f"{_COUNT_PREFIX}{digest}", f"{_LOCK_PREFIX}{digest}")
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("delete", exc)
        self._fallback.clear(subject)
