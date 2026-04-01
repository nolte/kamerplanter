from app.common.enums import PhaseName
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry

ALL_PHASES = [p for p in PhaseName]


def resolve_effective_entry(
    entries: list[NutrientPlanPhaseEntry],
    current_phase: str,
    current_week: int,
    cycle_restart_from_sequence: int | None,
) -> NutrientPlanPhaseEntry | None:
    """Find the matching phase entry, handling perennial cycle restarts.

    For plans with ``cycle_restart_from_sequence`` set, weeks beyond the
    plan's terminal week are mapped back into the recurring portion of the
    plan.  Entries with ``sequence_order < cycle_restart_from_sequence``
    are one-time entries (e.g. initial rooting); entries at or above that
    threshold repeat cyclically.
    """
    sorted_entries = sorted(entries, key=lambda e: e.sequence_order)

    # 1. Direct match (works for linear plans and first cycle of perennials)
    for entry in sorted_entries:
        if entry.phase_name.value == current_phase and entry.week_start <= current_week <= entry.week_end:
            return entry

    # Fallback without phase name constraint (week range only)
    for entry in sorted_entries:
        if entry.week_start <= current_week <= entry.week_end:
            return entry

    # 2. Cycle restart logic for perennial plans
    if cycle_restart_from_sequence is None or not sorted_entries:
        return None

    # Separate one-time vs. recurring entries
    recurring = [e for e in sorted_entries if e.sequence_order >= cycle_restart_from_sequence]
    if not recurring:
        return None

    cycle_start_week = recurring[0].week_start
    cycle_end_week = recurring[-1].week_end
    cycle_length = cycle_end_week - cycle_start_week + 1

    if cycle_length <= 0 or current_week <= cycle_end_week:
        return None

    # Map current_week into recurring range
    weeks_past_cycle = current_week - cycle_end_week
    effective_offset = (weeks_past_cycle - 1) % cycle_length
    effective_week = cycle_start_week + effective_offset

    # Match by phase name first, then by week range
    for entry in recurring:
        if entry.phase_name.value == current_phase and entry.week_start <= effective_week <= entry.week_end:
            return entry

    for entry in recurring:
        if entry.week_start <= effective_week <= entry.week_end:
            return entry

    return None


class NutrientPlanValidator:
    """Validates nutrient plan completeness."""

    def validate_completeness(self, entries: list[NutrientPlanPhaseEntry]) -> dict:
        """Check if weeks are contiguous and report unused phases as hints.

        Not all plans use every PhaseName (e.g. houseplant plans skip
        FLOWERING/HARVEST, cannabis plans skip DORMANCY).  Missing phases
        are reported as informational ``hints``, not blocking ``issues``.
        """
        issues: list[str] = []
        hints: list[str] = []

        # Report unused phases as hints (not errors)
        covered_phases = {e.phase_name for e in entries}
        for phase in ALL_PHASES:
            if phase not in covered_phases:
                hints.append(f"Phase not used: {phase.value}")

        # Check for week gaps and overlaps across all phases
        if entries:
            sorted_entries = sorted(entries, key=lambda e: e.week_start)
            for i in range(1, len(sorted_entries)):
                prev = sorted_entries[i - 1]
                curr = sorted_entries[i]
                if curr.week_start > prev.week_end:
                    issues.append(f"Week gap: week {prev.week_end} to {curr.week_start}")
                if curr.week_start < prev.week_end:
                    issues.append(
                        f"Overlapping weeks: {prev.phase_name.value} (W{prev.week_start}-{prev.week_end}) "
                        f"and {curr.phase_name.value} (W{curr.week_start}-{curr.week_end})"
                    )

        complete = len(issues) == 0
        return {"complete": complete, "issues": issues, "hints": hints}
