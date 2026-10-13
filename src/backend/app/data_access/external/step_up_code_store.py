"""Two-tier store for the e-mailed one-time step-up code (#1815).

See :mod:`app.domain.interfaces.step_up_code` for what the code is for. The shape
of the step-up throttle store next to it (``step_up_throttle``):

* :class:`MemoryStepUpCodeStore` — a bounded, TTL'd map inside the worker process,
  and the degradation target.
* :class:`RedisStepUpCodeStore` — the shared tier (Valkey in production), so a code
  issued by one replica is redeemable on another. On a Redis error it degrades to
  the in-process map. Failing *closed* instead (refusing to issue) would lock every
  federated account out of its own erasure, password setup and e-mail change for
  the length of the outage; failing *open* is not an option at all. A code that
  landed locally during an outage is still found after the shared tier is back.

Its own key namespaces (``kp:auth:stepup:code:`` for the code,
``kp:auth:stepup:codecooldown:`` and ``kp:auth:stepup:codeissues:`` for the issuance
bounds of review SEC-002), apart from the throttle's ``count``/``strikes``/``lock``
keys: one store's writes must never land on the other's.

**Single use in the shared tier** is ``GET`` + constant-time compare + ``DEL``,
and only a ``DEL`` that answered ``1`` counts: two requests presenting the same
code both read it, but only one of them removes it.
"""

import hashlib
import hmac
import threading
from collections import OrderedDict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import structlog

from app.domain.interfaces.step_up_code import IStepUpCodeStore

logger = structlog.get_logger()

_NAMESPACE_ROOT = "kp:auth:stepup:"

#: Entry cap of the in-process tier. Subjects are authenticated accounts, so the
#: map cannot be flooded anonymously; the cap bounds memory during an outage.
_FALLBACK_CAPACITY = 4096


class _StringRedis(Protocol):
    """The Redis calls this store makes, typed so a fake can stand in."""

    def set(self, name: str, value: str, ex: int | None = ..., nx: bool = ...) -> object: ...

    def get(self, name: str) -> str | None: ...

    def ttl(self, name: str) -> int: ...

    def pipeline(self, transaction: bool = ...) -> Any: ...

    def delete(self, *names: str) -> int: ...

    def decr(self, name: str, amount: int = ...) -> int: ...


def _subject_digest(subject: str) -> str:
    """Full sha256 of the normalised subject (NFR-011: the account key never reaches the store)."""
    return hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()


def _matches(stored: str | bytes | None, presented: str) -> bool:
    if stored is None:
        return False
    value = stored.decode() if isinstance(stored, bytes) else stored
    return hmac.compare_digest(value.encode(), presented.encode())


class MemoryStepUpCodeStore(IStepUpCodeStore):
    """Bounded, TTL'd in-process codes, safe under concurrent request threads."""

    def __init__(
        self,
        capacity: int = _FALLBACK_CAPACITY,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._capacity = capacity
        self._clock = clock or (lambda: datetime.now(UTC))
        self._mutex = threading.Lock()
        self._entries: OrderedDict[str, tuple[str, datetime]] = OrderedDict()
        #: Replacement wait: subject digest -> until when a new code is refused.
        self._cooldowns: dict[str, datetime] = {}
        #: Issuance budget: subject digest -> (issues in the window, window end).
        self._issues: OrderedDict[str, tuple[int, datetime]] = OrderedDict()

    def reserve_issue(self, subject: str, *, cooldown_seconds: int, max_issues: int, window_seconds: int) -> int:
        key = _subject_digest(subject)
        now = self._clock()
        with self._mutex:
            cooldown_until = self._cooldowns.get(key)
            if cooldown_until is not None and cooldown_until > now and key in self._entries:
                return max(1, int((cooldown_until - now).total_seconds()))
            count, window_end = self._issues.pop(key, (0, now + timedelta(seconds=window_seconds)))
            if window_end <= now:
                count, window_end = 0, now + timedelta(seconds=window_seconds)
            count += 1
            self._issues[key] = (count, window_end)
            while len(self._issues) > self._capacity:
                self._issues.popitem(last=False)
            if count > max_issues:
                return max(1, int((window_end - now).total_seconds()))
            if cooldown_seconds > 0:
                self._cooldowns[key] = now + timedelta(seconds=cooldown_seconds)
                if len(self._cooldowns) > self._capacity:
                    self._cooldowns = {k: v for k, v in self._cooldowns.items() if v > now}
            return 0

    def issue(self, subject: str, code_digest: str, ttl_seconds: int) -> None:
        key = _subject_digest(subject)
        expires_at = self._clock() + timedelta(seconds=ttl_seconds)
        with self._mutex:
            self._entries.pop(key, None)
            self._entries[key] = (code_digest, expires_at)
            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)

    def consume(self, subject: str, code_digest: str) -> bool:
        key = _subject_digest(subject)
        now = self._clock()
        with self._mutex:
            entry = self._entries.get(key)
            if entry is None:
                return False
            stored, expires_at = entry
            if expires_at <= now:
                del self._entries[key]
                return False
            if not _matches(stored, code_digest):
                return False
            del self._entries[key]
            self._cooldowns.pop(key, None)
            return True

    def release_issue(self, subject: str) -> None:
        key = _subject_digest(subject)
        with self._mutex:
            self._entries.pop(key, None)
            self._cooldowns.pop(key, None)
            if key in self._issues:
                count, window_end = self._issues[key]
                self._issues[key] = (max(0, count - 1), window_end)

    def discard(self, subject: str) -> None:
        """Drop the subject's code, if any (a newer one was issued in the shared tier)."""
        with self._mutex:
            self._entries.pop(_subject_digest(subject), None)


