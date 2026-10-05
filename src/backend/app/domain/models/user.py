from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, PrivateAttr

from app.common.validators import DisplayName

# REQ-023 v1.10: ``service`` accounts are M2M identities (Home Assistant,
# Grafana, CI/CD). They have no password, can never log in via the
# web UI, and authenticate exclusively via API keys with optional IP
# allowlists and per-account rate limits.
#
# The other value is ``human``, the spelling REQ-023 §Datenmodell declares
# (``Literal['human', 'service']``, default ``human``). The code carried
# ``user`` until #1620; ``v0055_rename_account_type_user_to_human`` rewrites the
# rows that were stored under it. The two spellings are held together by
# ``tests/unit/guards/test_spec_literal_discriminators_match_models.py``, which
# reads this literal and the spec's and refuses a third one.
AccountType = Literal["human", "service"]

#: Domain of the address a soft-deleted account is parked under (REQ-025 Szenario 3).
#:
#: RFC 2606's documentation domain: guaranteed undeliverable, and — unlike
#: ``.local``/``.invalid``/``.test`` — accepted by ``EmailStr``'s validator, which
#: refuses every special-use/reserved name. The previous ``@deleted.local`` made the
#: repository's model re-validation (#968) raise, so the soft-delete persisted nothing
#: at all (#1525).
DELETED_EMAIL_DOMAIN = "deleted.example.com"


def tombstone_email(user_key: str) -> str:
    """The address ``UserService.delete_account`` parked a soft-deleted account under.

    That method is gone (#1813 — ``DELETE /users/me`` now opens the Art. 17
    request), but accounts it tombstoned still carry this address, so the domain
    stays reserved (:func:`is_tombstone_email`).
    """
    return f"deleted_{user_key}@{DELETED_EMAIL_DOMAIN}"


def is_tombstone_email(email: str) -> bool:
    """Whether ``email`` lives in the reserved soft-delete domain.

    ``users.email`` is uniquely indexed, so an address in this domain that somebody
    *registered* would make the eventual soft-delete of the account it impersonates
    collide: the Art. 17 path would answer 409 and the account could not be deleted at
    all. Registration and the email-change flow therefore refuse the domain outright
    (#1525 SCR-014). The rule is on the address alone, never on whether an account
    exists, so it adds no enumeration oracle (SEC-H-009).
    """
    return email.strip().lower().endswith(f"@{DELETED_EMAIL_DOMAIN}")


