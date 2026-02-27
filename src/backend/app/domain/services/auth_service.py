from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.domain.services.tenant_service import TenantService

from app.common.enums import AuthProviderType
from app.common.exceptions import (
    AccountLockedError,
    DuplicateError,
    EmailNotVerifiedError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.common.types import UserKey
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.auth import AuthProvider, AuthProviderInfo, RefreshToken, SessionInfo, TokenPair
from app.domain.models.user import User, UserProfile

logger = structlog.get_logger()


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
        tenant_service: TenantService | None = None,
        require_email_verification: bool = False,
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
        self._tenant_service = tenant_service
        self._require_email_verification = require_email_verification

    # ── Registration ────────────────────────────────────────────────────

    def register_local(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> UserProfile:
        # Check password policy
        errors = self._password_engine.validate_password_policy(password)
        if errors:
            raise ValidationError("; ".join(errors))

        # Check duplicate email
        existing = self._user_repo.get_by_email(email)
        if existing:
            raise DuplicateError("User", "email", email)

        # Create user
        skip_verification = not self._require_email_verification
        verification_token = None if skip_verification else secrets.token_urlsafe(32)
        user = User(
            email=email,
            display_name=display_name,
            password_hash=self._password_engine.hash_password(password),
            email_verified=skip_verification,
            email_verification_token=verification_token,
            email_verification_expires=(
                None if skip_verification else datetime.now(UTC) + timedelta(hours=24)
            ),
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
    ) -> tuple[TokenPair, str]:
        """Returns (token_pair, raw_refresh_token)."""
        user = self._user_repo.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Invalid email or password.")

        # Check lockout
        if not self._throttle_engine.check_allowed(user.failed_login_attempts, user.locked_until):
            minutes = self._throttle_engine.get_lockout_minutes(user.locked_until)
            raise AccountLockedError(minutes)

        # Verify password
        if not user.password_hash or not self._password_engine.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            user.locked_until = self._throttle_engine.calculate_lockout(user.failed_login_attempts)
            if user.key:
                self._user_repo.update(user.key, user)
            raise UnauthorizedError("Invalid email or password.")

        # Check email verification (only when required)
        if self._require_email_verification and not user.email_verified:
            raise EmailNotVerifiedError()

        # Success: reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        if user.key:
            self._user_repo.update(user.key, user)

        return self._create_tokens(user, user_agent, ip_address)

    # ── Token refresh ───────────────────────────────────────────────────

    def refresh_tokens(
        self,
        raw_refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenPair, str]:
        """Rotate refresh token. Returns (new_token_pair, new_raw_refresh_token)."""
        token_hash = self._token_engine.hash_token(raw_refresh_token)
        stored = self._refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenError("refresh token")

        # Check expiry
        if stored.expires_at < datetime.now(UTC):
            if stored.key:
                self._refresh_token_repo.revoke(stored.key)
            raise InvalidTokenError("refresh token")

        # Revoke old token (rotation)
        if stored.key:
            self._refresh_token_repo.revoke(stored.key)

        # Load user
        user = self._user_repo.get_by_key(stored.user_key)
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is inactive.")

        return self._create_tokens(user, user_agent, ip_address)

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
            updated = self._user_repo.update(user.key, user)
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
            self._user_repo.update(user.key, user)

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
            self._user_repo.update(user.key, user)
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

    def change_password(self, user_key: UserKey, current_password: str, new_password: str) -> None:
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)

        if not user.password_hash or not self._password_engine.verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect.")

        errors = self._password_engine.validate_password_policy(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        user.password_hash = self._password_engine.hash_password(new_password)
        self._user_repo.update(user_key, user)
        # Revoke all sessions except current would be ideal, but for simplicity revoke all
        self._refresh_token_repo.revoke_all_for_user(user_key)

    # ── Helpers ─────────────────────────────────────────────────────────

    def _create_tokens(
        self,
        user: User,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[TokenPair, str]:
        token_pair = self._token_engine.create_access_token(
            user_key=user.key or "",
            email=user.email,
            display_name=user.display_name,
            expire_minutes=self._access_expire_min,
        )

        raw_refresh, refresh_hash = self._token_engine.create_refresh_token()
        refresh = RefreshToken(
            user_key=user.key or "",
            token_hash=refresh_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(UTC) + timedelta(days=self._refresh_expire_days),
        )
        self._refresh_token_repo.create(refresh)

        return token_pair, raw_refresh

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
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
