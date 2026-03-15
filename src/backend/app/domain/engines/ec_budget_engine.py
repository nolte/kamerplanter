"""EC-Budget calculation engine.

Implements REQ-004-A: 3-stage pipeline — water mix → EC budget → fertilizer dosing.
Calculates how to distribute available EC headroom among silicate, CalMag,
base fertilizers, and pH reserve.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.enums import FertilizerType, PhaseName, SubstrateType

# ── Constants ────────────────────────────────────────────────────────

# EC_MAX table: substrate × phase → (min, max) mS/cm
# Source: REQ-004-A §4.2
EC_MAX_TABLE: dict[SubstrateType, dict[PhaseName, tuple[float, float]]] = {
    SubstrateType.HYDRO_SOLUTION: {
        PhaseName.SEEDLING: (0.8, 1.2),
        PhaseName.VEGETATIVE: (1.6, 2.4),
        PhaseName.FLOWERING: (1.8, 2.8),
        PhaseName.FLUSHING: (0.0, 0.3),
    },
    SubstrateType.COCO: {
        PhaseName.SEEDLING: (0.8, 1.0),
        PhaseName.VEGETATIVE: (1.6, 2.0),
        PhaseName.FLOWERING: (1.8, 2.4),
        PhaseName.FLUSHING: (0.0, 0.3),
    },
    SubstrateType.SOIL: {
        PhaseName.SEEDLING: (0.4, 0.6),
        PhaseName.VEGETATIVE: (0.8, 1.4),
        PhaseName.FLOWERING: (1.0, 1.6),
        PhaseName.FLUSHING: (0.0, 0.3),
    },
}

# Alkalinity-based pH reserve (mS/cm)
PH_RESERVE: dict[str, float] = {
    "soft": 0.02,    # < 50 ppm alkalinity
    "medium": 0.03,  # 50–150 ppm
    "hard": 0.05,    # > 150 ppm
}

# Extra EC reserve per uncertain fertilizer
UNCERTAIN_EC_RESERVE = 0.15  # mS/cm

# Fresh coco CalMag boost (cycles_used == 0)
FRESH_COCO_CALMAG_BOOST = 0.20  # +20%

# Fallback max dose if not specified on product
SYSTEM_MAX_ML_PER_LITER = 20.0


# ── Input / output models ────────────────────────────────────────────


class EcBudgetFertilizerInput(BaseModel):
    """One fertilizer in the EC budget calculation."""

    key: str
    product_name: str
    ec_contribution_per_ml: float = Field(ge=0)
    ec_contribution_uncertain: bool = False
    max_dose_ml_per_liter: float | None = None
    fertilizer_type: FertilizerType = FertilizerType.BASE


class EcBudgetInput(BaseModel):
    """All inputs for a single EC budget calculation."""

    base_water_ec: float = Field(ge=0, description="EC of blended water (mS/cm)")
    target_ec: float = Field(gt=0, description="Desired final EC (mS/cm)")
    alkalinity_ppm: float = Field(default=0, ge=0, description="Water alkalinity in ppm CaCO3")
    substrate: SubstrateType = SubstrateType.COCO
    phase: PhaseName = PhaseName.VEGETATIVE
    volume_liters: float = Field(gt=0, description="Target solution volume")
    fertilizers: list[EcBudgetFertilizerInput] = Field(default_factory=list)
    recipe_ml_per_liter: dict[str, float] = Field(
        default_factory=dict,
        description="Manufacturer recipe: fertilizer key → ml/L",
    )
    # Optional pre-deduction products
    calmag_key: str | None = None
    calmag_dose_ml_per_liter: float | None = Field(default=None, ge=0)
    calmag_ec_per_ml: float = Field(default=0, ge=0)
    silicate_key: str | None = None
    silicate_dose_ml_per_liter: float | None = Field(default=None, ge=0)
    silicate_ec_per_ml: float = Field(default=0, ge=0)
    # Substrate cycles
    substrate_cycles_used: int | None = None
    # Temperature correction
    measured_ec: float | None = Field(default=None, ge=0)
    measured_temp_celsius: float | None = None


class EcSegment(BaseModel):
    """One segment of the EC budget bar."""

    label: str
    ec_contribution: float
    color_hint: str
    ml_per_liter: float = 0
    total_ml: float = 0
    warning: str | None = None


class EcBudgetResult(BaseModel):
    """Complete EC budget calculation result."""

    ec_mix: float
    ec_net: float
    ec_silicate: float = 0
    ec_calmag: float = 0
    ec_fertilizers: float = 0
    ec_ph_reserve: float = 0
    ec_final: float = 0
    ec_max: float
    ec_target: float
    ec_at_25_corrected: float | None = None
    tolerance: float
    valid: bool = True
    living_soil_bypass: bool = False
    segments: list[EcSegment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dosage_table: list[dict] = Field(default_factory=list)
    dosage_instructions: list[str] = Field(default_factory=list)


# ── Engine ────────────────────────────────────────────────────────────


class EcBudgetCalculator:
    """EC budget calculation engine (REQ-004-A)."""

    @staticmethod
    def correct_ec_at_25(measured_ec: float, temp_celsius: float) -> float:
        """Temperature-correct an EC reading to reference 25 °C.

        Formula: EC@25 = EC_measured / (1 + 0.02 × (T - 25))
        """
        factor = 1 + 0.02 * (temp_celsius - 25)
        if factor <= 0:
            return measured_ec
        return round(measured_ec / factor, 4)

    def calculate(self, inp: EcBudgetInput) -> EcBudgetResult:
        """Run the full EC budget pipeline."""
        warnings: list[str] = []
        segments: list[EcSegment] = []
        dosage_table: list[dict] = []
        instructions: list[str] = []

        # ── Living Soil bypass ────────────────────────────────────
        if inp.substrate == SubstrateType.LIVING_SOIL:
            warnings.append(
                "Living Soil: EC-based dosing is not applicable. "
                "Use organic amendments (compost tea, top dress, g/m²) "
                "as per REQ-004 organic fertilization guidelines."
            )
            return EcBudgetResult(
                ec_mix=inp.base_water_ec,
                ec_net=0,
                ec_max=0,
                ec_target=inp.target_ec,
                tolerance=0,
                valid=True,
                living_soil_bypass=True,
                warnings=warnings,
            )

        # ── Temperature correction ────────────────────────────────
        ec_at_25: float | None = None
        if inp.measured_ec is not None and inp.measured_temp_celsius is not None:
            ec_at_25 = self.correct_ec_at_25(inp.measured_ec, inp.measured_temp_celsius)

        # ── EC max lookup ─────────────────────────────────────────
        phase_table = EC_MAX_TABLE.get(inp.substrate, EC_MAX_TABLE[SubstrateType.SOIL])
        ec_range = phase_table.get(inp.phase, (0.8, 2.0))
        ec_max = ec_range[1]

        # ── Base water segment ────────────────────────────────────
        ec_mix = inp.base_water_ec
        segments.append(EcSegment(
            label="Base water",
            ec_contribution=ec_mix,
            color_hint="bluegrey",
        ))
        instructions.append(f"1. Fill container with {inp.volume_liters}L of blended water (EC {ec_mix} mS)")

        # ── EC net ────────────────────────────────────────────────
        ec_net = max(0, inp.target_ec - ec_mix)
        if ec_net <= 0:
            warnings.append(
                f"Base water EC ({ec_mix} mS) meets or exceeds target EC ({inp.target_ec} mS). "
                "Increase RO percentage or lower target EC."
            )

        remaining = ec_net
        step = 2

        # ── pH reserve ────────────────────────────────────────────
        if inp.alkalinity_ppm < 50:
            ph_reserve = PH_RESERVE["soft"]
        elif inp.alkalinity_ppm <= 150:
            ph_reserve = PH_RESERVE["medium"]
        else:
            ph_reserve = PH_RESERVE["hard"]

        # ── Silicate pre-deduction ────────────────────────────────
        ec_silicate = 0.0
        if inp.silicate_key and inp.silicate_dose_ml_per_liter and inp.silicate_ec_per_ml > 0:
            dose = inp.silicate_dose_ml_per_liter
            ec_silicate = dose * inp.silicate_ec_per_ml
            remaining -= ec_silicate

            # Check for uncertain EC
            si_fert = next(
                (f for f in inp.fertilizers if f.key == inp.silicate_key),
                None,
            )
            if si_fert and si_fert.ec_contribution_uncertain:
                remaining -= UNCERTAIN_EC_RESERVE
                warnings.append(
                    f"{si_fert.product_name}: EC contribution is uncertain. "
                    f"Extra {UNCERTAIN_EC_RESERVE} mS reserve applied. Measure EC after adding."
                )

            segments.append(EcSegment(
                label="Silicate",
                ec_contribution=ec_silicate,
                color_hint="teal",
                ml_per_liter=dose,
                total_ml=round(dose * inp.volume_liters, 1),
            ))
            dosage_table.append({
                "key": inp.silicate_key,
                "product_name": inp.silicate_key,
                "ml_per_liter": round(dose, 2),
                "total_ml": round(dose * inp.volume_liters, 1),
                "ec_contribution": round(ec_silicate, 3),
            })
            instructions.append(
                f"{step}. Add silicate ({inp.silicate_key}): "
                f"{round(dose * inp.volume_liters, 1)}ml ({dose} ml/L) — stir well, wait 5 min"
            )
            step += 1

        # ── CalMag pre-deduction ──────────────────────────────────
        ec_calmag = 0.0
        if inp.calmag_key and inp.calmag_dose_ml_per_liter and inp.calmag_ec_per_ml > 0:
            dose = inp.calmag_dose_ml_per_liter

            # Fresh coco boost
            if (
                inp.substrate == SubstrateType.COCO
                and inp.substrate_cycles_used is not None
                and inp.substrate_cycles_used == 0
            ):
                dose = round(dose * (1 + FRESH_COCO_CALMAG_BOOST), 2)
                warnings.append(
                    f"Fresh coco (first use): CalMag dose increased by "
                    f"{FRESH_COCO_CALMAG_BOOST:.0%} to {dose} ml/L"
                )

            ec_calmag = dose * inp.calmag_ec_per_ml
            remaining -= ec_calmag

            segments.append(EcSegment(
                label="CalMag",
                ec_contribution=ec_calmag,
                color_hint="orange",
                ml_per_liter=dose,
                total_ml=round(dose * inp.volume_liters, 1),
            ))
            dosage_table.append({
                "key": inp.calmag_key,
                "product_name": inp.calmag_key,
                "ml_per_liter": round(dose, 2),
                "total_ml": round(dose * inp.volume_liters, 1),
                "ec_contribution": round(ec_calmag, 3),
            })
            instructions.append(
                f"{step}. Add CalMag ({inp.calmag_key}): "
                f"{round(dose * inp.volume_liters, 1)}ml ({dose} ml/L) — mix thoroughly"
            )
            step += 1

        # ── Subtract pH reserve from remaining ────────────────────
        remaining -= ph_reserve

        # ── Fertilizer dosing (recipe scaling or equal share) ─────
        ec_fertilizers = 0.0
        ferts = [f for f in inp.fertilizers if f.ec_contribution_per_ml > 0]

        # Track uncertain fertilizers for reserve
        uncertain_ferts = [f for f in ferts if f.ec_contribution_uncertain]
        uncertain_reserve_total = UNCERTAIN_EC_RESERVE * len(uncertain_ferts)
        remaining -= uncertain_reserve_total

        if uncertain_ferts:
            for uf in uncertain_ferts:
                warnings.append(
                    f"{uf.product_name}: EC contribution is uncertain. "
                    f"Extra {UNCERTAIN_EC_RESERVE} mS reserve applied. Measure EC after adding."
                )

        if remaining > 0 and ferts:
            # Try recipe scaling first
            recipe = inp.recipe_ml_per_liter
            ec_recipe = sum(
                recipe.get(f.key, 0.0) * f.ec_contribution_per_ml
                for f in ferts
            )

            use_recipe_scaling = ec_recipe > 0

            if use_recipe_scaling:
                k = remaining / ec_recipe
                for f in ferts:
                    recipe_dose = recipe.get(f.key, 0.0)
                    ml_per_liter = k * recipe_dose

                    # Cap at max dose
                    max_dose = f.max_dose_ml_per_liter or SYSTEM_MAX_ML_PER_LITER
                    if ml_per_liter > max_dose:
                        warnings.append(
                            f"{f.product_name}: dose capped at {max_dose} ml/L "
                            f"(calculated {ml_per_liter:.2f} ml/L)"
                        )
                        ml_per_liter = max_dose

                    ec_contrib = ml_per_liter * f.ec_contribution_per_ml
                    ec_fertilizers += ec_contrib
                    total_ml = ml_per_liter * inp.volume_liters

                    segments.append(EcSegment(
                        label=f.product_name,
                        ec_contribution=round(ec_contrib, 3),
                        color_hint="green",
                        ml_per_liter=round(ml_per_liter, 2),
                        total_ml=round(total_ml, 1),
                    ))
                    dosage_table.append({
                        "key": f.key,
                        "product_name": f.product_name,
                        "ml_per_liter": round(ml_per_liter, 2),
                        "total_ml": round(total_ml, 1),
                        "ec_contribution": round(ec_contrib, 3),
                    })
                    instructions.append(
                        f"{step}. Add {f.product_name}: "
                        f"{round(total_ml, 1)}ml ({round(ml_per_liter, 2)} ml/L) — mix thoroughly"
                    )
                    step += 1
            else:
                # Equal share fallback
                equal_share = remaining / len(ferts)
                for f in ferts:
                    ml_per_liter = equal_share / f.ec_contribution_per_ml

                    max_dose = f.max_dose_ml_per_liter or SYSTEM_MAX_ML_PER_LITER
                    if ml_per_liter > max_dose:
                        warnings.append(
                            f"{f.product_name}: dose capped at {max_dose} ml/L "
                            f"(calculated {ml_per_liter:.2f} ml/L)"
                        )
                        ml_per_liter = max_dose

                    ec_contrib = ml_per_liter * f.ec_contribution_per_ml
                    ec_fertilizers += ec_contrib
                    total_ml = ml_per_liter * inp.volume_liters

                    segments.append(EcSegment(
                        label=f.product_name,
                        ec_contribution=round(ec_contrib, 3),
                        color_hint="green",
                        ml_per_liter=round(ml_per_liter, 2),
                        total_ml=round(total_ml, 1),
                    ))
                    dosage_table.append({
                        "key": f.key,
                        "product_name": f.product_name,
                        "ml_per_liter": round(ml_per_liter, 2),
                        "total_ml": round(total_ml, 1),
                        "ec_contribution": round(ec_contrib, 3),
                    })
                    instructions.append(
                        f"{step}. Add {f.product_name}: "
                        f"{round(total_ml, 1)}ml ({round(ml_per_liter, 2)} ml/L) — mix thoroughly"
                    )
                    step += 1

        # ── pH reserve segment ────────────────────────────────────
        segments.append(EcSegment(
            label="pH reserve",
            ec_contribution=ph_reserve,
            color_hint="grey",
        ))
        instructions.append(f"{step}. Adjust pH to target — stir and wait 5 min")
        step += 1
        instructions.append(f"{step}. Verify final EC reading")

        # ── Final EC ──────────────────────────────────────────────
        ec_final = ec_mix + ec_silicate + ec_calmag + ec_fertilizers + ph_reserve

        # ── Validation ────────────────────────────────────────────
        tolerance = max(0.1, inp.target_ec * 0.10)
        valid = True

        if ec_final > ec_max:
            valid = False
            warnings.append(
                f"Final EC ({ec_final:.2f} mS) exceeds phase/substrate maximum "
                f"({ec_max:.1f} mS) for {inp.phase.value} on {inp.substrate.value}."
            )

        if abs(ec_final - inp.target_ec) > tolerance:
            valid = False
            warnings.append(
                f"Final EC ({ec_final:.2f} mS) deviates from target ({inp.target_ec:.2f} mS) "
                f"by {abs(ec_final - inp.target_ec):.2f} mS (tolerance ±{tolerance:.2f} mS)."
            )

        return EcBudgetResult(
            ec_mix=round(ec_mix, 4),
            ec_net=round(ec_net, 4),
            ec_silicate=round(ec_silicate, 4),
            ec_calmag=round(ec_calmag, 4),
            ec_fertilizers=round(ec_fertilizers, 4),
            ec_ph_reserve=ph_reserve,
            ec_final=round(ec_final, 4),
            ec_max=ec_max,
            ec_target=inp.target_ec,
            ec_at_25_corrected=ec_at_25,
            tolerance=tolerance,
            valid=valid,
            living_soil_bypass=False,
            segments=segments,
            warnings=warnings,
            dosage_table=dosage_table,
            dosage_instructions=instructions,
        )
