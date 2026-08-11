"""Lockout bookkeeping for device-pairing redemption, keyed by source IP (#1118).

``POST /api/v1/auth/device-pairing/redeem`` is unauthenticated and mints a full
token pair. The per-IP ``slowapi`` limit on the route bounds the *rate* of
guessing but never stops it: it refuses the burst and lets the next minute's
budget through, forever. A guessing loop that respects the limit is a guessing
loop that never ends.

This store gives that surface the same counter the login path has, so the same
:class:`~app.domain.engines.login_throttle_engine.LoginThrottleEngine` decision
can turn repeated failures into a growing lockout. Reusing the engine is the
point: a second threshold constant here would drift from the login one and
nobody would notice which of the two was in force.

The subject is an IP address rather than an account, because redemption has no
account until it succeeds. The address is personal data (NFR-011), and the
caller supplying it is unauthenticated, so it is stored as a digest — the same
convention as :mod:`app.domain.interfaces.unknown_account_store`.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class IDevicePairingThrottleStore(ABC):
    """Failed-redemption bookkeeping keyed by the redeeming source address."""

    @abstractmethod
    def get_failure_state(self, ip_address: str) -> tuple[int, datetime | None]:
        """Return ``(failed_attempts, locked_until)`` for the address.

        Returns ``(0, None)`` when nothing is recorded, which is the state an
        address that has never redeemed must be indistinguishable from.
        """
        ...

    @abstractmethod
    def record_failure(
        self,
        ip_address: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        """Persist the attempt counter and lockout expiry for the address."""
        ...

    @abstractmethod
    def clear(self, ip_address: str) -> None:
        """Drop the counter after a *successful* redemption.

        Without this a household behind one NAT address would accumulate
        failures from mistyped or expired codes across days until an entirely
        legitimate pairing is refused. A success is proof of possession, so it
        is the natural reset — mirroring ``login_local``, which zeroes
        ``failed_login_attempts`` on a correct password.
        """
        ...
