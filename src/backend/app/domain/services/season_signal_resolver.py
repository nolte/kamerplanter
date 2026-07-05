"""REQ-047 §3.1 — the season trigger cascade (best source wins).

Resolves, for one outdoor/greenhouse site and a reference date, the best
available cold/warm :class:`SeasonSignal`:

1. **live** — :class:`WeatherForecast` frost / min-temperature forecast
   (REQ-005/046). Preferred: day-fresh and site-near.
2. **climatological** — the site's own average frost dates
   (``first_frost_date_avg`` / ``last_frost_date_avg`` / ``eisheilige_date``,
   REQ-002/015). Static, but site-specific.
3. **calendar** — hemisphere preset months (REQ-022) — the coarse fallback.

The resolver degrades gracefully: it always returns a usable signal, and upgrades
automatically once a better source becomes available (AC-6/AC-18).

The public :meth:`resolve` is synchronous because the ArangoDB repositories are
synchronous (python-arango). The REQ-047 spec sketch shows ``async``; that is an
aspirational shape — the concrete repository contract this consumes is sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

from app.common.enums import SeasonTriggerTier
from app.config.settings import settings

if TYPE_CHECKING:
    from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
    from app.domain.models.site import Site

#: Look-ahead window (days) for the live frost forecast.
_LIVE_FORECAST_WINDOW_DAYS = 7


def hemisphere_from_site(site: Site) -> Literal["north", "south"]:
    """Derive the hemisphere from the site's GPS latitude.

    ``gps_coordinates`` is ``(lat, lon)``; a negative latitude is the southern
    hemisphere. Falls back to ``"north"`` when no coordinates are set (matching the
    care-reminder default).
    """
    coords = site.gps_coordinates
    if coords is not None and coords[0] < 0:
        return "south"
    return "north"


@dataclass(frozen=True)
class SeasonSignal:
    """REQ-047 §3.1 — the prepared cold/warm signal of a site for a reference date."""

    tier: SeasonTriggerTier
    #: Assessed night/day minimum temperature (°C) — ``None`` on the calendar /
    #: climatological tiers (no live temperature reading).
    min_temp_c: float | None
    #: Next forecast frost date (live tier only).
    forecast_first_frost_date: date | None
    #: Climatological frost termini (tier 2/3), format ``MM-DD``.
    estimated_first_frost_md: str | None
    estimated_last_frost_md: str | None
    reason_i18n_key: str
    #: Hemisphere of the site — drives the calendar month windows and the
    #: "after the coldest month" spring guard in the engine.
    hemisphere: Literal["north", "south"] = "north"


class SeasonSignalResolver:
    """Resolve the best-available :class:`SeasonSignal` for a site."""

    def __init__(self, weather_forecast_repo: IWeatherForecastRepository) -> None:
        self._weather_repo = weather_forecast_repo

    def resolve(self, site: Site, on_date: date) -> SeasonSignal:
        live = self._try_live(site, on_date)
        if live is not None:
            return live
        clim = self._try_climatological(site, on_date)
        if clim is not None:
            return clim
        return self._calendar_fallback(site, on_date)

    # ── Tier 1: live weather forecast ───────────────────────────────────

    def _try_live(self, site: Site, on_date: date) -> SeasonSignal | None:
        """Use the frost/min-temperature forecast for the next few days.

        Returns ``None`` when the site has no fresh forecast covering the
        look-ahead window (graceful degradation to tier 2/3).
        """
        if not site.key:
            return None
        forecasts = self._weather_repo.find_by_site(site.key, site.tenant_key)
        window_end = date.fromordinal(on_date.toordinal() + _LIVE_FORECAST_WINDOW_DAYS)
        fresh = [fc for fc in forecasts if fc.temp_min_c is not None and on_date <= fc.forecast_date <= window_end]
        if not fresh:
            return None

        fresh.sort(key=lambda fc: fc.forecast_date)
        min_temp = min(fc.temp_min_c for fc in fresh if fc.temp_min_c is not None)
        frost_threshold = settings.season_frost_temp_c
        first_frost = next(
            (fc.forecast_date for fc in fresh if fc.temp_min_c is not None and fc.temp_min_c <= frost_threshold),
            None,
        )
        reason = "pages.season.trigger.frostForecast" if first_frost is not None else "pages.season.trigger.liveTemp"
        return SeasonSignal(
            tier=SeasonTriggerTier.LIVE,
            min_temp_c=min_temp,
            forecast_first_frost_date=first_frost,
            estimated_first_frost_md=self._to_md(site.first_frost_date_avg),
            estimated_last_frost_md=self._to_md(site.last_frost_date_avg or site.eisheilige_date),
            reason_i18n_key=reason,
            hemisphere=hemisphere_from_site(site),
        )

    # ── Tier 2: climatological (site average frost dates) ───────────────

    def _try_climatological(self, site: Site, on_date: date) -> SeasonSignal | None:
        """Use the site's average frost dates (REQ-002/015).

        Returns ``None`` when the site carries no frost dates at all — there is no
        persisted ``:ClimateNormal`` to fall back on, so the site frost dates are
        the tier-2 source (REQ-047 deviation, documented).
        """
        first_md = self._to_md(site.first_frost_date_avg)
        last_md = self._to_md(site.last_frost_date_avg or site.eisheilige_date)
        if first_md is None and last_md is None:
            return None
        return SeasonSignal(
            tier=SeasonTriggerTier.CLIMATOLOGICAL,
            min_temp_c=None,
            forecast_first_frost_date=None,
            estimated_first_frost_md=first_md,
            estimated_last_frost_md=last_md,
            reason_i18n_key="pages.season.trigger.climateEstimate",
            hemisphere=hemisphere_from_site(site),
        )

    # ── Tier 3: calendar fallback ───────────────────────────────────────

    def _calendar_fallback(self, site: Site, on_date: date) -> SeasonSignal:
        """Hemisphere preset months (REQ-022). Transitions run month-based."""
        return SeasonSignal(
            tier=SeasonTriggerTier.CALENDAR,
            min_temp_c=None,
            forecast_first_frost_date=None,
            estimated_first_frost_md=None,
            estimated_last_frost_md=None,
            reason_i18n_key="pages.season.trigger.calendar",
            hemisphere=hemisphere_from_site(site),
        )

    @staticmethod
    def _to_md(value: date | None) -> str | None:
        """Format a date as ``MM-DD`` (year-agnostic), or ``None``."""
        if value is None:
            return None
        return f"{value.month:02d}-{value.day:02d}"
