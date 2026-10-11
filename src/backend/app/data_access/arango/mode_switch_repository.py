"""ArangoDB persistence of the deployment-mode bookkeeping (REQ-027 §7a, #1855).

Two documents in ``system_meta``: ``deployment_mode`` (the mode the last start ran in) and
``pending_takeover`` (an open light-to-full take-over). Plus the two reads the take-over
needs: the size of the light-mode tenant and the earliest person account.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from arango.collection import StandardCollection
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.domain.interfaces.mode_switch_repository import IModeSwitchRepository
from app.domain.models.mode_switch import DeploymentMode, PendingTakeover, TakeoverResourceCounts

DEPLOYMENT_MODE_KEY = "deployment_mode"
PENDING_TAKEOVER_KEY = "pending_takeover"

#: ArangoDB's "unique constraint violated" — the document is there already.
_UNIQUE_CONSTRAINT_VIOLATED = 1210

#: One statement: the open take-over is removed and returned, so of two concurrent decisions
#: exactly one receives it.
_CLAIM_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key
  REMOVE doc IN @@collection
  RETURN OLD
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

#: The earliest active person account; an undated account sorts after every dated one.
_EARLIEST_PERSON_QUERY = """
FOR u IN @@collection
  FILTER u._key != @excluding
  FILTER u.is_active != false
  FILTER u.account_type != "service"
  SORT u.created_at == null, DATE_TIMESTAMP(u.created_at), u._key
  LIMIT 1
  RETURN u._key
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

    def claim_pending_takeover(self) -> PendingTakeover | None:
        cursor = self._db.aql.execute(
            _CLAIM_QUERY, bind_vars={"@collection": col.SYSTEM_META, "key": PENDING_TAKEOVER_KEY}
        )
        docs = list(cast(Cursor, cursor))
        return self._takeover(docs[0]) if docs else None

    def clear_pending_takeover(self) -> bool:
        return self.claim_pending_takeover() is not None

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

    def earliest_active_person_key(self, *, excluding: str) -> str | None:
        cursor = self._db.aql.execute(
            _EARLIEST_PERSON_QUERY, bind_vars={"@collection": col.USERS, "excluding": excluding}
        )
        keys = list(cast(Cursor, cursor))
        return str(keys[0]) if keys else None

    @staticmethod
    def _takeover(doc: dict[str, Any]) -> PendingTakeover:
        return PendingTakeover(
            system_tenant_key=doc.get("system_tenant_key") or "",
            created_at=doc.get("created_at") or datetime.now(UTC),
        )
