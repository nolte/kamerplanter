"""Reactive frost-warning detection (REQ-005 / REQ-018 / REQ-039).

Pure, side-effect-free evaluation of a location's frost risk from its most
recent ambient-temperature reading. This backs the Home Assistant binary
entity ``binary_sensor.kp_{location}_frost_warning`` (see
``docs/de/guides/home-assistant-integration.md``).

Design note — reactive, not predictive:
    This engine derives the warning from the *current* measured air
    temperature, not from a weather forecast. Proactive forecast-based frost
    warning (DWD / OpenWeatherMap / Open-Meteo) remains a documented follow-up
    and is intentionally out of scope here.

Default threshold — 3.0 °C:
    A frost *warning* fires at a small positive margin above 0 °C rather than
    at 0 °C itself. Screen-height air temperature (~2 m) is regularly several
    degrees warmer than the ground/plant surface on clear, calm nights because
    of radiative cooling, so ground frost already occurs while the measured air
    temperature still reads ~+3 °C. This mirrors the German Wetterdienst
    convention of issuing ground-frost ("Bodenfrost") warnings around +3 °C.
    The threshold is configurable via ``settings.frost_warning_threshold_celsius``.
"""

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
