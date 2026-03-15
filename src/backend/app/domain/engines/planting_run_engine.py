from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import InvalidStatusTransitionError
from app.domain.models.planting_run import ALLOWED_STATUS_TRANSITIONS, PlantingRunEntry


class PlantingRunEngine:
    """Pure logic for planting run operations — no DB access."""

    def validate_status_transition(
        self,
        current: PlantingRunStatus,
        target: PlantingRunStatus,
    ) -> None:
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise InvalidStatusTransitionError(current.value, target.value)

    def generate_plant_ids(
        self,
        location_key: str,
        entries: list[PlantingRunEntry],
        existing_ids: set[str],
    ) -> list[dict]:
        """Generate unique plant instance IDs for batch creation.

        Format: {LOCATION}_{PREFIX}_{SEQ:02d}
        Returns list of dicts: {entry_key, instance_id, species_key, cultivar_key}
        """
        result = []
        for entry in entries:
            seq = 1
            for _ in range(entry.quantity):
                while True:
                    instance_id = f"{location_key}_{entry.id_prefix}_{seq:02d}"
                    if instance_id not in existing_ids:
                        break
                    seq += 1
                existing_ids.add(instance_id)
                result.append(
                    {
                        "entry_key": entry.key,
                        "instance_id": instance_id,
                        "species_key": entry.species_key,
                        "cultivar_key": entry.cultivar_key,
                    }
                )
                seq += 1
        return result

    def filter_transition_eligible(
        self,
        plants: list[dict],
        target_phase: str,
        exclude_keys: set[str] | None = None,
    ) -> tuple[list[dict], list[dict]]:
        """Split plants into eligible and skipped for phase transition.

        Returns (eligible, skipped).
        """
        eligible = []
        skipped = []
        exclude = exclude_keys or set()
        for plant in plants:
            key = plant.get("_key", "")
            if key in exclude or plant.get("removed_on") is not None or plant.get("current_phase") == target_phase:
                skipped.append(plant)
            else:
                eligible.append(plant)
        return eligible, skipped

    def validate_run_type_constraints(
        self,
        run_type: PlantingRunType,
        entries: list[PlantingRunEntry],
        source_plant_key: str | None = None,
    ) -> None:
        """Validate constraints based on run type."""
        if run_type == PlantingRunType.CLONE:
            if not source_plant_key:
                raise ValueError("Clone runs require a source_plant_key.")
            if len(entries) != 1:
                raise ValueError("Clone runs must have exactly one entry.")
        elif run_type == PlantingRunType.MONOCULTURE:
            if len(entries) != 1:
                raise ValueError("Monoculture runs must have exactly one entry.")
        elif run_type == PlantingRunType.MIXED_CULTURE:
            if len(entries) < 2:
                raise ValueError("Mixed culture runs require at least two entries.")
