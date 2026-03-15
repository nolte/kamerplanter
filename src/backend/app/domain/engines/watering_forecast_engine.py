"""Pure domain engine for projecting future watering dates from a CareProfile."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.domain.models.care_reminder import CareProfile


class PhaseInterval(BaseModel):
    """A time span with a phase-specific watering interval."""

    phase_name: str
    start_date: date
    end_date: date
    interval_days: int = Field(ge=1, le=90)


class WateringForecastEngine:
    """Generate projected watering dates within a date range.

    Uses the CareProfile interval with seasonal/winter adjustments
    to project forward from the last watering confirmation.

    When phase_intervals are provided, uses the phase-specific interval
    for dates falling within that phase.  Resolution order:
      1. Cultivar phase_watering_overrides (passed via phase_intervals)
      2. GrowthPhase.watering_interval_days (passed via phase_intervals)
      3. CareProfile.watering_interval_learned or watering_interval_days (fallback)
    """

    def generate_forecast(
        self,
        profile: CareProfile,
        last_watering_date: date,
        forecast_start: date,
        forecast_end: date,
        hemisphere: str = "north",
        phase_intervals: list[PhaseInterval] | None = None,
    ) -> list[date]:
        """Generate projected watering dates within the date range."""
        if forecast_start > forecast_end:
            return []

        dates: list[date] = []
        current = last_watering_date

        # Walk forward from last watering until we pass forecast_end
        max_iterations = 500  # safety cap
        for _ in range(max_iterations):
            interval = self._interval_for_date(
                profile, current, hemisphere, phase_intervals,
            )
            current = current + timedelta(days=interval)

            if current > forecast_end:
                break
            if current >= forecast_start:
                dates.append(current)

        return dates

    @staticmethod
    def _interval_for_date(
        profile: CareProfile,
        ref_date: date,
        hemisphere: str,
        phase_intervals: list[PhaseInterval] | None = None,
    ) -> int:
        """Get the watering interval applicable at a given date.

        Priority: phase-specific interval > learned interval > base interval.
        Winter multiplier is applied to whatever base is resolved.
        """
        # Check phase-specific interval
        phase_base: int | None = None
        if phase_intervals:
            for pi in phase_intervals:
                if pi.start_date <= ref_date <= pi.end_date:
                    phase_base = pi.interval_days
                    break

        base = phase_base or profile.watering_interval_learned or profile.watering_interval_days
        month = ref_date.month

        is_winter = (
            month in (6, 7, 8) if hemisphere == "south" else month in (12, 1, 2)
        )
        if is_winter:
            return max(1, int(base * profile.winter_watering_multiplier))
        return base
