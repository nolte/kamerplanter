from datetime import datetime, timedelta

# Base inspection interval in days
BASE_INTERVAL_DAYS = 7

# Phase multipliers (lower = more frequent)
PHASE_MULTIPLIERS = {
    "germination": 1.0,
    "seedling": 0.8,
    "vegetative": 1.0,
    "flowering": 0.5,
    "harvest": 0.33,
}

# Pressure multipliers (lower = more frequent)
PRESSURE_MULTIPLIERS = {
    "none": 1.0,
    "low": 0.8,
    "medium": 0.5,
    "high": 0.33,
    "critical": 0.25,
}


class InspectionScheduler:
    """Pure logic for inspection scheduling -- no DB access."""

    def next_inspection_date(
        self,
        last_inspection_at: datetime | None,
        current_phase: str,
        pressure_level: str,
    ) -> datetime:
        """Calculate the next recommended inspection date.

        Args:
            last_inspection_at: When the last inspection was performed.
                If None, inspection is due immediately.
            current_phase: Current growth phase name.
            pressure_level: Current pest pressure level.

        Returns:
            The recommended next inspection datetime.
        """
        if last_inspection_at is None:
            return datetime.now()

        phase_mult = PHASE_MULTIPLIERS.get(current_phase, 1.0)
        pressure_mult = PRESSURE_MULTIPLIERS.get(pressure_level, 1.0)

        interval_days = max(1, BASE_INTERVAL_DAYS * phase_mult * pressure_mult)
        return last_inspection_at + timedelta(days=interval_days)

    def calculate_urgency(
        self,
        next_due: datetime,
        now: datetime | None = None,
    ) -> dict:
        """Calculate inspection urgency.

        Returns:
            Dict with is_overdue, days_until_due (negative if overdue),
            and urgency_level.
        """
        if now is None:
            now = datetime.now()

        delta = (next_due - now).total_seconds() / 86400
        days_until = round(delta, 1)

        if days_until < 0:
            urgency = "overdue"
        elif days_until < 1:
            urgency = "due_today"
        elif days_until < 3:
            urgency = "due_soon"
        else:
            urgency = "scheduled"

        return {
            "is_overdue": days_until < 0,
            "days_until_due": days_until,
            "urgency_level": urgency,
        }
