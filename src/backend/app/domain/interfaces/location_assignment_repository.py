from abc import ABC, abstractmethod

from app.domain.models.location_assignment import LocationAssignment


class ILocationAssignmentRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> LocationAssignment | None: ...

    @abstractmethod
    def create(self, assignment: LocationAssignment) -> LocationAssignment: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> LocationAssignment | None:
        """Apply a partial field update to one location assignment (#968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Under the old
        name it shadowed the full-model ``update`` of the base repository with
        an arbitrary-``dict`` signature — an "update" that silently accepted
        mass assignment.

        Callers MUST build ``fields`` from named fields or a validated
        schema's ``model_dump()``, never from a raw request body.

        Returns ``None`` when no location assignment carries ``key``.
        """

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_tenant(self, tenant_key: str) -> list[LocationAssignment]: ...

    @abstractmethod
    def list_by_membership(self, membership_key: str) -> list[LocationAssignment]: ...

    @abstractmethod
    def get_by_membership_and_location(self, membership_key: str, location_key: str) -> LocationAssignment | None: ...

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...
