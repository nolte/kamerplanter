"""Who may create an account — the registration policy of an installation (REQ-023 §3.2d, #2132).

Pure logic: the mode and the domain allowlist come from the settings, the facts about one attempt
(the address, whether an e-mail invitation admits it, whether a provider proved the address) from the
caller. The decision never reads stored accounts, so a refusal cannot tell whether an address exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.common.enums import RegistrationMode


def email_domain(email: str) -> str | None:
    """The domain of *email*, lower-cased; ``None`` when the address has none."""
    local, at, domain = email.strip().rpartition("@")
    if not at or not local or not domain:
        return None
    return domain.lower()


def parse_domain_allowlist(raw: str) -> frozenset[str]:
    """``REGISTRATION_ALLOWED_DOMAINS`` as a set: comma-separated, case-folded, an optional ``@`` dropped."""
    domains = (part.strip().lower().removeprefix("@") for part in raw.split(","))
    return frozenset(domain for domain in domains if domain)


@dataclass(frozen=True)
class RegistrationPolicy:
    """The registration mode and the optional allowlist of e-mail domains.

    The rule, in the order it is decided:

    * ``closed`` admits nobody — an invitation included; otherwise ``closed`` and ``invite_only``
      would be the same mode. Existing accounts sign in as before; only *creating* one is refused.
    * an **e-mail invitation** that admits the address (pending, unexpired, issued for exactly that
      address, proven by its token or by the provider's assertion of the address) admits the
      registration in ``invite_only`` and outside the allowlist — the invitation is the exception.
    * ``invite_only`` admits nobody else.
    * ``open`` admits everybody, or — with an allowlist — the addresses of its domains (exact
      match, case-insensitive; a subdomain is another domain). On the first OIDC sign-in the
      allowlist counts only an address the provider asserted as verified: an unproven claim of
      ``someone@club.example`` proves nothing about membership of the club.

    ``provider_proven`` is ``None`` for a local registration (no provider; the address is proven
    later by the verification mail) and the provider's ``email_verified`` assertion otherwise.
    """

    mode: RegistrationMode = RegistrationMode.OPEN
    allowed_domains: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_settings(cls, mode: str, allowed_domains: str) -> RegistrationPolicy:
        return cls(mode=RegistrationMode(mode), allowed_domains=parse_domain_allowlist(allowed_domains))

    @property
    def domain_restricted(self) -> bool:
        return bool(self.allowed_domains)

    def admits(self, email: str, *, invited: bool, provider_proven: bool | None) -> bool:
        """Whether an account may be created for *email* (see the class docstring for the rule)."""
        if self.mode == RegistrationMode.CLOSED:
            return False
        if invited:
            return True
        if self.mode == RegistrationMode.INVITE_ONLY:
            return False
        if not self.allowed_domains:
            return True
        if provider_proven is False:
            return False
        return email_domain(email) in self.allowed_domains
