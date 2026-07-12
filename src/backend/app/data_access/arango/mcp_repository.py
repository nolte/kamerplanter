"""ArangoDB repositories for the REQ-033 MCP adapter-layer collections.

Two small repositories back the audit log and the idempotency store. Both use
parametrised AQL (bind_vars only — never f-strings) to stay injection-safe
(NFR-006), and both are scoped by ``service_account_key``/``tenant_key`` so an
MCP caller can never read another account's records (AC-S1).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.models.mcp import McpAuditLog, McpAuditLogEntry, McpIdempotencyRecord


class ArangoMcpAuditRepository:
    """Append-only audit log for MCP tool calls (§4.6)."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def record(self, entry: McpAuditLog) -> str:
        doc = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        if not doc.get("created_at"):
            doc["created_at"] = datetime.now(UTC).isoformat()
        meta = self._db.collection(col.MCP_AUDIT_LOG).insert(doc)
        return str(meta["_key"])

    def list_for_service_account(
        self,
        service_account_key: str,
        *,
        limit: int = 100,
    ) -> list[McpAuditLogEntry]:
        """Return the most recent audit entries for a single service account."""

        query = """
        FOR doc IN @@collection
          FILTER doc.service_account_key == @sa_key
          SORT doc.created_at DESC
          LIMIT @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MCP_AUDIT_LOG,
                "sa_key": service_account_key,
                "limit": limit,
            },
        )
        return [McpAuditLogEntry(**doc) for doc in cursor]

    def list_for_user_accounts(
        self,
        service_account_keys: list[str],
        *,
        limit: int = 200,
    ) -> list[McpAuditLogEntry]:
        """Return recent audit entries across a user's service accounts (§4.6)."""

        if not service_account_keys:
            return []
        query = """
        FOR doc IN @@collection
          FILTER doc.service_account_key IN @sa_keys
          SORT doc.created_at DESC
          LIMIT @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MCP_AUDIT_LOG,
                "sa_keys": service_account_keys,
                "limit": limit,
            },
        )
        return [McpAuditLogEntry(**doc) for doc in cursor]

    def delete_expired(self, *, retention_days: int = 90) -> int:
        """Delete audit entries older than the retention window (NFR-011, AC-S4)."""

        cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.created_at < @cutoff
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.MCP_AUDIT_LOG, "cutoff": cutoff},
        )
        result = list(cursor)
        return int(result[0]) if result else 0


class ArangoMcpIdempotencyRepository:
    """ArangoDB-backed idempotency store for MCP write tools (§2.6, §3)."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _doc_key(service_account_key: str, tool_name: str, idempotency_key: str) -> str:
        # Deterministic, ASCII-safe document key. ArangoDB keys allow a limited
        # charset, so hash the composite to avoid rejecting arbitrary
        # client-supplied idempotency keys.
        import hashlib

        raw = f"{service_account_key}:{tool_name}:{idempotency_key}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(
        self,
        service_account_key: str,
        tool_name: str,
        idempotency_key: str,
    ) -> McpIdempotencyRecord | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.service_account_key == @sa_key
             AND doc.tool_name == @tool
             AND doc.idempotency_key == @idem
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MCP_IDEMPOTENCY_RECORD,
                "sa_key": service_account_key,
                "tool": tool_name,
                "idem": idempotency_key,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return McpIdempotencyRecord(**docs[0])

    def store(self, record: McpIdempotencyRecord, *, ttl_hours: int = 24) -> McpIdempotencyRecord:
        now = datetime.now(UTC)
        record.created_at = record.created_at or now
        record.expires_at = record.expires_at or (now + timedelta(hours=ttl_hours))
        doc = record.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc["_key"] = self._doc_key(record.service_account_key, record.tool_name, record.idempotency_key)
        self._db.collection(col.MCP_IDEMPOTENCY_RECORD).insert(doc, overwrite=True)
        return record

    def delete_expired(self) -> int:
        """Delete idempotency records past their TTL (AC-22)."""

        now = datetime.now(UTC).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.expires_at < @now
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.MCP_IDEMPOTENCY_RECORD, "now": now},
        )
        result = list(cursor)
        return int(result[0]) if result else 0
