from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.location_assignment import LocationAssignment


class ILocationAssignmentRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> LocationAssignment | None: ...

    @abstractmethod
    def create(self, assignment: LocationAssignment) -> LocationAssignment: ...

    @abstractmethod
    def update(self, key: str, data: dict) -> LocationAssignment | None: ...

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
