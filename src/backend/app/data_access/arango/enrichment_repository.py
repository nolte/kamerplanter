from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.enrichment_repository import (
    IExternalMappingRepository,
    IExternalSourceRepository,
    ISyncRunRepository,
)
from app.domain.models.enrichment import ExternalMapping, ExternalSource, SyncRun


class ArangoExternalSourceRepository(BaseArangoRepository[ExternalSource], IExternalSourceRepository):
    _model_cls = ExternalSource

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.EXTERNAL_SOURCES)

    def get_all(self) -> list[ExternalSource]:
        items, _ = super().get_all(offset=0, limit=100)
        return items

    def get_by_source_key(self, source_key: str) -> ExternalSource | None:
        return self.find_one_by_field("source_key", source_key)


class ArangoExternalMappingRepository(BaseArangoRepository[ExternalMapping], IExternalMappingRepository):
    _model_cls = ExternalMapping

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.EXTERNAL_MAPPINGS)

    def get_by_internal(self, internal_collection: str, internal_key: str, source_key: str) -> ExternalMapping | None:
        query = """
        FOR em IN external_mappings
            FILTER em.internal_collection == @col
               AND em.internal_key == @key
               AND em.source_key == @src
            LIMIT 1
            RETURN em
        """
        cursor = self._db.aql.execute(
            query, bind_vars={"col": internal_collection, "key": internal_key, "src": source_key}
        )
        doc = next(cursor, None)
        return ExternalMapping(**self._from_doc(doc)) if doc else None

    def get_all_for_internal(self, internal_collection: str, internal_key: str) -> list[ExternalMapping]:
        query = """
        FOR em IN external_mappings
            FILTER em.internal_collection == @col
               AND em.internal_key == @key
            RETURN em
        """
        cursor = self._db.aql.execute(query, bind_vars={"col": internal_collection, "key": internal_key})
        return [ExternalMapping(**self._from_doc(doc)) for doc in cursor]

    def find_unmapped_species(self, source_key: str) -> list[dict[str, str]]:
        query = """
        FOR s IN species
            LET has_mapping = LENGTH(
                FOR em IN external_mappings
                    FILTER em.internal_collection == "species"
                       AND em.internal_key == s._key
                       AND em.source_key == @source_key
                    LIMIT 1 RETURN 1
            )
            FILTER has_mapping == 0
            RETURN { _key: s._key, scientific_name: s.scientific_name }
        """
        cursor = self._db.aql.execute(query, bind_vars={"source_key": source_key})
        return [dict(doc) for doc in cursor]  # type: ignore[arg-type]


class ArangoSyncRunRepository(BaseArangoRepository[SyncRun], ISyncRunRepository):
    _model_cls = SyncRun

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SYNC_RUNS)

    def get_by_source(self, source_key: str, limit: int = 20) -> list[SyncRun]:
        query = """
        FOR sr IN sync_runs
            FILTER sr.source_key == @source_key
            SORT sr.created_at DESC
            LIMIT @limit
            RETURN sr
        """
        cursor = self._db.aql.execute(query, bind_vars={"source_key": source_key, "limit": limit})
        return [SyncRun(**self._from_doc(doc)) for doc in cursor]
