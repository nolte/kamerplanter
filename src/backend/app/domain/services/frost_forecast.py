"""The site's frost verdict from the stored forecasts, with the configured threshold and horizon (REQ-392, WP 8.20).

One place both the early-warning task and the plant state read, so the verdict is the same expression
(:func:`~app.domain.engines.frost_warning_engine.evaluate_forecast_frost_warning`) on the same settings.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Any

import structlog

from app.config.settings import settings
from app.domain.engines.frost_warning_engine import evaluate_forecast_frost_warning
from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
from app.domain.models.weather import WeatherForecast

logger = structlog.get_logger()


def site_frost_verdict(forecasts: Iterable[WeatherForecast], today: date | None = None) -> dict[str, Any]:
    """``{"predicted", "min_temp", "expected_date", "source"}`` for the site, as the early warning computes it."""
    return evaluate_forecast_frost_warning(
        list(forecasts),
        threshold_celsius=settings.frost_forecast_threshold_celsius,
        horizon_days=settings.frost_forecast_horizon_days,
        today=today if today is not None else datetime.now(UTC).date(),
    )


def read_site_frost_verdict(
    forecasts: IWeatherForecastRepository | None, site_key: str, *, tenant_key: str, now: datetime
) -> dict[str, Any] | None:
    """The verdict for a site read from the stored forecasts, tenant-scoped; ``None`` when there is no source.

    A failed *read* answers ``None`` (the frost reason is an overlay: no reason, no 500); only the site and the error
    class are logged.
    """
    if forecasts is None:
        return None
    try:
        stored = forecasts.find_by_site(site_key, tenant_key)
    except Exception as exc:  # noqa: BLE001 — an unreadable forecast drops the reason, never the plant state
        logger.warning("frost_forecast.verdict_unavailable", site_key=site_key, error=type(exc).__name__)
        return None
    return site_frost_verdict(stored, now.astimezone(UTC).date())
