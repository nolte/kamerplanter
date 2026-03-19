"""Water mix calculation and water source validation engine.

Implements REQ-004 v3.1: WaterMixCalculator for RO/tap water blending
and CalMag correction, plus WaterSourceValidator for plausibility checks.
"""

import math
from datetime import date

from pydantic import BaseModel

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


class MixAlternative(BaseModel):
    ro_percent: int
    ec_headroom: float
    trade_off: str


class WaterMixRecommendation(BaseModel):
    recommended_ro_percent: int
    ec_headroom: float
    effective_ec_ms: float
    available_ec_for_nutrients: float
    target_ec_ms: float
    substrate_type: str
    min_headroom_ratio: float
    reasoning: str
    alternatives: list[MixAlternative]
    calmag_correction: CalMagCorrection | None = None


class WaterSourceWarning(BaseModel):
    code: str
    message: str
    severity: str


# ── WaterMixCalculator ────────────────────────────────────────────────


SUBSTRATE_HEADROOM: dict[str, float] = {
    "hydro_solution": 0.70,
    "deep_water_culture": 0.70,
    "aeroponics": 0.70,
    "coco": 0.60,
    "soil": 0.50,
    "living_soil": 0.50,
}

DEFAULT_HEADROOM = 0.60

# Per-substrate alkalinity limits (ppm CaCO₃ in blended water).
# High alkalinity demands excessive pH-Down which introduces uncontrolled
# phosphate into the nutrient solution and destabilises pH management.
SUBSTRATE_ALKALINITY_LIMIT: dict[str, float] = {
    "hydro_solution": 60.0,
    "deep_water_culture": 60.0,
    "aeroponics": 60.0,
    "coco": 80.0,
    "soil": 120.0,
    "living_soil": 150.0,  # living soil buffers well
}

DEFAULT_ALKALINITY_LIMIT = 80.0

CHLORINE_LIMIT_PPM = 0.5
CHLORAMINE_LIMIT_PPM = 0.3
FALLBACK_RO_PERCENT = 80

# Ca:Mg ratio thresholds — ideal 3:1–4:1 in the blended water.
# Above 5:1 Mg² uptake is competitively inhibited at the root.
CA_MG_RATIO_WARN = 5.0
# Minimum RO% bump when tap Ca:Mg ratio exceeds the warning threshold.
# This ensures enough dilution so a CalMag supplement can correct the ratio.
CA_MG_RATIO_MIN_RO_BUMP = 15

