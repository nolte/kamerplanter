"""Attempt bookkeeping for password step-ups, keyed by a caller-derived subject (#1816).

A step-up re-checks the current password of a *signed-in* account before an
irreversible act (account erasure, tenant deletion) or a password change. Until
#1816 every one of those checks ran bcrypt without any bound: with a stolen
session each route was an unthrottled password oracle, and the lockout that
protects ``/auth/login`` did not apply.

This store gives the step-up its own counters. It is deliberately **not** the
login lockout (``User.failed_login_attempts`` / ``locked_until``): the only
caller that can produce a step-up failure for an account is someone holding a
session of that account, and letting that caller lock the *login* would hand a
session thief a way to keep the owner from signing in and revoking the stolen
session. See :mod:`app.domain.services.step_up_service` for the full reasoning.

**Reservation, not after-the-fact counting.** :meth:`reserve_attempt` counts an
attempt *before* the password is tested and returns the new count atomically.
The login and pairing counters read, test, then write back — a burst of
concurrent requests all read the same count and all get to test a password.
Here the n-th concurrent attempt sees ``n`` and is refused once ``n`` passes the
threshold, whatever the timing. A correct password clears the counter, so the
reservation it spent costs the owner nothing.

Subjects are opaque strings built by the verifier (account key, or account key
plus client address); implementations store only a digest of them (NFR-011).
"""

from abc import ABC, abstractmethod
from collections.abc import Callable


class IStepUpThrottleStore(ABC):
    """Attempt counters and lockout windows for password step-ups."""

    @abstractmethod
    def lock_remaining_seconds(self, subject: str) -> int:
        """Seconds the subject stays locked; ``0`` when it is not locked."""
        ...

    @abstractmethod
    def reserve_attempt(self, subject: str) -> int:
        """Count one attempt for the subject atomically and return the new count.

        The count lives for the store's window (24 h after the last attempt) so the
        lockout backoff grows across repeated lockouts, as the login one does.
        """
        ...

    @abstractmethod
    def strike(self, subject: str, *, rearm_to: int, lock_seconds: Callable[[int], int]) -> int:
        """Lock the subject after a failed attempt; return how many locks it has had.

        In **one** step (a single transaction in the shared tier): the strike count
        goes up by one, the lock is set for ``lock_seconds(strikes)`` seconds, and
        the attempt counter is set back to *rearm_to* — so once the lock ends the
        next attempt is tested again (one try, as after a login lockout) instead of
        being refused on a count that only ever grows (security review SEC-001).
        One step, because a request arriving between a separate re-arm and lock
        would pass the lock check and be tested (``/code-review`` of #1846).

        Reservations refused over the budget are never given back: the re-arm
        overwrites them, and a give-back landing after it would undercount.
        """
        ...

    @abstractmethod
    def lock(self, subject: str, seconds: int) -> None:
        """Lock the subject for *seconds* (a longer existing lock is replaced)."""
        ...

    @abstractmethod
    def clear(self, subject: str) -> None:
        """Drop counter, strikes and lock after a *successful* step-up (proof of possession)."""
        ...
