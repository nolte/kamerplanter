from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.common.types import SpeciesKey

#: ``adjacent_to.source`` of an edge the adjacency engine derived from geometry (GP-FR-130).
ADJACENCY_SOURCE_DERIVED = "derived"
#: ``adjacent_to.source`` of an edge a user set; the derivation never touches it.
ADJACENCY_SOURCE_MANUAL = "manual"


@dataclass(frozen=True)
class AdjacencySync:
    """What :meth:`IGraphRepository.sync_derived_adjacency` changed, in directed edges."""

    created: int = 0
    updated: int = 0
    removed: int = 0
    kept: int = 0


class IGraphRepository(ABC):
    @abstractmethod
    def get_compatible_species(self, species_key: SpeciesKey, *, tenant_key: str | None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_incompatible_species(self, species_key: SpeciesKey, *, tenant_key: str | None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_companion_counts(self, *, tenant_key: str | None) -> dict[str, dict[str, int]]: ...

    @abstractmethod
    def set_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, score: float) -> None: ...

    @abstractmethod
    def set_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, reason: str) -> None: ...

    @abstractmethod
    def remove_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool: ...

    @abstractmethod
    def remove_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool: ...

    @abstractmethod
    def get_rotation_successors(self, family_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_rotation_successor_counts(self) -> dict[str, int]: ...

    @abstractmethod
    def set_rotation_successor(
        self,
        from_family_key: str,
        to_family_key: str,
        wait_years: int,
        benefit_score: float = 0.0,
        benefit_reason: str = "",
    ) -> None: ...

    @abstractmethod
    def get_adjacent_slots(self, slot_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def set_adjacent_slots(
        self,
        slot_a_key: str,
        slot_b_key: str,
        *,
        distance_cm: float | None = None,
        source: str = ADJACENCY_SOURCE_DERIVED,
    ) -> None:
        """Set the neighbourhood of two slots in both directions, replacing an edge between them (GP-FR-130)."""

    @abstractmethod
    def sync_derived_adjacency(self, slot_keys: list[str], pairs: list[tuple[str, str, float]]) -> AdjacencySync:
        """Make the derived ``adjacent_to`` edges among *slot_keys* exactly *pairs* ``(a, b, distance_cm)``.

        Only edges with ``source = derived`` are managed: manual edges and legacy edges without a source are
        neither removed nor overwritten, and a pair that already has such an edge gets no derived one.
        Idempotent: running it twice with the same pairs changes nothing.
        """

    @abstractmethod
    def remove_manual_adjacency(self, slot_a_key: str, slot_b_key: str) -> int:
        """Delete the manual edge(s) between two slots; the number removed (derived edges stay)."""

    # ── Family-level edges ─────────────────────────────────────────────

    @abstractmethod
    def get_pest_risks(self, family_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def set_pest_risk(
        self,
        a_key: str,
        b_key: str,
        shared_pests: list[str],
        shared_diseases: list[str],
        risk_level: str,
    ) -> None: ...

    @abstractmethod
    def get_family_compatible(self, family_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def set_family_compatible(
        self,
        a_key: str,
        b_key: str,
        benefit_type: str,
        compatibility_score: float,
        notes: str,
    ) -> None: ...

    @abstractmethod
    def get_family_incompatible(self, family_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def set_family_incompatible(
        self,
        a_key: str,
        b_key: str,
        reason: str,
        severity: str,
    ) -> None: ...

    @abstractmethod
    def get_species_by_family(self, family_key: str, *, tenant_key: str | None) -> list[dict[str, Any]]: ...
