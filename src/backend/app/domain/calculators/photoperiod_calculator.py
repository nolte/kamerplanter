def calculate_transition_schedule(
    current_hours: float,
    target_hours: float,
    transition_days: int = 7,
    lights_on_time: str = "06:00",
) -> list[dict[str, float | int]]:
    """Generate gradual photoperiod transition schedule.
    Returns list of {day, photoperiod_hours, lights_on, lights_off}.
    Recommended 7-day transition to prevent plant stress.

    Args:
        lights_on_time: Lights-on time in HH:MM format (default "06:00").
    """
    if transition_days < 1:
        transition_days = 1
    h, m = lights_on_time.split(":")
    base_on_minutes = int(h) * 60 + int(m)
    schedule = []
    step = (target_hours - current_hours) / transition_days
    for day in range(1, transition_days + 1):
        hours = current_hours + (step * day)
        hours = round(max(0.0, min(24.0, hours)), 2)
        lights_on_minutes = base_on_minutes
        lights_off_minutes = lights_on_minutes + int(hours * 60)
        if lights_off_minutes >= 24 * 60:
            lights_off_minutes = 24 * 60 - 1
        schedule.append(
            {
                "day": day,
                "photoperiod_hours": hours,
                "lights_on": _minutes_to_time_str(lights_on_minutes),
                "lights_off": _minutes_to_time_str(lights_off_minutes),
            }
        )
    return schedule


def _minutes_to_time_str(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def _time_str_to_minutes(value: str) -> int:
    h, m = value.split(":")
    return int(h) * 60 + int(m)


def effective_light_hours(lights_on: str | None, lights_off: str | None) -> float | None:
    """Hours of light per day for an artificial grow-light schedule (REQ-018).

    Parses two ``HH:MM`` strings and returns the on-duration, handling the
    midnight wrap: ``18:00``→``06:00`` yields 12h via ``(off - on) mod 24h``.
    Used as the indoor equivalent of astronomical day length for the
    ``photoperiod_based`` transition trigger (REQ-003 E1).

    Returns ``None`` (photoperiod trigger then skipped) when either bound is
    missing/malformed, or when ``lights_on == lights_off`` — equal times are
    ambiguous (0h permanent-dark vs 24h permanent-light are both nonsensical as
    a real schedule), so the trigger is skipped rather than guessed.
    """
    if not lights_on or not lights_off:
        return None
    try:
        on_minutes = _time_str_to_minutes(lights_on)
        off_minutes = _time_str_to_minutes(lights_off)
    except ValueError:
        # malformed HH:MM (unpack / int() failure) -> skip the trigger
        return None
    if on_minutes == off_minutes:
        return None
    return ((off_minutes - on_minutes) % (24 * 60)) / 60.0


def calculate_dli(ppfd: int, photoperiod_hours: float) -> float:
    """Calculate Daily Light Integral (mol/m²/day).
    DLI = PPFD × photoperiod_hours × 3600 / 1_000_000
    """
    return ppfd * photoperiod_hours * 3600 / 1_000_000


def is_short_day_triggered(day_length_hours: float, critical_hours: float) -> bool:
    """Check if short-day flowering is triggered (day shorter than critical)."""
    return day_length_hours < critical_hours


def is_long_day_triggered(day_length_hours: float, critical_hours: float) -> bool:
    """Check if long-day flowering is triggered (day longer than critical)."""
    return day_length_hours > critical_hours
