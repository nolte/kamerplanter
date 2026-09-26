"""The one step-up re-authentication every irreversible account action passes (#1813, #1814, #1816).

Before this module each site re-checked the password itself —
``PrivacyService.request_erasure``, ``TenantService`` (#1791) and
``AuthService.change_password`` — three copies of "if the account has a
password, verify it", none of them throttled, and two erasure routes
(``DELETE /users/me``, ``DELETE /admin/platform/users/{key}``) had no copy at all.
The class was opt-in at the call site, and the siblings drifted.

:meth:`StepUpVerifier.verify` is the rule, in this order:

1. **Who** — a human account from a signed-in session. A service account (REQ-023,
   API-key-only) and any request authenticated with a ``kp_`` API key — also one a
   human account issued — are refused (403): a key is a stored machine credential,
   not a person present (#1791 review SEC-001). Refused *before* anything is
   counted, so a leaked key cannot be used to lock the owner's step-ups.
2. **Lockout** — a locked subject is refused (429 ``STEP_UP_LOCKED``) before the
   echo or the password is looked at.
3. **Echo** — the target typed back (the account's e-mail, the tenant's slug):
   names what the requester believes they are destroying. A mismatch is 422 and is
   **not** counted — it tests nothing secret, and counting it would let a typo
   lock the step-up.
4. **Secret** — for an account with a local password hash, its current password;
   for an account without one (it signs in only through a federated provider and
   has no local secret to re-enter), a one-time code mailed to its address
   (:meth:`StepUpVerifier.issue_code`, ``POST /users/me/step-up-code``, #1815). A
   missing password is 401, a missing code 401 ``STEP_UP_CODE_REQUIRED`` — so a
   client knows to ask for one. Either secret is *reserved* on both counters
   before it is tested; a wrong one is 401 and counts into the same budget.

**Fresh re-authentication at the identity provider (#1815, operator decision:
variant 1).** An account without a local password whose linked provider can
re-authenticate a person *freshly* confirms by doing so: ``POST
/users/me/step-up/oidc`` sends the browser to the provider with ``prompt=login`` and
``max_age=0``; the callback checks the ID token (issuer, audience, nonce, expiry,
``sub`` = a link of this account, ``auth_time`` at most five minutes old) and hands
back a one-time token bound to account and act (:meth:`StepUpVerifier.issue_reauth_token`),
which the act presents as ``step_up_token`` — method ``oidc_reauth``.

The provider boundary: only OpenID Connect providers can prove *when* the person
signed in — Google and generic OIDC (with the ``openid`` scope). **GitHub** is plain
OAuth2: it issues no ID token, so no ``auth_time``. **Apple** issues an ID token but
without ``auth_time``. Accounts whose links are all of those keep the e-mailed code
(below) as the fallback; an account with an OIDC-capable link is refused the code
(``STEP_UP_REAUTH_REQUIRED``), because the code proves only the mailbox. Variant 2 —
no code at all — would leave GitHub/Apple-only accounts unable to exercise their
Art. 17 erasure themselves; it is the one flag :data:`EMAIL_CODE_FALLBACK`.

**Why a mailed code and not the echo (#1815).** Until #1815 the typed echo was the
whole confirmation of a federated account, and its password change (setting a
first password) passed on nothing at all. The echo tests nothing secret: whoever
holds the session reads the e-mail address off the profile page. The code proves
access to the mailbox the account was registered with — the same proof a password
reset relies on. Not an OIDC ``max_age``/``auth_time`` re-login: GitHub is plain
OAuth2 without ``auth_time``, so that would have left one provider class on the echo.

The code is eight digits, lives :data:`CODE_TTL_SECONDS`, confirms only the act it
was requested for (review SEC-003), is issued at most :data:`CODE_ISSUES_PER_WINDOW`
times an hour and never replaces an unspent one within :data:`CODE_COOLDOWN_SECONDS`
(review SEC-002), is stored only as an HMAC-SHA256 of ``account key : act : code``
under a server secret
(:mod:`app.domain.interfaces.step_up_code`), is spent by the first act that presents
it, and a new one replaces the old. It is guessed at most as often as a password:
the attempts count into the same throttle.

**Why an HMAC and which secret.** A bare ``sha256(key:code)`` over 10**8 codes is
reversed offline in seconds by anyone who reads the Valkey keyspace (a dump, a
replica, a shared instance) while the code lives — the store would hand out the
code it exists to protect. The key is ``JWT_SECRET_KEY``, derived for this one
purpose (``HMAC(secret, "kp-step-up-code")``) so the digest can never be replayed
as, or confused with, a token signature: it is present in every deployment that
has accounts (the access tokens are signed with it), so no new mandatory secret is
introduced, and whoever holds it can mint sessions anyway, so binding the code to
it gives an attacker nothing new. Not ``ERASURE_TOMBSTONE_SALT``: it may be empty
on an install that cannot erase, and it is purpose-bound to pseudonymisation.
Rotating the JWT secret invalidates outstanding codes — ten minutes' worth.

**Throttle (#1816).** Two counters, both over :class:`LoginThrottleEngine` so the
backoff curve is the login one (15 min, doubling to 4 h):

* per *(account, client address)* at the login threshold (5) — the bucket that
  normally trips;
* per *account* at :data:`ACCOUNT_CEILING` — bounds an attacker who rotates
  addresses, without letting one address lock the others below it.

**Why not the login lockout, as #1816 suggested.** Only a caller holding a session
of the account can produce a step-up failure for it: the password tested is always
the requester's *own* (an admin erasing someone else re-enters the admin's
password), and API keys are refused before counting. So no outsider can lock a
victim through this path. But the session holder can — and if their failures fed
``failed_login_attempts``, a session thief could lock the owner out of *signing
in*, the very step the owner needs to see and revoke the stolen session. Reading
the login lock the other way round would let an unauthenticated outsider (who can
already lock any known address at ``/auth/login``) block the owner's step-ups too.
So the step-up lock holds step-ups only. The residual: a session thief can keep
the account-wide step-up bucket locked; the owner still signs in, revokes sessions
and can reset the password by mail, which kills the thief's refresh token. That
last step holds only while the e-mail itself is behind a step-up — which it is
since #1841 (``PrivacyService.request_email_change`` passes this verifier, and the
current address is told of every request, and the owner's password reset or
change — or signing out everywhere — withdraws a still pending change). The
remaining residual: a thief who also controls the mailbox of a federated account
passes the code step-up; that is the mailbox, not this verifier.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

import structlog
from pydantic import BaseModel

from app.common.exceptions import (
    ForbiddenError,
    StepUpCodeRequiredError,
    StepUpLockedError,
    StepUpPasswordRequiredError,
    StepUpReauthRequiredError,
    UnauthorizedError,
    ValidationError,
)
from app.common.log_privacy import log_subject
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine, supports_fresh_reauth
from app.domain.engines.password_engine import PasswordEngine
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.step_up_code import IStepUpCodeStore
from app.domain.interfaces.step_up_throttle import IStepUpThrottleStore
from app.domain.models.auth import AuthProvider
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User, allows_interactive_auth

logger = structlog.get_logger()

#: How the requester confirmed: their current password, or — for an account
#: without a local password — a fresh sign-in at its identity provider
#: (``oidc_reauth``) or, where no linked provider can do that, the one-time code
#: mailed to it (``email_code``, #1815). The echo is
#: never a confirmation on its own any more (the results ``echo`` and
#: ``no_local_password`` are gone); ``echo`` / ``slug_confirmation`` survive only on
#: erasure and tenant-deletion records written before #1815.
type StepUpMethod = Literal["oidc_reauth", "email_code", "password"]

#: The acts that pass the verifier; only a log field, never a separate budget —
#: failures on one route lock the others, or an attacker would get one budget per route.
type StepUpAction = Literal[
    "account_erasure", "admin_account_erasure", "tenant_deletion", "password_change", "email_change"
]

#: Operator decision on #1815 (variant 1): the e-mailed code is the fallback of an
#: account whose linked providers all cannot re-authenticate freshly (GitHub —
#: plain OAuth2, no ID token; Apple — no ``auth_time``). Variant 2 would refuse
#: such an account every step-up, and with it the self-service Art. 17 erasure;
#: switching to it is this one flag (``False``: no code, the account is told to
#: re-authenticate — which it cannot, so only a password or an operator helps).
EMAIL_CODE_FALLBACK = True

#: How long the one-time token of a fresh re-authentication is valid (#1815).
REAUTH_TOKEN_TTL_SECONDS = 300

#: How long a mailed step-up code is valid (#1815): long enough to switch to the
#: mail client and back, short enough that a code read later is worthless.
CODE_TTL_SECONDS = 600

#: Digits of a step-up code — 10**8 values against at most :data:`ACCOUNT_CEILING`
#: tested guesses per throttle window.
CODE_DIGITS = 8

#: Review SEC-002 — how often an account may be mailed a code: a still-unspent code
#: is not replaced within this many seconds (so a request cannot void the code the
#: owner is typing), and at most :data:`CODE_ISSUES_PER_WINDOW` codes per
#: :data:`CODE_ISSUE_WINDOW_SECONDS` (so a session cannot turn the account into a
#: mail cannon — the per-address rate limit bounds one address only).
CODE_COOLDOWN_SECONDS = 60
CODE_ISSUES_PER_WINDOW = 5
CODE_ISSUE_WINDOW_SECONDS = 3600

#: What the mailed code confirms, per act (review SEC-003). Fixed English text, never
#: user input, so the mail can name the act without becoming a message channel.
CODE_PURPOSES: dict[str, str] = {
    "account_erasure": "delete your Kamerplanter account",
    "admin_account_erasure": "delete another user's account as a platform administrator",
    "tenant_deletion": "delete a garden (tenant) and all its data",
    "password_change": "set or change the password of your account",
    "email_change": "change the email address of your account",
}

#: Attempts per account across all addresses before the account-wide lock starts.
#: Three address-sized budgets: a user on a phone and a laptop who mistypes a few
#: times never gets near it, an attacker rotating addresses is bounded by it.
ACCOUNT_CEILING = 3 * MAX_ATTEMPTS

_UNKNOWN_ADDRESS = "unknown"


class StepUpConfirmation(BaseModel):
    """The step-up an irreversible account action carries in its request body."""

    model_config = {"frozen": True}

    #: The target typed back: the account's e-mail or the tenant's slug.
    echo: str
    #: The requester's current password; required when the account has one.
    password: str | None = None
    #: The one-time code mailed to an account without a local password (#1815).
    code: str | None = None
    #: The one-time token of a fresh sign-in at the account's identity provider (#1815).
    reauth_token: str | None = None


def echo_matches(given: str, expected: str, *, case_insensitive: bool = False) -> bool:
    """Constant-time comparison of a typed echo, ignoring surrounding whitespace.

    E-mail addresses compare case-insensitively (the stored address is what the
    user typed at registration, the echo is typed again); slugs compare exactly.
    """
    left, right = given.strip(), expected.strip()
    if case_insensitive:
        left, right = left.casefold(), right.casefold()
    return hmac.compare_digest(left.encode(), right.encode())


def _code_key(server_secret: str) -> bytes:
    """The purpose-derived HMAC key of the code digest (see the module docstring)."""
    return hmac.new(server_secret.encode(), b"kp-step-up-code", hashlib.sha256).digest()


def _code_digest(key: bytes, user_key: str, action: str, code: str) -> str:
    """What the code store keeps: bound to the account, the act and the server secret.

    The act is part of the digest (review SEC-003): a code the owner requested to
    set a password must not confirm the erasure of the account. ``verify`` builds
    the digest with *its* act, so a code presented to another act simply matches
    nothing — and is not spent by the mismatch.
    """
    return hmac.new(key, f"{user_key}:{action}:{code.strip()}".encode(), hashlib.sha256).hexdigest()


def _reauth_key(server_secret: str) -> bytes:
    """The HMAC key of the re-authentication token digest, purpose-separated from the code's."""
    return hmac.new(server_secret.encode(), b"kp-step-up-reauth", hashlib.sha256).digest()


