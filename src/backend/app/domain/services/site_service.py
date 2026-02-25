from app.common.exceptions import NotFoundError
from app.common.types import LocationKey, SiteKey, SlotKey
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, Slot


class SiteService:
    def __init__(self, site_repo: ISiteRepository) -> None:
        self._repo = site_repo

    # --- Sites ---

    def list_sites(self, offset: int = 0, limit: int = 50) -> tuple[list[Site], int]:
        return self._repo.get_all_sites(offset, limit)

    def get_site(self, key: SiteKey) -> Site:
        site = self._repo.get_site_by_key(key)
        if site is None:
            raise NotFoundError("Site", key)
        return site

    def create_site(self, site: Site) -> Site:
        return self._repo.create_site(site)

    def update_site(self, key: SiteKey, site: Site) -> Site:
        self.get_site(key)
        return self._repo.update_site(key, site)

    def delete_site(self, key: SiteKey) -> bool:
        self.get_site(key)
        return self._repo.delete_site(key)

    # --- Locations ---

    def list_locations(self, site_key: SiteKey) -> list[Location]:
        self.get_site(site_key)
        return self._repo.get_locations_by_site(site_key)

    def get_location(self, key: LocationKey) -> Location:
        location = self._repo.get_location_by_key(key)
        if location is None:
            raise NotFoundError("Location", key)
        return location

    def create_location(self, location: Location) -> Location:
        self.get_site(location.site_key)
        return self._repo.create_location(location)

    def update_location(self, key: LocationKey, location: Location) -> Location:
        self.get_location(key)
        return self._repo.update_location(key, location)

    def delete_location(self, key: LocationKey) -> bool:
        self.get_location(key)
        return self._repo.delete_location(key)

    # --- Slots ---

    def list_slots(self, location_key: LocationKey) -> list[Slot]:
        self.get_location(location_key)
        return self._repo.get_slots_by_location(location_key)

    def get_slot(self, key: SlotKey) -> Slot:
        slot = self._repo.get_slot_by_key(key)
        if slot is None:
            raise NotFoundError("Slot", key)
        return slot

    def create_slot(self, slot: Slot) -> Slot:
        self.get_location(slot.location_key)
        return self._repo.create_slot(slot)

    def update_slot(self, key: SlotKey, slot: Slot) -> Slot:
        self.get_slot(key)
        return self._repo.update_slot(key, slot)

    def delete_slot(self, key: SlotKey) -> bool:
        self.get_slot(key)
        return self._repo.delete_slot(key)
