from abc import ABC, abstractmethod
from typing import Any

from app.common.types import UserKey
from app.domain.models.privacy import ErasureRequest, ErasureRequestKey


class IErasureRepository(ABC):
    @abstractmethod
    def create(self, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def create_with_key(self, erasure: ErasureRequest, key: ErasureRequestKey) -> ErasureRequest:
        """Insert under a caller-chosen key; a taken key raises (#1767 SEC-003).

        Raises:
            DuplicateError: a request with this key exists.
            WriteConflictError: a concurrent insert holds the key.
        """
        ...

    @abstractmethod
    def get_by_key(self, key: ErasureRequestKey) -> ErasureRequest | None: ...

    @abstractmethod
    def get_or_raise(self, key: ErasureRequestKey) -> ErasureRequest: ...

    @abstractmethod
    def update(self, key: ErasureRequestKey, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def update_fields(self, key: ErasureRequestKey, fields: dict[str, Any]) -> ErasureRequest:
        """Merge exactly ``fields``, preserving ``None`` (``keep_none=True``).

        The status transitions write through this: the repository merges, so a
        full-model write can never clear ``error_message``, and a record that
        reached ``completed`` would keep saying the erasure did not run (#1662
        SCR-003).
        """
        ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ErasureRequest]: ...

    @abstractmethod
    def find_active_for_user(self, user_key: UserKey) -> ErasureRequest | None: ...

    @abstractmethod
    def list_due_for_hard_delete(self, now_iso: str, stale_before_iso: str) -> list[ErasureRequest]: ...

    @abstractmethod
    def claim_for_run(self, key: ErasureRequestKey, *, now_iso: str, stale_before_iso: str) -> ErasureRequest | None:
        """Atomically move an open request to ``in_progress``, or return ``None`` (#1767 SEC-003).

        The request is claimed only when it is not ``completed`` and not held
        by a *fresh* ``in_progress`` run (``updated_at`` after
        ``stale_before_iso``). A second caller — a double admin delete, or the
        daily beat meeting an admin delete — gets ``None`` and must not run the
        erasure; a concurrent write on the same document counts as not claimed.
        """
        ...

    @abstractmethod
    def delete_completed_before(self, cutoff_iso: str) -> int:
        """Hard-delete ``completed`` requests whose ``completed_at`` is before the cutoff (NFR-011 R-06).

        Only ``status == 'completed'`` with a ``completed_at`` strictly before
        ``cutoff_iso`` — compared as instants — **and** a ``user_key`` that is
        already a tombstone (``anon_`` + 16 hex) qualifies. A request still owed
        a run (``scheduled``, ``in_progress``, ``partially_completed``), a
        completed one without a completion time, and a completed one still
        carrying a plaintext key (possibly the only trace of an unfulfilled
        Art. 17 duty, #1773 review GDPR-006) are never selected. The
        ``requested_erasure`` edges pointing at a deleted request go with it.
        Returns the number of requests deleted.
        """
        ...

    @abstractmethod
    def count_completed_without_tombstone_before(self, cutoff_iso: str) -> int:
        """Count the ``completed`` requests past the cutoff that the purge holds: no tombstone key."""
        ...
