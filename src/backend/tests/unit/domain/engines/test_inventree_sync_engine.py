"""REQ-016 — unit tests for the InvenTree sync engine and consumption tracker.

A fake adapter (canned parts / stock / adjustment results) and a small in-memory
repository exercise the READ drift detection, the WRITE push with retry bumping,
and the consumption-tracker's ``auto_deduct`` gating — all without any HTTP.
"""

from __future__ import annotations

import pytest

from app.common.enums import StockTransactionStatus, StockTransactionType
from app.domain.engines.inventree_sync_engine import ConsumptionTracker, InvenTreeSyncEngine
from app.domain.interfaces.inventree_adapter import (
    InvenTreePartData,
    InvenTreeStockItemData,
    StockAdjustmentResult,
)
from app.domain.models.inventree import InvenTreeReference, StockTransaction

TENANT = "tenant_a"


class FakeAdapter:
    def __init__(self, *, part=None, stock_items=None, adjust_success=True):
        self._part = part
        self._stock_items = stock_items or []
        self._adjust_success = adjust_success
        self.calls: list[str] = []

    async def get_part(self, part_id: int):
        self.calls.append(f"get_part:{part_id}")
        return self._part

    async def get_stock_items(self, part_id: int):
        return self._stock_items

    async def remove_stock(self, items, *, notes=""):
        self.calls.append("remove_stock")
        return StockAdjustmentResult(
            success=self._adjust_success, items_affected=len(items), error=None if self._adjust_success else "boom"
        )

    async def add_stock(self, items, *, notes=""):
        return StockAdjustmentResult(success=self._adjust_success)

    async def count_stock(self, items, *, notes=""):
        return StockAdjustmentResult(success=self._adjust_success)


