"""v0017 — REQ-017 propagation / lineage: collections + indexes.

Creates the three REQ-017 document collections on *existing* volumes:
``propagation_batches``, ``rooting_protocols`` and ``phenotype_notes`` (the
``propagation_events`` collection and the ``descended_from`` edge already exist
from the D10 groundwork). Adds the tenant-scoped read indexes.

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
    col.PROPAGATION_BATCHES,
    col.ROOTING_PROTOCOLS,
    col.PHENOTYPE_NOTES,
]

#: (collection, index-fields) pairs applied after creation (additive, idempotent).
_INDEXES: list[tuple[str, list[str]]] = [
    (col.PROPAGATION_EVENTS, ["tenant_key", "batch_key"]),
    (col.PROPAGATION_EVENTS, ["tenant_key", "species_key"]),
    (col.PROPAGATION_BATCHES, ["tenant_key", "status"]),
    (col.ROOTING_PROTOCOLS, ["tenant_key", "method"]),
    (col.PHENOTYPE_NOTES, ["tenant_key", "plant_key"]),
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class PropagationCollectionsMigration(Migration):
    version = "0017"
    name = "propagation_collections"
    description = "Create the REQ-017 propagation_batches / rooting_protocols / phenotype_notes collections + indexes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        docs_missing = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]
        indexes_missing = [
            (name, fields)
            for name, fields in _INDEXES
            if not db.has_collection(name) or not _has_index(db.collection(name).indexes(), fields)
        ]

        pending = {
            "document_collections": docs_missing,
            "indexes": [f"{name}:{'+'.join(fields)}" for name, fields in indexes_missing],
        }
        changes = len(docs_missing) + len(indexes_missing)

        if dry_run:
            logger.info("propagation_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=len(_DOC_COLLECTIONS) + len(_INDEXES),
                changed=0,
                dry_run=True,
                details=pending,
            )

        for name in docs_missing:
            db.create_collection(name)

        for name, fields in _INDEXES:
            collection = db.collection(name)
            if not _has_index(collection.indexes(), fields):
                collection.add_persistent_index(fields=fields, unique=False)

        logger.info("propagation_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(_DOC_COLLECTIONS) + len(_INDEXES),
            changed=changes,
            dry_run=False,
            details=pending,
        )


migration = PropagationCollectionsMigration()
