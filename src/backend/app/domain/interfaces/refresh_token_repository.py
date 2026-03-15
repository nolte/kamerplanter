from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import UserKey
    from app.domain.models.auth import RefreshToken


class IRefreshTokenRepository(ABC):
    @abstractmethod
    def create(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    def revoke(self, key: str) -> bool: ...

    @abstractmethod
    def revoke_all_for_user(self, user_key: UserKey) -> int: ...

    @abstractmethod
    def cleanup_expired(self) -> int: ...

    @abstractmethod
    def list_active_for_user(self, user_key: UserKey) -> list[RefreshToken]: ...
