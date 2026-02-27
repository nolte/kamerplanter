from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.types import LocationKey, SlotKey, WateringEventKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.watering_repository import IWateringRepository
from app.domain.models.watering_event import WateringEvent


class ArangoWateringRepository(IWateringRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.WATERING_EVENTS)

    # ── Create & Read ──────────────────────────────────────────────────

    def create(self, event: WateringEvent) -> WateringEvent:
        data = event.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        if "watered_at" not in data or data["watered_at"] is None:
            data["watered_at"] = now
        result = self._db.collection(col.WATERING_EVENTS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = WateringEvent(**doc)

        # Create WATERED_SLOT edges (WateringEvent → Slot)
        event_id = f"{col.WATERING_EVENTS}/{doc['_key']}"
        for slot_key in event.slot_keys:
            slot_id = f"{col.SLOTS}/{slot_key}"
            self.create_edge(col.WATERED_SLOT, event_id, slot_id)

        return created

    def get_by_key(self, key: WateringEventKey) -> WateringEvent | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return WateringEvent(**doc) if doc else None

    def get_all(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[WateringEvent], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [WateringEvent(**doc) for doc in docs], total

    # ── Queries ────────────────────────────────────────────────────────

    def get_by_slot(
        self, slot_key: SlotKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        query = """
        FOR e IN @@edge_col
          FILTER e._to == @slot_id
          LET doc = DOCUMENT(e._from)
          SORT doc.watered_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        slot_id = f"{col.SLOTS}/{slot_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@edge_col": col.WATERED_SLOT,
            "slot_id": slot_id,
            "offset": offset,
            "limit": limit,
        })
        return [WateringEvent(**self._from_doc(doc)) for doc in cursor]

    def get_by_location(
        self, location_key: LocationKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        query = """
        FOR slot_edge IN @@has_slot
          FILTER slot_edge._from == @location_id
          FOR water_edge IN @@watered_slot
            FILTER water_edge._to == slot_edge._to
            LET doc = DOCUMENT(water_edge._from)
            SORT doc.watered_at DESC
            LIMIT @offset, @limit
            RETURN DISTINCT doc
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@has_slot": col.HAS_SLOT,
            "@watered_slot": col.WATERED_SLOT,
            "location_id": location_id,
            "offset": offset,
            "limit": limit,
        })
        return [WateringEvent(**self._from_doc(doc)) for doc in cursor]

    def get_stats_by_location(self, location_key: LocationKey) -> dict:
        query = """
        LET events = (
          FOR slot_edge IN @@has_slot
            FILTER slot_edge._from == @location_id
            FOR water_edge IN @@watered_slot
              FILTER water_edge._to == slot_edge._to
              LET doc = DOCUMENT(water_edge._from)
              RETURN DISTINCT doc
        )
        LET by_method = (
          FOR e IN events
            COLLECT method = e.application_method
            AGGREGATE cnt = COUNT(e), vol = SUM(e.volume_liters)
            RETURN { method, count: cnt, total_volume: vol }
        )
        RETURN {
          total_events: LENGTH(events),
          total_volume: SUM(events[*].volume_liters),
          by_method: by_method
        }
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@has_slot": col.HAS_SLOT,
            "@watered_slot": col.WATERED_SLOT,
            "location_id": location_id,
        })
        result = next(cursor, None)
        return result or {"total_events": 0, "total_volume": 0.0, "by_method": []}
