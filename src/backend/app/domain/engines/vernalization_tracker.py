class VernalizationTracker:
    """Tracks vernalization (cold period) progress for biennials."""

    def calculate_vernalization_progress(
        self,
        cold_days_accumulated: int,
        required_min_days: int,
    ) -> dict[str, float | int | bool]:
        """Calculate vernalization progress.
        Returns dict with progress_percent, days_remaining, is_complete.
        """
        if required_min_days <= 0:
            return {"progress_percent": 100.0, "days_remaining": 0, "is_complete": True}

        progress = min(100.0, (cold_days_accumulated / required_min_days) * 100.0)
        remaining = max(0, required_min_days - cold_days_accumulated)

        return {
            "progress_percent": round(progress, 1),
            "days_remaining": remaining,
            "is_complete": cold_days_accumulated >= required_min_days,
        }

    def is_cold_day(self, avg_temp_c: float, threshold_c: float = 5.0) -> bool:
        """Check if a day counts as a vernalization cold day."""
        return avg_temp_c <= threshold_c
