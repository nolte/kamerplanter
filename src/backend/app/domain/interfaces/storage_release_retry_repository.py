"""#2630 — the stored objects whose delete is still owed after their last record was removed."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageReleaseRetry:
    """One owed release: the object and its renditions, the tenant whose namespace they are in."""

    key: str
    tenant_key: str
    object_keys: tuple[str, ...]
    attempts: int
    #: When the release was first owed (ISO 8601, UTC); an object rewritten after it is a new upload, not ours.
    created_at: str


class IStorageReleaseRetryRepository(ABC):
    @abstractmethod
    def record(self, *, tenant_key: str, object_keys: list[str]) -> None:
        """Remember that ``object_keys`` must still be deleted; a second record of the same object merges."""

    @abstractmethod
    def due(self, limit: int) -> list[StorageReleaseRetry]:
        """The owed releases, oldest first, at most ``limit``."""

    @abstractmethod
    def resolve(self, key: str) -> None:
        """The release happened, or the object is held again: forget it."""

    @abstractmethod
    def failed_again(self, key: str) -> None:
        """Another attempt failed: count it, keep the entry."""
