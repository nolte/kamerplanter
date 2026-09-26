from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import EmailChangeRequest, EmailChangeRequestKey


class IEmailChangeRepository(ABC):
    @abstractmethod
    def create(self, change_request: EmailChangeRequest) -> EmailChangeRequest: ...

    @abstractmethod
    def get_by_key(self, key: EmailChangeRequestKey) -> EmailChangeRequest | None: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> EmailChangeRequest | None: ...

    @abstractmethod
    def update(
        self,
        key: EmailChangeRequestKey,
        change_request: EmailChangeRequest,
    ) -> EmailChangeRequest: ...

    @abstractmethod
    def get_by_revert_token_hash(self, token_hash: str) -> EmailChangeRequest | None:
        """The confirmed change whose revert token hashes to *token_hash* (#1848)."""

    @abstractmethod
    def find_revert_reservation(self, email: str, now_iso: str) -> EmailChangeRequest | None:
        """The confirmed change whose open revert window reserves *email* (#1848), or ``None``."""

    @abstractmethod
    def claim_status(self, key: EmailChangeRequestKey, from_status: str, to_status: str, now_iso: str) -> bool:
        """Move the request from *from_status* to *to_status* atomically; ``False`` when it was not in *from_status*."""

    @abstractmethod
    def record_confirmation(
        self,
        key: EmailChangeRequestKey,
        *,
        previous_email: str,
        revert_token_hash: str,
        revert_expires_at_iso: str,
        now_iso: str,
    ) -> bool:
        """Store the revert data of a confirmation — only while the request is still ``confirmed`` (#1848)."""

    @abstractmethod
    def supersede_confirmed_after(self, user_key: UserKey, confirmed_after_iso: str, now_iso: str) -> int:
        """Mark every confirmed change of *user_key* confirmed after the instant as ``superseded`` (#1848)."""

    @abstractmethod
    def close_revert_windows(self, now_iso: str) -> int:
        """Clear ``previous_email`` and the revert token of every change past ``revert_expires_at`` (NFR-011 R-07)."""

    @abstractmethod
    def list_pending_for_user(self, user_key: UserKey) -> list[EmailChangeRequest]: ...

    @abstractmethod
    def expire_old(self, now_iso: str) -> int: ...

    @abstractmethod
    def delete(self, key: EmailChangeRequestKey) -> bool: ...

    @abstractmethod
    def delete_expired_unconfirmed(self, now_iso: str) -> int:
        """Hard-delete every unconfirmed request past its ``expires_at`` (NFR-011 R-07)."""

    @abstractmethod
    def delete_confirmed_past_revert_window(self, now_iso: str) -> int:
        """Hard-delete a confirmed change whose *stored* R-07a revert window has closed (NFR-011 R-07b)."""
