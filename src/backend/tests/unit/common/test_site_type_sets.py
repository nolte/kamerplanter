"""Unit tests for the site-type classification sets in ``app.common.enums``.

These lock in the SSOT behaviour behind SITE #492: a balcony is a frost-exposed
outdoor location, so it must be both overwintering- and weather-relevant, and the
two sets must not drift apart.
"""

from app.common.enums import (
    OVERWINTERING_SITE_TYPES,
    WEATHER_RELEVANT_SITE_TYPES,
    SiteType,
)


class TestWeatherRelevantSiteTypes:
    def test_includes_balcony(self) -> None:
        assert SiteType.BALCONY in WEATHER_RELEVANT_SITE_TYPES

    def test_includes_outdoor_and_greenhouse(self) -> None:
        assert SiteType.OUTDOOR in WEATHER_RELEVANT_SITE_TYPES
        assert SiteType.GREENHOUSE in WEATHER_RELEVANT_SITE_TYPES

    def test_excludes_indoor_types(self) -> None:
        assert SiteType.INDOOR not in WEATHER_RELEVANT_SITE_TYPES
        assert SiteType.WINDOWSILL not in WEATHER_RELEVANT_SITE_TYPES
        assert SiteType.GROW_TENT not in WEATHER_RELEVANT_SITE_TYPES

    def test_matches_frost_exposed_set_no_drift(self) -> None:
        # A frost-exposed site is, by the same reasoning, a weather-relevant one.
        assert WEATHER_RELEVANT_SITE_TYPES == OVERWINTERING_SITE_TYPES

    def test_is_frozenset(self) -> None:
        assert isinstance(WEATHER_RELEVANT_SITE_TYPES, frozenset)
