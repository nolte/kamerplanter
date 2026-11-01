from collections.abc import Callable
from typing import Protocol

import structlog

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import LocationKey, SiteKey, SlotKey
from app.domain.engines.frost_exposure_resolver import frost_risk_from_exposed
from app.domain.engines.water_mix_engine import WaterSourceValidator, WaterSourceWarning
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, SiteConditions, SiteWaterConfig, Slot
from app.domain.models.tank import Tank
from app.domain.services.fields_kept_on_edit import keep_stored_fields
from app.domain.services.location_ownership import require_owned_site, resolve_owned_slot

logger = structlog.get_logger(__name__)

#: ``Location`` fields the ``PUT /locations/{key}`` body (``LocationCreate``) does not carry and
#: that are written by the garden-plan paths (REQ-053 WP 1.7 — editor, batch, PATCH in WP 1.9).
#: The location view is a *full-replace* repository (#714), so a rebuilt model would erase every
#: one of them on an ordinary edit; they are taken from the stored row instead.
#: ``area_m2`` and ``bbox`` are re-derived from the kept ``geometry`` afterwards (GP-ACC-035).
LOCATION_FIELDS_KEPT_ON_EDIT: tuple[str, ...] = (
    "bbox",
    "bed_status",
    "description",
    "geometry",
    "height_m",
    "irrigation_zone_key",
    "locked",
    "notes",
    "pitch_m",
    "rotation_enabled",
    "rotation_exempt",
    "site_conditions",
    "soil_profile",
    "sun_exposure",
    "template_key",
    "z_order",
)

#: ``Slot`` fields the ``PUT /slots/{key}`` body (``SlotCreate``) does not carry and that the
#: garden-plan paths write (REQ-053 WP 1.7). The slot view merges (a ``None`` is dropped), but
#: ``slot_role`` defaults to ``position`` and would overwrite a row or zone — all are kept.
SLOT_FIELDS_KEPT_ON_EDIT: tuple[str, ...] = (
    "archived_at",
    "container_volume_l",
    "geometry",
    "geometry_source",
    "planned_spacing_cm",
    "row_index",
    "sequence",
    "slot_role",
    "sown_at",
)


def mirror_frost_exposed(location: Location, stored: Location | None) -> None:
    """Carry a changed legacy ``frost_exposed`` into ``site_conditions.microclimate.frost_risk`` (WP 3.9).

    ``stored`` is the location as it was (``None`` on create). Only a change counts, so an edit that sends
    the unchanged boolean never overwrites a risk somebody entered on the new field.
    """
    before = stored.frost_exposed if stored is not None else None
    if location.frost_exposed == before:
        return
    current = location.site_conditions or SiteConditions()
    location.site_conditions = current.with_frost_risk(frost_risk_from_exposed(location.frost_exposed))


def place_in_tree(location: Location, parent: Location | None) -> None:
    """Derive ``depth`` and ``path`` of *location* from its *parent* (``None`` = directly on the site).

    Module-level so the garden-plan batch (REQ-053 WP 1.8) places a created location exactly as
    ``POST /locations`` does.
    """
    segment = location.name.lower().replace(" ", "_")
    if parent is None:
        location.depth = 0
        location.path = segment
        return
    location.depth = parent.depth + 1
    parent_path = parent.path or parent.name.lower().replace(" ", "_")
    location.path = f"{parent_path}/{segment}"


class _TankSource(Protocol):
    def get_by_key(self, key: str) -> Tank | None: ...


class _UnderlayDiscard(Protocol):
    """``GardenPlanUnderlayService.discard``: delete a picture of the tenant unless a carrier still names it."""

    async def discard(self, attachment_key: str | None, *, keep: str | None, tenant_key: str) -> None: ...


