from app.domain.calculators.photoperiod_calculator import calculate_dli, calculate_transition_schedule


class PhotoperiodManager:
    """Manages photoperiod transitions and DLI tracking."""

    def plan_transition(
        self,
        current_hours: float,
        target_hours: float,
        transition_days: int = 7,
        ppfd: int = 400,
        lights_on_time: str = "06:00",
    ) -> dict:
        """Plan a photoperiod transition with DLI calculations."""
        schedule = calculate_transition_schedule(current_hours, target_hours, transition_days, lights_on_time)

        for entry in schedule:
            entry["dli"] = round(calculate_dli(ppfd, entry["photoperiod_hours"]), 2)

        return {
            "current_photoperiod": current_hours,
            "target_photoperiod": target_hours,
            "transition_days": transition_days,
            "ppfd": ppfd,
            "schedule": schedule,
        }
