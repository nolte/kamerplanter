"""REQ-047 §3.1 — unit tests for the SeasonSignalResolver cascade.

Covers all three tiers (live / climatological / calendar), graceful degradation
when the higher tier has no fresh data, hemisphere derivation and the frost-date
formatting.
"""

from datetime import UTC, date, datetime

from app.common.enums import SeasonTriggerTier, SiteType
from app.domain.models.site import Site
from app.domain.models.weather import ClimateNormal, WeatherForecast
from app.domain.services.season_signal_resolver import SeasonSignalResolver, hemisphere_from_site


class _FakeWeatherRepo:
    """Minimal stand-in for ``IWeatherForecastRepository.find_by_site``."""

    def __init__(self, forecasts: list[WeatherForecast]) -> None:
        self._forecasts = forecasts

    def find_by_site(self, site_key: str, tenant_key: str) -> list[WeatherForecast]:
        return list(self._forecasts)


class _FakeClimateNormalRepo:
    """Minimal stand-in for ``IClimateNormalRepository.get_by_site``."""

    def __init__(self, normals: list[ClimateNormal]) -> None:
        self._normals = normals

    def get_by_site(self, site_key: str, tenant_key: str) -> list[ClimateNormal]:
        return list(self._normals)


def _site(**overrides) -> Site:
    data = {
        "key": "s1",
        "tenant_key": "t1",
        "name": "Garden",
        "type": SiteType.OUTDOOR,
        "gps_coordinates": (52.5, 13.4),
        "climate_zone": "7b",
    }
    data.update(overrides)
    return Site(**data)


def _forecast(day: date, temp_min_c: float | None) -> WeatherForecast:
    return WeatherForecast(
        site_key="s1",
        tenant_key="t1",
        forecast_date=day,
        temp_min_c=temp_min_c,
        source="open-meteo",
        fetched_at=datetime.now(UTC),
    )


class TestLiveTier:
    def test_live_signal_reports_min_temp_and_frost_date(self) -> None:
        on = date(2026, 10, 1)
        forecasts = [
            _forecast(date(2026, 10, 1), 6.0),
            _forecast(date(2026, 10, 2), 1.0),  # frost (<= 2 °C default)
            _forecast(date(2026, 10, 3), 4.0),
        ]
        resolver = SeasonSignalResolver(_FakeWeatherRepo(forecasts))
        signal = resolver.resolve(_site(), on)

        assert signal.tier == SeasonTriggerTier.LIVE
        assert signal.min_temp_c == 1.0
        assert signal.forecast_first_frost_date == date(2026, 10, 2)
        assert signal.reason_i18n_key == "pages.season.trigger.frostForecast"

    def test_live_without_frost_uses_temp_reason(self) -> None:
        on = date(2026, 10, 1)
        forecasts = [_forecast(date(2026, 10, 2), 8.0), _forecast(date(2026, 10, 3), 7.0)]
        resolver = SeasonSignalResolver(_FakeWeatherRepo(forecasts))
        signal = resolver.resolve(_site(), on)

        assert signal.tier == SeasonTriggerTier.LIVE
        assert signal.forecast_first_frost_date is None
        assert signal.reason_i18n_key == "pages.season.trigger.liveTemp"

    def test_stale_forecasts_outside_window_degrade_to_lower_tier(self) -> None:
        on = date(2026, 10, 1)
        # All forecasts are in the past → not fresh within the look-ahead window.
        forecasts = [_forecast(date(2026, 9, 1), 3.0)]
        site = _site(first_frost_date_avg=date(2026, 10, 20), last_frost_date_avg=date(2027, 4, 15))
        resolver = SeasonSignalResolver(_FakeWeatherRepo(forecasts))
        signal = resolver.resolve(site, on)

        assert signal.tier == SeasonTriggerTier.CLIMATOLOGICAL


class TestClimatologicalTier:
    def test_uses_site_frost_dates_when_no_live_data(self) -> None:
        site = _site(first_frost_date_avg=date(2026, 10, 20), last_frost_date_avg=date(2027, 4, 15))
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CLIMATOLOGICAL
        assert signal.min_temp_c is None
        assert signal.estimated_first_frost_md == "10-20"
        assert signal.estimated_last_frost_md == "04-15"

    def test_eisheilige_fills_last_frost_when_last_avg_missing(self) -> None:
        site = _site(first_frost_date_avg=date(2026, 10, 20), eisheilige_date=date(2027, 5, 15))
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CLIMATOLOGICAL
        assert signal.estimated_last_frost_md == "05-15"


