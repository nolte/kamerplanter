"""Two-tier store for the thumbnail-dispatch claim (#2108).

See :mod:`app.domain.interfaces.rendition_dispatch_claims` for why the claim
exists. Same shape as :mod:`app.data_access.external.registration_notice_store`:
``SET key NX EX ttl`` in Valkey, degrading to a bounded in-process tier when
Valkey fails — never to "always dispatch", which would hand back the per-GET
amplification during exactly the outage a caller can provoke.
"""

import threading
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog
from redis.exceptions import RedisError

from app.common.log_privacy import loggable_error
from app.domain.interfaces.rendition_dispatch_claims import IRenditionDispatchClaims

logger = structlog.get_logger()

_PREFIX = "kp:thumb:dispatch:"

#: Length of one dispatch window. The task retries up to three times, 60 s
#: apart (``generate_thumbnails``), so a first run plus its retries finishes
#: inside five minutes; a GET after that may queue a fresh attempt.
DISPATCH_WINDOW_SECONDS = 300

#: Entry cap of the in-process tier — a few hundred kB at worst.
_FALLBACK_CAPACITY = 4096


class _ClaimingRedis(Protocol):
    """The single Redis call this store makes, typed so a fake can stand in."""

    def set(self, name: str, value: str, ex: int | None = ..., nx: bool = ...) -> object: ...


class MemoryRenditionDispatchClaims(IRenditionDispatchClaims):
    """Bounded, TTL'd in-process claim map — the degradation tier and the test default.

    Across several worker processes it windows per process, which weakens the
    bound by the process count but does not remove it.
    """

    def __init__(self, ttl_seconds: int = DISPATCH_WINDOW_SECONDS, capacity: int = _FALLBACK_CAPACITY) -> None:
        self._ttl_seconds = ttl_seconds
        self._capacity = capacity
        # attachment id -> expires_at; insertion-ordered so eviction drops oldest first.
        self._claims: OrderedDict[str, datetime] = OrderedDict()
        # Thumbnail GETs run in the threadpool; the check-and-set must be atomic.
        self._lock = threading.Lock()

    def claim(self, attachment_id: str) -> bool:
        now = datetime.now(UTC)
        with self._lock:
            expires_at = self._claims.get(attachment_id)
            if expires_at is not None and expires_at > now:
                return False
            self._claims.pop(attachment_id, None)
            self._claims[attachment_id] = now + timedelta(seconds=self._ttl_seconds)
            while len(self._claims) > self._capacity:
                self._claims.popitem(last=False)
            return True


#: Process-wide default. A per-call instance would start empty every time and
#: always claim — a window that looks implemented and suppresses nothing.
DEFAULT_RENDITION_DISPATCH_CLAIMS = MemoryRenditionDispatchClaims()


class RedisRenditionDispatchClaims(IRenditionDispatchClaims):
    """Valkey-backed claim shared across replicas, with an in-process fallback."""

    def __init__(
        self,
        redis_client: _ClaimingRedis,
        ttl_seconds: int = DISPATCH_WINDOW_SECONDS,
        fallback: IRenditionDispatchClaims | None = None,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        self._fallback = fallback if fallback is not None else DEFAULT_RENDITION_DISPATCH_CLAIMS

    def claim(self, attachment_id: str) -> bool:
        """Claim via ``SET key value NX EX ttl`` — one round trip, no race."""
        try:
            claimed = self._redis.set(f"{_PREFIX}{attachment_id}", "1", ex=self._ttl_seconds, nx=True)
        except (RedisError, OSError) as exc:
            logger.warning("rendition_dispatch_claims_unavailable", error=loggable_error(exc))
            return self._fallback.claim(attachment_id)
        return bool(claimed)