# Flush detection: when the phase name indicates a flush, recommend high RO
# regardless of EC headroom.
FLUSH_PHASE_NAMES = frozenset({"flushing", "flush"})
FLUSH_MIN_RO_PERCENT = 85


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
                ca_mg_warning = f"Ca:Mg ratio {ca_mg_ratio:.1f}:1 is low (ideal 3:1–4:1). Risk of calcium deficiency."
            elif ca_mg_ratio > 5.0:
                ca_mg_warning = f"Ca:Mg ratio {ca_mg_ratio:.1f}:1 is high (ideal 3:1–4:1). Risk of magnesium lockout."

        return CalMagCorrection(
            calcium_deficit_ppm=round(ca_deficit, 2),
            magnesium_deficit_ppm=round(mg_deficit, 2),
            ca_mg_ratio=ca_mg_ratio,
            ca_mg_ratio_warning=ca_mg_warning,
            needs_correction=ca_deficit > 0 or mg_deficit > 0,
        )

    def recommend_mix_ratio(
        self,
        tap: TapWaterProfile,
        ro: RoWaterProfile,
        target_ec_ms: float,
        substrate_type: str,
        target_ca_ppm: float = 0.0,
        target_mg_ppm: float = 0.0,
        phase_name: str = "",
    ) -> WaterMixRecommendation:
        """Recommend optimal RO/tap mix ratio for a given target EC and substrate.

        Iterates RO percentages from 0% to 100% in 5% steps and selects the
        lowest RO percentage that satisfies ALL constraints:
        - EC headroom >= min_headroom * target_ec
        - Effective chlorine < 0.5 ppm
        - Effective chloramine < 0.3 ppm
        - Alkalinity in blended water < substrate-specific limit
        - Ca:Mg ratio of tap water considered (min RO bump if > 5:1)
        - Flush phases force >= 85% RO

        Falls back to 80% RO if no percentage meets all criteria.
        """
        # ── Flush override ───────────────────────────────────────────
        is_flush = phase_name.lower() in FLUSH_PHASE_NAMES

        min_headroom = SUBSTRATE_HEADROOM.get(substrate_type, DEFAULT_HEADROOM)
        min_available_ec = min_headroom * target_ec_ms
        alk_limit = SUBSTRATE_ALKALINITY_LIMIT.get(substrate_type, DEFAULT_ALKALINITY_LIMIT)

        # ── Ca:Mg ratio floor ────────────────────────────────────────
        ca_mg_min_ro = 0
        if tap.magnesium_ppm > 0:
            tap_ca_mg = tap.calcium_ppm / tap.magnesium_ppm
            if tap_ca_mg > CA_MG_RATIO_WARN:
                ca_mg_min_ro = CA_MG_RATIO_MIN_RO_BUMP

        best_ro: int | None = None
        best_effective: EffectiveWaterProfile | None = None
        candidates: list[tuple[int, EffectiveWaterProfile, float]] = []

        for ro_pct in range(0, 101, 5):
            effective = self.calculate_effective_water(tap, ro, ro_pct)
            available_ec = target_ec_ms - effective.ec_ms

            meets_ec = available_ec >= min_available_ec
            meets_chlorine = effective.chlorine_ppm < CHLORINE_LIMIT_PPM
            meets_chloramine = effective.chloramine_ppm < CHLORAMINE_LIMIT_PPM
            meets_alkalinity = effective.alkalinity_ppm <= alk_limit
            meets_ca_mg_floor = ro_pct >= ca_mg_min_ro
            meets_flush = ro_pct >= FLUSH_MIN_RO_PERCENT if is_flush else True

            candidates.append((ro_pct, effective, available_ec))

            all_met = (
                meets_ec
                and meets_chlorine
                and meets_chloramine
                and meets_alkalinity
                and meets_ca_mg_floor
                and meets_flush
            )
            if all_met and best_ro is None:
                best_ro = ro_pct
                best_effective = effective

        # Fallback
        if best_ro is None:
            best_ro = max(FALLBACK_RO_PERCENT, FLUSH_MIN_RO_PERCENT if is_flush else 0)
            best_effective = self.calculate_effective_water(tap, ro, best_ro)

        assert best_effective is not None  # noqa: S101
        available_ec = target_ec_ms - best_effective.ec_ms

        # Build reasoning
        reasoning = self._build_reasoning(
            best_ro, best_effective, target_ec_ms, substrate_type,
            min_headroom, available_ec, alk_limit, is_flush,
            ca_mg_min_ro,
        )

        # Generate alternatives (±10%, ±20% from optimal, clamped to 0-100)
        alternatives = self._build_alternatives(
            best_ro, candidates, min_headroom, target_ec_ms,
        )

        # CalMag correction
        calmag: CalMagCorrection | None = None
        if target_ca_ppm > 0 or target_mg_ppm > 0:
            calmag = self.suggest_calmag_correction(
                best_effective, target_ca_ppm, target_mg_ppm,
            )

        return WaterMixRecommendation(
            recommended_ro_percent=best_ro,
            ec_headroom=round(available_ec / target_ec_ms, 3) if target_ec_ms > 0 else 0.0,
            effective_ec_ms=best_effective.ec_ms,
            available_ec_for_nutrients=round(available_ec, 4),
            target_ec_ms=target_ec_ms,
            substrate_type=substrate_type,
            min_headroom_ratio=min_headroom,
            reasoning=reasoning,
            alternatives=alternatives,
            calmag_correction=calmag,
        )

    def _build_reasoning(
        self,
        ro_pct: int,
        effective: EffectiveWaterProfile,
        target_ec: float,
        substrate_type: str,
        min_headroom: float,
        available_ec: float,
        alk_limit: float = DEFAULT_ALKALINITY_LIMIT,
        is_flush: bool = False,
        ca_mg_min_ro: int = 0,
    ) -> str:
        """Build a human-readable recommendation reasoning."""
        parts: list[str] = []

        if is_flush:
            parts.append(
                f"Flush phase: {ro_pct}% RO recommended to wash out accumulated salts."
            )
        elif ro_pct == 0:
            parts.append(
                f"No RO water needed. Tap water EC ({effective.ec_ms:.2f} mS/cm) "
                f"leaves {available_ec:.2f} mS/cm for nutrients."
            )
        elif ro_pct == FALLBACK_RO_PERCENT and available_ec < min_headroom * target_ec:
            parts.append(
                f"Fallback: {ro_pct}% RO recommended. Your tap water is very hard "
                f"(EC {effective.ec_ms:.2f} mS/cm) and no lower RO ratio meets all criteria."
            )
        else:
            parts.append(
                f"{ro_pct}% RO water recommended for {substrate_type} substrate "
                f"(requires {min_headroom:.0%} EC headroom)."
            )
            parts.append(
                f"Effective base water EC: {effective.ec_ms:.2f} mS/cm, "
                f"leaving {available_ec:.2f} mS/cm for nutrients."
            )

        # Alkalinity note
        if effective.alkalinity_ppm > alk_limit * 0.8 and not is_flush:
            parts.append(
                f"Alkalinity ({effective.alkalinity_ppm:.0f} ppm CaCO₃) "
                f"requires dilution to limit pH-Down usage and phosphate build-up."
            )

        # Ca:Mg ratio note
        if ca_mg_min_ro > 0:
            parts.append(
                "Tap water Ca:Mg ratio exceeds 5:1 — higher RO dilution "
                "recommended so CalMag supplement can correct the imbalance."
            )

        if effective.chlorine_ppm >= CHLORINE_LIMIT_PPM * 0.8:
            parts.append(
                f"Chlorine level ({effective.chlorine_ppm:.2f} ppm) is near the limit. "
                "Consider letting water sit 24h or increasing RO ratio."
            )

        return " ".join(parts)

    def _build_alternatives(
        self,
        best_ro: int,
        candidates: list[tuple[int, EffectiveWaterProfile, float]],
        min_headroom: float,
        target_ec: float,
    ) -> list[MixAlternative]:
        """Generate 2-3 alternative RO ratios with trade-off descriptions."""
        alternatives: list[MixAlternative] = []
        offsets = [-20, -10, 10, 20]

        for offset in offsets:
            alt_ro = best_ro + offset
            if alt_ro < 0 or alt_ro > 100 or alt_ro == best_ro:
                continue

            # Find matching candidate
            match = None
            for ro_pct, eff, avail in candidates:
                if ro_pct == alt_ro:
                    match = (eff, avail)
                    break

            if match is None:
                continue

            eff, avail = match
            headroom = avail / target_ec if target_ec > 0 else 0.0

            if offset < 0:
                trade_off = (
                    f"Less RO ({alt_ro}%): saves RO water but only "
                    f"{headroom:.0%} EC headroom (min {min_headroom:.0%})."
                )
                if eff.chlorine_ppm >= CHLORINE_LIMIT_PPM:
                    trade_off += " Chlorine exceeds limit."
            else:
                trade_off = (
                    f"More RO ({alt_ro}%): cleaner base water with "
                    f"{headroom:.0%} EC headroom but uses more RO water."
                )
                if headroom > 0.9:
                    trade_off += " May need more CalMag supplementation."

            alternatives.append(
                MixAlternative(
                    ro_percent=alt_ro,
                    ec_headroom=round(headroom, 3),
                    trade_off=trade_off,
                )
            )

            if len(alternatives) >= 3:
                break

        return alternatives


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
            warnings.append(
                WaterSourceWarning(
                    code="gh_plausibility",
                    message=(
                        f"GH is {profile.gh_ppm:.0f} ppm but Ca and Mg are both 0. Check your water report values."
                    ),
                    severity="warning",
                )
            )
        elif expected_gh > 0:
            deviation = abs(profile.gh_ppm - expected_gh) / expected_gh
            if deviation > self.GH_TOLERANCE:
                warnings.append(
                    WaterSourceWarning(
                        code="gh_plausibility",
                        message=(
                            f"GH ({profile.gh_ppm:.0f} ppm) deviates {deviation:.0%} from "
                            f"expected value ({expected_gh:.0f} ppm based on Ca/Mg). "
                            "Check your water report."
                        ),
                        severity="warning",
                    )
                )

        return warnings

    def validate_measurement_age(
        self,
        profile: TapWaterProfile,
        today: date | None = None,
    ) -> list[WaterSourceWarning]:
        """Warn if measurement_date is older than 12 months."""
        warnings: list[WaterSourceWarning] = []
        if profile.measurement_date is None:
            return warnings

        reference = today or date.today()
        age_days = (reference - profile.measurement_date).days
        if age_days > 365:
            months = age_days // 30
            warnings.append(
                WaterSourceWarning(
                    code="measurement_age",
                    message=(f"Water measurement is {months} months old. Consider getting a fresh water report."),
                    severity="info",
                )
            )

        return warnings

    def validate_ro_membrane(self, ro: RoWaterProfile) -> list[WaterSourceWarning]:
        """Warn if RO water EC suggests membrane degradation."""
        warnings: list[WaterSourceWarning] = []
        if ro.ec_ms > 0.05:
            warnings.append(
                WaterSourceWarning(
                    code="ro_membrane",
                    message=(f"RO water EC ({ro.ec_ms} mS/cm) is above 0.05. Your RO membrane may need replacement."),
                    severity="warning",
                )
            )
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
