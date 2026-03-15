from app.config.constants import EC_LIMITS


class HydroSystemMonitor:
    """Monitors hydroponic system parameters."""

    def analyze_runoff(
        self,
        input_ec: float,
        input_ph: float,
        runoff_ec: float,
        runoff_ph: float,
        input_volume_liters: float,
        runoff_volume_liters: float,
    ) -> dict:
        """Analyze runoff data and return health assessment."""
        ec_diff = runoff_ec - input_ec
        ph_diff = runoff_ph - input_ph
        runoff_percent = (runoff_volume_liters / input_volume_liters * 100) if input_volume_liters > 0 else 0

        ec_status = "healthy"
        ec_action = "No action needed"
        if abs(ec_diff) > 0.5:
            ec_status = "warning"
            if ec_diff > 0:
                ec_action = "Salt buildup detected. Consider flushing."
            else:
                ec_action = "Plant is consuming heavily. Consider increasing feed strength."

        ph_status = "healthy"
        ph_action = "No action needed"
        if abs(ph_diff) > 1.0:
            ph_status = "warning"
            ph_action = "Substrate pH buffering exhausted. Consider substrate amendment or replacement."

        runoff_status = "healthy"
        runoff_action = "No action needed"
        if runoff_percent < 15:
            runoff_status = "low"
            runoff_action = "Increase watering volume to achieve 15-20% runoff."
        elif runoff_percent > 20:
            runoff_status = "high"
            runoff_action = "Reduce watering volume. Aim for 15-20% runoff."

        overall = "healthy"
        if ec_status == "warning" or ph_status == "warning":
            overall = "attention_needed"

        return {
            "ec_analysis": {
                "status": ec_status,
                "input_ec": input_ec,
                "runoff_ec": runoff_ec,
                "difference": round(ec_diff, 2),
                "action": ec_action,
            },
            "ph_analysis": {
                "status": ph_status,
                "input_ph": input_ph,
                "runoff_ph": runoff_ph,
                "difference": round(ph_diff, 2),
                "action": ph_action,
            },
            "runoff_volume": {
                "status": runoff_status,
                "percent": round(runoff_percent, 1),
                "action": runoff_action,
            },
            "overall_health": overall,
        }

    def validate_ec_for_substrate(self, target_ec: float, substrate_type: str) -> tuple[bool, str]:
        """Validate EC target against substrate limits."""
        limits = EC_LIMITS.get(substrate_type)
        if limits is None:
            return True, "No EC limits defined for this substrate type"
        low, high = limits
        if target_ec < low:
            return False, f"EC {target_ec} below minimum {low} for {substrate_type}"
        if target_ec > high:
            return False, f"EC {target_ec} above maximum {high} for {substrate_type}"
        return True, "EC within acceptable range"
