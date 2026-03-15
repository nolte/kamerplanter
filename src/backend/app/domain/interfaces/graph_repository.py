from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.common.types import SpeciesKey


class IGraphRepository(ABC):
    @abstractmethod
    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, score: float) -> None:
        ...

    @abstractmethod
    def set_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, reason: str) -> None:
        ...

    @abstractmethod
    def remove_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        ...

    @abstractmethod
    def remove_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        ...

    @abstractmethod
    def get_rotation_successors(self, family_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_rotation_successor(
        self, from_family_key: str, to_family_key: str, wait_years: int,
        benefit_score: float = 0.0, benefit_reason: str = "",
    ) -> None:
        ...

    @abstractmethod
    def get_adjacent_slots(self, slot_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_adjacent_slots(self, slot_a_key: str, slot_b_key: str) -> None:
        ...

    # ── Family-level edges ─────────────────────────────────────────────

    @abstractmethod
    def get_pest_risks(self, family_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_pest_risk(
        self, a_key: str, b_key: str,
        shared_pests: list[str], shared_diseases: list[str], risk_level: str,
    ) -> None:
        ...

    @abstractmethod
    def get_family_compatible(self, family_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_family_compatible(
        self, a_key: str, b_key: str,
        benefit_type: str, compatibility_score: float, notes: str,
    ) -> None:
        ...

    @abstractmethod
    def get_family_incompatible(self, family_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_family_incompatible(
        self, a_key: str, b_key: str, reason: str, severity: str,
    ) -> None:
        ...

    @abstractmethod
    def get_species_by_family(self, family_key: str) -> list[dict[str, Any]]:
        ...
