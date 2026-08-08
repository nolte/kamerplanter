from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: UserKey) -> User | None: ...

    @abstractmethod
    def get_or_raise(self, key: UserKey) -> User: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, key: UserKey, user: User) -> User: ...

    @abstractmethod
    def update_fields(self, key: UserKey, fields: dict) -> User | None:
        """Apply a partial field update to one user (#1018, mirrors #968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Callers MUST build
        ``fields`` from named fields or a validated schema's ``model_dump()``,
        never from a raw request body — the payload is applied key-by-key and
        ``model_copy(update=...)`` does not validate, so the re-validation of the
        merged model (#968) is what catches an ill-typed declared field.

        Returns ``None`` when no user carries ``key``.
        """

    @abstractmethod
    def delete(self, key: UserKey) -> bool: ...

    @abstractmethod
    def get_unverified_before(self, cutoff_iso: str) -> list[User]: ...
