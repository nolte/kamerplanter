from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.watering_log_repository import IWateringLogRepository
from app.domain.models.watering_log import WateringLog

if TYPE_CHECKING:
    from arango.database import StandardDatabase


class ArangoWateringLogRepository(IWateringLogRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.WATERING_LOGS)

    # ── Mapping helper ──────────────────────────────────────────────────

    def _to_model(self, doc: dict) -> WateringLog:
        return WateringLog(**self._from_doc(doc))

    # ── Create ──────────────────────────────────────────────────────────

    def create(self, log: WateringLog) -> WateringLog:
        data = log.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        if "logged_at" not in data or data["logged_at"] is None:
            data["logged_at"] = now
        result = self._db.collection(col.WATERING_LOGS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = WateringLog(**doc)

        log_id = f"{col.WATERING_LOGS}/{doc['_key']}"

        # Create LOG_SLOT edges (WateringLog -> Slot)
        for slot_key in log.slot_keys:
            slot_id = f"{col.SLOTS}/{slot_key}"
            self.create_edge(col.LOG_SLOT, log_id, slot_id)

        # Create LOG_PLANT edges (WateringLog -> PlantInstance)
        for plant_key in log.plant_keys:
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            self.create_edge(col.LOG_PLANT, log_id, plant_id)

        # Create LOG_FERTILIZER edges (WateringLog -> Fertilizer)
        for fert in log.fertilizers_used:
            fert_id = f"{col.FERTILIZERS}/{fert.fertilizer_key}"
            self.create_edge(
                col.LOG_FERTILIZER, log_id, fert_id,
                {"ml_per_liter": fert.ml_per_liter},
            )

        return created

    # ── Read ────────────────────────────────────────────────────────────

    def get_by_key(self, key: str) -> WateringLog | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return WateringLog(**doc) if doc else None

    def get_all(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[WateringLog], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [WateringLog(**doc) for doc in docs], total

    def resolve_plant_names(self, plant_keys: list[str]) -> dict[str, str]:
        """Batch-resolve plant keys to display names."""
        if not plant_keys:
            return {}
        query = """
        FOR pk IN @plant_keys
          LET pi = DOCUMENT(CONCAT(@col, "/", pk))
          FILTER pi != null
          RETURN { key: pk, name: pi.plant_name || pi.instance_id || pk }
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "plant_keys": plant_keys,
            "col": col.PLANT_INSTANCES,
        })
        return {r["key"]: r["name"] for r in cursor}

    def resolve_fertilizer_names(self, fert_keys: list[str]) -> dict[str, str]:
        """Batch-resolve fertilizer keys to display names."""
        if not fert_keys:
            return {}
        query = """
        FOR fk IN @fert_keys
          LET f = DOCUMENT(CONCAT(@col, "/", fk))
          FILTER f != null
          RETURN { key: fk, name: CONCAT(f.product_name, " (", f.brand, ")") }
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "fert_keys": fert_keys,
            "col": col.FERTILIZERS,
        })
        return {r["key"]: r["name"] for r in cursor}

    # ── Update ──────────────────────────────────────────────────────────

    def update(self, key: str, log: WateringLog) -> WateringLog:
        data = log.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.WATERING_LOGS).update(
            {"_key": key, **data}, return_new=True,
        )
        return WateringLog(**self._from_doc(result["new"]))

    def update_fields(self, key: str, fields: dict) -> WateringLog:
        fields["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.WATERING_LOGS).update(
            {"_key": key, **fields}, return_new=True,
        )
        return WateringLog(**self._from_doc(result["new"]))

    # ── Delete ──────────────────────────────────────────────────────────

    def delete(self, key: str) -> bool:
        log_id = f"{col.WATERING_LOGS}/{key}"
        # Delete outbound edges
        self.delete_edges(col.LOG_SLOT, log_id)
        self.delete_edges(col.LOG_PLANT, log_id)
        self.delete_edges(col.LOG_FERTILIZER, log_id)
        return BaseArangoRepository.delete(self, key)

    # ── Queries ─────────────────────────────────────────────────────────

    def get_by_slot(
        self, slot_key: str, offset: int = 0, limit: int = 50,
    ) -> list[WateringLog]:
        query = """
        FOR e IN @@edge_col
          FILTER e._to == @slot_id
          LET doc = DOCUMENT(e._from)
          SORT doc.logged_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        slot_id = f"{col.SLOTS}/{slot_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@edge_col": col.LOG_SLOT,
            "slot_id": slot_id,
            "offset": offset,
            "limit": limit,
        })
        return [self._to_model(doc) for doc in cursor]

    def get_by_location(
        self, location_key: str, offset: int = 0, limit: int = 50,
    ) -> list[WateringLog]:
        query = """
        FOR slot_edge IN @@has_slot
          FILTER slot_edge._from == @location_id
          FOR log_edge IN @@log_slot
            FILTER log_edge._to == slot_edge._to
            LET doc = DOCUMENT(log_edge._from)
            SORT doc.logged_at DESC
            LIMIT @offset, @limit
            RETURN DISTINCT doc
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@has_slot": col.HAS_SLOT,
            "@log_slot": col.LOG_SLOT,
            "location_id": location_id,
            "offset": offset,
            "limit": limit,
        })
        return [self._to_model(doc) for doc in cursor]

    def get_stats_by_location(self, location_key: str) -> dict:
        query = """
        LET logs = (
          FOR slot_edge IN @@has_slot
            FILTER slot_edge._from == @location_id
            FOR log_edge IN @@log_slot
              FILTER log_edge._to == slot_edge._to
              LET doc = DOCUMENT(log_edge._from)
              RETURN DISTINCT doc
        )
        LET by_method = (
          FOR l IN logs
            COLLECT method = l.application_method
            AGGREGATE cnt = COUNT(l), vol = SUM(l.volume_liters)
            RETURN { method, count: cnt, total_volume: vol }
        )
        RETURN {
          total_events: LENGTH(logs),
          total_volume: SUM(logs[*].volume_liters),
          by_method: by_method
        }
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@has_slot": col.HAS_SLOT,
            "@log_slot": col.LOG_SLOT,
            "location_id": location_id,
        })
        result = next(cursor, None)
        return result or {"total_events": 0, "total_volume": 0.0, "by_method": []}

    def get_last_watering_date_for_run(self, run_key: str) -> date | None:
        query = """
        LET slot_keys = (
          FOR rc IN @@run_contains
            FILTER rc._from == @run_id
            FILTER rc.detached_at == null
            FOR pi IN @@placed_in
              FILTER pi._from == rc._to
              RETURN PARSE_IDENTIFIER(pi._to).key
        )
        FOR wl IN @@watering_logs
          FILTER LENGTH(INTERSECTION(wl.slot_keys, slot_keys)) > 0
          SORT wl.logged_at DESC
          LIMIT 1
          RETURN wl.logged_at
        """
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@run_contains": col.RUN_CONTAINS,
            "@placed_in": col.PLACED_IN,
            "@watering_logs": col.WATERING_LOGS,
            "run_id": run_id,
        })
        result = next(cursor, None)
        if result is None:
            return None
        if isinstance(result, str):
            return datetime.fromisoformat(result).date()
        if isinstance(result, datetime):
            return result.date()
        return None

    def get_by_plant(
        self, plant_key: str, offset: int = 0, limit: int = 50,
    ) -> list[WateringLog]:
        query = """
        FOR doc IN @@collection
          FILTER @plant_key IN doc.plant_keys
          SORT doc.logged_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.WATERING_LOGS,
            "plant_key": plant_key,
            "offset": offset,
            "limit": limit,
        })
        return [self._to_model(doc) for doc in cursor]

    def get_latest_by_plant(self, plant_key: str) -> WateringLog | None:
        results = self.get_by_plant(plant_key, offset=0, limit=1)
        return results[0] if results else None

    def get_recent_runoff_logs(
        self, plant_key: str, limit: int = 5,
    ) -> list[WateringLog]:
        query = """
        FOR doc IN @@collection
          FILTER @plant_key IN doc.plant_keys
            AND doc.runoff_ec != null
          SORT doc.logged_at DESC
          LIMIT @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.WATERING_LOGS,
            "plant_key": plant_key,
            "limit": limit,
        })
        return [self._to_model(doc) for doc in cursor]
