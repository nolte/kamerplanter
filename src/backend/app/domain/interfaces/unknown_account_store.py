"""Lockout bookkeeping for email addresses that own no account.

The login lockout used to live exclusively on the ``User`` document
(``failed_login_attempts`` / ``locked_until``). An address without an account has
no document, so it could never reach the lockout and ``/auth/login`` answered
423 for registered addresses and 401 for everything else — an account-enumeration
oracle that needs no password guess at all.

This store gives the non-existent address the same counter, so both paths can
run the identical :class:`~app.domain.engines.login_throttle_engine.LoginThrottleEngine`
decision and produce the identical response.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class IUnknownAccountStore(ABC):
    """Failed-attempt bookkeeping keyed by an address that has no account."""

    @abstractmethod
    def get_failure_state(self, email: str) -> tuple[int, datetime | None]:
        """Return ``(failed_attempts, locked_until)`` for the address.

        Returns ``(0, None)`` when nothing is recorded — the same starting state
        a freshly created ``User`` document carries.
        """
        ...

    @abstractmethod
    def record_failure(
        self,
        email: str,
        failed_attempts: int,
        locked_until: datetime | None,
    ) -> None:
        """Persist the attempt counter and lockout expiry for the address."""
        ...
