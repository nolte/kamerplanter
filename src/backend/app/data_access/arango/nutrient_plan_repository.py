from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry


class ArangoNutrientPlanRepository(INutrientPlanRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.NUTRIENT_PLANS)

    # ── Plan CRUD ────────────────────────────────────────────────────

    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[NutrientPlan], int]:
        if filters:
            query = f"FOR doc IN {col.NUTRIENT_PLANS}"
            bind_vars: dict[str, Any] = {}
            filter_clauses = []
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")
            query += " FILTER " + " AND ".join(filter_clauses)
            count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
            query += f" SORT doc.name LIMIT {offset}, {limit} RETURN doc"
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            items = [NutrientPlan(**self._from_doc(doc)) for doc in cursor]
            count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
            total = next(count_cursor, 0)
            return items, total
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [NutrientPlan(**doc) for doc in docs], total

    def get_by_key(self, key: NutrientPlanKey) -> NutrientPlan | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return NutrientPlan(**doc) if doc else None

    def create(self, plan: NutrientPlan) -> NutrientPlan:
        doc = BaseArangoRepository.create(self, plan)
        return NutrientPlan(**doc)

    def update(self, key: NutrientPlanKey, plan: NutrientPlan) -> NutrientPlan:
        doc = BaseArangoRepository.update(self, key, plan)
        return NutrientPlan(**doc)

    def delete(self, key: NutrientPlanKey) -> bool:
        plan_id = f"{col.NUTRIENT_PLANS}/{key}"
        # Delete phase entries and their edges
        entries = self.get_phase_entries(key)
        for entry in entries:
            if entry.key:
                self.delete_phase_entry(entry.key)
        # Delete outbound edges
        for edge_col in [col.HAS_PHASE_ENTRY, col.CLONED_FROM]:
            self.delete_edges(edge_col, plan_id)
        # Delete inbound edges
        for edge_col in [col.FOLLOWS_PLAN, col.CLONED_FROM]:
            query = f"FOR e IN {edge_col} FILTER e._to == @pid REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"pid": plan_id})
        return BaseArangoRepository.delete(self, key)

    # ── Phase entries ────────────────────────────────────────────────

    def create_phase_entry(self, entry: NutrientPlanPhaseEntry) -> NutrientPlanPhaseEntry:
        data = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        result = self._db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = NutrientPlanPhaseEntry(**doc)
        # Create edge
        from_id = f"{col.NUTRIENT_PLANS}/{entry.plan_key}"
        to_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{doc['_key']}"
        self.create_edge(col.HAS_PHASE_ENTRY, from_id, to_id)
        return created

    def get_phase_entries(self, plan_key: NutrientPlanKey) -> list[NutrientPlanPhaseEntry]:
        query = """
        FOR doc IN @@collection
          FILTER doc.plan_key == @plan_key
          SORT doc.sequence_order ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.NUTRIENT_PLAN_PHASE_ENTRIES,
            "plan_key": plan_key,
        })
        return [NutrientPlanPhaseEntry(**self._from_doc(doc)) for doc in cursor]

    def get_phase_entry_by_key(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry | None:
        doc = self._db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).get(key)
        if doc is None:
            return None
        return NutrientPlanPhaseEntry(**self._from_doc(doc))

    def update_phase_entry(
        self, key: NutrientPlanPhaseEntryKey, entry: NutrientPlanPhaseEntry,
    ) -> NutrientPlanPhaseEntry:
        data = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).update(
            {"_key": key, **data}, return_new=True,
        )
        return NutrientPlanPhaseEntry(**self._from_doc(result["new"]))

    def delete_phase_entry(self, key: NutrientPlanPhaseEntryKey) -> bool:
        entry_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{key}"
        # Delete fertilizer edges
        self.delete_edges(col.PLAN_USES_FERTILIZER, entry_id)
        # Delete parent edge
        query = f"FOR e IN {col.HAS_PHASE_ENTRY} FILTER e._to == @eid REMOVE e IN {col.HAS_PHASE_ENTRY}"
        self._db.aql.execute(query, bind_vars={"eid": entry_id})
        try:
            self._db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).delete(key)
            return True
        except Exception:
            return False

    # ── Fertilizer edges ─────────────────────────────────────────────

    def add_fertilizer_to_entry(
        self, entry_key: NutrientPlanPhaseEntryKey, fertilizer_key: FertilizerKey,
        ml_per_liter: float, optional: bool = False,
    ) -> dict:
        from_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{entry_key}"
        to_id = f"{col.FERTILIZERS}/{fertilizer_key}"
        edge_data = {"ml_per_liter": ml_per_liter, "optional": optional}
        return self.create_edge(col.PLAN_USES_FERTILIZER, from_id, to_id, edge_data)

    def remove_fertilizer_from_entry(
        self, entry_key: NutrientPlanPhaseEntryKey, fertilizer_key: FertilizerKey,
    ) -> bool:
        from_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{entry_key}"
        to_id = f"{col.FERTILIZERS}/{fertilizer_key}"
        self.delete_edges(col.PLAN_USES_FERTILIZER, from_id, to_id)
        return True

    # ── Plant assignment ─────────────────────────────────────────────

    def assign_to_plant(self, plant_key: str, plan_key: NutrientPlanKey, assigned_by: str = "") -> dict:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        plan_id = f"{col.NUTRIENT_PLANS}/{plan_key}"
        # Remove existing assignment
        self.delete_edges(col.FOLLOWS_PLAN, plant_id)
        # Create new
        edge_data = {"assigned_by": assigned_by, "assigned_at": datetime.now(UTC).isoformat()}
        return self.create_edge(col.FOLLOWS_PLAN, plant_id, plan_id, edge_data)

    def get_plant_plan(self, plant_key: str) -> NutrientPlan | None:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        query = f"""
        FOR e IN {col.FOLLOWS_PLAN}
          FILTER e._from == @pid
          LET plan = DOCUMENT(e._to)
          RETURN plan
        """
        cursor = self._db.aql.execute(query, bind_vars={"pid": plant_id})
        docs = list(cursor)
        if not docs or docs[0] is None:
            return None
        return NutrientPlan(**self._from_doc(docs[0]))

    def remove_plant_plan(self, plant_key: str) -> bool:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        self.delete_edges(col.FOLLOWS_PLAN, plant_id)
        return True

    # ── Clone ────────────────────────────────────────────────────────

    def clone(self, source_key: NutrientPlanKey, new_name: str, author: str = "") -> NutrientPlan:
        source = self.get_by_key(source_key)
        if source is None:
            raise ValueError(f"Source plan '{source_key}' not found")

        # Create new plan
        new_plan = NutrientPlan(
            name=new_name,
            description=source.description,
            recommended_substrate_type=source.recommended_substrate_type,
            author=author,
            is_template=False,
            version="1.0",
            tags=list(source.tags),
            cloned_from_key=source_key,
        )
        created_plan = self.create(new_plan)

        # Create CLONED_FROM edge
        from_id = f"{col.NUTRIENT_PLANS}/{created_plan.key}"
        to_id = f"{col.NUTRIENT_PLANS}/{source_key}"
        self.create_edge(col.CLONED_FROM, from_id, to_id)

        # Clone phase entries
        entries = self.get_phase_entries(source_key)
        for entry in entries:
            new_entry = NutrientPlanPhaseEntry(
                plan_key=created_plan.key or "",
                phase_name=entry.phase_name,
                sequence_order=entry.sequence_order,
                week_start=entry.week_start,
                week_end=entry.week_end,
                npk_ratio=entry.npk_ratio,
                target_ec_ms=entry.target_ec_ms,
                target_ph=entry.target_ph,
                calcium_ppm=entry.calcium_ppm,
                magnesium_ppm=entry.magnesium_ppm,
                feeding_frequency_per_week=entry.feeding_frequency_per_week,
                volume_per_feeding_liters=entry.volume_per_feeding_liters,
                notes=entry.notes,
                fertilizer_dosages=list(entry.fertilizer_dosages),
            )
            self.create_phase_entry(new_entry)

        return created_plan
