from abc import ABC, abstractmethod

from app.common.types import LocationKey, SiteKey, SlotKey
from app.domain.models.site import Location, Site, Slot


class ISiteRepository(ABC):
    @abstractmethod
    def get_all_sites(self, offset: int = 0, limit: int = 50) -> tuple[list[Site], int]:
        ...

    @abstractmethod
    def get_site_by_key(self, key: SiteKey) -> Site | None:
        ...

    @abstractmethod
    def create_site(self, site: Site) -> Site:
        ...

    @abstractmethod
    def update_site(self, key: SiteKey, site: Site) -> Site:
        ...

    @abstractmethod
    def delete_site(self, key: SiteKey) -> bool:
        ...

    @abstractmethod
    def get_locations_by_site(self, site_key: SiteKey) -> list[Location]:
        ...

    @abstractmethod
    def get_location_by_key(self, key: LocationKey) -> Location | None:
        ...

    @abstractmethod
    def create_location(self, location: Location) -> Location:
        ...

    @abstractmethod
    def update_location(self, key: LocationKey, location: Location) -> Location:
        ...

    @abstractmethod
    def delete_location(self, key: LocationKey) -> bool:
        ...

    @abstractmethod
    def get_location_children(self, parent_key: LocationKey) -> list[Location]:
        ...

    @abstractmethod
    def get_location_tree(self, site_key: SiteKey) -> list[Location]:
        ...

    @abstractmethod
    def get_slots_by_location(self, location_key: LocationKey) -> list[Slot]:
        ...

    @abstractmethod
    def get_slot_by_key(self, key: SlotKey) -> Slot | None:
        ...

    @abstractmethod
    def create_slot(self, slot: Slot) -> Slot:
        ...

    @abstractmethod
    def update_slot(self, key: SlotKey, slot: Slot) -> Slot:
        ...

    @abstractmethod
    def delete_slot(self, key: SlotKey) -> bool:
        ...
