"""v0017 — REQ-033 MCP server: ``mcp_audit_log`` + ``mcp_idempotency_record``.

Creates the two adapter-layer document collections that back the MCP server on
*existing* volumes and adds their persistent indexes (§3):

* ``mcp_audit_log`` — ``service_account_key`` + ``(tenant_key, created_at)`` +
  ``created_at`` indexes (privacy self-service lookups + 90d retention sweep);
* ``mcp_idempotency_record`` — unique ``(service_account_key, tenant_key,
  tool_name, idempotency_key)`` + ``expires_at`` (24h retention sweep). The
  ``tenant_key`` is part of the unique scope (SEC-005) so a multi-tenant service
  account can never replay tenant-A's stored result for a tenant-B call.

The MCP server keeps **no** own domain collections (§3) — it is a pure
aggregation layer over the existing services; these two collections only hold
audit metadata (hashes/sizes, never PII) and idempotency replay payloads.

Fresh databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``), which the app lifespan runs *before*
migrations; this migration brings existing volumes — and the standalone
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

_DOC_COLLECTIONS = [col.MCP_AUDIT_LOG, col.MCP_IDEMPOTENCY_RECORD]

#: ``(collection, fields, unique)`` index specifications (§3).
_INDEXES: list[tuple[str, list[str], bool]] = [
    (col.MCP_AUDIT_LOG, ["service_account_key"], False),
    (col.MCP_AUDIT_LOG, ["tenant_key", "created_at"], False),
    (col.MCP_AUDIT_LOG, ["created_at"], False),
    (col.MCP_IDEMPOTENCY_RECORD, ["service_account_key", "tenant_key", "tool_name", "idempotency_key"], True),
    (col.MCP_IDEMPOTENCY_RECORD, ["expires_at"], False),
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class McpCollectionsMigration(Migration):
    version = "0017"
    name = "mcp_collections"
    description = "Create the REQ-033 mcp_audit_log + mcp_idempotency_record collections on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        docs_missing = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]

        index_missing: list[tuple[str, list[str], bool]] = []
        for collection_name, fields, unique in _INDEXES:
            present = [] if collection_name in docs_missing else db.collection(collection_name).indexes()
            if collection_name in docs_missing or not _has_index(present, fields):
                index_missing.append((collection_name, fields, unique))

        pending = {
            "document_collections": docs_missing,
            "indexes": [f"{name}:{fields}" for name, fields, _ in index_missing],
        }
        changes = len(docs_missing) + len(index_missing)
        scanned = len(_DOC_COLLECTIONS) + len(_INDEXES)

        if dry_run:
            logger.info("mcp_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=pending
            )

        for name in docs_missing:
            db.create_collection(name)

        for collection_name, fields, unique in index_missing:
            collection = db.collection(collection_name)
            if not _has_index(collection.indexes(), fields):
                collection.add_persistent_index(fields=fields, unique=unique)

        logger.info("mcp_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=pending
        )


migration = McpCollectionsMigration()
