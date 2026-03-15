from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tank_repository import ITankRepository
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankFillEvent, TankState

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import (
        LocationKey,
        MaintenanceScheduleKey,
        TankKey,
    )


class ArangoTankRepository(ITankRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.TANKS)

    # ── Tank CRUD ──────────────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
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
        # Delete fill event edges
        self.delete_edges(col.HAS_FILL_EVENT, tank_id)
        # Delete child documents
        for child_col in [col.TANK_STATES, col.MAINTENANCE_LOGS, col.MAINTENANCE_SCHEDULES, col.TANK_FILL_EVENTS]:
            query = f"FOR doc IN {child_col} FILTER doc.tank_key == @key REMOVE doc IN {child_col}"
            self._db.aql.execute(query, bind_vars={"key": key})
        return BaseArangoRepository.delete(self, key)

    # ── Edge operations ────────────────────────────────────────────────

    def link_to_location(self, tank_key: TankKey, location_key: LocationKey) -> None:
        from_id = f"{col.LOCATIONS}/{location_key}"
        to_id = f"{col.TANKS}/{tank_key}"
        self.create_edge(col.HAS_TANK, from_id, to_id)

    def update_location(
        self,
        tank_key: TankKey,
        old_location_key: LocationKey | None,
        new_location_key: LocationKey | None,
    ) -> None:
        tank_id = f"{col.TANKS}/{tank_key}"
        # Remove old edge
        if old_location_key:
            query = f"FOR e IN {col.HAS_TANK} FILTER e._to == @tank_id REMOVE e IN {col.HAS_TANK}"
            self._db.aql.execute(query, bind_vars={"tank_id": tank_id})
        # Create new edge
        if new_location_key:
            self.link_to_location(tank_key, new_location_key)

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
        self,
        tank_key: TankKey,
        offset: int = 0,
        limit: int = 50,
    ) -> list[TankState]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          SORT doc.recorded_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TANK_STATES,
                "tank_key": tank_key,
                "offset": offset,
                "limit": limit,
            },
        )
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
        self,
        tank_key: TankKey,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MaintenanceLog]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          SORT doc.performed_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MAINTENANCE_LOGS,
                "tank_key": tank_key,
                "offset": offset,
                "limit": limit,
            },
        )
        return [MaintenanceLog(**self._from_doc(doc)) for doc in cursor]

    def get_last_maintenance_by_type(
        self,
        tank_key: TankKey,
        maintenance_type: str,
    ) -> MaintenanceLog | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key AND doc.maintenance_type == @mtype
          SORT doc.performed_at DESC
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MAINTENANCE_LOGS,
                "tank_key": tank_key,
                "mtype": maintenance_type,
            },
        )
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
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MAINTENANCE_SCHEDULES,
                "tank_key": tank_key,
            },
        )
        return [MaintenanceSchedule(**self._from_doc(doc)) for doc in cursor]

    def get_schedule_by_key(self, key: MaintenanceScheduleKey) -> MaintenanceSchedule | None:
        doc = self._db.collection(col.MAINTENANCE_SCHEDULES).get(key)
        if doc is None:
            return None
        return MaintenanceSchedule(**self._from_doc(doc))

    def update_schedule(
        self,
        key: MaintenanceScheduleKey,
        schedule: MaintenanceSchedule,
    ) -> MaintenanceSchedule:
        data = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.MAINTENANCE_SCHEDULES).update(
            {"_key": key, **data},
            return_new=True,
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

    # ── Fill Events ──────────────────────────────────────────────────────

    def create_fill_event(self, event: TankFillEvent) -> TankFillEvent:
        data = event.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        if "filled_at" not in data or data["filled_at"] is None:
            data["filled_at"] = now
        result = self._db.collection(col.TANK_FILL_EVENTS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = TankFillEvent(**doc)
        # Create has_fill_event edge
        if event.tank_key:
            from_id = f"{col.TANKS}/{event.tank_key}"
            to_id = f"{col.TANK_FILL_EVENTS}/{doc['_key']}"
            self.create_edge(col.HAS_FILL_EVENT, from_id, to_id)
        # Create mixed_into edge if mixing_result_key provided
        if event.mixing_result_key:
            from_id = f"{col.NUTRIENT_PLANS}/{event.mixing_result_key}"
            to_id = f"{col.TANK_FILL_EVENTS}/{doc['_key']}"
            self.create_edge(col.MIXED_INTO, from_id, to_id)
        return created

    def get_fill_events(
        self,
        tank_key: TankKey,
        offset: int = 0,
        limit: int = 50,
    ) -> list[TankFillEvent]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key
          SORT doc.filled_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TANK_FILL_EVENTS,
                "tank_key": tank_key,
                "offset": offset,
                "limit": limit,
            },
        )
        return [TankFillEvent(**self._from_doc(doc)) for doc in cursor]

    def get_latest_fill_event(self, tank_key: TankKey) -> TankFillEvent | None:
        events = self.get_fill_events(tank_key, offset=0, limit=1)
        return events[0] if events else None

    def get_latest_full_change(self, tank_key: TankKey) -> TankFillEvent | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.tank_key == @tank_key AND doc.fill_type == "full_change"
          SORT doc.filled_at DESC
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TANK_FILL_EVENTS,
                "tank_key": tank_key,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return TankFillEvent(**self._from_doc(docs[0]))

    def get_fill_event_stats(
        self,
        tank_key: TankKey,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        filters = ["doc.tank_key == @tank_key"]
        bind_vars: dict[str, Any] = {
            "@collection": col.TANK_FILL_EVENTS,
            "tank_key": tank_key,
        }
        if start_date:
            filters.append("doc.filled_at >= @start_date")
            bind_vars["start_date"] = start_date
        if end_date:
            filters.append("doc.filled_at <= @end_date")
            bind_vars["end_date"] = end_date
        filter_clause = " AND ".join(filters)
        query = f"""
        FOR doc IN @@collection
          FILTER {filter_clause}
          COLLECT fill_type = doc.fill_type WITH COUNT INTO count
          RETURN {{fill_type, count}}
        """
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        type_counts = {row["fill_type"]: row["count"] for row in cursor}
        # Total volume
        vol_query = f"""
        FOR doc IN @@collection
          FILTER {filter_clause}
          COLLECT AGGREGATE total_vol = SUM(doc.volume_liters), total_count = LENGTH(doc)
          RETURN {{total_volume: total_vol, total_count: total_count}}
        """
        vol_cursor = self._db.aql.execute(vol_query, bind_vars=bind_vars)
        vol_result = next(vol_cursor, {"total_volume": 0, "total_count": 0})
        # Avg EC deviation
        ec_query = f"""
        FOR doc IN @@collection
          FILTER {filter_clause} AND doc.target_ec_ms != null AND doc.measured_ec_ms != null
          COLLECT AGGREGATE avg_dev = AVG(ABS(doc.measured_ec_ms - doc.target_ec_ms))
          RETURN avg_dev
        """
        ec_cursor = self._db.aql.execute(ec_query, bind_vars=bind_vars)
        avg_ec_deviation = next(ec_cursor, None)
        return {
            "fill_type_counts": type_counts,
            "total_volume_liters": vol_result["total_volume"] or 0,
            "total_count": vol_result["total_count"] or 0,
            "avg_ec_deviation_ms": round(avg_ec_deviation, 3) if avg_ec_deviation else None,
        }

    # ── Queries ────────────────────────────────────────────────────────

    def get_active_auto_create_schedules(self) -> list[MaintenanceSchedule]:
        query = """
        FOR doc IN @@collection
          FILTER doc.auto_create_task == true AND doc.is_active == true
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MAINTENANCE_SCHEDULES,
            },
        )
        return [MaintenanceSchedule(**self._from_doc(doc)) for doc in cursor]

    def get_tanks_for_location(self, location_key: LocationKey) -> list[Tank]:
        query = """
        FOR doc IN @@collection
          FILTER doc.location_key == @location_key
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TANKS,
                "location_key": location_key,
            },
        )
        return [Tank(**self._from_doc(doc)) for doc in cursor]

    def get_active_nutrient_plans(self, tank_key: TankKey) -> list[dict]:
        query = """
        LET tank = DOCUMENT(CONCAT(@tanks, '/', @tank_key))
        FILTER tank != null AND tank.location_key != null

        FOR run IN @@planting_runs
          FILTER run.location_key == tank.location_key
            AND run.status IN ['active', 'harvesting']
            AND run.nutrient_plan_key != null

          LET plan = DOCUMENT(CONCAT(@nutrient_plans, '/', run.nutrient_plan_key))
          FILTER plan != null

          LET plants = (
            FOR entry IN @@planting_run_entries
              FILTER entry.run_key == run._key AND entry.detached_at == null
              LET plant = DOCUMENT(CONCAT(@plant_instances, '/', entry.plant_key))
              FILTER plant != null
              LET gp = DOCUMENT(CONCAT('growth_phases/', plant.current_phase_key))
              RETURN gp != null ? gp.name : ''
          )
          LET dominant_phase = FIRST(
            FOR phase IN plants
              COLLECT p = phase WITH COUNT INTO cnt
              SORT cnt DESC
              RETURN p
          )

          LET phase_entries = (
            FOR pe IN @@phase_entries
              FILTER pe.plan_key == plan._key
              SORT pe.sequence_order ASC
              RETURN pe
          )
          LET current_entry = FIRST(
            FOR pe IN phase_entries
              FILTER pe.phase_name == dominant_phase
              RETURN pe
          )

          LET fertilizer_keys = (
            FOR pe IN (current_entry != null ? [current_entry] : [])
              FOR ch IN (pe.delivery_channels || [])
                FOR dos IN (ch.fertilizer_dosages || [])
                  RETURN DISTINCT dos.fertilizer_key
          )
          LET fertilizers = (
            FOR fk IN fertilizer_keys
              LET f = DOCUMENT(CONCAT(@fertilizers, '/', fk))
              FILTER f != null
              RETURN {
                key: f._key,
                product_name: f.product_name,
                brand: f.brand,
                fertilizer_type: f.fertilizer_type,
                npk_ratio: f.npk_ratio,
                ec_contribution_per_ml: f.ec_contribution_per_ml,
                mixing_priority: f.mixing_priority
              }
          )

          RETURN {
            run_key: run._key,
            run_name: run.name,
            run_status: run.status,
            plan_key: plan._key,
            plan_name: plan.name,
            current_phase: dominant_phase,
            plant_count: LENGTH(plants),
            current_phase_entry: current_entry,
            all_phase_entries: phase_entries,
            fertilizers: fertilizers,
            watering_schedule: plan.watering_schedule,
            water_mix_ratio_ro_percent: plan.water_mix_ratio_ro_percent
          }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "tank_key": tank_key,
                "tanks": col.TANKS,
                "nutrient_plans": col.NUTRIENT_PLANS,
                "plant_instances": col.PLANT_INSTANCES,
                "fertilizers": col.FERTILIZERS,
                "@planting_runs": col.PLANTING_RUNS,
                "@planting_run_entries": col.PLANTING_RUN_ENTRIES,
                "@phase_entries": col.NUTRIENT_PLAN_PHASE_ENTRIES,
            },
        )
        return list(cursor)
