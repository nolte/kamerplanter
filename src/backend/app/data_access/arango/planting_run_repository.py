from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import LocationKey, PlantID, PlantingRunEntryKey, PlantingRunKey


class ArangoPlantingRunRepository(IPlantingRunRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PLANTING_RUNS)

    # ── Run CRUD ──────────────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[PlantingRun], int]:
        if filters:
            query = f"FOR doc IN {col.PLANTING_RUNS}"
            bind_vars: dict[str, Any] = {}
            filter_clauses = []
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")
            query += " FILTER " + " AND ".join(filter_clauses)
            count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
            query += f" SORT doc._key LIMIT {offset}, {limit} RETURN doc"
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            items = [PlantingRun(**self._from_doc(doc)) for doc in cursor]
            count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
            total = next(count_cursor, 0)
            return items, total
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [PlantingRun(**doc) for doc in docs], total

    def get_by_key(self, key: PlantingRunKey) -> PlantingRun | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return PlantingRun(**doc) if doc else None

    def create(self, run: PlantingRun) -> PlantingRun:
        doc = BaseArangoRepository.create(self, run)
        created = PlantingRun(**doc)
        if run.location_key:
            self.link_run_to_location(doc["_key"], run.location_key)
        if run.substrate_batch_key:
            self.link_run_to_substrate(doc["_key"], run.substrate_batch_key)
        return created

    def update(self, key: PlantingRunKey, run: PlantingRun) -> PlantingRun:
        doc = BaseArangoRepository.update(self, key, run)
        return PlantingRun(**doc)

    def delete(self, key: PlantingRunKey) -> bool:
        run_id = f"{col.PLANTING_RUNS}/{key}"
        self.delete_edges(col.RUN_CONTAINS, from_id=run_id)
        self.delete_edges(col.RUN_AT_LOCATION, from_id=run_id)
        self.delete_edges(col.RUN_USES_SUBSTRATE, from_id=run_id)
        self.delete_edges(col.HAS_ENTRY, from_id=run_id)
        # Delete entries and their edges
        entries = self.get_entries(key)
        for entry in entries:
            if entry.key:
                entry_id = f"{col.PLANTING_RUN_ENTRIES}/{entry.key}"
                self.delete_edges(col.ENTRY_FOR_SPECIES, from_id=entry_id)
                self._db.collection(col.PLANTING_RUN_ENTRIES).delete(entry.key)
        return BaseArangoRepository.delete(self, key)

    # ── Entry CRUD ────────────────────────────────────────────────────

    def create_entry(self, entry: PlantingRunEntry) -> PlantingRunEntry:
        data = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        result = self._db.collection(col.PLANTING_RUN_ENTRIES).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = PlantingRunEntry(**doc)
        # Create edges
        if entry.run_key:
            self.link_run_to_entry(entry.run_key, doc["_key"])
        self.link_entry_to_species(doc["_key"], entry.species_key)
        return created

    def get_entries(self, run_key: PlantingRunKey) -> list[PlantingRunEntry]:
        query = """
        FOR doc IN @@collection
          FILTER doc.run_key == @run_key
          RETURN doc
        """
        bind_vars = {
            "@collection": col.PLANTING_RUN_ENTRIES,
            "run_key": run_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantingRunEntry(**self._from_doc(doc)) for doc in cursor]

    def get_entry_by_key(self, entry_key: PlantingRunEntryKey) -> PlantingRunEntry | None:
        doc = self._db.collection(col.PLANTING_RUN_ENTRIES).get(entry_key)
        if doc is None:
            return None
        return PlantingRunEntry(**self._from_doc(doc))

    def update_entry(self, entry_key: PlantingRunEntryKey, entry: PlantingRunEntry) -> PlantingRunEntry:
        data = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.PLANTING_RUN_ENTRIES).update(
            {"_key": entry_key, **data},
            return_new=True,
        )
        return PlantingRunEntry(**self._from_doc(result["new"]))

    def delete_entry(self, entry_key: PlantingRunEntryKey) -> bool:
        entry_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
        self.delete_edges(col.ENTRY_FOR_SPECIES, from_id=entry_id)
        # Remove has_entry edges pointing to this entry
        query = f"FOR e IN {col.HAS_ENTRY} FILTER e._to == @entry_id REMOVE e IN {col.HAS_ENTRY}"
        self._db.aql.execute(query, bind_vars={"entry_id": entry_id})
        try:
            self._db.collection(col.PLANTING_RUN_ENTRIES).delete(entry_key)
            return True
        except Exception:
            return False

    # ── Edge operations ───────────────────────────────────────────────

    def link_run_to_location(self, run_key: PlantingRunKey, location_key: str) -> None:
        from_id = f"{col.PLANTING_RUNS}/{run_key}"
        to_id = f"{col.LOCATIONS}/{location_key}"
        self.create_edge(col.RUN_AT_LOCATION, from_id, to_id)

    def link_run_to_substrate(self, run_key: PlantingRunKey, batch_key: str) -> None:
        from_id = f"{col.PLANTING_RUNS}/{run_key}"
        to_id = f"{col.SUBSTRATE_BATCHES}/{batch_key}"
        self.create_edge(col.RUN_USES_SUBSTRATE, from_id, to_id)

    def link_run_to_plant(self, run_key: PlantingRunKey, plant_key: PlantID) -> None:
        from_id = f"{col.PLANTING_RUNS}/{run_key}"
        to_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        self.create_edge(col.RUN_CONTAINS, from_id, to_id)

    def link_run_to_entry(self, run_key: PlantingRunKey, entry_key: PlantingRunEntryKey) -> None:
        from_id = f"{col.PLANTING_RUNS}/{run_key}"
        to_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
        self.create_edge(col.HAS_ENTRY, from_id, to_id)

    def link_entry_to_species(self, entry_key: PlantingRunEntryKey, species_key: str) -> None:
        from_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
        to_id = f"{col.SPECIES}/{species_key}"
        self.create_edge(col.ENTRY_FOR_SPECIES, from_id, to_id)

    # ── Queries ───────────────────────────────────────────────────────

    def get_run_plants(self, run_key: PlantingRunKey, include_detached: bool = False) -> list[dict]:
        query = f"""
        FOR e IN {col.RUN_CONTAINS}
          FILTER e._from == @run_id
        """
        if not include_detached:
            query += "  FILTER e.detached_at == null\n"
        query += f"""  LET v = DOCUMENT(e._to)
          LET gp = DOCUMENT(CONCAT('{col.GROWTH_PHASES}/', v.current_phase_key))
          RETURN MERGE(v, {{
            _edge_detached_at: e.detached_at,
            _edge_detach_reason: e.detach_reason,
            current_phase: gp != null ? gp.name : ''
          }})"""
        bind_vars = {
            "run_id": f"{col.PLANTING_RUNS}/{run_key}",
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._from_doc(doc) for doc in cursor]

    def detach_plant(self, run_key: PlantingRunKey, plant_key: PlantID, reason: str) -> None:
        now = datetime.now(UTC).isoformat()
        query = f"""
        FOR e IN {col.RUN_CONTAINS}
          FILTER e._from == @from_id AND e._to == @to_id
          UPDATE e WITH {{detached_at: @now, detach_reason: @reason}} IN {col.RUN_CONTAINS}
        """
        self._db.aql.execute(
            query,
            bind_vars={
                "from_id": f"{col.PLANTING_RUNS}/{run_key}",
                "to_id": f"{col.PLANT_INSTANCES}/{plant_key}",
                "now": now,
                "reason": reason,
            },
        )

    def get_existing_ids_at_location(self, location_key: LocationKey) -> set[str]:
        query = """
        FOR slot IN 1..1 OUTBOUND @loc_id GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@slot_edge]}
          FOR plant IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
            OPTIONS {edgeCollections: [@plant_edge]}
            RETURN plant.instance_id
        """
        bind_vars = {
            "loc_id": f"{col.LOCATIONS}/{location_key}",
            "slot_edge": col.HAS_SLOT,
            "plant_edge": col.PLACED_IN,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return {doc for doc in cursor if doc}

    def get_runs_for_plant(self, plant_key: PlantID) -> list[PlantingRun]:
        query = f"""
        FOR e IN {col.RUN_CONTAINS}
          FILTER e._to == @plant_id
          LET run = DOCUMENT(e._from)
          FILTER run != null
          SORT run.started_at DESC
          RETURN run
        """
        bind_vars = {"plant_id": f"{col.PLANT_INSTANCES}/{plant_key}"}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantingRun(**self._from_doc(doc)) for doc in cursor]

    def get_runs_at_site(self, site_key: str) -> list[PlantingRun]:
        query = f"""
        FOR run IN {col.PLANTING_RUNS}
          FILTER run.location_key != null
          FILTER run.status IN ['active', 'harvesting', 'completed']
          LET loc = DOCUMENT(CONCAT('{col.LOCATIONS}/', run.location_key))
          FILTER loc != null AND loc.site_key == @site_key
          SORT run.started_at DESC
          RETURN run
        """
        cursor = self._db.aql.execute(query, bind_vars={"site_key": site_key})
        return [PlantingRun(**self._from_doc(doc)) for doc in cursor]

    # ── Nutrient plan assignment ───────────────────────────────────────

    def assign_nutrient_plan(self, run_key: PlantingRunKey, plan_key: str, assigned_by: str) -> dict:
        # Remove existing assignment if any
        self.remove_nutrient_plan(run_key)
        # Create edge
        from_id = f"{col.PLANTING_RUNS}/{run_key}"
        to_id = f"{col.NUTRIENT_PLANS}/{plan_key}"
        edge = self.create_edge(col.RUN_FOLLOWS_PLAN, from_id, to_id, {"assigned_by": assigned_by})
        # Update run doc
        now = datetime.now(UTC).isoformat()
        self._db.collection(col.PLANTING_RUNS).update(
            {
                "_key": run_key,
                "nutrient_plan_key": plan_key,
                "updated_at": now,
            }
        )
        # Cascade FOLLOWS_PLAN edges for plants in the run
        plants = self.get_run_plants(run_key, include_detached=False)
        for plant in plants:
            plant_key = plant.get("_key", "")
            if plant_key:
                plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
                # Remove existing FOLLOWS_PLAN
                self.delete_edges(col.FOLLOWS_PLAN, from_id=plant_id, to_id=to_id)
                self.create_edge(col.FOLLOWS_PLAN, plant_id, to_id)
        return {"run_key": run_key, "plan_key": plan_key, "edge_key": edge.get("_key", "")}

    def get_run_nutrient_plan_key(self, run_key: PlantingRunKey) -> str | None:
        query = f"""
        FOR e IN {col.RUN_FOLLOWS_PLAN}
          FILTER e._from == @run_id
          LIMIT 1
          RETURN PARSE_IDENTIFIER(e._to).key
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "run_id": f"{col.PLANTING_RUNS}/{run_key}",
            },
        )
        return next(cursor, None)

    def remove_nutrient_plan(self, run_key: PlantingRunKey) -> bool:
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        # Get existing plan key before removing
        existing_plan_key = self.get_run_nutrient_plan_key(run_key)
        if existing_plan_key is None:
            return False
        # Remove RUN_FOLLOWS_PLAN edge
        self.delete_edges(col.RUN_FOLLOWS_PLAN, from_id=run_id)
        # Remove FOLLOWS_PLAN edges from plants to this plan
        plan_id = f"{col.NUTRIENT_PLANS}/{existing_plan_key}"
        plants = self.get_run_plants(run_key, include_detached=False)
        for plant in plants:
            plant_key = plant.get("_key", "")
            if plant_key:
                plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
                self.delete_edges(col.FOLLOWS_PLAN, from_id=plant_id, to_id=plan_id)
        # Clear run field
        self._db.collection(col.PLANTING_RUNS).update(
            {
                "_key": run_key,
                "nutrient_plan_key": None,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        return True

    def get_active_runs_with_schedule(self) -> list[dict]:
        query = f"""
        FOR run IN {col.PLANTING_RUNS}
          FILTER run.status == 'active'
          FILTER run.nutrient_plan_key != null
          LET plan = DOCUMENT(CONCAT('{col.NUTRIENT_PLANS}/', run.nutrient_plan_key))
          FILTER plan != null
          FILTER plan.watering_schedule != null
          RETURN {{
            run_key: run._key,
            run_name: run.name,
            plan_key: run.nutrient_plan_key,
            watering_schedule: plan.watering_schedule
          }}
        """
        cursor = self._db.aql.execute(query)
        return list(cursor)

    def get_batch_phase_summaries(self, run_keys: list[str]) -> dict[str, list[dict]]:
        if not run_keys:
            return {}
        query = f"""
        FOR run_key IN @run_keys
          LET run_id = CONCAT('{col.PLANTING_RUNS}/', run_key)
          LET phases = (
            FOR e IN {col.RUN_CONTAINS}
              FILTER e._from == run_id AND e.detached_at == null
              LET plant = DOCUMENT(e._to)
              FILTER plant != null AND plant.removed_on == null
              LET gp = DOCUMENT(CONCAT('{col.GROWTH_PHASES}/', plant.current_phase_key))
              LET phase_name = gp != null ? gp.name : ''
              COLLECT phase = phase_name WITH COUNT INTO cnt
              RETURN {{ phase: phase, cnt: cnt }}
          )
          RETURN {{ run_key: run_key, phases: phases }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"run_keys": run_keys})
        result: dict[str, list[dict]] = {}
        for row in cursor:
            result[row["run_key"]] = row["phases"]
        return result

    def get_plant_keys_with_active_schedule(self) -> set[str]:
        query = f"""
        FOR run IN {col.PLANTING_RUNS}
          FILTER run.status == 'active'
          FILTER run.nutrient_plan_key != null
          LET plan = DOCUMENT(CONCAT('{col.NUTRIENT_PLANS}/', run.nutrient_plan_key))
          FILTER plan != null
          FILTER plan.watering_schedule != null
          FOR e IN {col.RUN_CONTAINS}
            FILTER e._from == CONCAT('{col.PLANTING_RUNS}/', run._key)
            FILTER e.detached_at == null
            RETURN PARSE_IDENTIFIER(e._to).key
        """
        cursor = self._db.aql.execute(query)
        return {key for key in cursor if key}
