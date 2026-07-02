"""Automatic-transition trigger evaluation (REQ-003 E1/E2 + gdd_based).

Decides whether a non-time-based transition rule should fire. Pure decision
logic — the caller (the ``check_auto_transitions`` Celery task) gathers the
context (day length, accumulated chill days, accumulated GDD) and passes it in,
so this engine stays trivially testable and free of I/O.

Reuses the existing calculators/trackers rather than re-deriving the maths:
``photoperiod_calculator`` for the short-/long-day threshold and
``VernalizationTracker`` for the chill-day completion.
"""

from __future__ import annotations

from app.common.enums import PhotoperiodType
from app.domain.calculators.photoperiod_calculator import (
    is_long_day_triggered,
    is_short_day_triggered,
)
from app.domain.engines.vernalization_tracker import VernalizationTracker


class TransitionTriggerEvaluator:
    """Evaluates the non-time-based auto-transition triggers."""

    def __init__(self) -> None:
        self._vernalization = VernalizationTracker()

    def photoperiod_should_fire(
        self,
        photoperiod_type: PhotoperiodType,
        critical_day_length_hours: float | None,
        day_length_hours: float,
    ) -> bool:
        """E1: fire when the effective photoperiod crosses the species' critical
        day length. Short-day species induce when the day is *shorter* than
        critical (cannabis 12/12, poinsettia); long-day species when *longer*.
        Day-neutral species never fire on photoperiod.
        """
        if critical_day_length_hours is None:
            return False
        if photoperiod_type == PhotoperiodType.SHORT_DAY:
            return is_short_day_triggered(day_length_hours, critical_day_length_hours)
        if photoperiod_type == PhotoperiodType.LONG_DAY:
            return is_long_day_triggered(day_length_hours, critical_day_length_hours)
        return False

    def vernalization_should_fire(
        self,
        vernalization_min_days: int | None,
        chill_days_accumulated: int,
    ) -> bool:
        """E2: fire once the accumulated chill days reach the species requirement
        (gates biennial ``bolting`` / perennial ``bud_break``)."""
        if not vernalization_min_days:
            return False
        progress = self._vernalization.calculate_vernalization_progress(chill_days_accumulated, vernalization_min_days)
        return bool(progress["is_complete"])

    def gdd_should_fire(self, gdd_threshold: float | None, accumulated_gdd: float) -> bool:
        """gdd_based: fire once the accumulated growing-degree-days reach the
        rule's threshold (``required_conditions.gdd_threshold``)."""
        if gdd_threshold is None:
            return False
        return accumulated_gdd >= gdd_threshold
