from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import BatchKey, SlotKey, SubstrateKey
    from app.domain.models.substrate import Substrate, SubstrateBatch


class ISubstrateRepository(ABC):
    @abstractmethod
    def get_all_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]: ...

    @abstractmethod
    def get_substrate_by_key(self, key: SubstrateKey) -> Substrate | None: ...

    @abstractmethod
    def create_substrate(self, substrate: Substrate) -> Substrate: ...

    @abstractmethod
    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate: ...

    @abstractmethod
    def delete_substrate(self, key: SubstrateKey) -> bool: ...

    @abstractmethod
    def get_batch_by_key(self, key: BatchKey) -> SubstrateBatch | None: ...

    @abstractmethod
    def get_batches_by_substrate(self, substrate_key: SubstrateKey) -> list[SubstrateBatch]: ...

    @abstractmethod
    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch: ...

    @abstractmethod
    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch: ...

    @abstractmethod
    def delete_batch(self, key: BatchKey) -> bool: ...

    @abstractmethod
    def assign_batch_to_slot(self, batch_key: BatchKey, slot_key: SlotKey) -> dict: ...
