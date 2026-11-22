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


@dataclass(frozen=True)
class SlotAdjacency:
    """One undirected ``adjacent_to`` pair; ``slot_a_key < slot_b_key`` (REQ-053 GP-FR-134)."""

    slot_a_key: str
    slot_b_key: str
    distance_cm: float | None = None


@dataclass(frozen=True)
class SlotAdjacencyWindow:
    """A bounded window of a bed's undirected ``adjacent_to`` pairs and the exact number of all of them."""

    #: At most ``limit`` pairs, sorted by ``(slot_a_key, slot_b_key)``.
    pairs: list[SlotAdjacency]
    #: Every distinct pair among the slots, counted in the database (not bounded by ``limit``).
    total: int


@dataclass(frozen=True)
class CompanionRelation:
    """One directed companion edge between two species (``compatible_with`` or ``incompatible_with``)."""

    from_key: str
    to_key: str
    incompatible: bool
    score: float | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CompanionRelations:
    """The companion edges among a set of species and the names of those the tenant may read, in one read."""

    relations: list[CompanionRelation]
    #: species key -> scientific name, only for species the tenant may read (own, global or granted).
    names: dict[str, str]
    #: ``False`` when an edge collection had more edges among the species than the read's ``limit``.
    complete: bool = True


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
    def load_companion_relations(self, species_keys: list[str], *, tenant_key: str, limit: int) -> CompanionRelations:
        """The companion edges whose two ends are among *species_keys* and readable by the tenant, in one read.

        Both edge collections, both directions as stored, at most *limit* edges per collection (``complete`` says
        whether that cut anything). A species the tenant may not read (another tenant's private one, MT-054 /
        #927) contributes neither an edge nor a name.
        """

    @abstractmethod
    def get_adjacent_slots(self, slot_key: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_slot_adjacency(
        self, location_key: str, slot_keys: list[str], *, tenant_key: str, limit: int
    ) -> SlotAdjacencyWindow:
        """The undirected ``adjacent_to`` pairs whose two ends are slots of the bed among *slot_keys*, in one read.

        Anchored on the bed: nothing when its site is not the tenant's (a slot has no ``tenant_key``, #706). Each
        pair once (the edges are stored in both directions), sorted by ``(slot_a_key, slot_b_key)`` and cut to
        *limit* in the database; ``total`` counts all pairs.
        """

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
