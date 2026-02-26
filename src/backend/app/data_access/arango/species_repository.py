from typing import Any

from arango.database import StandardDatabase

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import AQLBuilder
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species


class ArangoSpeciesRepository(ISpeciesRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SPECIES)
        self._cultivar_col = db.collection(col.CULTIVARS)

    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [Species(**doc) for doc in docs], total

    def get_by_key(self, key: SpeciesKey) -> Species | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Species(**doc) if doc else None

    def get_by_scientific_name(self, name: str) -> Species | None:
        docs = self.find_by_field("scientific_name", name)
        return Species(**docs[0]) if docs else None

    def create(self, species: Species) -> Species:
        doc = BaseArangoRepository.create(self, species)
        return Species(**doc)

    def update(self, key: SpeciesKey, species: Species) -> Species:
        doc = BaseArangoRepository.update(self, key, species)
        return Species(**doc)

    def delete(self, key: SpeciesKey) -> bool:
        return BaseArangoRepository.delete(self, key)

    def search(self, name: str | None = None, family_key: FamilyKey | None = None) -> list[Species]:
        builder = AQLBuilder(col.SPECIES)
        if name:
            builder.filter("scientific_name", "LIKE", f"%{name}%")
        query, bind_vars = builder.build_list()
        # If family_key filter needed, use graph traversal
        if family_key and not name:
            query = """
            FOR v, e IN 1..1 OUTBOUND @family_id GRAPH 'kamerplanter_graph'
              OPTIONS {edgeCollections: ['belongs_to_family']}
              RETURN v
            """
            bind_vars = {"family_id": f"{col.BOTANICAL_FAMILIES}/{family_key}"}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        docs = BaseArangoRepository(self._db, col.CULTIVARS).find_by_field("species_key", species_key)
        return [Cultivar(**doc) for doc in docs]

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        repo = BaseArangoRepository(self._db, col.CULTIVARS)
        doc = repo.create(cultivar)
        species_id = f"{col.SPECIES}/{cultivar.species_key}"
        cultivar_id = f"{col.CULTIVARS}/{doc['_key']}"
        self.create_edge(col.HAS_CULTIVAR, species_id, cultivar_id)
        return Cultivar(**doc)

    def get_cultivar_by_key(self, key: CultivarKey) -> Cultivar | None:
        doc = BaseArangoRepository(self._db, col.CULTIVARS).get_by_key(key)
        return Cultivar(**doc) if doc else None

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        repo = BaseArangoRepository(self._db, col.CULTIVARS)
        doc = repo.update(key, cultivar)
        return Cultivar(**doc)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        return BaseArangoRepository(self._db, col.CULTIVARS).delete(key)

    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None:
        self.collection.update({"_key": key, field: value, "updated_at": self._now()})
