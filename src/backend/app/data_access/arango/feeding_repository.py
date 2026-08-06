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

    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[FeedingEvent]:
        """One plant's feeding events **inside one tenant**, newest first (#927).

        ``tenant_key`` is keyword-only and has no default. The selection is a
        bare ``plant_key == @plant_key`` scan over a tenant-scoped collection, and
        ``plant_key`` comes from the URL of
        ``GET /t/{slug}/feeding-events/plant/{pk}``. Without the second predicate
        a member of tenant A read tenant B's fertigation record — EC/pH before
        and after, runoff, volumes, notes.

        The filter lives here rather than in the endpoint so that the isolation
        is a property of the data-access layer: the parameter cannot be omitted,
        and :meth:`BaseArangoRepository._require_tenant_key` rejects the empty
        sentinel that would otherwise re-open the scan.
        """
        self._require_tenant_key(tenant_key, "get_by_plant")
        return self.find_by_field(
            "plant_key",
            plant_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def get_latest_by_plant(self, plant_key: str, *, tenant_key: str) -> FeedingEvent | None:
        """Newest feeding event of a plant inside ``tenant_key`` (#927)."""
        events = self.get_by_plant(plant_key, offset=0, limit=1, tenant_key=tenant_key)
        return events[0] if events else None

    def get_recent_runoff_events(self, plant_key: str, limit: int = 5, *, tenant_key: str) -> list[FeedingEvent]:
        """Last ``limit`` runoff-carrying feeding events of a plant, tenant-scoped (#927).

        Same unfiltered ``plant_key`` scan as :meth:`get_by_plant`. Its only
        caller is a Celery sweep, which now reads the owning tenant off the plant
        document and passes it in rather than querying across every tenant.
        """
        self._require_tenant_key(tenant_key, "get_recent_runoff_events")
        return self.find_by_field(
            "plant_key",
            plant_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=0,
            limit=limit,
            extra_filters=[
                ("tenant_key", "==", tenant_key),
                ("runoff_ec", "!=", None),
            ],
        )
