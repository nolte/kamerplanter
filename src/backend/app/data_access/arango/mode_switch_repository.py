"""ArangoDB persistence of the deployment-mode bookkeeping (REQ-027 §7a, #1855).

Two documents in ``system_meta``: ``deployment_mode`` (the mode the last start ran in) and
``pending_takeover`` (an open light-to-full take-over, claimed while a decision runs). Plus the
reads the take-over needs: the size of the light-mode tenant, the earliest eligible account and
the number of person accounts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from arango.collection import StandardCollection
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError
from pydantic_core import to_jsonable_python

from app.data_access.arango import collections as col
from app.domain.interfaces.mode_switch_repository import IModeSwitchRepository
from app.domain.models.mode_switch import DeploymentMode, PendingTakeover, TakeoverReceipt, TakeoverResourceCounts

DEPLOYMENT_MODE_KEY = "deployment_mode"
PENDING_TAKEOVER_KEY = "pending_takeover"

#: ArangoDB's "unique constraint violated" — the document is there already.
_UNIQUE_CONSTRAINT_VIOLATED = 1210
#: ArangoDB's "conflict" — the document changed between the read and the revision-checked write.
_CONFLICT = 1200

#: One statement, revision-checked (``ignoreRevs: false``): of two concurrent decisions exactly one
#: claims the take-over; the other's write conflicts. A claim older than ``@stale_before`` belongs to a
#: decision that died and may be taken over (#1855 SEC-004). The document stays until the decision succeeded.
_CLAIM_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key
  FILTER doc.claim_id == null OR DATE_TIMESTAMP(doc.claimed_at) < DATE_TIMESTAMP(@stale_before)
  UPDATE doc WITH { claim_id: @claimant, claimed_at: @now } IN @@collection OPTIONS { ignoreRevs: false }
  RETURN NEW
"""

#: Remove the take-over only while *this* claimant holds it.
_COMPLETE_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key AND doc.claim_id == @claimant
  REMOVE doc IN @@collection
  RETURN OLD._key
"""

#: Drop the claim only while *this* claimant holds it; the take-over stays open.
_RELEASE_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key AND doc.claim_id == @claimant
  UPDATE doc WITH { claim_id: null, claimed_at: null } IN @@collection OPTIONS { keepNull: false }
  RETURN NEW._key
"""

#: Whether *this* claimant still holds the take-over (#1855 R2-003).
_HOLDS_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key AND doc.claim_id == @claimant
  RETURN doc._key
"""

#: Store what a failed decision could not undo, while *this* claimant holds it (#1855 R2-002).
_ATTENTION_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key AND doc.claim_id == @claimant
  UPDATE doc WITH { needs_attention: true, receipt: @receipt } IN @@collection OPTIONS { mergeObjects: false }
  RETURN NEW._key
"""

#: Drop the stored receipt once *this* claimant undid it; the claim stays.
_RESOLVE_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key AND doc.claim_id == @claimant
  UPDATE doc WITH { needs_attention: null, receipt: null } IN @@collection OPTIONS { keepNull: false }
  RETURN NEW._key
"""

#: Remove the take-over whoever holds it (a light-mode start, where nobody can decide it).
_CLEAR_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key
  REMOVE doc IN @@collection
  RETURN OLD._key
"""

#: The light-mode tenant's size in one statement. Every count is bound to the tenant; the collections
#: are bind parameters, never interpolated. Plants are counted alive only (``removed_on == null``), the
#: marker the dashboard counts use.
_COUNT_QUERY = """
RETURN {
  plants: LENGTH(FOR doc IN @@plants FILTER doc.tenant_key == @tenant_key AND doc.removed_on == null RETURN 1),
  sites: LENGTH(FOR doc IN @@sites FILTER doc.tenant_key == @tenant_key RETURN 1),
  planting_runs: LENGTH(FOR doc IN @@runs FILTER doc.tenant_key == @tenant_key RETURN 1),
  nutrient_plans: LENGTH(FOR doc IN @@plans FILTER doc.tenant_key == @tenant_key RETURN 1),
  tasks: LENGTH(FOR doc IN @@tasks FILTER doc.tenant_key == @tenant_key RETURN 1)
}
"""

#: The earliest account that may decide a take-over without a platform admin (#1855 SEC-002, SEC-008):
#: registered at or after the take-over opened, active, a person, a verified address and an active
#: membership in a personal tenant it owns (what registration leaves). An undated account never qualifies.
_EARLIEST_ELIGIBLE_QUERY = """
FOR u IN @@users
  FILTER u._key != @excluding
  FILTER u.is_active == true
  FILTER u.account_type != "service"
  FILTER u.email_verified == true
  FILTER u.created_at != null AND DATE_TIMESTAMP(u.created_at) >= DATE_TIMESTAMP(@created_since)
  FILTER LENGTH(
    FOR m IN @@memberships
      FILTER m.user_key == u._key AND m.is_active == true
      FOR t IN @@tenants
        FILTER t._key == m.tenant_key AND t.tenant_type == "personal" AND t.owner_user_key == u._key
        LIMIT 1
        RETURN 1
  ) > 0
  SORT DATE_TIMESTAMP(u.created_at), u._key
  LIMIT 1
  RETURN u._key
"""

#: Active person accounts besides the system account (#1855 SEC-007).
_COUNT_PERSONS_QUERY = """
RETURN LENGTH(
  FOR u IN @@users
    FILTER u._key != @excluding
    FILTER u.is_active == true
    FILTER u.account_type != "service"
    RETURN 1
)
"""


