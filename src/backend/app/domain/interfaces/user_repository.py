from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import UserKey
    from app.domain.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: UserKey) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, key: UserKey, user: User) -> User: ...

    @abstractmethod
    def delete(self, key: UserKey) -> bool: ...

    @abstractmethod
    def get_unverified_before(self, cutoff_iso: str) -> list[User]: ...
