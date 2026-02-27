from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.types import (
    LocationKey,
    MaintenanceScheduleKey,
    TankKey,
)
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tank_repository import ITankRepository
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState


class ArangoTankRepository(ITankRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.TANKS)

    # ── Tank CRUD ──────────────────────────────────────────────────────

    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[Tank], int]:
        if filters:
            query = f"FOR doc IN {col.TANKS}"
            bind_vars: dict[str, Any] = {}
            filter_clauses = []
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")
            query += " FILTER " + " AND ".join(filter_clauses)
            count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
            query += f" SORT doc._key LIMIT {offset}, {limit} RETURN doc"
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            items = [Tank(**self._from_doc(doc)) for doc in cursor]
            count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
            total = next(count_cursor, 0)
            return items, total
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [Tank(**doc) for doc in docs], total

    def get_by_key(self, key: TankKey) -> Tank | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Tank(**doc) if doc else None

    def create(self, tank: Tank) -> Tank:
        doc = BaseArangoRepository.create(self, tank)
        created = Tank(**doc)
        if tank.location_key:
            self.link_to_location(doc["_key"], tank.location_key)
        return created

    def update(self, key: TankKey, tank: Tank) -> Tank:
        doc = BaseArangoRepository.update(self, key, tank)
        return Tank(**doc)

    def delete(self, key: TankKey) -> bool:
        tank_id = f"{col.TANKS}/{key}"
        # Delete outbound edges
        self.delete_edges(col.SUPPLIES, tank_id)
        self.delete_edges(col.FEEDS_FROM, tank_id)
        self.delete_edges(col.HAS_STATE, tank_id)
        self.delete_edges(col.HAS_MAINTENANCE, tank_id)
        self.delete_edges(col.HAS_SCHEDULE, tank_id)
        # Delete inbound edges (has_tank, feeds_from targeting this tank)
        for edge_col in [col.HAS_TANK, col.FEEDS_FROM]:
            query = f"FOR e IN {edge_col} FILTER e._to == @tank_id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"tank_id": tank_id})
        # Delete child documents
        for child_col in [col.TANK_STATES, col.MAINTENANCE_LOGS, col.MAINTENANCE_SCHEDULES]:
            query = f"FOR doc IN {child_col} FILTER doc.tank_key == @key REMOVE doc IN {child_col}"
            self._db.aql.execute(query, bind_vars={"key": key})
        return BaseArangoRepository.delete(self, key)

    # ── Edge operations ────────────────────────────────────────────────

    def link_to_location(self, tank_key: TankKey, location_key: LocationKey) -> None:
        from_id = f"{col.LOCATIONS}/{location_key}"
        to_id = f"{col.TANKS}/{tank_key}"
        self.create_edge(col.HAS_TANK, from_id, to_id)

    def link_supply(self, tank_key: TankKey, location_key: LocationKey) -> None:
        from_id = f"{col.TANKS}/{tank_key}"
        to_id = f"{col.LOCATIONS}/{location_key}"
        self.create_edge(col.SUPPLIES, from_id, to_id)

    def link_feeds_from(self, tank_key: TankKey, source_tank_key: TankKey) -> None:
        from_id = f"{col.TANKS}/{tank_key}"
        to_id = f"{col.TANKS}/{source_tank_key}"
        self.create_edge(col.FEEDS_FROM, from_id, to_id)

    # ── State CRUD ─────────────────────────────────────────────────────

    def create_state(self, state: TankState) -> TankState:
        data = state.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        if "recorded_at" not in data or data["recorded_at"] is None:
            data["recorded_at"] = now
        result = self._db.collection(col.TANK_STATES).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = TankState(**doc)
        # Create edge
        if state.tank_key:
            from_id = f"{col.TANKS}/{state.tank_key}"
            to_id = f"{col.TANK_STATES}/{doc['_key']}"
            self.create_edge(col.HAS_STATE, from_id, to_id)
        return created

    def get_states(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[TankState]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          SORT doc.recorded_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.TANK_STATES,
            "tank_key": tank_key,
            "offset": offset,
            "limit": limit,
        })
        return [TankState(**self._from_doc(doc)) for doc in cursor]

    def get_latest_state(self, tank_key: TankKey) -> TankState | None:
        states = self.get_states(tank_key, offset=0, limit=1)
        return states[0] if states else None

    # ── MaintenanceLog CRUD ────────────────────────────────────────────

    def create_maintenance_log(self, log: MaintenanceLog) -> MaintenanceLog:
        data = log.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        if "performed_at" not in data or data["performed_at"] is None:
            data["performed_at"] = now
        result = self._db.collection(col.MAINTENANCE_LOGS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = MaintenanceLog(**doc)
        if log.tank_key:
            from_id = f"{col.TANKS}/{log.tank_key}"
            to_id = f"{col.MAINTENANCE_LOGS}/{doc['_key']}"
            self.create_edge(col.HAS_MAINTENANCE, from_id, to_id)
        return created

    def get_maintenance_logs(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[MaintenanceLog]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          SORT doc.performed_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.MAINTENANCE_LOGS,
            "tank_key": tank_key,
            "offset": offset,
            "limit": limit,
        })
        return [MaintenanceLog(**self._from_doc(doc)) for doc in cursor]

    def get_last_maintenance_by_type(
        self, tank_key: TankKey, maintenance_type: str,
    ) -> MaintenanceLog | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key AND doc.maintenance_type == @mtype
          SORT doc.performed_at DESC
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.MAINTENANCE_LOGS,
            "tank_key": tank_key,
            "mtype": maintenance_type,
        })
        docs = list(cursor)
        if not docs:
            return None
        return MaintenanceLog(**self._from_doc(docs[0]))

    # ── Schedule CRUD ──────────────────────────────────────────────────

    def create_schedule(self, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        data = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        result = self._db.collection(col.MAINTENANCE_SCHEDULES).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = MaintenanceSchedule(**doc)
        if schedule.tank_key:
            from_id = f"{col.TANKS}/{schedule.tank_key}"
            to_id = f"{col.MAINTENANCE_SCHEDULES}/{doc['_key']}"
            self.create_edge(col.HAS_SCHEDULE, from_id, to_id)
        return created

    def get_schedules(self, tank_key: TankKey) -> list[MaintenanceSchedule]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.MAINTENANCE_SCHEDULES,
            "tank_key": tank_key,
        })
        return [MaintenanceSchedule(**self._from_doc(doc)) for doc in cursor]

    def get_schedule_by_key(self, key: MaintenanceScheduleKey) -> MaintenanceSchedule | None:
        doc = self._db.collection(col.MAINTENANCE_SCHEDULES).get(key)
        if doc is None:
            return None
        return MaintenanceSchedule(**self._from_doc(doc))

    def update_schedule(
        self, key: MaintenanceScheduleKey, schedule: MaintenanceSchedule,
    ) -> MaintenanceSchedule:
        data = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.MAINTENANCE_SCHEDULES).update(
            {"_key": key, **data}, return_new=True,
        )
        return MaintenanceSchedule(**self._from_doc(result["new"]))

    def delete_schedule(self, key: MaintenanceScheduleKey) -> bool:
        schedule_id = f"{col.MAINTENANCE_SCHEDULES}/{key}"
        query = f"FOR e IN {col.HAS_SCHEDULE} FILTER e._to == @sid REMOVE e IN {col.HAS_SCHEDULE}"
        self._db.aql.execute(query, bind_vars={"sid": schedule_id})
        try:
            self._db.collection(col.MAINTENANCE_SCHEDULES).delete(key)
            return True
        except Exception:
            return False

    # ── Queries ────────────────────────────────────────────────────────

    def get_tanks_for_location(self, location_key: LocationKey) -> list[Tank]:
        query = """
        FOR doc IN @@collection
          FILTER doc.location_key == @location_key
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.TANKS,
            "location_key": location_key,
        })
        return [Tank(**self._from_doc(doc)) for doc in cursor]
