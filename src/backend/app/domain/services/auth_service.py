import hashlib
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import NoReturn

import structlog

from app.common.decoys import decoy_document_key, email_digest
from app.common.enums import AuthProviderType, TenantRole
from app.common.exceptions import (
    AccountLockedError,
    EmailNotVerifiedError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.common.types import UserKey
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.data_access.external.redis_oauth_state import RedisOAuthStateStore
from app.data_access.external.unknown_account_store import DEFAULT_UNKNOWN_ACCOUNT_STORE
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.unknown_account_store import IUnknownAccountStore
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.auth import (
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
from app.domain.models.user import User, UserProfile
from app.domain.services.tenant_service import TenantService

logger = structlog.get_logger()


def _iso(value):  # noqa: ANN001, ANN202 — datetime | None -> str | None
    """Serialize an optional datetime for a partial update doc (JSON mode)."""
    return value.isoformat() if value is not None else None


_API_KEY_PREFIX = "kp_"

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
        require_email_verification: bool = False,
        oauth_engine: OAuthEngine | None = None,
        oauth_state_store: RedisOAuthStateStore | None = None,
        api_key_repo: IApiKeyRepository | None = None,
        oidc_config_repo: ArangoOidcConfigRepository | None = None,
        encryption_engine: EncryptionEngine | None = None,
        unknown_account_store: IUnknownAccountStore | None = None,
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
        self._oidc_config_repo = oidc_config_repo
        self._encryption_engine = encryption_engine
        # Never ``None``: a missing store would make the SEC-H-010 login guard
        # inert instead of merely process-local. See the module docstring of
        # ``data_access.external.unknown_account_store``.
        self._unknown_account_store: IUnknownAccountStore = (
            unknown_account_store if unknown_account_store is not None else DEFAULT_UNKNOWN_ACCOUNT_STORE
        )

    # ── Registration ────────────────────────────────────────────────────

    def register_local(
        self,
        email: str,
        password: str,
        display_name: str,
        *,
        on_existing_address: Callable[[UserKey], None] | None = None,
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

        Returns:
            The profile of the created account — or, for a taken address, one
            synthesised to be indistinguishable from it.

        Raises:
            ValidationError: If the password violates the policy.
        """
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
        if existing is not None:
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
            if on_existing_address is not None and existing.key:
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
            email_verification_expires=(None if skip_verification else datetime.now(UTC) + timedelta(hours=24)),
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
            self._email_service.send_verification_email(
                to_email=email,
                display_name=display_name,
                token=verification_token,
                frontend_url=self._frontend_url,
            )

        logger.info("user_registered", email=email, verified=skip_verification)
        return self._to_profile(created)

    # ── Login ───────────────────────────────────────────────────────────

    def login_local(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
        remember_me: bool = False,
    ) -> tuple[TokenPair, str, bool]:
        """Returns (token_pair, raw_refresh_token, is_persistent)."""
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
                # Partial update: a full-document write would clobber any
                # concurrent change to the user (e.g. a profile edit) with
                # this request's stale read — classic lost update.
                self._user_repo.update_fields(
                    user.key,
                    {
                        "failed_login_attempts": user.failed_login_attempts,
                        "locked_until": _iso(user.locked_until),
                    },
                )
            raise UnauthorizedError("Invalid email or password.")

        # Check email verification (only when required)
        if self._require_email_verification and not user.email_verified:
            raise EmailNotVerifiedError()

        # Success: reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        if user.key:
            # Partial update (lost-update guard): a concurrent login used to
            # write its stale full user snapshot back and silently revert
            # e.g. a display-name change saved moments earlier.
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

        # Revoke old token (rotation)
        if stored.key:
            self._refresh_token_repo.revoke(stored.key)

        # Load user
        user = self._user_repo.get_by_key(stored.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is inactive.")

        return self._create_tokens(user, user_agent, ip_address, is_persistent=is_persistent)

    # ── Email verification ──────────────────────────────────────────────

    def verify_email(self, token: str) -> UserProfile:
        # Scan for user with this token
        # (In production, this would be a direct lookup by token hash)
        # For simplicity, we iterate — acceptable with small user counts
        from app.data_access.arango import collections as col

        db = self._user_repo._db  # type: ignore[attr-defined]
        query = """
        FOR doc IN @@collection
          FILTER doc.email_verification_token == @token
          LIMIT 1
          RETURN doc
        """
        cursor = db.aql.execute(query, bind_vars={"@collection": col.USERS, "token": token})
        docs = list(cursor)
        if not docs:
            raise InvalidTokenError("verification token")

        doc = docs[0]
        user = User(**{**doc, "_key": doc.get("_key", doc.get("_id", "").split("/")[-1])})

        # Check expiry
        if user.email_verification_expires and user.email_verification_expires < datetime.now(UTC):
            raise InvalidTokenError("verification token")

        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        if user.key:
            updated = self._user_repo.update_fields(
                user.key,
                {
                    "email_verified": True,
                    "email_verification_token": None,
                    "email_verification_expires": None,
                },
            )
            logger.info("email_verified", email=user.email)
            return self._to_profile(updated)
        raise InvalidTokenError("verification token")

    # ── Password reset ──────────────────────────────────────────────────

    def request_password_reset(self, email: str) -> None:
        """Always succeeds (no email enumeration)."""
        user = self._user_repo.get_by_email(email)
        if user is None:
            return  # Silent fail to prevent enumeration

        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
        if user.key:
            self._user_repo.update_fields(
                user.key,
                {
                    "password_reset_token": token,
                    "password_reset_expires": _iso(user.password_reset_expires),
                },
            )

        self._email_service.send_password_reset_email(
            to_email=email,
            display_name=user.display_name,
            token=token,
            frontend_url=self._frontend_url,
        )

    def reset_password(self, token: str, new_password: str) -> None:
        errors = self._password_engine.validate_password_policy(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        from app.data_access.arango import collections as col

        db = self._user_repo._db  # type: ignore[attr-defined]
        query = """
        FOR doc IN @@collection
          FILTER doc.password_reset_token == @token
          LIMIT 1
          RETURN doc
        """
        cursor = db.aql.execute(query, bind_vars={"@collection": col.USERS, "token": token})
        docs = list(cursor)
        if not docs:
            raise InvalidTokenError("reset token")

        doc = docs[0]
        user = User(**{**doc, "_key": doc.get("_key", doc.get("_id", "").split("/")[-1])})

        if user.password_reset_expires and user.password_reset_expires < datetime.now(UTC):
            raise InvalidTokenError("reset token")

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
            logger.info("password_reset", email=user.email)

    # ── Logout ──────────────────────────────────────────────────────────

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = self._token_engine.hash_token(raw_refresh_token)
        stored = self._refresh_token_repo.get_by_hash(token_hash)
        if stored and stored.key:
            self._refresh_token_repo.revoke(stored.key)

    def logout_all(self, user_key: UserKey) -> int:
        return self._refresh_token_repo.revoke_all_for_user(user_key)

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

    def unlink_provider(self, user_key: UserKey, provider_key: str) -> None:
        providers = self._auth_provider_repo.list_by_user(user_key)
        if len(providers) <= 1:
            raise ValidationError("Cannot unlink the last authentication provider.")

        target = next((p for p in providers if p.key == provider_key), None)
        if target is None:
            raise NotFoundError("AuthProvider", provider_key)
        if target.user_key != user_key:
            raise ValidationError("Provider does not belong to this user.")

        self._auth_provider_repo.delete(provider_key)

    # ── Sessions ────────────────────────────────────────────────────────

    def list_sessions(self, user_key: UserKey, current_token_hash: str | None = None) -> list[SessionInfo]:
        tokens = self._refresh_token_repo.list_active_for_user(user_key)
        return [
            SessionInfo(
                key=t.key or "",
                user_agent=t.user_agent,
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
    ) -> None:
        user = self._user_repo.get_or_raise(user_key)

        # SSO-only users (no password_hash) can set initial password without current_password
        if user.password_hash and (
            not current_password
            or not self._password_engine.verify_password(
                current_password,
                user.password_hash,
            )
        ):
            raise UnauthorizedError("Current password is incorrect.")

        errors = self._password_engine.validate_password_policy(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

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

        redirect = self._oauth_engine.build_authorization_url(config, redirect_uri)

        # Store state -> { code_verifier, nonce, provider_slug } in Redis
        self._oauth_state_store.save_state(
            redirect.state,
            {
                "code_verifier": redirect.code_verifier,
                "nonce": redirect.nonce,
                "provider_slug": provider_slug,
            },
        )

        return redirect

    def complete_oauth(
        self,
        provider_slug: str,
        code: str,
        state: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenPair, str, bool]:
        """Exchange code, find/create user, return tokens."""
        if not self._oauth_engine or not self._oauth_state_store or not self._oidc_config_repo:
            raise ValidationError("OAuth is not configured.")

        # Retrieve and validate state
        state_data = self._oauth_state_store.get_and_delete(state)
        if state_data is None:
            raise InvalidTokenError("OAuth state")
        if state_data.get("provider_slug") != provider_slug:
            raise InvalidTokenError("OAuth state")

        config = self._oidc_config_repo.get_by_slug(provider_slug)
        if config is None or not config.enabled:
            raise NotFoundError("OidcProviderConfig", provider_slug)

        # Decrypt client secret
        client_secret = config.client_secret_encrypted
        if self._encryption_engine:
            client_secret = self._encryption_engine.decrypt(client_secret)

        redirect_uri = f"{self._frontend_url}/auth/callback"

        # Exchange code for tokens
        token_response = self._oauth_engine.exchange_code_for_tokens(
            config,
            code,
            state_data["code_verifier"],
            redirect_uri,
            client_secret,
        )

        access_token = token_response.get("access_token", "")
        oauth_user = self._oauth_engine.extract_user_info(config, token_response, access_token)

        # Find existing auth provider link
        existing_provider = self._auth_provider_repo.get_by_provider(
            oauth_user.provider,
            oauth_user.provider_user_id,
        )

        if existing_provider:
            # Existing link — login
            user = self._user_repo.get_by_key(existing_provider.user_key)
            if user is None or not user.is_active:
                raise UnauthorizedError("User account is inactive.")
            # Update last_used_at on provider
            existing_provider.last_used_at = datetime.now(UTC)
            if existing_provider.key:
                self._auth_provider_repo.update(existing_provider.key, existing_provider)
        else:
            # No link — check if email matches existing user (auto-link)
            existing_user = self._user_repo.get_by_email(oauth_user.email)
            if existing_user:
                if self._oauth_engine.should_auto_link(existing_user.email_verified, True):
                    user = existing_user
                    # Create provider link
                    self._create_oauth_provider(user.key or "", oauth_user, token_response)
                else:
                    raise ValidationError(
                        "An account with this email exists but is not verified. "
                        "Verify your email first or log in with your password.",
                    )
            else:
                # New user — register via OAuth
                user = self._register_oauth_user(oauth_user)
                self._create_oauth_provider(user.key or "", oauth_user, token_response)

        user.last_login_at = datetime.now(UTC)
        if user.key:
            self._user_repo.update_fields(user.key, {"last_login_at": _iso(user.last_login_at)})

        logger.info("oauth_login", provider=provider_slug, email=oauth_user.email)
        return self._create_tokens(user, user_agent, ip_address, is_persistent=True)

    def link_provider(
        self,
        user_key: UserKey,
        provider_slug: str,
        code: str,
        state: str,
    ) -> AuthProviderInfo:
        """Link an OAuth provider to an existing user account."""
        if not self._oauth_engine or not self._oauth_state_store or not self._oidc_config_repo:
            raise ValidationError("OAuth is not configured.")

        state_data = self._oauth_state_store.get_and_delete(state)
        if state_data is None:
            raise InvalidTokenError("OAuth state")

        config = self._oidc_config_repo.get_by_slug(provider_slug)
        if config is None or not config.enabled:
            raise NotFoundError("OidcProviderConfig", provider_slug)

        client_secret = config.client_secret_encrypted
        if self._encryption_engine:
            client_secret = self._encryption_engine.decrypt(client_secret)

        redirect_uri = f"{self._frontend_url}/auth/callback"
        token_response = self._oauth_engine.exchange_code_for_tokens(
            config,
            code,
            state_data["code_verifier"],
            redirect_uri,
            client_secret,
        )
        access_token = token_response.get("access_token", "")
        oauth_user = self._oauth_engine.extract_user_info(config, token_response, access_token)

        # Check not already linked to another user
        existing = self._auth_provider_repo.get_by_provider(
            oauth_user.provider,
            oauth_user.provider_user_id,
        )
        if existing:
            raise ValidationError("This provider account is already linked to another user.")

        provider = self._create_oauth_provider(user_key, oauth_user, token_response)
        return AuthProviderInfo(
            key=provider.key or "",
            provider=provider.provider,
            provider_email=provider.provider_email,
            provider_display_name=provider.provider_display_name,
            linked_at=provider.linked_at,
            last_used_at=provider.last_used_at,
        )

    def _register_oauth_user(self, oauth_user: OAuthUserInfo) -> User:
        """Create a new user from OAuth info (no password)."""

        user = User(
            email=oauth_user.email,
            display_name=oauth_user.display_name,
            email_verified=True,  # OAuth emails are considered verified
            avatar_url=oauth_user.avatar_url,
        )
        created = self._user_repo.create(user)
        if self._tenant_service and created.key:
            self._tenant_service.create_personal_tenant(created.key, created.display_name)
        logger.info("oauth_user_registered", email=oauth_user.email, provider=oauth_user.provider)
        return created

    def _create_oauth_provider(
        self,
        user_key: str,
        oauth_user: OAuthUserInfo,
        token_response: dict,
    ) -> AuthProvider:
        """Create an AuthProvider record for an OAuth login."""

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
    ) -> ApiKeyCreated:
        if not self._api_key_repo:
            raise ValidationError("API keys are not configured.")

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

        logger.info("api_key_created", user_key=user_key, label=label, prefix=key_prefix)
        return ApiKeyCreated(
            key=created.key or "",
            label=created.label,
            raw_key=raw_key,
            key_prefix=key_prefix,
            tenant_scope=tenant_scope,
            created_at=created.created_at,
        )

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
        logger.info("api_key_revoked", key_id=key_id, user_key=user_key)

    def authenticate_api_key(self, raw_key: str) -> User | None:
        """Authenticate a request via API key. Returns the user or None."""
        if not self._api_key_repo:
            return None
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._api_key_repo.get_by_hash(key_hash)
        if api_key is None or api_key.revoked:
            return None
        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            return None
        # Update last_used_at
        if api_key.key:
            self._api_key_repo.update_last_used(api_key.key)
        user = self._user_repo.get_by_key(api_key.user_key)
        if user is None or not user.is_active:
            return None
        return user

    # ── Helpers ─────────────────────────────────────────────────────────

    def _create_tokens(
        self,
        user: User,
        user_agent: str | None,
        ip_address: str | None,
        is_persistent: bool = False,
    ) -> tuple[TokenPair, str, bool]:
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
