"""Two-tier store for the device-pairing redemption lockout (#1118).

See :mod:`app.domain.interfaces.device_pairing_throttle` for why the lockout
exists next to the route's rate limit.

Two implementations, deliberately — the shape of
:mod:`app.data_access.external.unknown_account_store`:

* :class:`MemoryDevicePairingThrottleStore` — a bounded, TTL'd map inside the
  worker process, and the default, so the guard can never be silently *inert*.
* :class:`RedisDevicePairingThrottleStore` — the shared tier used in production,
  so the counter survives across replicas. On a Redis error it degrades to the
  in-process map rather than fail-open: failing open on this store does not skip
  a nicety, it reopens unbounded guessing against an endpoint that mints
  sessions, and an attacker able to provoke the outage would be the one who
  benefits.

Both tiers are bounded. The Redis tier bounds by TTL, the memory tier by TTL
*and* by entry count, evicting oldest-first — an unauthenticated caller decides
which addresses become keys, so an unbounded map would trade a guessing bound
for a memory-growth vector.

Addresses are never stored in the clear (NFR-011): the key is a sha256 digest of
the normalised address.

Deliberately **not** reusing ``unknown_account_store``: its keys mean "this
address owns no account" and its subject is an email. Writing a second meaning
into that namespace would let a login sweep and a pairing sweep overwrite each
other's state — one guard going quietly inert because the other was exercised.
"""

import hashlib
import json
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.domain.interfaces.device_pairing_throttle import IDevicePairingThrottleStore

logger = structlog.get_logger()

_PREFIX = "kp:auth:pairing:throttle:"

#: Lifetime of one address' counter.
#:
#: 24 h, matching ``unknown_account_store.DEFAULT_TTL_SECONDS``, and comfortably
#: above the 4 h maximum lockout
#: (``login_throttle_engine.MAX_LOCKOUT_MINUTES``) so an active lockout is never
#: cut short by the counter expiring under it. Residual: an attacker who spreads
#: guesses more than 24 h apart never reaches the threshold — at that cadence a
#: 256-bit code with a 90 s life is not being guessed anyway.
DEFAULT_TTL_SECONDS = 86_400

#: Entry cap of the in-process tier. Bounds worst-case memory to a few hundred
#: kB. Reached only when Redis is absent or unreachable *and* a sweep is
#: running; how fast entries can be created is bounded by the per-IP limit on
#: the redemption route (``settings.rate_limit_auth`` today, a dedicated
#: ``rate_limit_device_pairing_redeem`` from P4 on).
_FALLBACK_CAPACITY = 4096


class _StringRedis(Protocol):
    """The three Redis calls this store makes, typed so a fake can stand in.

    ``redis-py`` is constructed with ``decode_responses=True`` throughout this
    codebase, hence ``str`` rather than ``bytes``.
    """

    def get(self, name: str) -> str | None: ...

    def set(self, name: str, value: str, ex: int | None = ...) -> object: ...

    def delete(self, *names: str) -> object: ...


def _digest(ip_address: str) -> str:
    """Return the full sha256 of the normalised address, used as the store key.

    Normalisation strips surrounding whitespace and lowercases, so the two
    spellings of an IPv6 address (``2001:DB8::1`` / ``2001:db8::1``) share one
    counter instead of handing an attacker two budgets for one host.

    Full length, not truncated: a collision would make two unrelated addresses
    share a lockout, locking out a bystander.
    """
    return hashlib.sha256(ip_address.strip().lower().encode("utf-8")).hexdigest()


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


class MemoryDevicePairingThrottleStore(IDevicePairingThrottleStore):
    """Bounded, TTL'd in-process counter map.

    Correct on a single-replica deployment (the common self-hosted shape, see
    REQ-027) and the degradation target of
    :class:`RedisDevicePairingThrottleStore`. With several replicas behind a
    load balancer it counts per replica, which weakens the bound by the replica
    count but does not remove it.
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

    def get_failure_state(self, ip_address: str) -> tuple[int, datetime | None]:
        key = _digest(ip_address)
        entry = self._entries.get(key)
        if entry is None:
            return 0, None
        failed_attempts, locked_until, expires_at = entry
        if expires_at <= datetime.now(UTC):
            self._entries.pop(key, None)
            return 0, None
        return failed_attempts, locked_until

    def record_failure(
        self,
        ip_address: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        key = _digest(ip_address)
        self._entries.pop(key, None)
        self._entries[key] = (
            failed_attempts,
            locked_until,
            datetime.now(UTC) + timedelta(seconds=self._ttl_seconds),
        )
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)

    def clear(self, ip_address: str) -> None:
        self._entries.pop(_digest(ip_address), None)


#: Process-wide default.
#:
#: The dependency factories build a fresh store per request, so a counter map
#: created in ``__init__`` would start empty on every call and never reach the
#: threshold — a guard that looks implemented and counts nothing (the failure
#: class ``DEFAULT_UNKNOWN_ACCOUNT_STORE`` exists for). The module-level
#: instance is what makes the local tier real.
DEFAULT_DEVICE_PAIRING_THROTTLE_STORE = MemoryDevicePairingThrottleStore()


class RedisDevicePairingThrottleStore(IDevicePairingThrottleStore):
    """Redis-backed counter, shared across replicas, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _StringRedis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        fallback: IDevicePairingThrottleStore | None = None,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        # Defaults to the process-wide instance for the same reason it exists:
        # this store is also rebuilt per request.
        self._fallback = fallback if fallback is not None else DEFAULT_DEVICE_PAIRING_THROTTLE_STORE

    def get_failure_state(self, ip_address: str) -> tuple[int, datetime | None]:
        try:
            raw = self._redis.get(f"{_PREFIX}{_digest(ip_address)}")
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            logger.warning(
                "device_pairing_throttle_store_unavailable",
                operation="get",
                error=str(exc),
            )
            return self._fallback.get_failure_state(ip_address)
        if raw is None:
            return 0, None
        try:
            return _decode(raw)
        except (ValueError, TypeError) as exc:
            # A malformed value must not be read as an active lockout on an
            # address that never earned one; treat it as "no record".
            logger.warning("device_pairing_throttle_corrupt_entry", error=str(exc))
            return 0, None

    def record_failure(
        self,
        ip_address: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        try:
            self._redis.set(
                f"{_PREFIX}{_digest(ip_address)}",
                _encode(failed_attempts, locked_until),
                ex=self._ttl_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - see get_failure_state
            logger.warning(
                "device_pairing_throttle_store_unavailable",
                operation="set",
                error=str(exc),
            )
            self._fallback.record_failure(ip_address, failed_attempts, locked_until)

    def clear(self, ip_address: str) -> None:
        """Drop the counter in **both** tiers.

        Asymmetric to the read path on purpose. ``get_failure_state`` consults
        the fallback only while Redis is unreachable, so failures recorded
        locally during an outage would otherwise sit there until their TTL — and
        the next outage would resurrect a lockout the user had already cleared.
        Clearing is the permissive direction: over-clearing costs an attacker
        nothing they did not already have (they must present a *valid* code to
        get here), while under-clearing locks out a legitimate device.
        """
        try:
            self._redis.delete(f"{_PREFIX}{_digest(ip_address)}")
        except Exception as exc:  # noqa: BLE001 - see get_failure_state
            logger.warning(
                "device_pairing_throttle_store_unavailable",
                operation="delete",
                error=str(exc),
            )
        self._fallback.clear(ip_address)
