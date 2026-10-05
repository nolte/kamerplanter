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
    def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """The token with this hash in any state, revoked and rotated ones included (#2116)."""

    @abstractmethod
    def claim_rotation(self, key: str, family_key: str, rotated_at: datetime) -> bool:
        """Atomically mark a live token rotated; ``False`` when it was no longer live (#2116)."""

    @abstractmethod
    def set_successor(self, key: str, successor_key: str) -> None:
        """Record the token a rotation minted in place of ``key`` (#2116)."""

    @abstractmethod
    def family_is_live(self, user_key: UserKey, family_key: str) -> bool:
        """Whether one token of the family is neither revoked nor expired (#2116)."""

    @abstractmethod
    def revoke(self, key: str) -> bool: ...

    @abstractmethod
    def revoke_family(self, user_key: UserKey, family_key: str) -> int:
        """Revoke one family (one login) and move the account's ``access_token_generation`` (#2116)."""

    @abstractmethod
    def revoke_all_for_user(self, user_key: UserKey) -> int:
        """Revoke every session and move both session generations of the account (#2116)."""

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
