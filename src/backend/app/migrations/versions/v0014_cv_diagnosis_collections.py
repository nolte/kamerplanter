"""v0014 — REQ-038 CV disease diagnosis: collection + 4 edges.

Creates the document collection ``plant_diagnosis_requests`` and the four edge
collections (``cv_diagnosed_for``, ``cv_diagnosis_found``,
``cv_attached_to_inspection``, ``cv_phenotype_of``) on *existing* volumes, adds
the ``(tenant_key, user_key, created_at)`` history index and wires the edges into
the named graph ``kamerplanter_graph``.

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

_INDEX_FIELDS: list[str] = ["tenant_key", "user_key", "created_at"]

_EDGE_COLLECTIONS = [
    col.CV_DIAGNOSED_FOR,
    col.CV_DIAGNOSIS_FOUND,
    col.CV_ATTACHED_TO_INSPECTION,
    col.CV_PHENOTYPE_OF,
]

_EDGE_DEFINITIONS = [
    {
        "edge_collection": col.CV_DIAGNOSED_FOR,
        "from_vertex_collections": [col.PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [col.PLANT_INSTANCES, col.PLANTING_RUNS],
    },
    {
        "edge_collection": col.CV_DIAGNOSIS_FOUND,
        "from_vertex_collections": [col.PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [col.DISEASES, col.PESTS],
    },
    {
        "edge_collection": col.CV_ATTACHED_TO_INSPECTION,
        "from_vertex_collections": [col.PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [col.INSPECTIONS],
    },
    {
        "edge_collection": col.CV_PHENOTYPE_OF,
        "from_vertex_collections": [col.PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [col.HARVEST_OBSERVATIONS],
    },
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class CvDiagnosisCollectionsMigration(Migration):
    version = "0014"
    name = "cv_diagnosis_collections"
    description = "Create the REQ-038 plant_diagnosis_requests collection + 4 CV-diagnosis edges on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        doc_missing = not db.has_collection(col.PLANT_DIAGNOSIS_REQUESTS)
        edges_missing = [name for name in _EDGE_COLLECTIONS if not db.has_collection(name)]
        index_missing = doc_missing or not _has_index(
            db.collection(col.PLANT_DIAGNOSIS_REQUESTS).indexes(), _INDEX_FIELDS
        )
        graph_edges_missing: list[str] = []
        if db.has_graph(col.GRAPH_NAME):
            existing = {ed["edge_collection"] for ed in db.graph(col.GRAPH_NAME).edge_definitions()}
            graph_edges_missing = [
                d["edge_collection"] for d in _EDGE_DEFINITIONS if d["edge_collection"] not in existing
            ]
        else:
            graph_edges_missing = [d["edge_collection"] for d in _EDGE_DEFINITIONS]

        pending = {
            "document_collection": doc_missing,
            "edge_collections": edges_missing,
            "index": index_missing,
            "graph_edges": graph_edges_missing,
        }
        changes = int(doc_missing) + len(edges_missing) + int(index_missing) + len(graph_edges_missing)

        if dry_run:
            logger.info("cv_diagnosis_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(_EDGE_COLLECTIONS) + 2,
                changed=0,
                dry_run=True,
                details=pending,
            )

        if doc_missing:
            db.create_collection(col.PLANT_DIAGNOSIS_REQUESTS)
        for name in edges_missing:
            db.create_collection(name, edge=True)

        collection = db.collection(col.PLANT_DIAGNOSIS_REQUESTS)
        if not _has_index(collection.indexes(), _INDEX_FIELDS):
            collection.add_persistent_index(fields=_INDEX_FIELDS, unique=False)

        if db.has_graph(col.GRAPH_NAME):
            graph = db.graph(col.GRAPH_NAME)
            for definition in _EDGE_DEFINITIONS:
                if definition["edge_collection"] in graph_edges_missing:
                    graph.create_edge_definition(**definition)

        logger.info("cv_diagnosis_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(_EDGE_COLLECTIONS) + 2,
            changed=changes,
            dry_run=False,
            details=pending,
        )


migration = CvDiagnosisCollectionsMigration()
