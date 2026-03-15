from abc import ABC, abstractmethod

from app.common.types import FertilizerKey, FertilizerStockKey
from app.domain.models.fertilizer import Fertilizer, FertilizerStock


class IFertilizerRepository(ABC):
    # ── Fertilizer CRUD ──────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[Fertilizer], int]: ...

    @abstractmethod
    def get_by_key(self, key: FertilizerKey) -> Fertilizer | None: ...

    @abstractmethod
    def create(self, fertilizer: Fertilizer) -> Fertilizer: ...

    @abstractmethod
    def update(self, key: FertilizerKey, fertilizer: Fertilizer) -> Fertilizer: ...

    @abstractmethod
    def delete(self, key: FertilizerKey) -> bool: ...

    # ── Stock CRUD ───────────────────────────────────────────────────

    @abstractmethod
    def create_stock(self, stock: FertilizerStock) -> FertilizerStock: ...

    @abstractmethod
    def get_stocks(self, fertilizer_key: FertilizerKey) -> list[FertilizerStock]: ...

    @abstractmethod
    def update_stock(self, key: FertilizerStockKey, stock: FertilizerStock) -> FertilizerStock: ...

    @abstractmethod
    def delete_stock(self, key: FertilizerStockKey) -> bool: ...

    # ── Incompatibility ──────────────────────────────────────────────

    @abstractmethod
    def add_incompatibility(
        self,
        key_a: FertilizerKey,
        key_b: FertilizerKey,
        reason: str,
        severity: str,
    ) -> dict: ...

    @abstractmethod
    def get_incompatibilities(self, key: FertilizerKey) -> list[dict]: ...

    @abstractmethod
    def remove_incompatibility(self, key_a: FertilizerKey, key_b: FertilizerKey) -> bool: ...

    # ── Reverse lookup ─────────────────────────────────────────────────

    @abstractmethod
    def get_nutrient_plan_usage(self, key: FertilizerKey) -> list[dict]: ...
