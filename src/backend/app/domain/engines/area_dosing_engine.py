"""Area-based organic fertilizer dosing engine (REQ-004 W-013, AP-11).

Outdoor gardeners dose solid/organic amendments per area (g/m², L/m²) instead
of per solution volume (ml/L). This engine multiplies each fertilizer's
per-area application rate by the bed area to produce concrete amounts, mirrors
the step-by-step ``instructions`` style of the EC calculators, and surfaces
agronomic warnings (missing rate, N on a nitrogen fixer).
"""

from pydantic import BaseModel, Field

from app.domain.models.fertilizer import Fertilizer

# Demand level that must not receive nitrogen (REQ-004 W-013 table).
NITROGEN_FIXER = "nitrogen_fixer"


class AreaDosingItem(BaseModel):
    """One fertilizer's area-based dosage."""

    fertilizer_key: str | None = None
    product_name: str
    rate_g_per_m2: float | None = None
    rate_l_per_m2: float | None = None
    total_grams: float | None = None
    total_liters: float | None = None
    dilution_ratio: str | None = None
    nutrient_release_speed: str | None = None
    note: str | None = None


class AreaDosingResult(BaseModel):
    """Complete area-based dosing result."""

    area_m2: float
    items: list[AreaDosingItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class AreaDosingCalculator:
    """Computes per-area organic fertilizer amounts (REQ-004 W-013)."""

    def calculate(
        self,
        fertilizers: list[Fertilizer],
        area_m2: float,
        demand_level: str | None = None,
    ) -> AreaDosingResult:
        """Compute total amounts for a bed area.

        Args:
            fertilizers: Products to apply (organic/area-based).
            area_m2: Bed area in m². Must be > 0.
            demand_level: Optional plant nutrient demand
                (heavy_feeder / medium_feeder / light_feeder / nitrogen_fixer)
                used only for advisory warnings.

        Raises:
            ValueError: if ``area_m2`` is not positive (mapped to HTTP 422).
        """
        if area_m2 <= 0:
            raise ValueError("area_m2 must be greater than 0")

        items: list[AreaDosingItem] = []
        warnings: list[str] = []
        instructions: list[str] = [f"Prepare bed of {area_m2} m²."]
        step = 2

        is_n_fixer = demand_level == NITROGEN_FIXER

        for fert in fertilizers:
            total_grams: float | None = None
            total_liters: float | None = None
            note: str | None = None

            if fert.application_rate_g_per_m2 is not None:
                total_grams = round(fert.application_rate_g_per_m2 * area_m2, 1)
            if fert.application_rate_l_per_m2 is not None:
                total_liters = round(fert.application_rate_l_per_m2 * area_m2, 1)

            if total_grams is None and total_liters is None:
                warnings.append(f"{fert.product_name}: no area application rate (g/m² or L/m²) — skipped.")

            if fert.dilution_ratio:
                note = f"Dilute {fert.dilution_ratio} before applying."

            # Nitrogen fixer must not receive nitrogen (npk_ratio[0] = N).
            if is_n_fixer and fert.npk_ratio[0] > 0:
                warnings.append(
                    f"{fert.product_name}: contains nitrogen (N={fert.npk_ratio[0]}) — "
                    f"avoid N fertilizers for nitrogen-fixing plants."
                )

            items.append(
                AreaDosingItem(
                    fertilizer_key=fert.key,
                    product_name=fert.product_name,
                    rate_g_per_m2=fert.application_rate_g_per_m2,
                    rate_l_per_m2=fert.application_rate_l_per_m2,
                    total_grams=total_grams,
                    total_liters=total_liters,
                    dilution_ratio=fert.dilution_ratio,
                    nutrient_release_speed=(
                        fert.nutrient_release_speed.value if fert.nutrient_release_speed is not None else None
                    ),
                    note=note,
                )
            )

            amount_parts: list[str] = []
            if total_grams is not None:
                amount_parts.append(f"{total_grams} g")
            if total_liters is not None:
                amount_parts.append(f"{total_liters} L")
            if amount_parts:
                dilution = f" ({note})" if note else ""
                instructions.append(f"{step}. Apply {' + '.join(amount_parts)} {fert.product_name}{dilution}.")
                step += 1

        instructions.append(f"{step}. Water in and rake lightly into the topsoil.")

        return AreaDosingResult(
            area_m2=area_m2,
            items=items,
            warnings=warnings,
            instructions=instructions,
        )
