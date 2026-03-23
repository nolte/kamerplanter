"""Dosage calculation engine for normalized EC dosing with runtime adaptation.

Implements REQ-004 section 4b: 3-stage pipeline that calculates actual fertilizer
dosages based on the user's water profile (tap water EC, RO availability, mixing ratio).

Pipeline stages:
1. WaterMixCalculator -> effective water profile
2. CalMag correction -> fill mineral gaps
3. EC budget scaling -> scale dosages proportionally
"""

from typing import Literal

import structlog
from pydantic import BaseModel, Field

from app.domain.engines.ec_budget_engine import FRESH_COCO_CALMAG_BOOST, PH_RESERVE
from app.domain.engines.substrate_ec_adapter import SubstrateEcAdapter
from app.domain.engines.water_mix_engine import (
    CalMagCorrection,
    EffectiveWaterProfile,
    WaterMixCalculator,
)
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry
from app.domain.models.site import RoWaterProfile, TapWaterProfile

logger = structlog.get_logger()

# ── Constants ────────────────────────────────────────────────────────

# EC contribution per ml for CalMag product (default if not specified)
DEFAULT_CALMAG_EC_PER_ML = 0.10

# Approximate ppm per ml/L for typical CalMag products (Terra Aquatica CalMag)
# Ca 3.2% = ~32 ppm per ml/L, Mg 1.2% = ~12 ppm per ml/L
CALMAG_CA_PPM_PER_ML = 32.0
CALMAG_MG_PPM_PER_ML = 12.0


# ── Input / Output models ────────────────────────────────────────────


class DosageCalculationInput(BaseModel):
    """All inputs for a dosage calculation."""

    phase_entry: NutrientPlanPhaseEntry
    channel_id: str | None = None
    volume_liters: float = Field(gt=0)
    tap_water: TapWaterProfile | None = None
    ro_water: RoWaterProfile | None = None
    ro_percent_override: int | None = Field(default=None, ge=0, le=100)
    substrate_type: str = "soil"
    substrate_cycles_used: int | None = None
    calmag_product: Fertilizer | None = None
    fertilizer_lookup: dict[str, Fertilizer] = Field(default_factory=dict)
    plan_reference_substrate_type: str = "soil"


class DosageEntry(BaseModel):
    """One dosage line in the calculation result."""

    product_name: str
    fertilizer_key: str | None = None
    ml_per_liter: float
    total_ml: float
    ec_contribution: float
    source: Literal["reference", "scaled", "auto_calmag"]
    mixing_order: int = 0


class EcBudgetSummary(BaseModel):
    """Simplified EC budget breakdown."""

    ec_base_water: float
    ec_calmag: float
    ec_ph_reserve: float
    ec_fertilizers: float
    ec_final: float


class DosageCalculationResult(BaseModel):
    """Complete dosage calculation result."""

    phase_name: str
    channel_id: str
    target_ec_ms: float
    effective_water: EffectiveWaterProfile | None = None
    ro_percent_used: int
    calmag_correction: CalMagCorrection | None = None
    calmag_dosage: DosageEntry | None = None
    ec_budget: EcBudgetSummary
    scaling_factor: float
    dosages: list[DosageEntry]
    mixing_instructions: list[str]
    warnings: list[str]
    reference_ec_ms: float | None = None
    substrate_correction_applied: bool = False


# ── Engine ────────────────────────────────────────────────────────────


