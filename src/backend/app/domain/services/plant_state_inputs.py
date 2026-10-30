"""The bed-level input of a plant's visual state that will need a read (REQ-053 GP-FR-192, GP-FR-162).

The pure assembly (:func:`~app.domain.calculators.plant_state_inputs.phase_facts`,
:func:`~app.domain.calculators.plant_state_inputs.visual_state_of`) lives in the calculators layer; this module
keeps what depends on the bed's stored state.

**Frost** (:func:`frost_risk_of`) has no source yet: the bed's ``microclimate.frost_risk`` arrives with WP 3.9
(GP-FR-162). Until then the reason is absent (operator question 2 of #2455), which §11.4 allows (a missing source
drops its reason without an error).
"""

from __future__ import annotations

from app.domain.models.site import Location


def frost_risk_of(location: Location) -> bool:
    """Whether the bed is at frost risk now; ``False`` until WP 3.9 adds ``microclimate.frost_risk``."""
    del location
    return False


__all__ = ["frost_risk_of"]
