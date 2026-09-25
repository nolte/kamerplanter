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
  oracle this store exists to close. A lock is read from **both** tiers, so a lock
  recorded locally during an outage still holds after the shared tier is back
  (security review SEC-008).

Its own key namespace (``kp:auth:stepup:``): sharing the pairing or unknown-account
keys would let one guard's traffic overwrite the other's state.

Subjects are never stored in the clear — the key is a sha256 digest (NFR-011); a
subject carries an account key and a client address.
"""

import hashlib
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import structlog

from app.domain.interfaces.step_up_throttle import IStepUpThrottleStore

logger = structlog.get_logger()

_COUNT_PREFIX = "kp:auth:stepup:count:"
_STRIKE_PREFIX = "kp:auth:stepup:strikes:"
_LOCK_PREFIX = "kp:auth:stepup:lock:"

#: Window of one subject's attempt and strike counters, renewed on every write.
#: 24 h, above the 4 h maximum lockout (``login_throttle_engine.MAX_LOCKOUT_MINUTES``),
#: so the backoff keeps growing across consecutive lockouts instead of restarting.
DEFAULT_TTL_SECONDS = 86_400

#: Entry cap of the in-process tier. Subjects are derived from authenticated
#: accounts, so the map cannot be flooded anonymously; the cap bounds memory when
#: Redis is down during a sweep across many sessions.
_FALLBACK_CAPACITY = 4096


class _StringRedis(Protocol):
    """The Redis calls this store makes, typed so a fake can stand in."""

    def pipeline(self, transaction: bool = ...) -> Any: ...

    def get(self, name: str) -> str | None: ...

    def ttl(self, name: str) -> int: ...

    def delete(self, *names: str) -> object: ...


def _digest(subject: str) -> str:
    """Full sha256 of the normalised subject; full length so two subjects never share a lock."""
    return hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()


@dataclass
class _Entry:
    count: int = 0
    strikes: int = 0
    expires_at: datetime | None = None
    locked_until: datetime | None = None


class MemoryStepUpThrottleStore(IStepUpThrottleStore):
    """Bounded, TTL'd in-process counters, safe under concurrent request threads.

    Correct on a single replica (the common self-hosted shape); with several
    replicas and Redis down it counts per replica, which weakens the bound by the
    replica count but does not remove it.
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        capacity: int = _FALLBACK_CAPACITY,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._capacity = capacity
        self._clock = clock or (lambda: datetime.now(UTC))
        self._mutex = threading.Lock()
        self._entries: OrderedDict[str, _Entry] = OrderedDict()

    def _entry(self, key: str, now: datetime) -> _Entry:
        """The live entry for *key*, created or aged as needed; moved to the young end."""
        entry = self._entries.pop(key, None) or _Entry()
        if entry.expires_at is not None and entry.expires_at <= now:
            entry.count, entry.strikes, entry.expires_at = 0, 0, None
        if entry.locked_until is not None and entry.locked_until <= now:
            entry.locked_until = None
        self._entries[key] = entry
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)
        return entry

    def lock_remaining_seconds(self, subject: str) -> int:
        now = self._clock()
        with self._mutex:
            entry = self._entries.get(_digest(subject))
            locked_until = entry.locked_until if entry else None
        if locked_until is None or locked_until <= now:
            return 0
        return max(1, int((locked_until - now).total_seconds()))

    def reserve_attempt(self, subject: str) -> int:
        now = self._clock()
        with self._mutex:
            entry = self._entry(_digest(subject), now)
            entry.count += 1
            entry.expires_at = now + self._ttl
            return entry.count

    def strike(self, subject: str, *, rearm_to: int, lock_seconds: Callable[[int], int]) -> int:
        now = self._clock()
        with self._mutex:
            entry = self._entry(_digest(subject), now)
            entry.strikes += 1
            entry.count = rearm_to
            entry.expires_at = now + self._ttl
            entry.locked_until = now + timedelta(seconds=max(1, lock_seconds(entry.strikes)))
            return entry.strikes

    def lock(self, subject: str, seconds: int) -> None:
        now = self._clock()
        with self._mutex:
            entry = self._entry(_digest(subject), now)
            entry.locked_until = now + timedelta(seconds=seconds)
            if entry.expires_at is None:
                entry.expires_at = now + self._ttl

    def clear(self, subject: str) -> None:
        with self._mutex:
            self._entries.pop(_digest(subject), None)


