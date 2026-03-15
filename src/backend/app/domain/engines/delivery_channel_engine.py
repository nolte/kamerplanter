"""DeliveryChannel validation and helper logic (REQ-004 Multi-Channel Delivery)."""

from typing import TYPE_CHECKING

from app.common.enums import ApplicationMethod

if TYPE_CHECKING:
    from app.domain.models.fertilizer import Fertilizer
    from app.domain.models.nutrient_plan import DeliveryChannel

EC_TOLERANCE_FIXED = 0.3  # mS — legacy, kept for reference


def ec_tolerance(target_ec: float) -> float:
    """Phase-dependent EC tolerance (REQ-004-A §5.5).

    At low EC targets (e.g. seedling 0.6 mS), a fixed 0.3 tolerance
    is 50% — far too loose. This uses 10% of target with 0.1 floor.
    """
    return max(0.1, target_ec * 0.10)


class DeliveryChannelValidator:
    """Validates delivery channels within a NutrientPlanPhaseEntry."""

    def validate_channels(
        self,
        channels: list[DeliveryChannel],
        fertilizers: dict[str, Fertilizer],
    ) -> dict:
        """Validate all channels in a phase entry.

        Returns:
            {
                "valid": bool,
                "channel_results": [
                    {
                        "channel_id": str,
                        "label": str,
                        "issues": [str],
                        "ec_budget": {"target": float, "calculated": float, "delta": float} | None,
                    }
                ],
            }
        """
        channel_results: list[dict] = []
        all_valid = True

        # Check unique IDs
        ids = [ch.channel_id for ch in channels]
        if len(ids) != len(set(ids)):
            return {
                "valid": False,
                "channel_results": [
                    {
                        "channel_id": "global",
                        "label": "",
                        "issues": ["Duplicate channel_id values found"],
                        "ec_budget": None,
                    }
                ],
            }

        for channel in channels:
            issues: list[str] = []
            ec_budget = None

            # Per-channel EC budget check
            if channel.target_ec_ms is not None and channel.fertilizer_dosages:
                calculated_ec = 0.0
                for dosage in channel.fertilizer_dosages:
                    fert = fertilizers.get(dosage.fertilizer_key)
                    if fert is None:
                        issues.append(f"Unknown fertilizer: {dosage.fertilizer_key}")
                        continue
                    calculated_ec += dosage.ml_per_liter * fert.ec_contribution_per_ml

                delta = abs(channel.target_ec_ms - calculated_ec)
                tolerance = ec_tolerance(channel.target_ec_ms)
                ec_budget = {
                    "target": channel.target_ec_ms,
                    "calculated": round(calculated_ec, 2),
                    "delta": round(delta, 2),
                    "tolerance": round(tolerance, 2),
                }
                if delta > tolerance:
                    issues.append(
                        f"EC mismatch: target {channel.target_ec_ms} mS, "
                        f"calculated {calculated_ec:.2f} mS "
                        f"(delta {delta:.2f}, tolerance {tolerance:.2f})"
                    )

            # Tank-safe check for fertigation channels
            if channel.application_method == ApplicationMethod.FERTIGATION:
                for dosage in channel.fertilizer_dosages:
                    fert = fertilizers.get(dosage.fertilizer_key)
                    if fert is not None and not fert.tank_safe:
                        issues.append(
                            f"{fert.product_name} is not tank-safe — "
                            f"do not use in fertigation channel '{channel.channel_id}'"
                        )

            # recommended_application mismatch warnings
            for dosage in channel.fertilizer_dosages:
                fert = fertilizers.get(dosage.fertilizer_key)
                if fert is None:
                    continue
                if (
                    fert.recommended_application != ApplicationMethod.ANY
                    and fert.recommended_application != channel.application_method
                ):
                    issues.append(
                        f"{fert.product_name} recommended for "
                        f"{fert.recommended_application.value}, "
                        f"but channel uses {channel.application_method.value}"
                    )

            if issues:
                all_valid = False

            channel_results.append(
                {
                    "channel_id": channel.channel_id,
                    "label": channel.label,
                    "issues": issues,
                    "ec_budget": ec_budget,
                }
            )

        return {"valid": all_valid, "channel_results": channel_results}
