"""ArangoDB persistence of the ``user_favorites`` edges (REQ-020, #1638).

Moved out of :class:`~app.domain.services.favorites_service.FavoritesService`,
which used to drive a ``StandardDatabase`` itself. The queries are the ones the
service ran, unchanged; the visibility decision (own ∪ global ∪ granted) stays in
the service, so this module only answers the questions it asks.
"""

import structlog
from arango.database import StandardDatabase
from arango.exceptions import DocumentGetError, DocumentInsertError

from app.data_access.arango import collections as col
from app.domain.interfaces.favorites_repository import IFavoritesRepository

logger = structlog.get_logger()

#: ``ARANGO_DATA_SOURCE_NOT_FOUND`` — the collection itself does not exist.
#: The one datastore error that legitimately means "no row of this key lives
#: here"; every other one means the answer is unknown, not "no" (#1538).
_ERR_DATA_SOURCE_NOT_FOUND = 1203


class ArangoFavoritesRepository(IFavoritesRepository):
    """Edge reads/writes on ``user_favorites`` plus the by-key catalogue probes.

    Not a :class:`~app.data_access.arango.base_repository.BaseArangoRepository`:
    a favourite is a raw edge document with no domain model, and the target reads
    span six collections rather than one.
    """

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    # ── user_favorites edges ─────────────────────────────────────────

    def find_edge(self, from_id: str, to_id: str) -> dict | None:
        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id AND e._to == @to_id
                RETURN e
            """,
            bind_vars={"from_id": from_id, "to_id": to_id},
        )
        existing = list(cursor)
        return existing[0] if existing else None

    def promote_to_manual(self, edge_key: str) -> None:
        # A raw driver write: python-arango's ``keep_none`` default is True, so the
        # ``cascade_from_key`` null is stored rather than dropped.
        self._db.collection(col.USER_FAVORITES).update({"_key": edge_key, "source": "manual", "cascade_from_key": None})

    def insert_edge(self, edge_data: dict) -> dict:
        try:
            result = self._db.collection(col.USER_FAVORITES).insert(edge_data, return_new=True)
            return result.get("new", edge_data)
        except DocumentInsertError as exc:
            if exc.http_code == 409:
                # Concurrent insert race — edge was created between check and insert
                cursor = self._db.aql.execute(
                    "FOR e IN user_favorites FILTER e._from == @f AND e._to == @t RETURN e",
                    bind_vars={"f": edge_data["_from"], "t": edge_data["_to"]},
                )
                rows = list(cursor)
                if rows:
                    return rows[0]
            raise

    def remove_edges_to_key(self, from_id: str, target_key: str) -> int:
        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id AND PARSE_IDENTIFIER(e._to).key == @target_key
                REMOVE e IN user_favorites
                RETURN OLD
            """,
            bind_vars={"from_id": from_id, "target_key": target_key},
        )
        return len(list(cursor))

    def remove_cascade_edges(self, from_id: str, cascade_from_key: str) -> int:
        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id
                    AND e.source == "cascade"
                    AND e.cascade_from_key == @plan_key
                REMOVE e IN user_favorites
                RETURN OLD
            """,
            bind_vars={"from_id": from_id, "plan_key": cascade_from_key},
        )
        return len(list(cursor))

    def list_edges(self, from_id: str, target_type: str | None = None) -> list[dict]:
        if target_type:
            cursor = self._db.aql.execute(
                """
                FOR e IN user_favorites
                    FILTER e._from == @from_id AND e.target_type == @entity_type
                    RETURN e
                """,
                bind_vars={"from_id": from_id, "entity_type": target_type},
            )
        else:
            cursor = self._db.aql.execute(
                """
                FOR e IN user_favorites
                    FILTER e._from == @from_id
                    RETURN e
                """,
                bind_vars={"from_id": from_id},
            )
        return list(cursor)

    # ── favourite-target resolution ──────────────────────────────────

    def get_catalogue_row(self, collection_name: str, key: str) -> dict | None:
        try:
            return self._db.collection(collection_name).get(key)
        except DocumentGetError as exc:
            if exc.error_code != _ERR_DATA_SOURCE_NOT_FOUND:
                raise
            logger.warning(
                "favorite_target_collection_missing",
                collection=collection_name,
                error_code=exc.error_code,
            )
            return None

    def is_granted(self, collection_name: str, key: str, tenant_key: str) -> bool:
        cursor = self._db.aql.execute(
            f"FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._from == @f AND g._to == @t LIMIT 1 RETURN 1",
            bind_vars={"f": f"{col.TENANTS}/{tenant_key}", "t": f"{collection_name}/{key}"},
        )
        return bool(list(cursor))
