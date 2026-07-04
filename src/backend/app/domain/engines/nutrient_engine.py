from app.common.enums import ApplicationMethod, FertilizerType, PhEffect, SubstrateType
from app.domain.engines.fertilizer_classification import (
    is_calmag,
    is_silicate,
    is_sulfate_bearing,
)
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import DeliveryChannel


class FlushingProtocol:
    """Generates pre-harvest flushing schedules."""

    # Flush duration ranges per substrate (min_days, max_days)
    FLUSH_DURATIONS: dict[SubstrateType, tuple[int, int]] = {
        SubstrateType.HYDRO_SOLUTION: (7, 14),
        SubstrateType.COCO: (10, 21),
        SubstrateType.ROCKWOOL_SLAB: (7, 14),
        SubstrateType.CLAY_PEBBLES: (7, 14),
        SubstrateType.PERLITE: (7, 14),
        SubstrateType.SOIL: (14, 30),
        SubstrateType.LIVING_SOIL: (14, 30),
    }

    def generate(
        self,
        current_ec_ms: float,
        days_until_harvest: int,
        substrate_type: SubstrateType,
    ) -> dict:
        min_days, max_days = self.FLUSH_DURATIONS.get(substrate_type, (14, 30))
        recommended_days = min(max_days, max(min_days, days_until_harvest))
        flush_start_day = max(0, days_until_harvest - recommended_days)

        schedule: list[dict] = []
        for day in range(recommended_days):
            progress = (day + 1) / recommended_days
            if progress < 0.3:
                target_ec = current_ec_ms * 0.5
                action = "Reduced nutrient solution"
                dosage_percent = 50
            elif progress < 0.6:
                target_ec = current_ec_ms * 0.25
                action = "Quarter-strength flush"
                dosage_percent = 25
            else:
                target_ec = 0.0
                action = "Plain water flush"
                dosage_percent = 0

            schedule.append(
                {
                    "day": day + 1,
                    "absolute_day": flush_start_day + day + 1,
                    "target_ec_ms": round(target_ec, 2),
                    "action": action,
                    "dosage_percent": dosage_percent,
                }
            )

        return {
            "substrate_type": substrate_type.value,
            "recommended_flush_days": recommended_days,
            "flush_start_day": flush_start_day,
            "current_ec_ms": current_ec_ms,
            "schedule": schedule,
        }


class RunoffAnalyzer:
    """Analyzes drain-to-waste runoff data."""

    EC_BUILDUP_THRESHOLD = 0.5  # mS above input = salt buildup
    EC_WARNING_THRESHOLD = 0.3
    PH_DRIFT_THRESHOLD = 0.5
    IDEAL_RUNOFF_PERCENT = (10, 30)

    def analyze(
        self,
        input_ec_ms: float,
        runoff_ec_ms: float,
        input_ph: float,
        runoff_ph: float,
        input_volume_liters: float,
        runoff_volume_liters: float,
    ) -> dict:
        ec_delta = runoff_ec_ms - input_ec_ms
        ph_delta = runoff_ph - input_ph
        runoff_percent = (runoff_volume_liters / input_volume_liters * 100) if input_volume_liters > 0 else 0

        # EC status
        if ec_delta > self.EC_BUILDUP_THRESHOLD:
            ec_status = "SALT_BUILDUP"
            ec_message = f"Runoff EC {ec_delta:+.2f} mS above input — salt accumulation detected"
        elif ec_delta > self.EC_WARNING_THRESHOLD:
            ec_status = "WARNING"
            ec_message = f"Runoff EC {ec_delta:+.2f} mS above input — monitor closely"
        elif ec_delta < -self.EC_WARNING_THRESHOLD:
            ec_status = "UNDERFED"
            ec_message = f"Runoff EC {ec_delta:+.2f} mS below input — plant may need more nutrients"
        else:
            ec_status = "OK"
            ec_message = "EC levels are within normal range"

        # pH status
        if abs(ph_delta) > self.PH_DRIFT_THRESHOLD:
            ph_status = "DRIFT"
            direction = "up" if ph_delta > 0 else "down"
            ph_message = f"pH drifted {direction} by {abs(ph_delta):.1f} — check substrate buffering"
        else:
            ph_status = "OK"
            ph_message = "pH drift is within acceptable range"

        # Runoff volume status
        if runoff_percent < self.IDEAL_RUNOFF_PERCENT[0]:
            volume_status = "LOW"
            volume_message = f"Runoff {runoff_percent:.0f}% — increase watering volume"
        elif runoff_percent > self.IDEAL_RUNOFF_PERCENT[1]:
            volume_status = "HIGH"
            volume_message = f"Runoff {runoff_percent:.0f}% — reduce watering volume"
        else:
            volume_status = "OK"
            volume_message = f"Runoff {runoff_percent:.0f}% — within ideal range"

        # Overall health
        statuses = [ec_status, ph_status, volume_status]
        if "SALT_BUILDUP" in statuses:
            overall = "POOR"
        elif "WARNING" in statuses or "DRIFT" in statuses:
            overall = "FAIR"
        else:
            overall = "GOOD"

        return {
            "ec_delta": round(ec_delta, 2),
            "ec_status": ec_status,
            "ec_message": ec_message,
            "ph_delta": round(ph_delta, 2),
            "ph_status": ph_status,
            "ph_message": ph_message,
            "runoff_percent": round(runoff_percent, 1),
            "volume_status": volume_status,
            "volume_message": volume_message,
            "overall_health": overall,
        }


