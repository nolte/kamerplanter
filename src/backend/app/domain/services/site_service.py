import asyncio
from collections.abc import Callable
from typing import Protocol

import structlog

from app.common.enums import FrostRisk
from app.common.exceptions import NotFoundError, ValidationError
from app.common.log_privacy import log_tenant
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import LocationKey, SiteKey, SlotKey
from app.domain.calculators.orientation_calculator import bed_axis
from app.domain.engines.frost_exposure_resolver import frost_risk_from_exposed
from app.domain.engines.water_mix_engine import WaterSourceValidator, WaterSourceWarning
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, SiteConditions, SiteWaterConfig, Slot
from app.domain.models.tank import Tank
from app.domain.services.fields_kept_on_edit import keep_stored_fields
from app.domain.services.location_ownership import require_owned_site, resolve_owned_slot
from app.domain.services.location_photo_service import LocationPhotoDiscard, release_location_photos

logger = structlog.get_logger(__name__)

#: ``Location`` fields the ``PUT /locations/{key}`` body (``LocationCreate``) does not carry and
#: that are written by the garden-plan paths (REQ-053 WP 1.7 — editor, batch, PATCH in WP 1.9).
#: The location view is a *full-replace* repository (#714), so a rebuilt model would erase every
#: one of them on an ordinary edit. ``PUT /locations`` therefore does **not write** them (#2623):
#: the repository leaves them out of the update, so they keep the value stored at write time —
#: a plan batch or ``PATCH`` that wrote them after the PUT's read is not reverted. The model
#: still takes them from the stored row (``keep_stored_fields``) so it validates as the stored
#: location does. ``bbox`` follows the stored ``geometry``; so does ``area_m2`` on a placed
#: location (GP-ACC-035), which is left unwritten then too. The one ``site_conditions`` write is
#: the ``frost_exposed`` mirror, a merge of ``microclimate.frost_risk`` alone.
LOCATION_FIELDS_KEPT_ON_EDIT: tuple[str, ...] = (
    # REQ-053 WP 10.11 (W-016): written by ``PATCH /locations`` only; the PUT body does not carry them.
    "adjacency_factor",
    "bbox",
    "bed_status",
    # REQ-053 WP 8.18: the bed's photos are written by ``LocationPhotoService`` only; an edit never resets them.
    "cover_photo_ref",
    "description",
    "geometry",
    "height_m",
    "irrigation_zone_key",
    "lighting",
    "locked",
    "notes",
    "photo_refs",
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
#: ``slot_role`` defaults to ``position`` and would overwrite a row or zone. ``PUT /slots``
#: therefore does **not write** them (#2639, the slot sibling of #2623): the repository leaves
#: them out of the update, so a ``PATCH /slots`` that wrote them after the PUT's read is not
#: reverted and a stored point geometry is never object-merged into a newer polygon. The model
#: still takes them from the stored row (``keep_stored_fields``) so it validates as the stored
#: slot does (the capacity bound follows ``slot_role``).
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
    "thinned_at",
)

#: What ``PUT /slots/{key}`` leaves out of its write (#2639): the plan fields plus the two
#: server-maintained columns no edit body carries — the occupancy (plant and planting-run
#: services) and ``last_sanitization`` (a ``None`` on the rebuilt model, never the body's).
SLOT_COLUMNS_A_PUT_LEAVES: tuple[str, ...] = (*SLOT_FIELDS_KEPT_ON_EDIT, "currently_occupied", "last_sanitization")


def frost_risk_to_mirror(location: Location, stored: Location | None) -> FrostRisk | None:
    """The ``microclimate.frost_risk`` a changed legacy ``frost_exposed`` stands for, ``None`` if unchanged (WP 3.9).

    ``stored`` is the location as it was (``None`` on create). Only a change counts, so an edit that sends
    the unchanged boolean never overwrites a risk somebody entered on the new field.
    """
    before = stored.frost_exposed if stored is not None else None
    if location.frost_exposed == before:
        return None
    return frost_risk_from_exposed(location.frost_exposed)


