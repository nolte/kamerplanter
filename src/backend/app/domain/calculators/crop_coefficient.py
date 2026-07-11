"""REQ-037 — crop-coefficient (Kc) resolution cascade.

The crop coefficient Kc scales reference evapotranspiration ET₀ into the
crop-specific ETc (``ETc = ET₀ × Kc``). Kc is resolved through a deterministic
cascade so a precise, phase-level value always wins over a coarse default:

1. **Growth phase** — ``GrowthPhase.crop_coefficient_kc`` (expert-maintained, most
   specific: Kc varies strongly across the initial/mid/late season stages).
2. **Species** — ``Species.default_crop_coefficient_kc`` (a representative
   season-average for the species).
3. **Plant-category table** — :data:`KC_DEFAULTS` (a coarse FAO-56-derived
   mid-season default per :class:`PlantCategory`).
4. **Global default** — :data:`GLOBAL_DEFAULT_KC` (0.8), a neutral mid-range value.

The resolver returns both the value and a ``source`` label so the API/UI can show
where a Kc came from and the expert override is auditable.
"""

from __future__ import annotations

from typing import Literal

from app.common.enums import PlantCategory
from app.domain.calculators.evapotranspiration_calculator import GLOBAL_DEFAULT_KC

#: Where a resolved Kc originated (surfaced to the API/UI).
KcSource = Literal["phase", "species", "category_default", "global_default"]

#: Coarse FAO-56-derived mid-season crop coefficients per plant category. These
#: are deliberately representative single values (not the full initial/mid/late
#: curve); the phase- and species-level overrides carry the finer resolution.
KC_DEFAULTS: dict[PlantCategory, float] = {
    PlantCategory.OUTDOOR_VEGETABLE: 1.05,
    PlantCategory.OUTDOOR_ORNAMENTAL: 0.9,
    PlantCategory.BALCONY_PLANT: 0.9,
    PlantCategory.HERB: 0.9,
    PlantCategory.BULB_TUBER: 0.85,
    PlantCategory.TROPICAL_FOLIAGE: 0.8,
    PlantCategory.INDOOR_HOUSEPLANT: 0.75,
    PlantCategory.ORCHID: 0.7,
    PlantCategory.SUCCULENT_CACTUS: 0.4,
}

#: Valid Kc range (FAO-56): bare/dormant surfaces sit near the low end, dense
#: fully-developed canopies with advection can exceed 1.2.
_KC_MIN = 0.1
_KC_MAX = 1.5


def resolve_kc(
    *,
    phase_kc: float | None = None,
    species_kc: float | None = None,
    plant_category: PlantCategory | None = None,
) -> tuple[float, KcSource]:
    """Resolve the effective crop coefficient and its provenance.

    Applies the phase → species → category → global cascade and clamps the result
    to the physically sensible FAO-56 range ``[0.1, 1.5]``.
    """
    if phase_kc is not None:
        return _clamp(phase_kc), "phase"
    if species_kc is not None:
        return _clamp(species_kc), "species"
    if plant_category is not None and plant_category in KC_DEFAULTS:
        return _clamp(KC_DEFAULTS[plant_category]), "category_default"
    return GLOBAL_DEFAULT_KC, "global_default"


def _clamp(value: float) -> float:
    return round(max(_KC_MIN, min(_KC_MAX, value)), 3)
