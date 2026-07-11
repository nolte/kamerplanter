"""v0012 — REQ-037: ``irrigation_demands`` collection + edges.

Creates the document collection ``irrigation_demands`` and the two edge collections
``has_irrigation_demand`` (sites → irrigation_demands) and ``demand_for_run``
(planting_runs → irrigation_demands) on *existing* volumes, adds the unique
``(tenant_key, site_key, run_key, demand_date)`` index and wires both edges into the
named graph ``kamerplanter_graph``.

Fresh databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``), which the app lifespan runs *before*
migrations. This migration brings existing volumes — and the standalone
``python -m app.migrations`` path, which does not call ``ensure_collections`` — to
the same shape.

Purely additive and idempotent (M-3): every step checks for existence first, so a
re-run (or a fresh DB that was already bootstrapped) is a no-op (``changed == 0``).
No data is read or rewritten. Irreversible (M-6): dropping a collection that the
bootstrap also creates would not honestly restore the pre-migration state, so no
inverse is offered.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_INDEX_FIELDS: list[str] = ["tenant_key", "site_key", "run_key", "demand_date"]

_EDGE_DEFINITIONS = [
    {
        "edge_collection": col.HAS_IRRIGATION_DEMAND,
        "from_vertex_collections": [col.SITES],
        "to_vertex_collections": [col.IRRIGATION_DEMANDS],
    },
    {
        "edge_collection": col.DEMAND_FOR_RUN,
        "from_vertex_collections": [col.PLANTING_RUNS],
        "to_vertex_collections": [col.IRRIGATION_DEMANDS],
    },
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class IrrigationDemandsCollectionMigration(Migration):
    version = "0012"
    name = "irrigation_demands_collection"
    description = "Create the REQ-037 irrigation_demands collection + edges on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        doc_missing = not db.has_collection(col.IRRIGATION_DEMANDS)
        has_edge_missing = not db.has_collection(col.HAS_IRRIGATION_DEMAND)
        run_edge_missing = not db.has_collection(col.DEMAND_FOR_RUN)
        index_missing = doc_missing or not _has_index(db.collection(col.IRRIGATION_DEMANDS).indexes(), _INDEX_FIELDS)

        all_edges = [ed["edge_collection"] for ed in _EDGE_DEFINITIONS]
        graph_edges_missing: list[str] = list(all_edges)
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edges_missing = [name for name in all_edges if name not in existing]

        pending = {
            "document_collection": doc_missing,
            "has_irrigation_demand_edge": has_edge_missing,
            "demand_for_run_edge": run_edge_missing,
            "index": index_missing,
            "graph_edges": bool(graph_edges_missing),
        }
        changes = sum(1 for is_pending in pending.values() if is_pending)

        if dry_run:
            logger.info("irrigation_demands_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(pending),
                changed=0,
                dry_run=True,
                details=pending,
            )

        if doc_missing:
            db.create_collection(col.IRRIGATION_DEMANDS)
        if has_edge_missing:
            db.create_collection(col.HAS_IRRIGATION_DEMAND, edge=True)
        if run_edge_missing:
            db.create_collection(col.DEMAND_FOR_RUN, edge=True)

        collection = db.collection(col.IRRIGATION_DEMANDS)
        if not _has_index(collection.indexes(), _INDEX_FIELDS):
            collection.add_persistent_index(fields=_INDEX_FIELDS, unique=True)

        if db.has_graph(col.GRAPH_NAME):
            graph = db.graph(col.GRAPH_NAME)
            existing = {ed["edge_collection"] for ed in graph.edge_definitions()}
            for definition in _EDGE_DEFINITIONS:
                if definition["edge_collection"] not in existing:
                    graph.create_edge_definition(**definition)

        logger.info("irrigation_demands_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(pending),
            changed=changes,
            dry_run=False,
            details=pending,
        )


migration = IrrigationDemandsCollectionMigration()
