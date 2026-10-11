"""ArangoDB store of the plan catalogue (REQ-056 §7, §13.2, #2142).

Global collection ``plans``; parametrised AQL only. A tenant stored before v0091
carries no ``plan_key`` and counts as the default plan ``standard``.

**A stored plan that does not validate is no plan (SEC-001, #2142 review).** A
document a later build, a restore or a hand edit left in a shape this model refuses
must not turn every quota decision of every tenant on it into a 500: the reads log
``entitlement.plan_invalid`` and answer "no such plan", and the entitlement service
takes its fallback chain (default plan, then the instance settings). Unknown limit
fields are ignored by the read model, so only a value of the wrong type or out of
range makes a plan invalid.

**Every write is one statement.** A change of name, description or limits is an
``UPDATE`` that never touches ``is_default`` or ``created_at`` and merges the changed
limits into the stored ones (SEC-003); the assignment of a plan to a tenant writes
only while the plan exists and touches the plan document too, so it write-conflicts
with a concurrent deletion of that plan instead of slipping past it (SEC-004).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import TenantStatus
from app.common.exceptions import DuplicateError, WriteConflictError
from app.data_access.arango import collections as col
from app.domain.interfaces.plan_repository import IPlanRepository
from app.domain.models.plan import DEFAULT_PLAN_KEY, Plan

logger = structlog.get_logger(__name__)

#: ArangoDB "unique constraint violated" - a plan key that is already taken.
_ERR_UNIQUE_CONSTRAINT = 1210
#: ArangoDB "conflict" - a concurrent transaction wrote the same document.
_ERR_CONFLICT = 1200

#: SEC-003 — name/description as sent, the changed limits merged into the stored ones; nothing else.
_APPLY_CHANGE = """
FOR p IN @@plans
  FILTER p._key == @key
  UPDATE p WITH MERGE(@fields, { limits: MERGE(p.limits || {}, @limit_changes), updated_at: @now })
    IN @@plans OPTIONS { mergeObjects: false }
  RETURN NEW
"""

#: SEC-004 — the tenant takes the plan only while the plan exists and the tenant is not being erased.
#: The plan document is written as well (``assigned_at``), so this statement and ``_DELETE_UNUSED``
#: (which removes it) write the same document and cannot both commit.
_ASSIGN_TO_TENANT = """
LET plan = DOCUMENT(@@plans, @plan_key)
FILTER plan != null
FOR t IN @@tenants
  FILTER t._key == @tenant_key AND t.status != @deleted
  UPDATE plan WITH { assigned_at: @now } IN @@plans
  UPDATE t WITH { plan_key: @plan_key, updated_at: @now } IN @@tenants
  RETURN NEW._key
"""

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


def _parsed(doc: dict[str, Any] | None) -> Plan | None:
    """The plan of *doc*, or ``None`` - for no document and for one that does not validate (SEC-001)."""
    if not doc:
        return None
    try:
        return Plan(**doc)
    except PydanticValidationError as exc:
        # The field names only, never the stored values.
        logger.error(
            "entitlement.plan_invalid",
            plan_key=str(doc.get("_key", "")),
            fields=sorted({".".join(str(part) for part in error["loc"]) for error in exc.errors()}),
        )
        return None


class ArangoPlanRepository(IPlanRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get(self, key: str) -> Plan | None:
        return _parsed(cast(dict[str, Any] | None, self._db.collection(col.PLANS).get(key)))

    def get_default(self) -> Plan | None:
        cursor = cast(Cursor, self._db.aql.execute(_GET_DEFAULT, bind_vars={"@plans": col.PLANS}))
        rows = [cast(dict[str, Any], row) for row in cursor]
        return _parsed(rows[0]) if rows else None

    def list_all(self) -> list[Plan]:
        """Every plan that validates; an invalid one is logged and left out, not a failed listing."""
        cursor = cast(Cursor, self._db.aql.execute(_LIST_ALL, bind_vars={"@plans": col.PLANS}))
        plans = [_parsed(cast(dict[str, Any], row)) for row in cursor]
        return [plan for plan in plans if plan is not None]

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

    def apply_plan_change(
        self, key: str, *, fields: dict[str, Any], limit_changes: dict[str, int | None]
    ) -> Plan | None:
        bind_vars: dict[str, Any] = {
            "@plans": col.PLANS,
            "key": key,
            "fields": {name: fields[name] for name in ("name", "description") if name in fields},
            "limit_changes": limit_changes,
            "now": datetime.now(UTC).isoformat(),
        }
        cursor = cast(Cursor, self._db.aql.execute(_APPLY_CHANGE, bind_vars=bind_vars))
        rows = [cast(dict[str, Any], row) for row in cursor]
        return _parsed(rows[0]) if rows else None

    def assign_to_tenant(self, tenant_key: str, plan_key: str) -> bool:
        bind_vars: dict[str, Any] = {
            "@plans": col.PLANS,
            "@tenants": col.TENANTS,
            "plan_key": plan_key,
            "tenant_key": tenant_key,
            "deleted": TenantStatus.DELETED.value,
            "now": datetime.now(UTC).isoformat(),
        }
        try:
            cursor = cast(Cursor, self._db.aql.execute(_ASSIGN_TO_TENANT, bind_vars=bind_vars))
        except AQLQueryExecuteError as exc:
            if exc.error_code == _ERR_CONFLICT:
                raise WriteConflictError("plans", "the plan was changed or deleted at the same time") from exc
            raise
        return any(True for _ in cursor)

    def make_default(self, key: str) -> Plan | None:
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                _MAKE_DEFAULT, bind_vars={"@plans": col.PLANS, "key": key, "now": datetime.now(UTC).isoformat()}
            ),
        )
        chosen = [cast(dict[str, Any], row) for row in cursor if cast(dict[str, Any], row).get("_key") == key]
        return _parsed(chosen[0]) if chosen else None

    def delete_unused(self, key: str) -> bool:
        try:
            cursor = cast(
                Cursor,
                self._db.aql.execute(
                    _DELETE_UNUSED,
                    bind_vars={
                        "@plans": col.PLANS,
                        "@tenants": col.TENANTS,
                        "key": key,
                        "default_key": DEFAULT_PLAN_KEY,
                    },
                ),
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == _ERR_CONFLICT:
                raise WriteConflictError("plans", "a tenant was assigned the plan at the same time") from exc
            raise
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
