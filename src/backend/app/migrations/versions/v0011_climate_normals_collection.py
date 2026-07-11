"""v0011 — REQ-041 NASA POWER: ``climate_normals`` collection + edge.

Creates the document collection ``climate_normals`` and the edge collection
``has_climate_normal`` (sites → climate_normals) on *existing* volumes, adds the
unique ``(tenant_key, site_key, source)`` index and wires the edge into the named
graph ``kamerplanter_graph``.

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

_INDEX_FIELDS: list[str] = ["tenant_key", "site_key", "source"]

_EDGE_DEFINITION = {
    "edge_collection": col.HAS_CLIMATE_NORMAL,
    "from_vertex_collections": [col.SITES],
    "to_vertex_collections": [col.CLIMATE_NORMALS],
}


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class ClimateNormalsCollectionMigration(Migration):
    version = "0011"
    name = "climate_normals_collection"
    description = "Create the REQ-041 climate_normals collection + has_climate_normal edge on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        doc_missing = not db.has_collection(col.CLIMATE_NORMALS)
        edge_missing = not db.has_collection(col.HAS_CLIMATE_NORMAL)
        index_missing = doc_missing or not _has_index(db.collection(col.CLIMATE_NORMALS).indexes(), _INDEX_FIELDS)
        graph_edge_missing = True
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edge_missing = col.HAS_CLIMATE_NORMAL not in existing

        pending = {
            "document_collection": doc_missing,
            "edge_collection": edge_missing,
            "index": index_missing,
            "graph_edge": graph_edge_missing,
        }
        changes = sum(1 for is_pending in pending.values() if is_pending)

        if dry_run:
            logger.info("climate_normals_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(pending),
                changed=0,
                dry_run=True,
                details=pending,
            )

        if doc_missing:
            db.create_collection(col.CLIMATE_NORMALS)
        if edge_missing:
            db.create_collection(col.HAS_CLIMATE_NORMAL, edge=True)

        collection = db.collection(col.CLIMATE_NORMALS)
        if not _has_index(collection.indexes(), _INDEX_FIELDS):
            collection.add_persistent_index(fields=_INDEX_FIELDS, unique=True)

        if db.has_graph(col.GRAPH_NAME) and graph_edge_missing:
            db.graph(col.GRAPH_NAME).create_edge_definition(**_EDGE_DEFINITION)

        logger.info("climate_normals_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(pending),
            changed=changes,
            dry_run=False,
            details=pending,
        )


migration = ClimateNormalsCollectionMigration()
