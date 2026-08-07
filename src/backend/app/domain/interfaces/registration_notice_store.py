"""Per-recipient suppression window for the duplicate-registration notice.

REQ-023 §3.2 wants the address that already owns an account to be told that
somebody tried to register with it. ``/auth/register`` is **anonymous**: the
attacker picks both the recipient and the trigger. Without a bound per recipient
that requirement is a mail-bombing primitive that spends this deployment's sender
reputation, and the obvious counter-measure — blocking the source — would take
password reset and email verification down for everyone.

So the notice is rate-limited where the abuse lands: at the *recipient*. One
notification per address per window; everything inside the window is dropped
silently. The recipient loses nothing by that — the second and the thousandth
attempt carry exactly the information the first one already delivered.

The interface is a single **claim** rather than a get/set pair on purpose: two
workers may pick up two attempts for the same address at the same moment, and
"read, decide, write" would let both send. Implementations must make the claim
atomic.
"""

from abc import ABC, abstractmethod


class IRegistrationNoticeStore(ABC):
    """Bookkeeping for "has this address already been told, recently?"."""

    @abstractmethod
    def claim(self, email: str) -> bool:
        """Atomically claim the notification slot of ``email`` for one window.

        Args:
            email: Recipient address. Implementations normalise and digest it;
                it is never stored in the clear.

        Returns:
            ``True`` when the caller may send — the slot was free and is now
            taken for the length of the window. ``False`` when a notification
            for this address was already claimed inside the current window.
        """
        ...