class SiteService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        *,
        tank_repo: _TankSource | None = None,
        underlay: Callable[[], _UnderlayDiscard] | None = None,
    ) -> None:
        self._repo = site_repo
        self._water_validator = WaterSourceValidator()
        # #1872 C4: the tank a location names, resolved under the tenant.
        self._tank_repo = tank_repo
        # #2545: the underlay picture of a deleted site plan goes with it (B3: unless another carrier names it).
        # A provider, built only by a delete that has a picture to discard: every other site route stays free of
        # the attachment service (object storage, quota, rendition claims).
        self._underlay = underlay

    def _require_owned_tank(self, tank_key: str, tenant_key: str) -> None:
        """404 unless *tank_key* is a tank of *tenant_key* — fail closed without a repository (#1872 C4)."""
        tank = self._tank_repo.get_by_key(tank_key) if self._tank_repo is not None and tenant_key else None
        if tank is None or tank.tenant_key != tenant_key:
            raise NotFoundError("Tank", tank_key)

    # --- Sites ---

    def list_sites(self, offset: int = 0, limit: int = 50, tenant_key: str = "") -> tuple[list[Site], int]:
        return self._repo.get_all_sites(offset, limit, tenant_key=tenant_key)

    def list_sites_window(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> list[Site]:
        """One ``_key``-ordered page of the tenant's sites without the count query (MT-035, #2131)."""
        return self._repo.list_sites_window(offset, limit, tenant_key=tenant_key)

    # #2107 (MT-010): every method below that addresses a site, location or slot by
    # key takes ``tenant_key`` keyword-only without a default and resolves the key
    # under it itself. The routers used to call ``get_site(key, tenant_key=…)`` and
    # then an unscoped ``update_site(key, …)`` — check-then-act, correct only as long
    # as every handler and MCP tool remembered the first call.

    def get_site(self, key: SiteKey, *, tenant_key: str) -> Site:
        site = self._repo.get_site_or_raise(key)
        verify_tenant_ownership(site, tenant_key, "Site")
        return site

    def create_site(self, site: Site) -> Site:
        return self._repo.create_site(site)

    def update_site(self, key: SiteKey, site: Site, *, tenant_key: str) -> Site:
        """Rewrite a site of ``tenant_key``; ownership stays with it whatever the body says.

        ``weather_source_priority`` is the denormalized view of the site's
        weather-source selection, written only by ``WeatherSourceService.save_config``
        (REQ-046 §2.1). The edit body does not carry it, so the rebuilt model held
        ``[]`` and every site edit erased the view (#2181) — it is taken from the
        stored site instead.
        """
        existing = self.get_site(key, tenant_key=tenant_key)
        site.tenant_key = tenant_key
        site.weather_source_priority = list(existing.weather_source_priority)
        if existing.plan is not None and existing.plan.boundary is not None:
            # REQ-053 §20.2: with a boundary the area is derived from it. ``SiteCreate`` carries a
            # ``total_area_m2`` (default 0) the model cannot tell from a typed value, and the repository
            # merge would write it over the derived one on every ordinary site edit.
            site.total_area_m2 = existing.total_area_m2
        return self._repo.update_site(key, site)

    async def delete_site(self, key: SiteKey, *, tenant_key: str, user_key: str) -> bool:
        """Delete the tenant's site with its structure; the care and change history stays (#2513).

        ``user_key`` is the deleting account, recorded on the plan audit row the repository writes in the same
        transaction (REQ-053 §20.13 SR-011). The repository reads the site under ``tenant_key`` once more inside
        that transaction (MT-010, #2107), so the ownership predicate does not rest on this read alone.

        The underlay picture of the deleted plan (an aerial photo can reveal where someone lives, GP-FR-033 §26)
        is discarded after the commit, through the underlay's own rule: deleted unless another site or carrier
        still names it (#2545). The picture the transaction read is the one discarded, not this method's
        earlier read.
        """
        self.get_site(key, tenant_key=tenant_key)
        deletion = self._repo.delete_site(key, tenant_key=tenant_key, user_key=user_key)
        if deletion.underlay_attachment_key is not None:
            if self._underlay is None:
                logger.warning("site.underlay_not_discarded", site_key=key)
            else:
                await self._underlay().discard(deletion.underlay_attachment_key, keep=None, tenant_key=tenant_key)
        return True

    def get_water_config(self, key: SiteKey, *, tenant_key: str) -> SiteWaterConfig | None:
        site = self.get_site(key, tenant_key=tenant_key)
        return site.water_config

    def get_water_warnings(self, site: Site) -> list[WaterSourceWarning]:
        if site.water_config is None:
            return []
        return self._water_validator.validate_all(
            tap=site.water_config.tap_water_profile,
            ro=site.water_config.ro_water_profile,
        )

    # --- Locations ---

    def list_locations(self, site_key: SiteKey, *, tenant_key: str) -> list[Location]:
        self.get_site(site_key, tenant_key=tenant_key)
        return self._repo.get_locations_by_site(site_key)

    def get_location(self, key: LocationKey, *, tenant_key: str) -> Location:
        """A location of ``tenant_key`` — anchored on its site, 404 otherwise.

        Anchored on the parent site (#1397). This used to compare against
        ``location.tenant_key``, which the write path never filled (the field is
        gone since #2107) — so with a tenant key supplied it refused **every**
        location including the caller's own, and MCP ``set_plant_location``
        answered 404 to every legitimate move.
        """
        location = self._repo.get_location_or_raise(key)
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
            location.site_key = parent.site_key
            self._place_in_tree(location, parent)
        else:
            self._place_in_tree(location, None)
        self.get_site(location.site_key, tenant_key=tenant_key)
        if location.tank_key:
            self._require_owned_tank(location.tank_key, tenant_key)
        mirror_frost_exposed(location, None)
        return self._repo.create_location(location)

    @staticmethod
    def _place_in_tree(location: Location, parent: Location | None) -> None:
        """Derive ``depth`` and ``path`` from the parent — the fields no request body carries."""
        place_in_tree(location, parent)

    def update_location(self, key: LocationKey, location: Location, *, tenant_key: str) -> Location:
        """Update a location; the parent and the tank it names are resolved under the tenant (#1872 C4).

        The body's ``parent_location_key`` and ``tank_key`` were stored as given —
        only ``site_key`` was checked. A foreign or unknown reference answers 404;
        a location cannot be its own parent.

        ``depth`` and ``path`` are derived as on create: the body does not carry
        them, so the rebuilt model held ``0`` / ``""`` and every edit turned a nested
        location into a root without a path (#2181). Descendants keep their stored
        path when a location is renamed or moved.

        The garden-plan fields (REQ-053, :data:`LOCATION_FIELDS_KEPT_ON_EDIT`) are
        taken from the stored location: the edit body does not carry them and the
        repository replaces the whole document, so a routine rename would otherwise
        unplace the bed and drop its soil profile. ``area_m2`` follows the kept
        geometry (GP-ACC-035), which is why the model is re-validated afterwards.
        """
        existing = self.get_location(key, tenant_key=tenant_key)
        keep_stored_fields(location, existing, LOCATION_FIELDS_KEPT_ON_EDIT)
        mirror_frost_exposed(location, existing)
        location = Location.model_validate(location.model_dump(by_alias=True))
        parent: Location | None = None
        # The body's site too (#2107): the router used to check it before this call.
        self.get_site(location.site_key, tenant_key=tenant_key)
        if location.parent_location_key:
            parent = self.get_location(location.parent_location_key, tenant_key=tenant_key)
            # Not itself, not one of its own descendants (/code-review of #1899): a
            # loop A→B→A made every ancestor walk — the location page's breadcrumb —
            # run forever. And within the location's own site, as create requires.
            if parent.site_key != location.site_key:
                raise ValidationError("A parent location must belong to the same site.")
            self._refuse_parent_cycle(key, parent)
        self._place_in_tree(location, parent)
        if location.tank_key:
            self._require_owned_tank(location.tank_key, tenant_key)
        return self._repo.update_location(key, location)

    def _refuse_parent_cycle(self, key: LocationKey, parent: Location) -> None:
        """422 when *parent* is *key* itself or lies below it — the walk up from the parent reaches *key*."""
        seen: set[str] = set()
        current: Location | None = parent
        while current is not None and current.key and current.key not in seen:
            if current.key == key:
                raise ValidationError("A location cannot be placed below itself.")
            seen.add(current.key)
            current = (
                self._repo.get_location_by_key(current.parent_location_key) if current.parent_location_key else None
            )

    def delete_location(self, key: LocationKey, *, tenant_key: str) -> bool:
        self.get_location(key, tenant_key=tenant_key)
        return self._repo.delete_location(key)

    def list_location_children(self, parent_key: LocationKey, *, tenant_key: str) -> list[Location]:
        self.get_location(parent_key, tenant_key=tenant_key)
        return self._repo.get_location_children(parent_key)

    def get_location_tree(self, site_key: SiteKey, *, tenant_key: str) -> list[Location]:
        """A site's location hierarchy, scoped to ``tenant_key`` (#927).

        The site is verified against the tenant here *and* the traversal carries
        the tenant predicate, so neither layer alone has to hold.
        """
        self.get_site(site_key, tenant_key=tenant_key)
        return self._repo.get_location_tree(site_key, tenant_key=tenant_key)

    # --- Slots ---

    def list_slots(self, location_key: LocationKey, *, tenant_key: str) -> list[Slot]:
        self.get_location(location_key, tenant_key=tenant_key)
        return self._repo.get_slots_by_location(location_key)

    def get_slot(self, key: SlotKey, *, tenant_key: str) -> Slot:
        """A slot of ``tenant_key`` — two hops, slot → location → site (#1397), 404 otherwise."""
        slot = self._repo.get_slot_or_raise(key)
        resolve_owned_slot(self._repo, key, tenant_key)
        return slot

    def create_slot(self, slot: Slot, *, tenant_key: str) -> Slot:
        """Create a slot in a location of ``tenant_key``."""
        self.get_location(slot.location_key, tenant_key=tenant_key)
        return self._repo.create_slot(slot)

    def update_slot(self, key: SlotKey, slot: Slot, *, tenant_key: str) -> Slot:
        """Rewrite a slot of ``tenant_key``; the location it names is resolved under the tenant too (#1871 B1).

        ``currently_occupied`` is set by placing a plant or a planting run, never by
        the edit body, which does not carry it: the rebuilt model held ``False`` and
        every slot edit freed an occupied slot for the next batch placement (#2181).
        It is taken from the stored slot.
        """
        existing = self.get_slot(key, tenant_key=tenant_key)
        self.get_location(slot.location_key, tenant_key=tenant_key)
        slot.currently_occupied = existing.currently_occupied
        # The garden-plan fields (REQ-053 WP 1.7) are the editor's, not the edit body's.
        keep_stored_fields(slot, existing, SLOT_FIELDS_KEPT_ON_EDIT)
        return self._repo.update_slot(key, slot)

    def delete_slot(self, key: SlotKey, *, tenant_key: str) -> bool:
        self.get_slot(key, tenant_key=tenant_key)
        return self._repo.delete_slot(key)
