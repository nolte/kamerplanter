from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.enrichment import ExternalCultivarData, ExternalSpeciesData


class ExternalSourceAdapter(ABC):
    source_key: str
    rate_limit_per_minute: int = 60

    @abstractmethod
    def search_species(self, query: str) -> list[ExternalSpeciesData]:
        ...

    @abstractmethod
    def get_species_by_id(self, external_id: str) -> ExternalSpeciesData | None:
        ...

    @abstractmethod
    def get_species_list(self, page: int = 1, per_page: int = 30) -> tuple[list[ExternalSpeciesData], int]:
        ...

    def enrich_species(self, scientific_name: str, full_sync: bool = False) -> ExternalSpeciesData | None:
        results = self.search_species(scientific_name)
        return results[0] if results else None

    def get_cultivars(self, species_external_id: str) -> list[ExternalCultivarData]:
        return []

    def health_check(self) -> bool:
        return True
