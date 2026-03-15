from typing import TYPE_CHECKING

from app.domain.interfaces.auth_provider import IAuthProvider

if TYPE_CHECKING:
    from app.domain.interfaces.user_repository import IUserRepository
    from app.domain.models.user import User

_SYSTEM_USER_KEY = "system-user"


class LightAuthProvider(IAuthProvider):
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo
        self._cached_user: User | None = None

    def _get_system_user(self) -> User:
        if self._cached_user is not None:
            return self._cached_user
        user = self._user_repo.get_by_key(_SYSTEM_USER_KEY)
        if user is None:
            msg = (
                "System user not found. "
                "Run seed_light_mode to create the system user."
            )
            raise RuntimeError(msg)
        self._cached_user = user
        return user

    def resolve_user(self, authorization: str | None) -> User:
        return self._get_system_user()

    def resolve_user_optional(self, authorization: str | None) -> User | None:
        return self._get_system_user()

    def is_authentication_required(self) -> bool:
        return False
