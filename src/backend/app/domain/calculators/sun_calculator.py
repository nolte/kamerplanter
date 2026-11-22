from dataclasses import dataclass
from datetime import date, timedelta, tzinfo
from decimal import ROUND_HALF_UP, Decimal

from astral import LocationInfo, Observer
from astral.sun import azimuth, sun, sunrise, sunset


def calculate_sun_times(
    latitude: float,
    longitude: float,
    calc_date: date,
    timezone: str = "UTC",
) -> dict:
    """Calculate sunrise, sunset, dawn, dusk and day length for a given location and date.

    Args:
        latitude: GPS latitude (-90 to 90).
        longitude: GPS longitude (-180 to 180).
        calc_date: The date to calculate for.
        timezone: IANA timezone string (e.g. "Europe/Berlin").

    Returns:
        Dict with sunrise, sunset, dawn, dusk (as HH:MM strings) and day_length_hours.
    """
    location = LocationInfo(name="query", region="", timezone=timezone, latitude=latitude, longitude=longitude)
    s = sun(location.observer, date=calc_date, tzinfo=location.timezone)

    sunrise = s["sunrise"]
    sunset = s["sunset"]
    dawn = s["dawn"]
    dusk = s["dusk"]
    day_length = (sunset - sunrise).total_seconds() / 3600

    return {
        "date": calc_date.isoformat(),
        "sunrise": sunrise.strftime("%H:%M"),
        "sunset": sunset.strftime("%H:%M"),
        "dawn": dawn.strftime("%H:%M"),
        "dusk": dusk.strftime("%H:%M"),
        "day_length_hours": round(day_length, 2),
    }


def calculate_sun_times_range(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    timezone: str = "UTC",
) -> list[dict]:
    """Calculate sun times for a date range.

    Args:
        latitude: GPS latitude.
        longitude: GPS longitude.
        start_date: First date (inclusive).
        end_date: Last date (inclusive).
        timezone: IANA timezone string.

    Returns:
        List of sun times dicts, one per day.
    """
    results = []
    current = start_date
    while current <= end_date:
        results.append(calculate_sun_times(latitude, longitude, current, timezone))
        current += timedelta(days=1)
    return results


@dataclass(frozen=True)
class SunDirection:
    """Where the sun stands at one moment: compass azimuth (0 = north, clockwise, 0.1 degree) and local ``HH:MM``."""

    azimuth_deg: float
    time: str


@dataclass(frozen=True)
class SunDirections:
    """Sunrise and sunset of one day as directions - what the garden plan's compass shows (REQ-053 GP-FR-016)."""

    day: date
    sunrise: SunDirection
    sunset: SunDirection


def _azimuth_tenth(value: float) -> float:
    """Wrap into ``[0, 360)`` and round to 0.1 degree like ``north_angle_deg`` (ties away from zero)."""
    rounded = float(Decimal(value % 360.0).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) + 0.0
    return 0.0 if rounded >= 360.0 else rounded


def calculate_sun_directions(latitude: float, longitude: float, calc_date: date, tz: tzinfo) -> SunDirections | None:
    """The azimuths of sunrise and sunset on *calc_date* (REQ-053 GP-FR-016), times in *tz*.

    Sunrise and sunset are the moments the upper limb crosses the horizon with standard refraction (astral's
    definition, the same as :func:`calculate_sun_times`); the azimuth is the sun's direction at that moment. No
    shading, no horizon profile (§29). ``None`` on a day without sunrise or sunset - polar day or polar night.
    """
    observer = Observer(latitude=latitude, longitude=longitude)
    try:
        rise = sunrise(observer, date=calc_date, tzinfo=tz)
        set_ = sunset(observer, date=calc_date, tzinfo=tz)
    except ValueError:
        return None
    return SunDirections(
        day=calc_date,
        sunrise=SunDirection(azimuth_deg=_azimuth_tenth(azimuth(observer, rise)), time=rise.strftime("%H:%M")),
        sunset=SunDirection(azimuth_deg=_azimuth_tenth(azimuth(observer, set_)), time=set_.strftime("%H:%M")),
    )
