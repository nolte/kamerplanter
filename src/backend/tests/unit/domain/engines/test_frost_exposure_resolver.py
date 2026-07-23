"""Issue #706 — Location-first frost-exposure resolution.

Truth-table tests for the :func:`resolve_frost_exposure` resolver that
determines whether a plant at a given location on a site is exposed to frost
for winter-hardiness calculations.

The resolver is stateless, pure domain logic: location-first (override wins),
fallback to site type (legacy behaviour). ``None`` values never collapse to
``False``; they fall through to the next layer (site type).
"""

from app.common.enums import SiteType
from app.domain.engines.frost_exposure_resolver import resolve_frost_exposure
from app.domain.models.site import Location, Site


def _location(*, key: str = "loc-1", site_key: str = "site-1", frost_exposed: bool | None = None) -> Location:
    return Location(
        _key=key,
        name="Test Location",
        site_key=site_key,
        area_m2=10.0,
        frost_exposed=frost_exposed,
    )


def _site(*, key: str = "site-1", site_type: SiteType) -> Site:
    return Site(key=key, name="Test Site", type=site_type, climate_zone="")


# ── Truth table: location=None fallback to site type ──────────────────────


class TestNoneLocationFallback:
    """When location is None, resolver falls back to site type."""

    def test_none_location_outdoor_site_returns_true(self) -> None:
        site = _site(site_type=SiteType.OUTDOOR)
        assert resolve_frost_exposure(None, site) is True

    def test_none_location_greenhouse_site_returns_true(self) -> None:
        site = _site(site_type=SiteType.GREENHOUSE)
        assert resolve_frost_exposure(None, site) is True

    def test_none_location_balcony_site_returns_true(self) -> None:
        site = _site(site_type=SiteType.BALCONY)
        assert resolve_frost_exposure(None, site) is True

    def test_none_location_indoor_site_returns_false(self) -> None:
        site = _site(site_type=SiteType.INDOOR)
        assert resolve_frost_exposure(None, site) is False

    def test_none_location_windowsill_site_returns_false(self) -> None:
        site = _site(site_type=SiteType.WINDOWSILL)
        assert resolve_frost_exposure(None, site) is False

    def test_none_location_grow_tent_site_returns_false(self) -> None:
        site = _site(site_type=SiteType.GROW_TENT)
        assert resolve_frost_exposure(None, site) is False


# ── Truth table: location.frost_exposed override wins ────────────────────


class TestLocationOverride:
    """When location.frost_exposed is set, it wins over site type."""

    def test_location_frost_exposed_true_overrides_indoor_site(self) -> None:
        """AC-1: frost-exposed balcony on indoor site (e.g. covered terrace)."""
        location = _location(frost_exposed=True)
        site = _site(site_type=SiteType.INDOOR)
        assert resolve_frost_exposure(location, site) is True

    def test_location_frost_exposed_false_overrides_outdoor_site(self) -> None:
        """AC-2: protected niche under outdoor site (e.g. south-facing wall)."""
        location = _location(frost_exposed=False)
        site = _site(site_type=SiteType.OUTDOOR)
        assert resolve_frost_exposure(location, site) is False

    def test_location_frost_exposed_true_overrides_greenhouse(self) -> None:
        location = _location(frost_exposed=True)
        site = _site(site_type=SiteType.GREENHOUSE)
        assert resolve_frost_exposure(location, site) is True

    def test_location_frost_exposed_false_overrides_greenhouse(self) -> None:
        location = _location(frost_exposed=False)
        site = _site(site_type=SiteType.GREENHOUSE)
        assert resolve_frost_exposure(location, site) is False


# ── Truth table: location.frost_exposed=None inherits from site ────────────


class TestNoneLocationFrostExposedFallback:
    """When location.frost_exposed is None, fall back to site type (AC-3)."""

    def test_location_none_frost_exposed_outdoor_site_returns_true(self) -> None:
        """AC-3: location with None frost_exposed on outdoor site."""
        location = _location(frost_exposed=None)
        site = _site(site_type=SiteType.OUTDOOR)
        assert resolve_frost_exposure(location, site) is True

    def test_location_none_frost_exposed_indoor_site_returns_false(self) -> None:
        """AC-3: location with None frost_exposed on indoor site."""
        location = _location(frost_exposed=None)
        site = _site(site_type=SiteType.INDOOR)
        assert resolve_frost_exposure(location, site) is False

    def test_location_none_frost_exposed_greenhouse_site_returns_true(self) -> None:
        location = _location(frost_exposed=None)
        site = _site(site_type=SiteType.GREENHOUSE)
        assert resolve_frost_exposure(location, site) is True

    def test_location_none_frost_exposed_balcony_site_returns_true(self) -> None:
        location = _location(frost_exposed=None)
        site = _site(site_type=SiteType.BALCONY)
        assert resolve_frost_exposure(location, site) is True
