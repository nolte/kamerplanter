"""REQ-016 §3.4/§3.5 — InvenTree sync engine and consumption tracker.

``InvenTreeSyncEngine`` orchestrates the bidirectional sync for **one** tenant:

* **READ** (:meth:`sync_stock_levels`) pulls current stock into the local cache
  and flags drift > 20 %.
* **WRITE** (:meth:`push_pending_transactions`) sends pending consumption
  bookings to InvenTree, marking each ``synced`` or bumping its ``retry_count``.

``ConsumptionTracker`` turns domain consumption events (feeding, tank fill,
maintenance) into pending :class:`StockTransaction` rows for entities linked
with ``auto_deduct=true`` — it never dials InvenTree itself (graceful
degradation: bookings queue locally and drain on the next push).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.enums import StockTransactionStatus, StockTransactionType
from app.data_access.arango.inventree_repository import ArangoInvenTreeRepository
from app.domain.interfaces.inventree_adapter import InvenTreeAdapter
from app.domain.models.inventree import StockTransaction

logger = structlog.get_logger(__name__)

STOCK_DRIFT_THRESHOLD = 0.20  # 20 % deviation → warning


class InvenTreeSyncEngine:
    """Bidirectional stock sync with InvenTree for a single tenant."""

    def __init__(self, adapter: InvenTreeAdapter, repo: ArangoInvenTreeRepository, tenant_key: str) -> None:
        self._adapter = adapter
        self._repo = repo
        self._tenant_key = tenant_key

    async def sync_stock_levels(self) -> dict[str, Any]:
        """READ: pull current stock from InvenTree into the local cache."""
        stats: dict[str, Any] = {"updated": 0, "skipped": 0, "errors": 0, "drift_warnings": []}

        for ref in self._repo.list_references(self._tenant_key):
            if ref.key is None:
                continue
            try:
                part = await self._adapter.get_part(ref.inventree_part_id)
                if part is None:
                    stats["skipped"] += 1
                    continue

                old_stock = ref.cached_stock
                new_stock = part.total_in_stock
                if old_stock is not None and old_stock > 0:
                    drift = abs(new_stock - old_stock) / old_stock
                    if drift > STOCK_DRIFT_THRESHOLD:
                        stats["drift_warnings"].append(
                            {
                                "entity": f"{ref.entity_collection}/{ref.entity_key}",
                                "part_id": ref.inventree_part_id,
                                "old_stock": old_stock,
                                "new_stock": new_stock,
                                "drift_pct": round(drift * 100, 1),
                            }
                        )
                        logger.warning(
                            "inventree_stock_drift",
                            part_id=ref.inventree_part_id,
                            drift_pct=round(drift * 100, 1),
                        )

                self._repo.update_cached_stock(
                    ref.key,
                    stock=new_stock,
                    unit=part.stock_unit,
                    updated_at=datetime.now(tz=UTC).isoformat(),
                )
                stats["updated"] += 1
            except Exception as exc:  # noqa: BLE001 — one bad ref must not abort the run
                stats["errors"] += 1
                logger.warning("inventree_stock_sync_error", ref_key=ref.key, error=type(exc).__name__)

        return stats

    async def push_pending_transactions(self) -> dict[str, Any]:
        """WRITE: send pending consumption bookings to InvenTree."""
        stats: dict[str, Any] = {"synced": 0, "failed": 0, "skipped": 0}

        for txn in self._repo.find_pending_transactions(self._tenant_key, max_retries=3):
            if txn.key is None:
                continue
            try:
                stock_items = await self._adapter.get_stock_items(txn.inventree_part_id)
                if not stock_items:
                    self._mark_failed(txn, "No stock items found")
                    stats["failed"] += 1
                    continue

                item = {"pk": stock_items[0].pk, "quantity": txn.quantity}
                if txn.transaction_type == StockTransactionType.REMOVE:
                    result = await self._adapter.remove_stock([item], notes=txn.reason)
                elif txn.transaction_type == StockTransactionType.ADD:
                    result = await self._adapter.add_stock([item], notes=txn.reason)
                else:
                    result = await self._adapter.count_stock([item], notes=txn.reason)

                if result.success:
                    self._mark_synced(txn, result.model_dump())
                    stats["synced"] += 1
                else:
                    self._increment_retry(txn, result.error)
                    stats["failed"] += 1
            except Exception as exc:  # noqa: BLE001 — a single failure must not abort the batch
                self._increment_retry(txn, type(exc).__name__)
                stats["failed"] += 1
                logger.warning("inventree_push_error", txn_key=txn.key, error=type(exc).__name__)

        return stats

    async def link_entity(
        self,
        entity_collection: str,
        entity_key: str,
        inventree_part_id: int,
        *,
        auto_deduct: bool = False,
        deduct_unit: str | None = None,
    ):
        """Verify the part exists, then persist the reference with an initial pull."""
        from app.common.exceptions import NotFoundError
        from app.domain.models.inventree import InvenTreeReference

        part = await self._adapter.get_part(inventree_part_id)
        if part is None:
            raise NotFoundError("InvenTreePart", str(inventree_part_id))

        reference = InvenTreeReference(
            tenant_key=self._tenant_key,
            entity_collection=entity_collection,
            entity_key=entity_key,
            inventree_part_id=inventree_part_id,
            inventree_part_name=part.name,
            inventree_ipn=part.ipn,
            cached_stock=part.total_in_stock,
            cached_stock_unit=part.stock_unit,
            cached_stock_updated_at=datetime.now(tz=UTC),
            auto_deduct=auto_deduct,
            deduct_unit=deduct_unit,
        )
        return self._repo.upsert_reference(reference)

    # ── Transaction status transitions ──────────────────────────────────

    def _mark_synced(self, txn: StockTransaction, response: dict) -> None:
        merged = txn.model_copy(
            update={
                "status": StockTransactionStatus.SYNCED,
                "inventree_response": response,
                "synced_at": datetime.now(tz=UTC),
                "last_error": None,
            }
        )
        if txn.key:
            self._repo.update_transaction(txn.key, merged)

    def _mark_failed(self, txn: StockTransaction, error: str) -> None:
        merged = txn.model_copy(update={"status": StockTransactionStatus.FAILED, "last_error": error})
        if txn.key:
            self._repo.update_transaction(txn.key, merged)

    def _increment_retry(self, txn: StockTransaction, error: str | None) -> None:
        retry_count = txn.retry_count + 1
        status = StockTransactionStatus.FAILED if retry_count >= 3 else StockTransactionStatus.PENDING
        merged = txn.model_copy(update={"retry_count": retry_count, "last_error": error, "status": status})
        if txn.key:
            self._repo.update_transaction(txn.key, merged)


class ConsumptionTracker:
    """Turns consumption events into pending stock transactions (REQ-016 §3.5)."""

    def __init__(self, repo: ArangoInvenTreeRepository, tenant_key: str) -> None:
        self._repo = repo
        self._tenant_key = tenant_key

    def _track(
        self,
        entity_collection: str,
        entity_key: str,
        quantity: float,
        default_unit: str,
        reason: str,
        source_collection: str,
        source_key: str,
    ) -> str | None:
        if not entity_key or quantity <= 0:
            return None
        ref = self._repo.find_reference_by_entity(self._tenant_key, entity_collection, entity_key)
        if ref is None or not ref.auto_deduct or ref.key is None:
            return None
        transaction = StockTransaction(
            tenant_key=self._tenant_key,
            reference_key=ref.key,
            inventree_part_id=ref.inventree_part_id,
            transaction_type=StockTransactionType.REMOVE,
            quantity=quantity,
            unit=ref.deduct_unit or default_unit,
            reason=reason,
            source_event_collection=source_collection,
            source_event_key=source_key,
        )
        created = self._repo.create_transaction(transaction)
        return created.key

    def on_feeding_event(self, feeding_event: dict) -> list[str]:
        """Hook after a FeedingEvent (REQ-004): one txn per auto-deduct fertilizer."""
        txn_keys: list[str] = []
        event_key = feeding_event.get("_key", feeding_event.get("key", ""))
        for component in feeding_event.get("components", []):
            fert_key = component.get("fertilizer_key")
            amount_ml = component.get("amount_ml", 0) or 0
            name = component.get("fertilizer_name", fert_key)
            key = self._track(
                "fertilizers",
                fert_key or "",
                float(amount_ml),
                "ml",
                f"FeedingEvent {event_key}: {name} {amount_ml}ml",
                "feeding_events",
                event_key,
            )
            if key:
                txn_keys.append(key)
        if txn_keys:
            logger.info("consumption_tracked_feeding", event_key=event_key, transactions=len(txn_keys))
        return txn_keys

    def on_maintenance_log(self, maintenance_log: dict) -> list[str]:
        """Hook after a MaintenanceLog (REQ-014): txn per consumed product."""
        txn_keys: list[str] = []
        log_key = maintenance_log.get("_key", maintenance_log.get("key", ""))
        maintenance_type = maintenance_log.get("maintenance_type", "")
        for product in maintenance_log.get("products_used", []):
            entity_collection = product.get("entity_collection", "equipment")
            entity_key = product.get("entity_key")
            amount = product.get("amount", 0) or 0
            unit = product.get("unit", "ml")
            name = product.get("name", entity_key)
            key = self._track(
                entity_collection,
                entity_key or "",
                float(amount),
                unit,
                f"MaintenanceLog {log_key}: {name} {amount}{unit} ({maintenance_type})",
                "maintenance_logs",
                log_key,
            )
            if key:
                txn_keys.append(key)
        if txn_keys:
            logger.info("consumption_tracked_maintenance", log_key=log_key, transactions=len(txn_keys))
        return txn_keys
