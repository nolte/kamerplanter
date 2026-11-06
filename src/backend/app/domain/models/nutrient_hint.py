"""The nutrient hint of a bed (REQ-053 GP-FR-125, W-010; WP 8.10, #2653): what the bed summary shows.

A state, a confidence and reason codes - **never a number** (no N amount, no dose, no class value). The rules that
produce it are the pure :mod:`app.domain.engines.nutrient_hint_engine`; this module only holds the result type, so
the read model of the bed summary (:class:`~app.domain.models.garden_plan.BedSummaryView`) can carry it without the
model layer importing an engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

NutrientHintState = Literal["ok", "check", "likely_deficit", "insufficient_data"]
NutrientHintConfidence = Literal["low", "medium", "high"]

#: Every reason code the engine can give; additive only (each code has a DE/EN text under
#: ``enums.nutrientHintReason``).
NutrientHintReason = Literal[
    # Why there is no assessment.
    "substrate_bed",
    "no_current_crop",
    "demand_unknown",
    "thresholds_without_source",
    # What decided the state.
    "no_feeding_recorded",
    "feeding_overdue",
    "feeding_due",
    "fed_recently",
    "p_class_low",
    "k_class_low",
    "content_classes_sufficient",
    # Qualitative flags (never an amount).
    "demand_partly_unknown",
    "preceding_nitrogen_fixer",
    "bark_mulch_n_binding",
    "p_or_k_class_high",
]

NUTRIENT_HINT_STATES: tuple[NutrientHintState, ...] = ("ok", "check", "likely_deficit", "insufficient_data")
NUTRIENT_HINT_REASONS: tuple[NutrientHintReason, ...] = (
    "substrate_bed",
    "no_current_crop",
    "demand_unknown",
    "thresholds_without_source",
    "no_feeding_recorded",
    "feeding_overdue",
    "feeding_due",
    "fed_recently",
    "p_class_low",
    "k_class_low",
    "content_classes_sufficient",
    "demand_partly_unknown",
    "preceding_nitrogen_fixer",
    "bark_mulch_n_binding",
    "p_or_k_class_high",
)


@dataclass(frozen=True)
class NutrientHint:
    """The assessment of one bed.

    ``compost_and_p_withheld`` is ``True`` when a lab result by CAL puts P or K into class D or E: the hint then never
    points to compost or a phosphorus fertiliser (review U-004, R-006). ``sources`` names the source of every
    threshold that took part in the state - empty for ``insufficient_data``.
    """

    state: NutrientHintState
    confidence: NutrientHintConfidence
    reasons: tuple[NutrientHintReason, ...] = ()
    compost_and_p_withheld: bool = False
    sources: tuple[str, ...] = field(default_factory=tuple)