class User(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    email: EmailStr
    display_name: DisplayName
    password_hash: str | None = None
    email_verified: bool = False
    #: When the owner of the address proved it (#1948): set only by the verification link, the
    #: e-mail-change confirmation, its revert, or an OIDC provider asserting ``email_verified``.
    #: ``email_verified`` alone proves nothing — with ``REQUIRE_EMAIL_VERIFICATION=false``
    #: registration stamps it without a confirmation — so every consumer that mails the address
    #: (REQ-030 §3.4) reads this field. ``None`` means "never proven".
    email_confirmed_at: datetime | None = None
    #: When an administrator lowered ``email_verified`` on a verified account (#1992). Set, the
    #: account is not an abandoned registration, whatever ``email_verified`` says now: the
    #: unverified-account cleanup (NFR-011 R-02) never selects or erases it.
    email_verified_lowered_at: datetime | None = None
    #: SHA-256 hex digest of the single-use verification token (#2158). The raw token
    #: only ever travels in the mail; the lookup hashes what the link presents
    #: (``TokenEngine.hash_token``), so a read of the database or of a backup yields
    #: no working link. ``v0085_hash_account_tokens`` hashed the values stored in clear.
    email_verification_token_hash: str | None = None
    email_verification_expires: datetime | None = None
    #: SHA-256 hex digest of the single-use password-reset token (#2158); see
    #: :attr:`email_verification_token_hash`.
    password_reset_token_hash: str | None = None
    password_reset_expires: datetime | None = None
    is_active: bool = True
    # REQ-023 v1.10 service accounts (M2M). ``human`` is the spec's default (#1620).
    account_type: AccountType = "human"
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    avatar_url: str | None = None
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    #: Moves on every event that ends **all** sessions of the account (#2116): logout
    #: everywhere, password reset or change, deactivation, an Art. 17 request. A
    #: refresh token minted under an older generation is refused.
    #:
    #: Written only by ``IRefreshTokenRepository`` in the same statement that revokes
    #: the sessions; :class:`~app.data_access.arango.user_repository.ArangoUserRepository`
    #: never writes either counter, so a writer that read the account before the
    #: revocation cannot set it back (``update_fields`` rewrites the whole account).
    session_generation: int = 0
    #: Moves on every revocation, of one session or of all (#2116). An access token
    #: carries the value it was minted under (claim ``gen``) and stops resolving the
    #: moment this moves: ``FullAuthProvider`` compares it with the account it reads
    #: anyway, so the check costs no extra read. Revoking one session therefore ends
    #: the access tokens of the account's other sessions too; their next request
    #: refreshes silently (their refresh tokens are untouched).
    access_token_generation: int = 0
    #: The ``tenant_scope`` of the API key this request authenticated with (#1817).
    #:
    #: Request state, not account state: a *private* attribute, so no stored
    #: document or validated payload can set it (``model_validate`` ignores it)
    #: and no ``model_dump`` can persist it. Only
    #: :meth:`with_api_key_tenant_scope` sets it, which
    #: ``AuthService.authenticate_api_key`` calls for a ``kp_`` bearer; every other
    #: resolution leaves it ``None`` (a session is never tenant-restricted). The
    #: tenant resolvers in ``app.common.auth`` refuse any tenant it does not admit.
    _api_key_tenant_scope: str | None = PrivateAttr(default=None)

    model_config = {"populate_by_name": True}

    @property
    def address_proven(self) -> bool:
        """Whether the owner of the address proved it — the only trust signal for acting on the address.

        ``email_verified`` alone proves nothing (registration stamps it with
        ``REQUIRE_EMAIL_VERIFICATION=false``), and a lowered flag (#1992) leaves the
        proof behind: both must hold.
        """
        return self.email_verified and self.email_confirmed_at is not None

    @property
    def api_key_tenant_scope(self) -> str | None:
        """The authenticating API key's tenant restriction, ``None`` for a session (#1817)."""
        return self._api_key_tenant_scope

    def with_api_key_tenant_scope(self, scope: str | None) -> User:
        """A copy of this account carrying one request's API-key tenant restriction.

        A copy, so an account object a repository hands out (and may cache) is
        never marked with one request's credential.
        """
        principal = self.model_copy()
        principal._api_key_tenant_scope = scope
        return principal


def allows_interactive_auth(user: User) -> bool:
    """Whether this account may hold a password and be handed a browser session.

    The REQ-023 boundary in one predicate, on the *state* rather than on a route
    (#1559). A ``service`` account is an M2M identity — Home Assistant, Grafana,
    CI/CD — that authenticates with API keys under an IP allowlist and a
    per-account rate limit; an interactive session carries none of those, and a
    stored password hash is a second credential the account type says must not
    exist.

    Kept here, next to :data:`AccountType`, so that the rule reads off the model
    every layer already imports instead of being restated as ``account_type ==
    "service"`` at each call site, which is the shape that drifts between
    siblings. Call sites today: the credential gates and the session-minting
    backstop in :class:`~app.domain.services.auth_service.AuthService`.
    """
    return user.account_type != "service"


class UserProfile(BaseModel):
    key: str
    email: str
    display_name: str
    email_verified: bool
    is_active: bool
    avatar_url: str | None
    locale: str
    timezone: str = "Europe/Berlin"
    last_login_at: datetime | None
    created_at: datetime | None


class UserProfileUpdate(BaseModel):
    display_name: DisplayName | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
