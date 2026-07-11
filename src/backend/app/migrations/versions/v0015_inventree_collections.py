"""v0015 — REQ-016 InvenTree integration: 4 collections + 3 edges.

Creates the tenant-scoped document collections ``inventree_connections``,
``inventree_references``, ``stock_transactions`` and ``equipment`` plus the three
edge collections (``has_inventree_ref``, ``has_stock_transaction``,
``equipment_at``) on *existing* volumes, adds the tenant-scoped persistent
indexes and wires the edges into the named graph ``kamerplanter_graph``.

Fresh databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``). This migration brings existing
volumes — and the standalone ``python -m app.migrations`` path — to the same
shape. Purely additive and idempotent (M-3): every step checks for existence
first, so a re-run is a no-op (``changed == 0``). No data is read or rewritten.
Irreversible (M-6).
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_DOC_COLLECTIONS = [
    col.INVENTREE_CONNECTIONS,
    col.INVENTREE_REFERENCES,
    col.STOCK_TRANSACTIONS,
    col.EQUIPMENT,
]

_EDGE_COLLECTIONS = [
    col.HAS_INVENTREE_REF,
    col.HAS_STOCK_TRANSACTION,
    col.EQUIPMENT_AT,
]

_INDEXES: dict[str, list[list[str]]] = {
    col.INVENTREE_CONNECTIONS: [["tenant_key"]],
    col.INVENTREE_REFERENCES: [["tenant_key", "entity_collection", "entity_key"]],
    col.STOCK_TRANSACTIONS: [["tenant_key", "status", "created_at"], ["reference_key"]],
    col.EQUIPMENT: [["tenant_key", "equipment_type", "status"]],
}

_EDGE_DEFINITIONS = [
    {
        "edge_collection": col.HAS_INVENTREE_REF,
        "from_vertex_collections": [col.FERTILIZERS, col.TANKS, col.EQUIPMENT],
        "to_vertex_collections": [col.INVENTREE_REFERENCES],
    },
    {
        "edge_collection": col.HAS_STOCK_TRANSACTION,
        "from_vertex_collections": [col.INVENTREE_REFERENCES],
        "to_vertex_collections": [col.STOCK_TRANSACTIONS],
    },
    {
        "edge_collection": col.EQUIPMENT_AT,
        "from_vertex_collections": [col.EQUIPMENT],
        "to_vertex_collections": [col.LOCATIONS],
    },
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class InvenTreeCollectionsMigration(Migration):
    version = "0015"
    name = "inventree_collections"
    description = "Create the REQ-016 InvenTree collections + 3 edges on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        docs_missing = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]
        edges_missing = [name for name in _EDGE_COLLECTIONS if not db.has_collection(name)]

        index_missing: list[tuple[str, list[str]]] = []
        for collection_name, index_specs in _INDEXES.items():
            present_indexes = [] if collection_name in docs_missing else db.collection(collection_name).indexes()
            for fields in index_specs:
                if collection_name in docs_missing or not _has_index(present_indexes, fields):
                    index_missing.append((collection_name, fields))

        graph_edges_missing: list[str] = []
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edges_missing = [
                d["edge_collection"] for d in _EDGE_DEFINITIONS if d["edge_collection"] not in existing
            ]
        else:
            graph_edges_missing = [d["edge_collection"] for d in _EDGE_DEFINITIONS]

        pending = {
            "document_collections": docs_missing,
            "edge_collections": edges_missing,
            "indexes": [f"{name}:{fields}" for name, fields in index_missing],
            "graph_edges": graph_edges_missing,
        }
        changes = len(docs_missing) + len(edges_missing) + len(index_missing) + len(graph_edges_missing)
        scanned = len(_DOC_COLLECTIONS) + len(_EDGE_COLLECTIONS)

        if dry_run:
            logger.info("inventree_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=pending
            )

        for name in docs_missing:
            db.create_collection(name)
        for name in edges_missing:
            db.create_collection(name, edge=True)

        for collection_name, fields in index_missing:
            collection = db.collection(collection_name)
            if not _has_index(collection.indexes(), fields):
                collection.add_persistent_index(fields=fields, unique=False)

        if db.has_graph(col.GRAPH_NAME):
            graph = db.graph(col.GRAPH_NAME)
            for definition in _EDGE_DEFINITIONS:
                if definition["edge_collection"] in graph_edges_missing:
                    graph.create_edge_definition(**definition)

        logger.info("inventree_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=pending
        )


migration = InvenTreeCollectionsMigration()