class DosageCalculationEngine:
    """Orchestrates the 3-stage dosage calculation pipeline.

    Stage 1: Water blending (WaterMixCalculator)
    Stage 2: CalMag correction
    Stage 3: EC budget scaling (proportional recipe scaling)
    """

    def __init__(self) -> None:
        self._water_calc = WaterMixCalculator()
        self._substrate_adapter = SubstrateEcAdapter()

    def calculate(self, inp: DosageCalculationInput) -> DosageCalculationResult:
        """Run the full dosage calculation pipeline."""
        warnings: list[str] = []
        entry = inp.phase_entry

        # Resolve target EC: phase-level is single source of truth,
        # channel-level is optional override. Apply substrate conversion if needed.
        channel, channel_id = self._resolve_channel(entry, inp.channel_id)
        target_ec, ref_ec, substrate_corrected = self._resolve_target_ec(
            entry,
            channel,
            inp.plan_reference_substrate_type,
            inp.substrate_type,
        )

        if target_ec <= 0:
            result = self._build_reference_result(
                entry,
                channel_id,
                target_ec,
                inp.volume_liters,
                inp.fertilizer_lookup,
                warnings=["Target EC is 0 — returning reference dosages (flush/germination phase)."],
            )
            result.reference_ec_ms = ref_ec
            result.substrate_correction_applied = substrate_corrected
            return result

        # Legacy mode: no reference_base_ec set or no water profiles
        has_water_profiles = inp.tap_water is not None
        is_legacy = entry.reference_base_ec is None

        if is_legacy or not has_water_profiles:
            reason = (
                "No water profile provided — returning reference dosages."
                if not is_legacy
                else "Legacy plan without reference_base_ec — returning reference dosages unchanged."
            )
            result = self._build_reference_result(
                entry,
                channel_id,
                target_ec,
                inp.volume_liters,
                inp.fertilizer_lookup,
                warnings=[reason],
            )
            result.reference_ec_ms = ref_ec
            result.substrate_correction_applied = substrate_corrected
            return result

        # ── Stage 1: Calculate effective water ─────────────────────
        effective_water: EffectiveWaterProfile | None = None
        ro_percent_used = 0

        if inp.tap_water and inp.ro_water:
            # Determine RO percentage
            if inp.ro_percent_override is not None:
                ro_percent_used = inp.ro_percent_override
            elif entry.water_mix_ratio_ro_percent is not None:
                ro_percent_used = entry.water_mix_ratio_ro_percent
            else:
                # Use WaterMixCalculator to recommend optimal mix
                phase_name_str = entry.phase_name.value if hasattr(entry.phase_name, "value") else str(entry.phase_name)
                recommendation = self._water_calc.recommend_mix_ratio(
                    tap=inp.tap_water,
                    ro=inp.ro_water,
                    target_ec_ms=target_ec,
                    substrate_type=inp.substrate_type,
                    phase_name=phase_name_str,
                )
                ro_percent_used = recommendation.recommended_ro_percent

            effective_water = self._water_calc.calculate_effective_water(
                tap=inp.tap_water,
                ro=inp.ro_water,
                ro_percent=ro_percent_used,
            )
        elif inp.tap_water:
            # Tap water only, no RO
            ro_percent_used = 0
            effective_water = EffectiveWaterProfile(
                ec_ms=inp.tap_water.ec_ms,
                ph=inp.tap_water.ph,
                alkalinity_ppm=inp.tap_water.alkalinity_ppm,
                calcium_ppm=inp.tap_water.calcium_ppm,
                magnesium_ppm=inp.tap_water.magnesium_ppm,
                chlorine_ppm=inp.tap_water.chlorine_ppm,
                chloramine_ppm=inp.tap_water.chloramine_ppm,
            )

        base_water_ec = effective_water.ec_ms if effective_water else 0.0

        # High RO warning — no pH buffer
        if ro_percent_used >= 80:
            warnings.append("High RO percentage (>=80%): almost no pH buffer (KH~0). Check pH after mixing.")

        # ── Stage 2: CalMag correction ─────────────────────────────
        calmag_correction: CalMagCorrection | None = None
        calmag_dosage: DosageEntry | None = None
        ec_calmag = 0.0

        if entry.target_calcium_ppm is None and entry.target_magnesium_ppm is None:
            warnings.append(
                "No target_calcium_ppm/target_magnesium_ppm set on phase entry. CalMag calculation skipped."
            )
        elif effective_water is not None:
            target_ca = entry.target_calcium_ppm or 0.0
            target_mg = entry.target_magnesium_ppm or 0.0

            calmag_correction = self._water_calc.suggest_calmag_correction(
                effective=effective_water,
                target_ca_ppm=target_ca,
                target_mg_ppm=target_mg,
            )

            if calmag_correction.needs_correction:
                calmag_dosage, ec_calmag = self._calculate_calmag_dosage(
                    correction=calmag_correction,
                    calmag_product=inp.calmag_product,
                    volume_liters=inp.volume_liters,
                    substrate_type=inp.substrate_type,
                    substrate_cycles_used=inp.substrate_cycles_used,
                    warnings=warnings,
                )

            if calmag_correction.ca_mg_ratio_warning:
                warnings.append(calmag_correction.ca_mg_ratio_warning)

        # ── Stage 3: EC budget scaling ─────────────────────────────
        alkalinity = effective_water.alkalinity_ppm if effective_water else 0.0
        ph_reserve = self._get_ph_reserve(alkalinity)

        ec_available_for_ferts = max(0.0, target_ec - base_water_ec - ec_calmag - ph_reserve)

        # Calculate reference EC from channel dosages
        reference_ec = self._calculate_reference_ec(
            channel,
            inp.fertilizer_lookup,
        )

        scaling_factor = ec_available_for_ferts / reference_ec if reference_ec > 0 else 1.0

        # Build scaled dosages
        dosages = self._build_scaled_dosages(
            channel=channel,
            fertilizer_lookup=inp.fertilizer_lookup,
            scaling_factor=scaling_factor,
            volume_liters=inp.volume_liters,
        )

        # Insert CalMag dosage at the front (sorted by mixing_order later)
        if calmag_dosage is not None:
            dosages.insert(0, calmag_dosage)

        # Sort by mixing_order
        dosages.sort(key=lambda d: d.mixing_order)

        # Calculate actual EC from fertilizers (after scaling)
        ec_fertilizers = sum(d.ec_contribution for d in dosages if d.source != "auto_calmag")
        ec_final = base_water_ec + ec_calmag + ph_reserve + ec_fertilizers

        # Build mixing instructions
        mixing_instructions = self._build_mixing_instructions(
            dosages=dosages,
            volume_liters=inp.volume_liters,
            ro_percent=ro_percent_used,
            base_water_ec=base_water_ec,
            target_ec=target_ec,
        )

        return DosageCalculationResult(
            phase_name=entry.phase_name.value,
            channel_id=channel_id,
            target_ec_ms=target_ec,
            effective_water=effective_water,
            ro_percent_used=ro_percent_used,
            calmag_correction=calmag_correction,
            calmag_dosage=calmag_dosage,
            ec_budget=EcBudgetSummary(
                ec_base_water=round(base_water_ec, 4),
                ec_calmag=round(ec_calmag, 4),
                ec_ph_reserve=round(ph_reserve, 4),
                ec_fertilizers=round(ec_fertilizers, 4),
                ec_final=round(ec_final, 4),
            ),
            scaling_factor=round(scaling_factor, 4),
            dosages=dosages,
            mixing_instructions=mixing_instructions,
            warnings=warnings,
            reference_ec_ms=ref_ec,
            substrate_correction_applied=substrate_corrected,
        )

    # ── Private helpers ───────────────────────────────────────────────

    def _resolve_channel(
        self,
        entry: NutrientPlanPhaseEntry,
        channel_id: str | None,
    ) -> tuple[object, str]:
        """Find the target delivery channel.

        Returns (channel, channel_id). If no channels exist, returns a
        sentinel with empty dosages.
        """
        if not entry.delivery_channels:
            return _EmptyChannel(), channel_id or "default"

        if channel_id:
            for ch in entry.delivery_channels:
                if ch.channel_id == channel_id:
                    return ch, channel_id
            # Channel not found — fall through to first fertigation channel

        # Default: first fertigation channel, or first channel
        for ch in entry.delivery_channels:
            if ch.application_method.value == "fertigation":
                return ch, ch.channel_id
        return entry.delivery_channels[0], entry.delivery_channels[0].channel_id

    def _resolve_target_ec(
        self,
        entry: NutrientPlanPhaseEntry,
        channel: object,
        plan_ref_substrate: str = "soil",
        runtime_substrate: str = "soil",
    ) -> tuple[float, float | None, bool]:
        """Resolve target EC with optional substrate conversion.

        Returns (effective_ec, reference_ec_ms, substrate_correction_applied).

        When reference_ec_ms is set on the phase entry, it is treated as the
        single source of truth and converted from the plan's reference substrate
        to the runtime substrate. Legacy entries without reference_ec_ms fall
        back to target_ec_ms / channel target_ec_ms unchanged.
        """
        phase_name = entry.phase_name.value if hasattr(entry.phase_name, "value") else str(entry.phase_name)

        # New path: reference_ec_ms is the SSOT
        ref_ec = entry.reference_ec_ms
        if ref_ec is not None:
            if ref_ec <= 0:
                return 0.0, ref_ec, False
            if plan_ref_substrate != runtime_substrate:
                effective_ec = self._substrate_adapter.convert_ec(
                    ref_ec,
                    plan_ref_substrate,
                    runtime_substrate,
                    phase_name,
                )
                return effective_ec, ref_ec, True
            return ref_ec, ref_ec, False

        # Legacy fallback: target_ec_ms directly (no substrate conversion)
        if entry.target_ec_ms is not None and entry.target_ec_ms > 0:
            return entry.target_ec_ms, None, False

        # Fallback: channel-level target_ec_ms
        channel_ec = getattr(channel, "target_ec_ms", None)
        if channel_ec is not None and channel_ec > 0:
            return channel_ec, None, False

        return 0.0, None, False

    def _calculate_reference_ec(
        self,
        channel: object,
        fertilizer_lookup: dict[str, Fertilizer],
    ) -> float:
        """Calculate total EC from reference dosages (only EC-contributing products)."""
        total_ec = 0.0
        dosages = getattr(channel, "fertilizer_dosages", [])
        for dosage in dosages:
            fert = fertilizer_lookup.get(dosage.fertilizer_key)
            if fert and fert.ec_contribution_per_ml > 0:
                total_ec += dosage.ml_per_liter * fert.ec_contribution_per_ml
        return total_ec

    def _calculate_calmag_dosage(
        self,
        correction: CalMagCorrection,
        calmag_product: Fertilizer | None,
        volume_liters: float,
        substrate_type: str,
        substrate_cycles_used: int | None,
        warnings: list[str],
    ) -> tuple[DosageEntry, float]:
        """Calculate CalMag dosage from mineral deficit."""
        # Determine CalMag EC per ml
        calmag_ec_per_ml = DEFAULT_CALMAG_EC_PER_ML
        calmag_name = "CalMag"
        calmag_key: str | None = None
        calmag_mixing_order = 8  # Default mixing priority for CalMag

        if calmag_product:
            calmag_ec_per_ml = calmag_product.ec_contribution_per_ml or DEFAULT_CALMAG_EC_PER_ML
            calmag_name = calmag_product.product_name
            calmag_key = calmag_product.key
            calmag_mixing_order = calmag_product.mixing_priority

        # Calculate dose from Ca deficit (primary driver)
        # Ca deficit drives the dose; Mg comes along proportionally
        ca_deficit = correction.calcium_deficit_ppm
        mg_deficit = correction.magnesium_deficit_ppm

        # Use the higher demand (Ca or Mg) to determine dose
        dose_from_ca = ca_deficit / CALMAG_CA_PPM_PER_ML if ca_deficit > 0 else 0.0
        dose_from_mg = mg_deficit / CALMAG_MG_PPM_PER_ML if mg_deficit > 0 else 0.0
        calmag_ml_per_liter = max(dose_from_ca, dose_from_mg)

        # Fresh coco boost
        if substrate_type == "coco" and substrate_cycles_used is not None and substrate_cycles_used == 0:
            calmag_ml_per_liter = round(
                calmag_ml_per_liter * (1 + FRESH_COCO_CALMAG_BOOST),
                2,
            )
            warnings.append(
                f"Fresh coco (first use): CalMag dose increased by "
                f"{FRESH_COCO_CALMAG_BOOST:.0%} to {calmag_ml_per_liter:.2f} ml/L."
            )

        calmag_ml_per_liter = round(calmag_ml_per_liter, 2)
        ec_contribution = round(calmag_ml_per_liter * calmag_ec_per_ml, 4)
        total_ml = round(calmag_ml_per_liter * volume_liters, 1)

        dosage = DosageEntry(
            product_name=calmag_name,
            fertilizer_key=calmag_key,
            ml_per_liter=calmag_ml_per_liter,
            total_ml=total_ml,
            ec_contribution=ec_contribution,
            source="auto_calmag",
            mixing_order=calmag_mixing_order,
        )

        return dosage, ec_contribution

    def _build_scaled_dosages(
        self,
        channel: object,
        fertilizer_lookup: dict[str, Fertilizer],
        scaling_factor: float,
        volume_liters: float,
    ) -> list[DosageEntry]:
        """Build scaled dosage entries from channel reference dosages."""
        dosages: list[DosageEntry] = []
        channel_dosages = getattr(channel, "fertilizer_dosages", [])

        for ref_dosage in channel_dosages:
            fert = fertilizer_lookup.get(ref_dosage.fertilizer_key)
            fert_name = fert.product_name if fert else ref_dosage.fertilizer_key
            ec_per_ml = fert.ec_contribution_per_ml if fert else 0.0
            mixing_order = fert.mixing_priority if fert else 50

            if ec_per_ml <= 0:
                # Products with no EC contribution keep their reference dose
                ml_per_liter = ref_dosage.ml_per_liter
                source: Literal["reference", "scaled", "auto_calmag"] = "reference"
            else:
                ml_per_liter = round(ref_dosage.ml_per_liter * scaling_factor, 2)
                source = "scaled"

            ec_contribution = round(ml_per_liter * ec_per_ml, 4)
            total_ml = round(ml_per_liter * volume_liters, 1)

            dosages.append(
                DosageEntry(
                    product_name=fert_name,
                    fertilizer_key=ref_dosage.fertilizer_key,
                    ml_per_liter=ml_per_liter,
                    total_ml=total_ml,
                    ec_contribution=ec_contribution,
                    source=source,
                    mixing_order=mixing_order,
                ),
            )

        return dosages

    def _build_reference_result(
        self,
        entry: NutrientPlanPhaseEntry,
        channel_id: str,
        target_ec: float,
        volume_liters: float,
        fertilizer_lookup: dict[str, Fertilizer],
        warnings: list[str] | None = None,
    ) -> DosageCalculationResult:
        """Build a result with unmodified reference dosages (no scaling)."""
        channel, resolved_id = self._resolve_channel(entry, channel_id)
        dosages: list[DosageEntry] = []
        ec_total = 0.0

        for ref_dosage in getattr(channel, "fertilizer_dosages", []):
            fert = fertilizer_lookup.get(ref_dosage.fertilizer_key)
            fert_name = fert.product_name if fert else ref_dosage.fertilizer_key
            ec_per_ml = fert.ec_contribution_per_ml if fert else 0.0
            mixing_order = fert.mixing_priority if fert else 50
            ec_contribution = round(ref_dosage.ml_per_liter * ec_per_ml, 4)
            ec_total += ec_contribution

            dosages.append(
                DosageEntry(
                    product_name=fert_name,
                    fertilizer_key=ref_dosage.fertilizer_key,
                    ml_per_liter=ref_dosage.ml_per_liter,
                    total_ml=round(ref_dosage.ml_per_liter * volume_liters, 1),
                    ec_contribution=ec_contribution,
                    source="reference",
                    mixing_order=mixing_order,
                ),
            )

        dosages.sort(key=lambda d: d.mixing_order)

        instructions = self._build_mixing_instructions(
            dosages=dosages,
            volume_liters=volume_liters,
            ro_percent=0,
            base_water_ec=0.0,
            target_ec=target_ec,
        )

        return DosageCalculationResult(
            phase_name=entry.phase_name.value,
            channel_id=resolved_id,
            target_ec_ms=target_ec,
            effective_water=None,
            ro_percent_used=0,
            calmag_correction=None,
            calmag_dosage=None,
            ec_budget=EcBudgetSummary(
                ec_base_water=0.0,
                ec_calmag=0.0,
                ec_ph_reserve=0.0,
                ec_fertilizers=round(ec_total, 4),
                ec_final=round(ec_total, 4),
            ),
            scaling_factor=1.0,
            dosages=dosages,
            mixing_instructions=instructions,
            warnings=warnings or [],
        )

    @staticmethod
    def _get_ph_reserve(alkalinity_ppm: float) -> float:
        """Determine pH reserve based on water alkalinity."""
        if alkalinity_ppm < 50:
            return PH_RESERVE["soft"]
        if alkalinity_ppm <= 150:
            return PH_RESERVE["medium"]
        return PH_RESERVE["hard"]

    @staticmethod
    def _build_mixing_instructions(
        dosages: list[DosageEntry],
        volume_liters: float,
        ro_percent: int,
        base_water_ec: float,
        target_ec: float,
    ) -> list[str]:
        """Generate step-by-step mixing instructions."""
        instructions: list[str] = []
        step = 1

        # Water preparation
        if ro_percent > 0:
            tap_percent = 100 - ro_percent
            instructions.append(
                f"{step}. Prepare {volume_liters}L water "
                f"({ro_percent}% RO / {tap_percent}% tap water, "
                f"base EC: {base_water_ec:.2f} mS)"
            )
        else:
            instructions.append(f"{step}. Prepare {volume_liters}L water")
        step += 1

        # Dosage steps
        for dosage in dosages:
            verb = "mix thoroughly" if dosage.source != "reference" else "stir well"
            wait = " -- wait 5 min" if "Rhino" in dosage.product_name or "Silic" in dosage.product_name else ""
            instructions.append(
                f"{step}. Add {dosage.product_name}: "
                f"{dosage.total_ml}ml ({dosage.ml_per_liter:.2f} ml/L) -- {verb}{wait}"
            )
            step += 1

        # pH adjustment
        instructions.append(f"{step}. Adjust pH to target -- stir and wait 5 min")
        step += 1

        # Final EC check
        if target_ec > 0:
            instructions.append(f"{step}. Verify final EC reading (target: {target_ec:.2f} mS)")

        return instructions


class _EmptyChannel:
    """Sentinel for entries without delivery channels."""

    fertilizer_dosages: list = []  # noqa: RUF012
    target_ec_ms: float | None = None
    application_method = type("_AM", (), {"value": "drench"})()
