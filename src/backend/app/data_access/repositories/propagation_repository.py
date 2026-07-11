"""REQ-017 Propagation / lineage repository.

Owns persistence for the propagation surface: events, batches, rooting-protocol
templates and phenotype notes, plus the genetic-lineage graph traversal over the
``descended_from`` edge (child -> mother).

All collections except the global rooting-protocol *templates* are tenant-scoped.
Every query is parametrised (``bind_vars``) and, where it reads tenant data,
strictly filtered on ``tenant_key`` — never an f-string value interpolation
(SEC-B4 tenant isolation). Cross-tenant / foreign-resource reads return ``None``
(the service maps that to a 404, no existence oracle).
"""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.propagation import (
    PhenotypeNote,
    PropagationBatch,
    PropagationEvent,
    RootingProtocol,
)


class PropagationRepository:
    """Multi-collection repository for the REQ-017 propagation domain."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db
        self._events = BaseArangoRepository(db, col.PROPAGATION_EVENTS, PropagationEvent)
        self._events.is_tenant_scoped = True
        self._batches = BaseArangoRepository(db, col.PROPAGATION_BATCHES, PropagationBatch)
        self._batches.is_tenant_scoped = True
        self._protocols = BaseArangoRepository(db, col.ROOTING_PROTOCOLS, RootingProtocol)
        self._phenotypes = BaseArangoRepository(db, col.PHENOTYPE_NOTES, PhenotypeNote)
        self._phenotypes.is_tenant_scoped = True

    # ── Events ───────────────────────────────────────────────────────────────

    def create_event(self, event: PropagationEvent) -> PropagationEvent:
        return self._events.create(event)

    def get_event(self, key: str, tenant_key: str) -> PropagationEvent | None:
        """Fetch one event, scoped to ``tenant_key`` (foreign -> ``None``)."""
        event = self._events.get_by_key(key)
        if event is None or event.tenant_key != tenant_key:
            return None
        return event

    def update_event(self, key: str, event: PropagationEvent) -> PropagationEvent:
        return self._events.update(key, event)

    def list_events(
        self,
        tenant_key: str,
        *,
        method: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PropagationEvent], int]:
        filters: list[tuple[str, str, Any]] = [("tenant_key", "==", tenant_key)]
        if method:
            filters.append(("method", "==", method))
        if status:
            filters.append(("status", "==", status))
        return self._events.get_page(
            offset=offset,
            limit=limit,
            filters=filters,
            sort="created_at",
            sort_direction="DESC",
        )

    def list_events_for_plant(self, plant_key: str, tenant_key: str) -> list[PropagationEvent]:
        """Events where the plant is either a source (parent) or a result (child)."""
        query = """
        FOR e IN @@col
          FILTER e.tenant_key == @tenant_key
          FILTER @plant_key IN e.parent_plant_keys OR @plant_key IN e.child_plant_keys
          SORT e.created_at DESC
          RETURN e
        """
        bind_vars = {"@col": col.PROPAGATION_EVENTS, "tenant_key": tenant_key, "plant_key": plant_key}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PropagationEvent(**self._events._from_doc(doc)) for doc in cursor]

    def list_events_for_batch(self, batch_key: str, tenant_key: str) -> list[PropagationEvent]:
        return self._events.get_page(
            filters=[("tenant_key", "==", tenant_key), ("batch_key", "==", batch_key)],
            sort="created_at",
            sort_direction="ASC",
            limit=500,
        )[0]

    # ── Batches ──────────────────────────────────────────────────────────────

    def create_batch(self, batch: PropagationBatch) -> PropagationBatch:
        return self._batches.create(batch)

    def get_batch(self, key: str, tenant_key: str) -> PropagationBatch | None:
        batch = self._batches.get_by_key(key)
        if batch is None or batch.tenant_key != tenant_key:
            return None
        return batch

    def update_batch(self, key: str, batch: PropagationBatch) -> PropagationBatch:
        return self._batches.update(key, batch)

    def list_batches(
        self,
        tenant_key: str,
        *,
        status: str | None = None,
        method: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PropagationBatch], int]:
        filters: list[tuple[str, str, Any]] = [("tenant_key", "==", tenant_key)]
        if status:
            filters.append(("status", "==", status))
        if method:
            filters.append(("method", "==", method))
        return self._batches.get_page(
            offset=offset,
            limit=limit,
            filters=filters,
            sort="created_at",
            sort_direction="DESC",
        )

    # ── Rooting protocols (global templates + tenant-owned) ──────────────────

    def create_protocol(self, protocol: RootingProtocol) -> RootingProtocol:
        return self._protocols.create(protocol)

    def get_protocol(self, key: str, tenant_key: str) -> RootingProtocol | None:
        """Fetch a protocol visible to ``tenant_key`` (own or global template)."""
        protocol = self._protocols.get_by_key(key)
        if protocol is None:
            return None
        if protocol.tenant_key not in ("", tenant_key):
            return None
        return protocol

    def update_protocol(self, key: str, protocol: RootingProtocol) -> RootingProtocol:
        return self._protocols.update(key, protocol)

    def delete_protocol(self, key: str) -> bool:
        return self._protocols.delete(key)

    def list_protocols(
        self,
        tenant_key: str,
        *,
        method: str | None = None,
        is_template: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[RootingProtocol], int]:
        """Union of global templates (``tenant_key == ""``) and the tenant's own."""
        query = """
        FOR p IN @@col
          FILTER p.tenant_key == "" OR p.tenant_key == @tenant_key
          FILTER @method == null OR p.method == @method
          FILTER @is_template == null OR p.is_template == @is_template
          SORT p.name ASC
          LIMIT @offset, @limit
          RETURN p
        """
        bind_vars = {
            "@col": col.ROOTING_PROTOCOLS,
            "tenant_key": tenant_key,
            "method": method,
            "is_template": is_template,
            "offset": int(offset),
            "limit": int(limit),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [RootingProtocol(**self._protocols._from_doc(doc)) for doc in cursor]

        count_query = """
        RETURN LENGTH(
          FOR p IN @@col
            FILTER p.tenant_key == "" OR p.tenant_key == @tenant_key
            FILTER @method == null OR p.method == @method
            FILTER @is_template == null OR p.is_template == @is_template
            RETURN 1
        )
        """
        count_vars = {
            "@col": col.ROOTING_PROTOCOLS,
            "tenant_key": tenant_key,
            "method": method,
            "is_template": is_template,
        }
        total = next(self._db.aql.execute(count_query, bind_vars=count_vars), 0)
        return items, total

    def protocol_in_use(self, protocol_key: str, tenant_key: str) -> bool:
        """Whether any of the tenant's events reference this protocol."""
        query = """
        FOR e IN @@col
          FILTER e.tenant_key == @tenant_key AND e.protocol_key == @protocol_key
          LIMIT 1
          RETURN 1
        """
        bind_vars = {"@col": col.PROPAGATION_EVENTS, "tenant_key": tenant_key, "protocol_key": protocol_key}
        return next(self._db.aql.execute(query, bind_vars=bind_vars), None) is not None

    # ── Phenotype notes ──────────────────────────────────────────────────────

    def create_phenotype(self, note: PhenotypeNote) -> PhenotypeNote:
        return self._phenotypes.create(note)

    def list_phenotypes_for_plant(self, plant_key: str, tenant_key: str) -> list[PhenotypeNote]:
        return self._phenotypes.get_page(
            filters=[("tenant_key", "==", tenant_key), ("plant_key", "==", plant_key)],
            sort="created_at",
            sort_direction="DESC",
            limit=500,
        )[0]

    def get_phenotype(self, key: str, tenant_key: str) -> PhenotypeNote | None:
        note = self._phenotypes.get_by_key(key)
        if note is None or note.tenant_key != tenant_key:
            return None
        return note

    def delete_phenotype(self, key: str) -> bool:
        return self._phenotypes.delete(key)

    # ── Lineage graph traversal (descended_from: child -> mother) ─────────────

    def get_plant(self, key: str, tenant_key: str) -> PlantInstance | None:
        """Fetch a plant instance scoped to ``tenant_key`` (foreign -> ``None``)."""
        doc = self.get_plant_raw(key, tenant_key)
        if doc is None:
            return None
        return PlantInstance(**doc)

    def get_plant_raw(self, key: str, tenant_key: str) -> dict[str, Any] | None:
        """Raw plant document scoped to ``tenant_key`` (keeps denormalized mother flags)."""
        doc = self._db.collection(col.PLANT_INSTANCES).get(key)
        if doc is None or doc.get("tenant_key") != tenant_key:
            return None
        return self._events._from_doc(doc)

    def trace_ancestor_paths(self, plant_key: str, tenant_key: str, max_depth: int) -> list[list[str]]:
        """Return ancestor chains as key-lists (immediate parent -> root).

        Traverses ``descended_from`` outbound from the plant. ``uniqueVertices:
        'path'`` plus the ``max_depth`` cap guarantee termination even if the data
        contains a cycle (Zyklus-Schutz). Only vertices of ``tenant_key`` are
        followed. Each returned list excludes the starting plant and holds the
        ancestor keys ordered from nearest to furthest.
        """
        query = """
        FOR v, e, p IN 1..@max_depth OUTBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge], uniqueVertices: "path", bfs: false}
          FILTER v.tenant_key == @tenant_key
          RETURN p.vertices[* FILTER CURRENT._key != @plant_key]._key
        """
        bind_vars = {
            "start": f"{col.PLANT_INSTANCES}/{plant_key}",
            "edge": col.DESCENDED_FROM,
            "tenant_key": tenant_key,
            "plant_key": plant_key,
            "max_depth": int(max_depth),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        all_paths: list[list[str]] = [list(row) for row in cursor if row]
        # Keep only maximal chains: drop any path that is a prefix of a longer one.
        maximal: list[list[str]] = []
        for path in sorted(all_paths, key=len, reverse=True):
            if not any(longer[: len(path)] == path for longer in maximal):
                maximal.append(path)
        return maximal

    def list_ancestors(self, plant_key: str, tenant_key: str, max_depth: int) -> list[PlantInstance]:
        """Flat, de-duplicated ancestor list (nearest first)."""
        query = """
        FOR v IN 1..@max_depth OUTBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge], uniqueVertices: "global", bfs: true}
          FILTER v.tenant_key == @tenant_key
          RETURN v
        """
        bind_vars = {
            "start": f"{col.PLANT_INSTANCES}/{plant_key}",
            "edge": col.DESCENDED_FROM,
            "tenant_key": tenant_key,
            "max_depth": int(max_depth),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantInstance(**self._events._from_doc(doc)) for doc in cursor]

    def list_descendants(self, plant_key: str, tenant_key: str, max_depth: int) -> list[PlantInstance]:
        """Flat, de-duplicated descendant list (clone tree, nearest first)."""
        query = """
        FOR v IN 1..@max_depth INBOUND @start GRAPH 'kamerplanter_graph'
          OPTIONS {edgeCollections: [@edge], uniqueVertices: "global", bfs: true}
          FILTER v.tenant_key == @tenant_key
          RETURN v
        """
        bind_vars = {
            "start": f"{col.PLANT_INSTANCES}/{plant_key}",
            "edge": col.DESCENDED_FROM,
            "tenant_key": tenant_key,
            "max_depth": int(max_depth),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantInstance(**self._events._from_doc(doc)) for doc in cursor]

    # ── Mothers ──────────────────────────────────────────────────────────────

    def list_mothers(self, tenant_key: str, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """Raw plant documents flagged as mother plants (``is_mother == true``)."""
        query = """
        FOR p IN @@col
          FILTER p.tenant_key == @tenant_key AND p.is_mother == true
          SORT p.created_at DESC
          LIMIT @offset, @limit
          RETURN p
        """
        bind_vars = {
            "@col": col.PLANT_INSTANCES,
            "tenant_key": tenant_key,
            "offset": int(offset),
            "limit": int(limit),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._events._from_doc(doc) for doc in cursor]

    def update_plant_fields(self, plant_key: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Patch a small set of scalar fields on a plant instance (mother flags)."""
        result = self._db.collection(col.PLANT_INSTANCES).update(
            {"_key": plant_key, **fields}, return_new=True, keep_none=False
        )
        return self._events._from_doc(result["new"])

    # ── Statistics ───────────────────────────────────────────────────────────

    def stats(self, tenant_key: str, group_by: str) -> list[dict[str, Any]]:
        """Success-rate aggregation grouped by ``method`` / ``species`` / ``protocol``.

        ``group_by`` is a code-level whitelist key, mapped to a document field
        here; it is never taken from client input verbatim.
        """
        field_map = {
            "method": "method",
            "species": "species_key",
            "protocol": "protocol_key",
            "cultivar": "cultivar_key",
        }
        field = field_map[group_by]
        query = """
        FOR e IN @@col
          FILTER e.tenant_key == @tenant_key
          COLLECT bucket = e.@field INTO group
          LET total_qty = SUM(group[*].e.quantity)
          LET total_survived = SUM(group[*].e.survived_count)
          RETURN {
            key: bucket,
            event_count: LENGTH(group),
            total_quantity: total_qty,
            total_survived: total_survived,
            success_rate: total_qty > 0 ? (total_survived / total_qty) : null
          }
        """
        bind_vars = {"@col": col.PROPAGATION_EVENTS, "tenant_key": tenant_key, "field": field}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)
