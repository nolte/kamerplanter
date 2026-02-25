def calculate_daily_gdd(temp_max_c: float, temp_min_c: float, base_temp_c: float) -> float:
    """Calculate Growing Degree Days for a single day.
    GDD = max(0, ((Tmax + Tmin) / 2) - Tbase)
    """
    avg_temp = (temp_max_c + temp_min_c) / 2.0
    return max(0.0, avg_temp - base_temp_c)


def calculate_accumulated_gdd(daily_temps: list[tuple[float, float]], base_temp_c: float) -> float:
    """Calculate accumulated GDD from a list of (max_temp, min_temp) tuples."""
    return sum(calculate_daily_gdd(tmax, tmin, base_temp_c) for tmax, tmin in daily_temps)


def estimate_days_to_gdd_target(target_gdd: float, current_gdd: float, avg_daily_gdd: float) -> int | None:
    """Estimate days remaining to reach a GDD target."""
    if avg_daily_gdd <= 0:
        return None
    remaining = target_gdd - current_gdd
    if remaining <= 0:
        return 0
    return int(remaining / avg_daily_gdd) + 1