class _OidcConfigSource(Protocol):
    def list_enabled(self) -> list[OidcProviderConfig]: ...


class FederatedReauthPolicy:
    """Which of an account's provider links can re-authenticate it freshly (#1815).

    A link is matched to **its own** configuration only (review SEC-001): the one
    named by ``oidc_config_slug``, if that configuration is enabled, of the link's
    type and supports a fresh re-authentication (:func:`supports_fresh_reauth`).
    A link made before the slug was recorded counts only when exactly one such
    configuration of its type exists — with two generic OIDC providers it could
    belong to either, and re-authenticating at the wrong one would confirm a
    stranger's ``sub``. Such an ambiguous link is not re-auth capable; the account
    keeps the e-mailed code (it is not locked out).
    """

    def __init__(self, auth_provider_repo: IAuthProviderRepository, oidc_config_repo: _OidcConfigSource) -> None:
        self._providers = auth_provider_repo
        self._configs = oidc_config_repo

    def reauth_links(self, user_key: str) -> list[tuple[AuthProvider, OidcProviderConfig]]:
        configs = sorted((c for c in self._configs.list_enabled() if supports_fresh_reauth(c)), key=lambda c: c.slug)
        links: list[tuple[AuthProvider, OidcProviderConfig]] = []
        for row in self._providers.list_by_user(user_key):
            of_type = [c for c in configs if OAuthEngine.link_type(c) == row.provider]
            if row.oidc_config_slug is not None:
                config = next((c for c in of_type if c.slug == row.oidc_config_slug), None)
            else:
                config = of_type[0] if len(of_type) == 1 else None
            if config is not None:
                links.append((row, config))
        return links

    def requires_reauth(self, user_key: str) -> bool:
        return bool(self.reauth_links(user_key))