class ArangoModeSwitchRepository(IModeSwitchRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @property
    def _meta(self) -> StandardCollection:
        return self._db.collection(col.SYSTEM_META)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def get_deployment_mode(self) -> DeploymentMode | None:
        doc = cast(dict[str, Any] | None, self._meta.get(DEPLOYMENT_MODE_KEY))
        if doc is None:
            return None
        mode = doc.get("mode")
        return cast(DeploymentMode, mode) if mode in ("light", "full") else None

    def set_deployment_mode(self, mode: DeploymentMode) -> None:
        self._meta.insert(
            {"_key": DEPLOYMENT_MODE_KEY, "mode": mode, "updated_at": self._now()},
            overwrite_mode="update",
        )

    def get_pending_takeover(self) -> PendingTakeover | None:
        doc = cast(dict[str, Any] | None, self._meta.get(PENDING_TAKEOVER_KEY))
        return None if doc is None else self._takeover(doc)

    def record_pending_takeover(self, takeover: PendingTakeover) -> bool:
        try:
            self._meta.insert(
                {
                    "_key": PENDING_TAKEOVER_KEY,
                    "system_tenant_key": takeover.system_tenant_key,
                    "created_at": takeover.created_at.isoformat(),
                }
            )
        except DocumentInsertError as exc:
            if exc.error_code == _UNIQUE_CONSTRAINT_VIOLATED:
                return False
            raise
        return True

    def claim_pending_takeover(self, *, claimant: str, now: datetime, stale_before: datetime) -> PendingTakeover | None:
        try:
            cursor = self._db.aql.execute(
                _CLAIM_QUERY,
                bind_vars={
                    "@collection": col.SYSTEM_META,
                    "key": PENDING_TAKEOVER_KEY,
                    "claimant": claimant,
                    "now": now.isoformat(),
                    "stale_before": stale_before.isoformat(),
                },
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == _CONFLICT:
                return None
            raise
        docs = list(cast(Cursor, cursor))
        return self._takeover(docs[0]) if docs else None

    def complete_pending_takeover(self, *, claimant: str) -> bool:
        cursor = self._db.aql.execute(
            _COMPLETE_QUERY,
            bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY, "claimant": claimant},
        )
        return bool(list(cast(Cursor, cursor)))

    def release_pending_takeover(self, *, claimant: str) -> bool:
        cursor = self._db.aql.execute(
            _RELEASE_QUERY,
            bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY, "claimant": claimant},
        )
        return bool(list(cast(Cursor, cursor)))

    def holds_claim(self, *, claimant: str) -> bool:
        cursor = self._db.aql.execute(
            _HOLDS_QUERY,
            bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY, "claimant": claimant},
        )
        return bool(list(cast(Cursor, cursor)))

    def mark_takeover_needs_attention(self, *, claimant: str, receipt: TakeoverReceipt) -> bool:
        cursor = self._db.aql.execute(
            _ATTENTION_QUERY,
            bind_vars={
                "@collection": col.SYSTEM_META,
                "key": PENDING_TAKEOVER_KEY,
                "claimant": claimant,
                "receipt": to_jsonable_python(receipt),
            },
        )
        return bool(list(cast(Cursor, cursor)))

    def resolve_takeover_attention(self, *, claimant: str) -> bool:
        cursor = self._db.aql.execute(
            _RESOLVE_QUERY,
            bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY, "claimant": claimant},
        )
        return bool(list(cast(Cursor, cursor)))

    def clear_pending_takeover(self) -> bool:
        cursor = self._db.aql.execute(
            _CLEAR_QUERY, bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY}
        )
        return bool(list(cast(Cursor, cursor)))

    def count_tenant_resources(self, *, tenant_key: str) -> TakeoverResourceCounts:
        if not tenant_key:
            return TakeoverResourceCounts()
        cursor = self._db.aql.execute(
            _COUNT_QUERY,
            bind_vars={
                "@plants": col.PLANT_INSTANCES,
                "@sites": col.SITES,
                "@runs": col.PLANTING_RUNS,
                "@plans": col.NUTRIENT_PLANS,
                "@tasks": col.TASKS,
                "tenant_key": tenant_key,
            },
        )
        counts = next(cast(Cursor, cursor), None) or {}
        return TakeoverResourceCounts(**{name: int(value or 0) for name, value in counts.items()})

    def earliest_eligible_person_key(self, *, excluding: str, created_since: datetime) -> str | None:
        cursor = self._db.aql.execute(
            _EARLIEST_ELIGIBLE_QUERY,
            bind_vars={
                "@users": col.USERS,
                "@memberships": col.MEMBERSHIPS,
                "@tenants": col.TENANTS,
                "excluding": excluding,
                "created_since": created_since.isoformat(),
            },
        )
        keys = list(cast(Cursor, cursor))
        return str(keys[0]) if keys else None

    def count_active_person_accounts(self, *, excluding: str) -> int:
        cursor = self._db.aql.execute(_COUNT_PERSONS_QUERY, bind_vars={"@users": col.USERS, "excluding": excluding})
        return int(next(cast(Cursor, cursor), 0) or 0)

    @staticmethod
    def _takeover(doc: dict[str, Any]) -> PendingTakeover:
        return PendingTakeover(
            system_tenant_key=doc.get("system_tenant_key") or "",
            created_at=doc.get("created_at") or datetime.now(UTC),
            claim_id=doc.get("claim_id"),
            claimed_at=doc.get("claimed_at"),
            needs_attention=bool(doc.get("needs_attention")),
            receipt=TakeoverReceipt(**doc["receipt"]) if doc.get("receipt") else None,
        )
