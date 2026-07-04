from arango.database import StandardDatabase

from app.common.types import BatchKey, SlotKey, SubstrateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import Substrate, SubstrateBatch


class ArangoSubstrateRepository(BaseArangoRepository[Substrate], ISubstrateRepository):
    _model_cls = Substrate

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SUBSTRATES)
        self._batches = BaseArangoRepository[SubstrateBatch](db, col.SUBSTRATE_BATCHES, SubstrateBatch)

    # ── Substrate CRUD ────────────────────────────────────────────────

    def get_all_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]:
        return super().get_all(offset, limit)

    def get_substrate_by_key(self, key: SubstrateKey) -> Substrate | None:
        return super().get_by_key(key)

    def create_substrate(self, substrate: Substrate) -> Substrate:
        return super().create(substrate)

    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate:
        return super().update(key, substrate)

    def delete_substrate(self, key: SubstrateKey) -> bool:
        return super().delete(key)

    # ── Substrate Batch CRUD ──────────────────────────────────────────

    def get_batch_by_key(self, key: BatchKey) -> SubstrateBatch | None:
        return self._batches.get_by_key(key)

    def get_batches_by_substrate(self, substrate_key: SubstrateKey) -> list[SubstrateBatch]:
        return self._batches.find_by_field("substrate_key", substrate_key)

    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch:
        created = self._batches.create(batch)
        if batch.substrate_key:
            batch_id_full = f"{col.SUBSTRATE_BATCHES}/{created.key}"
            substrate_id = f"{col.SUBSTRATES}/{batch.substrate_key}"
            self.create_edge(
                col.USES_TYPE,
                batch_id_full,
                substrate_id,
                data={
                    "batch_id": batch.batch_id,
                },
            )
        return created

    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch:
        return self._batches.update(key, batch)

    def delete_batch(self, key: BatchKey) -> bool:
        batch_id = f"{col.SUBSTRATE_BATCHES}/{key}"
        self.delete_edges(col.USES_TYPE, batch_id)
        self.delete_edges(col.FILLED_WITH, batch_id, direction="inbound")
        return self._batches.delete(key)

    def assign_batch_to_slot(self, batch_key: BatchKey, slot_key: SlotKey) -> dict:
        slot_id = f"{col.SLOTS}/{slot_key}"
        batch_id = f"{col.SUBSTRATE_BATCHES}/{batch_key}"
        return self.create_edge(col.FILLED_WITH, slot_id, batch_id)
