"""REQ-008 §3 — pure drying / mold-risk calculations.

Stateless helpers implementing the weight-based drying-progress formula, the
snap-test interpretation and the RH / water-activity mold-risk assessment from
REQ-008 §2/§3. Kept free of I/O so they can be unit-tested in isolation and
reused by the service and (future) Celery health-check task.
"""

from __future__ import annotations

import math

from app.common.enums import DryingMethod

#: REQ-008 §3 ``_estimate_remaining_days`` base durations per drying method (days
#: to fully dry). Hang-dry is slowest/best quality, dehydrator fastest.
_BASE_DRYING_DAYS: dict[DryingMethod, int] = {
    DryingMethod.HANG_DRY: 10,
    DryingMethod.RACK_DRY: 8,
    DryingMethod.DEHYDRATOR: 1,
    DryingMethod.AIR_CURE: 14,
}

#: REQ-008 §2 — mold grows above a_w 0.65 regardless of room RH.
MOLD_AW_CRITICAL = 0.65
MOLD_AW_WARNING = 0.60
#: RH-based fallback thresholds when no a_w sensor is present.
MOLD_RH_CRITICAL = 65.0
MOLD_RH_WARNING = 62.0


def calculate_dryness_progress(
    start_weight_g: float,
    current_weight_g: float,
    target_moisture_percent: float = 10.0,
    drying_method: DryingMethod = DryingMethod.HANG_DRY,
) -> dict:
    """Compute a drying-progress report from wet vs. current weight.

    Mirrors ``DryingProtocol.calculate_dryness_progress`` (REQ-008 §3):
    progress is the achieved weight loss relative to the target loss, capped at
    100 %. ``ready_for_curing`` is reached at >= 95 % progress; ``over_dried``
    warns above 85 % raw weight loss.

    Raises ``ValueError`` when weights are non-positive or the current weight
    exceeds the start weight (a batch cannot gain mass while drying).
    """
    if start_weight_g <= 0 or current_weight_g <= 0:
        raise ValueError("start_weight_g and current_weight_g must be positive")
    if current_weight_g > start_weight_g:
        raise ValueError("current_weight_g cannot exceed start_weight_g")

    weight_loss_percent = (start_weight_g - current_weight_g) / start_weight_g * 100
    target_loss = 100 - target_moisture_percent
    progress = min(100.0, (weight_loss_percent / target_loss) * 100) if target_loss > 0 else 0.0

    over_dried = weight_loss_percent > 85
    ready_for_curing = progress >= 95
    snap_test_ready = progress >= 70

    return {
        "weight_loss_percent": round(weight_loss_percent, 1),
        "dryness_progress_percent": round(progress, 1),
        "ready_for_curing": ready_for_curing,
        "snap_test_ready": snap_test_ready,
        "over_dried": over_dried,
        "current_weight_g": current_weight_g,
        "target_weight_g": round(start_weight_g * (target_moisture_percent / 100), 1),
        "estimated_days_remaining": _estimate_remaining_days(progress, drying_method),
        "next_action": _next_action(progress, over_dried),
    }


def _estimate_remaining_days(progress: float, drying_method: DryingMethod) -> int:
    """Estimate remaining drying days from current progress and method."""
    total_days = _BASE_DRYING_DAYS.get(drying_method, 10)
    if progress >= 95:
        return 0
    if progress >= 70:
        return 2
    if progress >= 50:
        return int(total_days * 0.3)
    return int(total_days * 0.7)


def _next_action(progress: float, over_dried: bool) -> str:
    """Recommend the next drying step (REQ-008 §3 ``_get_next_action``)."""
    if over_dried:
        return "over_dried"
    if progress >= 95:
        return "ready_for_curing"
    if progress >= 70:
        return "run_snap_test"
    if progress >= 40:
        return "monitor_climate"
    return "ensure_airflow"


def interpret_snap_test(snaps_cleanly: bool, splinters: bool) -> dict:
    """Interpret a manual snap-test result (REQ-008 §3 ``perform_snap_test``).

    The snap test is an independent operator input (P-002), not a computed
    value; this helper only maps the two booleans onto a verdict.
    """
    if snaps_cleanly and not splinters:
        return {"result": "optimal", "moisture_estimate": "10-12%", "passed": True}
    if snaps_cleanly and splinters:
        return {"result": "overdried", "moisture_estimate": "<8%", "passed": True}
    return {"result": "underdried", "moisture_estimate": ">15%", "passed": False}


def calculate_dew_point(temp_c: float, rh_percent: float) -> float:
    """Magnus-formula dew point in °C (REQ-008 §3 ``calculate_dew_point``)."""
    rh = max(min(rh_percent, 100.0), 1.0)
    a, b = 17.27, 237.7
    gamma = (a * temp_c) / (b + temp_c) + math.log(rh / 100.0)
    return round((b * gamma) / (a - gamma), 1)


def assess_mold_risk(
    avg_rh_percent: float | None,
    max_temp_c: float | None = None,
    avg_water_activity: float | None = None,
) -> dict:
    """Grade mold risk from RH / temperature / water activity (REQ-008 §2).

    Prefers the a_w sensor when present (biologically precise — mold grows above
    a_w 0.65 independent of room RH); falls back to RH thresholds otherwise.
    Returns ``{"risk_level", "reason"}`` where ``risk_level`` is one of
    ``ok`` / ``warning`` / ``critical``.
    """
    if avg_water_activity is not None:
        if avg_water_activity > MOLD_AW_CRITICAL:
            return {"risk_level": "critical", "reason": f"a_w {round(avg_water_activity, 3)} > {MOLD_AW_CRITICAL}"}
        if avg_water_activity > MOLD_AW_WARNING:
            return {"risk_level": "warning", "reason": f"a_w {round(avg_water_activity, 3)} > {MOLD_AW_WARNING}"}
        return {"risk_level": "ok", "reason": f"a_w {round(avg_water_activity, 3)} within safe range"}

    if avg_rh_percent is None:
        return {"risk_level": "ok", "reason": "no humidity data"}

    if avg_rh_percent > MOLD_RH_CRITICAL:
        return {"risk_level": "critical", "reason": f"RH {round(avg_rh_percent, 1)}% > {MOLD_RH_CRITICAL}%"}
    if avg_rh_percent > MOLD_RH_WARNING:
        return {"risk_level": "warning", "reason": f"RH {round(avg_rh_percent, 1)}% > {MOLD_RH_WARNING}%"}
    if avg_rh_percent > 55 and max_temp_c is not None and max_temp_c > 22:
        return {"risk_level": "warning", "reason": f"RH {round(avg_rh_percent, 1)}% at {round(max_temp_c, 1)}°C"}
    return {"risk_level": "ok", "reason": f"RH {round(avg_rh_percent, 1)}% within safe range"}
