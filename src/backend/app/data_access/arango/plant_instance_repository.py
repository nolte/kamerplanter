from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.enums import TerminationType
from app.common.types import PlantID, SlotKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.plant_instance import PlantInstance


class ArangoPlantInstanceRepository(BaseArangoRepository[PlantInstance], IPlantInstanceRepository):
    is_tenant_scoped = True
    _model_cls = PlantInstance

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.PLANT_INSTANCES)

    def _resolve_phase_name(self, doc: dict) -> dict:
        """Strip legacy current_phase string; the key is the single source of truth."""
        doc.pop("current_phase", None)
        return doc

    # ── Basic CRUD ────────────────────────────────────────────────────

    def get_by_instance_id(self, instance_id: str, tenant_key: str = "") -> PlantInstance | None:
        """Look up a plant by its (globally unique) ``instance_id``.

        ``instance_id`` carries a unique index, so a bare lookup already returns at
        most one document. When ``tenant_key`` is given the match is additionally
        constrained to that tenant (SEC-001, defence in depth) so a caller can never
        act on another tenant's instance even if an id were to collide.
        """
        extra = [("tenant_key", "==", tenant_key)] if tenant_key else None
        return self.find_one_by_field("instance_id", instance_id, extra_filters=extra)

    def create(self, plant: PlantInstance) -> PlantInstance:
        created = super().create(plant)
        if plant.slot_key:
            plant_id = f"{col.PLANT_INSTANCES}/{created.key}"
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
        return PlantInstance(**self._from_doc(result["new"]))

    def delete(self, key: PlantID) -> bool:
        plant_id = f"{col.PLANT_INSTANCES}/{key}"
        self.delete_edges(col.PLACED_IN, from_id=plant_id)
        self.delete_edges(col.PHASE_HISTORY_EDGE, from_id=plant_id)
        self.delete_edges(col.CURRENT_PHASE, from_id=plant_id)
        # REQ-017 / D10 lineage: a descended_from edge points child → mother, so a
        # plant can be either endpoint. Remove edges in BOTH directions so deleting
        # a pup (outbound) or a mother (inbound) never leaves a dangling edge — an
        # orphaned inbound edge would otherwise keep ``has_descendants(mother)`` true
        # and permanently block a re-spawn.
        self.delete_edges(col.DESCENDED_FROM, vertex_id=plant_id, direction="any")
        return super().delete(key)

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
        return self.find_by_field("species_key", species_key)

    # ── Genetic lineage (REQ-017 / REQ-003 D10) ───────────────────────

    def create_descended_from_edge(self, child_key: PlantID, mother_key: PlantID) -> None:
        """Link a clonal pup back to its mother: child (descendant) → mother (ancestor)."""
        child_id = f"{col.PLANT_INSTANCES}/{child_key}"
        mother_id = f"{col.PLANT_INSTANCES}/{mother_key}"
        self.create_edge(col.DESCENDED_FROM, child_id, mother_id)

    def has_descendants(self, mother_key: PlantID) -> bool:
        """Whether ``mother_key`` already has a descendant (inbound descended_from edge).

        The edge points child → mother, so descendants are the *inbound* neighbours
        of the mother vertex. Only the existence is needed (D10 idempotency guard),
        so the traversal is capped at a single hop and stops at the first match.
        """
        mother_id = f"{col.PLANT_INSTANCES}/{mother_key}"
        query = """
        FOR v, e IN 1..1 INBOUND @mother_id GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge_col]}
          LIMIT 1
          RETURN 1
        """
        bind_vars = {"mother_id": mother_id, "edge_col": col.DESCENDED_FROM}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, None) is not None

    def resolve_phase_name(self, phase_key: str) -> str:
        """Resolve a GrowthPhase key to its name."""
        if not phase_key:
            return ""
        doc = self._db.collection(col.GROWTH_PHASES).get(phase_key)
        return doc.get("name", "") if doc else ""

    # ── Survival / failure-cause analytics (REQ-003 G1) ───────────────

    def get_survival_stats(self, tenant_key: str) -> dict[str, Any]:
        """Aggregate the tenant's plant instances for survival analytics.

        A single AQL statement computes the totals and the three COLLECT
        breakdowns. Every sub-query filters on ``p.tenant_key == @tenant_key``,
        and the collection name is bound via ``@@col`` (never interpolated), so
        the query is both injection-safe and strictly tenant-scoped (SEC-B4).
        The empty ``tenant_key`` sentinel is rejected up-front to avoid an
        unscoped cross-tenant read.
        """
        if not tenant_key:
            raise ValueError(
                f"Collection '{self._collection_name}' is tenant-scoped: "
                "get_survival_stats requires a non-empty tenant_key (SEC-B4)."
            )
        query = """
        LET rows = (
          FOR p IN @@col
            FILTER p.tenant_key == @tenant_key
            RETURN {
              termination_type: p.termination_type,
              termination_cause: p.termination_cause,
              phase_key: p.current_phase_key,
              removed_on: p.removed_on
            }
        )
        LET total = LENGTH(rows)
        LET terminated = LENGTH(FOR r IN rows FILTER r.removed_on != null RETURN 1)
        LET died = LENGTH(FOR r IN rows FILTER r.termination_type == @died RETURN 1)
        LET by_type = (
          FOR r IN rows
            FILTER r.termination_type != null
            COLLECT value = r.termination_type WITH COUNT INTO count
            RETURN {value, count}
        )
        LET by_cause = (
          FOR r IN rows
            FILTER r.termination_type == @died AND r.termination_cause != null
            COLLECT value = r.termination_cause WITH COUNT INTO count
            RETURN {value, count}
        )
        LET by_phase = (
          FOR r IN rows
            FILTER r.termination_type == @died
            COLLECT value = r.phase_key WITH COUNT INTO count
            RETURN {value, count}
        )
        RETURN {total, terminated, died, by_type, by_cause, by_phase}
        """
        bind_vars = {
            "@col": self._collection_name,
            "tenant_key": tenant_key,
            "died": TerminationType.DIED.value,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, {})

    # ── Dashboard counts (REQ-009) ────────────────────────────────────

    def count_for_tenant(self, tenant_key: str) -> int:
        """Count all plant instances owned by ``tenant_key`` (REQ-009).

        The collection is bound via ``@@col`` (never interpolated) and every row
        is filtered on ``p.tenant_key == @tenant_key``; the empty-tenant sentinel
        is rejected up-front so the count can never span tenants (SEC-B4).
        """
        self._require_tenant_key(tenant_key, "count_for_tenant")
        query = """
        RETURN LENGTH(
          FOR p IN @@col
            FILTER p.tenant_key == @tenant_key
            RETURN 1
        )
        """
        bind_vars = {"@col": self._collection_name, "tenant_key": tenant_key}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def count_active_for_tenant(self, tenant_key: str) -> int:
        """Count *alive* plant instances of ``tenant_key`` (REQ-009).

        "Alive" mirrors the codebase-wide marker: a plant is active while it has
        not been removed (``removed_on == null``) — the same predicate used by
        ``get_active_by_slot`` and by ``get_survival_stats`` (``terminated =
        removed_on != null``).
        """
        self._require_tenant_key(tenant_key, "count_active_for_tenant")
        query = """
        RETURN LENGTH(
          FOR p IN @@col
            FILTER p.tenant_key == @tenant_key AND p.removed_on == null
            RETURN 1
        )
        """
        bind_vars = {"@col": self._collection_name, "tenant_key": tenant_key}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)
