from datetime import UTC, date, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.types import LocationKey, PlantInstanceKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.watering_repository import IWateringRepository
from app.domain.models.watering_event import WateringEvent

#: The watering events of the plants that stand in one of the location's slots **now** (#2952). A plant is
#: selected by its own ``slot_key``, never through ``placed_in``: that edge stays on every slot a plant ever stood
#: in (#2948), so a moved plant's events appeared under the old *and* the new bed, and a plant moved before #2948
#: has no edge to the slot it stands in. A watering event records no slot, so where the plant stood at the time is
#: not known; it is attributed to where the plant stands. ``COLLECT`` keeps one row per event when it watered two
#: plants of the bed. The tenant predicate sits on the plant (the anchor that carries the tenant, #706) and on the
#: event.
_EVENTS_AT_LOCATION = """
    LET slot_keys = (
      FOR slot_edge IN @@has_slot
        FILTER slot_edge._from == @location_id
        RETURN PARSE_IDENTIFIER(slot_edge._to).key
    )
    LET events = (
      FOR plant IN @@plants
        FILTER plant.slot_key IN slot_keys
        FILTER plant.tenant_key == @tenant_key
        FOR water_edge IN @@watered_plant
          FILTER water_edge._to == plant._id
          COLLECT event_id = water_edge._from
          LET doc = DOCUMENT(event_id)
          FILTER doc != null AND doc.tenant_key == @tenant_key
          RETURN doc
    )
"""


