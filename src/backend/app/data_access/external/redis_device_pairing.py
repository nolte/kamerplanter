"""Redis-backed one-time store for QR device-pairing codes (REQ-023, #1118).

See :mod:`app.domain.interfaces.device_pairing_store` for why the guarantees
live here rather than in the service.

Shape follows :class:`~app.data_access.external.redis_oauth_state.RedisOAuthStateStore`
— ``SET`` with an ``ex`` TTL, and a **pipelined** ``GET``+``DEL`` for the
one-time read, which is what makes two simultaneous redemptions of the same code
resolve to one winner instead of two sessions. Keys are digests, following
:mod:`app.data_access.external.unknown_account_store` and
``RefreshToken.token_hash``.

Redis errors are handled **asymmetrically**, on purpose:

* ``consume`` fails **closed** — an outage answers like an unknown code, so a
  redemption is refused rather than granted, and the caller still cannot tell
  the two apart.
* ``issue`` fails **loud** — swallowing the write would hand the user a QR code
  that can never be redeemed, i.e. a silent, unreportable failure instead of a
  500 the operator can see.

There is deliberately no in-process fallback tier here, unlike the sibling
lockout stores. Those count *against* a caller, so a fallback keeps a guard from
going inert. This one hands out *credentials*: a per-replica fallback would make
a code redeemable only on the replica that minted it, which behind a load
balancer means intermittent, unexplainable failures — and during an outage the
right answer for a credential store is "no", which is exactly what a raising
``issue`` and a ``None``-returning ``consume`` produce.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import structlog

from app.domain.interfaces.device_pairing_store import (
    DevicePairingRecord,
    IDevicePairingCodeStore,
)

logger = structlog.get_logger()

_PREFIX = "kp:auth:pairing:"

#: Fallback lifetime of one pairing code, in seconds.
#:
#: The operative value is ``settings.device_pairing_ttl_seconds`` (default 90,
#: bounded 60–120 by the settings model); this constant only keeps a store
#: constructed without an explicit TTL inside that window instead of unbounded.
DEFAULT_TTL_SECONDS = 90


class _RedisPipeline(Protocol):
    """The queued commands the one-time read uses, typed so a fake can stand in."""

    def get(self, name: str) -> Any: ...

    def delete(self, *names: str) -> Any: ...

    def execute(self) -> list[Any]: ...


class _PairingRedis(Protocol):
    """The two Redis entry points this store uses.

    ``redis-py`` is constructed with ``decode_responses=True`` throughout this
    codebase, hence ``str`` rather than ``bytes``.
    """

    def set(self, name: str, value: str, ex: int | None = ...) -> object: ...

    def pipeline(self) -> _RedisPipeline: ...


def _digest(code: str) -> str:
    """Return the full sha256 of the raw code, used as the store key.

    Full length, not truncated: a collision would let one user's code redeem
    into another user's account.
    """
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class RedisDevicePairingCodeStore(IDevicePairingCodeStore):
    """Single-use pairing codes in Redis, expiring by TTL."""

    def __init__(
        self,
        redis_client: _PairingRedis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    @property
    def ttl_seconds(self) -> int:
        """Lifetime handed to Redis, so callers can report ``expires_in``."""
        return self._ttl_seconds

    def issue(self, code: str, user_key: str) -> datetime:
        """Store ``{user_key, issued_at}`` under the code's digest with a TTL.

        Raises:
            Exception: whatever the Redis client raises. Deliberately not
                swallowed — see the module docstring.
        """
        issued_at = datetime.now(UTC)
        key_digest = _digest(code)
        self._redis.set(
            f"{_PREFIX}{key_digest}",
            json.dumps({"user_key": user_key, "issued_at": issued_at.isoformat()}),
            ex=self._ttl_seconds,
        )
        logger.info(
            "device_pairing_code_issued",
            user_key=user_key,
            # Digest prefix, never a prefix of the code itself: a raw prefix in
            # a log line shrinks the search space of the credential it names.
            code_sha256=key_digest[:16],
            ttl_seconds=self._ttl_seconds,
        )
        return issued_at + timedelta(seconds=self._ttl_seconds)

    def consume(self, code: str) -> DevicePairingRecord | None:
        """Read and delete the code in one pipeline — see the interface docstring."""
        key_digest = _digest(code)
        key = f"{_PREFIX}{key_digest}"
        try:
            pipe = self._redis.pipeline()
            pipe.get(key)
            pipe.delete(key)
            results = pipe.execute()
        except Exception as exc:  # noqa: BLE001 - an outage answers like an unknown code
            logger.warning("device_pairing_store_unavailable", operation="consume", error=str(exc))
            return None

        raw = results[0] if results else None
        if raw is None:
            logger.info("device_pairing_code_not_redeemable", code_sha256=key_digest[:16])
            return None

        try:
            payload = json.loads(raw)
            record = DevicePairingRecord(
                user_key=str(payload["user_key"]),
                issued_at=datetime.fromisoformat(payload["issued_at"]),
            )
        except (ValueError, TypeError, KeyError) as exc:
            # A malformed value must answer like an unknown code, not raise:
            # a 500 here would tell the caller their code existed.
            logger.warning("device_pairing_code_corrupt_entry", error=str(exc))
            return None
        return record
