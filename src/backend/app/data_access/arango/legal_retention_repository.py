"""ArangoDB purge of the rows a tenant deletion keeps for NFR-011 R-16..R-18, and of its proof (R-06a).

#1789: harvest, treatment and inspection rows survive a tenant deletion
pseudonymised (``TenantErasureEngine.INVENTORY``) and nothing removed them once
their legal period had run out. #1793: the ``tenant_erasure_records`` proof had
no period at all. Collection names come off the rule the caller passes; only the
two collections every rule is checked against (``tenants``,
``tenant_erasure_records``) are named here.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import structlog
from arango.database import StandardDatabase, TransactionDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.legal_retention_repository import ILegalRetentionRepository
from app.domain.models.legal_retention import LegalRetentionPurgeCount, LegalRetentionRule

logger = structlog.get_logger()

# A destructive selector by age: a row without a readable instant is excluded
# (NFR-011 §3.2), and both sides are compared as instants, never as strings.
# ``tenant_key`` must name *no* tenant: the rows of a living tenant are its own
# records and not retention residue (#1789, the narrower reading).
_SELECT_EXPIRED = """
FOR doc IN @@collection
  FILTER IS_STRING(doc.tenant_key) AND doc.tenant_key != ""
  LET happened = NOT_NULL(DATE_TIMESTAMP(doc[@date_field]), DATE_TIMESTAMP(doc[@fallback_field]))
  FILTER happened != null AND happened < DATE_TIMESTAMP(@cutoff)
  FILTER LENGTH(FOR tenant IN @@tenants FILTER tenant._key == doc.tenant_key LIMIT 1 RETURN 1) == 0
  LIMIT @batch
  RETURN {id: doc._id, key: doc._key}
"""

_SELECT_CHILDREN = """
FOR doc IN @@collection
  FILTER doc[@parent_field] IN @parent_keys
  RETURN {id: doc._id, key: doc._key}
"""

_REMOVE_BY_KEYS = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_REMOVE_EDGES = """
FOR edge IN @@collection
  FILTER edge._from IN @ids OR edge._to IN @ids
  REMOVE edge IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

