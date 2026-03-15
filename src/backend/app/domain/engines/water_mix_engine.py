"""Water mix calculation and water source validation engine.

Implements REQ-004 v3.1: WaterMixCalculator for RO/tap water blending
and CalMag correction, plus WaterSourceValidator for plausibility checks.
"""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.domain.models.site import RoWaterProfile, TapWaterProfile

# ── Result types ──────────────────────────────────────────────────────


class EffectiveWaterProfile(BaseModel):
    ec_ms: float
    ph: float
    alkalinity_ppm: float
    calcium_ppm: float
    magnesium_ppm: float
    chlorine_ppm: float
    chloramine_ppm: float


class CalMagCorrection(BaseModel):
    calcium_deficit_ppm: float
    magnesium_deficit_ppm: float
    ca_mg_ratio: float | None = None
    ca_mg_ratio_warning: str | None = None
    needs_correction: bool


class WaterSourceWarning(BaseModel):
    code: str
    message: str
    severity: str


# ── WaterMixCalculator ────────────────────────────────────────────────


class WaterMixCalculator:
    """Calculate effective water parameters from RO/tap mixing."""

    def calculate_effective_water(
        self,
        tap: TapWaterProfile,
        ro: RoWaterProfile,
        ro_percent: int,
    ) -> EffectiveWaterProfile:
        """Calculate blended water profile from tap and RO water.

        EC and mineral concentrations use linear weighted average.
        pH uses logarithmic mixing (H⁺ concentration space):
            pH_mix = -log10(10^(-pH_ro) × ratio + 10^(-pH_tap) × (1 - ratio))
        """
        ratio = ro_percent / 100.0
        tap_ratio = 1.0 - ratio

        # Logarithmic pH mixing via H⁺ concentration
        h_mix = (10 ** (-ro.ph)) * ratio + (10 ** (-tap.ph)) * tap_ratio
        ph_mix = -math.log10(h_mix) if h_mix > 0 else (ro.ph * ratio + tap.ph * tap_ratio)

        return EffectiveWaterProfile(
            ec_ms=round(ro.ec_ms * ratio + tap.ec_ms * tap_ratio, 4),
            ph=round(ph_mix, 2),
            alkalinity_ppm=round(tap.alkalinity_ppm * tap_ratio, 2),
            calcium_ppm=round(tap.calcium_ppm * tap_ratio, 2),
            magnesium_ppm=round(tap.magnesium_ppm * tap_ratio, 2),
            chlorine_ppm=round(tap.chlorine_ppm * tap_ratio, 2),
            chloramine_ppm=round(tap.chloramine_ppm * tap_ratio, 2),
        )

    def calculate_ro_percent_for_target(
        self,
        tap: TapWaterProfile,
        ro: RoWaterProfile,
        target_ec_ms: float,
    ) -> int:
        """Reverse calculation: determine RO% needed to reach target EC.

        Formula: r = (EC_tap - EC_target) / (EC_tap - EC_ro) × 100
        Returns clamped to 0–100.
        """
        if tap.ec_ms <= ro.ec_ms:
            return 0
        if target_ec_ms >= tap.ec_ms:
            return 0
        if target_ec_ms <= ro.ec_ms:
            return 100
        ratio = (tap.ec_ms - target_ec_ms) / (tap.ec_ms - ro.ec_ms)
        return max(0, min(100, round(ratio * 100)))

    def suggest_calmag_correction(
        self,
        effective: EffectiveWaterProfile,
        target_ca_ppm: float,
        target_mg_ppm: float,
    ) -> CalMagCorrection:
        """Calculate CalMag supplement needed to reach target levels.

        Also validates Ca:Mg ratio — ideal is 3:1 to 4:1.
        Warns if ratio < 2.0 or > 5.0.
        """
        ca_deficit = max(0.0, target_ca_ppm - effective.calcium_ppm)
        mg_deficit = max(0.0, target_mg_ppm - effective.magnesium_ppm)

        # Ca:Mg ratio check on target levels
        ca_mg_ratio: float | None = None
        ca_mg_warning: str | None = None
        if target_mg_ppm > 0:
            ca_mg_ratio = round(target_ca_ppm / target_mg_ppm, 2)
            if ca_mg_ratio < 2.0:
                ca_mg_warning = (
                    f"Ca:Mg ratio {ca_mg_ratio:.1f}:1 is low (ideal 3:1–4:1). "
                    "Risk of calcium deficiency."
                )
            elif ca_mg_ratio > 5.0:
                ca_mg_warning = (
                    f"Ca:Mg ratio {ca_mg_ratio:.1f}:1 is high (ideal 3:1–4:1). "
                    "Risk of magnesium lockout."
                )

        return CalMagCorrection(
            calcium_deficit_ppm=round(ca_deficit, 2),
            magnesium_deficit_ppm=round(mg_deficit, 2),
            ca_mg_ratio=ca_mg_ratio,
            ca_mg_ratio_warning=ca_mg_warning,
            needs_correction=ca_deficit > 0 or mg_deficit > 0,
        )


