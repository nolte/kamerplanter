from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.types import PlantID, SlotKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.plant_instance import PlantInstance


class ArangoPlantInstanceRepository(IPlantInstanceRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PLANT_INSTANCES)

    # ── Basic CRUD ────────────────────────────────────────────────────

    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[PlantInstance], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [PlantInstance(**doc) for doc in docs], total

    def get_by_key(self, key: PlantID) -> PlantInstance | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return PlantInstance(**doc) if doc else None

    def get_by_instance_id(self, instance_id: str) -> PlantInstance | None:
        docs = self.find_by_field("instance_id", instance_id)
        return PlantInstance(**docs[0]) if docs else None

    def create(self, plant: PlantInstance) -> PlantInstance:
        doc = BaseArangoRepository.create(self, plant)
        created = PlantInstance(**doc)
        if plant.slot_key:
            plant_id = f"{col.PLANT_INSTANCES}/{doc['_key']}"
            slot_id = f"{col.SLOTS}/{plant.slot_key}"
            self.create_edge(col.PLACED_IN, plant_id, slot_id)
        return created

    def update(self, key: PlantID, plant: PlantInstance) -> PlantInstance:
        doc = BaseArangoRepository.update(self, key, plant)
        return PlantInstance(**doc)

    def delete(self, key: PlantID) -> bool:
        plant_id = f"{col.PLANT_INSTANCES}/{key}"
        self.delete_edges(col.PLACED_IN, from_id=plant_id)
        self.delete_edges(col.PHASE_HISTORY_EDGE, from_id=plant_id)
        self.delete_edges(col.CURRENT_PHASE, from_id=plant_id)
        return BaseArangoRepository.delete(self, key)

    # ── Slot-based queries ────────────────────────────────────────────

    def get_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]:
        slot_id = f"{col.SLOTS}/{slot_key}"
        results = self.get_edges(col.PLACED_IN, slot_id, direction="inbound")
        return [PlantInstance(**self._from_doc(r["vertex"])) for r in results]

    def get_active_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]:
        query = """
        FOR v, e IN 1..1 INBOUND @slot_id GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          FILTER v.removed_on == null
          RETURN v
        """
        bind_vars = {
            "slot_id": f"{col.SLOTS}/{slot_key}",
            "edge_col": col.PLACED_IN,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantInstance(**self._from_doc(doc)) for doc in cursor]

    def get_history_by_slot(self, slot_key: SlotKey, years: int = 3) -> list[PlantInstance]:
        cutoff = datetime.now(UTC).replace(year=datetime.now(UTC).year - years)
        cutoff_iso = cutoff.isoformat()
        query = """
        FOR v, e IN 1..1 INBOUND @slot_id GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          FILTER v.planted_on >= @cutoff
          SORT v.planted_on DESC
          RETURN v
        """
        bind_vars = {
            "slot_id": f"{col.SLOTS}/{slot_key}",
            "edge_col": col.PLACED_IN,
            "cutoff": cutoff_iso,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantInstance(**self._from_doc(doc)) for doc in cursor]

    # ── Species-based query ───────────────────────────────────────────

    def get_by_species(self, species_key: SpeciesKey) -> list[PlantInstance]:
        docs = self.find_by_field("species_key", species_key)
        return [PlantInstance(**doc) for doc in docs]
