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

    def _resolve_phase_name(self, doc: dict) -> dict:
        """Strip legacy current_phase string; the key is the single source of truth."""
        doc.pop("current_phase", None)
        return doc

    # ── Basic CRUD ────────────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
    ) -> tuple[list[PlantInstance], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit, tenant_key=tenant_key)
        return [PlantInstance(**self._resolve_phase_name(doc)) for doc in docs], total

    def get_by_key(self, key: PlantID) -> PlantInstance | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return PlantInstance(**self._resolve_phase_name(doc)) if doc else None

    def get_by_instance_id(self, instance_id: str) -> PlantInstance | None:
        docs = self.find_by_field("instance_id", instance_id)
        return PlantInstance(**self._resolve_phase_name(docs[0])) if docs else None

    def create(self, plant: PlantInstance) -> PlantInstance:
        doc = BaseArangoRepository.create(self, plant)
        created = PlantInstance(**self._resolve_phase_name(doc))
        if plant.slot_key:
            plant_id = f"{col.PLANT_INSTANCES}/{doc['_key']}"
            slot_id = f"{col.SLOTS}/{plant.slot_key}"
            self.create_edge(col.PLACED_IN, plant_id, slot_id)
        return created

    def update(self, key: PlantID, plant: PlantInstance) -> PlantInstance:
        # Use exclude_none=False so nullable fields (location_key, slot_key, etc.)
        # can be explicitly set to null.  keep_none=False tells ArangoDB to remove
        # the attribute from the document when the value is null.
        data = plant.model_dump(by_alias=True, exclude_none=False, mode="json")
        data.pop("_key", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self.collection.update({"_key": key, **data}, return_new=True, keep_none=False)
        return PlantInstance(**self._resolve_phase_name(self._from_doc(result["new"])))

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
        return [PlantInstance(**self._resolve_phase_name(self._from_doc(r["vertex"]))) for r in results]

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
        return [PlantInstance(**self._resolve_phase_name(self._from_doc(doc))) for doc in cursor]

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
        return [PlantInstance(**self._resolve_phase_name(self._from_doc(doc))) for doc in cursor]

    # ── Species-based query ───────────────────────────────────────────

    def get_by_species(self, species_key: SpeciesKey) -> list[PlantInstance]:
        docs = self.find_by_field("species_key", species_key)
        return [PlantInstance(**self._resolve_phase_name(doc)) for doc in docs]

    def resolve_phase_name(self, phase_key: str) -> str:
        """Resolve a GrowthPhase key to its name."""
        if not phase_key:
            return ""
        doc = self._db.collection(col.GROWTH_PHASES).get(phase_key)
        return doc.get("name", "") if doc else ""