class TestCalendarTier:
    def test_falls_back_to_calendar_without_any_data(self) -> None:
        site = _site(gps_coordinates=None)  # no frost dates, no coordinates
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 11, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR
        assert signal.min_temp_c is None
        assert signal.reason_i18n_key == "pages.season.trigger.calendar"
        assert signal.hemisphere == "north"

    def test_only_eisheilige_falls_through_to_calendar(self) -> None:
        """K1 — a site with only a spring terminus (eisheilige, no autumn frost
        date) cannot drive the climatological winter entry, so the resolver falls
        through to the calendar tier whose month windows still enter winter."""
        site = _site(eisheilige_date=date(2027, 5, 15))  # no first/last frost avg
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR

    def test_only_last_frost_avg_falls_through_to_calendar(self) -> None:
        """K1 — likewise for a lone spring last-frost average without an autumn
        terminus: the climatological tier would strand the site in ``growing``."""
        site = _site(last_frost_date_avg=date(2027, 4, 15))
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR


def _climate_normal(monthly_min: list[float], hemisphere_site_key: str = "s1") -> ClimateNormal:
    return ClimateNormal(
        site_key=hemisphere_site_key,
        tenant_key="t1",
        source="nasa-power",
        fetched_at=datetime.now(UTC),
        monthly_temp_min_c=monthly_min,
        coldest_month_min_c=min(monthly_min),
    )


class TestClimateNormalTier:
    """AC-4 upgrade path — climatological tier derived from :class:`ClimateNormal`."""

    #: Northern-hemisphere monthly minima: Jan/Feb/Nov/Dec are sub-frost (<= 2 °C).
    _NORTH_MIN = [-2.0, -1.0, 3.0, 6.0, 10.0, 14.0, 16.0, 15.0, 11.0, 6.0, 1.0, -1.0]

    def test_derives_frost_termini_when_site_has_no_frost_dates(self) -> None:
        site = _site()  # no first/last frost avg, but GPS present
        resolver = SeasonSignalResolver(
            _FakeWeatherRepo([]),
            _FakeClimateNormalRepo([_climate_normal(self._NORTH_MIN)]),
        )
        signal = resolver.resolve(site, date(2026, 7, 1))

        assert signal.tier == SeasonTriggerTier.CLIMATOLOGICAL
        # First autumn frost month = November (index 10) → 11-15.
        assert signal.estimated_first_frost_md == "11-15"
        # Last spring frost month = February (index 1) → 02-15.
        assert signal.estimated_last_frost_md == "02-15"
        # July normal min exposed for transparency.
        assert signal.min_temp_c == 16.0

    def test_site_frost_dates_win_over_climate_normal(self) -> None:
        site = _site(first_frost_date_avg=date(2026, 10, 20), last_frost_date_avg=date(2027, 4, 15))
        resolver = SeasonSignalResolver(
            _FakeWeatherRepo([]),
            _FakeClimateNormalRepo([_climate_normal(self._NORTH_MIN)]),
        )
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.estimated_first_frost_md == "10-20"
        assert signal.min_temp_c is None  # site-frost-date path stays temperature-free

    def test_frost_free_normals_fall_through_to_calendar(self) -> None:
        site = _site()
        warm = [8.0] * 12  # never dips to the frost threshold
        resolver = SeasonSignalResolver(
            _FakeWeatherRepo([]),
            _FakeClimateNormalRepo([_climate_normal(warm)]),
        )
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR

    def test_no_normals_falls_through_to_calendar(self) -> None:
        site = _site()
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]), _FakeClimateNormalRepo([]))
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR

    def test_without_repo_falls_through_to_calendar(self) -> None:
        site = _site()
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))  # no climate-normal repo
        signal = resolver.resolve(site, date(2026, 9, 1))

        assert signal.tier == SeasonTriggerTier.CALENDAR


class TestHemisphere:
    def test_southern_hemisphere_from_negative_latitude(self) -> None:
        assert hemisphere_from_site(_site(gps_coordinates=(-33.9, 151.2))) == "south"

    def test_northern_default_without_coordinates(self) -> None:
        assert hemisphere_from_site(_site(gps_coordinates=None)) == "north"

    def test_calendar_signal_carries_hemisphere(self) -> None:
        site = _site(gps_coordinates=(-33.9, 151.2))
        resolver = SeasonSignalResolver(_FakeWeatherRepo([]))
        signal = resolver.resolve(site, date(2026, 5, 1))
        assert signal.hemisphere == "south"
