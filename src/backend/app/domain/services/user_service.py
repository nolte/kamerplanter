import structlog

from app.common.exceptions import NotFoundError
from app.common.types import UserKey
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User, UserProfile, UserProfileUpdate

logger = structlog.get_logger()


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo

    def get_profile(self, user_key: UserKey) -> UserProfile:
        user = self._user_repo.get_or_raise(user_key)
        return self._to_profile(user)

    def update_profile(self, user_key: UserKey, update: UserProfileUpdate) -> UserProfile:
        user = self._user_repo.get_or_raise(user_key)

        if update.display_name is not None:
            user.display_name = update.display_name
        if update.avatar_url is not None:
            user.avatar_url = update.avatar_url
        if update.locale is not None:
            user.locale = update.locale

        updated = self._user_repo.update(user_key, user)
        return self._to_profile(updated)

    def get_user(self, user_key: UserKey) -> User:
        """Load one full user, raising :class:`NotFoundError` when absent.

        Used by the platform-admin path (#1018), which needs the full ``User``
        (not the trimmed :class:`UserProfile`) to build its response.
        """
        return self._user_repo.get_or_raise(user_key)

    def admin_update_user(self, user_key: UserKey, data: dict) -> User:
        """Apply a partial platform-admin update to one user (#1018).

        ``data`` is a partial payload passed straight to
        :meth:`IUserRepository.update_fields`, so the **caller owns the
        allow-list**: build it from a closed request schema's ``model_dump()``
        (``AdminUserUpdate``), never from a raw request body. The single endpoint
        that reaches this — ``PATCH /admin/platform/users/{key}`` — does exactly
        that, and that closedness is what keeps ``email``, ``password_hash``,
        ``account_type`` and the token/lock fields out of the payload.

        Routed here by #1018, which ended a router that wrote to the users
        collection itself (``collection.update``) — Presentation straight onto
        Persistence (NFR-001), outside the repository's model re-validation
        (#982/#996), reserved-attribute strip and 1202 → ``NotFoundError``
        mapping.
        """
        user = self._user_repo.update_fields(user_key, data)
        if not user:
            raise NotFoundError("User", user_key)
        return user

    def delete_account(self, user_key: UserKey) -> None:
        user = self._user_repo.get_or_raise(user_key)

        # Revoke all sessions
        self._refresh_token_repo.revoke_all_for_user(user_key)

        # Soft-delete: deactivate
        user.is_active = False
        user.email = f"deleted_{user_key}@deleted.local"
        user.display_name = "Deleted User"
        user.password_hash = None
        user.avatar_url = None
        self._user_repo.update(user_key, user)
        logger.info("account_deleted", user_key=user_key)

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
