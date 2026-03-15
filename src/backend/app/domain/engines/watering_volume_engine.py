"""Pure domain engine for calculating suggested watering volumes.

Combines phase requirements, species watering guide, substrate properties,
and container size into a single volume recommendation.

Resolution order (highest priority first):
  1. Phase RequirementProfile.irrigation_volume_ml_per_plant (if set and > 0)
  2. Species/Cultivar WateringGuide.volume_ml_min/max (with seasonal adjustments)
  3. Container-based calculation: container_volume_liters * substrate_ratio
  4. Fallback default: 250 ml
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date

    from app.common.enums import IrrigationStrategy, SubstrateType, WaterRetention


class VolumeSuggestion(BaseModel):
    """Recommended watering volume for a single plant."""

    volume_ml: int = Field(ge=0, description="Recommended volume in milliliters")
    volume_ml_min: int = Field(ge=0, description="Lower bound of recommended range")
    volume_ml_max: int = Field(ge=0, description="Upper bound of recommended range")
    source: str = Field(description="Which data source determined the volume")
    adjustments: list[str] = Field(
        default_factory=list,
        description="Applied adjustments (phase, seasonal, substrate, etc.)",
    )


# ── Substrate watering ratio: fraction of container volume per watering ──
# Moved from CalendarAggregationEngine so it's reusable.
SUBSTRATE_WATERING_RATIO: dict[str, float] = {
    "clay_pebbles": 0.25,
    "hydro_solution": 0.30,
    "coco": 0.20,
    "perlite": 0.20,
    "rockwool_slab": 0.15,
    "rockwool_plug": 0.15,
    "sphagnum": 0.20,
    "orchid_bark": 0.20,
    "pon_mineral": 0.20,
    "soil": 0.15,
    "living_soil": 0.12,
    "peat": 0.15,
    "vermiculite": 0.15,
    "none": 0.20,
}

# ── Water retention modifier: adjusts base ratio up/down ──
_RETENTION_MODIFIER: dict[str, float] = {
    "low": 1.20,     # low retention → more water needed per event
    "medium": 1.00,
    "high": 0.80,    # high retention → less water needed per event
}

# ── Irrigation strategy modifier ──
_STRATEGY_MODIFIER: dict[str, float] = {
    "infrequent": 1.30,   # larger volume per event (less frequent)
    "moderate": 1.00,
    "frequent": 0.70,     # smaller volume per event (more frequent)
    "continuous": 0.50,   # minimal per event (always running)
}

# ── Phase factor: multiplier relative to vegetative baseline ──
_PHASE_FACTOR: dict[str, float] = {
    "germination": 0.30,
    "seedling": 0.50,
    "vegetative": 1.00,
    "flowering": 1.20,
    "flushing": 1.40,
    "dormancy": 0.25,
    "harvest": 0.60,
}

DEFAULT_VOLUME_ML = 250
DEFAULT_RANGE_PERCENT = 0.25  # +-25% for min/max when only a point estimate is available


class WateringVolumeEngine:
    """Pure calculation engine — no database access."""

    def suggest_volume(
        self,
        *,
        container_volume_liters: float | None = None,
        substrate_type: SubstrateType | str | None = None,
        water_retention: WaterRetention | str | None = None,
        water_holding_capacity_percent: float | None = None,
        irrigation_strategy: IrrigationStrategy | str | None = None,
        phase_name: str | None = None,
        phase_irrigation_volume_ml: int | None = None,
        species_volume_ml_min: int | None = None,
        species_volume_ml_max: int | None = None,
        species_seasonal_adjustments: list[dict] | None = None,
        reference_date: date | None = None,
        hemisphere: str = "north",
    ) -> VolumeSuggestion:
        """Calculate a volume suggestion combining all available inputs.

        Args:
            container_volume_liters: Pot/container size in liters.
            substrate_type: SubstrateType enum value or string.
            water_retention: WaterRetention enum value or string.
            water_holding_capacity_percent: Fine-grained WHC if known (0-100).
            irrigation_strategy: IrrigationStrategy enum value or string.
            phase_name: Current growth phase (e.g., "vegetative", "flowering").
            phase_irrigation_volume_ml: Explicit per-phase volume from RequirementProfile.
            species_volume_ml_min: WateringGuide lower bound.
            species_volume_ml_max: WateringGuide upper bound.
            species_seasonal_adjustments: List of SeasonalWateringAdjustment dicts.
            reference_date: Date for seasonal lookup (defaults to today).
            hemisphere: "north" or "south" for seasonal logic.

        Returns:
            VolumeSuggestion with recommended volume and metadata.
        """
        adjustments: list[str] = []
        source: str = "fallback_default"
        volume_ml: float = DEFAULT_VOLUME_ML
        vol_min: float | None = None
        vol_max: float | None = None

        # ── 1. Try phase RequirementProfile override ───────────────────
        if phase_irrigation_volume_ml is not None and phase_irrigation_volume_ml > 0:
            volume_ml = float(phase_irrigation_volume_ml)
            source = "phase_requirement_profile"
            adjustments.append(f"phase_override={phase_irrigation_volume_ml}ml")

        # ── 2. Try species/cultivar WateringGuide ──────────────────────
        elif species_volume_ml_min is not None and species_volume_ml_max is not None:
            seasonal = self._apply_seasonal(
                species_volume_ml_min,
                species_volume_ml_max,
                species_seasonal_adjustments,
                reference_date,
            )
            vol_min = float(seasonal[0])
            vol_max = float(seasonal[1])
            volume_ml = (vol_min + vol_max) / 2.0
            source = "species_watering_guide"
            if seasonal[2]:
                adjustments.append(f"seasonal_adjustment={seasonal[2]}")

        # ── 3. Try container-based calculation ─────────────────────────
        elif container_volume_liters is not None and container_volume_liters > 0:
            substrate_key = str(substrate_type).lower() if substrate_type else ""
            ratio = SUBSTRATE_WATERING_RATIO.get(substrate_key, 0.15)
            volume_ml = container_volume_liters * ratio * 1000  # L → ml
            source = "container_substrate_calculation"
            adjustments.append(f"base_ratio={ratio}")

        # ── Apply substrate modifiers (retention + strategy) ───────────
        volume_ml = self._apply_retention_modifier(
            volume_ml, water_retention, water_holding_capacity_percent, adjustments,
        )
        volume_ml = self._apply_strategy_modifier(
            volume_ml, irrigation_strategy, adjustments,
        )

        # ── Apply phase factor (if not already from RequirementProfile) ─
        if source != "phase_requirement_profile" and phase_name:
            factor = _PHASE_FACTOR.get(phase_name.lower(), 1.0)
            if factor != 1.0:
                volume_ml *= factor
                if vol_min is not None:
                    vol_min *= factor
                if vol_max is not None:
                    vol_max *= factor
                adjustments.append(f"phase_factor={phase_name}*{factor}")

        # ── Scale species guide by container size if both available ────
        if source == "species_watering_guide" and container_volume_liters is not None:
            scale = self._container_scale_factor(container_volume_liters)
            if scale != 1.0:
                volume_ml *= scale
                if vol_min is not None:
                    vol_min *= scale
                if vol_max is not None:
                    vol_max *= scale
                adjustments.append(f"container_scale={scale:.2f}")

        # ── Finalize min/max range ─────────────────────────────────────
        final_ml = max(10, round(volume_ml))  # minimum 10ml
        if vol_min is not None and vol_max is not None:
            final_min = max(10, round(vol_min))
            final_max = max(final_min, round(vol_max))
        else:
            final_min = max(10, round(final_ml * (1 - DEFAULT_RANGE_PERCENT)))
            final_max = round(final_ml * (1 + DEFAULT_RANGE_PERCENT))

        return VolumeSuggestion(
            volume_ml=final_ml,
            volume_ml_min=final_min,
            volume_ml_max=final_max,
            source=source,
            adjustments=adjustments,
        )

    # ── Private helpers ────────────────────────────────────────────────

    @staticmethod
    def _apply_seasonal(
        vol_min: int,
        vol_max: int,
        seasonal_adjustments: list[dict] | None,
        reference_date: date | None,
    ) -> tuple[int, int, str]:
        """Apply seasonal override if the current month matches."""
        if not seasonal_adjustments or not reference_date:
            return vol_min, vol_max, ""
        month = reference_date.month
        for adj in seasonal_adjustments:
            months = adj.get("months", [])
            if month in months:
                adj_min = adj.get("volume_ml_min", 0)
                adj_max = adj.get("volume_ml_max", 0)
                label = adj.get("label", "")
                if adj_min > 0 and adj_max > 0:
                    return adj_min, adj_max, label
                if adj_min > 0:
                    return adj_min, vol_max, label
        return vol_min, vol_max, ""

    @staticmethod
    def _apply_retention_modifier(
        volume_ml: float,
        water_retention: WaterRetention | str | None,
        water_holding_capacity_percent: float | None,
        adjustments: list[str],
    ) -> float:
        """Adjust volume based on substrate water retention."""
        # Prefer fine-grained WHC if available
        if water_holding_capacity_percent is not None:
            # WHC 50% = baseline (modifier 1.0), lower WHC → more water, higher → less
            whc_modifier = 1.0 + (50.0 - water_holding_capacity_percent) / 100.0
            whc_modifier = max(0.5, min(1.5, whc_modifier))  # clamp
            if abs(whc_modifier - 1.0) > 0.01:
                volume_ml *= whc_modifier
                adjustments.append(f"whc={water_holding_capacity_percent}%→*{whc_modifier:.2f}")
            return volume_ml

        if water_retention:
            key = str(water_retention).lower()
            modifier = _RETENTION_MODIFIER.get(key, 1.0)
            if modifier != 1.0:
                volume_ml *= modifier
                adjustments.append(f"retention={key}→*{modifier}")
        return volume_ml

    @staticmethod
    def _apply_strategy_modifier(
        volume_ml: float,
        irrigation_strategy: IrrigationStrategy | str | None,
        adjustments: list[str],
    ) -> float:
        """Adjust volume based on irrigation strategy (frequency affects per-event volume)."""
        if irrigation_strategy:
            key = str(irrigation_strategy).lower()
            modifier = _STRATEGY_MODIFIER.get(key, 1.0)
            if modifier != 1.0:
                volume_ml *= modifier
                adjustments.append(f"strategy={key}→*{modifier}")
        return volume_ml

    @staticmethod
    def _container_scale_factor(container_volume_liters: float) -> float:
        """Scale species-based volume suggestions by container size.

        Species WateringGuide volumes assume a "typical" container (~5L).
        Scale proportionally for significantly different container sizes.
        """
        reference_liters = 5.0
        if container_volume_liters <= 0:
            return 1.0
        raw_scale = container_volume_liters / reference_liters
        # Dampen scaling: sqrt to prevent linear blow-up for large containers
        # e.g. 20L pot → scale = sqrt(4) = 2.0x, not 4.0x
        if raw_scale > 1.0:
            return raw_scale ** 0.5
        # For small pots, scale linearly (already < 1.0)
        return max(0.2, raw_scale)
