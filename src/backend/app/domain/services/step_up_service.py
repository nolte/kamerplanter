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
4. **Password** — for an account with a local password hash. The attempt is
   *reserved* on both counters before bcrypt runs; a wrong or missing password is
   401. An account without a hash signs in only through a federated provider and
   has no local secret to re-enter; the echo is its confirmation (REQ-394, #1791),
   and a real re-authentication for it is #1815.

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
and can reset the password by mail, which kills the thief's refresh token.
"""

from __future__ import annotations

import hmac
from datetime import UTC, datetime
from typing import Literal

import structlog
from pydantic import BaseModel

from app.common.exceptions import (
    ForbiddenError,
    StepUpLockedError,
    UnauthorizedError,
    ValidationError,
)
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.interfaces.step_up_throttle import IStepUpThrottleStore
from app.domain.models.user import User, allows_interactive_auth

logger = structlog.get_logger()

#: How the requester confirmed: their current password, or — for an account
#: without a local password — the typed echo alone. ``no_local_password`` is the
#: password change of a federated account setting its first password, which has
#: neither (#1815 is where it gets a real re-authentication).
type StepUpMethod = Literal["password", "echo", "no_local_password"]

#: The acts that pass the verifier; only a log field, never a separate budget —
#: failures on one route lock the others, or an attacker would get one budget per route.
type StepUpAction = Literal["account_erasure", "admin_account_erasure", "tenant_deletion", "password_change"]

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


def echo_matches(given: str, expected: str, *, case_insensitive: bool = False) -> bool:
    """Constant-time comparison of a typed echo, ignoring surrounding whitespace.

    E-mail addresses compare case-insensitively (the stored address is what the
    user typed at registration, the echo is typed again); slugs compare exactly.
    """
    left, right = given.strip(), expected.strip()
    if case_insensitive:
        left, right = left.casefold(), right.casefold()
    return hmac.compare_digest(left.encode(), right.encode())


class StepUpVerifier:
    """Checks — and throttles — the step-up of every irreversible account action."""

    def __init__(
        self,
        throttle_store: IStepUpThrottleStore,
        password_engine: PasswordEngine | None = None,
        throttle_engine: LoginThrottleEngine | None = None,
        tombstone_salt: str = "",
    ) -> None:
        self._store = throttle_store
        self._password_engine = password_engine or PasswordEngine()
        self._throttle_engine = throttle_engine or LoginThrottleEngine()
        self._tombstone_salt = tombstone_salt

    def verify(
        self,
        requester: User,
        *,
        action: StepUpAction,
        echo_ok: bool | None,
        password: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> StepUpMethod:
        """Refuse or accept the requester's step-up; return how it was confirmed.

        ``echo_ok`` is the caller's :func:`echo_matches` result, or ``None`` for an
        act that has no target to type back (the password change).

        Raises:
            ForbiddenError: a service account, or a request authenticated with an API key (403).
            StepUpLockedError: too many failed step-ups for this account (429).
            ValidationError: the echo does not match (422).
            UnauthorizedError: the password is missing or wrong (401).
        """
        if not allows_interactive_auth(requester) or authenticated_with_api_key:
            raise ForbiddenError("This action requires a signed-in session of a person, not an API key.")
        user_key = requester.key or ""
        pair = f"pair:{user_key}:{client_ip or _UNKNOWN_ADDRESS}"
        account = f"account:{user_key}"

        remaining = max(self._store.lock_remaining_seconds(pair), self._store.lock_remaining_seconds(account))
        if remaining > 0:
            self._refuse_locked(action, user_key, remaining)

        if echo_ok is False:
            raise ValidationError("The confirmation does not match.")

        # Falsy, not ``is None``: an empty hash verifies nothing and ``login_local``
        # refuses a password sign-in for it too — such an account signs in only
        # through a federated provider, like one without the attribute.
        if not requester.password_hash:
            return "echo" if echo_ok is not None else "no_local_password"

        if not password:
            raise UnauthorizedError("Password confirmation failed.")

        pair_attempts = self._store.reserve_attempt(pair)
        account_attempts = self._store.reserve_attempt(account)
        if pair_attempts > MAX_ATTEMPTS or account_attempts > ACCOUNT_CEILING:
            # A burst that raced past the lock check: its reservation is over the
            # threshold, so the password is not tested at all.
            self._lock(pair, pair_attempts, MAX_ATTEMPTS)
            self._lock(account, account_attempts, ACCOUNT_CEILING)
            self._refuse_locked(action, user_key, self._store.lock_remaining_seconds(pair) or 60)

        if not self._password_engine.verify_password(password, requester.password_hash):
            self._lock(pair, pair_attempts, MAX_ATTEMPTS)
            self._lock(account, account_attempts, ACCOUNT_CEILING)
            logger.info(
                "step_up.failed",
                action=action,
                subject=ErasureEngine.log_subject(user_key, self._tombstone_salt),
                pair_attempts=pair_attempts,
                account_attempts=account_attempts,
            )
            raise UnauthorizedError("Password confirmation failed.")

        self._store.clear(pair)
        self._store.clear(account)
        return "password"

    def _lock(self, subject: str, attempts: int, threshold: int) -> None:
        locked_until = self._throttle_engine.calculate_lockout(attempts, threshold=threshold)
        if locked_until is None:
            return
        self._store.lock(subject, max(1, int((locked_until - datetime.now(UTC)).total_seconds())))

    def _refuse_locked(self, action: StepUpAction, user_key: str, remaining_seconds: int) -> None:
        minutes = max(1, -(-remaining_seconds // 60))
        logger.info(
            "step_up.locked",
            action=action,
            subject=ErasureEngine.log_subject(user_key, self._tombstone_salt),
            retry_after_minutes=minutes,
        )
        raise StepUpLockedError(minutes)


def default_step_up_verifier(
    password_engine: PasswordEngine | None = None, *, tombstone_salt: str = ""
) -> StepUpVerifier:
    """A verifier over the process-wide in-memory tier — what a service gets when not wired.

    The DI providers wire the Valkey-backed store (``get_step_up_verifier``); this
    default exists so a service constructed without one still *throttles*, rather
    than degrading to the unbounded check #1816 removed (the ``DEFAULT_*`` lesson
    of #1118).
    """
    from app.data_access.external.step_up_throttle import DEFAULT_STEP_UP_THROTTLE_STORE

    return StepUpVerifier(DEFAULT_STEP_UP_THROTTLE_STORE, password_engine, tombstone_salt=tombstone_salt)
