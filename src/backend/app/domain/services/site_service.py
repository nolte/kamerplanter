from typing import Protocol

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import LocationKey, SiteKey, SlotKey
from app.domain.engines.water_mix_engine import WaterSourceValidator, WaterSourceWarning
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, SiteWaterConfig, Slot
from app.domain.models.tank import Tank
from app.domain.services.location_ownership import require_owned_site, resolve_owned_slot


class _TankSource(Protocol):
    def get_by_key(self, key: str) -> Tank | None: ...


class SiteService:
    def __init__(self, site_repo: ISiteRepository, *, tank_repo: _TankSource | None = None) -> None:
        self._repo = site_repo
        self._water_validator = WaterSourceValidator()
        # #1872 C4: the tank a location names, resolved under the tenant.
        self._tank_repo = tank_repo

    def _require_owned_tank(self, tank_key: str, tenant_key: str) -> None:
        """404 unless *tank_key* is a tank of *tenant_key* — fail closed without a repository (#1872 C4)."""
        tank = self._tank_repo.get_by_key(tank_key) if self._tank_repo is not None and tenant_key else None
        if tank is None or tank.tenant_key != tenant_key:
            raise NotFoundError("Tank", tank_key)

    # --- Sites ---

    def list_sites(self, offset: int = 0, limit: int = 50, tenant_key: str = "") -> tuple[list[Site], int]:
        return self._repo.get_all_sites(offset, limit, tenant_key=tenant_key)

    def get_site(self, key: SiteKey, tenant_key: str = "") -> Site:
        site = self._repo.get_site_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(site, tenant_key, "Site")
        return site

    def create_site(self, site: Site) -> Site:
        return self._repo.create_site(site)

    def update_site(self, key: SiteKey, site: Site) -> Site:
        self.get_site(key)
        return self._repo.update_site(key, site)

    def delete_site(self, key: SiteKey) -> bool:
        self.get_site(key)
        return self._repo.delete_site(key)

    def get_water_config(self, key: SiteKey) -> SiteWaterConfig | None:
        site = self.get_site(key)
        return site.water_config

    def get_water_warnings(self, site: Site) -> list[WaterSourceWarning]:
        if site.water_config is None:
            return []
        return self._water_validator.validate_all(
            tap=site.water_config.tap_water_profile,
            ro=site.water_config.ro_water_profile,
        )

    # --- Locations ---

    def list_locations(self, site_key: SiteKey) -> list[Location]:
        self.get_site(site_key)
        return self._repo.get_locations_by_site(site_key)

    def get_location(self, key: LocationKey, tenant_key: str = "") -> Location:
        """A location, optionally required to belong to ``tenant_key``.

        Anchored on the parent site (#1397). This used to compare against
        ``location.tenant_key``, which the write path never fills — so with a
        tenant key supplied it refused **every** location including the caller's
        own, and MCP ``set_plant_location`` answered 404 to every legitimate move.
        """
        location = self._repo.get_location_or_raise(key)
        if tenant_key:
            require_owned_site(self._repo, location.site_key, tenant_key, "Location", key)
        return location

    def create_location(self, location: Location, *, tenant_key: str) -> Location:
        """Create a location, nested under a parent of the same tenant (#1864 bundle, L1).

        The parent used to be resolved without a tenant and its ``site_key``
        copied over the caller's verified one, so a location could be grafted
        into another tenant's tree. Parent and site are both resolved under
        ``tenant_key`` now (keyword-only without a default); a foreign or unknown
        parent answers 404.
        """
        if location.parent_location_key:
            parent = self.get_location(location.parent_location_key, tenant_key=tenant_key)
            location.depth = parent.depth + 1
            parent_path = parent.path or parent.name.lower().replace(" ", "_")
            location.path = f"{parent_path}/{location.name.lower().replace(' ', '_')}"
            location.site_key = parent.site_key
        else:
            location.depth = 0
            location.path = location.name.lower().replace(" ", "_")
        self.get_site(location.site_key, tenant_key=tenant_key)
        if location.tank_key:
            self._require_owned_tank(location.tank_key, tenant_key)
        return self._repo.create_location(location)

    def update_location(self, key: LocationKey, location: Location, *, tenant_key: str) -> Location:
        """Update a location; the parent and the tank it names are resolved under the tenant (#1872 C4).

        The body's ``parent_location_key`` and ``tank_key`` were stored as given —
        only ``site_key`` was checked. A foreign or unknown reference answers 404;
        a location cannot be its own parent.
        """
        self.get_location(key, tenant_key=tenant_key)
        if location.parent_location_key:
            if location.parent_location_key == key:
                raise ValidationError("A location cannot be its own parent.")
            self.get_location(location.parent_location_key, tenant_key=tenant_key)
        if location.tank_key:
            self._require_owned_tank(location.tank_key, tenant_key)
        return self._repo.update_location(key, location)

    def delete_location(self, key: LocationKey) -> bool:
        self.get_location(key)
        return self._repo.delete_location(key)

    def list_location_children(self, parent_key: LocationKey) -> list[Location]:
        self.get_location(parent_key)
        return self._repo.get_location_children(parent_key)

    def get_location_tree(self, site_key: SiteKey, *, tenant_key: str) -> list[Location]:
        """A site's location hierarchy, scoped to ``tenant_key`` (#927).

        The site is verified against the tenant here *and* the traversal carries
        the tenant predicate, so neither layer alone has to hold.
        """
        self.get_site(site_key, tenant_key=tenant_key)
        return self._repo.get_location_tree(site_key, tenant_key=tenant_key)

    # --- Slots ---

    def list_slots(self, location_key: LocationKey) -> list[Slot]:
        self.get_location(location_key)
        return self._repo.get_slots_by_location(location_key)

    def get_slot(self, key: SlotKey, tenant_key: str = "") -> Slot:
        """A slot, optionally required to belong to ``tenant_key``.

        Two hops — slot → location → site — for the reason ``get_location`` gives:
        ``Slot.tenant_key`` is as empty as ``Location.tenant_key`` (#1397).
        """
        slot = self._repo.get_slot_or_raise(key)
        if tenant_key:
            resolve_owned_slot(self._repo, key, tenant_key)
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
