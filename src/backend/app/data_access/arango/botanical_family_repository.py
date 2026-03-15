from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species


class ArangoBotanicalFamilyRepository(BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.BOTANICAL_FAMILIES)

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        docs, total = super().get_all(offset, limit)
        return [BotanicalFamily(**doc) for doc in docs], total

    def get_by_key(self, key: str) -> BotanicalFamily | None:
        doc = super().get_by_key(key)
        return BotanicalFamily(**doc) if doc else None

    def get_by_name(self, name: str) -> BotanicalFamily | None:
        docs = self.find_by_field("name", name)
        return BotanicalFamily(**docs[0]) if docs else None

    def create_family(self, family: BotanicalFamily) -> BotanicalFamily:
        doc = super().create(family)
        return BotanicalFamily(**doc)

    def update_family(self, key: str, family: BotanicalFamily) -> BotanicalFamily:
        doc = super().update(key, family)
        return BotanicalFamily(**doc)

    def delete_family(self, key: str) -> bool:
        return super().delete(key)

    def get_species_by_family(self, family_key: str) -> list[Species]:
        query = """
        FOR v IN 1..1 INBOUND @family_id GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: ['belongs_to_family']}
          SORT v.scientific_name ASC
          RETURN v
        """
        bind_vars = {"family_id": f"{col.BOTANICAL_FAMILIES}/{family_key}"}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_species_count_by_family(self, family_key: str) -> int:
        query = """
        RETURN LENGTH(
          FOR v IN 1..1 INBOUND @family_id GRAPH 'kamerplanter_graph'
            OPTIONS {edgeCollections: ['belongs_to_family']}
            RETURN 1
        )
        """
        bind_vars = {"family_id": f"{col.BOTANICAL_FAMILIES}/{family_key}"}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)
