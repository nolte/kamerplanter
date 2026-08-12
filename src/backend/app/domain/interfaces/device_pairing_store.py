"""One-time codes that pair a mobile client with an account (REQ-023, #1118).

The QR code shown in the browser carries a short-lived secret. Redeeming it
mints the *existing* REQ-023 token pair, so the code is a bearer credential for
the few seconds it lives: whoever presents it first gets the session. Two
properties therefore belong to the store, not to its callers:

* **single use** — the read and the delete happen in one round trip, so two
  racing redemptions cannot both win;
* **expiry** — the store, not a sweep task, is what makes a forgotten code stop
  working (``settings.device_pairing_ttl_seconds``, bounded to 60–120 s).

The code itself is never written down. The store key is a sha256 digest of it,
following the pseudonymisation convention already used for
``RefreshToken.token_hash`` and
:mod:`app.data_access.external.unknown_account_store` — a Redis dump, a slow-log
line or a keyspace notification must not hand a reader a redeemable credential.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DevicePairingRecord:
    """What a pairing code stands for while it is valid.

    Attributes:
        user_key: The ``User`` document key the code was issued for. The code is
            bound to its issuer here, so redemption never has to trust a
            caller-supplied identity.
        issued_at: Issue time (UTC), for the audit event on redemption.
    """

    user_key: str
    issued_at: datetime


class IDevicePairingCodeStore(ABC):
    """Single-use, self-expiring custody of pairing codes."""

    @abstractmethod
    def issue(self, code: str, user_key: str) -> datetime:
        """Persist ``code`` for ``user_key`` and return its expiry (UTC).

        Args:
            code: The raw pairing code. Stored only as a digest.
            user_key: The ``User`` document key the code is bound to.

        Returns:
            The instant after which the code no longer redeems, so the caller
            can put it in the QR payload without re-deriving the TTL.
        """
        ...

    @abstractmethod
    def consume(self, code: str) -> DevicePairingRecord | None:
        """Redeem ``code`` exactly once.

        Returns the record on the first call for a live code and ``None`` on
        every later call for it.

        ``None`` is the single answer for "unknown", "already used", "expired"
        and "store unreachable". The caller must not be able to tell those
        apart, and neither must its caller: distinguishing "used" from "never
        existed" would confirm to an attacker that a guessed code was real.
        Implementations therefore never raise to signal a bad code.
        """
        ...
