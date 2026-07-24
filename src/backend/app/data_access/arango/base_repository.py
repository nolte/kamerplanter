import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal

from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError, DocumentUpdateError
from pydantic import BaseModel

from app.common.exceptions import DuplicateError, NotFoundError
from app.data_access.arango import tenant_ownership
from app.data_access.arango.query_builder import AQLBuilder

#: ``(field, operator, value)`` filter triple. ``operator`` must be one of the
#: :attr:`AQLBuilder._ALLOWED_OPS` whitelist (injection guard).
type FilterTriple = tuple[str, str, Any]

type SortDirection = Literal["ASC", "DESC"]


class BaseArangoRepository[TModel: BaseModel]:
    """Generic, typed ArangoDB CRUD operations for one primary collection.

    The class is parameterised over a Pydantic domain model ``TModel``. A
    concrete repository binds the model in one of two ways:

    * **Subclass binding** — set the :attr:`_model_cls` class attribute
      (``class ArangoActivityRepository(BaseArangoRepository[Activity]):
      _model_cls = Activity``). The inherited public methods
      (:meth:`get_by_key`, :meth:`create`, …) then return ``Activity`` models
      and the subclass drops its hand-written CRUD wrappers.
    * **Composition binding** — pass ``model_cls`` to the constructor
      (``BaseArangoRepository[Disease](db, col.DISEASES, Disease)``). This builds
      a typed view onto a secondary collection, used by multi-collection
      repositories (IPM, harvest, fertilizer stocks).

    **Unbound repositories (raw dict mode, opt-in).** A repository without any
    model binding is *unbound*. Genuinely unbound repositories still exist and
    are legitimate — edge/graph managers, custom-AQL-only repositories, and the
    service-embedded ``BaseArangoRepository(db, collection)`` views that hand a
    raw ``dict`` straight to a domain model. They must now declare that intent
    explicitly by passing ``raw=True``; the typed public API then returns the
    raw ``dict`` document exactly as before this class became generic.

    **Fail-fast (FR-002 A3).** When a repository is neither bound *nor* in raw
    mode, the typed public API (:meth:`get_by_key`, :meth:`get_all`,
    :meth:`create`, :meth:`update`, :meth:`find_by_field`, …) raises
    :class:`TypeError` instead of silently returning ``dict`` documents. This
    catches the accidental case — a caller who forgot to bind a model and would
    otherwise receive untyped dicts. Model-agnostic methods (:meth:`delete`,
    :meth:`create_edge`, :meth:`delete_edges`, and the private doc primitives)
    stay available on unbound repositories regardless of ``raw``.

    Two layers are exposed:

    * private **doc primitives** (:meth:`_get_doc`, :meth:`_insert_doc`, …) that
      always operate on ``dict`` documents — used internally and by composed
      views that need raw docs;
    * the **typed public API** that wraps those primitives and maps to models
      when a model is bound.
    """

    #: Bound domain model for subclass binding. ``None`` leaves the repository
    #: unbound; the typed API then fails fast unless ``raw=True`` was passed
    #: (FR-002 A3).
    _model_cls: ClassVar[type[BaseModel] | None] = None

    #: Optional override for the entity name used in :class:`NotFoundError`
    #: (defaults to ``_model_cls.__name__``).
    _entity_name: ClassVar[str | None] = None

    #: Whether the backing collection is tenant-scoped (REQ-024 isolation
    #: container).  Tenant-scoped repositories MUST receive a ``tenant_key`` on
    #: list queries, or an explicit ``all_tenants=True`` system-context opt-in.
    #: When neither is supplied :meth:`get_all` raises instead of silently
    #: returning documents of *all* tenants (SEC-B4 cross-tenant leak guard).
    is_tenant_scoped: bool = False

    def __init__(
        self,
        db: StandardDatabase,
        collection_name: str,
        model_cls: type[TModel] | None = None,
        *,
        raw: bool = False,
    ) -> None:
        self._db = db
        self._collection_name = collection_name
        #: Instance-level model binding (composition). Wins over ``_model_cls``.
        self._instance_model_cls: type[TModel] | None = model_cls
        #: Explicit opt-in to the legacy raw-``dict`` API for a genuinely
        #: unbound repository (edge/graph managers, custom-AQL-only repos,
        #: service-embedded dict views). Without it, an unbound typed call fails
        #: fast instead of silently returning dicts (FR-002 A3).
        self._raw_mode = raw

    # ── Model resolution / wrapping ──────────────────────────────────────────

    def _resolve_model_cls(self) -> type[BaseModel] | None:
        """Resolve the bound model: constructor arg wins over class attribute."""
        return self._instance_model_cls or self._model_cls

    def _require_bound_or_raw(self) -> None:
        """Guard the typed public API against accidental unbound use (FR-002 A3).

        An unbound repository (no ``_model_cls`` class attribute and no
        constructor ``model_cls``) may only serve the typed methods when it has
        explicitly opted into the legacy raw-``dict`` API via ``raw=True``.
        Otherwise the caller has almost certainly forgotten to bind a model, so
        we fail fast instead of silently handing back raw ``dict`` documents.
        """
        if not self._raw_mode:
            raise TypeError(
                f"BaseArangoRepository for collection '{self._collection_name}' "
                "is unbound (no model_cls) and not in raw mode: the typed API "
                "(get_by_key/get_all/create/update/find_by_field/…) requires a "
                "bound Pydantic model. Bind one via the '_model_cls' class "
                "attribute or the 'model_cls' constructor argument, or pass "
                "'raw=True' to opt into the legacy dict API explicitly "
                "(FR-002 A3)."
            )

    def _wrap(self, doc: dict[str, Any] | None) -> Any:
        """Map a raw doc onto the bound model, or return it unchanged (raw mode).

        ``doc`` is already normalised through :meth:`_from_doc`. Fails fast when
        the repository is unbound and not in raw mode (FR-002 A3).
        """
        if doc is None:
            return None
        model_cls = self._resolve_model_cls()
        if model_cls is None:
            self._require_bound_or_raw()
            return doc
        return model_cls(**doc)

    def _wrap_many(self, docs: list[dict[str, Any]]) -> list[Any]:
        model_cls = self._resolve_model_cls()
        if model_cls is None:
            self._require_bound_or_raw()
            return docs
        return [model_cls(**doc) for doc in docs]

    def _require_entity_name(self) -> str:
        if self._entity_name is not None:
            return self._entity_name
        model_cls = self._resolve_model_cls()
        if model_cls is not None:
            return model_cls.__name__
        return self._collection_name

    # ── Helpers (unchanged) ──────────────────────────────────────────────────

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

    #: Matches the indexed field name in an ArangoDB unique-constraint message,
    #: e.g. ``... over '["batch_id"]' ...`` or the older ``... over 'batch_id' ...``.
    _UNIQUE_INDEX_FIELD_RE: ClassVar[re.Pattern[str]] = re.compile(r"over\s+'?\[?\"?(?P<field>[A-Za-z_][A-Za-z0-9_.]*)")

    @classmethod
    def _extract_unique_field(cls, error_message: str | None) -> str | None:
        """Extract the conflicting field name from an ArangoDB 1210 error message.

        ArangoDB names the violated unique index in its error message, e.g.::

            unique constraint violated - in index 42 of type persistent
            over '["batch_id"]'; conflicting key: '...'

        Returns the first indexed field name, or ``None`` when the message does
        not follow the recognised shape (so callers can fall back gracefully).
        """
        if not error_message:
            return None
        match = cls._UNIQUE_INDEX_FIELD_RE.search(error_message)
        return match.group("field") if match else None

    @classmethod
    def _describe_unique_conflict(cls, error: DocumentInsertError, data: dict[str, Any]) -> tuple[str, str]:
        """Turn a unique-constraint violation into a ``(field, value)`` pair.

        Extracts the real conflicting field from the ArangoDB error message and
        pairs it with the value taken from the document being inserted, so the
        resulting :class:`DuplicateError` names the actual culprit instead of the
        misleading ``key='duplicate'`` placeholder. Falls back to a non-misleading
        ``field='<value>'`` when the message cannot be parsed.
        """
        field = cls._extract_unique_field(getattr(error, "error_message", None))
        if field and field in data:
            return field, str(data[field])
        if field:
            return field, ""
        return "field", ""

    def _require_tenant_key(self, tenant_key: str, method: str) -> None:
        """Reject the empty-``tenant_key`` sentinel before issuing a scoped query.

        Single-value tenant-scoped reads (dashboard counts/lists) must never run
        with an empty ``tenant_key``: that would silently read across every
        tenant (SEC-001 / SEC-B4). Mirrors the up-front guard in
        ``ArangoPlantInstanceRepository.get_survival_stats``.
        """
        if not tenant_key:
            raise ValueError(
                f"{method} is tenant-scoped and requires a non-empty tenant_key (SEC-B4 tenant isolation)."
            )

    def verify_entity_ownership(
        self,
        collection: str,
        key: str,
        tenant_key: str,
        *,
        entity_name: str | None = None,
    ) -> None:
        """Guard a caller-supplied foreign reference before persisting it (#517).

        Thin delegate to :func:`tenant_ownership.verify_entity_ownership` bound to
        this repository's ``self._db``. Fails **closed** with
        :class:`NotFoundError` (→ HTTP 404) when the referenced document is
        missing or belongs to another tenant, so a foreign key's existence is
        never disclosed (no cross-tenant oracle, SEC-B4).
        """
        tenant_ownership.verify_entity_ownership(self._db, collection, key, tenant_key, entity_name=entity_name)

    def verify_entities_ownership(
        self,
        collection: str,
        keys: Any,
        tenant_key: str,
        *,
        entity_name: str | None = None,
    ) -> None:
        """Batch variant of :meth:`verify_entity_ownership` (#517).

        Verifies every distinct, non-empty key, skipping falsy ones. Fails closed
        with :class:`NotFoundError` on the first missing/foreign reference.
        """
        tenant_ownership.verify_entities_ownership(self._db, collection, keys, tenant_key, entity_name=entity_name)

    def _enforce_tenant_scope(self, tenant_key: str | None, all_tenants: bool) -> None:
        """Fail loudly when a tenant-scoped list query is not tenant-bound.

        Guards against SEC-B4: a caller that forgets to pass ``tenant_key``
        would otherwise receive documents across every tenant.  An empty
        ``tenant_key`` (``None`` or ``""``) is treated as "not provided" because
        both fall through the ``if tenant_key`` filter downstream.
        """
        if self.is_tenant_scoped and not tenant_key and not all_tenants:
            raise ValueError(
                f"Collection '{self._collection_name}' is tenant-scoped: pass a "
                "tenant_key, or set all_tenants=True for an explicit "
                "system-context query (SEC-B4 tenant isolation)."
            )

    # ── Doc primitives (dict level) ──────────────────────────────────────────

    def _get_doc(self, key: str) -> dict[str, Any] | None:
        doc = self.collection.get(key)
        if doc is None:
            return None
        return self._from_doc(doc)

    def _list_docs(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
        *,
        all_tenants: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        self._enforce_tenant_scope(tenant_key, all_tenants)
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

    def _insert_doc(
        self,
        model: BaseModel,
        *,
        default_now_fields: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        data = self._to_doc(model)
        data["created_at"] = self._now()
        data["updated_at"] = self._now()
        for field in default_now_fields:
            if not data.get(field):
                data[field] = self._now()
        try:
            result = self.collection.insert(data, return_new=True)
        except DocumentInsertError as e:
            if e.error_code == 1210:  # unique constraint violated
                field, value = self._describe_unique_conflict(e, data)
                raise DuplicateError(self._collection_name, field, value) from e
            raise
        return self._from_doc(result["new"])

    def _update_doc(self, key: str, model: BaseModel) -> dict[str, Any]:
        data = self._to_doc(model)
        data["updated_at"] = self._now()
        try:
            result = self.collection.update({"_key": key, **data}, return_new=True)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            raise
        return self._from_doc(result["new"])

    def _update_doc_fields(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Partial in-place update of only ``fields`` (plus ``updated_at``).

        Unlike :meth:`_update_doc`, which rewrites the whole document from a
        full model dump, this hands ArangoDB only the supplied keys.
        ``collection.update`` merges them into the stored document, so
        concurrent updates of *disjoint* fields commute instead of clobbering
        each other's writes (lost-update guard). ``keep_none=True`` (the
        python-arango default, asserted explicitly here) keeps an intentional
        ``None`` — e.g. a REQ-045 dashboard_layout reset — persisted as ``null``
        rather than silently dropping the key.
        """
        data = dict(fields)
        data["updated_at"] = self._now()
        try:
            result = self.collection.update({"_key": key, **data}, return_new=True, keep_none=True)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            raise
        return self._from_doc(result["new"])

    def _delete_doc(self, key: str) -> bool:
        try:
            self.collection.delete(key)
            return True
        except Exception:
            return False

    def _find_docs(
        self,
        filters: list[FilterTriple],
        *,
        sort: str | None = None,
        sort_direction: SortDirection = "ASC",
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        builder = AQLBuilder(self._collection_name)
        for field, op, value in filters:
            builder.filter(field, op, value)
        if sort:
            builder.sort(sort, sort_direction)
        if offset is not None and limit is not None:
            builder.paginate(offset, limit)
        query, bind_vars = builder.build_list()
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._from_doc(doc) for doc in cursor]

    # ── Typed public API ─────────────────────────────────────────────────────

    def get_by_key(self, key: str) -> TModel | None:
        """Fetch one document by key, mapped to the bound model (or ``dict``)."""
        return self._wrap(self._get_doc(key))

    def get_or_raise(self, key: str) -> TModel:
        """Like :meth:`get_by_key` but raise :class:`NotFoundError` when absent.

        Replaces the ~118 copied ``get_by_key`` + ``if x is None: raise
        NotFoundError(...)`` blocks in the service layer (DUP-B6). The entity
        name matches the previous hand-written call: ``_entity_name`` if set,
        otherwise the bound model's class name.
        """
        result = self.get_by_key(key)
        if result is None:
            raise NotFoundError(self._require_entity_name(), key)
        return result

    def get_or_raise_by[T](self, getter: Callable[[str], T | None], entity_name: str, key: str) -> T:
        """Run a custom single-doc ``getter`` and raise when it returns ``None``.

        Facade repositories load *secondary* entities through hand-written
        getters (``get_schedule_by_key`` → ``MaintenanceSchedule``,
        ``get_workflow_template_by_key`` → ``WorkflowTemplate``). Calling the
        inherited :meth:`get_or_raise` there would raise with the *primary*
        model's name. This helper funnels the copied ``getter`` + ``None`` check
        + :class:`NotFoundError` block (DUP-B6) into the base while letting the
        caller name the entity that was actually loaded. Composed-view backed
        facades should prefer delegating to the view's :meth:`get_or_raise`
        instead, which derives ``entity_name`` from the bound model.
        """
        result = getter(key)
        if result is None:
            raise NotFoundError(entity_name, key)
        return result

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
        *,
        all_tenants: bool = False,
    ) -> tuple[list[TModel], int]:
        items, total = self._list_docs(offset, limit, tenant_key, all_tenants=all_tenants)
        return self._wrap_many(items), total

    def get_page(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterTriple] | None = None,
        sort: str = "_key",
        sort_direction: SortDirection = "ASC",
    ) -> tuple[list[TModel], int]:
        """Filtered, sorted, paginated fetch with a matching total count.

        Generalises :meth:`get_all` for the hand-written ``FILTER … SORT …
        LIMIT`` list queries in the multi-collection repositories.
        """
        builder = AQLBuilder(self._collection_name)
        for field, op, value in filters or []:
            builder.filter(field, op, value)
        builder.sort(sort, sort_direction).paginate(offset, limit)

        query, bind_vars = builder.build_list()
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [self._from_doc(doc) for doc in cursor]

        count_query, count_vars = builder.build_count()
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)

        return self._wrap_many(items), total

    def create(
        self,
        model: TModel,
        *,
        default_now_fields: tuple[str, ...] = (),
    ) -> TModel:
        """Insert a document (setting ``created_at``/``updated_at``).

        ``default_now_fields`` additionally back-fills any domain timestamp
        (e.g. ``applied_at``, ``inspected_at``) that is missing/empty on the
        model, replacing the copied ``if not data.get(...): data[...] = now``
        idiom in the IPM/harvest repositories.
        """
        return self._wrap(self._insert_doc(model, default_now_fields=default_now_fields))

    def update(self, key: str, model: TModel) -> TModel:
        return self._wrap(self._update_doc(key, model))

    def update_fields(self, key: str, fields: dict[str, Any]) -> TModel:
        """Partial update, merging only ``fields`` into the document (lost-update safe).

        Companion to :meth:`update` for callers that want ArangoDB to merge a
        subset of fields in place rather than rewrite the whole document from a
        full model dump. This lets concurrent PATCHes of disjoint fields commute
        instead of the last full-document writer winning (lost update). ``None``
        values are preserved (``keep_none=True``), so an explicit reset survives.
        Returns the updated document mapped to the bound model (or the raw
        ``dict`` in raw mode).
        """
        return self._wrap(self._update_doc_fields(key, fields))

    def delete(self, key: str) -> bool:
        return self._delete_doc(key)

    def find_by_field(
        self,
        field: str,
        value: Any,
        *,
        sort: str | None = None,
        sort_direction: SortDirection = "ASC",
        offset: int | None = None,
        limit: int | None = None,
        extra_filters: list[FilterTriple] | None = None,
    ) -> list[TModel]:
        """Find documents where ``field == value`` (plus optional extras).

        Called with only ``field``/``value`` it is behaviour-identical to the
        pre-refactor method (single ``==`` filter, no sort/limit). The optional
        keyword arguments express the single-field ``FILTER … SORT … LIMIT``
        queries (DUP-B3) that previously required hand-written AQL.
        """
        filters: list[FilterTriple] = [(field, "==", value)]
        if extra_filters:
            filters.extend(extra_filters)
        docs = self._find_docs(
            filters,
            sort=sort,
            sort_direction=sort_direction,
            offset=offset,
            limit=limit,
        )
        return self._wrap_many(docs)

    def find_one_by_field(
        self,
        field: str,
        value: Any,
        *,
        extra_filters: list[FilterTriple] | None = None,
    ) -> TModel | None:
        """Return the first ``field == value`` match (``LIMIT 1``) or ``None``.

        Replaces the byte-identical ``get_by_slug`` / ``get_by_token`` style
        single-result lookups (DUP-B3).
        """
        results = self.find_by_field(
            field,
            value,
            extra_filters=extra_filters,
            offset=0,
            limit=1,
        )
        return results[0] if results else None

    # ── Edges ────────────────────────────────────────────────────────────────

    def create_edge(
        self,
        edge_collection: str,
        from_id: str,
        to_id: str,
        data: dict[str, Any] | None = None,
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

    def delete_edges(
        self,
        edge_collection: str,
        from_id: str | None = None,
        to_id: str | None = None,
        *,
        vertex_id: str | None = None,
        other_id: str | None = None,
        direction: Literal["outbound", "inbound", "any"] = "outbound",
    ) -> int:
        """Remove edges incident to a vertex, honouring ``direction`` (DUP-B10).

        Two call styles are supported for backward compatibility:

        * **Legacy** ``delete_edges(col, from_id[, to_id])`` — removes outbound
          edges ``e._from == from_id`` (optionally also ``e._to == to_id``).
        * **Directional** ``delete_edges(col, vertex_id=..., direction=...)`` —

          - ``outbound`` → ``e._from == vertex`` (default),
          - ``inbound`` → ``e._to == vertex``,
          - ``any`` → ``e._from == vertex OR e._to == vertex``,

          with an optional ``other_id`` constraining the opposite endpoint.

        The collection name (always a code-level ``collections.py`` constant) is
        bound via ``@@edge`` rather than interpolated, and the honest count of
        removed edges is returned instead of a hard-coded ``1``.
        """
        vertex = vertex_id if vertex_id is not None else from_id
        other = other_id if other_id is not None else to_id
        if vertex is None:
            raise ValueError("delete_edges requires from_id or vertex_id")

        if direction == "inbound":
            clause = "e._to == @vertex"
        elif direction == "any":
            clause = "(e._from == @vertex OR e._to == @vertex)"
        else:
            clause = "e._from == @vertex"

        bind_vars: dict[str, Any] = {"@edge": edge_collection, "vertex": vertex}
        if other is not None:
            if direction == "inbound":
                clause += " AND e._from == @other"
            elif direction == "any":
                clause += " AND (e._from == @other OR e._to == @other)"
            else:
                clause += " AND e._to == @other"
            bind_vars["other"] = other

        query = f"FOR e IN @@edge FILTER {clause} REMOVE e IN @@edge RETURN OLD._key"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return sum(1 for _ in cursor)
