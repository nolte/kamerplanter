from datetime import UTC, date, datetime

from arango.database import StandardDatabase

from app.common.types import LocationKey, PlantInstanceKey, WateringEventKey
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

        # Create WATERED_PLANT edges (WateringEvent → PlantInstance)
        event_id = f"{col.WATERING_EVENTS}/{doc['_key']}"
        for plant_key in event.plant_keys:
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            self.create_edge(col.WATERED_PLANT, event_id, plant_id)

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

    def get_by_plant(
        self, plant_key: PlantInstanceKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        query = """
        FOR e IN @@edge_col
          FILTER e._to == @plant_id
          LET doc = DOCUMENT(e._from)
          SORT doc.watered_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@edge_col": col.WATERED_PLANT,
            "plant_id": plant_id,
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
          FOR placed_edge IN @@placed_in
            FILTER placed_edge._to == slot_edge._to
            FOR water_edge IN @@watered_plant
              FILTER water_edge._to == placed_edge._from
              LET doc = DOCUMENT(water_edge._from)
              SORT doc.watered_at DESC
              LIMIT @offset, @limit
              RETURN DISTINCT doc
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@has_slot": col.HAS_SLOT,
            "@placed_in": col.PLACED_IN,
            "@watered_plant": col.WATERED_PLANT,
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
            FOR placed_edge IN @@placed_in
              FILTER placed_edge._to == slot_edge._to
              FOR water_edge IN @@watered_plant
                FILTER water_edge._to == placed_edge._from
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
            "@placed_in": col.PLACED_IN,
            "@watered_plant": col.WATERED_PLANT,
            "location_id": location_id,
        })
        result = next(cursor, None)
        return result or {"total_events": 0, "total_volume": 0.0, "by_method": []}

    def get_last_watering_date_for_run(self, run_key: str) -> date | None:
        query = """
        LET plant_keys = (
          FOR rc IN @@run_contains
            FILTER rc._from == @run_id
            FILTER rc.detached_at == null
            RETURN PARSE_IDENTIFIER(rc._to).key
        )
        FOR we IN @@watering_events
          FILTER LENGTH(INTERSECTION(we.plant_keys, plant_keys)) > 0
          SORT we.watered_at DESC
          LIMIT 1
          RETURN we.watered_at
        """
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        cursor = self._db.aql.execute(query, bind_vars={
            "@run_contains": col.RUN_CONTAINS,
            "@watering_events": col.WATERING_EVENTS,
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
