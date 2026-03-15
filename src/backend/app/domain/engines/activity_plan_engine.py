from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.models.task import TaskTemplate, WorkflowTemplate

if TYPE_CHECKING:
    from app.domain.models.activity import Activity
    from app.domain.models.lifecycle import GrowthPhase
    from app.domain.models.species import Species


# Stress ranking for gate checks
_STRESS_RANK: dict[str, int] = {"none": 0, "low": 1, "medium": 2, "high": 3}
_TOLERANCE_RANK: dict[str, int] = {"low": 1, "medium": 2, "high": 3}

# Skill hierarchy for filtering
_SKILL_RANK: dict[str, int] = {"beginner": 0, "intermediate": 1, "advanced": 2}

# Category priority for ordering within a phase (lower = earlier)
_CATEGORY_PRIORITY: dict[str, int] = {
    "transplant": 0,
    "training_hst": 1,
    "training_lst": 2,
    "pruning": 3,
    "ausgeizen": 4,
    "propagation": 5,
    "inspection": 6,
    "general": 7,
    "harvest_prep": 8,
}

# Default day offsets by category
_CATEGORY_DEFAULT_OFFSETS: dict[str, int] = {
    "transplant": 0,
    "training_hst": 3,
    "training_lst": 3,
    "pruning": 5,
    "ausgeizen": 5,
    "propagation": 7,
    "inspection": 1,
    "general": 1,
    "harvest_prep": -2,  # negative = from end of phase
}

# Categories that share recovery slots (no two HST on same day)
_HST_CATEGORIES = {"training_hst"}

# Map ActivityCategory values to TaskCategory values
_ACTIVITY_TO_TASK_CATEGORY: dict[str, str] = {
    "training_hst": "training",
    "training_lst": "training",
    "pruning": "pruning",
    "ausgeizen": "ausgeizen",
    "transplant": "transplant",
    "harvest_prep": "harvest",
    "propagation": "maintenance",
    "inspection": "observation",
    "general": "maintenance",
}


