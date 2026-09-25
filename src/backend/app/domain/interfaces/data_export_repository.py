from abc import ABC, abstractmethod
from typing import Any

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
    def update_fields(self, key: DataExportRequestKey, fields: dict[str, Any]) -> DataExportRequest:
        """Merge exactly ``fields`` into the record, preserving ``None`` values.

        The export pipeline writes through this rather than through
        :meth:`update`: the repository merges, so a field set to ``None`` on a
        full model never reaches the payload and a clear that was meant to
        happen silently does not (#1506). It is also the lost-update-safe write
        for a record whose read and write are separated by a collection walk and
        an object-storage upload (#1525).
        """
        ...

    @abstractmethod
    def increment_download_count(self, key: DataExportRequestKey) -> DataExportRequest:
        """Atomically bump ``download_count`` by one and return the record.

        Not a full-model write-back: if ``expire_data_exports`` ran between the
        read and the write, that would resurrect ``completed`` and a
        ``file_path`` that no longer exists (#1662 SCR-005).
        """
        ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[DataExportRequest]: ...

    @abstractmethod
    def list_active_by_user(self, user_key: UserKey) -> list[DataExportRequest]: ...

    @abstractmethod
    def delete(self, key: DataExportRequestKey) -> bool: ...

    @abstractmethod
    def list_expiry_due(self, now_iso: str) -> list[DataExportRequest]:
        """Exports whose bundle NFR-011 R-05 wants gone, without changing them (#1767 GDPR-005).

        ``completed`` exports past ``expires_at``, plus ``expired`` ones that
        still point at a bundle — records an earlier run flipped before a
        failed delete. The caller deletes each bundle **first** and writes
        ``expired`` only afterwards, so the status never claims a removal
        that did not happen.
        """
        ...

    @abstractmethod
    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        """Return pending exports requested before ``cutoff_iso`` (re-dispatch candidates)."""
        ...

    @abstractmethod
    def complete_if_processing(self, key: DataExportRequestKey, fields: dict[str, Any]) -> DataExportRequest | None:
        """Write the completion *fields* only while the export is still ``processing`` (#1767).

        ``None`` when it is not — an account erasure closed it while the bundle
        was being built; the caller then removes the bundle it just stored.
        """
        ...

    @abstractmethod
    def fail_open_for_user(self, user_key: UserKey, reason: str) -> int:
        """Close every ``pending``/``processing`` export of *user_key* as ``failed`` (#1767).

        Run by the account erasure before it deletes the stored bundles, so a
        build still in flight can no longer complete behind it. Returns the count.
        """
        ...

    @abstractmethod
    def start_processing(
        self, key: DataExportRequestKey, *, from_statuses: list[str], fields: dict[str, Any]
    ) -> DataExportRequest | None:
        """Move the export to ``processing`` only while it is in *from_statuses* (#1767).

        ``None`` when it is not — an account erasure closed it after the caller
        read it; the build must not start (it would reopen the request).
        """
        ...
