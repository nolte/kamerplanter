from abc import ABC, abstractmethod

from app.domain.models.user import User


class IAuthProvider(ABC):
    @abstractmethod
    def resolve_user(self, authorization: str | None) -> User: ...

    @abstractmethod
    def resolve_user_optional(self, authorization: str | None) -> User | None: ...

    @abstractmethod
    def is_authentication_required(self) -> bool: ...
