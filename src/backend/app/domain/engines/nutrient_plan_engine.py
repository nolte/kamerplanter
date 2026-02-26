from app.common.enums import PhaseName
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry

ALL_PHASES = [p for p in PhaseName]
EC_TOLERANCE = 0.3  # mS


class NutrientPlanValidator:
    """Validates nutrient plan completeness and EC budgets."""

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

    def validate_ec_budget(
        self,
        entry: NutrientPlanPhaseEntry,
        fertilizers: dict[str, Fertilizer],
    ) -> dict:
        """Check if dosage EC matches target EC within tolerance."""
        if not entry.fertilizer_dosages:
            return {
                "valid": True,
                "target_ec": entry.target_ec_ms,
                "calculated_ec": 0.0,
                "delta": entry.target_ec_ms,
                "message": "No dosages defined — cannot verify EC",
            }

        calculated_ec = 0.0
        missing_ferts: list[str] = []

        for dosage in entry.fertilizer_dosages:
            fert = fertilizers.get(dosage.fertilizer_key)
            if fert is None:
                missing_ferts.append(dosage.fertilizer_key)
                continue
            calculated_ec += dosage.ml_per_liter * fert.ec_contribution_per_ml

        delta = abs(entry.target_ec_ms - calculated_ec)
        valid = round(delta, 10) <= EC_TOLERANCE and not missing_ferts

        messages = []
        if missing_ferts:
            messages.append(f"Missing fertilizers: {', '.join(missing_ferts)}")
        if delta > EC_TOLERANCE:
            messages.append(
                f"EC mismatch: target {entry.target_ec_ms} mS, calculated {calculated_ec:.2f} mS "
                f"(delta {delta:.2f}, tolerance {EC_TOLERANCE})"
            )

        return {
            "valid": valid,
            "target_ec": entry.target_ec_ms,
            "calculated_ec": round(calculated_ec, 2),
            "delta": round(delta, 2),
            "message": "; ".join(messages) if messages else "EC budget within tolerance",
        }
