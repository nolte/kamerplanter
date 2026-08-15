from abc import ABC, abstractmethod
from typing import Any

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.domain.models.species import Cultivar, Species


class ISpeciesRepository(ABC):
    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None
    ) -> tuple[list[Species], int]: ...

    @abstractmethod
    def get_by_key(self, key: SpeciesKey) -> Species | None: ...

    @abstractmethod
    def get_or_raise(self, key: SpeciesKey) -> Species: ...

    @abstractmethod
    def get_by_scientific_name(self, name: str) -> Species | None: ...

    @abstractmethod
    def get_by_normalized_scientific_name(self, name: str) -> Species | None: ...

    @abstractmethod
    def get_by_normalized_scientific_name_for_tenant(self, name: str, tenant_key: str) -> Species | None: ...

    @abstractmethod
    def upsert_by_normalized_scientific_name(self, species: Species) -> Species: ...

    # ── explicit masterdata grants (#1092) ──────────────────────────────────
    # Read-only sharing: a grant makes a row visible to another tenant, never
    # editable or deletable. Declared on the interface so a second implementation
    # cannot ship the read arm without the revoke path.

    @abstractmethod
    def grant_access(self, species_key: str, to_tenant_key: str) -> None: ...

    @abstractmethod
    def revoke_access(self, species_key: str, from_tenant_key: str) -> bool: ...

    @abstractmethod
    def list_grants(self, species_key: str) -> list[str]: ...

    @abstractmethod
    def is_granted_to(self, species_key: str, tenant_key: str) -> bool: ...

    @abstractmethod
    def grant_cultivar_access(self, cultivar_key: str, to_tenant_key: str) -> None: ...

    @abstractmethod
    def revoke_cultivar_access(self, cultivar_key: str, from_tenant_key: str) -> bool: ...

    @abstractmethod
    def list_cultivar_grants(self, cultivar_key: str) -> list[str]: ...

    @abstractmethod
    def is_cultivar_granted_to(self, cultivar_key: str, tenant_key: str) -> bool: ...

    @abstractmethod
    def find_synonym_match_candidates(self, species: Species) -> list[Species]: ...

    @abstractmethod
    def list_all_species(self) -> list[Species]: ...

    @abstractmethod
    def create(self, species: Species) -> Species: ...

    @abstractmethod
    def update(self, key: SpeciesKey, species: Species) -> Species: ...

    @abstractmethod
    def delete(self, key: SpeciesKey) -> bool: ...

    @abstractmethod
    def search(
        self, name: str | None = None, family_key: FamilyKey | None = None, *, tenant_key: str | None = None
    ) -> list[Species]: ...

    @abstractmethod
    def get_cultivars(self, species_key: SpeciesKey, *, tenant_key: str | None = None) -> list[Cultivar]: ...

    @abstractmethod
    def create_cultivar(self, cultivar: Cultivar) -> Cultivar: ...

    @abstractmethod
    def get_cultivar_by_key(self, key: CultivarKey) -> Cultivar | None: ...

    @abstractmethod
    def get_cultivar_or_raise(self, key: CultivarKey) -> Cultivar: ...

    @abstractmethod
    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar: ...

    @abstractmethod
    def delete_cultivar(self, key: CultivarKey) -> bool: ...

    @abstractmethod
    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None: ...
