import hashlib
import hmac
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from secrets import token_urlsafe
from typing import NoReturn

import structlog

from app.common.datetimes import now_utc
from app.common.decoys import decoy_document_key, email_digest
from app.common.enums import AuthProviderType, TenantRole
from app.common.exceptions import (
    AccountLockedError,
    EmailNotVerifiedError,
    ForbiddenError,
    InvalidTokenError,
    NotFoundError,
    OAuthAutoLinkRefusedError,
    StepUpCodeUndeliverableError,
    StepUpReauthFailedError,
    StepUpReauthUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from app.common.log_privacy import log_subject, loggable_ip
from app.common.types import UserKey
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.data_access.external.device_pairing_throttle import DEFAULT_DEVICE_PAIRING_THROTTLE_STORE
from app.data_access.external.redis_oauth_state import RedisOAuthStateStore
from app.data_access.external.step_up_throttle import (
    DEFAULT_PASSWORD_RESET_STORE,
    DEFAULT_VERIFICATION_RESEND_PROVEN_STORE,
    DEFAULT_VERIFICATION_RESEND_STORE,
)
from app.data_access.external.unknown_account_store import DEFAULT_UNKNOWN_ACCOUNT_STORE
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.erasure_engine import UNAVAILABLE_LOG_SUBJECT
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import (
    FreshReauthRejectedError,
    InsecureEndpointError,
    LoginIdentityRejectedError,
    OAuthEngine,
    supports_fresh_reauth,
)
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.device_pairing_store import IDevicePairingCodeStore
from app.domain.interfaces.device_pairing_throttle import IDevicePairingThrottleStore
from app.domain.interfaces.email_change_repository import IEmailChangeRepository
from app.domain.interfaces.email_service import EmailUndeliverableError, IEmailService
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.step_up_throttle import IStepUpThrottleStore
from app.domain.interfaces.unknown_account_store import IUnknownAccountStore
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.auth import (
    DEVICE_NAME_MAX_LENGTH,
    ApiKey,
    ApiKeyCreated,
    ApiKeySummary,
    AuthProvider,
    AuthProviderInfo,
    OAuthRedirect,
    OAuthUserInfo,
    RefreshToken,
    SessionInfo,
    TokenPair,
)
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User, UserProfile, allows_interactive_auth, is_tombstone_email
from app.domain.services.api_key_controls import ApiKeyRateLimiter, enforce_api_key_controls
from app.domain.services.step_up_service import (
    CODE_PURPOSES,
    TARGETED_ACTIONS,
    FederatedReauthPolicy,
    StepUpAction,
    StepUpVerifier,
    default_step_up_verifier,
)
from app.domain.services.tenant_service import TenantService

logger = structlog.get_logger()

#: Hands a no-argument callable to whatever runs work after the response (FastAPI's
#: ``BackgroundTasks.add_task``). The service never imports the web layer (#1890).
MailDeferrer = Callable[[Callable[[], None]], object]


def _iso(value):  # noqa: ANN001, ANN202 — datetime | None -> str | None
    """Serialize an optional datetime for a partial update doc (JSON mode)."""
    return value.isoformat() if value is not None else None


_API_KEY_PREFIX = "kp_"

#: What a tenant key or slug looks like; the shape ``create_api_key`` accepts as a scope (#1852).
_TENANT_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")

#: The single refusal message for an account whose ``is_active`` is ``False``
#: (#1528). All six raise sites **in this module** use it — the five entry points
#: plus the backstop in ``_create_tokens`` — so they cannot drift into answers
#: that are distinguishable from one another.
#:
#: **It is not, however, repository-wide, and this note says so (SCR-001).** Two
#: raise sites outside this module answer the same condition in their own words:
#: ``full_auth_provider.resolve_user`` ("User not found or inactive.") and
#: ``mcp_server.auth.McpAuth.authenticate`` ("Account not found or inactive.").
#: All three are 401 and all three sit after an accepted credential, so the three
#: wordings cost nothing an attacker can use; unifying them would change two API
#: contracts this issue is not about. The constant stays module-local rather than
#: moving to ``app/common/``, and this note exists so the next reader measures the
#: other two instead of trusting a "the one place" claim that was not true.
#:
#: Deliberately **not** the message a wrong password gets: the check that uses it
#: runs only *after* the credential has been accepted, so the caller who sees it
#: already holds the account's credential and learns nothing they could not
#: confirm otherwise. Seeing "inactive" is the diagnostic a suspended owner needs
#: in order to contact an administrator instead of resetting a password that was
#: never wrong.
#: The ``purpose`` a state entry of a step-up re-authentication carries (#1815). A
#: login state has none; the callback dispatches on it.
_STEP_UP_PURPOSE = "step_up"


@dataclass(frozen=True)
class OAuthCallbackOutcome:
    """What a provider callback produced: a session (sign-in) or a step-up token (#1815)."""

    token_pair: TokenPair | None = None
    raw_refresh: str | None = None
    is_persistent: bool = False
    step_up_token: str | None = None
    step_up_action: str | None = None
    #: The ``client_nonce`` the step-up was started with, handed back beside the token.
    step_up_client_nonce: str | None = None


_INACTIVE_ACCOUNT_MESSAGE = "User account is inactive."

#: Requests one address may make to ``/auth/resend-verification`` before the
#: mail stops (#2037). Three covers the legitimate case — the first mail went to
#: spam, the second was clicked too late — with one to spare. The budget's
#: window is ``step_up_throttle.VERIFICATION_RESEND_WINDOW_SECONDS`` (one hour,
#: renewed by every request). A request over the budget answers exactly like one
#: inside it; it only sends nothing. Fixed rather than configurable: raising it
#: turns the route back into a way to flood a chosen inbox.
MAX_VERIFICATION_RESENDS_PER_WINDOW = 3

#: Subject prefix of the resend budget in the shared step-up counter store; see
#: ``step_up_throttle.VERIFICATION_RESEND_WINDOW_SECONDS`` for why it cannot
#: collide with a step-up subject. The store normalises (strips, lowercases) and
#: digests the whole subject, so ``Victim@Example.com`` and ``victim@example.com``
#: share one budget and the address is never stored in the clear.
_VERIFICATION_RESEND_SUBJECT = "verification-resend:"

#: Fresh links the login refusal ``EMAIL_NOT_VERIFIED`` may mail one account per
#: window (#2046). That refusal is reached only with the account's correct
#: password, so it issues the link itself instead of sending the owner to the
#: anonymous resend, whose per-address budget anyone can spend for them. The
#: same number and window as :data:`MAX_VERIFICATION_RESENDS_PER_WINDOW`, on a
#: budget of its own, keyed by the account. Over it the refusal answers exactly
#: the same and only sends nothing.
MAX_PROVEN_VERIFICATION_RESENDS_PER_WINDOW = 3

#: Subject prefix of the proven budget — followed by the account key, never the
#: address, so no spelling of the address buys a second budget and an anonymous
#: request (subject ``verification-resend:<address>``) can never spend it. The
#: store digests the whole subject.
_VERIFICATION_RESEND_PROVEN_SUBJECT = "verification-resend-proven:"

#: Requests one **source address** may make to ``/auth/password-reset/request``
#: for one recipient before the mail stops (#2043, per source since #2059). The
#: same number and window as the resend budget
#: (:data:`MAX_VERIFICATION_RESENDS_PER_WINDOW`): the route is anonymous and the
#: caller chooses the recipient. The window is
#: ``step_up_throttle.PASSWORD_RESET_WINDOW_SECONDS`` (one hour, renewed by every
#: request of that source for that address — above the budget too, so a source
#: that keeps asking keeps only *itself* out). A request over the budget answers
#: exactly like one inside it; it only sends nothing. Fixed, not configurable.
#:
#: Why per source (#2059): counted per address alone, one request an hour kept
#: an address above the budget, and the owner — asking from her own address —
#: got no link. Measured on the real route with a fake clock: one source at the
#: default 20/minute held 1199 addresses; 100 owners asking from their own
#: address received 0 links.
MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW = 3

#: Links one recipient may receive per window over **all** sources (#2059) — the
#: bound on mail to one inbox now that each source has its own three. Counted
#: only for requests the per-source stage admitted, and renewed only by them,
#: so one source contributes at most
#: :data:`MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW` per window and holding an
#: address above this bound takes four sources that keep mailing it.
MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW = 10

#: Subject prefix of the reset budget over all sources — its own, so it never
#: shares a counter with the resend budget or a step-up subject. The address is
#: stripped and lowercased before the prefix is put in front (the lookup
#: compares ``LOWER(doc.email) == LOWER(@email)``); the store then digests it.
_PASSWORD_RESET_SUBJECT = "password-reset:"

#: Subject prefix of the per-source stage: ``password-reset-source:<address>|<ip>``.
#: The last ``|`` separates the two — a domain and an IP address contain none — so
#: no two pairs share a subject; the store digests it.
_PASSWORD_RESET_SOURCE_SUBJECT = "password-reset-source:"

#: The source a request is counted under when no client address could be
#: established (``resolve_client_ip`` returned ``None``): all such requests share
#: one per-source budget, which is the safe direction.
_UNKNOWN_SOURCE = "unknown"

#: Lifetime of a mailed e-mail verification link — at registration and on every
#: resend (#2037). One constant, so the two issuance paths cannot drift apart.
_VERIFICATION_TOKEN_TTL = timedelta(hours=24)

#: Answer to a service account that tries to acquire an interactive credential (#1559).
#:
#: 403 and not 401: the caller *is* authenticated — it presented a valid API key —
#: and what refuses it is the kind of account it is, which no credential changes.
#: The account type is stated outright because the caller already knows which
#: account its own key belongs to; there is no third party to leak it to.
_SERVICE_ACCOUNT_CREDENTIAL_MESSAGE = (
    "A service account authenticates with API keys only and cannot hold a password (REQ-023)."
)

#: Answer to an interactive session minted for a service account (#1559).
#:
#: Reached only once a credential has been accepted, like the inactive-account
#: message above, so it discloses nothing to an anonymous caller. Since the
#: credential gate keeps a service account from ever holding a password, the
#: local-login path can no longer reach this at all; a hash planted by a
#: migration, a fixture or an account converted from ``user`` still can.
_SERVICE_ACCOUNT_LOGIN_MESSAGE = "A service account cannot log in interactively (REQ-023)."


#: Entropy of one QR pairing code, in bytes handed to ``secrets.token_urlsafe``
#: (#1118). 32 bytes = 256 bit, the same budget as an API key and a refresh
#: token, which is what makes the 60–120 s guessing window a non-event.
_PAIRING_CODE_BYTES = 32

#: Throttle bucket for a redemption that arrives without a source address.
#:
#: The HTTP path always supplies one (``slowapi``'s ``get_remote_address``), so
#: this is reached only by non-HTTP callers. Sharing one bucket over-counts
#: those; skipping the throttle instead would make the guard opt-out-able by
#: simply not passing an address, which is the direction that costs something.
_UNKNOWN_IP_BUCKET = "unknown"

#: Cache for the throw-away hash the SEC-H-010 login guard verifies against.
#: Computed once per process on first use rather than at import time, so a
#: bcrypt round is not charged to every worker start.
_DECOY_PASSWORD_HASH: str | None = None


def _decoy_password_hash(password_engine: PasswordEngine) -> str:
    """Return a bcrypt hash no password can ever match.

    Hashes a fresh random string once per process. The value is never stored,
    never compared to a real credential, and cannot be pre-computed by an
    attacker — its only job is to make ``verify_password`` do its full work on
    the "this address has no account" branch, so that branch costs the same as
    the one that checks a real password.
    """
    global _DECOY_PASSWORD_HASH
    if _DECOY_PASSWORD_HASH is None:
        _DECOY_PASSWORD_HASH = password_engine.hash_password(secrets.token_urlsafe(32))
    return _DECOY_PASSWORD_HASH


def _code_fingerprint(code: str) -> str:
    """Return a short sha256 prefix of a pairing code, for audit lines.

    A prefix **of the code itself** would be the obvious thing to log and is the
    wrong thing: it shrinks the search space of the very credential the line is
    about, and the line outlives the 90-second code in whatever log sink
    collects it. The digest identifies one issuance across the
    ``device_pairing_created`` / ``device_pairing_redeemed`` pair without being
    reversible, and matches what
    :mod:`app.data_access.external.redis_device_pairing` already emits, so the
    two layers' lines correlate on the same value.
    """
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def _refusal_reason(exc: ValueError) -> str:
    """What may be logged of a ``ValueError`` from the provider-facing steps (#1987).

    The text of an :class:`InsecureEndpointError` names the endpoint kind and the rule, never a value.
    Any other ``ValueError`` here can be a ``pydantic.ValidationError`` whose text quotes the
    provider's claims (an e-mail address, a name): only its type is logged.
    """
    return str(exc) if isinstance(exc, InsecureEndpointError) else type(exc).__name__


def _id_token_issuer(token_response: dict) -> str | None:
    """The ``iss`` of the ID token in a token response; ``None`` without one (plain OAuth2, GitHub)."""
    if not token_response.get("id_token"):
        return None
    try:
        return str(OAuthEngine.id_token_claims(token_response).get("iss") or "") or None
    except ValueError:
        return None


def _report_budget_crossing(stage: str, address: str, reserved: int, budget: int) -> None:
    """Log the one request that takes a password-reset stage over its budget (#2059).

    Only the crossing, not every request above it: a source that keeps asking
    must not turn into a log flood. The address appears only as the keyed
    ``email_digest`` (NFR-011); the source address not at all. Operators see a
    subject pushed over its budget — the signature of the lock-out #2059
    describes — without the log naming whom.
    """
    if reserved == budget + 1:
        logger.warning("password_reset_budget_exhausted", stage=stage, email_digest=email_digest(address))


class AuthService:
    def __init__(
        self,
        user_repo: IUserRepository,
        auth_provider_repo: IAuthProviderRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_engine: PasswordEngine,
        token_engine: TokenEngine,
        throttle_engine: LoginThrottleEngine,
        email_service: IEmailService,
        frontend_url: str,
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 30,
        session_token_expire_hours: int = 24,
        tenant_service: TenantService | None = None,
        require_email_verification: bool = True,  # matches settings since #1948; wiring passes the setting
        oauth_engine: OAuthEngine | None = None,
        oauth_state_store: RedisOAuthStateStore | None = None,
        api_key_repo: IApiKeyRepository | None = None,
        oidc_config_repo: ArangoOidcConfigRepository | None = None,
        encryption_engine: EncryptionEngine | None = None,
        unknown_account_store: IUnknownAccountStore | None = None,
        device_pairing_code_store: IDevicePairingCodeStore | None = None,
        device_pairing_throttle_store: IDevicePairingThrottleStore | None = None,
        step_up_verifier: StepUpVerifier | None = None,
        email_change_repo: IEmailChangeRepository | None = None,
        light_mode: bool = False,
        api_key_rate_limiter: ApiKeyRateLimiter | None = None,
        verification_resend_store: IStepUpThrottleStore | None = None,
        password_reset_store: IStepUpThrottleStore | None = None,
        verification_resend_proven_store: IStepUpThrottleStore | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._auth_provider_repo = auth_provider_repo
        self._refresh_token_repo = refresh_token_repo
        self._password_engine = password_engine
        self._token_engine = token_engine
        self._throttle_engine = throttle_engine
        self._email_service = email_service
        self._frontend_url = frontend_url
        self._access_expire_min = access_token_expire_minutes
        self._refresh_expire_days = refresh_token_expire_days
        self._session_expire_hours = session_token_expire_hours
        self._tenant_service = tenant_service
        self._require_email_verification = require_email_verification
        self._oauth_engine = oauth_engine
        self._oauth_state_store = oauth_state_store
        self._api_key_repo = api_key_repo
        self._api_key_rate_limiter = api_key_rate_limiter
        self._oidc_config_repo = oidc_config_repo
        self._encryption_engine = encryption_engine
        # Never ``None``: a missing store would make the SEC-H-010 login guard
        # inert instead of merely process-local. See the module docstring of
        # ``data_access.external.unknown_account_store``.
        self._unknown_account_store: IUnknownAccountStore = (
            unknown_account_store if unknown_account_store is not None else DEFAULT_UNKNOWN_ACCOUNT_STORE
        )
        # #1118 device pairing. The two collaborators are wired asymmetrically,
        # for the same reason their stores are built differently:
        #
        # * the code store may be ``None`` — it is the *capability*, and an
        #   instance without it must refuse to mint codes (like ``api_key_repo``)
        #   rather than invent an in-process one, since a per-replica code store
        #   would hand out codes redeemable on one replica only;
        # * the throttle store is never ``None`` — it is the *guard*, and a
        #   missing one would not disable the feature, it would silently unbound
        #   guessing against it. Same reasoning as ``_unknown_account_store``.
        # #1816 — the one throttled step-up; the password change re-checks through it.
        self._step_up_verifier = step_up_verifier or default_step_up_verifier(password_engine)
        # #1815 — which provider links can re-authenticate freshly; the same rule
        # the verifier asks (``get_step_up_verifier`` builds it over the same repos).
        self._reauth_policy = (
            FederatedReauthPolicy(auth_provider_repo, oidc_config_repo) if oidc_config_repo is not None else None
        )
        # #1841 — the pending e-mail changes an owner's take-back withdraws; see
        # ``_cancel_pending_email_changes``.
        self._email_change_repo = email_change_repo
        # #1815 review — light mode has one shared, seeded system account.
        self._light_mode = light_mode
        self._device_pairing_code_store = device_pairing_code_store
        # #2037 — the per-address budget of the resend endpoint. Never ``None``,
        # for the reason ``_unknown_account_store`` is not: a missing store would
        # not disable the endpoint, it would unbound the mail it sends.
        self._verification_resend_store: IStepUpThrottleStore = (
            verification_resend_store if verification_resend_store is not None else DEFAULT_VERIFICATION_RESEND_STORE
        )
        # #2043 — the per-address budget of the reset request. Never ``None``, for
        # the reason ``_verification_resend_store`` is not.
        self._password_reset_store: IStepUpThrottleStore = (
            password_reset_store if password_reset_store is not None else DEFAULT_PASSWORD_RESET_STORE
        )
        # #2046 — the per-account budget of the link the login refusal mails.
        # Never ``None``, for the reason ``_verification_resend_store`` is not.
        self._verification_resend_proven_store: IStepUpThrottleStore = (
            verification_resend_proven_store
            if verification_resend_proven_store is not None
            else DEFAULT_VERIFICATION_RESEND_PROVEN_STORE
        )
        self._device_pairing_throttle_store: IDevicePairingThrottleStore = (
            device_pairing_throttle_store
            if device_pairing_throttle_store is not None
            else DEFAULT_DEVICE_PAIRING_THROTTLE_STORE
        )

    def _log_subject(self, user_key: str) -> str:
        """The reference an auth log line carries instead of the account key (#1773).

        :meth:`ErasureEngine.log_subject` under ``LOG_PSEUDONYM_SALT`` (#1812):
        the log stream has no retention rule (NFR-011) and outlives the account,
        so the lines name the subject by a salted reference — purpose-separated
        from the tombstone its pseudonymised audit rows get after an erasure
        (R-06), and keyed separately so the log salt can rotate. Without a salt
        every line carries the constant ``anon_unavailable`` — never the key.
        """
        return log_subject(user_key) or UNAVAILABLE_LOG_SUBJECT

    def _refuse_interactive_credential(self, user: User) -> None:
        """Refuse to grant ``user`` a password it is not allowed to hold (#1559).

        One helper for both write paths (``change_password``, ``reset_password``)
        rather than the same ``if`` twice, so the two cannot answer differently. The
        predicate itself is :func:`~app.domain.models.user.allows_interactive_auth`;
        nothing here decides what a service account is. A method rather than a
        module function since #1773, because the refusal is logged under the
        salted subject reference, which needs the instance's salt.

        Raises:
            ForbiddenError: 403, the account is a service account.
        """
        if allows_interactive_auth(user):
            return
        logger.warning(
            "service_account_interactive_credential_refused",
            subject=self._log_subject(user.key or ""),
        )
        raise ForbiddenError(_SERVICE_ACCOUNT_CREDENTIAL_MESSAGE)

    # ── Registration ────────────────────────────────────────────────────

    def register_local(
        self,
        email: str,
        password: str,
        display_name: str,
        *,
        on_existing_address: Callable[[UserKey], None] | None = None,
        defer_mail: MailDeferrer | None = None,
    ) -> UserProfile:
        """Register a local account, or answer as if one had been registered.

        Args:
            email: Submitted address.
            password: Submitted password, validated against the policy.
            display_name: Submitted display name.
            on_existing_address: Called with the **key of the existing account**
                when the address is already taken (REQ-023 §3.2). It MUST only
                defer work — the caller is inside the timed request, and any
                real I/O here would make the duplicate branch measurably differ
                from a genuine registration, which is the oracle SEC-H-009
                exists to close. The API layer passes a callback that appends to
                the response's background tasks; the enqueue itself then runs
                after the response has been written. ``None`` means "no notice",
                which is what unit tests and any non-HTTP caller want.
            defer_mail: Runs the verification mail after the response (#1890);
                see :meth:`_deliver_mail`. ``None`` sends inline, still without
                letting a delivery failure out.

        Returns:
            The profile of the created account — or, for a taken address, one
            synthesised to be indistinguishable from it.

        Raises:
            ValidationError: If the password violates the policy.
        """
        # The soft-delete tombstone domain is reserved (#1525 SCR-014). `users.email`
        # is uniquely indexed, so an account registered at
        # `deleted_<key>@deleted.example.com` would make the eventual soft-delete of
        # the account whose key it names collide — a caller could pick an address that
        # blocks somebody else's Art. 17 erasure. Checked before the duplicate lookup
        # and independently of any stored state, so it is no enumeration oracle.
        if is_tombstone_email(email):
            raise ValidationError("This email domain is reserved and cannot be registered.")

        # Check password policy
        errors = self._password_engine.validate_password_policy(password)
        if errors:
            raise ValidationError("; ".join(errors))

        skip_verification = not self._require_email_verification

        # Duplicate email — account-enumeration guard (SEC-H-009).
        #
        # This branch used to return ``self._to_profile(existing)``: the stored
        # record of whoever owns the address, handed to an unauthenticated caller
        # who had just proven nothing (any password, right or wrong, took this
        # path). That inverted the very property the comment claimed — the
        # response differed from a real registration in every field derived from
        # the account (key, display_name, email_verified, is_active, avatar_url,
        # locale, timezone, last_login_at, created_at), so it both confirmed the
        # address exists and disclosed another person's data.
        #
        # Nothing below is read from ``existing``: the profile is synthesised
        # from the SUBMITTED email and display name plus the defaults a
        # brand-new account would carry, so it matches what a genuine
        # registration returns field for field.
        existing = self._user_repo.get_by_email(email)
        # An address held for the revert of a confirmed e-mail change counts as
        # taken (/code-review of #1893): an account registered on it — no mailbox
        # access needed, registration is unverified — made every revert answer
        # "taken". No notice: the holder's current address may be the attacker's.
        reserved = existing is None and self._address_held_for_revert(email)
        if existing is not None or reserved:
            logger.info("registration_duplicate_suppressed", email_sha256=email_digest(email))
            # Hash the submitted password and throw the result away.
            #
            # This is not dead code and must not be deleted as such. The
            # response above is byte-for-byte indistinguishable from a real
            # registration, but this branch skipped the only expensive operation
            # the genuine path performs — bcrypt, which costs ~100 ms against
            # single-digit milliseconds for the DB write and the mail dispatch
            # that also do not happen here. A caller with a stopwatch therefore
            # still read the answer the body no longer gives: a fast 201 meant
            # "taken", a slow one meant "created".
            #
            # Charging the round here closes that gap. It also caps what the
            # branch costs an attacker to trigger: exactly what a genuine
            # registration costs, and `/auth/register` is rate-limited per IP.
            self._password_engine.hash_password(password)
            # REQ-023 §3.2: tell the address that already owns an account. Only
            # the *handing over* happens here; the callback is contractually
            # non-blocking (see the docstring), so this branch stays exactly as
            # expensive as the genuine one below. Nothing about ``existing``
            # other than its key crosses this line — the key never reaches the
            # caller, only the worker that resolves it.
            if on_existing_address is not None and existing is not None and existing.key:
                on_existing_address(existing.key)
            decoy = User(
                email=email,
                display_name=display_name,
                email_verified=skip_verification,
                created_at=datetime.now(UTC),
            )
            decoy.key = decoy_document_key()
            return self._to_profile(decoy)

        # Create user
        verification_token = None if skip_verification else secrets.token_urlsafe(32)
        user = User(
            email=email,
            display_name=display_name,
            password_hash=self._password_engine.hash_password(password),
            email_verified=skip_verification,
            email_verification_token=verification_token,
            email_verification_expires=(None if skip_verification else datetime.now(UTC) + _VERIFICATION_TOKEN_TTL),
        )
        created = self._user_repo.create(user)

        # Create local auth provider record
        if created.key:
            provider = AuthProvider(
                user_key=created.key,
                provider=AuthProviderType.LOCAL,
                provider_user_id=created.key,
                provider_email=email,
                linked_at=datetime.now(UTC),
            )
            self._auth_provider_repo.create(provider)

        # Create personal tenant
        if self._tenant_service and created.key:
            self._tenant_service.create_personal_tenant(created.key, display_name)

        # Send verification email (only when required)
        if self._require_email_verification and verification_token:
            self._deliver_mail(
                "verification",
                lambda: self._email_service.send_verification_email(
                    to_email=email,
                    token=verification_token,
                    frontend_url=self._frontend_url,
                ),
                defer_mail,
            )

        logger.info("user_registered", email_sha256=email_digest(email), verified=skip_verification)
        return self._to_profile(created)

    # ── Login ───────────────────────────────────────────────────────────

    def login_local(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
        remember_me: bool = False,
        *,
        defer_mail: MailDeferrer | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Returns (token_pair, raw_refresh_token, is_persistent).

        Args:
            defer_mail: Runs the fresh verification link of an
                ``EMAIL_NOT_VERIFIED`` refusal after the response (#2046); see
                :meth:`_deliver_mail`. ``None`` sends inline, still without
                letting a failure out. The caller must hand the refusal back as
                a *returned* response for a deferred send to run at all —
                FastAPI drops background tasks when the handler raises.

        Raises:
            EmailNotVerifiedError: The password was correct, but the address is
                not verified. Within the account's budget a fresh link has been
                handed to ``defer_mail`` before this is raised.
        """
        user = self._user_repo.get_by_email(email)
        if user is None:
            self._reject_unknown_account(email, password)

        # Check lockout
        if not self._throttle_engine.check_allowed(user.failed_login_attempts, user.locked_until):
            minutes = self._throttle_engine.get_lockout_minutes(user.locked_until)
            raise AccountLockedError(minutes)

        # Verify password
        if not user.password_hash or not self._password_engine.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            user.locked_until = self._throttle_engine.calculate_lockout(user.failed_login_attempts)
            if user.key:
                # Named fields, not a full-model write-back: this request's stale
                # snapshot never reaches the document, so a profile edit saved in
                # between is not carried away by it.
                #
                # It is **not** the base class's commuting partial update (#1525
                # SCR-003). `ArangoUserRepository` overrides `update_fields` into a
                # read-modify-write of the whole model (#1018), so two concurrent
                # calls touching *disjoint* fields still serialise on the full
                # document — the window is one repository call wide instead of one
                # request wide, not zero. This comment claimed the stronger property
                # the override stopped providing.
                self._user_repo.update_fields(
                    user.key,
                    {
                        "failed_login_attempts": user.failed_login_attempts,
                        "locked_until": _iso(user.locked_until),
                    },
                )
            raise UnauthorizedError("Invalid email or password.")

        # Check the account is not deactivated — #1528.
        #
        # **After the password, not before it.** The issue proposed placing this
        # right after the lookup. That would answer "User account is inactive."
        # to an anonymous caller who supplies nothing but an address and any
        # password, which is precisely the account-enumeration oracle
        # `_reject_unknown_account` (SEC-H-010) was built to close: today an
        # address with no account, an address with a wrong password and an
        # address belonging to a suspended account are one answer, and a check
        # ahead of the hash comparison would split the third one out.
        #
        # The four paths this gate is copied from all sit *after* their
        # credential has been accepted — `refresh_tokens` after the stored
        # refresh token matched, OAuth after the code exchange, the API key after
        # its hash matched, the pairing redeem after the code matched. Here that
        # is this position, and not the one the issue suggested.
        #
        # Also before the success write-back below: a refused login must not
        # reset the lockout counter or move `last_login_at`.
        if not user.is_active:
            # Logged, because this branch is otherwise silent (SCR-004): the
            # password was CORRECT, so no lockout counter moves and no failure
            # line is written, and whoever holds the credential of a suspended
            # account can repeat this indefinitely without leaving a trace. The
            # weaker case — an address with no account — is already logged.
            # Digest, never the address: the caller is unauthenticated and the
            # address may belong to a third party (NFR-011).
            logger.info("login_refused_inactive_account", email_sha256=email_digest(email))
            raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)

        # Check email verification (only when required)
        if self._require_email_verification and not user.email_verified:
            # #2046 — the caller has just proven the password, so this refusal
            # issues the fresh link itself: the anonymous resend's per-address
            # budget can be spent by anyone who knows the address, this one only
            # by whoever holds the password. No new oracle — the refusal is
            # already distinct from the wrong-password answer, its body does not
            # change, and the work runs after the response.
            #
            # The reservation sits in this method's own body, before the send:
            # ``test_anonymous_mail_routes_bound_the_recipient`` reads it here.
            if user.key is not None and self._needs_verification_mail(user):
                reserved = self._verification_resend_proven_store.reserve_attempt(
                    _VERIFICATION_RESEND_PROVEN_SUBJECT + user.key
                )
                if reserved <= MAX_PROVEN_VERIFICATION_RESENDS_PER_WINDOW:
                    self._deliver_mail(
                        "verification_resend_proven", partial(self._send_proven_verification_link, user.key), defer_mail
                    )
            raise EmailNotVerifiedError()

        # Success: reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        if user.key:
            # Named fields (see the failure branch above): a concurrent login used to
            # write its stale full user snapshot back and silently revert e.g. a
            # display-name change saved moments earlier. Same caveat — this is not the
            # base class's commuting partial update, because `ArangoUserRepository`
            # overrides `update_fields` into a full-model read-modify-write (#1018,
            # #1525 SCR-003).
            self._user_repo.update_fields(
                user.key,
                {
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "last_login_at": _iso(user.last_login_at),
                },
            )

        return self._create_tokens(user, user_agent, ip_address, is_persistent=remember_me)

    def _reject_unknown_account(self, email: str, password: str) -> NoReturn:
        """Answer a login for an address that has no account — SEC-H-010.

        This branch used to be a bare ``raise UnauthorizedError``. The branch for
        an address that *does* exist checks the lockout first and answers
        **423 "Account temporarily locked. Try again in N minutes."** once the
        threshold is reached. So an unauthenticated caller learned whether an
        arbitrary address was registered by sending five wrong passwords and
        reading the status code — no password guess ever had to succeed.

        Closing that by dropping the 423 would take the diagnostic away from the
        legitimate user it was added for. Instead the non-existent address gets a
        counter of its own (``IUnknownAccountStore``) and this method runs the
        *same* ``LoginThrottleEngine`` decision the existing-account path runs, so
        both reach 423 after the same number of attempts, with the same remaining
        minutes in the message.

        Raises:
            AccountLockedError: 423, once the threshold is reached — identical to
                what a registered address answers under the same conditions.
            UnauthorizedError: 401 otherwise.
        """
        failed_attempts, locked_until = self._unknown_account_store.get_failure_state(email)

        if not self._throttle_engine.check_allowed(failed_attempts, locked_until):
            minutes = self._throttle_engine.get_lockout_minutes(locked_until)
            raise AccountLockedError(minutes)

        # Burn the same bcrypt round ``login_local`` spends verifying the
        # password of an address that does exist.
        # Without it the two branches stay distinguishable by a stopwatch even
        # though their responses have become identical: bcrypt dominates the
        # request by two orders of magnitude over everything else on this path.
        # The result is deliberately discarded — it can only ever be False.
        self._password_engine.verify_password(password, _decoy_password_hash(self._password_engine))

        failed_attempts += 1
        self._unknown_account_store.record_failure(
            email,
            failed_attempts,
            self._throttle_engine.calculate_lockout(failed_attempts),
        )
        logger.info(
            "login_unknown_account_attempt",
            email_sha256=email_digest(email),
            failed_attempts=failed_attempts,
        )
        raise UnauthorizedError("Invalid email or password.")

    # ── Token refresh ───────────────────────────────────────────────────

    def refresh_tokens(
        self,
        raw_refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Rotate refresh token. Returns (new_token_pair, new_raw_refresh_token, is_persistent)."""
        token_hash = self._token_engine.hash_token(raw_refresh_token)
        stored = self._refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenError("refresh token")

        # Check expiry
        if stored.expires_at < datetime.now(UTC):
            if stored.key:
                self._refresh_token_repo.revoke(stored.key)
            raise InvalidTokenError("refresh token")

        # Preserve persistence flag from old token
        is_persistent = stored.is_persistent
        # …and the device label with it (#1118). Rotation replaces the session
        # document, so a label that is not carried over survives exactly one
        # refresh: the paired phone would silently turn back into an anonymous
        # user-agent row in the session list, which is the visibility this
        # feature exists to provide.
        device_name = stored.device_name

        # Revoke old token (rotation)
        if stored.key:
            self._refresh_token_repo.revoke(stored.key)

        # Load user
        user = self._user_repo.get_by_key(stored.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)

        return self._create_tokens(
            user,
            user_agent,
            ip_address,
            is_persistent=is_persistent,
            device_name=device_name,
        )

    # ── Email verification ──────────────────────────────────────────────

    def verify_email(self, token: str) -> UserProfile:
        user = self._user_repo.get_by_email_verification_token(token)
        if user is None:
            raise InvalidTokenError("verification token")

        # Check expiry
        if user.email_verification_expires and user.email_verification_expires < datetime.now(UTC):
            raise InvalidTokenError("verification token")

        confirmed_at = datetime.now(UTC)
        user.email_verified = True
        user.email_confirmed_at = confirmed_at
        user.email_verification_token = None
        user.email_verification_expires = None
        if user.key:
            updated = self._user_repo.update_fields(
                user.key,
                {
                    "email_verified": True,
                    "email_confirmed_at": confirmed_at,
                    "email_verification_token": None,
                    "email_verification_expires": None,
                },
            )
            logger.info("email_verified", email_sha256=email_digest(user.email))
            return self._to_profile(updated)
        raise InvalidTokenError("verification token")

    def resend_verification_email(self, email: str, *, defer_mail: MailDeferrer | None = None) -> None:
        """Issue a fresh verification link to ``email`` if it still needs one (REQ-023 §3.2b, #2037).

        Anonymous and enumeration-safe: the caller learns nothing from this
        method — it returns nothing and raises nothing, whatever the address. The
        request path does the **same work for every address**: one reservation
        against the per-address budget, then (inside the budget) handing one
        deferred call to ``defer_mail``. The account lookup, the token write and
        the mail all run in that call, after the response has been written, so
        neither a database round trip that only a known address would cause nor a
        delivery failure can be read off the answer or its duration (#1890 shape,
        one step further than the password reset, whose lookup still runs inline).

        Nothing is sent, and nothing is reserved, while
        ``require_email_verification`` is off: there is no gate to get past.

        In the deferred half (:meth:`_send_fresh_verification_link`) a mail goes
        out only to an account that needs it —
        exists, is active, is not yet verified, may sign in interactively (not a
        service account, #1559) and holds a local password (a federated-only
        account signs in at its provider and is never asked for this). Each send
        writes a **new** single-use token with a fresh 24-hour expiry, which
        overwrites — and so invalidates — every link mailed before it.

        Args:
            email: Submitted address.
            defer_mail: Runs the deferred call after the response (#1890); see
                :meth:`_deliver_mail`. ``None`` runs it inline, still without
                letting a failure out.
        """
        if not self._require_email_verification:
            return

        # Counted before anything is known about the address, for every address
        # alike: the budget is a property of the submitted string, so reaching it
        # says nothing about whether an account stands behind it. Silent on
        # purpose — no log line here, so the request path stays one store call.
        reserved = self._verification_resend_store.reserve_attempt(_VERIFICATION_RESEND_SUBJECT + email.strip().lower())
        if reserved > MAX_VERIFICATION_RESENDS_PER_WINDOW:
            return

        # A bound method through ``partial`` rather than a closure: the deferred
        # work stays a typed call the write-route detector can follow.
        self._deliver_mail("verification_resend", partial(self._send_fresh_verification_link, email), defer_mail)

    def _send_fresh_verification_link(self, email: str) -> None:
        """The deferred half of :meth:`resend_verification_email` — runs after the response.

        Writes a new token over the stored one before mailing it, so every link
        sent earlier stops working the moment this one is issued.
        """
        user: User | None = self._user_repo.get_by_email(email)
        if user is None or not self._needs_verification_mail(user):
            return
        self._issue_verification_link(user)

    def _send_proven_verification_link(self, user_key: UserKey) -> None:
        """The deferred half of the ``EMAIL_NOT_VERIFIED`` refusal (#2046) — runs after the response.

        Re-reads the account by key rather than using the snapshot taken at
        login: between the response and this call the address may have been
        verified, the account deactivated or deleted, and none of those may still
        get a token written or a mail sent. Same re-check as the anonymous path.
        """
        user: User | None = self._user_repo.get_by_key(user_key)
        if user is None or not self._needs_verification_mail(user):
            return
        self._issue_verification_link(user)

    def _issue_verification_link(self, user: User) -> None:
        """Write a new verification token for ``user`` and mail it to the stored address (#2037, #2046).

        One unit, so the token write and the mail are deferred together: a link
        that is written but never mailed would only invalidate the previous one.
        The recipient is ``user.email`` — the stored spelling, never what a
        caller typed.
        """
        if user.key is None:
            return
        token = token_urlsafe(32)
        self._user_repo.update_fields(
            user.key,
            {
                "email_verification_token": token,
                "email_verification_expires": _iso(now_utc() + _VERIFICATION_TOKEN_TTL),
            },
        )
        self._email_service.send_verification_email(
            to_email=user.email,
            token=token,
            frontend_url=self._frontend_url,
        )

    @staticmethod
    def _needs_verification_mail(user: User) -> bool:
        """Whether a verification link is what ``user`` still needs: a sign-in (#2037) or a proof (#1948).

        An account registered while verification was off is ``email_verified`` yet
        carries no ``email_confirmed_at``: it signs in, but no mail goes to the
        address until the link has been followed.
        """
        return (
            user.is_active
            and (not user.email_verified or user.email_confirmed_at is None)
            and bool(user.password_hash)
            and allows_interactive_auth(user)
            and not is_tombstone_email(user.email)
        )

    # ── Password reset ──────────────────────────────────────────────────

    def request_password_reset(
        self, email: str, *, client_ip: str | None, defer_mail: MailDeferrer | None = None
    ) -> None:
        """Always succeeds (no email enumeration).

        The token write and the mail go through :meth:`_deliver_mail`: neither a
        failing adapter or database nor the time they take may answer a known
        address differently from an unknown one (#1890).

        Two-stage budget (#2043, #2059), both reserved before anything is looked
        up, for an unknown address exactly like for a registered one:

        1. per address **and** source (*client_ip*):
           :data:`MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW`. A source that keeps
           asking for someone else's address keeps only itself out.
        2. per address over all sources, counted only for requests stage 1
           admitted: :data:`MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW`.

        Past either the call returns without a lookup, a token or a mail — and
        without any other visible difference. The request that first crosses a
        stage logs ``password_reset_budget_exhausted`` with the stage and a keyed
        digest of the address, never the address or the source.

        Args:
            email: The address the caller submitted.
            client_ip: The resolved client address (``resolve_client_ip``);
                ``None`` counts under one shared "unknown" source.
            defer_mail: Runs the mail step after the response (the route passes
                ``BackgroundTasks.add_task``).
        """
        # Counted before anything is known about the address, for every address
        # alike, so reaching the budget says nothing about whether an account
        # stands behind it. Silent on purpose, like the resend budget. The address
        # is normalised here and not only by the store: the store strips the
        # whole subject, so whitespace between the prefix and the address would
        # survive it and buy a fresh budget for the same inbox.
        address = email.strip().lower()
        source = (client_ip or _UNKNOWN_SOURCE).strip().lower()
        per_source = self._password_reset_store.reserve_attempt(f"{_PASSWORD_RESET_SOURCE_SUBJECT}{address}|{source}")
        if per_source > MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW:
            _report_budget_crossing("address_source", address, per_source, MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW)
            return
        per_address = self._password_reset_store.reserve_attempt(_PASSWORD_RESET_SUBJECT + address)
        if per_address > MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW:
            _report_budget_crossing("address", address, per_address, MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW)
            return

        # Lookup, token write AND mail are deferred together, like the resend
        # (#2062): the request path does the two reservations and nothing else,
        # for every address and on either side of the budget. A lookup on the
        # request path made an answer inside the budget measurably slower than one
        # above it, and a token written inline would do database work only for a
        # known address (security review of #1890); a failing lookup or write is
        # caught by ``_deliver_mail`` instead of answering 5xx on one branch.
        def _issue_and_send() -> None:
            user = self._user_repo.get_by_email(email)
            if user is None:
                return  # Silent fail to prevent enumeration
            # A service account has no interactive credential to reset (#1559), and
            # minting a token for one would write reset state onto a machine
            # identity and mail a link to whatever address it carries. Refused the
            # same way the unknown address is — silently — because a distinct answer
            # would tell an anonymous caller which addresses belong to machine
            # accounts, the enumeration oracle SEC-H-009/SEC-H-010 exist to close.
            if not allows_interactive_auth(user):
                return
            token = secrets.token_urlsafe(32)
            expires = datetime.now(UTC) + timedelta(hours=1)
            if user.key:
                self._user_repo.update_fields(
                    user.key,
                    {"password_reset_token": token, "password_reset_expires": _iso(expires)},
                )
            # The stored spelling, never the typed one (#2060): the lookup matches
            # case-insensitively, and a mail server may not — a link for
            # ``Owner@d`` must not reach a different mailbox ``owner@d``.
            self._email_service.send_password_reset_email(
                to_email=user.email,
                token=token,
                frontend_url=self._frontend_url,
            )

        self._deliver_mail("password_reset", _issue_and_send, defer_mail)

    def _deliver_mail(self, kind: str, send: Callable[[], None], defer: MailDeferrer | None) -> None:
        """Run an anonymous-flow mail step so that neither its outcome nor its duration reaches the response (#1890).

        ``/auth/register`` and ``/auth/password-reset/request`` are anonymous and
        answer the same for a known and an unknown address (SEC-H-009/010). Only
        one branch sends, so a send that raises (SMTP outage; a Resend 429 an
        attacker can provoke) or merely takes a round trip would tell the caller
        which branch it hit. Hence:

        * the failure is caught here, whatever the adapter raises, and logged by
          type only — ``SMTPRecipientsRefused`` embeds the refused address in its
          text, so neither ``str(exc)`` nor the address may reach the log;
        * the API layer passes ``defer`` (``BackgroundTasks.add_task``), which runs
          the send after the response has been written.

        Not retried: the user asks again, and the request path has no durable
        outbox that would not put the token or the address in a second store.
        """

        def _run() -> None:
            try:
                send()
            except Exception as exc:  # noqa: BLE001 - a delivery failure must never reach the caller
                logger.error("auth_mail_send_failed", kind=kind, error_type=type(exc).__name__)

        if defer is None:
            _run()
        else:
            defer(_run)

    def reset_password(self, token: str, new_password: str) -> None:
        errors = self._password_engine.validate_password_policy(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        user = self._user_repo.get_by_password_reset_token(token)
        if user is None:
            raise InvalidTokenError("reset token")

        if user.password_reset_expires and user.password_reset_expires < datetime.now(UTC):
            raise InvalidTokenError("reset token")

        # The issuance path above can no longer hand a service account a token, so
        # reaching this needs one planted by a migration, a fixture, or an account
        # converted to ``service`` while a token was outstanding. This is the second
        # door into the same write and is gated on its own rather than on the
        # unreachability of the first (#1559).
        self._refuse_interactive_credential(user)

        user.password_hash = self._password_engine.hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.key:
            self._user_repo.update_fields(
                user.key,
                {
                    "password_hash": user.password_hash,
                    "password_reset_token": None,
                    "password_reset_expires": None,
                    "failed_login_attempts": 0,
                    "locked_until": None,
                },
            )
            # Revoke all sessions for security
            self._refresh_token_repo.revoke_all_for_user(user.key)
            # The reset proves the mailbox the account is registered under — the
            # owner taking it back. A pending e-mail change stops here (#1841).
            self._cancel_pending_email_changes(user.key, reason="password_reset")
            logger.info("password_reset", email_sha256=email_digest(user.email))

    # ── Logout ──────────────────────────────────────────────────────────

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = self._token_engine.hash_token(raw_refresh_token)
        stored = self._refresh_token_repo.get_by_hash(token_hash)
        if stored and stored.key:
            self._refresh_token_repo.revoke(stored.key)

    def logout_all(self, user_key: UserKey) -> int:
        """Revoke every session — and withdraw a pending e-mail change (#1841), the owner's other lever."""
        revoked = self._refresh_token_repo.revoke_all_for_user(user_key)
        self._cancel_pending_email_changes(user_key, reason="logout_all")
        return revoked

    def _address_held_for_revert(self, email: str) -> bool:
        """Whether *email* is the previous address of a confirmed change whose revert window is open (#1848)."""
        if self._email_change_repo is None:
            return False
        return self._email_change_repo.find_revert_reservation(email, datetime.now(UTC).isoformat()) is not None

    def _cancel_pending_email_changes(self, user_key: UserKey, *, reason: str) -> int:
        """Withdraw every pending e-mail change of the account (#1841); return how many.

        The notice the current address gets for an e-mail change tells the owner
        to reset the password. Until this existed the reset stopped nothing: the
        confirmation link is unauthenticated, so whoever read the new mailbox still
        moved the account after the owner had taken it back. Called by the three
        acts that prove the owner (or end every session): the password reset by
        mail, the password change behind the step-up, and signing out everywhere.
        A withdrawn request answers ``InvalidTokenError`` at confirmation, like an
        expired one.

        Without a wired repository (a service built outside the DI provider) there
        is nothing to withdraw from; ``get_auth_service`` always wires it.
        """
        if self._email_change_repo is None:
            return 0
        cancelled = 0
        for change in self._email_change_repo.list_pending_for_user(user_key):
            if change.key is None:
                continue
            change.status = "cancelled"
            self._email_change_repo.update(change.key, change)
            cancelled += 1
        if cancelled:
            logger.info("email_change_cancelled", subject=self._log_subject(user_key), count=cancelled, reason=reason)
        return cancelled

    # ── Provider linking ────────────────────────────────────────────────

    def list_providers(self, user_key: UserKey) -> list[AuthProviderInfo]:
        providers = self._auth_provider_repo.list_by_user(user_key)
        return [
            AuthProviderInfo(
                key=p.key or "",
                provider=p.provider,
                provider_email=p.provider_email,
                provider_display_name=p.provider_display_name,
                linked_at=p.linked_at,
                last_used_at=p.last_used_at,
            )
            for p in providers
        ]

    def unlink_provider(
        self,
        user_key: UserKey,
        provider_key: str,
        *,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> None:
        """Remove one sign-in method of the account, behind the step-up (#1847).

        The checks that read only the account's own links run first, so a request
        that would be refused anyway does not spend the mailed code or an attempt.
        """
        providers = self._auth_provider_repo.list_by_user(user_key)
        if len(providers) <= 1:
            raise ValidationError("Cannot unlink the last authentication provider.")

        target = next((p for p in providers if p.key == provider_key), None)
        if target is None:
            raise NotFoundError("AuthProvider", provider_key)
        if target.user_key != user_key:
            raise ValidationError("Provider does not belong to this user.")

        self._verify_credential_step_up(
            user_key,
            action="provider_unlink",
            # #1884 — a factor obtained to unlink this provider confirms this one only.
            target=provider_key,
            current_password=current_password,
            step_up_code=step_up_code,
            step_up_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        self._auth_provider_repo.delete(provider_key)

    def _verify_credential_step_up(
        self,
        user_key: UserKey,
        *,
        action: StepUpAction,
        target: str | None,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> None:
        """The shared step-up in front of minting or removing a sign-in credential (#1847).

        A stolen session — or a leaked key, which ``get_current_user`` resolves to
        its owner — minted an API key or a pairing code that outlives the owner's
        password change, or removed a sign-in method, on nothing but the session.
        The verifier refuses an API-key request and a service account (403), wants
        the current password or, for an account without one, the fresh
        re-authentication or the mailed code (401), and throttles in the one
        budget of every step-up (429).
        """
        user = self._user_repo.get_or_raise(user_key)
        self._step_up_verifier.verify(
            user,
            action=action,
            target=target,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

    # ── Sessions ────────────────────────────────────────────────────────

    def list_sessions(self, user_key: UserKey, current_token_hash: str | None = None) -> list[SessionInfo]:
        tokens = self._refresh_token_repo.list_active_for_user(user_key)
        return [
            SessionInfo(
                key=t.key or "",
                user_agent=t.user_agent,
                device_name=t.device_name,
                ip_address=t.ip_address,
                created_at=t.created_at,
                expires_at=t.expires_at,
                is_current=t.token_hash == current_token_hash if current_token_hash else False,
                is_persistent=t.is_persistent,
            )
            for t in tokens
        ]

    def revoke_session(self, user_key: UserKey, session_key: str) -> None:
        tokens = self._refresh_token_repo.list_active_for_user(user_key)
        target = next((t for t in tokens if t.key == session_key), None)
        if target is None:
            raise NotFoundError("Session", session_key)
        self._refresh_token_repo.revoke(session_key)

    # ── Change password ─────────────────────────────────────────────────

    def change_password(
        self,
        user_key: UserKey,
        current_password: str | None,
        new_password: str,
        *,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> None:
        user = self._user_repo.get_or_raise(user_key)

        # REQ-023: a service account is API-key-only (#1559). It reaches this method
        # because ``FullAuthProvider.resolve_user`` resolves a ``kp_`` bearer through
        # ``authenticate_api_key`` and ``POST /users/me/password`` depends on
        # ``get_current_user`` alone — and it then walks straight through the SSO
        # branch below, which waives ``current_password`` for any account with no
        # hash. Refused before the policy check, so a service account cannot even
        # probe the password policy from here.
        self._refuse_interactive_credential(user)

        # The policy is stateless, so it runs before the step-up: a too-weak new
        # password must not spend the mailed code or a throttled attempt
        # (/code-review of #1862).
        errors = self._password_engine.validate_password_policy(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        # The current password is a step-up like any other (#1816): the shared
        # verifier refuses an API-key request (a key is not a person present),
        # throttles the check per account and address (429 ``STEP_UP_LOCKED``) and
        # counts into the same budget as account erasure and tenant deletion — one
        # budget per account, not one per route. An SSO-only user (no
        # password_hash) setting a first password confirms with the one-time code
        # mailed to it (#1815); until then it passed on nothing at all.
        try:
            self._step_up_verifier.verify(
                user,
                action="password_change",
                target=None,
                echo_ok=None,
                password=current_password,
                code=step_up_code,
                reauth_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )
        except UnauthorizedError as exc:
            message = "Current password is incorrect." if user.password_hash else exc.message
            raise UnauthorizedError(message) from exc

        user.password_hash = self._password_engine.hash_password(new_password)
        # A password change also consumes any outstanding reset token (SEC-011).
        # Without this, a reset token requested before the change stays valid for
        # its full hour, so whoever holds it — the very reason the owner rotated
        # the password — can take the account back over afterwards. Mirrors what
        # ``reset_password`` already clears, and relies on ``update_fields``
        # persisting an explicit ``None`` (``keep_none=True``).
        user.password_reset_token = None
        user.password_reset_expires = None
        self._user_repo.update_fields(
            user_key,
            {
                "password_hash": user.password_hash,
                "password_reset_token": None,
                "password_reset_expires": None,
            },
        )

        # If this is the first local password, create LOCAL auth provider
        if not self._has_local_provider(user_key):
            provider = AuthProvider(
                user_key=user_key,
                provider=AuthProviderType.LOCAL,
                provider_user_id=user_key,
                provider_email=user.email,
                linked_at=datetime.now(UTC),
            )
            self._auth_provider_repo.create(provider)

        self._refresh_token_repo.revoke_all_for_user(user_key)
        # Behind the step-up, so it is the owner's act; a pending e-mail change stops (#1841).
        self._cancel_pending_email_changes(user_key, reason="password_change")

    def send_step_up_code(
        self,
        user_key: UserKey,
        *,
        action: StepUpAction,
        target: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> datetime:
        """Mail the one-time step-up code to an account without a local password (#1815).

        The code confirms that account's irreversible acts and credential changes
        (erasure, tenant deletion, first password, e-mail change). Everything that
        decides whether a code may be issued — a person's session (403), the step-up
        lock (429), an account that has a password (422) — is the verifier's; this
        method only delivers it. The code goes to the account's own address and
        never into a response or a log line.

        Refused in light mode (403), like the account erasure there: every caller
        is the one seeded system account, whose address is public in the seed, and
        nothing a code could confirm is open to it anyway.

        Returns:
            When the code expires (UTC).
        """
        if self._light_mode:
            raise ForbiddenError("A light-mode installation has no personal account to confirm.")
        user = self._user_repo.get_or_raise(user_key)
        code, expires_at = self._step_up_verifier.issue_code(
            user,
            action=action,
            target=target,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        try:
            self._email_service.send_step_up_code_email(
                to_email=user.email,
                display_name=user.display_name,
                code=code,
                purpose=CODE_PURPOSES[action],
            )
        except (EmailUndeliverableError, NotImplementedError, OSError) as exc:
            # /code-review of #1862: a code nobody receives must not be answered with
            # "sent". OSError covers smtplib.SMTPException and connection failures;
            # the Resend adapter raises an EmailUndeliverableError (#1888 review).
            # The code and its issuance are taken back, so the retry after the
            # operator fixed the mail setup is not held by the wait or the budget.
            self._step_up_verifier.withdraw_code(user)
            logger.warning(
                "step_up.code_undeliverable", subject=self._log_subject(user_key), error_type=type(exc).__name__
            )
            raise StepUpCodeUndeliverableError() from exc
        return expires_at

    def _has_local_provider(self, user_key: UserKey) -> bool:
        providers = self._auth_provider_repo.list_by_user(user_key)
        return any(p.provider == AuthProviderType.LOCAL for p in providers)

    # ── OAuth/OIDC ───────────────────────────────────────────────────

    def initiate_oauth(
        self,
        provider_slug: str,
        redirect_uri: str,
    ) -> OAuthRedirect:
        """Build authorization URL and store state in Redis."""
        if not self._oauth_engine or not self._oauth_state_store or not self._oidc_config_repo:
            raise ValidationError("OAuth is not configured.")

        config = self._oidc_config_repo.get_by_slug(provider_slug)
        if config is None or not config.enabled:
            raise NotFoundError("OidcProviderConfig", provider_slug)

        redirect = self._build_redirect(config, redirect_uri)

        # The state keeps the redirect URI so the code exchange repeats it exactly
        # (RFC 6749 §4.1.3, #1865) — as the step-up request does.
        self._oauth_state_store.save_state(
            redirect.state,
            {
                "code_verifier": redirect.code_verifier,
                "nonce": redirect.nonce,
                "provider_slug": provider_slug,
                "redirect_uri": redirect_uri,
            },
        )

        return redirect

    def _require_configuration_unchanged(self, config: OidcProviderConfig) -> None:
        """Refuse when the configuration a login loaded is no longer the enabled one at its slug (#1987).

        The callback loads the configuration, exchanges the code (up to the HTTP timeout) and
        verifies the token, and only then writes. In between an admin can delete the provider and
        create another under the same slug — possibly at another IdP — or switch it off or repoint
        it; a write made on the strength of the old one would land under the new. The same ``_key``,
        still enabled, at the same issuer: nothing moved. Anything else is the generic refusal.
        """
        assert self._oidc_config_repo is not None  # noqa: S101 — checked by the caller
        current = self._oidc_config_repo.get_by_slug(config.slug)
        if (
            current is None
            or not current.enabled
            or current.key != config.key
            or current.issuer_url != config.issuer_url
        ):
            logger.info("oauth_login_refused", provider=config.slug, reason="configuration_changed")
            raise ValidationError("OAuth sign-in could not be completed.")

    def _build_redirect(
        self, config: OidcProviderConfig, redirect_uri: str, *, fresh_login: bool = False
    ) -> OAuthRedirect:
        """The authorization request of *config*; an unusable endpoint is a 422, not a 500 (#1987)."""
        assert self._oauth_engine is not None  # noqa: S101 — the callers checked
        try:
            return self._oauth_engine.build_authorization_url(config, redirect_uri, fresh_login=fresh_login)
        except ValueError as exc:
            logger.warning("oauth_endpoint_refused", provider=config.slug, reason=_refusal_reason(exc))
            raise ValidationError("This sign-in provider is not configured correctly.") from exc

    def complete_oauth(
        self,
        provider_slug: str,
        code: str,
        state: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Exchange code, find/create user, return tokens.

        A state issued for a step-up re-authentication (#1815) is refused here: the
        login entry never turns a step-up callback into a session.
        """
        state_data = self._take_oauth_state(provider_slug, state)
        if state_data.get("purpose") == _STEP_UP_PURPOSE:
            raise InvalidTokenError("OAuth state")
        return self._complete_login(provider_slug, code, state_data, user_agent, ip_address)

    def handle_oauth_callback(
        self,
        provider_slug: str,
        code: str,
        state: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> OAuthCallbackOutcome:
        """The provider callback: a sign-in, or the fresh re-authentication of a step-up (#1815).

        The state is taken once; its ``purpose`` decides. A ``step_up`` state
        never reaches :meth:`_complete_login` — no session, no refresh token, no
        ``last_login_at``, no ``last_used_at``.
        """
        state_data = self._take_oauth_state(provider_slug, state)
        if state_data.get("purpose") == _STEP_UP_PURPOSE:
            client_nonce = state_data.get("client_nonce")
            try:
                token, action = self.complete_step_up_reauth(provider_slug, code, state_data)
            except StepUpReauthFailedError as exc:
                exc.client_nonce = client_nonce
                raise
            return OAuthCallbackOutcome(step_up_token=token, step_up_action=action, step_up_client_nonce=client_nonce)
        token_pair, raw_refresh, is_persistent = self._complete_login(
            provider_slug, code, state_data, user_agent, ip_address
        )
        return OAuthCallbackOutcome(token_pair=token_pair, raw_refresh=raw_refresh, is_persistent=is_persistent)

    def abandon_oauth_state(self, state: str | None) -> dict | None:
        """Take (and so end) a state the provider answered with an error; return what it was for."""
        if not state or not self._oauth_state_store:
            return None
        return self._oauth_state_store.get_and_delete(state)

    def _take_oauth_state(self, provider_slug: str, state: str) -> dict:
        if not self._oauth_engine or not self._oauth_state_store or not self._oidc_config_repo:
            raise ValidationError("OAuth is not configured.")
        state_data = self._oauth_state_store.get_and_delete(state)
        if state_data is None:
            raise InvalidTokenError("OAuth state")
        if state_data.get("provider_slug") != provider_slug:
            raise InvalidTokenError("OAuth state")
        return state_data

    # ── Step-up: fresh re-authentication at the identity provider (#1815) ──

    def start_step_up_reauth(
        self,
        user_key: UserKey,
        *,
        action: StepUpAction,
        target: str | None,
        provider_key: str | None,
        client_nonce: str | None,
        callback_url: Callable[[str], str],
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> str:
        """Answer the authorization URL of a fresh sign-in at a linked provider (#1815).

        Refused like any step-up for an API key or a service account (403) and while
        the step-up is locked (429); an account with a local password confirms with
        it (422). The provider is *provider_key* — a link of this account — or the
        first link whose configuration supports a fresh re-authentication
        (:func:`supports_fresh_reauth`); none such is 422 (the account confirms with
        the e-mailed code instead).

        The request is the login one (PKCE, state, nonce, the same callback URL
        from *callback_url*) plus ``prompt=login`` and ``max_age=0``; the state entry
        additionally names the purpose, the account, the act and its target (#1884 —
        admitted by the verifier: named for a targeted act, and one the requester may
        act on), and keeps the
        redirect URI so the code exchange repeats it exactly. *client_nonce* — a
        value the starting page generated — rides along unchanged and comes back
        beside the token, so that page can refuse a token it did not ask for
        (review SEC-005: a crafted callback link could otherwise plant one).
        """
        user = self._user_repo.get_or_raise(user_key)
        bound_target = self._step_up_verifier.admit_reauth(
            user,
            action=action,
            target=target,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        if not self._oauth_engine or not self._oauth_state_store or self._reauth_policy is None:
            raise ValidationError("Sign-in providers are not configured.")
        links = self._reauth_policy.reauth_links(user_key)
        if provider_key is not None:
            links = [(row, config) for row, config in links if row.key == provider_key]
        if not links:
            raise StepUpReauthUnavailableError()
        _row, config = links[0]

        redirect_uri = callback_url(config.slug)
        redirect = self._build_redirect(config, redirect_uri, fresh_login=True)
        self._oauth_state_store.save_state(
            redirect.state,
            {
                "code_verifier": redirect.code_verifier,
                "nonce": redirect.nonce,
                "provider_slug": config.slug,
                "purpose": _STEP_UP_PURPOSE,
                "user_key": user_key,
                "action": action,
                # #1884 — the target the token will be bound to, admitted above.
                "target": bound_target,
                "redirect_uri": redirect_uri,
                "client_nonce": client_nonce,
            },
        )
        logger.info("step_up.reauth_started", action=action, provider=config.slug, subject=self._log_subject(user_key))
        return redirect.authorization_url

    def complete_step_up_reauth(self, provider_slug: str, code: str, state_data: dict) -> tuple[str, str]:
        """Check the provider's answer proves a fresh sign-in of the account; mint the step-up token (#1815).

        ID token checks (OIDC Core 3.1.3.7 plus the step-up rule) are
        :meth:`OAuthEngine.validate_fresh_reauth_claims`; here: the provider still
        supports it, the account is still an active person, and ``sub`` is a
        provider link **of this account** of this provider's type.

        **No signature check.** The ID token comes straight from the provider's
        token endpoint, over TLS, in the exchange this server authenticated with
        its client secret and the PKCE verifier; OIDC Core 3.1.3.7 step 6 allows
        TLS server validation in place of the signature in exactly that case. A
        JWKS check would add a key fetch and cache per provider for no gain against
        an attacker who cannot sit in that TLS session.

        Returns:
            ``(step_up_token, action)``.

        Raises:
            StepUpReauthFailedError: ``reason="stale"`` for a sign-in older than
                five minutes, ``"failed"`` for anything else. Nothing is written.
        """
        action = str(state_data.get("action", ""))
        user_key = str(state_data.get("user_key", ""))
        try:
            config = self._oidc_config_repo.get_by_slug(provider_slug) if self._oidc_config_repo else None
            if config is None or not supports_fresh_reauth(config) or self._oauth_engine is None:
                raise FreshReauthRejectedError("failed", "the provider cannot re-authenticate")
            client_secret = config.client_secret_encrypted
            if self._encryption_engine:
                client_secret = self._encryption_engine.decrypt(client_secret)
            token_response = self._oauth_engine.exchange_code_for_tokens(
                config, code, state_data["code_verifier"], state_data["redirect_uri"], client_secret
            )
            claims = self._oauth_engine.id_token_claims(token_response)
            sub = self._oauth_engine.validate_fresh_reauth_claims(
                claims, config=config, nonce=str(state_data.get("nonce", "")), now=datetime.now(UTC)
            )
            user = self._user_repo.get_by_key(user_key)
            if user is None or not user.is_active or not allows_interactive_auth(user):
                raise FreshReauthRejectedError("failed", "the account is gone or not a person")
            # The link must be one of this account's, of *this* configuration (review
            # SEC-001) — the same rule the start chose it by — and, where the link
            # recorded its issuer, from that issuer.
            issuer = str(claims.get("iss", "")).rstrip("/")
            links = self._reauth_policy.reauth_links(user_key) if self._reauth_policy is not None else []
            if not any(
                link_config.slug == config.slug
                and hmac.compare_digest(row.provider_user_id, sub)
                and (row.issuer is None or OAuthEngine.same_issuer(row.issuer, issuer))
                for row, link_config in links
            ):
                raise FreshReauthRejectedError("failed", "sub is no provider link of this account at this provider")
        except FreshReauthRejectedError as exc:
            logger.info(
                "step_up.reauth_refused",
                provider=provider_slug,
                action=action,
                reason=exc.reason,
                detail=exc.detail,
                subject=self._log_subject(user_key),
            )
            raise StepUpReauthFailedError(exc.reason, action=action or None) from exc
        except Exception as exc:  # noqa: BLE001 - a provider or decoding failure is a failed step-up, never a 500
            logger.info(
                "step_up.reauth_refused",
                provider=provider_slug,
                action=action,
                reason="failed",
                error_type=type(exc).__name__,
                subject=self._log_subject(user_key),
            )
            raise StepUpReauthFailedError("failed", action=action or None) from exc

        target = str(state_data.get("target") or "") or None
        if (action in TARGETED_ACTIONS) != (target is not None):
            # A state written before #1884 names no target for a targeted act: the
            # re-authentication is refused rather than minting an unbound token.
            logger.info(
                "step_up.reauth_refused",
                provider=provider_slug,
                action=action,
                reason="failed",
                detail="the state names no target for a targeted act",
                subject=self._log_subject(user_key),
            )
            raise StepUpReauthFailedError("failed", action=action or None)
        token = self._step_up_verifier.issue_reauth_token(
            user,
            action=action,  # type: ignore[arg-type]
            target=target,
        )
        return token, action

    def _complete_login(
        self,
        provider_slug: str,
        code: str,
        state_data: dict,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[TokenPair, str, bool]:
        """The sign-in half of the callback: exchange, find or create the account, issue a session."""
        if not self._oauth_engine or not self._oidc_config_repo:
            raise ValidationError("OAuth is not configured.")
        # The exchange repeats the authorization request's redirect URI (#1865). A
        # state that does not carry it — written before #1865 — cannot say which one
        # that was; it is refused rather than guessed.
        redirect_uri = state_data.get("redirect_uri")
        if not isinstance(redirect_uri, str) or not redirect_uri:
            raise InvalidTokenError("OAuth state")
        config = self._oidc_config_repo.get_by_slug(provider_slug)
        if config is None or not config.enabled:
            raise NotFoundError("OidcProviderConfig", provider_slug)

        # Decrypt client secret
        client_secret = config.client_secret_encrypted
        if self._encryption_engine:
            client_secret = self._encryption_engine.decrypt(client_secret)

        # Exchange code for tokens
        try:
            token_response = self._oauth_engine.exchange_code_for_tokens(
                config,
                code,
                state_data["code_verifier"],
                redirect_uri,
                client_secret,
            )
        except ValueError as exc:
            # A stored token endpoint that is not https (#1987): nothing was sent to it.
            logger.warning("oauth_endpoint_refused", provider=provider_slug, reason=_refusal_reason(exc))
            raise ValidationError("OAuth sign-in could not be completed.") from exc

        access_token = token_response.get("access_token", "")
        # The ID token's signature, ``iss``, ``aud``, ``nonce`` and ``exp``, and the
        # subject, are checked before an identity is trusted (#1936). Every refusal
        # is one generic error to the caller — which check failed is not an oracle —
        # and one value-free line here.
        try:
            oauth_user = self._oauth_engine.authenticate_login(
                config,
                token_response,
                access_token,
                nonce=str(state_data.get("nonce", "")),
                now=datetime.now(UTC),
            )
        except LoginIdentityRejectedError as exc:
            logger.info("oauth_login_refused", provider=provider_slug, reason=exc.reason)
            raise ValidationError("OAuth sign-in could not be completed.") from exc
        except ValueError as exc:
            # A stored userinfo endpoint that is not https (#1987), or a response that
            # carries no identity: refused like any other failed check.
            logger.warning("oauth_endpoint_refused", provider=provider_slug, reason=_refusal_reason(exc))
            raise ValidationError("OAuth sign-in could not be completed.") from exc

        # The configuration was loaded before the exchange, which can take its full timeout.
        # Whatever is written from here on is written against it — so it must still be the
        # configuration at that slug (#1987).
        self._require_configuration_unchanged(config)

        # Find the existing link — of *this* configuration (#1869).
        issuer = _id_token_issuer(token_response)
        existing_provider = self._login_link(config, oauth_user, issuer)

        if existing_provider:
            # Existing link — login
            user = self._user_repo.get_by_key(existing_provider.user_key)
            if user is None or not user.is_active:
                raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)
            # Update last_used_at on provider. A link without a recorded issuer — one
            # v0064 bound, or one made without an ID token — records this sign-in's,
            # so a later repointing of the configuration at another IdP is refused
            # (/security review of #1869, SEC-001).
            existing_provider.last_used_at = datetime.now(UTC)
            if existing_provider.issuer is None and issuer:
                existing_provider.issuer = issuer
            if existing_provider.key:
                self._require_configuration_unchanged(config)
                self._auth_provider_repo.update(existing_provider.key, existing_provider)
        else:
            # No link — check if email matches existing user (auto-link)
            existing_user = self._user_repo.get_by_email(oauth_user.email)
            if existing_user:
                # The provider's own claim, not a literal (#1403). `None` — the
                # provider said nothing — refuses, by the operator decision
                # recorded on `should_auto_link`.
                if self._oauth_engine.should_auto_link(existing_user.email_verified, oauth_user.email_verified):
                    # The sibling branch above carries this check; this one never
                    # did (#1528 class sweep). A suspended account whose address
                    # a provider asserts as verified could therefore be logged
                    # into — and, worse, acquire a *new* provider link on the way
                    # in, so the refusal added here also has to run before
                    # `_create_oauth_provider`.
                    if not existing_user.is_active:
                        # Same silent-branch argument as in `login_local`
                        # (SCR-004); here the accepted credential is the
                        # provider's rather than a password.
                        logger.info(
                            "oauth_refused_inactive_account",
                            provider=provider_slug,
                            email_sha256=email_digest(oauth_user.email),
                        )
                        raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)
                    user = existing_user
                    # Create provider link
                    self._create_oauth_provider(user.key or "", oauth_user, token_response, config=config)
                else:
                    # Deliberately does not say WHICH side is unverified: the
                    # caller of this endpoint is not necessarily the owner of the
                    # local account, and "that address exists here and is
                    # verified" is an account-enumeration answer. The remedy is
                    # the same either way.
                    #
                    # And deliberately does not advise linking from the account
                    # settings, which the earlier wording did: there is no manual
                    # link, on either side. `api/endpoints/auth.ts` exports
                    # `unlinkProvider` and nothing that links, and the route that
                    # would have served one — `POST /users/me/providers/{slug}/link`
                    # — was removed with #1416 because it never had a consumer.
                    # Advice a reader cannot follow is worse than none — it sends
                    # them looking for a button that is not there.
                    #
                    # This branch is therefore the whole of the linking policy:
                    # a provider is linked on the automatic path or not at all.
                    raise OAuthAutoLinkRefusedError(
                        "This email cannot be linked automatically. Sign in with your password instead.",
                    )
            else:
                # New user — register via OAuth. Not onto an address held for the
                # revert of a confirmed e-mail change (/code-review of #1893).
                if self._address_held_for_revert(oauth_user.email):
                    raise OAuthAutoLinkRefusedError(
                        "This email cannot be used to create an account right now. Sign in with your password instead.",
                    )
                self._require_configuration_unchanged(config)
                user = self._register_oauth_user(oauth_user)
                self._create_oauth_provider(user.key or "", oauth_user, token_response, config=config)

        user.last_login_at = datetime.now(UTC)
        if user.key:
            self._user_repo.update_fields(user.key, {"last_login_at": _iso(user.last_login_at)})

        logger.info("oauth_login", provider=provider_slug, email_sha256=email_digest(oauth_user.email))
        return self._create_tokens(user, user_agent, ip_address, is_persistent=True)

    def _login_link(
        self, config: OidcProviderConfig, oauth_user: OAuthUserInfo, issuer: str | None
    ) -> AuthProvider | None:
        """The provider link a sign-in through *config* with this ``sub`` belongs to, if any (#1869).

        OIDC guarantees ``sub`` unique per issuer only, and every generic OIDC
        configuration stores its links under the one type ``oidc`` — so (type,
        ``sub``) is no identity: an identity at IdP A whose ``sub`` equals a
        victim's at IdP B would sign in as the victim. A link matches only when it
        records *this* configuration (``oidc_config_slug``) and — where it recorded
        the ID token's issuer — the sign-in's issuer is that one (the configuration
        may since point at another IdP).

        A link that records no configuration (made before #1815 SEC-001) matches
        nothing: migration v0064 bound every such link whose type had exactly one
        configuration when it ran, so one still unbound could belong to either of
        two — it is not guessed, and no later deletion of a configuration makes it
        look unambiguous (/security review of #1869, SEC-003). More than one account
        matching is ambiguous as well. "No link" falls through to the e-mail
        auto-link / registration path with its own checks — never to the owner of a
        colliding ``sub``.

        Raises:
            OAuthAutoLinkRefusedError: a link of this configuration and ``sub``
                exists but recorded another issuer. Refused here rather than
                answered "no link": the registration path would create the same
                (type, configuration, sub) again and fail on the unique index —
                after creating an account (/code-review of #1937).
        """
        candidates = self._auth_provider_repo.list_by_provider(oauth_user.provider, oauth_user.provider_user_id)
        of_slug = [row for row in candidates if row.oidc_config_slug == config.slug]
        # A link that recorded the configuration's key (#1987) belongs to THAT configuration. One
        # whose key is not this configuration's was written by a login that loaded a configuration
        # since deleted, under a slug since re-used: it is an orphan of the old one. It matches
        # nothing, and is removed — it would also collide on the (type, slug, sub) unique key with
        # the link this sign-in is about to make.
        of_config = []
        for row in of_slug:
            if config.key is not None and row.oidc_config_key not in (None, config.key):
                if row.key:
                    self._auth_provider_repo.delete(row.key)
                logger.warning("oauth_orphan_link_removed", provider=config.slug)
                continue
            of_config.append(row)
        bound = [row for row in of_config if row.issuer is None or OAuthEngine.same_issuer(row.issuer, issuer)]
        if len({row.user_key for row in bound}) == 1:
            return bound[0]
        if of_config:
            logger.warning("oauth_link_issuer_mismatch", provider=config.slug, links=len(of_config), matches=len(bound))
            raise OAuthAutoLinkRefusedError(
                "This sign-in does not match the account linked to this provider. Sign in with your password instead.",
            )
        return None

    def _register_oauth_user(self, oauth_user: OAuthUserInfo) -> User:
        """Create a new user from OAuth info (no password).

        **The provider's claim decides `email_verified`, not a literal (#1403).**
        This line read `email_verified=True  # OAuth emails are considered
        verified` — the same assumption the auto-link path was repaired for, one
        branch over, and the one the AST guard does not watch because it only
        follows `should_auto_link`.

        It matters because the two are connected: an account created here with
        `email_verified=True` from an address the provider never asserted then
        satisfies `existing_email_verified` for **every subsequent provider**.
        Refusing the auto-link while minting accounts that make the next one
        succeed would have fixed the symptom and kept the mechanism.

        `is True` and not a truthiness test: `None` means the provider said
        nothing, and under the decision recorded on `should_auto_link` silence is
        not an assertion.
        """

        user = User(
            email=oauth_user.email,
            display_name=oauth_user.display_name,
            email_verified=oauth_user.email_verified is True,
            # The provider's assertion is the proof (#1948); silence is not.
            email_confirmed_at=datetime.now(UTC) if oauth_user.email_verified is True else None,
            avatar_url=oauth_user.avatar_url,
        )
        created = self._user_repo.create(user)
        if self._tenant_service and created.key:
            self._tenant_service.create_personal_tenant(created.key, created.display_name)
        logger.info("oauth_user_registered", email_sha256=email_digest(oauth_user.email), provider=oauth_user.provider)
        return created

    def _create_oauth_provider(
        self,
        user_key: str,
        oauth_user: OAuthUserInfo,
        token_response: dict,
        *,
        config: OidcProviderConfig,
    ) -> AuthProvider:
        """Create an AuthProvider record for an OAuth login.

        Records the configuration and the ID token's issuer (#1815 review SEC-001),
        so a step-up re-authentication can send the link only to its own provider.
        """
        issuer = _id_token_issuer(token_response)
        # The last check before the write: the link is bound to this configuration's key, and the
        # slug is only its label (#1987).
        self._require_configuration_unchanged(config)

        encrypted_access = token_response.get("access_token", "")
        encrypted_refresh = token_response.get("refresh_token", "")
        if self._encryption_engine:
            if encrypted_access:
                encrypted_access = self._encryption_engine.encrypt(encrypted_access)
            if encrypted_refresh:
                encrypted_refresh = self._encryption_engine.encrypt(encrypted_refresh)

        provider = AuthProvider(
            user_key=user_key,
            provider=oauth_user.provider,
            provider_user_id=oauth_user.provider_user_id,
            oidc_config_slug=config.slug,
            oidc_config_key=config.key,
            issuer=issuer,
            provider_email=oauth_user.email,
            provider_display_name=oauth_user.display_name,
            avatar_url=oauth_user.avatar_url,
            access_token_encrypted=encrypted_access or None,
            refresh_token_encrypted=encrypted_refresh or None,
            last_used_at=datetime.now(UTC),
            linked_at=datetime.now(UTC),
        )
        return self._auth_provider_repo.create(provider)

    # ── M2M API Keys ─────────────────────────────────────────────────

    def create_api_key(
        self,
        user_key: UserKey,
        label: str,
        tenant_scope: str | None = None,
        *,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> ApiKeyCreated:
        """Mint an API key for the account, behind the step-up (#1847).

        A key is a credential that survives a password change and "sign out
        everywhere", so minting one is a credential change like the password
        itself: a person's session and the current password (or, without one,
        the fresh re-authentication or the mailed code). An API-key request is
        refused (403) — a key cannot mint a key.

        **Light mode** skips the step-up: every request there already is the one
        seeded system account, there is no person to confirm and no mailbox a
        code could reach, and the key grants nothing a request does not already
        have (REQ-033 §4.3 — it only makes MCP reachable).

        The step-up runs before the scope is resolved, so the scope check answers
        nothing to a caller who has not passed it.
        """
        if not self._api_key_repo:
            raise ValidationError("API keys are not configured.")

        if not self._light_mode:
            self._verify_credential_step_up(
                user_key,
                action="api_key_creation",
                target=None,
                current_password=current_password,
                step_up_code=step_up_code,
                step_up_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )

        # #1852: the scope is stored as the tenant's *key*, resolved here from the
        # slug or key the caller typed — never verbatim.
        tenant_scope = self._canonical_tenant_scope(user_key, tenant_scope)

        raw_key = f"{_API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        api_key = ApiKey(
            user_key=user_key,
            label=label,
            key_hash=key_hash,
            key_prefix=key_prefix,
            tenant_scope=tenant_scope,
        )
        created = self._api_key_repo.create(api_key)

        # Not the prefix: ``kp_`` plus five characters of the secret (#1828). The
        # record's own key correlates the line with the stored key.
        logger.info("api_key_created", subject=self._log_subject(user_key), label=label, api_key_id=created.key)
        return ApiKeyCreated(
            key=created.key or "",
            label=created.label,
            raw_key=raw_key,
            key_prefix=key_prefix,
            tenant_scope=tenant_scope,
            created_at=created.created_at,
        )

    def _canonical_tenant_scope(self, user_key: UserKey, requested: str | None) -> str | None:
        """Resolve a requested ``tenant_scope`` to the key of a tenant the caller is active in (#1852).

        Until #1852 the scope was stored as typed and matched on slug *or* key.
        A slug is a name, not an identity: renaming a tenant re-derives it and a
        deleted tenant's slug is issued again, so a slug-form scope re-bound to
        whichever tenant held the name, and the tenant erasure — which deletes
        keys whose ``tenant_scope`` equals the erased tenant's key — left it in
        place. Resolving at creation makes the stored scope the stable key.

        The caller may name the tenant by slug or by key. An unknown value, a
        tenant the caller holds no *active* membership in, and a tenant that is
        itself inactive are refused with one message, so the endpoint answers no
        "does this tenant exist?" question.
        """
        if requested is None or not requested.strip():
            return None
        refusal = ForbiddenError("tenant_scope must name a tenant you are an active member of.")
        if self._tenant_service is None:
            raise refusal
        value = requested.strip()
        # Keys and slugs are both plain tokens. Anything else (a ``/`` would make
        # the key lookup read a document *id* in another collection) is refused
        # before it reaches a lookup.
        if not _TENANT_REF.fullmatch(value):
            raise refusal
        tenant = None
        for lookup in (self._tenant_service.get_tenant, self._tenant_service.get_tenant_by_slug):
            try:
                tenant = lookup(value)
            except NotFoundError:
                continue
            break
        if tenant is None or not tenant.key or not getattr(tenant, "is_active", True):
            raise refusal
        membership = self._tenant_service.get_membership(user_key, tenant.key)
        if membership is None or not membership.is_active:
            raise refusal
        return tenant.key

    def list_api_keys(self, user_key: UserKey) -> list[ApiKeySummary]:
        if not self._api_key_repo:
            raise ValidationError("API keys are not configured.")

        keys = self._api_key_repo.list_by_user(user_key)
        return [
            ApiKeySummary(
                key=k.key or "",
                label=k.label,
                key_prefix=k.key_prefix,
                tenant_scope=k.tenant_scope,
                revoked=k.revoked,
                last_used_at=k.last_used_at,
                created_at=k.created_at,
            )
            for k in keys
        ]

    def revoke_api_key(self, user_key: UserKey, key_id: str) -> None:
        if not self._api_key_repo:
            raise ValidationError("API keys are not configured.")

        api_key = self._api_key_repo.get_or_raise(key_id)
        if api_key.user_key != user_key:
            raise ValidationError("API key does not belong to this user.")
        self._api_key_repo.revoke(key_id)
        logger.info("api_key_revoked", key_id=key_id, subject=self._log_subject(user_key))

    def authenticate_api_key(self, raw_key: str, *, client_ip: str | None) -> User | None:
        """Authenticate a request via API key. Returns the user or None.

        ``None`` for an unknown, revoked or expired key and an inactive owner.
        The key's own network controls raise instead (#1850): a request from
        outside its ``ip_allowlist`` is a 401 and a spent
        ``rate_limit_per_minute`` budget a 429, decided by
        :func:`~app.domain.services.api_key_controls.enforce_api_key_controls` —
        the implementation the MCP authenticator uses, so the two surfaces
        cannot disagree about what a key may do.
        """
        if not self._api_key_repo:
            return None
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._api_key_repo.get_by_hash(key_hash)
        if api_key is None or api_key.revoked:
            return None
        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            return None
        enforce_api_key_controls(api_key, client_ip=client_ip, rate_limiter=self._api_key_rate_limiter)
        # Update last_used_at
        if api_key.key:
            self._api_key_repo.update_last_used(api_key.key)
        user = self._user_repo.get_by_key(api_key.user_key)
        if user is None or not user.is_active:
            return None
        # The key's tenant restriction travels with the principal (#1817): the
        # tenant resolvers refuse every tenant it does not admit.
        return user.with_api_key_tenant_scope(api_key.tenant_scope)

    # ── Device pairing (REQ-023 / #1118) ────────────────────────────────

    def create_device_pairing(
        self,
        user_key: UserKey,
        ip_address: str | None = None,
        *,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
    ) -> tuple[str, datetime]:
        """Mint a one-time pairing code for ``user_key``, behind the step-up (#1847).

        The code is a bearer credential for the seconds it lives: whoever
        presents it first gets a session on this account. It is therefore drawn
        from ``secrets`` with the same 256-bit budget as an API key — never from
        ``random``, never with a counter or a timestamp mixed in, because any
        predictable component would let a code be derived rather than guessed.

        Args:
            user_key: Account the code is bound to. Binding happens **here**, in
                the store, so redemption never has to trust a caller-supplied
                identity.
            ip_address: Source address of the issuing request, for the audit
                event and the step-up throttle.
            current_password, step_up_code, step_up_token: The step-up
                (:meth:`_verify_credential_step_up`).
            authenticated_with_api_key: Whether the request came with a ``kp_``
                key — refused, a key cannot mint a session.

        Returns:
            ``(code, expires_at)`` — the raw code, which the caller shows once
            and never stores, and its expiry in UTC.

        Raises:
            ForbiddenError, UnauthorizedError, StepUpLockedError: The step-up (403 / 401 / 429).
            ValidationError: If no pairing store is configured.
            Exception: Whatever the store raises when it cannot persist the
                code. Deliberately not swallowed: a caught error would hand the
                user a QR code that can never be redeemed.
        """
        store = self._require_device_pairing_store()
        # The code redeems into a full session on this account: a credential
        # issued like an API key, so the same step-up (#1847). ``ip_address`` is
        # the client address the step-up throttle buckets on.
        self._verify_credential_step_up(
            user_key,
            action="device_pairing",
            target=None,
            current_password=current_password,
            step_up_code=step_up_code,
            step_up_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=ip_address,
        )
        code = secrets.token_urlsafe(_PAIRING_CODE_BYTES)
        expires_at = store.issue(code, user_key)
        logger.info(
            "device_pairing_created",
            subject=self._log_subject(user_key),
            ip_prefix=loggable_ip(ip_address),
            # Never the code, not even a prefix of it — see ``_code_fingerprint``.
            code_sha256=_code_fingerprint(code),
            expires_at=expires_at.isoformat(),
        )
        return code, expires_at

    def redeem_device_pairing(
        self,
        code: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
        device_name: str | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Exchange a pairing code for the standard REQ-023 token pair.

        Returns exactly what ``login_local`` returns, from exactly the same
        factory (``_create_tokens``): no new token type, no extra claim, and a
        ``RefreshToken`` document that ``list_sessions`` shows and
        ``revoke_session`` kills like any browser session. A separate token
        class for paired devices would have needed its own revocation, its own
        expiry sweep and its own place in the session list — three things that
        already exist and would then exist twice.

        The order below is load-bearing and mirrors ``_reject_unknown_account``:

        1. read the lockout state for the source address and refuse **before**
           the code store is touched — a locked-out caller must not be able to
           test a code at all, otherwise the lockout costs an attacker a status
           code and nothing else;
        2. only then consume the code (single-use, atomically, in the store);
        3. on a miss, count the failure and answer with the *same* generic
           error an unknown code gets, so "used", "expired" and "never existed"
           stay indistinguishable;
        4. on a hit, clear the counter — a valid code is proof of possession,
           and without the reset a household behind one NAT address would
           accumulate failures from mistyped codes until a legitimate pairing is
           refused.

        Args:
            code: The raw pairing code as scanned.
            user_agent: Client user agent, recorded on the session.
            ip_address: Source address; the throttle subject and the audit
                field. ``None`` falls back to a shared bucket rather than
                skipping the guard.
            device_name: Client-supplied label (operator decision, plan §Open
                questions 2). Normalised and length-capped here, then stored on
                the session document so the paired phone is distinguishable
                from a browser in the session list — and revocable there.

        Returns:
            ``(token_pair, raw_refresh_token, is_persistent)``.

        Raises:
            AccountLockedError: 423, once this address has failed too often.
            InvalidTokenError: 401 for a code that is unknown, already used,
                expired, or unreadable because the store is unreachable.
            UnauthorizedError: 401 if the bound account is gone or deactivated.
            ValidationError: 422 for an over-long ``device_name``, or if no
                pairing store is configured.
        """
        store = self._require_device_pairing_store()
        throttle = self._device_pairing_throttle_store
        bucket = ip_address or _UNKNOWN_IP_BUCKET
        device_name = self._validate_device_name(device_name)

        # Step 1 — lockout first. Nothing below this block may run for a locked
        # address, and in particular not ``store.consume``: consuming would burn
        # a code the attacker guessed correctly while the lockout was active.
        failed_attempts, locked_until = throttle.get_failure_state(bucket)
        if not self._throttle_engine.check_allowed(failed_attempts, locked_until):
            minutes = self._throttle_engine.get_lockout_minutes(locked_until)
            logger.info(
                "device_pairing_redeem_failed",
                reason="locked_out",
                ip_prefix=loggable_ip(ip_address),
                failed_attempts=failed_attempts,
                retry_after_minutes=minutes,
            )
            raise AccountLockedError(minutes)

        # Step 2 — single use lives in the store (pipelined GET+DEL), so two
        # redemptions racing on one code resolve to one winner.
        record = store.consume(code)
        if record is None:
            failed_attempts += 1
            throttle.record_failure(
                bucket,
                failed_attempts,
                self._throttle_engine.calculate_lockout(failed_attempts),
            )
            logger.info(
                "device_pairing_redeem_failed",
                reason="not_redeemable",
                ip_prefix=loggable_ip(ip_address),
                code_sha256=_code_fingerprint(code),
                failed_attempts=failed_attempts,
            )
            # One error for every miss. A distinct "already used" would confirm
            # to whoever sent it that the code they guessed was real.
            raise InvalidTokenError("pairing code")

        throttle.clear(bucket)

        # The account comes from the record, never from the request: the code
        # *is* the identity assertion, and there is no caller-supplied user to
        # cross-check it against.
        user = self._user_repo.get_by_key(record.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)

        logger.info(
            "device_pairing_redeemed",
            subject=self._log_subject(record.user_key),
            ip_prefix=loggable_ip(ip_address),
            code_sha256=_code_fingerprint(code),
            issued_at=record.issued_at.isoformat(),
            device_name_supplied=device_name is not None,
        )
        # Persistent by construction: a paired phone that had to be re-paired
        # every 24 hours would defeat the point of pairing it. Same choice
        # ``complete_oauth`` makes, and the session stays revocable from the
        # session list either way.
        return self._create_tokens(
            user,
            user_agent,
            ip_address,
            is_persistent=True,
            device_name=device_name,
        )

    def _require_device_pairing_store(self) -> IDevicePairingCodeStore:
        """Return the configured code store, or refuse like ``create_api_key``."""
        if self._device_pairing_code_store is None:
            raise ValidationError("Device pairing is not configured.")
        return self._device_pairing_code_store

    @staticmethod
    def _validate_device_name(device_name: str | None) -> str | None:
        """Normalise and bound the client-supplied device label.

        Blank-after-strip becomes ``None`` rather than an empty string, so a
        session list never has to distinguish "" from "not given".

        The label is an unauthenticated caller's free text, so it is bounded
        here as well as at the HTTP boundary: the request schema rejects an
        over-long value with 422, but a service reachable from a task or a test
        must not depend on that having happened. Both read the same
        :data:`DEVICE_NAME_MAX_LENGTH`.
        """
        if device_name is None:
            return None
        cleaned = device_name.strip()
        if not cleaned:
            return None
        if len(cleaned) > DEVICE_NAME_MAX_LENGTH:
            raise ValidationError(f"device_name must be at most {DEVICE_NAME_MAX_LENGTH} characters.")
        return cleaned

    # ── Helpers ─────────────────────────────────────────────────────────

    def _create_tokens(
        self,
        user: User,
        user_agent: str | None,
        ip_address: str | None,
        is_persistent: bool = False,
        device_name: str | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Mint the REQ-023 token pair and persist its session document.

        ``device_name`` defaults to ``None`` so the browser login and OAuth
        paths keep calling this unchanged and keep producing sessions that carry
        no label — the paired-device flow is the only caller that supplies one,
        and rotation (``refresh_tokens``) carries it over rather than dropping
        it (#1118).

        **A backstop against a caller that forgets its own check (#1528).** Four
        methods mint a pair; three of them (``refresh_tokens``, ``complete_oauth``,
        ``redeem_device_pairing``) carried their own ``is_active`` check and
        ``login_local`` carried none. That is the shape that drifts: the check is
        opt-in at the call site, so a fifth entry point — or a second branch
        inside an existing one, which is exactly how the OAuth auto-link slipped
        through — is ungated by default. Minting is the one thing all of them do,
        so the invariant is asserted here as well.

        **What this does NOT guarantee (SCR-003).** It reads the ``User`` it was
        handed. Every current caller hands it one the repository just returned, so
        for them the flag is the stored one — but a future caller that builds a
        ``User`` from a token payload rather than reading the account gets
        ``is_active`` from the model default (``True``, ``models/user.py``) and
        walks through. Making that impossible means re-reading the account here,
        one document read per minting on every login, refresh and rotation, to
        defend against a caller that does not exist; the cheaper and more honest
        move is to say plainly what the check covers. It is a backstop against a
        forgotten check, not against a fabricated principal.

        The per-path checks stay where they are: each of them refuses *before*
        its own side effects (the lockout write-back, the provider-link
        creation), which this one cannot do, and each returns the answer its
        caller's contract expects. This is the backstop, not the replacement.

        Raises:
            UnauthorizedError: The account is deactivated. Reached only when a
                caller forgot its own check — every current path refuses earlier.
        """
        if not user.is_active:
            raise UnauthorizedError(_INACTIVE_ACCOUNT_MESSAGE)

        # And the account type is not one that logs in at all (#1559). REQ-023 makes
        # ``service`` an M2M identity: API keys only, no interactive session, with an
        # IP allowlist and a per-account rate limit that a minted token pair carries
        # none of. This sits here for the reason the ``is_active`` check above sits
        # here: minting is the one step all four session paths share (``login_local``,
        # ``complete_oauth``, ``refresh_tokens``, ``redeem_device_pairing``), so a
        # fifth one — or a new branch inside an existing one — inherits the refusal
        # instead of having to remember it. The same SCR-003 caveat applies: it reads
        # the ``User`` it was handed, which every current caller takes from the
        # repository.
        if not allows_interactive_auth(user):
            raise UnauthorizedError(_SERVICE_ACCOUNT_LOGIN_MESSAGE)

        # Determine platform admin status from membership in "platform" tenant
        is_platform_admin = False
        if self._tenant_service and user.key:
            membership = self._tenant_service.get_membership(user.key, "platform")
            if membership and membership.is_active and membership.role == TenantRole.LEAD:
                is_platform_admin = True

        token_pair = self._token_engine.create_access_token(
            user_key=user.key or "",
            expire_minutes=self._access_expire_min,
            is_platform_admin=is_platform_admin,
        )

        raw_refresh, refresh_hash = self._token_engine.create_refresh_token()
        if is_persistent:
            expires_at = datetime.now(UTC) + timedelta(days=self._refresh_expire_days)
        else:
            expires_at = datetime.now(UTC) + timedelta(hours=self._session_expire_hours)
        refresh = RefreshToken(
            user_key=user.key or "",
            token_hash=refresh_hash,
            user_agent=user_agent,
            device_name=device_name,
            ip_address=ip_address,
            expires_at=expires_at,
            is_persistent=is_persistent,
        )
        self._refresh_token_repo.create(refresh)

        return token_pair, raw_refresh, is_persistent

    @staticmethod
    def _to_profile(user: User) -> UserProfile:
        return UserProfile(
            key=user.key or "",
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            locale=user.locale,
            timezone=user.timezone,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
