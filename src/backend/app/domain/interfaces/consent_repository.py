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
