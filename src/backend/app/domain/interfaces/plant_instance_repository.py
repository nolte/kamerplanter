from abc import ABC, abstractmethod
from typing import Any

from app.common.types import PlantID, SlotKey, SpeciesKey
from app.domain.models.plant_instance import PlantInstance


class IPlantInstanceRepository(ABC):
    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[PlantInstance], int]: ...

    @abstractmethod
    def get_by_key(self, key: PlantID) -> PlantInstance | None: ...

    @abstractmethod
    def get_or_raise(self, key: PlantID) -> PlantInstance: ...

    @abstractmethod
    def get_by_instance_id(self, instance_id: str, tenant_key: str = "") -> PlantInstance | None: ...

    @abstractmethod
    def create(self, plant: PlantInstance) -> PlantInstance: ...

    @abstractmethod
    def update(self, key: PlantID, plant: PlantInstance) -> PlantInstance: ...

    @abstractmethod
    def delete(self, key: PlantID) -> bool: ...

    @abstractmethod
    def get_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]: ...

    @abstractmethod
    def get_active_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]: ...

    @abstractmethod
    def get_history_by_slot(self, slot_key: SlotKey, years: int = 3) -> list[PlantInstance]: ...

    @abstractmethod
    def get_by_species(self, species_key: SpeciesKey) -> list[PlantInstance]: ...

    @abstractmethod
    def create_descended_from_edge(self, child_key: PlantID, mother_key: PlantID) -> None:
        """Create the REQ-017 lineage edge child (descendant) → mother (ancestor)."""
        ...

    @abstractmethod
    def has_descendants(self, mother_key: PlantID) -> bool:
        """Whether any instance descends from ``mother_key`` (inbound descended_from edge).

        Backs the D10 idempotency guard: a monocarpic mother that already has a
        clonal pup must not spawn a second one on re-evaluation.
        """
        ...

    @abstractmethod
    def resolve_phase_name(self, phase_key: str) -> str:
        """Resolve a GrowthPhase key to its name. Returns empty string if not found."""
        ...

    @abstractmethod
    def list_active_in_phase_definition(self, tenant_key: str, phase_definition_key: str) -> list[dict[str, Any]]:
        """List the tenant's active instances currently in a phase definition (FIX-01 R1/R8).

        Returns enriched dicts (key, instance_id, plant_name, denormalised species /
        location / slot labels, current_phase_key, current_phase_started_at). MUST be
        tenant-scoped (SEC-001): only ``removed_on == null`` instances of ``tenant_key``,
        and no cross-tenant document may be read. Resolving ``current_phase_key`` to the
        definition follows the PhaseSequenceEntry path plus a best-effort legacy
        GrowthPhase name match (A1).
        """
        ...

    @abstractmethod
    def get_survival_stats(self, tenant_key: str) -> dict[str, Any]:
        """Aggregate the tenant's plant instances for survival analytics (REQ-003 G1).

        Returns a raw aggregation dict with ``total``, ``terminated``, ``died``
        counts and ``by_type`` / ``by_cause`` / ``by_phase`` breakdown lists of
        ``{"value": ..., "count": int}``. Phase names are resolved by the service
        layer. MUST be tenant-scoped — no cross-tenant document may be counted.
        """
        ...
