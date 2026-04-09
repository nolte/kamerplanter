import math


def calculate_svp(temp_c: float) -> float:
    """Saturation Vapor Pressure using Tetens formula (kPa)."""
    return 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))


def calculate_vpd(temp_c: float, humidity_percent: float) -> float:
    """Calculate VPD in kPa from temperature and relative humidity."""
    svp = calculate_svp(temp_c)
    avp = svp * (humidity_percent / 100.0)
    return svp - avp


def classify_vpd(
    vpd_kpa: float,
    phase: str,
    vpd_ranges: dict[str, tuple[float, float]] | None = None,
) -> tuple[str, str]:
    """Classify VPD value for a given growth phase.
    Returns (status, recommendation) tuple.
    status: 'low', 'optimal', 'high'

    vpd_ranges: optional mapping of phase name -> (low, high) kPa.
        When omitted, uses built-in defaults from ResourceProfileGenerator.
    """
    if vpd_ranges is None:
        from app.domain.engines.resource_profile_generator import ResourceProfileGenerator

        vpd_ranges = ResourceProfileGenerator().get_vpd_ranges()

    ranges = vpd_ranges.get(phase, (0.8, 1.2))
    low, high = ranges
    if vpd_kpa < low:
        return "low", f"VPD too low ({vpd_kpa:.2f} kPa). Decrease humidity or increase temperature."
    elif vpd_kpa > high:
        return "high", f"VPD too high ({vpd_kpa:.2f} kPa). Increase humidity or decrease temperature."
    else:
        return "optimal", f"VPD is optimal ({vpd_kpa:.2f} kPa) for {phase} phase."


def calculate_leaf_vpd(air_temp_c: float, leaf_temp_c: float, humidity_percent: float) -> float:
    """Calculate leaf VPD (more accurate, accounts for leaf temperature offset)."""
    svp_leaf = calculate_svp(leaf_temp_c)
    avp_air = calculate_svp(air_temp_c) * (humidity_percent / 100.0)
    return svp_leaf - avp_air


def target_humidity_for_vpd(temp_c: float, target_vpd: float) -> float:
    """Calculate required humidity to achieve target VPD at given temperature."""
    svp = calculate_svp(temp_c)
    if svp == 0:
        return 0.0
    required_avp = svp - target_vpd
    return max(0.0, min(100.0, (required_avp / svp) * 100.0))
