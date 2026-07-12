"""REQ-016 §3.2 — InvenTree adapter interface + normalized transfer models.

The interface pins the surface the sync engine / service depend on; the concrete
REST implementation lives in ``app.data_access.external.inventree_adapter``.
Normalized transfer models decouple the domain from InvenTree's raw JSON shape.

Source code is English (NFR-003); the specification lives in
``spec/req/REQ-016_InvenTree-Integration.md`` (German).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class InvenTreePartData(BaseModel):
    """Normalized part data from InvenTree."""

    pk: int
    name: str
    ipn: str | None = None
    description: str | None = None
    category_name: str | None = None
    is_purchaseable: bool = False
    is_trackable: bool = False
    total_in_stock: float = 0.0
    stock_unit: str | None = None


class InvenTreeStockItemData(BaseModel):
    """Normalized stock-item data from InvenTree."""

    pk: int
    part_id: int
    quantity: float
    serial: str | None = None
    location_name: str | None = None
    status: int = 10  # 10 = OK in InvenTree


class InvenTreeCategoryData(BaseModel):
    """Normalized part-category data from InvenTree."""

    pk: int
    name: str
    parent: int | None = None
    path: str = ""
    part_count: int = 0


class StockAdjustmentResult(BaseModel):
    """Result of a stock adjustment (remove/add/count)."""

    success: bool
    items_affected: int = 0
    error: str | None = None


class InvenTreeAdapter(ABC):
    """Adapter interface for InvenTree communication."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the InvenTree API is reachable and authenticated."""

    @abstractmethod
    async def get_part(self, part_id: int) -> InvenTreePartData | None:
        """Load a single part by id (``None`` when it does not exist)."""

    @abstractmethod
    async def search_parts(
        self, query: str, *, category_id: int | None = None, limit: int = 25
    ) -> list[InvenTreePartData]:
        """Search parts by name / IPN / description."""

    @abstractmethod
    async def get_stock_items(self, part_id: int) -> list[InvenTreeStockItemData]:
        """Load all stock items of a part."""

    @abstractmethod
    async def remove_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        """Remove stock (consumption). ``items``: ``[{"pk", "quantity"}]``."""

    @abstractmethod
    async def add_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        """Add stock (correction). ``items``: ``[{"pk", "quantity"}]``."""

    @abstractmethod
    async def count_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        """Stock-take reconciliation. ``items``: ``[{"pk", "quantity"}]``."""

    @abstractmethod
    async def get_categories(self, *, parent_id: int | None = None) -> list[InvenTreeCategoryData]:
        """Load part categories (optionally filtered by parent)."""
