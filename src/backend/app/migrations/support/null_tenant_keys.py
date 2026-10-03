"""Normalise a missing ``tenant_key`` to ``""`` before a ``(tenant_key, name)`` index (#2027).

A hybrid catalogue marks its global rows with ``tenant_key == ""``, but a row written
before the field existed carries no ``tenant_key`` at all, and ArangoDB indexes the
absent attribute as ``null``. For a unique ``(tenant_key, name)`` index ``null`` and
``""`` are two different values: a legacy global row without the field and a later
global row with ``""`` and the same name would both be admitted, so "global exactly
once" would not hold. The readers already treat both as global
(``tenant_key == "" OR tenant_key == null``); this makes the stored value agree.

A ``null`` row whose name a ``""`` row already holds is **not** rewritten — the update
would violate the new index and abort the migration. It is counted and reported, and
the two global rows stay as they are for an operator to resolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

_CANDIDATES_AQL = """
FOR doc IN @@collection
    FILTER doc.tenant_key == null
    LET held = FIRST(
        FOR other IN @@collection
            FILTER other.tenant_key == "" AND other.name == doc.name
            LIMIT 1
            RETURN 1
    )
    RETURN { key: doc._key, conflict: held != null }
"""

_NORMALISE_AQL = """
FOR key IN @keys
    UPDATE key WITH { tenant_key: "" } IN @@collection
"""


@dataclass(frozen=True)
class NullTenantKeyNormalisation:
    """What :func:`normalise_null_tenant_keys` found and wrote. Counts only, no keys."""

    candidates: int
    conflicts: int
    normalised: int

    def details(self) -> dict[str, Any]:
        """Report payload shared by the migrations that call this."""
        return {
            "null_tenant_keys": self.candidates + self.conflicts,
            "null_tenant_keys_normalised": self.normalised,
            "null_tenant_key_name_conflicts": self.conflicts,
        }


def normalise_null_tenant_keys(db: StandardDatabase, collection: str, *, dry_run: bool) -> NullTenantKeyNormalisation:
    """Set ``tenant_key = ""`` on every row of ``collection`` that has none (or ``null``).

    Idempotent: a re-run finds no ``null`` row. ``dry_run`` counts and writes nothing.
    """
    rows = list(cast(Cursor, db.aql.execute(_CANDIDATES_AQL, bind_vars={"@collection": collection})))
    keys = [str(row["key"]) for row in rows if isinstance(row, dict) and not row.get("conflict")]
    conflicts = sum(1 for row in rows if isinstance(row, dict) and row.get("conflict"))
    if dry_run or not keys:
        return NullTenantKeyNormalisation(candidates=len(keys), conflicts=conflicts, normalised=0)
    db.aql.execute(_NORMALISE_AQL, bind_vars={"@collection": collection, "keys": keys})
    return NullTenantKeyNormalisation(candidates=len(keys), conflicts=conflicts, normalised=len(keys))
