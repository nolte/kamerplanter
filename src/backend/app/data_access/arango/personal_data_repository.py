"""ArangoDB read side of the Art. 15 personal-data manifest (REQ-025)."""

from collections.abc import Sequence
from typing import Any

from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataSourceDefinition

#: Filter fields that name an edge endpoint. Their value is a document id.
EDGE_ENDPOINT_FIELDS = frozenset({"_from", "_to"})


class ArangoPersonalDataRepository(IPersonalDataRepository):
    """Resolves one declared manifest source into the user's rows.

    No collection name is written down here. Every name comes from the
    :class:`DataSourceDefinition` the caller passes in, which is what keeps the
    declared inventory and the executing path from splitting again (#1622).
    """

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def collect_for_user(
        self,
        source: DataSourceDefinition,
        user_key: UserKey,
        tenant_keys: Sequence[str],
        *,
        tombstone: str | None = None,
    ) -> list[dict[str, Any]]:
        if source.disclosure_gap is not None:
            # Refused rather than answered: an empty list from a source that
            # cannot be attributed to the subject reads as "no data", which is
            # the lie #1645 is about. The service never asks; this is the floor.
            msg = f"Manifest source '{source.collection}' cannot be disclosed per subject: {source.disclosure_gap}"
            raise ValueError(msg)
        if not source.fields:
            # ``KEEP(doc, [])`` returns ``{}`` for every row, which would read
            # as "the user has data here but all of it is blank". A source that
            # declares no field is a manifest defect, not an empty result.
            msg = f"Manifest source '{source.collection}' declares no fields to export."
            raise ValueError(msg)

        if source.time_series is not None:
            # #2165 — a TimescaleDB table, not a collection: answering here would query a
            # collection that does not exist, or worse, one that happens to share the name.
            msg = f"Manifest source '{source.collection}' is a time-series table, not an ArangoDB collection."
            raise ValueError(msg)

        if source.personal_tenant_scope is not None:
            return self._collect_personal_tenant(source, tenant_keys)

        if source.edge_collection:
            return self._collect_via_edge(source, user_key)

        field = source.filter_field
        if not field:
            msg = f"Manifest source '{source.collection}' declares neither an edge collection nor a filter field."
            raise ValueError(msg)

        # ``_key`` is a system attribute and cannot be reached through
        # ``doc[@field]`` bind syntax in the same way, so it gets its own query
        # rather than a string-built one.
        # An edge collection whose rows *are* the subject's data (#1719,
        # ``user_favorites``: which catalogue entries they marked, and when)
        # is filtered on its endpoint, which stores the document id
        # ``users/<key>`` rather than the bare key. Comparing the endpoint with
        # the bare key would match nothing and read as "no favourites".
        match_value = f"{col.USERS}/{user_key}" if field in EDGE_ENDPOINT_FIELDS else user_key
        bind_vars: dict[str, Any] = {
            "@collection": source.collection,
            "user_key": match_value,
            "fields": list(source.fields),
        }
        if field == "_key":
            query = """
            FOR doc IN @@collection
              FILTER doc._key == @user_key
              RETURN KEEP(doc, @fields)
            """
        elif source.tenant_scoped:
            # The user-reference field is written by whoever edits the document,
            # not by the subject. Without this clause anyone with write access
            # in their own tenant could name a foreign, enumerable user key and
            # plant rows into that subject's disclosure (#1662 SCR-001). No
            # membership means no tenant-scoped rows, not all of them.
            #
            # REQ-025 §3.1.2 rule 6 (#1793): a tenant deletion rewrote the
            # subject's key on its retained rows to their tombstone hash, and the
            # subject is no member of a tenant that no longer exists. Those rows
            # are matched by the tombstone, and only while their tenant is gone —
            # a salted hash nobody can type, on a row of a tenant nobody writes to.
            if not tenant_keys and tombstone is None:
                return []
            query = """
            FOR doc IN @@collection
              FILTER (doc[@field] == @user_key AND doc.tenant_key IN @tenant_keys)
                OR (
                  @tombstone != null
                  AND doc[@field] == @tombstone
                  AND LENGTH(FOR tenant IN @@tenants FILTER tenant._key == doc.tenant_key LIMIT 1 RETURN 1) == 0
                )
              RETURN KEEP(doc, @fields)
            """
            bind_vars["field"] = field
            bind_vars["tenant_keys"] = list(tenant_keys)
            bind_vars["tombstone"] = tombstone
            bind_vars["@tenants"] = col.TENANTS
        else:
            # A row without a tenant key (``quality_assessments`` hangs off its
            # batch) carries the tombstone only where an erasure wrote it.
            query = """
            FOR doc IN @@collection
              FILTER doc[@field] == @user_key OR (@tombstone != null AND doc[@field] == @tombstone)
              RETURN KEEP(doc, @fields)
            """
            bind_vars["field"] = field
            bind_vars["tombstone"] = tombstone
        return [dict(doc) for doc in self._db.aql.execute(query, bind_vars=bind_vars)]

    def _collect_personal_tenant(
        self, source: DataSourceDefinition, tenant_keys: Sequence[str]
    ) -> list[dict[str, Any]]:
        """Every row of the subject's own personal tenants in *source* (#2135, MT-039).

        *tenant_keys* are the personal tenants the subject owns (the service passes
        ``personal_tenant_keys_of``, never the memberships). A row belongs when its
        ``tenant_key`` is one of them, or — for ``locations`` / ``slots``, whose own
        ``tenant_key`` no write path fills (#1397) — when its declared parent chain
        reaches a row that carries one: the anchor the tenant-erasure inventory uses.
        A scope with several chains (#2165, ``sensors``: tank, site or location) matches
        a row that any of them reaches. No personal tenant means no rows, never all of them.
        """
        if not tenant_keys:
            return []
        scope = source.personal_tenant_scope
        assert scope is not None  # the caller dispatched on it
        bind_vars: dict[str, Any] = {
            "@collection": source.collection,
            "tenant_keys": list(tenant_keys),
            "fields": list(source.fields),
        }
        clauses = ["doc.tenant_key IN @tenant_keys"]
        for index, chain in enumerate(scope.chains):
            if not chain:
                continue  # the row's own tenant_key, already the first clause
            # Every name is a bind parameter, numbered per chain; no identifier is spliced.
            f1, c1 = f"c{index}f1", f"c{index}c1"
            bind_vars |= {f1: chain[0].field, c1: chain[0].collection}
            if len(chain) == 1:
                clauses.append(f"(doc[@{f1}] != null AND DOCUMENT(@{c1}, doc[@{f1}]).tenant_key IN @tenant_keys)")
                continue
            f2, c2 = f"c{index}f2", f"c{index}c2"
            bind_vars |= {f2: chain[1].field, c2: chain[1].collection}
            clauses.append(
                f"(doc[@{f1}] != null AND LENGTH("
                f"FOR p IN [DOCUMENT(@{c1}, doc[@{f1}])] "
                f"FILTER p != null AND (p.tenant_key IN @tenant_keys OR "
                f"(p[@{f2}] != null AND DOCUMENT(@{c2}, p[@{f2}]).tenant_key IN @tenant_keys)) RETURN 1) > 0)"
            )
        anchor = " OR ".join(clauses)
        query = f"""
        FOR doc IN @@collection
          FILTER {anchor}
          RETURN KEEP(doc, @fields)
        """
        return [dict(doc) for doc in self._db.aql.execute(query, bind_vars=bind_vars)]

    def _collect_via_edge(self, source: DataSourceDefinition, user_key: UserKey) -> list[dict[str, Any]]:
        """Traverse the declared edge from the user vertex.

        Direction is ``ANY`` on purpose. The manifest declares *which* edge
        connects the user to the source, not which way round it was modelled,
        and a wrong guess here does not fail loudly — it returns an empty list,
        which reads exactly like "the user has no linked providers". The target
        collection is filtered explicitly so ``ANY`` cannot widen the result.
        """
        query = """
        FOR v IN 1..1 ANY @user_id @@edge
          FILTER PARSE_IDENTIFIER(v._id).collection == @collection
          RETURN KEEP(v, @fields)
        """
        return [
            dict(doc)
            for doc in self._db.aql.execute(
                query,
                bind_vars={
                    "user_id": f"{col.USERS}/{user_key}",
                    "@edge": source.edge_collection,
                    "collection": source.collection,
                    "fields": list(source.fields),
                },
            )
        ]
