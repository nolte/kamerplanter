from arango.database import StandardDatabase

from app.common.types import FeedingEventKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.feeding_repository import IFeedingRepository
from app.domain.models.feeding_event import FeedingEvent


class ArangoFeedingRepository(BaseArangoRepository[FeedingEvent], IFeedingRepository):
    is_tenant_scoped = True
    _model_cls = FeedingEvent

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.FEEDING_EVENTS)

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(self, event: FeedingEvent) -> FeedingEvent:
        created = super().create(event, default_now_fields=("timestamp",))

        # Create FED_BY edge (PlantInstance → FeedingEvent)
        plant_id = f"{col.PLANT_INSTANCES}/{event.plant_key}"
        event_id = f"{col.FEEDING_EVENTS}/{created.key}"
        self.create_edge(col.FED_BY, plant_id, event_id)

        # Create FEEDING_USED edges (FeedingEvent → Fertilizer)
        for fert_used in event.fertilizers_used:
            fert_id = f"{col.FERTILIZERS}/{fert_used.fertilizer_key}"
            self.create_edge(
                col.FEEDING_USED,
                event_id,
                fert_id,
                {"ml_applied": fert_used.ml_applied},
            )

        return created

    def delete(self, key: FeedingEventKey) -> bool:
        event_id = f"{col.FEEDING_EVENTS}/{key}"
        # Delete edges
        self.delete_edges(col.FEEDING_USED, event_id)
        self.delete_edges(col.FED_BY, event_id, direction="inbound")
        return super().delete(key)

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> list[FeedingEvent]:
        return self.find_by_field(
            "plant_key",
            plant_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
        )

    def get_latest_by_plant(self, plant_key: str) -> FeedingEvent | None:
        events = self.get_by_plant(plant_key, offset=0, limit=1)
        return events[0] if events else None

    def get_recent_runoff_events(self, plant_key: str, limit: int = 5) -> list[FeedingEvent]:
        return self.find_by_field(
            "plant_key",
            plant_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=0,
            limit=limit,
            extra_filters=[("runoff_ec", "!=", None)],
        )
