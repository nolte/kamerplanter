from datetime import datetime, timedelta

# HST (High Stress Training) tasks forbidden in all flowering sub-phases
FORBIDDEN_ALL_FLOWER = {"topping", "fim", "mainlining", "heavy_defoliation"}

# Forbidden mid-to-late flowering (allowed in early flowering / stretch)
FORBIDDEN_MID_FLOWER = {"supercropping", "transplant"}

# Recovery time in days per species group
RECOVERY_DAYS = {
    "cannabis": 7,
    "tomato": 3,
    "pepper": 5,
    "default": 5,
}

# Flowering sub-phases where mid-flower restrictions apply
MID_LATE_FLOWER_KEYWORDS = {"mid_flower", "late_flower", "ripening"}


class HSTValidator:
    """Pure logic for High Stress Training validation -- no DB access."""

    def validate(
        self,
        task_name: str,
        current_phase: str,
        recent_hst_tasks: list[dict],
        species_name: str = "",
    ) -> dict:
        """Validate whether an HST task can be performed.

        Args:
            task_name: The training technique name (lowercase).
            current_phase: Current growth phase (e.g., 'flowering').
            recent_hst_tasks: List of dicts with keys:
                - name: str
                - completed_at: datetime | str
            species_name: Species common name for recovery lookup.

        Returns:
            Dict with can_perform (bool), reason (str), recovery_status (dict|None).
        """
        task_lower = task_name.lower().replace(" ", "_").replace("-", "_")
        phase_lower = current_phase.lower()

        # Check flowering phase restrictions
        is_flowering = "flower" in phase_lower or phase_lower == "harvest"

        if is_flowering and task_lower in FORBIDDEN_ALL_FLOWER:
            return {
                "can_perform": False,
                "reason": f"'{task_name}' is forbidden during flowering phase.",
                "recovery_status": None,
            }

        is_mid_late = any(kw in phase_lower for kw in MID_LATE_FLOWER_KEYWORDS)
        if is_mid_late and task_lower in FORBIDDEN_MID_FLOWER:
            return {
                "can_perform": False,
                "reason": f"'{task_name}' is forbidden in mid/late flowering.",
                "recovery_status": None,
            }

        # Check recovery time
        species_key = "default"
        for key in RECOVERY_DAYS:
            if key in species_name.lower():
                species_key = key
                break

        recovery_days = RECOVERY_DAYS[species_key]
        recovery_status = self._check_recovery(recent_hst_tasks, recovery_days)

        if recovery_status and not recovery_status["recovered"]:
            return {
                "can_perform": False,
                "reason": (
                    f"Plant needs {recovery_status['days_remaining']} more days "
                    f"to recover from '{recovery_status['last_task']}'."
                ),
                "recovery_status": recovery_status,
            }

        return {
            "can_perform": True,
            "reason": "",
            "recovery_status": recovery_status,
        }

    def _check_recovery(
        self,
        recent_hst_tasks: list[dict],
        recovery_days: int,
    ) -> dict | None:
        """Check if the plant has recovered from the last HST."""
        if not recent_hst_tasks:
            return None

        now = datetime.now()
        latest = None
        latest_name = ""

        for task in recent_hst_tasks:
            completed_at = task.get("completed_at")
            if completed_at is None:
                continue
            if isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at)
            if latest is None or completed_at > latest:
                latest = completed_at
                latest_name = task.get("name", "unknown")

        if latest is None:
            return None

        recovery_end = latest + timedelta(days=recovery_days)
        recovered = now >= recovery_end
        days_remaining = max(0, (recovery_end - now).days) if not recovered else 0

        return {
            "last_task": latest_name,
            "completed_at": latest.isoformat(),
            "recovery_end": recovery_end.isoformat(),
            "recovered": recovered,
            "days_remaining": days_remaining,
        }
