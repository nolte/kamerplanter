from typing import Any

from arango.database import StandardDatabase

from app.common.types import SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.graph_repository import IGraphRepository


class ArangoGraphRepository(IGraphRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SPECIES)

    # ── Companion Planting ────────────────────────────────────────────

    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 OUTBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN {species: v, score: e.score}
        """
        bind_vars = {
            "start": f"{col.SPECIES}/{species_key}",
            "edge_col": col.COMPATIBLE_WITH,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "species": self._from_doc(r["species"]),
                "score": r.get("score", 0.0),
            }
            for r in cursor
        ]

    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 OUTBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN {species: v, reason: e.reason}
        """
        bind_vars = {
            "start": f"{col.SPECIES}/{species_key}",
            "edge_col": col.INCOMPATIBLE_WITH,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "species": self._from_doc(r["species"]),
                "reason": r.get("reason", ""),
            }
            for r in cursor
        ]

    def set_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, score: float) -> None:
        from_id = f"{col.SPECIES}/{from_key}"
        to_id = f"{col.SPECIES}/{to_key}"
        # Remove existing edge if present, then create new one
        self.delete_edges(col.COMPATIBLE_WITH, from_id, to_id)
        self.create_edge(col.COMPATIBLE_WITH, from_id, to_id, data={"score": score})
        # Create reverse edge for bidirectional lookup
        self.delete_edges(col.COMPATIBLE_WITH, to_id, from_id)
        self.create_edge(col.COMPATIBLE_WITH, to_id, from_id, data={"score": score})

    def set_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, reason: str) -> None:
        from_id = f"{col.SPECIES}/{from_key}"
        to_id = f"{col.SPECIES}/{to_key}"
        # Remove existing edge if present, then create new one
        self.delete_edges(col.INCOMPATIBLE_WITH, from_id, to_id)
        self.create_edge(col.INCOMPATIBLE_WITH, from_id, to_id, data={"reason": reason})
        # Create reverse edge for bidirectional lookup
        self.delete_edges(col.INCOMPATIBLE_WITH, to_id, from_id)
        self.create_edge(col.INCOMPATIBLE_WITH, to_id, from_id, data={"reason": reason})

    def remove_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        from_id = f"{col.SPECIES}/{from_key}"
        to_id = f"{col.SPECIES}/{to_key}"
        self.delete_edges(col.COMPATIBLE_WITH, from_id, to_id)
        self.delete_edges(col.COMPATIBLE_WITH, to_id, from_id)
        return True

    def remove_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        from_id = f"{col.SPECIES}/{from_key}"
        to_id = f"{col.SPECIES}/{to_key}"
        self.delete_edges(col.INCOMPATIBLE_WITH, from_id, to_id)
        self.delete_edges(col.INCOMPATIBLE_WITH, to_id, from_id)
        return True

    # ── Rotation Planning ─────────────────────────────────────────────

    def get_rotation_successors(self, family_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 OUTBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN {family: v, wait_years: e.wait_years}
        """
        bind_vars = {
            "start": f"{col.BOTANICAL_FAMILIES}/{family_key}",
            "edge_col": col.ROTATION_AFTER,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "family": self._from_doc(r["family"]),
                "wait_years": r.get("wait_years", 1),
            }
            for r in cursor
        ]

    def set_rotation_successor(self, from_family_key: str, to_family_key: str, wait_years: int) -> None:
        from_id = f"{col.BOTANICAL_FAMILIES}/{from_family_key}"
        to_id = f"{col.BOTANICAL_FAMILIES}/{to_family_key}"
        self.delete_edges(col.ROTATION_AFTER, from_id, to_id)
        self.create_edge(col.ROTATION_AFTER, from_id, to_id, data={"wait_years": wait_years})

    # ── Slot Adjacency ────────────────────────────────────────────────

    def get_adjacent_slots(self, slot_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 ANY @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN {slot: v}
        """
        bind_vars = {
            "start": f"{col.SLOTS}/{slot_key}",
            "edge_col": col.ADJACENT_TO,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [{"slot": self._from_doc(r["slot"])} for r in cursor]

    def set_adjacent_slots(self, slot_a_key: str, slot_b_key: str) -> None:
        a_id = f"{col.SLOTS}/{slot_a_key}"
        b_id = f"{col.SLOTS}/{slot_b_key}"
        # Adjacency is bidirectional — create edges in both directions
        self.delete_edges(col.ADJACENT_TO, a_id, b_id)
        self.delete_edges(col.ADJACENT_TO, b_id, a_id)
        self.create_edge(col.ADJACENT_TO, a_id, b_id)
        self.create_edge(col.ADJACENT_TO, b_id, a_id)
