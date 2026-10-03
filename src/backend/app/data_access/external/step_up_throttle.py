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

#: Entry cap of the in-process tier; it bounds memory while Valkey is down. The
#: step-up's subjects derive from authenticated accounts and cannot be flooded
#: anonymously, so its full map evicts the least recently written entry (LRU).
#: The password-proven resend budget (``DEFAULT_VERIFICATION_RESEND_PROVEN_STORE``,
#: #2046) has the same cap and the same eviction: its subjects are account keys
#: reached only with the account's correct password, so filling it takes that
#: many proven accounts. The two anonymous budgets use
#: :func:`anonymous_budget_fallback` instead (#2058).
_FALLBACK_CAPACITY = 4096

#: Entry cap of the in-process tier of the two **anonymous** mail budgets — the
#: verification resend (#2037) and the password reset (#2043), whose subjects are
#: caller-chosen addresses (#2058). Four times the step-up's: an entry is a
#: 64-character digest plus a small record, a few hundred bytes, so a full map
#: is a few megabytes per store and process.
ANONYMOUS_BUDGET_FALLBACK_CAPACITY = 16_384

#: What :meth:`MemoryStepUpThrottleStore.reserve_attempt` answers for a new
#: subject it cannot admit into a full non-evicting map: above every budget, so
#: the caller treats it as spent and stays silent (#2058).
FULL_MAP_COUNT = 2**31 - 1


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
        *,
        refuse_new_subjects_when_full: bool = False,
    ) -> None:
        """Build the map.

        Args:
            ttl_seconds: Window of a subject's counters, renewed on every write.
            capacity: Most entries the map holds.
            clock: Source of "now"; the wall clock unless a test supplies one.
            refuse_new_subjects_when_full: ``False`` (the step-up): a full map
                evicts its least recently written entry. ``True`` (the anonymous
                mail budgets, #2058): a full map first drops entries whose
                window has passed, and if it is still full,
                :meth:`reserve_attempt` answers :data:`FULL_MAP_COUNT` for a
                **new** subject without storing it — no live entry, and with it
                no spent budget, is ever evicted by a flood of new subjects.
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._capacity = capacity
        self._clock = clock or (lambda: datetime.now(UTC))
        self._mutex = threading.Lock()
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._refuse_when_full = refuse_new_subjects_when_full
        self._full_reported = False

    @property
    def capacity(self) -> int:
        """Most entries the map holds."""
        return self._capacity

    @property
    def refuses_new_subjects_when_full(self) -> bool:
        """Whether a full map refuses new subjects instead of evicting (#2058)."""
        return self._refuse_when_full

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

    def _has_room_for(self, key: str, now: datetime) -> bool:
        """Whether *key* may be stored without evicting a live entry; the caller holds ``_mutex``.

        Entries are kept in order of their last write and every write renews the
        window, so the expired ones sit at the old end: dropping from there until
        the first live entry purges all of them.
        """
        if key in self._entries or len(self._entries) < self._capacity:
            return True
        while self._entries:
            oldest = next(iter(self._entries.values()))
            if oldest.expires_at is None or oldest.expires_at > now:
                break
            if oldest.locked_until is not None and oldest.locked_until > now:
                break
            self._entries.popitem(last=False)
        return len(self._entries) < self._capacity

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
        key = _digest(subject)
        with self._mutex:
            if self._refuse_when_full and not self._has_room_for(key, now):
                report, self._full_reported = not self._full_reported, True
            else:
                if self._refuse_when_full:
                    self._full_reported = False
                entry = self._entry(key, now)
                entry.count += 1
                entry.expires_at = now + self._ttl
                return entry.count
        if report:
            # Once per episode of a full map, never per refused subject: a flood
            # must not turn into a log flood. No subject, no address.
            logger.warning("anonymous_budget_fallback_full", capacity=self._capacity)
        return FULL_MAP_COUNT

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


#: Window of the per-address budget of ``POST /auth/resend-verification`` (#2037).
#:
#: That budget is a second, separate user of this mechanism: an atomic counter
#: per subject whose window is renewed by every request. It needs nothing else
#: the step-up does (no strikes, no locks), and its subjects —
#: ``verification-resend:<address>`` — can never digest to a step-up subject (an
#: account key, or a key plus a client address), so the two never touch each
#: other's counters. One hour: the budget refills once an address has been left
#: alone that long.
VERIFICATION_RESEND_WINDOW_SECONDS = 3_600


def anonymous_budget_fallback(
    ttl_seconds: int,
    *,
    capacity: int = ANONYMOUS_BUDGET_FALLBACK_CAPACITY,
    clock: Callable[[], datetime] | None = None,
) -> MemoryStepUpThrottleStore:
    """The in-process tier of an anonymous per-address mail budget (#2058).

    Non-evicting: a caller who submits more distinct addresses than the map
    holds while Valkey is down must not evict a victim's spent budget and buy
    it a fresh one (measured before #2058: 4096 invented addresses → a 4th
    mail to the victim). A full map drops expired entries first; a new address
    that still finds no room is answered as over its budget — silently, no mail
    — until entries expire. ``capacity`` and ``clock`` are for tests.
    """
    return MemoryStepUpThrottleStore(
        ttl_seconds=ttl_seconds, capacity=capacity, clock=clock, refuse_new_subjects_when_full=True
    )


#: Process-wide in-process tier of the resend budget, and the degradation target
#: of its Redis tier — its own instance, so the step-up's 24-hour window and this
#: one-hour window are never applied to each other's subjects. Module-level for
#: the same reason as :data:`DEFAULT_STEP_UP_THROTTLE_STORE`; non-evicting
#: (:func:`anonymous_budget_fallback`).
DEFAULT_VERIFICATION_RESEND_STORE = anonymous_budget_fallback(VERIFICATION_RESEND_WINDOW_SECONDS)

#: Process-wide in-process tier of the password-proven resend budget (#2046) —
#: the fresh link the login refusal ``EMAIL_NOT_VERIFIED`` mails once the
#: password was correct — and the degradation target of its Redis tier. Same
#: one-hour window as the anonymous resend budget, but its own instance and its
#: own subjects (``verification-resend-proven:<user_key>``): an anonymous caller
#: who spends the per-address budget never reaches this one, so the owner cannot
#: be locked out of a new link by someone who only knows the address.
DEFAULT_VERIFICATION_RESEND_PROVEN_STORE = MemoryStepUpThrottleStore(ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS)


#: Window of the per-address budget of ``POST /auth/password-reset/request``
#: (#2043) — the third user of this mechanism, shaped exactly like the resend
#: budget above: an atomic counter per subject, window renewed by every request,
#: no strikes, no locks. Its subjects — ``password-reset:<address>`` — digest to
#: neither a step-up subject nor a ``verification-resend:`` one, so the budgets
#: never spend each other. One hour, like the resend budget: the reset link
#: itself lives one hour, so a fourth link inside it would only replace a link
#: that is still valid.
PASSWORD_RESET_WINDOW_SECONDS = 3_600

#: Process-wide in-process tier of the reset budget, and the degradation target
#: of its Redis tier. Its own instance, for the reason
#: :data:`DEFAULT_VERIFICATION_RESEND_STORE` is one; non-evicting
#: (:func:`anonymous_budget_fallback`).
DEFAULT_PASSWORD_RESET_STORE = anonymous_budget_fallback(PASSWORD_RESET_WINDOW_SECONDS)


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
