from datetime import UTC, date, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.enums import TaskStatus, TerminationType
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

    # ── Phase-definition detail lists (FIX-01 R1/R8) ──────────────────

    def list_active_in_phase_definition(self, tenant_key: str, phase_definition_key: str) -> list[dict[str, Any]]:
        """Return the tenant's *active* instances currently in a phase definition (FIX-01 R1/R8).

        The phase indirection (A1) is resolved inside a single AQL statement: a
        plant's ``current_phase_key`` points at a ``PhaseSequenceEntry`` (the
        preferred path) or — for legacy data — at a ``GrowthPhase``. There is no
        ``phase_definition_key`` on ``GrowthPhase``, so the only stable legacy
        bridge is the shared canonical phase ``name`` (``GrowthPhase.name ==
        PhaseDefinition.name``); it is applied best-effort alongside the entry
        keys. "Active" mirrors the codebase-wide alive marker ``removed_on ==
        null`` (A2), consistent with ``count_active_for_tenant`` / survival stats.

        Security (SEC-001 / SEC-B4): every plant row is filtered on
        ``p.tenant_key == @tenant_key`` and the empty-tenant sentinel is rejected
        up-front, so the list can never span tenants; the denormalised location /
        slot labels are additionally gated on the *same* tenant so a cross-tenant
        foreign reference can never leak a name. All collection names travel as
        binds (``@@col`` / ``DOCUMENT(@…_col, …)``), never interpolated.
        """
        self._require_tenant_key(tenant_key, "list_active_in_phase_definition")
        query = """
        LET defn = DOCUMENT(@defn_col, @phase_definition_key)
        LET seq_entry_keys = (
          FOR e IN @@entry_col
            FILTER e.phase_definition_key == @phase_definition_key
            RETURN e._key
        )
        LET legacy_phase_keys = defn == null ? [] : (
          FOR gp IN @@growth_phase_col
            FILTER gp.name == defn.name
            RETURN gp._key
        )
        LET phase_keys = APPEND(seq_entry_keys, legacy_phase_keys)
        FOR p IN @@col
          FILTER p.tenant_key == @tenant_key
            AND p.removed_on == null
            AND p.current_phase_key != null
            AND p.current_phase_key IN phase_keys
          SORT p.current_phase_started_at DESC, p._key ASC
          LET species = p.species_key != null ? DOCUMENT(@species_col, p.species_key) : null
          LET location = p.location_key != null ? DOCUMENT(@location_col, p.location_key) : null
          LET slot = p.slot_key != null ? DOCUMENT(@slot_col, p.slot_key) : null
          RETURN {
            key: p._key,
            instance_id: p.instance_id,
            plant_name: p.plant_name,
            species_key: p.species_key,
            species_scientific_name: species != null ? species.scientific_name : null,
            species_common_names: species != null ? (species.common_names || []) : [],
            location_key: p.location_key,
            location_name: (location != null AND location.tenant_key == @tenant_key) ? location.name : null,
            slot_key: p.slot_key,
            slot_label: (slot != null AND slot.tenant_key == @tenant_key) ? slot.slot_id : null,
            current_phase_key: p.current_phase_key,
            current_phase_started_at: p.current_phase_started_at
          }
        """
        bind_vars = {
            "@col": self._collection_name,
            "@entry_col": col.PHASE_SEQUENCE_ENTRIES,
            "@growth_phase_col": col.GROWTH_PHASES,
            "tenant_key": tenant_key,
            "phase_definition_key": phase_definition_key,
            "defn_col": col.PHASE_DEFINITIONS,
            "species_col": col.SPECIES,
            "location_col": col.LOCATIONS,
            "slot_col": col.SLOTS,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

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

    def list_active_for_tenant(self, tenant_key: str, limit: int) -> list[dict[str, Any]]:
        """Return the newest *alive* plant instances of ``tenant_key``, enriched (REQ-009).

        Feeds the ``plant_grid`` dashboard widget (#461 / #488): a newest-first list of
        active plants, each carrying its ``_key`` for a deep link to the plant detail
        view plus the per-card status fields the rich grid renders — the human-readable
        ``instance_id`` reference, the species common/scientific name (for the speaking
        card title, FIX-02 R2), cultivar name, current growth phase with its
        ``phase_definition_key`` (for the phase deep link, FIX-02 R5), location and an
        open-task marker with the earliest due date. "Alive" mirrors
        ``count_active_for_tenant`` (``removed_on == null``).

        Efficiency (no N+1): everything is resolved server-side in a *single* AQL
        round-trip. The related documents (species / cultivar / growth phase / phase
        sequence entry / location) are pulled with :func:`DOCUMENT` primary-key lookups
        (O(1) each), and the open-task marker is a correlated sub-query over the tasks
        collection filtered on the same ``tenant_key`` — so the whole enriched grid
        costs one query regardless of how many plants it returns.

        Security: the plant and task collections are bound via ``@@col`` / ``@@task_col``
        (never interpolated); the related-collection names travel as plain string binds
        to :func:`DOCUMENT`. Every plant row *and* every open-task row is filtered on
        ``… .tenant_key == @tenant_key``, and the empty-tenant sentinel is rejected
        up-front, so neither the list nor the task marker can ever span tenants (SEC-B4).
        The species join is the plant's *own* ``species_key`` (global catalog data, and
        the plant is already tenant-filtered), so it cannot leak a foreign-tenant record;
        the location label is additionally gated on the same ``tenant_key`` (defence in
        depth), mirroring ``list_active_in_phase_definition``. ``@limit`` is a bound
        integer, never interpolated.
        """
        self._require_tenant_key(tenant_key, "list_active_for_tenant")
        query = """
        FOR p IN @@col
          FILTER p.tenant_key == @tenant_key AND p.removed_on == null
          SORT p.planted_on DESC, p._key ASC
          LIMIT @limit
          LET cultivar = p.cultivar_key != null ? DOCUMENT(@cultivar_col, p.cultivar_key) : null
          LET species = p.species_key != null ? DOCUMENT(@species_col, p.species_key) : null
          LET phase = p.current_phase_key != null ? DOCUMENT(@phase_col, p.current_phase_key) : null
          // #488 FIX-02 (R5): resolve the phase-definition key for the card's phase
          // deep link. ``current_phase_key`` points at a ``PhaseSequenceEntry`` on the
          // preferred path; ``DOCUMENT`` returns null for the legacy ``GrowthPhase``
          // path (whose key lives in a different collection), leaving
          // ``phase_definition_key`` null so the chip renders without a link (A4).
          LET phase_entry = p.current_phase_key != null ? DOCUMENT(@entry_col, p.current_phase_key) : null
          LET species_common_name = (species != null AND LENGTH(species.common_names) > 0)
            ? species.common_names[0]
            : null
          LET location = p.location_key != null ? DOCUMENT(@location_col, p.location_key) : null
          LET open_task_due_dates = (
            FOR tsk IN @@task_col
              FILTER tsk.tenant_key == @tenant_key
                AND tsk.entity_type == @plant_entity_type
                AND tsk.entity_key == p._key
                AND tsk.status IN @open_statuses
              RETURN tsk.due_date
          )
          // #548 — "open task" means *due now / overdue*, consistent with the task
          // queue's bucketing and the activity plan. A task merely scheduled in the
          // future must not raise the dashboard alarm, so ``has_open_task`` only
          // counts open tasks whose due date is today-or-earlier (an undated open
          // task is always actionable). ``next_due_date`` still surfaces the earliest
          // scheduled date for glanceable "next due" info, alarm or not.
          LET due_now_task_count = LENGTH(
            FOR d IN open_task_due_dates
              FILTER d == null OR LEFT(d, 10) <= @today
              RETURN 1
          )
          LET has_open_task = due_now_task_count > 0
          RETURN {
            _key: p._key,
            instance_id: p.instance_id,
            plant_name: p.plant_name,
            species_key: p.species_key,
            species_common_name: species_common_name,
            species_scientific_name: species != null ? species.scientific_name : null,
            cultivar_key: p.cultivar_key,
            cultivar_name: cultivar != null ? cultivar.name : null,
            phase_key: p.current_phase_key,
            phase_definition_key: phase_entry != null ? phase_entry.phase_definition_key : null,
            phase_name: phase != null ? (phase.display_name != "" ? phase.display_name : phase.name) : null,
            location_key: p.location_key,
            location_name: location != null AND location.tenant_key == @tenant_key ? location.name : null,
            has_open_task: has_open_task,
            next_due_date: LENGTH(open_task_due_dates) > 0 ? MIN(open_task_due_dates) : null
          }
        """
        bind_vars = {
            "@col": self._collection_name,
            "@task_col": col.TASKS,
            "tenant_key": tenant_key,
            "limit": int(limit),
            "cultivar_col": col.CULTIVARS,
            "species_col": col.SPECIES,
            "phase_col": col.GROWTH_PHASES,
            "entry_col": col.PHASE_SEQUENCE_ENTRIES,
            "location_col": col.LOCATIONS,
            "plant_entity_type": "plant_instance",
            "open_statuses": [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value],
            "today": date.today().isoformat(),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)
