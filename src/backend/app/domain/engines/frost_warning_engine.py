"""Reactive frost-warning detection (REQ-005 / REQ-018 / REQ-039).

Pure, side-effect-free evaluation of a location's frost risk from its most
recent ambient-temperature reading. This backs the Home Assistant binary
entity ``binary_sensor.kp_{location}_frost_warning`` (see
``docs/de/guides/home-assistant-integration.md``).

Design note — reactive *and* proactive:
    :func:`evaluate_frost_warning` derives the warning from the *current*
    measured air temperature (reactive). :func:`evaluate_forecast_frost_warning`
    (Issue #392) adds a *proactive* early warning derived from the persisted
    daily :class:`WeatherForecast` records (REQ-046 / DWD / OpenWeatherMap /
    Open-Meteo), so a grower is warned *before* a frost night. Both functions are
    pure and side-effect-free; the reactive function is unchanged.

Default threshold — 3.0 °C:
    A frost *warning* fires at a small positive margin above 0 °C rather than
    at 0 °C itself. Screen-height air temperature (~2 m) is regularly several
    degrees warmer than the ground/plant surface on clear, calm nights because
    of radiative cooling, so ground frost already occurs while the measured air
    temperature still reads ~+3 °C. This mirrors the German Wetterdienst
    convention of issuing ground-frost ("Bodenfrost") warnings around +3 °C.
    The threshold is configurable via ``settings.frost_warning_threshold_celsius``.
"""

from datetime import date, timedelta

from app.domain.models.weather import WeatherForecast

#: Ambient-temperature metric types accepted for a location, in priority order.
#: ``temperature_celsius`` is the canonical air-temperature metric for
#: locations/sites (frontend default for non-tank sensors); ``water_temp_celsius``
#: is tolerated as a fallback because Home-Assistant-suggested temperature
#: entities are mapped onto that key by ``SensorService.get_ha_entities``.
AIR_TEMPERATURE_METRIC_TYPES: tuple[str, ...] = (
    "temperature_celsius",
    "water_temp_celsius",
)

#: Sensible default warning threshold in °C (see module docstring for rationale).
DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS: float = 3.0

#: Sensible default proactive (forecast) warning threshold in °C. Kept separate
#: from and slightly more conservative than the reactive threshold — see
#: ``settings.frost_forecast_threshold_celsius``.
DEFAULT_FROST_FORECAST_THRESHOLD_CELSIUS: float = 2.0

#: Default forecast horizon in days (today + next day) — see
#: ``settings.frost_forecast_horizon_days``.
DEFAULT_FROST_FORECAST_HORIZON_DAYS: int = 2


def evaluate_frost_warning(
    temperature_celsius: float | None,
    threshold_celsius: float = DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS,
) -> bool | None:
    """Return the frost-warning state for a single ambient temperature.

    Args:
        temperature_celsius: The most recent ambient air temperature in °C, or
            ``None`` when no temperature reading is available.
        threshold_celsius: The warning threshold in °C. A warning fires when the
            temperature is at or below this value.

    Returns:
        ``True`` when frost is warned (temperature at/below threshold),
        ``False`` when a reading exists and is above the threshold, and
        ``None`` when no temperature reading is available. ``None`` is returned
        honestly rather than defaulting to ``False`` so the Home Assistant entity
        reports ``unknown`` instead of a fabricated "no frost".
    """
    if temperature_celsius is None:
        return None
    return temperature_celsius <= threshold_celsius


def evaluate_forecast_frost_warning(
    forecasts: list[WeatherForecast],
    threshold_celsius: float,
    horizon_days: int,
    today: date,
) -> dict:
    """Evaluate a proactive frost early-warning from persisted daily forecasts.

    Scans the daily :class:`WeatherForecast` records for the location's site over
    the inclusive horizon ``today .. today + horizon_days`` and reports whether a
    frost night is expected within it. Records outside the horizon — including any
    stale record with ``forecast_date < today`` — are ignored.

    Args:
        forecasts: The daily forecast records for one site (any date range;
            filtered to the horizon here). Usually the result of
            ``IWeatherForecastRepository.find_by_site``.
        threshold_celsius: The proactive warning threshold in °C. A frost is
            predicted when an in-horizon record's ``temp_min_c`` is at or below
            this value.
        horizon_days: How many days ahead of ``today`` to scan (inclusive). ``0``
            means only ``today``.
        today: The reference "today" (injected so the function stays pure and
            deterministic).

    Returns:
        A mapping ``{"predicted", "min_temp", "expected_date", "source"}``:

        * ``predicted=True`` — at least one in-horizon record has a known
          ``temp_min_c`` at/below the threshold. ``expected_date`` / ``min_temp``
          / ``source`` describe the **earliest** such frost day (ties broken by
          the lowest ``temp_min_c``).
        * ``predicted=False`` — at least one in-horizon record has a known
          ``temp_min_c`` but none reaches the threshold. The other fields are
          ``None``.
        * ``predicted=None`` — no usable signal (no in-horizon record, or every
          in-horizon record has ``temp_min_c = None``). Reported honestly as
          "unknown" rather than a fabricated "no frost", mirroring
          :func:`evaluate_frost_warning`.
    """
    unknown: dict = {"predicted": None, "min_temp": None, "expected_date": None, "source": None}

    horizon_end = today + timedelta(days=horizon_days)
    usable = [
        record for record in forecasts if record.temp_min_c is not None and today <= record.forecast_date <= horizon_end
    ]
    if not usable:
        return unknown

    frost_days = [record for record in usable if record.temp_min_c <= threshold_celsius]
    if not frost_days:
        return {"predicted": False, "min_temp": None, "expected_date": None, "source": None}

    # Earliest frost day wins; ties on the same date are broken by the lowest
    # (most severe) minimum temperature.
    earliest = min(frost_days, key=lambda record: (record.forecast_date, record.temp_min_c))
    return {
        "predicted": True,
        "min_temp": earliest.temp_min_c,
        "expected_date": earliest.forecast_date,
        "source": earliest.source,
    }


def pick_air_temperature(values: dict[str, dict]) -> tuple[float | None, str | None]:
    """Extract the ambient air temperature from a live-state ``values`` map.

    Args:
        values: The ``values`` mapping produced by
            ``SensorService.get_live_state_for_sensors`` — keyed by
            ``metric_type`` with ``{"value", "entity_id", ...}`` entries.

    Returns:
        A ``(temperature_celsius, entity_id)`` tuple. Both are ``None`` when no
        accepted air-temperature metric is present. The first matching metric in
        :data:`AIR_TEMPERATURE_METRIC_TYPES` wins.
    """
    for metric_type in AIR_TEMPERATURE_METRIC_TYPES:
        entry = values.get(metric_type)
        if entry is None:
            continue
        raw = entry.get("value")
        if raw is None:
            continue
        # A non-numeric live state (Home Assistant reports ``"unavailable"`` /
        # ``"unknown"`` as the entity value) must not surface as a 500 on the
        # frost-warning endpoint. Skip this metric and fall through to the next
        # candidate; if none is numeric we honestly report "no temperature".
        # NB: the ``as exc`` binding is deliberate — a bare tuple-except without it
        # is miscompiled by ``ruff format`` into invalid ``except A, B:`` syntax.
        try:
            temperature = float(raw)
        except (ValueError, TypeError) as exc:  # noqa: F841
            continue
        return temperature, entry.get("entity_id")
    return None, None
