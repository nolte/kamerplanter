"""Storage of the e-mailed one-time step-up code (#1815).

An account without a local password — it signs in only through a federated
provider — has no secret of its own to re-enter before an irreversible act or a
credential change. Until #1815 the typed echo (its e-mail, a tenant slug) was its
whole confirmation, which a hijacked session types as easily as the owner. The
step-up now mails such an account a short one-time code and requires it back; this
store holds the code between the two requests.

The store keeps **one** digest per subject, replaced on every issue, and hands it
out once. It also keeps the issuance bounds of review SEC-002
(:meth:`IStepUpCodeStore.reserve_issue`: a replacement wait and an hourly budget),
because they are facts about the codes it holds. What a subject is (the account
key), how the digest is formed (bound to the act, review SEC-003), the bound values
and how many wrong codes may be tried are the verifier's business
(:mod:`app.domain.services.step_up_service`) — wrong codes are counted in the
step-up throttle, not here, so a code and a password share one budget.

Neither the subject nor the code is stored in the clear (NFR-011): implementations
key by a digest of the subject and store only the digest the verifier hands over.
"""

from abc import ABC, abstractmethod


class IStepUpCodeStore(ABC):
    """One pending one-time step-up code per subject."""

    @abstractmethod
    def issue(self, subject: str, code_digest: str, ttl_seconds: int) -> None:
        """Store *code_digest* for *subject* for *ttl_seconds*, replacing any previous code."""
        ...

    @abstractmethod
    def reserve_issue(self, subject: str, *, cooldown_seconds: int, max_issues: int, window_seconds: int) -> int:
        """Admit one more code for *subject*, or say how many seconds to wait (review SEC-002).

        ``0`` admits the issue and counts it; a positive number refuses it. Two bounds,
        checked in this order:

        * **Replacement wait** — while a code issued less than *cooldown_seconds* ago
          is still unspent, no new code replaces it. A refusal here is not counted.
        * **Budget** — at most *max_issues* codes per *window_seconds*. The issue is
          *reserved* atomically before the code is minted (as the throttle reserves
          attempts), so a concurrent burst cannot overshoot the budget.

        Without these, a session holder could make the account mail a code on every
        request (the per-address rate limit only bounds one address), and each new
        code silently voided the one the owner was typing.
        """
        ...

    @abstractmethod
    def release_issue(self, subject: str) -> None:
        """Take back the last issue of *subject*: drop its code and wait, return one budget slot.

        For a code that could not be delivered (/code-review of #1862): it was
        never in the owner's hands, so it must neither confirm anything nor hold
        the next request back. The budget never goes below zero.
        """
        ...

    @abstractmethod
    def consume(self, subject: str, code_digest: str) -> bool:
        """Spend the subject's code if *code_digest* matches it; ``True`` only for the one caller that did.

        Single use: of several concurrent callers presenting the right code, only
        the one whose delete actually removed the entry wins. A wrong digest leaves
        the stored code in place (guesses are bounded by the step-up throttle), and
        an expired code matches nothing.
        """
        ...
