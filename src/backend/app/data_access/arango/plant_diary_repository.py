from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.plant_diary_repository import IPlantDiaryRepository
from app.domain.models.plant_diary_entry import PlantDiaryEntry


class ArangoPlantDiaryRepository(IPlantDiaryRepository, BaseArangoRepository):
    """ArangoDB implementation for plant diary entries."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PLANT_DIARY_ENTRIES)

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(self, entry: PlantDiaryEntry) -> PlantDiaryEntry:
        doc = BaseArangoRepository.create(self, entry)
        created = PlantDiaryEntry(**doc)

        # Create has_diary_entry edge: plant → diary entry
        if entry.plant_key:
            plant_id = f"{col.PLANT_INSTANCES}/{entry.plant_key}"
            entry_id = f"{col.PLANT_DIARY_ENTRIES}/{doc['_key']}"
            self.create_edge(col.HAS_DIARY_ENTRY, plant_id, entry_id)

        return created

    def get_by_key(self, key: str) -> PlantDiaryEntry | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return PlantDiaryEntry(**doc) if doc else None

    def update(self, key: str, entry: PlantDiaryEntry) -> PlantDiaryEntry:
        doc = BaseArangoRepository.update(self, key, entry)
        return PlantDiaryEntry(**doc)

    def delete(self, key: str) -> bool:
        # Remove has_diary_entry edges pointing to this entry
        entry_id = f"{col.PLANT_DIARY_ENTRIES}/{key}"
        query = f"FOR e IN {col.HAS_DIARY_ENTRY} FILTER e._to == @entry_id REMOVE e IN {col.HAS_DIARY_ENTRY}"
        self._db.aql.execute(query, bind_vars={"entry_id": entry_id})
        return BaseArangoRepository.delete(self, key)

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> tuple[list[PlantDiaryEntry], int]:
        """Get diary entries for a specific plant, ordered by creation date descending."""
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"

        count_query = (
            f"FOR e IN {col.HAS_DIARY_ENTRY} FILTER e._from == @plant_id COLLECT WITH COUNT INTO cnt RETURN cnt"
        )
        count_cursor = self._db.aql.execute(count_query, bind_vars={"plant_id": plant_id})
        total = next(count_cursor, 0)

        query = (
            f"FOR e IN {col.HAS_DIARY_ENTRY} "
            "FILTER e._from == @plant_id "
            "LET entry = DOCUMENT(e._to) "
            "SORT entry.created_at DESC "
            "LIMIT @offset, @limit "
            "RETURN entry"
        )
        bind_vars = {
            "plant_id": plant_id,
            "offset": offset,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        entries = [PlantDiaryEntry(**self._from_doc(doc)) for doc in cursor]
        return entries, total

    def get_by_run(self, run_key: str, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        """Get diary entries for all non-detached plants in a run.

        Returns a list of dicts with plant_key, plant_id (instance_id),
        plant_name and the diary_entry object.
        """
        run_id = f"{col.PLANTING_RUNS}/{run_key}"

        # Count total diary entries across all plants in the run
        count_query = (
            f"FOR rc IN {col.RUN_CONTAINS} "
            "FILTER rc._from == @run_id AND rc.detached_at == null "
            "LET plant = DOCUMENT(rc._to) "
            f"FOR de IN {col.HAS_DIARY_ENTRY} "
            "FILTER de._from == rc._to "
            "COLLECT WITH COUNT INTO cnt "
            "RETURN cnt"
        )
        count_cursor = self._db.aql.execute(count_query, bind_vars={"run_id": run_id})
        total = next(count_cursor, 0)

        # Fetch diary entries with plant context
        query = (
            f"FOR rc IN {col.RUN_CONTAINS} "
            "FILTER rc._from == @run_id AND rc.detached_at == null "
            "LET plant = DOCUMENT(rc._to) "
            f"FOR de IN {col.HAS_DIARY_ENTRY} "
            "FILTER de._from == rc._to "
            "LET entry = DOCUMENT(de._to) "
            "SORT entry.created_at DESC "
            "LIMIT @offset, @limit "
            "RETURN { "
            "  plant_key: plant._key, "
            "  plant_id: plant.instance_id, "
            "  plant_name: plant.name, "
            "  diary_entry: entry "
            "}"
        )
        bind_vars = {
            "run_id": run_id,
            "offset": offset,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        results = []
        for doc in cursor:
            entry_data = doc.get("diary_entry")
            if entry_data:
                entry_data = self._from_doc(entry_data)
                doc["diary_entry"] = PlantDiaryEntry(**entry_data).model_dump(by_alias=True, mode="json")
            results.append(doc)

        return results, total
