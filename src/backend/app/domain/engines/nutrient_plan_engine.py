from app.common.enums import PhaseName
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry

ALL_PHASES = [p for p in PhaseName]


class NutrientPlanValidator:
    """Validates nutrient plan completeness."""

    def validate_completeness(self, entries: list[NutrientPlanPhaseEntry]) -> dict:
        """Check if all growth phases are covered and weeks are contiguous."""
        issues: list[str] = []

        # Check for missing phases
        covered_phases = {e.phase_name for e in entries}
        for phase in ALL_PHASES:
            if phase not in covered_phases:
                issues.append(f"Missing phase: {phase.value}")

        # Check for week gaps within same phase
        phases_entries: dict[PhaseName, list[NutrientPlanPhaseEntry]] = {}
        for entry in entries:
            phases_entries.setdefault(entry.phase_name, []).append(entry)

        for phase, phase_entries in phases_entries.items():
            sorted_entries = sorted(phase_entries, key=lambda e: e.week_start)
            for i in range(1, len(sorted_entries)):
                prev_end = sorted_entries[i - 1].week_end
                curr_start = sorted_entries[i].week_start
                if curr_start > prev_end + 1:
                    issues.append(
                        f"Week gap in {phase.value}: week {prev_end} to {curr_start}"
                    )
                if curr_start <= sorted_entries[i - 1].week_start:
                    issues.append(
                        f"Overlapping weeks in {phase.value}: entries at week {curr_start}"
                    )

        complete = len(issues) == 0
        return {"complete": complete, "issues": issues}
