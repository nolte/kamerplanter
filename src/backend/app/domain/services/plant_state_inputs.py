"""The bed-level input of a plant's visual state that will need a read (REQ-053 GP-FR-192, GP-FR-162).

The pure assembly (:func:`~app.domain.calculators.plant_state_inputs.phase_facts`,
:func:`~app.domain.calculators.plant_state_inputs.visual_state_of`) lives in the calculators layer; this module
keeps what depends on the bed's stored state.

**Frost** (:func:`frost_risk_of`) is a live reason (WP 8.20): the bed's ``microclimate.frost_risk`` is ``high`` *and*
the site's stored forecasts predict a frost within the horizon, the same expression the early warning uses
(:mod:`app.domain.engines.bed_frost_engine`). Without a verdict the reason is absent, which §11.4 allows.
"""

from __future__ import annotations

from typing import Any

from app.domain.engines.bed_frost_engine import frost_reason_active
from app.domain.models.site import Location


def frost_risk_of(location: Location, prediction: dict[str, Any] | None) -> bool:
    """Whether the bed carries the frost reason: it is ``high`` and ``prediction`` reports a frost within the forecast
    horizon (not necessarily tonight).

    ``prediction`` is the site's verdict (:func:`~app.domain.services.frost_forecast.site_frost_verdict`); ``None``
    (no source) is no frost."""
    return prediction is not None and frost_reason_active(location, prediction)


__all__ = ["frost_risk_of"]