# ── WaterSourceValidator ──────────────────────────────────────────────


class WaterSourceValidator:
    """Validate water source profiles and generate warnings."""

    GH_TOLERANCE = 0.30  # 30% deviation threshold

    def validate_gh_plausibility(self, profile: TapWaterProfile) -> list[WaterSourceWarning]:
        """Check if GH value is plausible given Ca and Mg concentrations.

        Expected GH (ppm CaCO3) = Ca * 2.497 + Mg * 4.116
        Warns if reported GH deviates by more than 30%.
        """
        warnings: list[WaterSourceWarning] = []
        if profile.gh_ppm == 0 and profile.calcium_ppm == 0 and profile.magnesium_ppm == 0:
            return warnings

        expected_gh = profile.calcium_ppm * 2.497 + profile.magnesium_ppm * 4.116

        if expected_gh == 0 and profile.gh_ppm > 0:
            warnings.append(WaterSourceWarning(
                code="gh_plausibility",
                message=(
                    f"GH is {profile.gh_ppm:.0f} ppm but Ca and Mg are both 0. "
                    "Check your water report values."
                ),
                severity="warning",
            ))
        elif expected_gh > 0:
            deviation = abs(profile.gh_ppm - expected_gh) / expected_gh
            if deviation > self.GH_TOLERANCE:
                warnings.append(WaterSourceWarning(
                    code="gh_plausibility",
                    message=(
                        f"GH ({profile.gh_ppm:.0f} ppm) deviates {deviation:.0%} from "
                        f"expected value ({expected_gh:.0f} ppm based on Ca/Mg). "
                        "Check your water report."
                    ),
                    severity="warning",
                ))

        return warnings

    def validate_measurement_age(
        self, profile: TapWaterProfile, today: date | None = None,
    ) -> list[WaterSourceWarning]:
        """Warn if measurement_date is older than 12 months."""
        warnings: list[WaterSourceWarning] = []
        if profile.measurement_date is None:
            return warnings

        reference = today or date.today()
        age_days = (reference - profile.measurement_date).days
        if age_days > 365:
            months = age_days // 30
            warnings.append(WaterSourceWarning(
                code="measurement_age",
                message=(
                    f"Water measurement is {months} months old. "
                    "Consider getting a fresh water report."
                ),
                severity="info",
            ))

        return warnings

    def validate_ro_membrane(self, ro: RoWaterProfile) -> list[WaterSourceWarning]:
        """Warn if RO water EC suggests membrane degradation."""
        warnings: list[WaterSourceWarning] = []
        if ro.ec_ms > 0.05:
            warnings.append(WaterSourceWarning(
                code="ro_membrane",
                message=(
                    f"RO water EC ({ro.ec_ms} mS/cm) is above 0.05. "
                    "Your RO membrane may need replacement."
                ),
                severity="warning",
            ))
        return warnings

    def validate_all(
        self,
        tap: TapWaterProfile | None,
        ro: RoWaterProfile | None,
        today: date | None = None,
    ) -> list[WaterSourceWarning]:
        """Run all applicable validations and return combined warnings."""
        warnings: list[WaterSourceWarning] = []
        if tap is not None:
            warnings.extend(self.validate_gh_plausibility(tap))
            warnings.extend(self.validate_measurement_age(tap, today))
        if ro is not None:
            warnings.extend(self.validate_ro_membrane(ro))
        return warnings
