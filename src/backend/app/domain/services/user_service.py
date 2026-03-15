from typing import TYPE_CHECKING

import structlog

from app.common.exceptions import NotFoundError
from app.domain.models.user import User, UserProfile, UserProfileUpdate

if TYPE_CHECKING:
    from app.common.types import UserKey
    from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
    from app.domain.interfaces.user_repository import IUserRepository

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
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)
        return self._to_profile(user)

    def update_profile(self, user_key: UserKey, update: UserProfileUpdate) -> UserProfile:
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)

        if update.display_name is not None:
            user.display_name = update.display_name
        if update.avatar_url is not None:
            user.avatar_url = update.avatar_url
        if update.locale is not None:
            user.locale = update.locale

        updated = self._user_repo.update(user_key, user)
        return self._to_profile(updated)

    def delete_account(self, user_key: UserKey) -> None:
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)

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