class StepUpVerifier:
    """Checks — and throttles — the step-up of every irreversible account action."""

    def __init__(
        self,
        throttle_store: IStepUpThrottleStore,
        password_engine: PasswordEngine | None = None,
        throttle_engine: LoginThrottleEngine | None = None,
        tombstone_salt: str = "",
        *,
        code_store: IStepUpCodeStore | None = None,
        code_secret: str | None = None,
        reauth_store: IStepUpCodeStore | None = None,
        reauth_policy: FederatedReauthPolicy | None = None,
    ) -> None:
        self._store = throttle_store
        self._password_engine = password_engine or PasswordEngine()
        self._throttle_engine = throttle_engine or LoginThrottleEngine()
        self._tombstone_salt = tombstone_salt
        if code_store is None:
            # The process-wide tier, as for the throttle: a store made per service
            # instance would forget the code between the two requests.
            from app.data_access.external.step_up_code_store import DEFAULT_STEP_UP_CODE_STORE

            code_store = DEFAULT_STEP_UP_CODE_STORE
        self._code_store = code_store
        if code_secret is None:
            from app.config.settings import settings

            code_secret = settings.jwt_secret_key
        self._code_key = _code_key(code_secret)
        self._reauth_key = _reauth_key(code_secret)
        if reauth_store is None:
            from app.data_access.external.step_up_code_store import DEFAULT_STEP_UP_REAUTH_STORE

            reauth_store = DEFAULT_STEP_UP_REAUTH_STORE
        self._reauth_store = reauth_store
        # ``None`` (a verifier built outside the DI provider): which factor an
        # account without a password needs is unknown, so both are accepted — a
        # re-authentication token can only exist after a fresh sign-in.
        self._reauth_policy = reauth_policy

    def _requires_reauth(self, user_key: str) -> bool:
        return self._reauth_policy is not None and self._reauth_policy.requires_reauth(user_key)

    def admit_reauth(self, requester: User, *, authenticated_with_api_key: bool, client_ip: str | None) -> None:
        """Refuse to start a fresh re-authentication for who may not step up (#1815).

        The same order as :meth:`verify`: a person's session (403), the lock (429);
        and an account with a local password confirms with that (422).
        """
        self._refuse_non_person(requester, authenticated_with_api_key)
        user_key = requester.key or ""
        pair, account = self._subjects(user_key, client_ip)
        self._refuse_if_locked("reauth_start", user_key, pair, account)
        if requester.password_hash:
            raise StepUpPasswordRequiredError()

    def issue_reauth_token(self, requester: User, *, action: StepUpAction) -> str:
        """Mint the one-time token a verified fresh re-authentication hands back (#1815).

        32 random bytes, stored only as an HMAC bound to the account and the act,
        valid :data:`REAUTH_TOKEN_TTL_SECONDS`, spent by the first act that presents
        it; a new one replaces the previous.
        """
        user_key = requester.key or ""
        token = secrets.token_urlsafe(32)
        self._reauth_store.issue(
            user_key, _code_digest(self._reauth_key, user_key, action, token), REAUTH_TOKEN_TTL_SECONDS
        )
        logger.info(
            "step_up.reauth_token_issued",
            action=action,
            subject=log_subject(user_key),
        )
        return token

    def issue_code(
        self,
        requester: User,
        *,
        action: StepUpAction,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> tuple[str, datetime]:
        """Mint the one-time code an account without a local password confirms *action* with (#1815).

        The caller mails the returned code to the account's address and never
        returns it in a response. A new code replaces the previous one — but not
        within :data:`CODE_COOLDOWN_SECONDS` while it is unspent, and at most
        :data:`CODE_ISSUES_PER_WINDOW` codes per hour (review SEC-002). The code
        confirms *action* only (review SEC-003).

        Returns:
            ``(code, expires_at)`` — the raw eight-digit code and its expiry in UTC.

        Raises:
            ForbiddenError: a service account, or a request authenticated with an API key (403).
            StepUpLockedError: the step-up is locked for this account or address, or
                the issuance bound is reached — ``retry_after_minutes`` says how long (429).
            ValidationError: the account has a local password and confirms with it (422).
        """
        self._refuse_non_person(requester, authenticated_with_api_key)
        user_key = requester.key or ""
        pair, account = self._subjects(user_key, client_ip)
        self._refuse_if_locked("code_issue", user_key, pair, account)
        if requester.password_hash:
            raise StepUpPasswordRequiredError()
        if self._requires_reauth(user_key) or not EMAIL_CODE_FALLBACK:
            # Variant 1 (#1815): the code proves only the mailbox; an account whose
            # provider can re-authenticate freshly does that instead.
            raise StepUpReauthRequiredError(status_code=422)

        wait = self._code_store.reserve_issue(
            user_key,
            cooldown_seconds=CODE_COOLDOWN_SECONDS,
            max_issues=CODE_ISSUES_PER_WINDOW,
            window_seconds=CODE_ISSUE_WINDOW_SECONDS,
        )
        if wait > 0:
            minutes = max(1, -(-wait // 60))
            logger.info(
                "step_up.code_issue_throttled",
                action=action,
                subject=log_subject(user_key),
                retry_after_minutes=minutes,
            )
            raise StepUpLockedError(minutes, code_issue=True)

        code = f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"
        self._code_store.issue(user_key, _code_digest(self._code_key, user_key, action, code), CODE_TTL_SECONDS)
        logger.info("step_up.code_issued", action=action, subject=log_subject(user_key))
        return code, datetime.now(UTC) + timedelta(seconds=CODE_TTL_SECONDS)

    def withdraw_code(self, requester: User) -> None:
        """Take back the code just issued to *requester* because it could not be mailed (/code-review of #1862).

        The code is dropped — it was never in the owner's hands — and its issuance
        returned: the one-minute wait ends and the hourly budget gets its slot back.
        """
        user_key = requester.key or ""
        self._code_store.release_issue(user_key)
        logger.info("step_up.code_withdrawn", subject=log_subject(user_key))

    def verify(
        self,
        requester: User,
        *,
        action: StepUpAction,
        echo_ok: bool | None,
        password: str | None,
        code: str | None,
        reauth_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> StepUpMethod:
        """Refuse or accept the requester's step-up; return how it was confirmed.

        ``echo_ok`` is the caller's :func:`echo_matches` result, or ``None`` for an
        act that has no target to type back (the password and e-mail change).
        ``password`` is tested for an account with a local password; for one
        without, ``reauth_token`` (from a fresh sign-in at its provider,
        :meth:`issue_reauth_token`) or — only where no linked provider can do that —
        ``code`` (from :meth:`issue_code`). What does not apply is ignored.

        Raises:
            ForbiddenError: a service account, or a request authenticated with an API key (403).
            StepUpLockedError: too many failed step-ups for this account (429).
            ValidationError: the echo does not match (422).
            StepUpReauthRequiredError: an account with a re-authenticating provider sent
                no token, or a code instead (401).
            StepUpCodeRequiredError: an account without such a provider sent neither (401).
            UnauthorizedError: the password or the code is missing or wrong (401).
        """
        self._refuse_non_person(requester, authenticated_with_api_key)
        user_key = requester.key or ""
        pair, account = self._subjects(user_key, client_ip)
        self._refuse_if_locked(action, user_key, pair, account)

        if echo_ok is False:
            raise ValidationError("The confirmation does not match.")

        # Falsy, not ``is None``: an empty hash verifies nothing and ``login_local``
        # refuses a password sign-in for it too — such an account signs in only
        # through a federated provider, like one without the attribute.
        password_hash = requester.password_hash
        method: StepUpMethod
        if password_hash:
            if not password:
                raise UnauthorizedError("Password confirmation failed.")
            method, failure = "password", "Password confirmation failed."
        elif reauth_token and reauth_token.strip():
            method, failure = "oidc_reauth", "The re-authentication is invalid or has expired."
        elif self._requires_reauth(user_key) or not EMAIL_CODE_FALLBACK:
            # A code is refused, not tested: the account's provider can do better.
            raise StepUpReauthRequiredError()
        else:
            if not code or not code.strip():
                raise StepUpCodeRequiredError()
            method, failure = "email_code", "The confirmation code is wrong or has expired."

        pair_attempts = self._store.reserve_attempt(pair)
        account_attempts = self._store.reserve_attempt(account)
        if pair_attempts > MAX_ATTEMPTS or account_attempts > ACCOUNT_CEILING:
            # Over this window's budget: a burst racing the attempt that is being
            # tested. Refused without bcrypt. The reservation is not given back —
            # the tested attempt either clears the counter (right password) or
            # strikes, which re-arms it and overwrites the overshoot; a give-back
            # landing after that re-arm would undercount (/code-review of #1846).
            remaining = max(self._store.lock_remaining_seconds(pair), self._store.lock_remaining_seconds(account))
            self._refuse_locked(action, user_key, remaining or 60)

        if method == "password":
            confirmed = self._password_engine.verify_password(password or "", password_hash or "")
        elif method == "oidc_reauth":
            confirmed = self._reauth_store.consume(
                user_key, _code_digest(self._reauth_key, user_key, action, (reauth_token or "").strip())
            )
        else:
            confirmed = self._code_store.consume(user_key, _code_digest(self._code_key, user_key, action, code or ""))
        if not confirmed:
            if pair_attempts >= MAX_ATTEMPTS:
                self._strike(pair, MAX_ATTEMPTS)
            if account_attempts >= ACCOUNT_CEILING:
                self._strike(account, ACCOUNT_CEILING)
            logger.info(
                "step_up.failed",
                action=action,
                subject=log_subject(user_key),
                method=method,
                pair_attempts=pair_attempts,
                account_attempts=account_attempts,
            )
            raise UnauthorizedError(failure)

        self._store.clear(pair)
        self._store.clear(account)
        return method

    @staticmethod
    def _refuse_non_person(requester: User, authenticated_with_api_key: bool) -> None:
        """403 for a service account and for any API-key request — before anything is counted."""
        if not allows_interactive_auth(requester) or authenticated_with_api_key:
            raise ForbiddenError("This action requires a signed-in session of a person, not an API key.")

    @staticmethod
    def _subjects(user_key: str, client_ip: str | None) -> tuple[str, str]:
        """The (account, address) and the account-wide throttle subjects."""
        return f"pair:{user_key}:{client_ip or _UNKNOWN_ADDRESS}", f"account:{user_key}"

    def _refuse_if_locked(self, action: str, user_key: str, pair: str, account: str) -> None:
        remaining = max(self._store.lock_remaining_seconds(pair), self._store.lock_remaining_seconds(account))
        if remaining > 0:
            self._refuse_locked(action, user_key, remaining)

    def _strike(self, subject: str, threshold: int) -> None:
        """Lock *subject* and re-arm it for exactly one tested attempt after the lock.

        The login curve (``LoginThrottleEngine``): the first lock after *threshold*
        failures lasts 15 minutes, and each failure after a lock locks again at
        once for twice as long, up to 4 hours. Re-arming the counter to one below
        the threshold is what lets the next attempt after the lock be tested —
        before review SEC-001 the count only grew, and every later attempt was
        refused without bcrypt until the 24-hour window ran out.
        """
        engine = self._throttle_engine

        def lock_seconds(strikes: int) -> int:
            locked_until = engine.calculate_lockout(threshold - 1 + strikes, threshold=threshold)
            return int((locked_until - datetime.now(UTC)).total_seconds()) if locked_until else 1

        self._store.strike(subject, rearm_to=threshold - 1, lock_seconds=lock_seconds)

    def _refuse_locked(self, action: str, user_key: str, remaining_seconds: int) -> None:
        minutes = max(1, -(-remaining_seconds // 60))
        logger.info(
            "step_up.locked",
            action=action,
            subject=log_subject(user_key),
            retry_after_minutes=minutes,
        )
        raise StepUpLockedError(minutes)


def default_step_up_verifier(
    password_engine: PasswordEngine | None = None, *, tombstone_salt: str = ""
) -> StepUpVerifier:
    """A verifier over the process-wide in-memory tiers — what a service gets when not wired.

    The DI providers wire the Valkey-backed stores (``get_step_up_verifier``); this
    default exists so a service constructed without them still *throttles* and still
    finds the code it issued, rather than degrading to the unbounded check #1816
    removed (the ``DEFAULT_*`` lesson of #1118).
    """
    from app.data_access.external.step_up_code_store import DEFAULT_STEP_UP_CODE_STORE
    from app.data_access.external.step_up_throttle import DEFAULT_STEP_UP_THROTTLE_STORE

    return StepUpVerifier(
        DEFAULT_STEP_UP_THROTTLE_STORE,
        password_engine,
        tombstone_salt=tombstone_salt,
        code_store=DEFAULT_STEP_UP_CODE_STORE,
    )
