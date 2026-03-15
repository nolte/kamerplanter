from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from arango.exceptions import DocumentInsertError, DocumentUpdateError

from app.common.exceptions import DuplicateError, NotFoundError
from app.data_access.arango.query_builder import AQLBuilder

if TYPE_CHECKING:
    from arango.database import StandardDatabase
    from pydantic import BaseModel


class BaseArangoRepository:
    """Generic ArangoDB CRUD operations."""

    def __init__(self, db: StandardDatabase, collection_name: str) -> None:
        self._db = db
        self._collection_name = collection_name

    @property
    def collection(self):  # type: ignore[no-untyped-def]
        return self._db.collection(self._collection_name)

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _to_doc(self, model: BaseModel) -> dict[str, Any]:
        data = model.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        return data

    def _from_doc(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc["_key"] = doc.get("_key", doc.get("_id", "").split("/")[-1])
        return doc

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        doc = self.collection.get(key)
        if doc is None:
            return None
        return self._from_doc(doc)

    def get_all(
        self, offset: int = 0, limit: int = 50, tenant_key: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        builder = AQLBuilder(self._collection_name)
        if tenant_key:
            builder.filter("tenant_key", "==", tenant_key)
        builder.sort("_key").paginate(offset, limit)

        query, bind_vars = builder.build_list()
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [self._from_doc(doc) for doc in cursor]

        count_query, count_vars = builder.build_count()
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)

        return items, total

    def create(self, model: BaseModel) -> dict[str, Any]:
        data = self._to_doc(model)
        data["created_at"] = self._now()
        data["updated_at"] = self._now()
        try:
            result = self.collection.insert(data, return_new=True)
        except DocumentInsertError as e:
            if e.error_code == 1210:  # unique constraint violated
                raise DuplicateError(self._collection_name, "key", "duplicate") from e
            raise
        return self._from_doc(result["new"])

    def update(self, key: str, model: BaseModel) -> dict[str, Any]:
        data = self._to_doc(model)
        data["updated_at"] = self._now()
        try:
            result = self.collection.update({"_key": key, **data}, return_new=True)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            raise
        return self._from_doc(result["new"])

    def delete(self, key: str) -> bool:
        try:
            self.collection.delete(key)
            return True
        except Exception:
            return False

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        builder = AQLBuilder(self._collection_name)
        builder.filter(field, "==", value)
        query, bind_vars = builder.build_list()
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._from_doc(doc) for doc in cursor]

    def create_edge(
        self, edge_collection: str, from_id: str, to_id: str, data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        edge_data = {
            "_from": from_id,
            "_to": to_id,
            "created_at": self._now(),
        }
        if data:
            edge_data.update(data)
        col = self._db.collection(edge_collection)
        result = col.insert(edge_data, return_new=True)
        return result["new"]

    def get_edges(self, edge_collection: str, vertex_id: str, direction: str = "outbound") -> list[dict[str, Any]]:
        query = f"""
        FOR v, e IN 1..1 {direction.upper()} @start
          GRAPH 'kamerplanter_graph'
          OPTIONS {{edgeCollections: [@edge_col]}}
          RETURN {{vertex: v, edge: e}}
        """
        cursor = self._db.aql.execute(query, bind_vars={"start": vertex_id, "edge_col": edge_collection})
        return list(cursor)

    def delete_edges(self, edge_collection: str, from_id: str, to_id: str | None = None) -> int:
        self._db.collection(edge_collection)
        if to_id:
            query = f"FOR e IN {edge_collection} FILTER e._from == @from AND e._to == @to REMOVE e IN {edge_collection}"
            self._db.aql.execute(query, bind_vars={"from": from_id, "to": to_id})
        else:
            query = f"FOR e IN {edge_collection} FILTER e._from == @from REMOVE e IN {edge_collection}"
            self._db.aql.execute(query, bind_vars={"from": from_id})
        return 1
