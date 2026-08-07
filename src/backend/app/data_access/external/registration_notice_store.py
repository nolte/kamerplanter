"""Two-tier store for the duplicate-registration notice's suppression window.

See :mod:`app.domain.interfaces.registration_notice_store` for why the window
exists at all. This module mirrors the shape of
:mod:`app.data_access.external.unknown_account_store` — digest keys, TTL, a
bounded in-process tier, degrade-to-local rather than fail-open — and
deliberately does **not** reuse that store:

* Its operations are a lockout counter (``get_failure_state`` /
  ``record_failure``, carrying ``failed_attempts`` and ``locked_until``). This
  needs one atomic *claim*: two workers may pick up two attempts for the same
  address at the same instant, and a read-decide-write pair would let both send.
* Its keys live under ``kp:auth:unknown:`` and mean "this address owns no
  account". Writing a second meaning into the same namespace would make a login
  sweep and a registration sweep overwrite each other's state — one guard going
  quietly inert because the other was exercised.

Addresses are never stored in the clear, for the same reason as in the sibling
store: an unauthenticated caller decides which addresses end up here, and their
owners never consented to being written down (NFR-011).
"""

import hashlib
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.domain.interfaces.registration_notice_store import IRegistrationNoticeStore

logger = structlog.get_logger()

_PREFIX = "kp:auth:regnotice:"

#: Length of one recipient's suppression window.
#:
#: 24 h, matching the sibling store's counter lifetime. The value trades the
#: recipient's awareness against their inbox: the second attempt inside a day
#: tells them nothing the first did not, while an unbounded notice would let an
#: anonymous caller drive their mail volume. Fixed rather than configurable —
#: an operator lowering it to seconds would restore the mail-bombing primitive
#: the window exists to remove.
DEFAULT_TTL_SECONDS = 86_400

#: Entry cap of the in-process tier, bounding worst-case memory to a few hundred
#: kB. Reached only while Redis is unreachable *and* a sweep is running; how fast
#: entries can be created is bounded by the per-IP limit on ``/auth/register``
#: (``settings.rate_limit_auth``).
_FALLBACK_CAPACITY = 4096


class _ClaimingRedis(Protocol):
    """The single Redis call this store makes, typed so a fake can stand in."""

    def set(self, name: str, value: str, ex: int | None = ..., nx: bool = ...) -> object: ...


def _digest(email: str) -> str:
    """Return the full sha256 of the normalised address, used as the store key.

    Full length, not truncated: a collision would make two unrelated addresses
    share one suppression window, and the loser would never be notified.
    """
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


class MemoryRegistrationNoticeStore(IRegistrationNoticeStore):
    """Bounded, TTL'd in-process claim map.

    Correct on a single-replica deployment (the common self-hosted shape, see
    REQ-027) and the degradation target of
    :class:`RedisRegistrationNoticeStore`. Across several worker processes it
    windows per process, which weakens the bound by the replica count but does
    not remove it.
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        capacity: int = _FALLBACK_CAPACITY,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._capacity = capacity
        # digest -> expires_at; insertion-ordered so eviction drops oldest first.
        self._claims: OrderedDict[str, datetime] = OrderedDict()

    def claim(self, email: str) -> bool:
        key = _digest(email)
        now = datetime.now(UTC)
        expires_at = self._claims.get(key)
        if expires_at is not None and expires_at > now:
            return False
        self._claims.pop(key, None)
        self._claims[key] = now + timedelta(seconds=self._ttl_seconds)
        while len(self._claims) > self._capacity:
            self._claims.popitem(last=False)
        return True


#: Process-wide default.
#:
#: The task builds its store per call, so a per-call instance would start empty
#: every time and claim would always succeed — a window that looks implemented
#: and suppresses nothing. The module-level instance is what makes the local
#: tier real.
DEFAULT_REGISTRATION_NOTICE_STORE = MemoryRegistrationNoticeStore()


class RedisRegistrationNoticeStore(IRegistrationNoticeStore):
    """Redis-backed claim shared across workers, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _ClaimingRedis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        fallback: IRegistrationNoticeStore | None = None,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        self._fallback = fallback if fallback is not None else DEFAULT_REGISTRATION_NOTICE_STORE

    def claim(self, email: str) -> bool:
        """Claim via ``SET key value NX EX ttl`` — one round trip, no race.

        On a Redis error the decision degrades to the in-process tier rather
        than defaulting to "yes": defaulting to yes during an outage would hand
        an attacker the unbounded send the window exists to prevent, and the
        outage itself is trivial to provoke from outside.
        """
        try:
            claimed = self._redis.set(
                f"{_PREFIX}{_digest(email)}",
                datetime.now(UTC).isoformat(),
                ex=self._ttl_seconds,
                nx=True,
            )
        except Exception as exc:  # noqa: BLE001 - any Redis failure degrades to the local tier
            logger.warning("registration_notice_store_unavailable", error=str(exc))
            return self._fallback.claim(email)
        return bool(claimed)
