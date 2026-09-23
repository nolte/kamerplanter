from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import DataExportRequest, DataExportRequestKey


class IDataExportRepository(ABC):
    @abstractmethod
    def create(self, export_request: DataExportRequest) -> DataExportRequest: ...

    @abstractmethod
    def get_by_key(self, key: DataExportRequestKey) -> DataExportRequest | None: ...

    @abstractmethod
    def get_or_raise(self, key: DataExportRequestKey) -> DataExportRequest: ...

    @abstractmethod
    def update(self, key: DataExportRequestKey, export_request: DataExportRequest) -> DataExportRequest: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[DataExportRequest]: ...

    @abstractmethod
    def list_active_by_user(self, user_key: UserKey) -> list[DataExportRequest]: ...

    @abstractmethod
    def delete(self, key: DataExportRequestKey) -> bool: ...

    @abstractmethod
    def expire_old(self, now_iso: str) -> list[DataExportRequest]:
        """Flip every expired export to ``expired`` and return the changed records.

        Returns the records rather than a count so the caller can delete each
        bundle's object (NFR-011 R-05 is "delete the file *and* set the
        status"; a count cannot say which files).
        """
        ...

    @abstractmethod
    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        """Return pending exports requested before ``cutoff_iso`` (re-dispatch candidates)."""
        ...
