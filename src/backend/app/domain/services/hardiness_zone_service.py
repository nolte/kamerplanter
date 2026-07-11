"""REQ-039 — hardiness-zone service: catalog access + per-site auto-fill.

Bridges the pure :mod:`hardiness_zone_resolver` engine to persistence: it reads
a site's REQ-041 climate normals, derives the USDA half-zone, writes it back onto
the site (replacing the manual free-text ``climate_zone`` with a structured,
provenance-tracked ``hardiness_zone``) and maintains the ``located_in_zone`` edge.

Tenant isolation is fail-closed: a site whose ``tenant_key`` does not match the
caller is treated as absent (``NotFoundError``), never silently resolved.
A ``manual`` zone assignment is never overwritten by the automatic refresh.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.common.exceptions import NotFoundError, ValidationError
from app.data_access.arango.hardiness_zone_repository import ArangoHardinessZoneRepository
from app.domain.engines.hardiness_zone_resolver import derive_from_climate_normals
from app.domain.interfaces.climate_normal_repository import IClimateNormalRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.hardiness_zone import HardinessZone
from app.domain.models.site import Site


class HardinessZoneService:
    def __init__(
        self,
        zone_repo: ArangoHardinessZoneRepository,
        site_repo: ISiteRepository,
        climate_normal_repo: IClimateNormalRepository,
    ) -> None:
        self._zone_repo = zone_repo
        self._site_repo = site_repo
        self._climate_normal_repo = climate_normal_repo

    # ── Catalog ──────────────────────────────────────────────────────────

    def list_zones(self) -> list[HardinessZone]:
        return self._zone_repo.get_all_zones()

    def get_zone(self, zone: str) -> HardinessZone:
        result = self._zone_repo.get_by_zone(zone)
        if result is None:
            raise NotFoundError("HardinessZone", zone)
        return result

    def catalog_entry(self, zone: str | None) -> HardinessZone | None:
        """Return the catalog entry for a zone label, or ``None`` (non-raising)."""
        if not zone:
            return None
        return self._zone_repo.get_by_zone(zone)

    # ── Per-site ─────────────────────────────────────────────────────────

    def _load_site(self, site_key: str, tenant_key: str) -> Site:
        """Tenant-guarded site load (fail-closed: foreign/unknown → 404)."""
        site = self._site_repo.get_site_by_key(site_key)
        if site is None or site.tenant_key != tenant_key:
            raise NotFoundError("Site", site_key)
        return site

    def get_site_hardiness(self, site_key: str, tenant_key: str) -> tuple[Site, HardinessZone | None]:
        """Return the site plus its resolved zone catalog entry (or ``None``)."""
        site = self._load_site(site_key, tenant_key)
        return site, self.catalog_entry(site.hardiness_zone)

    def resolve_for_site(self, site_key: str, tenant_key: str, *, force: bool = False) -> Site:
        """Derive the site's hardiness zone from its climate normals and persist it.

        A ``manual`` assignment is preserved unless ``force`` is set. Raises
        :class:`ValidationError` (422) when the site has no climate normals with a
        usable minimum temperature yet — the caller should fetch climate normals
        (REQ-041) first.
        """
        site = self._load_site(site_key, tenant_key)

        if site.hardiness_zone_source == "manual" and site.hardiness_zone and not force:
            return site

        derivation = self._derive_zone(site_key, tenant_key)
        if derivation is None:
            raise ValidationError(
                "Für diesen Standort liegen noch keine Klimanormale mit verwertbarer "
                "Minimaltemperatur vor. Bitte zuerst die Klimanormale abrufen (REQ-041).",
                details=[{"field": "climate_normals", "reason": "missing", "code": "not_available"}],
            )
        zone_label, mean_minimum = derivation
        now = datetime.now(UTC)

        zone_doc = self._zone_repo.get_by_zone(zone_label)
        updated = site.model_copy(
            update={
                "hardiness_zone": zone_label,
                # Keep the legacy free-text field in sync so consumers that still
                # read ``climate_zone`` (and the winter-hardiness ampel fallback)
                # stay consistent with the structured zone.
                "climate_zone": zone_label,
                "hardiness_zone_source": "derived_gps",
                "hardiness_zone_resolved_at": now,
                "mean_annual_minimum_c": mean_minimum,
                **self._frost_defaults(site, zone_doc, now.year),
            }
        )
        saved = self._site_repo.update_site(site_key, updated)
        self._zone_repo.assign_site_to_zone(site_key, zone_label, source="derived_gps", resolved_at=now)
        return saved

    def _derive_zone(self, site_key: str, tenant_key: str) -> tuple[str, float] | None:
        """Pick the first climate-normal record that yields a usable minimum."""
        normals = self._climate_normal_repo.get_by_site(site_key, tenant_key)
        for normal in normals:
            derivation = derive_from_climate_normals(normal)
            if derivation is not None:
                return derivation
        return None

    @staticmethod
    def _frost_defaults(site: Site, zone_doc: HardinessZone | None, year: int) -> dict[str, date]:
        """Pre-fill the REQ-015 frost anchors from the zone catalog, when unset.

        Only fields that are still ``None`` on the site are populated, so a
        manually entered or weather-API-derived frost date is never overwritten.
        """
        if zone_doc is None:
            return {}
        updates: dict[str, date] = {}
        if site.last_frost_date_avg is None and zone_doc.typical_last_frost_md:
            updates["last_frost_date_avg"] = _month_day_to_date(zone_doc.typical_last_frost_md, year)
        if site.first_frost_date_avg is None and zone_doc.typical_first_frost_md:
            updates["first_frost_date_avg"] = _month_day_to_date(zone_doc.typical_first_frost_md, year)
        return updates


def _month_day_to_date(month_day: str, year: int) -> date:
    """Convert a ``MM-DD`` frost anchor to a concrete :class:`date` in ``year``."""
    month, day = (int(part) for part in month_day.split("-"))
    return date(year, month, day)
