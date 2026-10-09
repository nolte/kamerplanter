"""Read-only measurement behind ``python -m app.migrations.audit_legacy_stamps`` (MT-052, #2144).

Migration ``v0004`` (``backfill_tenant_key.py``) stamped every row without a
``tenant_key`` with **one** default tenant. On a volume that held data of more than
one person then, rows authored by someone who never belonged to that tenant now
carry it. Nothing can tell a stamp from ownership by the key alone — but the author
fields can: a row whose ``created_by`` / ``*_by_key`` names an account that holds no
membership in the row's ``tenant_key`` was either stamped onto the wrong tenant or
written by someone who has since left.

This class only reads. It walks every document collection (system and bookkeeping
collections excluded), takes the rows with a non-empty ``tenant_key`` and at least
one author field, and classifies each author against the ``memberships`` collection
(index-backed on ``(user_key, tenant_key)``): **member** (active membership),
**former** (an inactive membership row) or **never** (no membership row at all —
the v0004 suspect, or a member whose row a removal deleted).

Attribute names are bound (``d[@field]``), never interpolated.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col

#: Collections that are not tenant data, or whose author field is the tenant relation itself.
_EXCLUDED: frozenset[str] = frozenset(
    {
        col.MEMBERSHIPS,
        col.TENANTS,
        col.USERS,
        "schema_migrations",
    }
)

#: One row per (collection, field, verdict); the sample keys are document keys only, never user keys.
_CLASSIFY = """
FOR d IN @@collection
  FILTER d.tenant_key != null AND d.tenant_key != ""
  FOR name IN ATTRIBUTES(d, true)
    FILTER name == "created_by" OR LIKE(name, "%\\_by\\_key")
    LET author = d[name]
    FILTER IS_STRING(author) AND author != ""
    LET membership = FIRST(
      FOR m IN @@memberships
        FILTER m.user_key == author AND m.tenant_key == d.tenant_key
        LIMIT 1
        RETURN m
    )
    LET verdict = membership == null ? "never" : (membership.is_active == false ? "former" : "member")
    COLLECT field = name, status = verdict INTO rows = d._key
    RETURN {field, status, count: LENGTH(rows), sample: SLICE(rows, 0, @sample)}
"""


@dataclass
class StampFinding:
    collection: str
    field: str
    status: str
    count: int
    sample: list[str] = dataclass_field(default_factory=list)


@dataclass
class StampAuditReport:
    collections_scanned: int = 0
    findings: list[StampFinding] = dataclass_field(default_factory=list)

    def count(self, status: str) -> int:
        return sum(f.count for f in self.findings if f.status == status)


class ArangoLegacyStampAudit:
    """Classify the author fields of every tenant-stamped row against the memberships."""

    def __init__(self, db: StandardDatabase, *, sample: int = 5) -> None:
        self._db = db
        self._sample = sample

    def _collections(self) -> list[str]:
        names: list[str] = []
        for info in cast(list[dict[str, Any]], self._db.collections()):
            name = str(info["name"])
            if info.get("system") or name.startswith("_") or name in _EXCLUDED:
                continue
            if info.get("type") not in ("document", 2):
                continue
            names.append(name)
        return sorted(names)

    def measure(self) -> StampAuditReport:
        report = StampAuditReport()
        if not self._db.has_collection(col.MEMBERSHIPS):
            return report
        for name in self._collections():
            report.collections_scanned += 1
            bind_vars: dict[str, Any] = {"@collection": name, "@memberships": col.MEMBERSHIPS, "sample": self._sample}
            for row in cast(Cursor, self._db.aql.execute(_CLASSIFY, bind_vars=bind_vars)):
                report.findings.append(
                    StampFinding(
                        collection=name,
                        field=str(row["field"]),
                        status=str(row["status"]),
                        count=int(row["count"]),
                        sample=[str(key) for key in row["sample"]],
                    )
                )
        return report