class MixingSafetyValidator:
    """Validates fertilizer mixing safety and order."""

    # Known incompatible pairs (component-based)
    KNOWN_INCOMPATIBLE = [
        {
            "pair": ("calcium", "sulfate"),
            "reason": "Calcium + sulfate → gypsum precipitation (CaSO₄)",
            "severity": "critical",
        },
        {
            "pair": ("calcium", "phosphate"),
            "reason": "Calcium + phosphate → calcium phosphate precipitation",
            "severity": "critical",
        },
        {
            "pair": ("iron_chelate", "high_ph"),
            "reason": "Iron chelate destabilizes at pH > 7",
            "severity": "warning",
        },
    ]

    def validate_combination(self, fertilizers: list[Fertilizer]) -> dict:
        """Validate a combination of fertilizers for mixing safety."""
        warnings: list[str] = []

        # Check for CalMag before sulfate rule (structural classification — DOM-6)
        calmag_ferts = [f for f in fertilizers if is_calmag(f)]
        sulfate_ferts = [f for f in fertilizers if is_sulfate_bearing(f)]

        if calmag_ferts and sulfate_ferts:
            for cf in calmag_ferts:
                for sf in sulfate_ferts:
                    if cf.mixing_priority > sf.mixing_priority:
                        warnings.append(
                            f"CRITICAL: {cf.product_name} (priority {cf.mixing_priority}) must be mixed BEFORE "
                            f"{sf.product_name} (priority {sf.mixing_priority}) — CalMag before sulfates!"
                        )

        # Check silicate-before-CalMag order (CaSiO₃ precipitation risk)
        silicate_ferts = [f for f in fertilizers if is_silicate(f)]
        calmag_ferts_all = calmag_ferts
        if silicate_ferts and calmag_ferts_all:
            for sf in silicate_ferts:
                for cf in calmag_ferts_all:
                    if sf.mixing_priority > cf.mixing_priority:
                        warnings.append(
                            f"CRITICAL: {sf.product_name} (silicate, priority {sf.mixing_priority}) "
                            f"must be mixed BEFORE {cf.product_name} (priority {cf.mixing_priority}) — "
                            f"Ca²⁺-silicate precipitation (CaSiO₃) risk!"
                        )

        # Check application method compatibility
        foliar_only = [f for f in fertilizers if f.recommended_application == ApplicationMethod.FOLIAR]
        fertigation = [f for f in fertilizers if f.recommended_application == ApplicationMethod.FERTIGATION]
        if foliar_only and fertigation:
            warnings.append("Mixing foliar-only and fertigation products — verify application method")

        # Check pH conflict
        acidic = [f for f in fertilizers if f.ph_effect == PhEffect.ACIDIC]
        alkaline = [f for f in fertilizers if f.ph_effect == PhEffect.ALKALINE]
        if acidic and alkaline:
            warnings.append("Mixing acidic and alkaline fertilizers — may cause pH instability")

        safe = len(warnings) == 0
        return {"safe": safe, "warnings": warnings}

    def validate_channel(
        self,
        channel: DeliveryChannel,
        fertilizers: list[Fertilizer],
    ) -> dict:
        """Validate fertilizer combination within a specific delivery channel."""
        result = self.validate_combination(fertilizers)

        # Additional tank-safe check for fertigation channels
        if channel.application_method == ApplicationMethod.FERTIGATION:
            for fert in fertilizers:
                if not fert.tank_safe:
                    result["warnings"].append(
                        f"{fert.product_name} is not tank-safe — "
                        f"incompatible with fertigation channel '{channel.channel_id}'"
                    )
                    result["safe"] = False

        return result

    def validate_temperature(self, water_temp_celsius: float, fertilizer_type: FertilizerType) -> dict:
        """Validate water temperature for fertilizer mixing."""
        if fertilizer_type == FertilizerType.BIOLOGICAL and water_temp_celsius > 35:
            return {
                "ok": False,
                "message": f"Water temperature {water_temp_celsius}°C too high for biological products (max 35°C)",
            }
        if water_temp_celsius < 5:
            return {
                "ok": False,
                "message": f"Water temperature {water_temp_celsius}°C too low — poor dissolution",
            }
        if water_temp_celsius > 30:
            return {
                "ok": True,
                "message": f"Water temperature {water_temp_celsius}°C is high — some products may degrade faster",
            }
        return {"ok": True, "message": "Temperature is within optimal range"}


def _ph_adjustment(current_ph: float, target_ph: float) -> dict:
    """Calculate pH adjustment recommendation."""
    delta = target_ph - current_ph
    if abs(delta) < 0.2:
        return {"needed": False, "direction": "none", "delta": 0.0}
    return {
        "needed": True,
        "direction": "up" if delta > 0 else "down",
        "delta": round(abs(delta), 1),
    }