#: Process-wide default. Services are built per request; a store created there would
#: forget the code between the request that issued it and the one that presents it.
DEFAULT_STEP_UP_CODE_STORE = MemoryStepUpCodeStore()

#: The process-wide tier of the one-time re-authentication tokens (#1815), apart
#: from the codes: one subject holds a pending code and a pending token independently.
DEFAULT_STEP_UP_REAUTH_STORE = MemoryStepUpCodeStore()


class RedisStepUpCodeStore(IStepUpCodeStore):
    """Valkey/Redis-backed codes shared across replicas, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _StringRedis,
        fallback: MemoryStepUpCodeStore | None = None,
        *,
        namespace: str = "code",
    ) -> None:
        """``namespace`` separates the key families of the stores built on this class.

        ``code`` (default) holds the e-mailed step-up codes; ``reauth`` the one-time
        tokens a fresh OIDC re-authentication issues (#1815). The keys are
        ``kp:auth:stepup:<ns>:``, ``…:<ns>cooldown:`` and ``…:<ns>issues:``.
        """
        self._redis = redis_client
        self._fallback = fallback if fallback is not None else DEFAULT_STEP_UP_CODE_STORE
        self._code_prefix = f"{_NAMESPACE_ROOT}{namespace}:"
        self._cooldown_prefix = f"{_NAMESPACE_ROOT}{namespace}cooldown:"
        self._issues_prefix = f"{_NAMESPACE_ROOT}{namespace}issues:"

    def _unavailable(self, operation: str, exc: Exception) -> None:
        logger.warning("step_up_code_store_unavailable", operation=operation, error_type=type(exc).__name__)

    def reserve_issue(self, subject: str, *, cooldown_seconds: int, max_issues: int, window_seconds: int) -> int:
        """Replacement wait, then a fixed-window budget reserved in one ``MULTI``/``EXEC``.

        The window key is created with ``NX`` and its expiry in the same
        transaction as the ``INCR``, so a counter never exists without an expiry.
        """
        digest = _subject_digest(subject)
        cooldown_key, issues_key = f"{self._cooldown_prefix}{digest}", f"{self._issues_prefix}{digest}"
        try:
            # Claim the wait with SET NX — check and set in one step, so two racing
            # requests cannot both read "no wait" and both issue (/code-review of #1862).
            claimed = cooldown_seconds <= 0 or bool(self._redis.set(cooldown_key, "1", ex=cooldown_seconds, nx=True))
            if not claimed:
                return max(1, int(self._redis.ttl(cooldown_key)))
            _, count, window_left = (
                self._redis.pipeline(transaction=True)
                .set(issues_key, "0", ex=window_seconds, nx=True)
                .incr(issues_key)
                .ttl(issues_key)
                .execute()
            )
            if int(count) > max_issues:
                # No code is sent, so the claimed wait must not hold the next request.
                if cooldown_seconds > 0:
                    self._redis.delete(cooldown_key)
                return max(1, int(window_left))
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            self._unavailable("reserve_issue", exc)
            return self._fallback.reserve_issue(
                subject, cooldown_seconds=cooldown_seconds, max_issues=max_issues, window_seconds=window_seconds
            )
        return 0

    def release_issue(self, subject: str) -> None:
        digest = _subject_digest(subject)
        issues_key = f"{self._issues_prefix}{digest}"
        try:
            self._redis.delete(f"{self._code_prefix}{digest}", f"{self._cooldown_prefix}{digest}")
            if int(self._redis.get(issues_key) or 0) > 0 and int(self._redis.decr(issues_key)) < 0:
                # A concurrent release got there first; never leave a negative budget.
                self._redis.set(issues_key, "0", ex=max(1, int(self._redis.ttl(issues_key))))
        except Exception as exc:  # noqa: BLE001 - see issue
            self._unavailable("release_issue", exc)
        self._fallback.release_issue(subject)

    def issue(self, subject: str, code_digest: str, ttl_seconds: int) -> None:
        try:
            self._redis.set(f"{self._code_prefix}{_subject_digest(subject)}", code_digest, ex=max(1, ttl_seconds))
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            self._unavailable("set", exc)
            self._fallback.issue(subject, code_digest, ttl_seconds)
            return
        # Issuing replaces *any* previous code, also one an outage parked locally.
        self._fallback.discard(subject)

    def consume(self, subject: str, code_digest: str) -> bool:
        key = f"{self._code_prefix}{_subject_digest(subject)}"
        try:
            stored = self._redis.get(key)
            if _matches(stored, code_digest):
                # Only the request whose DEL removed the entry wins; a concurrent
                # one that read the same value finds it gone (answer 0). A spent
                # code ends the replacement wait with it.
                won = int(self._redis.delete(key)) == 1
                if won:
                    self._redis.delete(f"{self._cooldown_prefix}{_subject_digest(subject)}")
                return won
        except Exception as exc:  # noqa: BLE001 - see issue
            self._unavailable("consume", exc)
        # Not in the shared tier (or it is down): a code issued during an outage
        # sits in the local one.
        return self._fallback.consume(subject, code_digest)
