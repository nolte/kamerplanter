"""Two-tier store for the login lockout of addresses that own no account.

See :mod:`app.domain.interfaces.unknown_account_store` for why this exists.

Two implementations, deliberately:

* :class:`MemoryUnknownAccountStore` — a bounded, TTL'd map inside the worker
  process. It is the default so the guard can never be silently *inert*: an
  ``AuthService`` built without an explicit store still counts.
* :class:`RedisUnknownAccountStore` — the shared tier used in production, so the
  counter survives across replicas. On a Redis error it degrades to the
  in-process map rather than fail-open, because failing open here does not skip
  a rate limit, it **reopens the disclosure** this module exists to close.

Both tiers are bounded. The Redis tier bounds by TTL, the memory tier by TTL
*and* by entry count, evicting oldest-first. Eviction and expiry are the two
residual windows in which the oracle reappears for a specific address; see
``_FALLBACK_CAPACITY`` and ``DEFAULT_TTL_SECONDS``.

Addresses are never stored in the clear. The key is a sha256 digest of the
normalised address, following the pseudonymisation convention already used for
audit records (``ai_audit_logger.hash_question``,
``ErasureEngine.compute_tombstone_hash``) — an unauthenticated caller can put an
arbitrary third party's address here, and that party never consented to it being
written down (NFR-011).
"""

import hashlib
import json
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.domain.interfaces.unknown_account_store import IUnknownAccountStore

logger = structlog.get_logger()

_PREFIX = "kp:auth:unknown:"

#: Lifetime of one address' counter.
#:
#: The counter on a real ``User`` never expires by itself — only a successful
#: login clears it. A phantom counter cannot be unbounded, so it is capped at
#: 24 h, comfortably above the 4 h maximum lockout
#: (``login_throttle_engine.MAX_LOCKOUT_MINUTES``). Residual: an attacker who
#: spreads probes more than 24 h apart never reaches the 5th attempt and so
#: never observes either answer — which tells them nothing either way.
DEFAULT_TTL_SECONDS = 86_400

#: Entry cap of the in-process tier. Bounds worst-case memory to a few hundred
#: kB. Reached only when Redis is absent or unreachable *and* a sweep is running;
#: the per-IP rate limit on ``/auth/login`` (``settings.rate_limit_auth``) is what
#: bounds how fast entries can be created.
_FALLBACK_CAPACITY = 4096


class _StringRedis(Protocol):
    """The two Redis calls this store makes, typed so a fake can stand in.

    ``redis-py`` is constructed with ``decode_responses=True`` throughout this
    codebase, hence ``str`` rather than ``bytes``.
    """

    def get(self, name: str) -> str | None: ...

    def set(self, name: str, value: str, ex: int | None = ...) -> object: ...


def _digest(email: str) -> str:
    """Return the full sha256 of the normalised address, used as the store key.

    Full length, not truncated: this value must not collide, or two unrelated
    addresses would share a lockout counter.
    """
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _encode(failed_attempts: int, locked_until: datetime | None) -> str:
    return json.dumps(
        {
            "failed_attempts": failed_attempts,
            "locked_until": locked_until.isoformat() if locked_until is not None else None,
        }
    )


def _decode(raw: str) -> tuple[int, datetime | None]:
    payload = json.loads(raw)
    locked_raw = payload.get("locked_until")
    locked_until = datetime.fromisoformat(locked_raw) if locked_raw else None
    return int(payload.get("failed_attempts", 0)), locked_until


class MemoryUnknownAccountStore(IUnknownAccountStore):
    """Bounded, TTL'd in-process counter map.

    Correct on a single-replica deployment (the common self-hosted shape, see
    REQ-027) and the degradation target of :class:`RedisUnknownAccountStore`.
    With several replicas behind a load balancer it counts per replica, which
    weakens the guarantee but does not remove it — an attacker still has to land
    five probes on the *same* replica to see the difference they were looking
    for, and that is the same fraction of probes for an existing address.
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        capacity: int = _FALLBACK_CAPACITY,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._capacity = capacity
        # digest -> (failed_attempts, locked_until, expires_at); insertion-ordered
        # so eviction can drop the oldest entry in O(1).
        self._entries: OrderedDict[str, tuple[int, datetime | None, datetime]] = OrderedDict()

    def get_failure_state(self, email: str) -> tuple[int, datetime | None]:
        entry = self._entries.get(_digest(email))
        if entry is None:
            return 0, None
        failed_attempts, locked_until, expires_at = entry
        if expires_at <= datetime.now(UTC):
            self._entries.pop(_digest(email), None)
            return 0, None
        return failed_attempts, locked_until

    def record_failure(
        self,
        email: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        key = _digest(email)
        self._entries.pop(key, None)
        self._entries[key] = (
            failed_attempts,
            locked_until,
            datetime.now(UTC) + timedelta(seconds=self._ttl_seconds),
        )
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)


#: Process-wide default.
#:
#: ``get_auth_service()`` builds a fresh ``AuthService`` per request, so a store
#: instantiated in ``AuthService.__init__`` would start empty on every call and
#: the counter would never reach 5 — a guard that looks implemented and counts
#: nothing. The module-level instance is what makes the default tier real.
DEFAULT_UNKNOWN_ACCOUNT_STORE = MemoryUnknownAccountStore()


class RedisUnknownAccountStore(IUnknownAccountStore):
    """Redis-backed counter, shared across replicas, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _StringRedis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        fallback: IUnknownAccountStore | None = None,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        # Defaults to the process-wide instance for the same reason it exists:
        # this store is also rebuilt per request.
        self._fallback = fallback if fallback is not None else DEFAULT_UNKNOWN_ACCOUNT_STORE

    def get_failure_state(self, email: str) -> tuple[int, datetime | None]:
        try:
            raw = self._redis.get(f"{_PREFIX}{_digest(email)}")
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            logger.warning("unknown_account_store_unavailable", operation="get", error=str(exc))
            return self._fallback.get_failure_state(email)
        if raw is None:
            return 0, None
        try:
            return _decode(raw)
        except (ValueError, TypeError) as exc:
            # A malformed value must not hand the caller a 401 that a real
            # account would have answered with 423; treat it as "no record".
            logger.warning("unknown_account_store_corrupt_entry", error=str(exc))
            return 0, None

    def record_failure(
        self,
        email: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        try:
            self._redis.set(
                f"{_PREFIX}{_digest(email)}",
                _encode(failed_attempts, locked_until),
                ex=self._ttl_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - see get_failure_state
            logger.warning("unknown_account_store_unavailable", operation="set", error=str(exc))
            self._fallback.record_failure(email, failed_attempts, locked_until)
