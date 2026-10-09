from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.domain.models.invitation import Invitation


class IInvitationRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> Invitation | None: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...

    @abstractmethod
    def create(self, invitation: Invitation) -> Invitation: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> Invitation | None:
        """Apply a partial field update to one invitation (#968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Under the old
        name it shadowed the full-model ``update`` of the base repository with
        an arbitrary-``dict`` signature — an "update" that silently accepted
        mass assignment.

        Callers MUST build ``fields`` from named fields or a validated
        schema's ``model_dump()``, never from a raw request body.

        Returns ``None`` when no invitation carries ``key``.
        """

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_tenant(
        self, tenant_key: str, *, offset: int | None = None, limit: int | None = None
    ) -> list[Invitation]: ...

    @abstractmethod
    def list_pending_email_invitations(self, email: str) -> list[Invitation]:
        """The pending ``email`` invitations issued for *email*, compared case-insensitively (#2132).

        Expiry is the caller's to check (:meth:`InvitationEngine.is_expired`).
        """

    @abstractmethod
    def mark_accepted_if_pending(self, key: str, fields: dict[str, Any]) -> Invitation | None:
        """Set *key* to ``accepted`` with *fields*, only while it is still ``pending``; else ``None``.

        One conditional statement, so a revocation that lands between the
        caller's read and this write wins instead of being overwritten
        (REQ-025 AK-IE-06, #1825 security review SEC-001).
        """
        ...

    @abstractmethod
    def revoke_pending_for_tenant(self, tenant_key: str) -> int:
        """Flip every ``pending`` invitation into *tenant_key* to ``revoked``; returns how many (REQ-025 AK-IE-06).

        One statement over the whole tenant — no page limit, e-mail and link
        invitations alike — so an invitation cannot be missed because it sat
        behind a listing's cut-off.
        """
        ...

    @abstractmethod
    def cleanup_expired(self, *, now: datetime | None = None) -> int: ...

    @abstractmethod
    def delete_expired_before(self, cutoff_iso: str) -> int:
        """Hard-delete every ``expired`` invitation whose ``expires_at`` is before the cutoff (NFR-011 R-12)."""
