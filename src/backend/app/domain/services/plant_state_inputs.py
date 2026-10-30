"""The one assembly of a plant's visual state from its stored facts (REQ-053 GP-FR-192, GP-UX-005/059/060).

``GET /locations/{key}/plant-states`` (:class:`~app.domain.services.plant_state_service.PlantStateService`) and the
plan's SVG/PDF (:class:`~app.domain.services.garden_plan_export_service.GardenPlanExportService`) both turn a
:class:`~app.domain.interfaces.plant_state_repository.PlantStateSource` into a
:class:`~app.domain.calculators.plant_state_calculator.PlantVisualState` here, so a plant has the same ring and the
same badge on the screen and on paper. Pure functions: no I/O, ``now`` is an argument.

**Frost** (:func:`frost_risk_of`) has no source yet: the bed's ``microclimate.frost_risk`` arrives with WP 3.9
(GP-FR-162). Until then the reason is absent (operator question 2 of #2455), which §11.4 allows (a missing source
drops its reason without an error).
"""

from __future__ import annotations

from datetime import datetime

from app.domain.calculators.plant_state_calculator import PhaseFacts, PlantFacts, PlantVisualState, compute
from app.domain.interfaces.plant_state_repository import PlantStateSource
from app.domain.models.site import Location


def phase_facts(row: PlantStateSource) -> PhaseFacts | None:
    """The phase the calculator reads; a phase without a recorded start counts from the planting day."""
    if not row.phase_key:
        return None
    return PhaseFacts(
        key=row.phase_key,
        started_on=row.phase_started_on or row.planted_on,
        typical_days=row.phase_typical_days,
        allows_harvest=row.phase_allows_harvest,
        is_terminal=row.phase_is_terminal,
    )


def frost_risk_of(location: Location) -> bool:
    """Whether the bed is at frost risk now; ``False`` until WP 3.9 adds ``microclimate.frost_risk``."""
    del location
    return False


def visual_state_of(row: PlantStateSource, *, frost_risk: bool, now: datetime) -> PlantVisualState:
    """The visual state of the standing plant ``row`` at ``now`` in a bed with the given frost input."""
    return compute(
        PlantFacts(),
        phase_facts(row),
        row.open_tasks,
        open_findings=row.open_finding_count,
        frost_risk=frost_risk,
        harvest_batches=row.harvest_batch_count,
        now=now,
    )


__all__ = ["frost_risk_of", "phase_facts", "visual_state_of"]
