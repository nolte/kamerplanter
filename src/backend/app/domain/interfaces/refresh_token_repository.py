from abc import ABC, abstractmethod
from datetime import datetime

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
    def cleanup_expired(self, *, now: datetime | None = None) -> int: ...

    @abstractmethod
    def list_active_for_user(self, user_key: UserKey, *, now: datetime | None = None) -> list[RefreshToken]: ...

    @abstractmethod
    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        """``(key, ip_address)`` of sessions created before ``cutoff_iso`` whose IP is still plain."""

    @abstractmethod
    def mark_ip_anonymized(self, key: str, anonymized_ip: str, anonymized_at_iso: str) -> None:
        """Replace the stored IP with ``anonymized_ip`` and stamp ``ip_anonymized_at``."""
