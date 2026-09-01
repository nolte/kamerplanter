from datetime import datetime, timedelta

from app.common.datetimes import ensure_aware_utc


class SafetyIntervalValidator:
    """Pure logic for Karenz/safety interval validation -- no DB access."""

    def can_harvest(
        self,
        active_karenz_periods: list[dict],
        planned_harvest_date: datetime,
    ) -> tuple[bool, list[dict]]:
        """Check if harvest is safe given active karenz periods.

        Args:
            active_karenz_periods: List of dicts with keys:
                - active_ingredient: str
                - applied_at: datetime
                - safety_interval_days: int
            planned_harvest_date: When the harvest is planned.

        Returns:
            (can_harvest, blocking_treatments) where blocking_treatments
            contains dicts with active_ingredient, safe_date, days_remaining.
        """
        blocking = []
        planned = ensure_aware_utc(planned_harvest_date)
        for period in active_karenz_periods:
            applied_at = ensure_aware_utc(period["applied_at"])
            safety_days = period["safety_interval_days"]
            safe_date = applied_at + timedelta(days=safety_days)
            if safe_date > planned:
                days_remaining = (safe_date - planned).days
                blocking.append(
                    {
                        "active_ingredient": period["active_ingredient"],
                        "safe_date": safe_date.isoformat(),
                        "days_remaining": days_remaining,
                    }
                )
        return len(blocking) == 0, blocking

    def earliest_safe_harvest_date(
        self,
        active_karenz_periods: list[dict],
    ) -> datetime | None:
        """Calculate the earliest date when harvest is safe.

        Returns None if there are no active karenz periods.
        """
        if not active_karenz_periods:
            return None
        latest = None
        for period in active_karenz_periods:
            applied_at = ensure_aware_utc(period["applied_at"])
            # recurrence-owner-ok: a Karenz period is a one-shot waiting time between
            # treatment and harvest (PflSchG), not a cadence — nothing recurs, so there is
            # no rule for RecurrenceEngine to advance. The word `interval` in the field name
            # is what the scan sees; the identical shift at line 32 is invisible to it
            # because that operand is spelled `safety_days`.
            safe_date = applied_at + timedelta(days=period["safety_interval_days"])
            if latest is None or safe_date > latest:
                latest = safe_date
        return latest
