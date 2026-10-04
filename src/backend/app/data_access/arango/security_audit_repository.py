"""ArangoDB repository of the persistent security-audit log (MT-014, #2111).

Append-only: :meth:`record` inserts, nothing here updates a row. Parametrised
AQL only (NFR-006).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.query_builder import instant_prefilter_bound
from app.domain.interfaces.security_audit_repository import ISecurityAuditRepository
from app.domain.models.security_audit import SecurityAuditEntry


class ArangoSecurityAuditRepository(ISecurityAuditRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def record(self, entry: SecurityAuditEntry) -> str:
        doc = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["created_at"] = (entry.created_at or datetime.now(UTC)).isoformat()
        meta = self._db.collection(col.SECURITY_AUDIT_LOG).insert(doc)
        return str(meta["_key"])  # type: ignore[index]

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        query = """
        FOR doc IN @@collection
          FILTER @tenant_key == null OR doc.tenant_key == @tenant_key
          SORT DATE_TIMESTAMP(doc.created_at) DESC
          LIMIT @limit
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.SECURITY_AUDIT_LOG, "tenant_key": tenant_key, "limit": limit},
        )
        return [SecurityAuditEntry(**doc) for doc in cursor]  # type: ignore[arg-type, union-attr]

    def delete_expired(self, *, retention_days: int, now: datetime | None = None) -> int:
        cutoff = ((now or datetime.now(UTC)) - timedelta(days=retention_days)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.created_at < @cutoff_slack
            AND DATE_TIMESTAMP(doc.created_at) != null
            AND DATE_TIMESTAMP(doc.created_at) < DATE_TIMESTAMP(@cutoff)
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.SECURITY_AUDIT_LOG,
                "cutoff": cutoff,
                "cutoff_slack": instant_prefilter_bound(cutoff),
            },
        )
        return int(next(iter(cursor), 0))  # type: ignore[call-overload]

    def count_undated(self) -> int:
        query = """
        FOR doc IN @@collection
          FILTER DATE_TIMESTAMP(doc.created_at) == null
          COLLECT WITH COUNT INTO held
          RETURN held
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.SECURITY_AUDIT_LOG})
        return int(next(iter(cursor), 0))  # type: ignore[call-overload]