def mirror_frost_exposed(location: Location, stored: Location | None) -> None:
    """Carry a changed legacy ``frost_exposed`` into ``location.site_conditions.microclimate.frost_risk`` (WP 3.9)."""
    frost_risk = frost_risk_to_mirror(location, stored)
    if frost_risk is None:
        return
    current = location.site_conditions or SiteConditions()
    location.site_conditions = current.with_frost_risk(frost_risk)


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
        photos: Callable[[], LocationPhotoDiscard] | None = None,
    ) -> None:
        self._repo = site_repo
        self._water_validator = WaterSourceValidator()
        # #1872 C4: the tank a location names, resolved under the tenant.
        self._tank_repo = tank_repo
        # #2545: the underlay picture of a deleted site plan goes with it (B3: unless another carrier names it).
        # A provider, built only by a delete that has a picture to discard: every other site route stays free of
        # the attachment service (object storage, quota, rendition claims).
        self._underlay = underlay
        # WP 8.18: the bed photos of the deleted locations, the same way (unless another carrier names them).
        self._photos = photos

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

        The garden-planning thresholds (REQ-053 GP-FR-164/166, WP 8.24; the window radius GP-FR-181, WP 10.7)
        are optional in the edit body: a body that does not send them (``None``) keeps the stored ones, so a
        client that does not know them - the MCP tools, an older form - never resets a configured value. Sending
        the defaults is how they are reset.
        """
        existing = self.get_site(key, tenant_key=tenant_key)
        site.tenant_key = tenant_key
        site.weather_source_priority = list(existing.weather_source_priority)
        if site.sun_class_thresholds is None:
            site.sun_class_thresholds = existing.sun_class_thresholds
        if site.reach_thresholds is None:
            site.reach_thresholds = existing.reach_thresholds
        if site.window_thresholds is None:
            site.window_thresholds = existing.window_thresholds
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
        earlier read. **The site is gone once the transaction commits**, so a failing discard (storage, the
        reference scan's time budget, the database) is logged and the delete still succeeds: a 500 there made
        the client retry into a 404 that never reaches the picture again.

        The repository calls are synchronous (python-arango); they run in a worker thread so the async route
        does not block the event loop with the cascade transaction.
        """
        await asyncio.to_thread(self.get_site, key, tenant_key=tenant_key)
        deletion = await asyncio.to_thread(self._repo.delete_site, key, tenant_key=tenant_key, user_key=user_key)
        if deletion.underlay_attachment_key is not None:
            await self._discard_underlay(key, deletion.underlay_attachment_key, tenant_key=tenant_key)
        await release_location_photos(self._photos, deletion.location_photo_refs, tenant_key=tenant_key)
        return True

    async def _discard_underlay(self, site_key: SiteKey, attachment_key: str, *, tenant_key: str) -> None:
        """Discard the deleted plan's picture after the commit; a failure is logged, never raised (#2545)."""
        if self._underlay is None:
            logger.warning("site.underlay_not_discarded", site_key=site_key)
            return
        try:
            await self._underlay().discard(attachment_key, keep=None, tenant_key=tenant_key)
        except Exception as exc:  # noqa: BLE001 — the site delete has committed; its response must not turn into a 500
            logger.warning(
                "site.underlay_discard_failed",
                tenant=log_tenant(tenant_key),
                site_key=site_key,
                attachment_id=attachment_key,
                error_type=type(exc).__name__,
            )

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
        not written (#2623): the edit body does not carry them, and the copy read here
        may be older than a plan batch or a ``PATCH`` that wrote them since — writing
        it back reverted that write without a 409. The repository leaves them out of
        the update, so they keep the values stored at write time, and returns the
        location as stored, which is what the response shows. On a placed location
        ``area_m2`` derives from the stored geometry (GP-ACC-035) and is not written
        either; on an unplaced one the body's ``area_m2`` stands. The model still
        takes the fields from the stored row and is re-validated, so the write is
        checked against the location as it was read.

        A changed ``frost_exposed`` is mirrored into ``site_conditions`` as the one
        sub-path ``microclimate.frost_risk`` (WP 3.9), merged into the stored value:
        the sun profile and every other part stay as stored.
        """
        existing = self.get_location(key, tenant_key=tenant_key)
        keep_stored_fields(location, existing, LOCATION_FIELDS_KEPT_ON_EDIT)
        frost_risk = frost_risk_to_mirror(location, existing)
        location = Location.model_validate(location.model_dump(by_alias=True))
        untouched = LOCATION_FIELDS_KEPT_ON_EDIT
        if existing.geometry is not None:
            untouched = (*untouched, "area_m2")
            if bed_axis(existing.geometry, 0.0) is not None:
                # GP-FR-017: a placed bed with a long axis has a derived orientation, no manually maintained one.
                untouched = (*untouched, "orientation")
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
        return self._repo.update_location(key, location, untouched=untouched, frost_risk=frost_risk)

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
        # Ownership first: a legacy slot of another tenant must answer 404, not the 409 of its read (#2709).
        slot, _location = resolve_owned_slot(self._repo, key, tenant_key)
        return slot

    def create_slot(self, slot: Slot, *, tenant_key: str) -> Slot:
        """Create a slot in a location of ``tenant_key``."""
        self.get_location(slot.location_key, tenant_key=tenant_key)
        return self._repo.create_slot(slot)

    def update_slot(self, key: SlotKey, slot: Slot, *, tenant_key: str) -> Slot:
        """Rewrite a slot of ``tenant_key``; the location it names is resolved under the tenant too (#1871 B1).

        Only the body's columns are written (#2639). ``currently_occupied`` is set by
        placing a plant or a planting run, never by the edit body, which does not
        carry it: the rebuilt model held ``False`` and every slot edit freed an
        occupied slot for the next batch placement (#2181). The garden-plan fields
        (:data:`SLOT_FIELDS_KEPT_ON_EDIT`) are the editor's. Neither is written: the
        copy read here may be older than an occupation write or a ``PATCH /slots``
        that landed since, and writing it back reverted that write without a 409.
        The model still takes them from the stored slot, so it validates as the slot
        was read, and the repository returns the slot as stored after the write.
        """
        existing = self.get_slot(key, tenant_key=tenant_key)
        self.get_location(slot.location_key, tenant_key=tenant_key)
        slot.currently_occupied = existing.currently_occupied
        keep_stored_fields(slot, existing, SLOT_FIELDS_KEPT_ON_EDIT)
        return self._repo.update_slot(key, slot, untouched=SLOT_COLUMNS_A_PUT_LEAVES)

    def delete_slot(self, key: SlotKey, *, tenant_key: str) -> bool:
        self.get_slot(key, tenant_key=tenant_key)
        return self._repo.delete_slot(key)
