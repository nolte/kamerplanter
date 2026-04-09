from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)


class PhaseSequenceService:
    """Service for managing phase definitions, sequences, and entries."""

    def __init__(self, repo: IPhaseSequenceRepository) -> None:
        self._repo = repo

    # ── PhaseDefinition CRUD ──

    def list_definitions(
        self,
        offset: int = 0,
        limit: int = 50,
        name_filter: str | None = None,
    ) -> tuple[list[PhaseDefinition], int]:
        return self._repo.get_all_definitions(offset, limit, name_filter)

    def get_definition(self, key: str) -> PhaseDefinition:
        defn = self._repo.get_definition_by_key(key)
        if not defn:
            raise NotFoundError("PhaseDefinition", key)
        return defn

    def create_definition(self, defn: PhaseDefinition) -> PhaseDefinition:
        return self._repo.create_definition(defn)

    def update_definition(self, key: str, data: dict) -> PhaseDefinition:
        defn = self.get_definition(key)
        for field, value in data.items():
            setattr(defn, field, value)
        return self._repo.update_definition(key, defn)

    def get_sequences_for_definition(self, key: str) -> list:
        self.get_definition(key)
        return self._repo.get_sequences_for_definition(key)

    def delete_definition(self, key: str) -> bool:
        defn = self.get_definition(key)
        if defn.is_system:
            raise ValidationError("Cannot delete system phase definitions.")
        usage_count = self._repo.get_definition_usage_count(key)
        if usage_count > 0:
            raise ValidationError(
                f"Cannot delete phase definition '{defn.name}': still referenced by {usage_count} sequence entries.",
            )
        return self._repo.delete_definition(key)

    # ── PhaseSequence CRUD ──

    def get_sequence_by_species(self, species_key: str) -> PhaseSequence | None:
        return self._repo.get_sequence_by_species(species_key)

    def list_sequences(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PhaseSequence], int]:
        return self._repo.get_all_sequences(offset, limit)

    def get_sequence(self, key: str) -> PhaseSequence:
        seq = self._repo.get_sequence_by_key(key)
        if not seq:
            raise NotFoundError("PhaseSequence", key)
        return seq

    def get_full_sequence(self, key: str) -> dict:
        """Return sequence data with entries and resolved phase definitions."""
        seq = self.get_sequence(key)
        entries = self._repo.get_entries_for_sequence(key)

        enriched_entries = []
        for entry in entries:
            entry_dict = entry.model_dump()
            defn = self._repo.get_definition_by_key(entry.phase_definition_key)
            if defn:
                entry_dict["phase_definition"] = defn.model_dump()
                entry_dict["effective_duration_days"] = (
                    entry.override_duration_days
                    if entry.override_duration_days is not None
                    else defn.typical_duration_days
                )
            else:
                entry_dict["phase_definition"] = None
                entry_dict["effective_duration_days"] = entry.override_duration_days or 1
            enriched_entries.append(entry_dict)

        return {
            **seq.model_dump(),
            "entries": enriched_entries,
        }

    def create_sequence(self, seq: PhaseSequence) -> PhaseSequence:
        return self._repo.create_sequence(seq)

    def update_sequence(self, key: str, data: dict) -> PhaseSequence:
        seq = self.get_sequence(key)
        for field, value in data.items():
            setattr(seq, field, value)
        return self._repo.update_sequence(key, seq)

    def delete_sequence(self, key: str) -> bool:
        seq = self.get_sequence(key)
        if seq.is_system:
            raise ValidationError("Cannot delete system phase sequences.")
        usage_count = self._repo.get_sequence_usage_count(key)
        if usage_count > 0:
            raise ValidationError(
                f"Cannot delete phase sequence '{seq.name}': "
                f"still referenced by {usage_count} workflows or lifecycle configs.",
            )
        return self._repo.delete_sequence(key)

    # ── PhaseSequenceEntry CRUD ──

    def get_entries(self, seq_key: str) -> list[PhaseSequenceEntry]:
        self.get_sequence(seq_key)  # ensure sequence exists
        return self._repo.get_entries_for_sequence(seq_key)

    def get_entry(self, key: str) -> PhaseSequenceEntry:
        entry = self._repo.get_entry_by_key(key)
        if not entry:
            raise NotFoundError("PhaseSequenceEntry", key)
        return entry

    def create_entry(self, entry: PhaseSequenceEntry) -> PhaseSequenceEntry:
        # Validate references exist
        self.get_sequence(entry.phase_sequence_key)
        self.get_definition(entry.phase_definition_key)
        return self._repo.create_entry(entry)

    def update_entry(self, key: str, data: dict) -> PhaseSequenceEntry:
        entry = self.get_entry(key)
        # Validate new references if provided
        if "phase_definition_key" in data:
            self.get_definition(data["phase_definition_key"])
        for field, value in data.items():
            setattr(entry, field, value)
        return self._repo.update_entry(key, entry)

    def delete_entry(self, key: str) -> bool:
        self.get_entry(key)  # ensure exists
        return self._repo.delete_entry(key)

    def reorder_entries(
        self,
        seq_key: str,
        orders: list[dict],
    ) -> list[PhaseSequenceEntry]:
        self.get_sequence(seq_key)  # ensure sequence exists
        return self._repo.reorder_entries(seq_key, orders)
