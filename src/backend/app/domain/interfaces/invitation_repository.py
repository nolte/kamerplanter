from abc import ABC, abstractmethod

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
    def list_by_tenant(self, tenant_key: str) -> list[Invitation]: ...

    @abstractmethod
    def cleanup_expired(self) -> int: ...

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...
