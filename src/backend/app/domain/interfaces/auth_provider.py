from abc import ABC, abstractmethod

from app.domain.models.user import User


class IAuthProvider(ABC):
    # ``client_ip`` is keyword-only without a default (#1850): an API key's
    # ``ip_allowlist`` is decided on it, so every caller must state the address
    # it resolved rather than inherit "unknown" by omission.
    @abstractmethod
    def resolve_user(self, authorization: str | None, *, client_ip: str | None) -> User: ...

    @abstractmethod
    def resolve_user_optional(self, authorization: str | None, *, client_ip: str | None) -> User | None: ...

    @abstractmethod
    def is_authentication_required(self) -> bool: ...
