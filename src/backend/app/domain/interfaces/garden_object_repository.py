from abc import ABC, abstractmethod

from app.common.types import GardenObjectKey, SiteKey
from app.domain.models.garden_object import GardenObject


class IGardenObjectRepository(ABC):
    """Persistence of the non-plantable plan objects of a site (REQ-053 §20.4).

    A garden object carries no ``tenant_key`` (E-01): every read here takes the
    tenant keyword-only without a default and resolves it through the object's
    site inside the query (§22.3 T-04, the #1714 shape for a by-key read a route
    feeds with a URL key), so a foreign or unknown object answers ``None`` / 404
    without a second lookup at the caller.
    """

    @abstractmethod
    def get_garden_objects_by_site(self, site_key: SiteKey, *, tenant_key: str) -> list[GardenObject]: ...

    @abstractmethod
    def get_garden_object_by_key(self, key: GardenObjectKey, *, tenant_key: str) -> GardenObject | None: ...

    @abstractmethod
    def get_garden_object_or_raise(self, key: GardenObjectKey, *, tenant_key: str) -> GardenObject: ...

    @abstractmethod
    def create_garden_object(self, garden_object: GardenObject) -> GardenObject: ...

    @abstractmethod
    def update_garden_object(self, key: GardenObjectKey, garden_object: GardenObject) -> GardenObject: ...

    @abstractmethod
    def delete_garden_object(self, key: GardenObjectKey) -> bool: ...