class ArangoWateringRepository(BaseArangoRepository[WateringEvent], IWateringRepository):
    is_tenant_scoped = True
    _model_cls = WateringEvent
    #: ``POST /t/{slug}/watering-events`` takes ``plant_keys`` from the request
    #: body and the create path wires a ``watered_plant`` edge per key, so every
    #: reference is ownership-verified before the write (#948). ``create`` below
    #: is hand-written rather than delegating to the base, so it invokes the
    #: check explicitly — the one place this declaration is not automatic.
    _owned_reference_fields = {"plant_keys": col.PLANT_INSTANCES}

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.WATERING_EVENTS)

    # ── Create & Read ──────────────────────────────────────────────────

    def create(self, event: WateringEvent) -> WateringEvent:
        # This create does not go through ``BaseArangoRepository.create``, so the
        # declared foreign-reference check has to be invoked by hand (#948).
        self._verify_owned_references(event)
        # NOTE: unlike the base ``create`` this intentionally sets only
        # ``created_at`` (no ``updated_at``) for a watering event; keep custom.
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

    # ── Queries ────────────────────────────────────────────────────────

    def get_by_plant(
        self,
        plant_key: PlantInstanceKey,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringEvent]:
        """One plant's watering events **inside one tenant**, newest first (#927).

        ``tenant_key`` is keyword-only and has no default on purpose. The read
        enters the graph through an edge — ``watered_plant`` inbound from
        ``plant_instances/{plant_key}`` — and that entry point is a key straight
        from the URL. Until #927 the query carried no tenant predicate at all, so
        a member of tenant A who put a foreign ``plant_key`` into
        ``GET /t/{slug}/plant-instances/{plant_key}/watering-events`` read the
        other tenant's watering history: volumes, EC/pH measurements, timestamps.

        The filter belongs here rather than in the endpoint. A caller-side check
        is one line the next endpoint forgets; with the parameter required and
        the empty sentinel rejected, a read that does not name a tenant cannot be
        written at all and the isolation becomes a property of the storage layer.

        ``doc != null`` guards a dangling edge: ``DOCUMENT()`` answers ``null``
        for a deleted target. The tenant predicate already excludes it, but
        naming it keeps the intent readable.
        """
        self._require_tenant_key(tenant_key, "get_by_plant")
        query = """
        FOR e IN @@edge_col
          FILTER e._to == @plant_id
          LET doc = DOCUMENT(e._from)
          FILTER doc != null AND doc.tenant_key == @tenant_key
          SORT DATE_TIMESTAMP(doc.watered_at) DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@edge_col": col.WATERED_PLANT,
                "plant_id": plant_id,
                "tenant_key": tenant_key,
                "offset": offset,
                "limit": limit,
            },
        )
        return [WateringEvent(**self._from_doc(doc)) for doc in cursor]

    def _location_bind_vars(self, location_key: LocationKey, tenant_key: str) -> dict[str, Any]:
        return {
            "@has_slot": col.HAS_SLOT,
            "@plants": col.PLANT_INSTANCES,
            "@watered_plant": col.WATERED_PLANT,
            "location_id": f"{col.LOCATIONS}/{location_key}",
            "tenant_key": tenant_key,
        }

    def get_by_location(
        self,
        location_key: LocationKey,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringEvent]:
        """A location's watering events **inside one tenant** (#927), newest first.

        The anchor is the caller-supplied ``location_key``, which names no tenant, so the plant and the event are
        filtered on it. An event belongs to the location its plant stands in **now** (``plant.slot_key``, #2952):
        each event is listed under one bed per plant it watered, whatever the plant's moves.
        """
        self._require_tenant_key(tenant_key, "get_by_location")
        query = (
            _EVENTS_AT_LOCATION
            + """
        FOR doc IN events
          SORT DATE_TIMESTAMP(doc.watered_at) DESC, doc._key DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        )
        bind_vars = self._location_bind_vars(location_key, tenant_key)
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [WateringEvent(**self._from_doc(doc)) for doc in cursor]

    def get_stats_by_location(self, location_key: LocationKey, *, tenant_key: str) -> dict:
        """Aggregated watering statistics for a location, **inside one tenant** (#927).

        The aggregate needs the filter at least as badly as the list does: the
        answer is nothing *but* counts and sums, so an unfiltered query hands a
        caller the number of foreign events and the total volume applied to
        another tenant's plants. The same event set as :meth:`get_by_location`
        (where the plants stand now, #2952), so list and counts agree.
        """
        self._require_tenant_key(tenant_key, "get_stats_by_location")
        query = (
            _EVENTS_AT_LOCATION
            + """
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
        )
        cursor = self._db.aql.execute(query, bind_vars=self._location_bind_vars(location_key, tenant_key))
        result = next(cursor, None)
        return result or {"total_events": 0, "total_volume": 0.0, "by_method": []}

    def get_last_watering_date_for_run(self, run_key: str, *, tenant_key: str) -> date | None:
        """Newest watering date for a run's active plants, **inside one tenant** (#927).

        Not one of the five demonstrated leaks — every current caller resolves the
        run against the tenant first — but structurally identical: the query
        selects ``watering_events`` by an intersection of plant keys and never
        named a tenant. Closing it here means the next caller cannot reintroduce
        the leak by forgetting the anchor check.
        """
        self._require_tenant_key(tenant_key, "get_last_watering_date_for_run")
        query = """
        LET plant_keys = (
          FOR rc IN @@run_contains
            FILTER rc._from == @run_id
            FILTER rc.detached_at == null
            RETURN PARSE_IDENTIFIER(rc._to).key
        )
        FOR we IN @@watering_events
          FILTER we.tenant_key == @tenant_key
          FILTER LENGTH(INTERSECTION(we.plant_keys, plant_keys)) > 0
          SORT DATE_TIMESTAMP(we.watered_at) DESC
          LIMIT 1
          RETURN we.watered_at
        """
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        bind_vars: dict[str, Any] = {
            "@run_contains": col.RUN_CONTAINS,
            "@watering_events": col.WATERING_EVENTS,
            "run_id": run_id,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        result = next(cursor, None)
        if result is None:
            return None
        if isinstance(result, str):
            return datetime.fromisoformat(result).date()
        if isinstance(result, datetime):
            return result.date()
        return None
