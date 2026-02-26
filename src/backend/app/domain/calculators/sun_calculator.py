from datetime import date, timedelta

from astral import LocationInfo
from astral.sun import sun


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
