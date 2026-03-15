from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.feeding_repository import IFeedingRepository
from app.domain.models.feeding_event import FeedingEvent

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import FeedingEventKey


class ArangoFeedingRepository(IFeedingRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.FEEDING_EVENTS)

    # ── CRUD ─────────────────────────────────────────────────────────

    def get_all(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[FeedingEvent], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [FeedingEvent(**doc) for doc in docs], total

    def get_by_key(self, key: FeedingEventKey) -> FeedingEvent | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return FeedingEvent(**doc) if doc else None

    def create(self, event: FeedingEvent) -> FeedingEvent:
        data = event.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = now
        result = self._db.collection(col.FEEDING_EVENTS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = FeedingEvent(**doc)

        # Create FED_BY edge (PlantInstance → FeedingEvent)
        plant_id = f"{col.PLANT_INSTANCES}/{event.plant_key}"
        event_id = f"{col.FEEDING_EVENTS}/{doc['_key']}"
        self.create_edge(col.FED_BY, plant_id, event_id)

        # Create FEEDING_USED edges (FeedingEvent → Fertilizer)
        for fert_used in event.fertilizers_used:
            fert_id = f"{col.FERTILIZERS}/{fert_used.fertilizer_key}"
            self.create_edge(
                col.FEEDING_USED, event_id, fert_id,
                {"ml_applied": fert_used.ml_applied},
            )

        return created

    def update(self, key: FeedingEventKey, event: FeedingEvent) -> FeedingEvent:
        data = event.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.FEEDING_EVENTS).update(
            {"_key": key, **data}, return_new=True,
        )
        return FeedingEvent(**self._from_doc(result["new"]))

    def delete(self, key: FeedingEventKey) -> bool:
        event_id = f"{col.FEEDING_EVENTS}/{key}"
        # Delete edges
        self.delete_edges(col.FEEDING_USED, event_id)
        for edge_col in [col.FED_BY]:
            query = f"FOR e IN {edge_col} FILTER e._to == @eid REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"eid": event_id})
        return BaseArangoRepository.delete(self, key)

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> list[FeedingEvent]:
        query = """
        FOR doc IN @@collection
          FILTER doc.plant_key == @plant_key
          SORT doc.timestamp DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.FEEDING_EVENTS,
            "plant_key": plant_key,
            "offset": offset,
            "limit": limit,
        })
        return [FeedingEvent(**self._from_doc(doc)) for doc in cursor]

    def get_latest_by_plant(self, plant_key: str) -> FeedingEvent | None:
        events = self.get_by_plant(plant_key, offset=0, limit=1)
        return events[0] if events else None

    def get_recent_runoff_events(self, plant_key: str, limit: int = 5) -> list[FeedingEvent]:
        query = """
        FOR doc IN @@collection
          FILTER doc.plant_key == @plant_key
            AND doc.runoff_ec != null
          SORT doc.timestamp DESC
          LIMIT @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.FEEDING_EVENTS,
            "plant_key": plant_key,
            "limit": limit,
        })
        return [FeedingEvent(**self._from_doc(doc)) for doc in cursor]
