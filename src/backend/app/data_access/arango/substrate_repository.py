from arango.database import StandardDatabase

from app.common.types import BatchKey, SubstrateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import Substrate, SubstrateBatch


class ArangoSubstrateRepository(ISubstrateRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SUBSTRATES)

    # ── Substrate CRUD ────────────────────────────────────────────────

    def get_all_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [Substrate(**doc) for doc in docs], total

    def get_substrate_by_key(self, key: SubstrateKey) -> Substrate | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Substrate(**doc) if doc else None

    def create_substrate(self, substrate: Substrate) -> Substrate:
        doc = BaseArangoRepository.create(self, substrate)
        return Substrate(**doc)

    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate:
        doc = BaseArangoRepository.update(self, key, substrate)
        return Substrate(**doc)

    def delete_substrate(self, key: SubstrateKey) -> bool:
        return BaseArangoRepository.delete(self, key)

    # ── Substrate Batch CRUD ──────────────────────────────────────────

    def get_batch_by_key(self, key: BatchKey) -> SubstrateBatch | None:
        repo = BaseArangoRepository(self._db, col.SUBSTRATE_BATCHES)
        doc = repo.get_by_key(key)
        return SubstrateBatch(**doc) if doc else None

    def get_batches_by_substrate(self, substrate_key: SubstrateKey) -> list[SubstrateBatch]:
        repo = BaseArangoRepository(self._db, col.SUBSTRATE_BATCHES)
        docs = repo.find_by_field("substrate_key", substrate_key)
        return [SubstrateBatch(**doc) for doc in docs]

    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch:
        repo = BaseArangoRepository(self._db, col.SUBSTRATE_BATCHES)
        doc = repo.create(batch)
        if batch.substrate_key:
            substrate_id = f"{col.SUBSTRATES}/{batch.substrate_key}"
            batch_id = f"{col.SUBSTRATE_BATCHES}/{doc['_key']}"
            self.create_edge(col.FILLED_WITH, substrate_id, batch_id, data={
                "batch_id": batch.batch_id,
            })
        return SubstrateBatch(**doc)

    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch:
        repo = BaseArangoRepository(self._db, col.SUBSTRATE_BATCHES)
        doc = repo.update(key, batch)
        return SubstrateBatch(**doc)
