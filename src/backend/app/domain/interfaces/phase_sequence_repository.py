from abc import ABC, abstractmethod

from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)


class IPhaseSequenceRepository(ABC):
    """Abstract repository for phase sequence management."""

    # ── PhaseDefinition CRUD ──

    @abstractmethod
    def get_all_definitions(
        self,
        offset: int,
        limit: int,
        name_filter: str | None = None,
    ) -> tuple[list[PhaseDefinition], int]: ...

    @abstractmethod
    def get_definition_by_key(self, key: str) -> PhaseDefinition | None: ...

    @abstractmethod
    def get_definition_by_name(self, name: str) -> PhaseDefinition | None: ...

    @abstractmethod
    def create_definition(self, defn: PhaseDefinition) -> PhaseDefinition: ...

    @abstractmethod
    def update_definition(self, key: str, defn: PhaseDefinition) -> PhaseDefinition: ...

    @abstractmethod
    def delete_definition(self, key: str) -> bool: ...

    @abstractmethod
    def get_definition_usage_count(self, key: str) -> int: ...

    @abstractmethod
    def get_sequences_for_definition(self, key: str) -> list[PhaseSequence]: ...

    # ── PhaseSequence CRUD ──

    @abstractmethod
    def get_sequence_by_species(self, species_key: str) -> PhaseSequence | None: ...

    @abstractmethod
    def get_species_for_sequence(self, seq_key: str) -> list[dict]: ...

    @abstractmethod
    def get_all_sequences(
        self,
        offset: int,
        limit: int,
    ) -> tuple[list[PhaseSequence], int]: ...

    @abstractmethod
    def get_sequence_by_key(self, key: str) -> PhaseSequence | None: ...

    @abstractmethod
    def create_sequence(self, seq: PhaseSequence) -> PhaseSequence: ...

    @abstractmethod
    def update_sequence(self, key: str, seq: PhaseSequence) -> PhaseSequence: ...

    @abstractmethod
    def delete_sequence(self, key: str) -> bool: ...

    @abstractmethod
    def get_sequence_usage_count(self, key: str) -> int: ...

    # ── PhaseSequenceEntry CRUD ──

    @abstractmethod
    def get_entries_for_sequence(self, seq_key: str) -> list[PhaseSequenceEntry]: ...

    @abstractmethod
    def get_entry_by_key(self, key: str) -> PhaseSequenceEntry | None: ...

    @abstractmethod
    def create_entry(self, entry: PhaseSequenceEntry) -> PhaseSequenceEntry: ...

    @abstractmethod
    def update_entry(self, key: str, entry: PhaseSequenceEntry) -> PhaseSequenceEntry: ...

    @abstractmethod
    def delete_entry(self, key: str) -> bool: ...

    @abstractmethod
    def reorder_entries(
        self,
        seq_key: str,
        orders: list[dict],
    ) -> list[PhaseSequenceEntry]: ...
