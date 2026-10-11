"""ArangoDB store of the plan catalogue (REQ-056 §7, §13.2, #2142).

Global collection ``plans``; parametrised AQL only. A tenant stored before v0091
carries no ``plan_key`` and counts as the default plan ``standard``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.domain.interfaces.plan_repository import IPlanRepository
from app.domain.models.plan import DEFAULT_PLAN_KEY, Plan

#: ArangoDB "unique constraint violated" - a plan key that is already taken.
_ERR_UNIQUE_CONSTRAINT = 1210

_GET_DEFAULT = """
FOR p IN @@plans
  FILTER p.is_default == true
  SORT DATE_TIMESTAMP(p.created_at) ASC, p._key ASC
  LIMIT 1
  RETURN p
"""

_LIST_ALL = """
FOR p IN @@plans
  SORT p._key ASC
  RETURN p
"""

#: One statement: the named plan becomes the default, every other loses the mark (REQ-056 §7.6).
_MAKE_DEFAULT = """
LET target = DOCUMENT(@@plans, @key)
FILTER target != null
FOR p IN @@plans
  FILTER p._key == @key OR p.is_default == true
  UPDATE p WITH { is_default: p._key == @key, updated_at: @now } IN @@plans
  RETURN NEW
"""

#: One statement: removed only when no tenant points at the plan and it is not the default.
_DELETE_UNUSED = """
LET target = DOCUMENT(@@plans, @key)
LET in_use = LENGTH(
  FOR t IN @@tenants
    FILTER (t.plan_key == null ? @default_key : t.plan_key) == @key
    LIMIT 1
    RETURN 1
) > 0
FILTER target != null AND target.is_default != true AND NOT in_use
REMOVE target IN @@plans
RETURN OLD._key
"""

_TENANT_COUNTS = """
FOR t IN @@tenants
  COLLECT plan_key = (t.plan_key == null ? @default_key : t.plan_key) WITH COUNT INTO n
  RETURN { plan_key, n }
"""

_COUNT_TENANTS_ON = """
FOR t IN @@tenants
  FILTER (t.plan_key == null ? @default_key : t.plan_key) == @key
  COLLECT WITH COUNT INTO n
  RETURN n
"""


def _to_doc(plan: Plan) -> dict[str, Any]:
    doc = plan.model_dump(by_alias=True, mode="json")
    for field in ("created_at", "updated_at"):
        if doc.get(field) is None:
            doc.pop(field, None)
    return doc


class ArangoPlanRepository(IPlanRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get(self, key: str) -> Plan | None:
        doc = self._db.collection(col.PLANS).get(key)
        return Plan(**cast(dict[str, Any], doc)) if doc else None

    def get_default(self) -> Plan | None:
        cursor = cast(Cursor, self._db.aql.execute(_GET_DEFAULT, bind_vars={"@plans": col.PLANS}))
        rows = [cast(dict[str, Any], row) for row in cursor]
        return Plan(**rows[0]) if rows else None

    def list_all(self) -> list[Plan]:
        cursor = cast(Cursor, self._db.aql.execute(_LIST_ALL, bind_vars={"@plans": col.PLANS}))
        return [Plan(**cast(dict[str, Any], row)) for row in cursor]

    def create(self, plan: Plan) -> Plan:
        now = datetime.now(UTC).isoformat()
        doc = {**_to_doc(plan), "created_at": now, "updated_at": now}
        try:
            result = self._db.collection(col.PLANS).insert(doc, return_new=True)
        except DocumentInsertError as exc:
            if exc.error_code == _ERR_UNIQUE_CONSTRAINT:
                raise DuplicateError("plans", "key", plan.key) from exc
            raise
        return Plan(**cast(dict[str, Any], result)["new"])

    def store_plan(self, plan: Plan) -> Plan | None:
        collection = self._db.collection(col.PLANS)
        stored = collection.get(plan.key)
        if not stored:
            return None
        doc = _to_doc(plan)
        # ``is_default`` moves only through ``make_default`` (exactly one default); ``created_at`` stays.
        doc["is_default"] = bool(cast(dict[str, Any], stored).get("is_default", False))
        doc["created_at"] = cast(dict[str, Any], stored).get("created_at")
        doc["updated_at"] = datetime.now(UTC).isoformat()
        result = collection.replace(doc, return_new=True)
        return Plan(**cast(dict[str, Any], result)["new"])

    def make_default(self, key: str) -> Plan | None:
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                _MAKE_DEFAULT, bind_vars={"@plans": col.PLANS, "key": key, "now": datetime.now(UTC).isoformat()}
            ),
        )
        chosen = [cast(dict[str, Any], row) for row in cursor if cast(dict[str, Any], row).get("_key") == key]
        return Plan(**chosen[0]) if chosen else None

    def delete_unused(self, key: str) -> bool:
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                _DELETE_UNUSED,
                bind_vars={"@plans": col.PLANS, "@tenants": col.TENANTS, "key": key, "default_key": DEFAULT_PLAN_KEY},
            ),
        )
        return any(True for _ in cursor)

    def tenant_counts(self) -> dict[str, int]:
        cursor = cast(
            Cursor,
            self._db.aql.execute(_TENANT_COUNTS, bind_vars={"@tenants": col.TENANTS, "default_key": DEFAULT_PLAN_KEY}),
        )
        return {str(row["plan_key"]): int(row["n"]) for row in cast(list[dict[str, Any]], list(cursor))}

    def count_tenants_on(self, key: str) -> int:
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                _COUNT_TENANTS_ON, bind_vars={"@tenants": col.TENANTS, "key": key, "default_key": DEFAULT_PLAN_KEY}
            ),
        )
        return int(next(iter(cursor), 0))