#: Process-wide default. Services are built per request; a map created there would
#: start empty on every call and never reach the threshold — a guard that looks
#: implemented and counts nothing. The module-level instance makes the local tier real.
DEFAULT_STEP_UP_THROTTLE_STORE = MemoryStepUpThrottleStore()


class RedisStepUpThrottleStore(IStepUpThrottleStore):
    """Valkey/Redis-backed counters shared across replicas, with an in-process fallback.

    Every counter write and its expiry go out in one ``MULTI``/``EXEC``
    transaction (security review SEC-005): an ``INCR`` that landed without its
    ``EXPIRE`` would leave a counter that never ages out.
    """

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
        logger.warning("step_up_throttle_store_unavailable", operation=operation, error_type=type(exc).__name__)

    def lock_remaining_seconds(self, subject: str) -> int:
        local = self._fallback.lock_remaining_seconds(subject)
        try:
            remaining = int(self._redis.ttl(f"{_LOCK_PREFIX}{_digest(subject)}"))
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            self._unavailable("ttl", exc)
            return local
        # -2: no key, -1: a key without expiry (never written by this store) — not a lock.
        return max(local, remaining if remaining > 0 else 0)

    def reserve_attempt(self, subject: str) -> int:
        key = f"{_COUNT_PREFIX}{_digest(subject)}"
        try:
            count, _ = self._redis.pipeline(transaction=True).incr(key).expire(key, self._ttl_seconds).execute()
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("incr", exc)
            return self._fallback.reserve_attempt(subject)
        return int(count)

    def strike(self, subject: str, *, rearm_to: int, lock_seconds: Callable[[int], int]) -> int:
        """Strike count, lock and re-arm in one ``MULTI``/``EXEC``.

        The next strike count is read first to size the lock. That read is not in
        the transaction, and needs not be: only the one request whose reservation
        reached the threshold strikes, so no two strikes of one subject race.
        """
        digest = _digest(subject)
        strikes_key = f"{_STRIKE_PREFIX}{digest}"
        try:
            strikes = int(self._redis.get(strikes_key) or 0) + 1
            self._redis.pipeline(transaction=True).set(
                f"{_LOCK_PREFIX}{digest}", "1", ex=max(1, lock_seconds(strikes))
            ).set(strikes_key, str(strikes), ex=self._ttl_seconds).set(
                f"{_COUNT_PREFIX}{digest}", str(rearm_to), ex=self._ttl_seconds
            ).execute()
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("strike", exc)
            return self._fallback.strike(subject, rearm_to=rearm_to, lock_seconds=lock_seconds)
        return strikes

    def lock(self, subject: str, seconds: int) -> None:
        try:
            self._redis.pipeline(transaction=True).set(
                f"{_LOCK_PREFIX}{_digest(subject)}", "1", ex=max(1, seconds)
            ).execute()
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("set", exc)
            self._fallback.lock(subject, seconds)

    def clear(self, subject: str) -> None:
        """Drop counters and lock in **both** tiers (an outage must not resurrect a cleared lock)."""
        digest = _digest(subject)
        try:
            self._redis.delete(f"{_COUNT_PREFIX}{digest}", f"{_STRIKE_PREFIX}{digest}", f"{_LOCK_PREFIX}{digest}")
        except Exception as exc:  # noqa: BLE001 - see lock_remaining_seconds
            self._unavailable("delete", exc)
        self._fallback.clear(subject)
