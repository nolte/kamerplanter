from datetime import date

from app.common.enums import IrrigationStrategy, SubstrateType
from app.common.exceptions import NotFoundError
from app.common.types import BatchKey, SlotKey, SubstrateKey
from app.domain.engines.substrate_lifecycle_manager import SubstrateLifecycleManager
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import Substrate, SubstrateBatch


class SubstrateService:
    def __init__(self, substrate_repo: ISubstrateRepository) -> None:
        self._repo = substrate_repo
        self._lifecycle_mgr = SubstrateLifecycleManager(substrate_repo)

    def list_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]:
        return self._repo.get_all_substrates(offset, limit)

    def get_substrate(self, key: SubstrateKey) -> Substrate:
        substrate = self._repo.get_substrate_by_key(key)
        if substrate is None:
            raise NotFoundError("Substrate", key)
        return substrate

    def create_substrate(self, substrate: Substrate) -> Substrate:
        return self._repo.create_substrate(substrate)

    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate:
        self.get_substrate(key)
        return self._repo.update_substrate(key, substrate)

    def delete_substrate(self, key: SubstrateKey) -> bool:
        self.get_substrate(key)
        return self._repo.delete_substrate(key)

    def list_batches(self, substrate_key: SubstrateKey) -> list[SubstrateBatch]:
        self.get_substrate(substrate_key)
        return self._repo.get_batches_by_substrate(substrate_key)

    def get_batch(self, key: BatchKey) -> SubstrateBatch:
        batch = self._repo.get_batch_by_key(key)
        if batch is None:
            raise NotFoundError("SubstrateBatch", key)
        return batch

    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch:
        self.get_substrate(batch.substrate_key)
        return self._repo.create_batch(batch)

    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch:
        self.get_batch(key)
        return self._repo.update_batch(key, batch)

    def delete_batch(self, key: BatchKey) -> bool:
        self.get_batch(key)
        return self._repo.delete_batch(key)

    def check_reusability(
        self, batch_key: BatchKey,
    ) -> tuple[bool, list[str], list[dict[str, str | float]], float, date | None]:
        self.get_batch(batch_key)
        return self._lifecycle_mgr.check_reusability(batch_key)

    def prepare_reuse(self, batch_key: BatchKey) -> dict:
        batch = self.get_batch(batch_key)
        substrate = self.get_substrate(batch.substrate_key)
        can_reuse, issues, prep_steps, prep_time, ready_date = self._lifecycle_mgr.check_reusability(batch_key)
        if not can_reuse:
            return {
                "can_reuse": False,
                "issues": issues,
                "preparation_steps": [],
                "estimated_prep_time_hours": 0,
                "ready_date": None,
            }
        return {
            "can_reuse": True,
            "issues": [],
            "preparation_steps": prep_steps,
            "estimated_prep_time_hours": prep_time,
            "ready_date": ready_date,
        }

    def assign_batch_to_slot(self, batch_key: BatchKey, slot_key: SlotKey) -> dict:
        self.get_batch(batch_key)
        return self._repo.assign_batch_to_slot(batch_key, slot_key)

    @staticmethod
    def get_irrigation_strategy(substrate_type: SubstrateType) -> IrrigationStrategy:
        return SubstrateLifecycleManager.get_irrigation_strategy(substrate_type)
