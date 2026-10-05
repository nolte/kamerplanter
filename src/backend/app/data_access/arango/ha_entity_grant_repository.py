"""ArangoDB repository of the per-tenant Home Assistant entity allowlist (MT-015, #2112).

Parametrised AQL only (NFR-006). The ``(tenant_key, entity_id)`` pair is unique in
the collection (``collections.HA_ENTITY_GRANT_IDENTITY_FIELDS``); :meth:`grant`
upserts on it, so granting twice — or two admins granting at once — leaves one row.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.ha_entity_grant_repository import IHaEntityGrantRepository
from app.domain.models.ha_entity_grant import HaEntityGrant, HaEntityGrantSource


class ArangoHaEntityGrantRepository(IHaEntityGrantRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def list_for_tenant(self, *, tenant_key: str) -> list[HaEntityGrant]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
          SORT doc.entity_id
          RETURN doc
        """
        bind_vars: dict[str, Any] = {"@collection": col.TENANT_HA_ENTITY_GRANTS, "tenant_key": tenant_key}
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return [HaEntityGrant(**doc) for doc in cursor]

    def granted_entity_ids(self, *, tenant_key: str) -> frozenset[str]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
          RETURN doc.entity_id
        """
        bind_vars: dict[str, Any] = {"@collection": col.TENANT_HA_ENTITY_GRANTS, "tenant_key": tenant_key}
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return frozenset(str(entity_id) for entity_id in cursor if entity_id)

    def all_granted(self) -> dict[str, frozenset[str]]:
        query = """
        FOR doc IN @@collection
          COLLECT tenant_key = doc.tenant_key INTO grouped = doc.entity_id
          RETURN { tenant_key, entity_ids: grouped }
        """
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars={"@collection": col.TENANT_HA_ENTITY_GRANTS}))
        return {
            str(row["tenant_key"]): frozenset(str(e) for e in row["entity_ids"] if e)
            for row in cursor
            if row.get("tenant_key")
        }

    def grant(self, tenant_key: str, entity_ids: Iterable[str], *, source: HaEntityGrantSource) -> int:
        wanted = sorted(set(entity_ids))
        if not wanted:
            return 0
        query = """
        FOR entity_id IN @entity_ids
          UPSERT { tenant_key: @tenant_key, entity_id: entity_id }
          INSERT { tenant_key: @tenant_key, entity_id: entity_id, source: @source, created_at: @now }
          UPDATE {}
          IN @@collection
          RETURN OLD ? 0 : 1
        """
        bind_vars: dict[str, Any] = {
            "@collection": col.TENANT_HA_ENTITY_GRANTS,
            "tenant_key": tenant_key,
            "entity_ids": wanted,
            "source": HaEntityGrantSource(source).value,
            "now": datetime.now(UTC).isoformat(),
        }
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return sum(int(created) for created in cursor)

    def revoke(self, tenant_key: str, entity_id: str) -> bool:
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key AND doc.entity_id == @entity_id
          REMOVE doc IN @@collection
          RETURN 1
        """
        bind_vars: dict[str, Any] = {
            "@collection": col.TENANT_HA_ENTITY_GRANTS,
            "tenant_key": tenant_key,
            "entity_id": entity_id,
        }
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return any(True for _ in cursor)
