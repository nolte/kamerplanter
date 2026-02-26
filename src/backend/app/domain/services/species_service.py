from app.common.exceptions import DuplicateError, NotFoundError
from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species


class SpeciesService:
    def __init__(self, species_repo: ISpeciesRepository, graph_repo: IGraphRepository) -> None:
        self._repo = species_repo
        self._graph = graph_repo

    def list_species(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]:
        return self._repo.get_all(offset, limit)

    def get_species(self, key: SpeciesKey) -> Species:
        species = self._repo.get_by_key(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    def create_species(self, species: Species) -> Species:
        existing = self._repo.get_by_scientific_name(species.scientific_name)
        if existing is not None:
            raise DuplicateError("Species", "scientific_name", species.scientific_name)
        return self._repo.create(species)

    def update_species(self, key: SpeciesKey, species: Species) -> Species:
        self.get_species(key)
        return self._repo.update(key, species)

    def delete_species(self, key: SpeciesKey) -> bool:
        self.get_species(key)
        return self._repo.delete(key)

    def search_species(self, name: str | None = None, family_key: FamilyKey | None = None) -> list[Species]:
        return self._repo.search(name=name, family_key=family_key)

    def list_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        self.get_species(species_key)
        return self._repo.get_cultivars(species_key)

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.get_species(cultivar.species_key)
        return self._repo.create_cultivar(cultivar)

    def get_cultivar(self, key: CultivarKey) -> Cultivar:
        cultivar = self._repo.get_cultivar_by_key(key)
        if cultivar is None:
            raise NotFoundError("Cultivar", key)
        return cultivar

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        self.get_cultivar(key)
        return self._repo.update_cultivar(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        self.get_cultivar(key)
        return self._repo.delete_cultivar(key)

    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        from app.data_access.arango.collections import SPECIES

        vertex_id = f"{SPECIES}/{species_key}"
        return self._graph.get_compatible_species(vertex_id)

    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        from app.data_access.arango.collections import SPECIES

        vertex_id = f"{SPECIES}/{species_key}"
        return self._graph.get_incompatible_species(vertex_id)
