from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import ConsentRecord, ConsentRecordKey


class IConsentRepository(ABC):
    @abstractmethod
    def create(self, consent: ConsentRecord) -> ConsentRecord: ...

    @abstractmethod
    def get_by_key(self, key: ConsentRecordKey) -> ConsentRecord | None: ...

    @abstractmethod
    def get_by_user_and_purpose(self, user_key: UserKey, purpose: str) -> ConsentRecord | None: ...

    @abstractmethod
    def update(self, key: ConsentRecordKey, consent: ConsentRecord) -> ConsentRecord: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ConsentRecord]: ...

    @abstractmethod
    def delete(self, key: ConsentRecordKey) -> bool: ...

    @abstractmethod
    def delete_all_for_user(self, user_key: UserKey) -> int: ...

    @abstractmethod
    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        """``(key, ip_address)`` of every consent record recorded before the cutoff whose IP is still plain (R-04a)."""

    @abstractmethod
    def mark_ip_anonymized(self, key: ConsentRecordKey, anonymized_ip: str, anonymized_at_iso: str) -> None:
        """Replace a consent record's IP with its anonymised form and stamp when that happened (NFR-011 R-04a)."""

    @abstractmethod
    def delete_revoked_before(self, cutoff_iso: str) -> int:
        """Hard-delete every consent record revoked before the cutoff (NFR-011 R-04)."""