class ActivityPlanEngine:
    def generate_plan(
        self,
        species_name: str,
        phases: list[GrowthPhase],
        activities: list[Activity],
        growth_system: str | None = None,
        skill_level: str | None = None,
        species: Species | None = None,
        family_name: str = "",
    ) -> tuple[WorkflowTemplate, list[TaskTemplate]]:
        if not phases or not activities:
            wt = WorkflowTemplate(
                name=species_name,
                growth_system=growth_system,
                skill_level_filter=skill_level,
                auto_generated=True,
            )
            return wt, []

        sorted_phases = sorted(phases, key=lambda p: p.sequence_order)
        skill_max = _SKILL_RANK.get(skill_level or "intermediate", 1)

        all_templates: list[TaskTemplate] = []
        sequence_counter = 0

        for phase in sorted_phases:
            eligible = self._filter_activities(
                activities, phase, species_name, skill_max,
                species=species, family_name=family_name,
            )
            templates = self._schedule_activities(eligible, phase, species_name)

            # Assign sequence_order across all phases
            for tt in templates:
                tt.sequence_order = sequence_counter
                sequence_counter += 1

            all_templates.extend(templates)

        total_days = sum(p.typical_duration_days for p in sorted_phases)

        wt = WorkflowTemplate(
            name=species_name,
            growth_system=growth_system,
            skill_level_filter=skill_level,
            auto_generated=True,
            total_duration_days=total_days,
        )

        return wt, all_templates

    def _filter_activities(
        self,
        activities: list[Activity],
        phase: GrowthPhase,
        species_name: str,
        skill_max: int,
        *,
        species: Species | None = None,
        family_name: str = "",
    ) -> list[Activity]:
        result: list[Activity] = []
        tolerance_rank = _TOLERANCE_RANK.get(phase.stress_tolerance.value, 2)

        # Precompute species traits for matching
        growth_habit = species.growth_habit.value if species else ""
        support_required = species.support_required if species else False
        container_suitable = (
            species.container_suitable is not None
            and species.container_suitable.value != "unsuitable"
        ) if species else True

        # Build name match set: scientific name, common names, genus
        name_tokens: set[str] = set()
        if species:
            name_tokens.add(species.scientific_name.lower())
            name_tokens.update(n.lower() for n in species.common_names)
            if species.genus:
                name_tokens.add(species.genus.lower())
        else:
            name_tokens.add(species_name.lower())

        for act in activities:
            # Forbidden phases check
            if phase.name in act.forbidden_phases:
                continue

            # Restricted sub-phases check (treat same as forbidden)
            if phase.name in act.restricted_sub_phases:
                continue

            # Species compatibility: explicit species list (case-insensitive, partial match)
            if act.species_compatible:
                matched = False
                for compat in act.species_compatible:
                    compat_lower = compat.lower()
                    if any(compat_lower in tok or tok in compat_lower for tok in name_tokens):
                        matched = True
                        break
                if not matched:
                    continue
            else:
                # Generic activity — apply structural filters

                # Growth habit filter
                if act.applicable_growth_habits and growth_habit and growth_habit not in act.applicable_growth_habits:
                    continue

                # Family filter
                if act.applicable_families and family_name:
                    family_lower = family_name.lower()
                    if not any(f.lower() in family_lower or family_lower in f.lower() for f in act.applicable_families):
                        continue

                # Support requirement filter
                if act.requires_support is True and not support_required:
                    continue

                # Container requirement filter
                if act.requires_container is True and not container_suitable:
                    continue

            # Skill gate
            act_skill = _SKILL_RANK.get(act.skill_level.value, 0)
            if act_skill > skill_max:
                continue

            # Stress gate: activity stress must not exceed phase tolerance
            act_stress = _STRESS_RANK.get(act.stress_level.value, 0)
            if act_stress > tolerance_rank:
                continue

            result.append(act)

        return result

    def _schedule_activities(
        self,
        activities: list[Activity],
        phase: GrowthPhase,
        species_name: str,
    ) -> list[TaskTemplate]:
        # Sort by sort_order, then category priority
        sorted_acts = sorted(
            activities,
            key=lambda a: (a.sort_order, _CATEGORY_PRIORITY.get(a.category.value, 6)),
        )

        templates: list[TaskTemplate] = []
        # Recovery calendar: tracks next available day per stress group
        recovery_calendar: dict[str, int] = {}
        duration = phase.typical_duration_days

        for act in sorted_acts:
            category = act.category.value

            # Determine base offset
            default_offset = _CATEGORY_DEFAULT_OFFSETS.get(category, 1)
            base_day = max(0, duration + default_offset) if default_offset < 0 else default_offset

            # Recovery group key: HST activities share one slot
            recovery_group = "hst" if category in _HST_CATEGORIES else f"cat_{category}"

            # Check recovery calendar
            earliest = recovery_calendar.get(recovery_group, 0)
            day_offset = max(base_day, earliest)

            # Resolve species-specific recovery days
            recovery = act.recovery_days_by_species.get(
                species_name, act.recovery_days_default,
            )

            # Update recovery calendar
            recovery_calendar[recovery_group] = day_offset + recovery + 1

            # Check if activity overflows phase
            is_optional = day_offset >= duration

            # Build rationale (EN + DE)
            rationale, rationale_de = self._build_rationale(act, category, day_offset, recovery, phase)

            templates.append(TaskTemplate(
                name=act.name,
                name_de=act.name_de,
                instruction=act.description or rationale,
                instruction_de=act.description_de or rationale_de,
                description=act.description,
                description_de=act.description_de,
                category=_ACTIVITY_TO_TASK_CATEGORY.get(category, "maintenance"),
                trigger_type="phase_entry",
                trigger_phase=phase.name,
                days_offset=day_offset,
                stress_level=act.stress_level,
                skill_level=act.skill_level,
                estimated_duration_minutes=act.estimated_duration_minutes,
                tools_required=list(act.tools_required),
                activity_key=act.key or "",
                rationale=rationale,
                rationale_de=rationale_de,
                recovery_days=recovery,
                is_optional=is_optional,
                enabled=not is_optional,
                phase_display_name=phase.display_name or phase.name,
                phase_duration_days=phase.typical_duration_days,
                phase_stress_tolerance=phase.stress_tolerance.value,
            ))

        return templates

    def _build_rationale(
        self,
        activity: Activity,
        category: str,
        day_offset: int,
        recovery: int,
        phase: GrowthPhase,
    ) -> tuple[str, str]:
        """Build human-readable rationale in EN and DE."""
        name_en = activity.name
        name_de = activity.name_de or activity.name
        phase_en = phase.name
        phase_de = phase.display_name or phase.name

        en_parts: list[str] = []
        de_parts: list[str] = []

        if category == "transplant":
            en_parts.append(f"{name_en} on day {day_offset} of {phase_en} phase")
            de_parts.append(f"{name_de} an Tag {day_offset} der {phase_de}-Phase")
        elif category in ("training_hst", "training_lst"):
            en_parts.append(f"{name_en} on day {day_offset} of {phase_en} phase")
            de_parts.append(f"{name_de} an Tag {day_offset} der {phase_de}-Phase")
            if recovery > 0:
                en_parts.append(f"Allow {recovery} days recovery before next stress activity")
                de_parts.append(f"{recovery} Tage Erholung vor der nächsten Stressmaßnahme einplanen")
        elif category == "harvest_prep":
            en_parts.append(f"{name_en} on day {day_offset} — towards end of {phase_en} phase")
            de_parts.append(f"{name_de} an Tag {day_offset} — gegen Ende der {phase_de}-Phase")
        elif category == "inspection":
            en_parts.append(f"{name_en} from day {day_offset} of {phase_en} phase — repeat regularly")
            de_parts.append(f"{name_de} ab Tag {day_offset} der {phase_de}-Phase — regelmäßig wiederholen")
        else:
            en_parts.append(f"{name_en} on day {day_offset} of {phase_en} phase")
            de_parts.append(f"{name_de} an Tag {day_offset} der {phase_de}-Phase")

        if day_offset >= phase.typical_duration_days:
            en_parts.append("Optional — phase may be too short for this activity")
            de_parts.append("Optional — Phase ist möglicherweise zu kurz für diese Maßnahme")

        if activity.tools_required:
            tools = ", ".join(activity.tools_required)
            en_parts.append(f"Tools needed: {tools}")
            de_parts.append(f"Benötigte Werkzeuge: {tools}")

        return ". ".join(en_parts), ". ".join(de_parts)
