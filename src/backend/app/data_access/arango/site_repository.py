from arango.database import StandardDatabase

from app.common.types import LocationKey, SiteKey, SlotKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, Slot


class ArangoSiteRepository(ISiteRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SITES)

    # ── Site CRUD ─────────────────────────────────────────────────────

    def get_all_sites(self, offset: int = 0, limit: int = 50) -> tuple[list[Site], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [Site(**doc) for doc in docs], total

    def get_site_by_key(self, key: SiteKey) -> Site | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Site(**doc) if doc else None

    def create_site(self, site: Site) -> Site:
        doc = BaseArangoRepository.create(self, site)
        return Site(**doc)

    def update_site(self, key: SiteKey, site: Site) -> Site:
        doc = BaseArangoRepository.update(self, key, site)
        return Site(**doc)

    def delete_site(self, key: SiteKey) -> bool:
        site_id = f"{col.SITES}/{key}"
        # Remove associated CONTAINS edges and cascade to locations
        results = self.get_edges(col.CONTAINS, site_id, direction="outbound")
        for result in results:
            location_doc = result["vertex"]
            location_key = location_doc.get("_key", location_doc.get("_id", "").split("/")[-1])
            self.delete_location(location_key)
        self.delete_edges(col.CONTAINS, from_id=site_id)
        return BaseArangoRepository.delete(self, key)

    # ── Location CRUD ─────────────────────────────────────────────────

    def get_locations_by_site(self, site_key: SiteKey) -> list[Location]:
        site_id = f"{col.SITES}/{site_key}"
        results = self.get_edges(col.CONTAINS, site_id, direction="outbound")
        return [Location(**self._from_doc(r["vertex"])) for r in results]

    def get_location_by_key(self, key: LocationKey) -> Location | None:
        repo = BaseArangoRepository(self._db, col.LOCATIONS)
        doc = repo.get_by_key(key)
        return Location(**doc) if doc else None

    def create_location(self, location: Location) -> Location:
        repo = BaseArangoRepository(self._db, col.LOCATIONS)
        doc = repo.create(location)
        if location.site_key:
            site_id = f"{col.SITES}/{location.site_key}"
            location_id = f"{col.LOCATIONS}/{doc['_key']}"
            self.create_edge(col.CONTAINS, site_id, location_id)
        return Location(**doc)

    def update_location(self, key: LocationKey, location: Location) -> Location:
        repo = BaseArangoRepository(self._db, col.LOCATIONS)
        doc = repo.update(key, location)
        return Location(**doc)

    def delete_location(self, key: LocationKey) -> bool:
        location_id = f"{col.LOCATIONS}/{key}"
        # Remove associated HAS_SLOT edges and cascade to slots
        results = self.get_edges(col.HAS_SLOT, location_id, direction="outbound")
        for result in results:
            slot_doc = result["vertex"]
            slot_key = slot_doc.get("_key", slot_doc.get("_id", "").split("/")[-1])
            self._delete_slot_internal(slot_key)
        self.delete_edges(col.HAS_SLOT, from_id=location_id)
        return BaseArangoRepository(self._db, col.LOCATIONS).delete(key)

    # ── Slot CRUD ─────────────────────────────────────────────────────

    def get_slots_by_location(self, location_key: LocationKey) -> list[Slot]:
        location_id = f"{col.LOCATIONS}/{location_key}"
        results = self.get_edges(col.HAS_SLOT, location_id, direction="outbound")
        return [Slot(**self._from_doc(r["vertex"])) for r in results]

    def get_slot_by_key(self, key: SlotKey) -> Slot | None:
        repo = BaseArangoRepository(self._db, col.SLOTS)
        doc = repo.get_by_key(key)
        return Slot(**doc) if doc else None

    def create_slot(self, slot: Slot) -> Slot:
        repo = BaseArangoRepository(self._db, col.SLOTS)
        doc = repo.create(slot)
        if slot.location_key:
            location_id = f"{col.LOCATIONS}/{slot.location_key}"
            slot_id = f"{col.SLOTS}/{doc['_key']}"
            self.create_edge(col.HAS_SLOT, location_id, slot_id)
        return Slot(**doc)

    def update_slot(self, key: SlotKey, slot: Slot) -> Slot:
        repo = BaseArangoRepository(self._db, col.SLOTS)
        doc = repo.update(key, slot)
        return Slot(**doc)

    def delete_slot(self, key: SlotKey) -> bool:
        return self._delete_slot_internal(key)

    def _delete_slot_internal(self, key: SlotKey) -> bool:
        slot_id = f"{col.SLOTS}/{key}"
        self.delete_edges(col.HAS_SLOT, from_id=f"{col.LOCATIONS}/%", to_id=slot_id)
        self.delete_edges(col.ADJACENT_TO, from_id=slot_id)
        self.delete_edges(col.FILLED_WITH, from_id=slot_id)
        return BaseArangoRepository(self._db, col.SLOTS).delete(key)