# ``{remaining}`` is filled with one ``LENGTH(FOR …)`` term per retained
# collection, each bound as its own ``@@retainedN`` — never with a value.
_REMOVE_EXPIRED_RECORDS = """
FOR rec IN @@records
  FILTER rec.status == "completed"
  LET done = DATE_TIMESTAMP(rec.completed_at)
  FILTER done != null
  LET capped = done < DATE_TIMESTAMP(@cap_before)
  LET kept_rows = LENGTH(
    FOR outcome IN (IS_ARRAY(rec.outcomes) ? rec.outcomes : [])
      FILTER outcome.collection IN @retained AND outcome.matched > 0
      RETURN 1
  ) > 0
  FILTER capped OR (kept_rows AND ({remaining}) == 0)
  REMOVE rec IN @@records
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_REMAINING_TERM = "LENGTH(FOR row IN @@retained{index} FILTER row.tenant_key == rec.tenant_key LIMIT 1 RETURN 1)"


class ArangoLegalRetentionRepository(ILegalRetentionRepository):
    """Runs the R-16..R-18 and R-06a purges; see :class:`ILegalRetentionRepository`."""

    #: Rows of one rule purged per transaction (SEC-003).
    BATCH_SIZE = 500

    def __init__(self, db: StandardDatabase, *, batch_size: int | None = None) -> None:
        self._db = db
        self._batch_size = batch_size or self.BATCH_SIZE

    def delete_expired_rows_of_deleted_tenants(
        self, rule: LegalRetentionRule, *, cutoff_iso: str
    ) -> LegalRetentionPurgeCount:
        """Purge in batches of :attr:`BATCH_SIZE` rows, one transaction each (security review SEC-003).

        A deleted tenant with years of harvests would otherwise put every row,
        child and edge into one stream transaction, which could outgrow the
        server's transaction limits and abort every night. Each batch is still
        atomic for a row together with its children and edges.
        """
        existing = {c["name"]: c for c in self._db.collections() if not c["system"]}
        if rule.collection not in existing:
            return LegalRetentionPurgeCount()
        total = LegalRetentionPurgeCount()
        while True:
            batch, selected = self._purge_batch(rule, cutoff_iso, existing)
            total.rows += batch.rows
            total.children += batch.children
            total.edges += batch.edges
            # A full batch may have left more behind; a batch that removed
            # nothing it selected must not spin.
            if selected < self._batch_size or batch.rows == 0:
                return total

    def _purge_batch(
        self, rule: LegalRetentionRule, cutoff_iso: str, existing: dict[str, Any]
    ) -> tuple[LegalRetentionPurgeCount, int]:
        children = [child for child in rule.children if child.collection in existing]
        edge_collections = sorted(name for name, info in existing.items() if info["type"] == "edge")
        writes = [rule.collection, *(child.collection for child in children), *edge_collections]
        reads = [col.TENANTS] if col.TENANTS in existing else []

        count = LegalRetentionPurgeCount()
        transaction = self._db.begin_transaction(read=reads, write=writes, allow_implicit=False)
        try:
            rows = [
                dict(row)
                for row in transaction.aql.execute(
                    _SELECT_EXPIRED,
                    bind_vars={
                        "@collection": rule.collection,
                        "@tenants": col.TENANTS,
                        "date_field": rule.date_field,
                        "fallback_field": rule.fallback_date_field or rule.date_field,
                        "cutoff": cutoff_iso,
                        "batch": self._batch_size,
                    },
                )
            ]
            if not rows:
                transaction.commit_transaction()
                return count, 0
            row_keys = [row["key"] for row in rows]
            doomed_ids = [row["id"] for row in rows]
            child_keys: dict[str, list[str]] = {}
            for child in children:
                found = [
                    dict(row)
                    for row in transaction.aql.execute(
                        _SELECT_CHILDREN,
                        bind_vars={
                            "@collection": child.collection,
                            "parent_field": child.parent_field,
                            "parent_keys": row_keys,
                        },
                    )
                ]
                child_keys[child.collection] = [row["key"] for row in found]
                doomed_ids.extend(row["id"] for row in found)

            for edge_collection in edge_collections:
                count.edges += self._counted(
                    transaction.aql.execute(
                        _REMOVE_EDGES, bind_vars={"@collection": edge_collection, "ids": doomed_ids}
                    )
                )
            for collection, keys in child_keys.items():
                if keys:
                    count.children += self._counted(
                        transaction.aql.execute(_REMOVE_BY_KEYS, bind_vars={"@collection": collection, "keys": keys})
                    )
            count.rows = self._counted(
                transaction.aql.execute(_REMOVE_BY_KEYS, bind_vars={"@collection": rule.collection, "keys": row_keys})
            )
            transaction.commit_transaction()
        except BaseException:
            self._abort_quietly(transaction)
            raise
        return count, len(rows)

    def delete_expired_tenant_erasure_records(self, *, cap_before_iso: str, retained_collections: Sequence[str]) -> int:
        existing = {c["name"] for c in self._db.collections() if not c["system"]}
        if col.TENANT_ERASURE_RECORDS not in existing:
            return 0
        present = [name for name in retained_collections if name in existing]
        # A retained collection the database does not have holds no row of anyone.
        remaining = " + ".join(_REMAINING_TERM.format(index=i) for i in range(len(present))) or "0"
        bind_vars: dict[str, Any] = {
            "@records": col.TENANT_ERASURE_RECORDS,
            "cap_before": cap_before_iso,
            "retained": list(retained_collections),
        }
        bind_vars.update({f"@retained{i}": name for i, name in enumerate(present)})
        cursor = self._db.aql.execute(_REMOVE_EXPIRED_RECORDS.format(remaining=remaining), bind_vars=bind_vars)
        return self._counted(cursor)

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _counted(cursor: Any) -> int:
        return int(next(iter(cursor), 0))

    @staticmethod
    def _abort_quietly(transaction: TransactionDatabase) -> None:
        try:
            transaction.abort_transaction()
        except Exception as exc:  # noqa: BLE001 — the primary error is the one to raise
            logger.warning("legal_retention.transaction_abort_failed", error_type=type(exc).__name__)
