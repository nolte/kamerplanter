from typing import Any

from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import ActivityKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.interfaces.activity_repository import IActivityRepository
from app.domain.models.activity import Activity


class ArangoActivityRepository(BaseArangoRepository[Activity], IActivityRepository):
    """The activity catalogue — a hybrid catalogue read as own ∪ global (#2119, MT-023).

    ``Activity`` declares ``tenant_key``: the global seed rows carry an empty one,
    and the per-tenant name index (v0076) and the tenant erasure already treat a
    tenant-stamped row as that tenant's. Every request read therefore takes the
    caller's tenant **keyword-only and without a default** and filters with the
    shared :func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`. An
    empty ``tenant_key`` (anonymous / light mode / no personal tenant) collapses the
    union to the global rows — never an error, never a foreign tenant's row.
    """

    _model_cls = Activity
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ACTIVITIES)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        *,
        tenant_key: str,
    ) -> tuple[list[Activity], int]:
        """One page of the activities ``tenant_key`` may read, plus their total."""
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        filter_clauses = [predicate]
        idx = 0
        for field, value in (filters or {}).items():
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
        query = f"FOR doc IN {col.ACTIVITIES} FILTER " + " AND ".join(filter_clauses)
        count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
        count_vars: dict[str, Any] = dict(bind_vars)
        list_vars: dict[str, Any] = {**bind_vars, "offset": offset, "limit": limit}
        # ``_key`` breaks ties so get_all_pages pages over a total order (#2015).
        query += " SORT doc.sort_order, doc.name, doc._key LIMIT @offset, @limit RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=list_vars)
        items = [Activity(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_readable_or_raise(self, key: ActivityKey, *, tenant_key: str) -> Activity:
        """One activity, if ``tenant_key`` may read it: its own row or a global one.

        Anything else raises :class:`NotFoundError` (HTTP 404, never 403 — a 403
        would confirm that the row exists in another tenant). The twin of
        ``ArangoNutrientPlanRepository.get_readable_or_raise`` (#950), except that
        an empty ``tenant_key`` is allowed and reads the global rows only.
        """
        activity = self.get_or_raise(key)
        if activity.tenant_key not in ("", tenant_key):
            raise NotFoundError("Activity", key)
        return activity

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

    def get_system_activities(self, *, tenant_key: str) -> list[Activity]:
        """The ``is_system`` activities ``tenant_key`` may read (own ∪ global)."""
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        query = f"""
        FOR doc IN {col.ACTIVITIES}
          FILTER doc.is_system == true AND {predicate}
          SORT doc.sort_order, doc.name
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Activity(**self._from_doc(doc)) for doc in cursor]

    def get_by_category(self, category: str, *, tenant_key: str) -> list[Activity]:
        """The activities of ``category`` that ``tenant_key`` may read (own ∪ global)."""
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        query = f"""
        FOR doc IN {col.ACTIVITIES}
          FILTER doc.category == @category AND {predicate}
          SORT doc.sort_order, doc.name
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={**bind_vars, "category": category})
        return [Activity(**self._from_doc(doc)) for doc in cursor]