class FakeRepo:
    def __init__(self):
        self.references: dict[str, InvenTreeReference] = {}
        self.transactions: dict[str, StockTransaction] = {}
        self._seq = 0

    def _next(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    def list_references(self, tenant_key):
        return [r for r in self.references.values() if r.tenant_key == tenant_key]

    def update_cached_stock(self, key, *, stock, unit, updated_at):
        ref = self.references[key]
        merged = ref.model_copy(update={"cached_stock": stock, "cached_stock_unit": unit})
        self.references[key] = merged
        return merged

    def find_reference_by_entity(self, tenant_key, entity_collection, entity_key):
        for r in self.references.values():
            if r.tenant_key == tenant_key and r.entity_collection == entity_collection and r.entity_key == entity_key:
                return r
        return None

    def upsert_reference(self, reference):
        key = reference.key or self._next("ref")
        stored = reference.model_copy(update={"key": key})
        self.references[key] = stored
        return stored

    def create_transaction(self, transaction):
        key = self._next("txn")
        stored = transaction.model_copy(update={"key": key})
        self.transactions[key] = stored
        return stored

    def find_pending_transactions(self, tenant_key, max_retries=3):
        return [
            t
            for t in self.transactions.values()
            if t.tenant_key == tenant_key and t.status == StockTransactionStatus.PENDING and t.retry_count < max_retries
        ]

    def update_transaction(self, key, transaction):
        self.transactions[key] = transaction
        return transaction


def _ref(**kwargs) -> InvenTreeReference:
    base = {
        "key": "ref1",
        "tenant_key": TENANT,
        "entity_collection": "fertilizers",
        "entity_key": "fert_1",
        "inventree_part_id": 42,
        "cached_stock": 1000.0,
        "auto_deduct": True,
        "deduct_unit": "ml",
    }
    base.update(kwargs)
    return InvenTreeReference(**base)


class TestSyncStockLevels:
    @pytest.mark.asyncio
    async def test_updates_cache_and_flags_drift(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref()
        adapter = FakeAdapter(part=InvenTreePartData(pk=42, name="BioGrow", total_in_stock=750.0, stock_unit="ml"))
        engine = InvenTreeSyncEngine(adapter, repo, TENANT)

        stats = await engine.sync_stock_levels()

        assert stats["updated"] == 1
        assert repo.references["ref1"].cached_stock == 750.0
        # |750-1000|/1000 = 25% > 20% threshold → one drift warning.
        assert len(stats["drift_warnings"]) == 1
        assert stats["drift_warnings"][0]["drift_pct"] == 25.0

    @pytest.mark.asyncio
    async def test_missing_part_is_skipped(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref()
        engine = InvenTreeSyncEngine(FakeAdapter(part=None), repo, TENANT)

        stats = await engine.sync_stock_levels()

        assert stats["skipped"] == 1
        assert stats["updated"] == 0


class TestPushPending:
    @pytest.mark.asyncio
    async def test_successful_push_marks_synced(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref()
        repo.transactions["txn1"] = StockTransaction(
            key="txn1",
            tenant_key=TENANT,
            reference_key="ref1",
            inventree_part_id=42,
            transaction_type=StockTransactionType.REMOVE,
            quantity=50,
            unit="ml",
            reason="feed",
        )
        adapter = FakeAdapter(stock_items=[InvenTreeStockItemData(pk=900, part_id=42, quantity=1000)])
        engine = InvenTreeSyncEngine(adapter, repo, TENANT)

        stats = await engine.push_pending_transactions()

        assert stats["synced"] == 1
        assert repo.transactions["txn1"].status == StockTransactionStatus.SYNCED
        assert repo.transactions["txn1"].synced_at is not None

    @pytest.mark.asyncio
    async def test_no_stock_items_marks_failed(self):
        repo = FakeRepo()
        repo.transactions["txn1"] = StockTransaction(
            key="txn1",
            tenant_key=TENANT,
            reference_key="ref1",
            inventree_part_id=42,
            transaction_type=StockTransactionType.REMOVE,
            quantity=50,
            unit="ml",
            reason="feed",
        )
        engine = InvenTreeSyncEngine(FakeAdapter(stock_items=[]), repo, TENANT)

        stats = await engine.push_pending_transactions()

        assert stats["failed"] == 1
        assert repo.transactions["txn1"].status == StockTransactionStatus.FAILED

    @pytest.mark.asyncio
    async def test_adjust_failure_bumps_retry_and_keeps_pending(self):
        repo = FakeRepo()
        repo.transactions["txn1"] = StockTransaction(
            key="txn1",
            tenant_key=TENANT,
            reference_key="ref1",
            inventree_part_id=42,
            transaction_type=StockTransactionType.REMOVE,
            quantity=50,
            unit="ml",
            reason="feed",
        )
        adapter = FakeAdapter(
            stock_items=[InvenTreeStockItemData(pk=900, part_id=42, quantity=1000)], adjust_success=False
        )
        engine = InvenTreeSyncEngine(adapter, repo, TENANT)

        stats = await engine.push_pending_transactions()

        assert stats["failed"] == 1
        txn = repo.transactions["txn1"]
        assert txn.retry_count == 1
        assert txn.status == StockTransactionStatus.PENDING

    @pytest.mark.asyncio
    async def test_link_entity_persists_reference_with_initial_pull(self):
        repo = FakeRepo()
        adapter = FakeAdapter(
            part=InvenTreePartData(pk=42, name="CalMag", ipn="CM-1", total_in_stock=500, stock_unit="ml")
        )
        engine = InvenTreeSyncEngine(adapter, repo, TENANT)

        ref = await engine.link_entity("fertilizers", "fert_9", 42, auto_deduct=True, deduct_unit="ml")

        assert ref.inventree_part_name == "CalMag"
        assert ref.cached_stock == 500
        assert ref.auto_deduct is True

    @pytest.mark.asyncio
    async def test_link_entity_unknown_part_raises(self):
        from app.common.exceptions import NotFoundError

        engine = InvenTreeSyncEngine(FakeAdapter(part=None), FakeRepo(), TENANT)
        with pytest.raises(NotFoundError):
            await engine.link_entity("fertilizers", "fert_9", 999)


class TestConsumptionTracker:
    def test_feeding_event_creates_pending_txn_for_auto_deduct(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref()
        tracker = ConsumptionTracker(repo, TENANT)

        keys = tracker.on_feeding_event(
            {
                "_key": "feed_42",
                "components": [{"fertilizer_key": "fert_1", "fertilizer_name": "CalMag", "amount_ml": 50}],
            }
        )

        assert len(keys) == 1
        txn = repo.transactions[keys[0]]
        assert txn.quantity == 50
        assert txn.unit == "ml"
        assert txn.status == StockTransactionStatus.PENDING
        assert "CalMag" in txn.reason

    def test_feeding_event_skips_when_auto_deduct_off(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref(auto_deduct=False)
        tracker = ConsumptionTracker(repo, TENANT)

        keys = tracker.on_feeding_event(
            {"_key": "feed_42", "components": [{"fertilizer_key": "fert_1", "amount_ml": 50}]}
        )

        assert keys == []

    def test_feeding_event_skips_unlinked_fertilizer(self):
        tracker = ConsumptionTracker(FakeRepo(), TENANT)
        keys = tracker.on_feeding_event(
            {"_key": "feed_42", "components": [{"fertilizer_key": "unknown", "amount_ml": 50}]}
        )
        assert keys == []

    def test_maintenance_log_tracks_products(self):
        repo = FakeRepo()
        repo.references["ref1"] = _ref(entity_collection="equipment", entity_key="h2o2", deduct_unit=None)
        tracker = ConsumptionTracker(repo, TENANT)

        keys = tracker.on_maintenance_log(
            {
                "_key": "maint_1",
                "maintenance_type": "sanitization",
                "products_used": [
                    {
                        "entity_collection": "equipment",
                        "entity_key": "h2o2",
                        "name": "H2O2",
                        "amount": 250,
                        "unit": "ml",
                    }
                ],
            }
        )

        assert len(keys) == 1
        assert repo.transactions[keys[0]].quantity == 250
