from typing import Any

from arango.database import StandardDatabase

from app.common.types import SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.graph_repository import IGraphRepository


class ArangoGraphRepository(IGraphRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        # Pure edge/graph manager: custom AQL + edge helpers only, returns raw
        # dicts. Explicit raw opt-in keeps the typed base API's fail-fast guard
        # from tripping on this legitimately unbound repository (FR-002 A3).
        BaseArangoRepository.__init__(self, db, col.SPECIES, raw=True)

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

    def get_companion_counts(self) -> dict[str, dict[str, int]]:
        # Single batch aggregation over BOTH edge collections in one round trip —
        # never a per-species query (no N+1). Edges are written bidirectionally
        # (set_compatibility/set_incompatibility create A→B and B→A), so grouping
        # outbound edges by their _from species yields, per species, exactly the
        # number of its curated companions — each relationship counted once from
        # that species' perspective. PARSE_IDENTIFIER strips the "species/" prefix
        # so the caller keys directly by species _key.
        query = """
        LET compatible = (
          FOR edge IN @@compatible_col
            COLLECT species_key = PARSE_IDENTIFIER(edge._from).key WITH COUNT INTO n
            RETURN {species_key: species_key, count: n}
        )
        LET incompatible = (
          FOR edge IN @@incompatible_col
            COLLECT species_key = PARSE_IDENTIFIER(edge._from).key WITH COUNT INTO n
            RETURN {species_key: species_key, count: n}
        )
        RETURN {compatible: compatible, incompatible: incompatible}
        """
        bind_vars = {
            "@compatible_col": col.COMPATIBLE_WITH,
            "@incompatible_col": col.INCOMPATIBLE_WITH,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        aggregate = next(iter(cursor), {"compatible": [], "incompatible": []})

        counts: dict[str, dict[str, int]] = {}
        for row in aggregate.get("compatible", []):
            entry = counts.setdefault(row["species_key"], {"compatible": 0, "incompatible": 0})
            entry["compatible"] = row["count"]
        for row in aggregate.get("incompatible", []):
            entry = counts.setdefault(row["species_key"], {"compatible": 0, "incompatible": 0})
            entry["incompatible"] = row["count"]
        return counts

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
          RETURN {family: v, wait_years: e.wait_years,
                  benefit_score: e.benefit_score, benefit_reason: e.benefit_reason}
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
                "benefit_score": r.get("benefit_score", 0.0),
                "benefit_reason": r.get("benefit_reason", ""),
            }
            for r in cursor
        ]

    def get_rotation_successor_counts(self) -> dict[str, int]:
        # Single batch aggregation over the ROTATION_AFTER edge collection in one
        # round trip — never a per-family query (no N+1). Grouping outbound edges
        # by their _from family yields, per family, exactly the number of curated
        # rotation successors. PARSE_IDENTIFIER strips the "botanical_families/"
        # prefix so the caller keys directly by family _key. Rotation edges are
        # global reference data — no tenant scoping applies.
        query = """
        FOR edge IN @@rotation_col
          COLLECT family_key = PARSE_IDENTIFIER(edge._from).key WITH COUNT INTO n
          RETURN {family_key: family_key, count: n}
        """
        bind_vars = {"@rotation_col": col.ROTATION_AFTER}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return {row["family_key"]: row["count"] for row in cursor}

    def set_rotation_successor(
        self,
        from_family_key: str,
        to_family_key: str,
        wait_years: int,
        benefit_score: float = 0.0,
        benefit_reason: str = "",
    ) -> None:
        from_id = f"{col.BOTANICAL_FAMILIES}/{from_family_key}"
        to_id = f"{col.BOTANICAL_FAMILIES}/{to_family_key}"
        self.delete_edges(col.ROTATION_AFTER, from_id, to_id)
        self.create_edge(
            col.ROTATION_AFTER,
            from_id,
            to_id,
            data={
                "wait_years": wait_years,
                "benefit_score": benefit_score,
                "benefit_reason": benefit_reason,
            },
        )

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

    # ── Family-level edges ─────────────────────────────────────────────

    def get_pest_risks(self, family_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 ANY @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN DISTINCT {family: v, shared_pests: e.shared_pests,
                  shared_diseases: e.shared_diseases, risk_level: e.risk_level}
        """
        bind_vars = {
            "start": f"{col.BOTANICAL_FAMILIES}/{family_key}",
            "edge_col": col.SHARES_PEST_RISK,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "family": self._from_doc(r["family"]),
                "shared_pests": r.get("shared_pests", []),
                "shared_diseases": r.get("shared_diseases", []),
                "risk_level": r.get("risk_level", "low"),
            }
            for r in cursor
        ]

    def set_pest_risk(
        self,
        a_key: str,
        b_key: str,
        shared_pests: list[str],
        shared_diseases: list[str],
        risk_level: str,
    ) -> None:
        a_id = f"{col.BOTANICAL_FAMILIES}/{a_key}"
        b_id = f"{col.BOTANICAL_FAMILIES}/{b_key}"
        data = {"shared_pests": shared_pests, "shared_diseases": shared_diseases, "risk_level": risk_level}
        self.delete_edges(col.SHARES_PEST_RISK, a_id, b_id)
        self.create_edge(col.SHARES_PEST_RISK, a_id, b_id, data=data)
        if a_key != b_key:
            self.delete_edges(col.SHARES_PEST_RISK, b_id, a_id)
            self.create_edge(col.SHARES_PEST_RISK, b_id, a_id, data=data)

    def get_family_compatible(self, family_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 ANY @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN DISTINCT {family: v, benefit_type: e.benefit_type,
                  compatibility_score: e.compatibility_score, notes: e.notes}
        """
        bind_vars = {
            "start": f"{col.BOTANICAL_FAMILIES}/{family_key}",
            "edge_col": col.FAMILY_COMPATIBLE_WITH,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "family": self._from_doc(r["family"]),
                "benefit_type": r.get("benefit_type", ""),
                "compatibility_score": r.get("compatibility_score", 0.0),
                "notes": r.get("notes", ""),
            }
            for r in cursor
        ]

    def set_family_compatible(
        self,
        a_key: str,
        b_key: str,
        benefit_type: str,
        compatibility_score: float,
        notes: str,
    ) -> None:
        a_id = f"{col.BOTANICAL_FAMILIES}/{a_key}"
        b_id = f"{col.BOTANICAL_FAMILIES}/{b_key}"
        data = {"benefit_type": benefit_type, "compatibility_score": compatibility_score, "notes": notes}
        self.delete_edges(col.FAMILY_COMPATIBLE_WITH, a_id, b_id)
        self.create_edge(col.FAMILY_COMPATIBLE_WITH, a_id, b_id, data=data)
        if a_key != b_key:
            self.delete_edges(col.FAMILY_COMPATIBLE_WITH, b_id, a_id)
            self.create_edge(col.FAMILY_COMPATIBLE_WITH, b_id, a_id, data=data)

    def get_family_incompatible(self, family_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 ANY @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN DISTINCT {family: v, reason: e.reason, severity: e.severity}
        """
        bind_vars = {
            "start": f"{col.BOTANICAL_FAMILIES}/{family_key}",
            "edge_col": col.FAMILY_INCOMPATIBLE_WITH,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [
            {
                "family": self._from_doc(r["family"]),
                "reason": r.get("reason", ""),
                "severity": r.get("severity", "moderate"),
            }
            for r in cursor
        ]

    def set_family_incompatible(
        self,
        a_key: str,
        b_key: str,
        reason: str,
        severity: str,
    ) -> None:
        a_id = f"{col.BOTANICAL_FAMILIES}/{a_key}"
        b_id = f"{col.BOTANICAL_FAMILIES}/{b_key}"
        data = {"reason": reason, "severity": severity}
        self.delete_edges(col.FAMILY_INCOMPATIBLE_WITH, a_id, b_id)
        self.create_edge(col.FAMILY_INCOMPATIBLE_WITH, a_id, b_id, data=data)
        if a_key != b_key:
            self.delete_edges(col.FAMILY_INCOMPATIBLE_WITH, b_id, a_id)
            self.create_edge(col.FAMILY_INCOMPATIBLE_WITH, b_id, a_id, data=data)

    def get_species_by_family(self, family_key: str) -> list[dict[str, Any]]:
        query = """
        FOR v, e IN 1..1 INBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          RETURN v
        """
        bind_vars = {
            "start": f"{col.BOTANICAL_FAMILIES}/{family_key}",
            "edge_col": col.BELONGS_TO_FAMILY,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._from_doc(r) for r in cursor]
