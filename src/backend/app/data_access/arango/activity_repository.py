from typing import Any

from arango.database import StandardDatabase

from app.common.types import ActivityKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import aql_field
from app.domain.interfaces.activity_repository import IActivityRepository
from app.domain.models.activity import Activity


class ArangoActivityRepository(BaseArangoRepository[Activity], IActivityRepository):
    _model_cls = Activity
    tenant_scope_exempt_reason = (
        "activity catalogue written only by platform admins and seeds, every stored row global (#2148 "
        "measurement); its unfiltered get_all is the activity-plan generator's whole-catalogue read. The "
        "own-or-global read and is_tenant_scoped are PR #2219 (#2119) - whichever lands second drops this "
        "reason and the name from EXEMPT_REPOSITORIES"
    )

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
                    filter_clauses.append(f"doc.{aql_field(field)} == @val{idx}")
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

    def get_global_activities(self) -> list[Activity]:
        """Every global (system) activity, the whole catalogue, no row limit (#2027).

        The activity seed matches a seed entry to its row through this and nothing
        wider — the twin of ``ArangoNutrientPlanRepository.get_global_plans`` (#1957).
        A row is global when its ``tenant_key`` is empty or absent, so a tenant's own
        activity that carries a seed's name is never returned and can never be
        rewritten from the seed as a global system row. Ordered by ``_key`` so a
        lookup by name resolves the same way on every boot.
        """
        cursor = self._db.aql.execute(
            f"""
            FOR doc IN {col.ACTIVITIES}
                FILTER doc.tenant_key == "" OR doc.tenant_key == null
                SORT doc._key
                RETURN doc
            """
        )
        return [Activity(**self._from_doc(doc)) for doc in cursor]

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
