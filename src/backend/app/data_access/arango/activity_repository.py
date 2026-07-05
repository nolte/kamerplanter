from typing import Any

from arango.database import StandardDatabase

from app.common.types import ActivityKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.activity_repository import IActivityRepository
from app.domain.models.activity import Activity


class ArangoActivityRepository(BaseArangoRepository[Activity], IActivityRepository):
    _model_cls = Activity

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ACTIVITIES)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[Activity], int]:
        if filters:
            query = f"FOR doc IN {col.ACTIVITIES}"
            bind_vars: dict[str, Any] = {}
            filter_clauses = []
            idx = 0
            for field, value in filters.items():
                if field == "scope":
                    if value == "universal":
                        filter_clauses.append("(doc.species_compatible == null OR LENGTH(doc.species_compatible) == 0)")
                    elif value == "restricted":
                        filter_clauses.append("doc.species_compatible != null AND LENGTH(doc.species_compatible) > 0")
                elif field == "species":
                    bind_vars[f"val{idx}"] = value.lower()
                    filter_clauses.append(
                        f"LENGTH(doc.species_compatible) > 0 AND "
                        f"LENGTH(FOR s IN (doc.species_compatible || []) "
                        f"FILTER CONTAINS(LOWER(s), @val{idx}) RETURN s) > 0"
                    )
                    idx += 1
                else:
                    bind_vars[f"val{idx}"] = value
                    filter_clauses.append(f"doc.{field} == @val{idx}")
                    idx += 1
            if filter_clauses:
                query += " FILTER " + " AND ".join(filter_clauses)
            count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
            count_vars = dict(bind_vars)
            bind_vars["offset"] = offset
            bind_vars["limit"] = limit
            query += " SORT doc.sort_order, doc.name LIMIT @offset, @limit RETURN doc"
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            items = [Activity(**self._from_doc(doc)) for doc in cursor]
            count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
            total = next(count_cursor, 0)
            return items, total
        return super().get_all(offset, limit)

    def get_by_name(self, name: str) -> Activity | None:
        return self.find_one_by_field("name", name)

    def delete(self, key: ActivityKey) -> bool:
        activity_id = f"{col.ACTIVITIES}/{key}"
        # Delete inbound edges
        for edge_col in [col.TASK_USES_ACTIVITY]:
            query = f"FOR e IN {edge_col} FILTER e._to == @aid REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"aid": activity_id})
        return super().delete(key)

    def get_system_activities(self) -> list[Activity]:
        query = f"""
        FOR doc IN {col.ACTIVITIES}
          FILTER doc.is_system == true
          SORT doc.sort_order, doc.name
          RETURN doc
        """
        cursor = self._db.aql.execute(query)
        return [Activity(**self._from_doc(doc)) for doc in cursor]

    def get_by_category(self, category: str) -> list[Activity]:
        query = f"""
        FOR doc IN {col.ACTIVITIES}
          FILTER doc.category == @category
          SORT doc.sort_order, doc.name
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={"category": category})
        return [Activity(**self._from_doc(doc)) for doc in cursor]
