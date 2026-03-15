from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.enrichment_repository import (
    IExternalMappingRepository,
    IExternalSourceRepository,
    ISyncRunRepository,
)
from app.domain.models.enrichment import ExternalMapping, ExternalSource, SyncRun

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import ExternalMappingKey, SourceKey, SyncRunKey


class ArangoExternalSourceRepository(IExternalSourceRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.EXTERNAL_SOURCES)

    def get_all(self) -> list[ExternalSource]:
        docs, _ = BaseArangoRepository.get_all(self, offset=0, limit=100)
        return [ExternalSource(**doc) for doc in docs]

    def get_by_key(self, key: SourceKey) -> ExternalSource | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ExternalSource(**doc) if doc else None

    def get_by_source_key(self, source_key: str) -> ExternalSource | None:
        docs = self.find_by_field("source_key", source_key)
        return ExternalSource(**docs[0]) if docs else None

    def create(self, source: ExternalSource) -> ExternalSource:
        doc = BaseArangoRepository.create(self, source)
        return ExternalSource(**doc)

    def update(self, key: SourceKey, source: ExternalSource) -> ExternalSource:
        doc = BaseArangoRepository.update(self, key, source)
        return ExternalSource(**doc)


class ArangoExternalMappingRepository(IExternalMappingRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.EXTERNAL_MAPPINGS)

    def get_by_key(self, key: ExternalMappingKey) -> ExternalMapping | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ExternalMapping(**doc) if doc else None

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

    def create(self, mapping: ExternalMapping) -> ExternalMapping:
        doc = BaseArangoRepository.create(self, mapping)
        return ExternalMapping(**doc)

    def update(self, key: ExternalMappingKey, mapping: ExternalMapping) -> ExternalMapping:
        doc = BaseArangoRepository.update(self, key, mapping)
        return ExternalMapping(**doc)

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


class ArangoSyncRunRepository(ISyncRunRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SYNC_RUNS)

    def create(self, run: SyncRun) -> SyncRun:
        doc = BaseArangoRepository.create(self, run)
        return SyncRun(**doc)

    def update(self, key: SyncRunKey, run: SyncRun) -> SyncRun:
        doc = BaseArangoRepository.update(self, key, run)
        return SyncRun(**doc)

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
