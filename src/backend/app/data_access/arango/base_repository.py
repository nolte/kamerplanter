import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal

import structlog
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError, DocumentUpdateError
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import DuplicateError, NotFoundError, ValidationError
from app.data_access.arango import tenant_ownership
from app.data_access.arango.query_builder import AQLBuilder

logger = structlog.get_logger(__name__)

#: ``(field, operator, value)`` filter triple. ``operator`` must be one of the
#: :attr:`AQLBuilder._ALLOWED_OPS` whitelist (injection guard).
type FilterTriple = tuple[str, str, Any]

type SortDirection = Literal["ASC", "DESC"]

#: ArangoDB system attributes a caller-supplied partial-update payload must never
#: carry: ``_key``/``_id`` would redirect the write onto a different document,
#: ``_rev`` would forge the revision used for optimistic concurrency, and
#: ``_from``/``_to`` would re-point an edge. Stripped in
#: :meth:`BaseArangoRepository._update_doc_fields`.
_RESERVED_DOC_ATTRIBUTES: frozenset[str] = frozenset({"_key", "_id", "_rev", "_from", "_to"})


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

    #: Caller-supplied foreign references this repository's documents carry, as
    #: ``{model field: target collection}``. Every declared field is
    #: ownership-verified against the row's own ``tenant_key`` before the
    #: document is written — see :meth:`_verify_owned_references` (#948).
    #:
    #: Declaring it here rather than calling ``verify_entity_ownership`` by hand
    #: in each create method is the whole point: #948 is what happens when the
    #: check is a line someone has to remember. A ``str`` field is verified as a
    #: single key, any other iterable as a batch.
    _owned_reference_fields: ClassVar[dict[str, str]] = {}

    #: Also ownership-verify a declared reference when :meth:`update` **changes**
    #: it (#1090 C-9). Off by default: the #948 declaration was written for
    #: create-only paths, and turning the update half on everywhere at once would
    #: put a stored-document read in front of every full-model update in the
    #: system — a change of blast radius that belongs to its own issue, not to the
    #: one closing a single leak. A repository whose declared reference is
    #: reachable from a ``PUT`` body opts in; see
    #: :meth:`_verify_changed_owned_references` for the changed-only semantics and
    #: why they, not an unconditional re-check, are the correct behaviour.
    _verify_references_on_update: ClassVar[bool] = False

    #: Full-replace semantics for :meth:`update` (Issue #714).
    #:
    #: ``False`` (default) — the model is dumped with ``exclude_none=True`` and
    #: ArangoDB merges it with ``keepNull=true``: a field the caller set to
    #: ``None`` is simply absent from the patch, so the stored value survives.
    #:
    #: ``True`` — the model is dumped with ``exclude_none=False`` and ArangoDB is
    #: told ``keep_none=False``, so an explicit ``None`` *removes* the attribute
    #: from the stored document and the Pydantic default reads back as ``None``.
    #: That is what a PUT needs when "unset" is a meaningful value:
    #: ``Location.frost_exposed = null`` means "inherit from the parent site",
    #: and ``PlantInstance.slot_key = null`` means "not placed anywhere".
    #:
    #: Under this mode ``created_at`` is stripped from the payload, because a
    #: model that carries none would otherwise *erase* the stored creation
    #: timestamp. Under the default mode ``exclude_none=True`` already drops it,
    #: and a model that carries one writes back the value it was read with.
    _update_is_full_replace: ClassVar[bool] = False

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

    def _to_doc(self, model: BaseModel, *, exclude_none: bool = True) -> dict[str, Any]:
        """Serialise a model into an ArangoDB document, re-validating it first (#968).

        **Why the guard lives here.** #968 was written as if
        :meth:`update` were the single place a full model reaches the database.
        Measured, it is not: six repositories override :meth:`update`, and 33
        hand-written repository methods dump a model and write it themselves —
        21 of them through *this* method (``upsert_zone``, the phase-sequence and
        task-repository writers, the species UPSERT, …). Sitting on the
        serialisation step rather than on one public method means every one of
        those is covered, and a new hand-written writer is covered the moment it
        serialises through the house helper instead of calling ``model_dump``
        itself.

        It is validated **exactly once** per write: :meth:`update` no longer
        checks separately, because :meth:`_update_doc` reaches the database only
        through this method.

        **On the create path this is deliberate, and largely redundant.** A model
        that was just constructed was validated by Pydantic at construction, so
        :meth:`create` will almost never see a rejection here. Almost never is not
        never: a service is free to build a model, mutate it, and then insert it
        (no domain model sets ``validate_assignment=True``, so the mutation is
        unchecked), and the seed/import paths assemble models over several steps.
        Excluding the create path would therefore buy nothing but a second rule to
        remember and a hole exactly where bulk writes live. The cost is one model
        validation per inserted document, against an ArangoDB round-trip.

        ``exclude_none`` selects the null handling; see
        :attr:`_update_is_full_replace` for the two modes and why they differ.
        """
        self._validate_model_before_write(model)
        data = model.model_dump(by_alias=True, exclude_none=exclude_none, mode="json")
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
    def _describe_unique_conflict(
        cls,
        error: DocumentInsertError | DocumentUpdateError,
        data: dict[str, Any],
    ) -> tuple[str, str]:
        """Turn a unique-constraint violation into a ``(field, value)`` pair.

        Reached from the insert **and** the two update paths: an update can violate
        a unique index just as an insert can (reopening a completed care task while
        an equivalent one is already open, #1301), and error code ``1210`` means the
        same thing on both.

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

    def _validate_model_before_write(self, model: BaseModel) -> None:
        """Re-validate a full model on its way to the database (#968).

        No domain model sets ``validate_assignment=True`` (0 of 261 under
        ``app/domain/models/``), so ``plan.reference_substrate_type = "gravel"``
        stores a raw ``str`` in a field annotated ``SubstrateType`` and Pydantic
        says nothing. #966/#967 hit exactly that through ``PUT
        /nutrient-plans/{key}``: HTTP 200, and every later read would have
        returned a string where the code expects an enum.

        Turning ``validate_assignment`` on globally would validate on *every*
        assignment, including the engines' hot loops. This check instead sits on
        the serialisation step every model-to-document write shares, so the cost
        is one model validation per persisted write — negligible next to the
        ArangoDB round-trip it precedes — and no writer can forget it.

        **Called from exactly one place:** :meth:`_to_doc`. Do not add a second
        call site on a public method; that would validate twice on the paths that
        already go through the serialiser. See :meth:`_to_doc` for why the guard
        sits there and what that reaches.

        The value is checked against ``type(model)`` rather than the bound
        ``_model_cls``, so composed views and raw-mode repositories are covered
        too, and a caller that passes a *different* model type is still checked
        against the annotations it actually carries.

        The dump is taken ``by_alias=True`` and re-validated, mirroring how
        :meth:`_wrap` reconstructs a document (``model_cls(**doc)``). Serializer
        warnings are suppressed (``warnings=False``): an invalid value makes the
        serializer complain *and* the validator reject, and the validator is the
        one that carries the field, the reason and a status code.

        **This does not cover :meth:`update_fields`.** That path writes a caller
        -built ``dict`` straight into the document and never materialises a full
        model, so there is nothing here to validate; see its docstring for the
        caller obligation that stands in for this check. Nor does it cover a
        repository method that bypasses :meth:`_to_doc` and calls
        ``model.model_dump()`` itself — 12 such methods remain, which is why the
        house rule is to serialise through :meth:`_to_doc`.

        Raises:
            ValidationError: The model contradicts its own annotations. 422, with
                one detail per offending field. The offending *value* is
                deliberately absent from both the response and the log — it can
                be personal data (NFR-011) and the field plus the reason already
                identify the defect.
        """
        model_cls = type(model)
        try:
            model_cls.model_validate(model.model_dump(by_alias=True, warnings=False))
        except PydanticValidationError as exc:
            details = [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "reason": error["msg"],
                    "code": error["type"],
                }
                for error in exc.errors()
            ]
            logger.error(
                "repository_write_rejected_invalid_model",
                collection=self._collection_name,
                model=model_cls.__name__,
                fields=[detail["field"] for detail in details],
                codes=[detail["code"] for detail in details],
            )
            raise ValidationError(
                f"{model_cls.__name__} does not satisfy its own field types and was not written.",
                details=details,
            ) from exc

    def _verify_owned_references(self, model: BaseModel, *, fields: dict[str, str] | None = None) -> None:
        """Ownership-verify every declared foreign reference before a write (#948).

        The tenant compared against is the **row's own** ``tenant_key``, which the
        tenant routers stamp from ``ctx.tenant_key`` on the way in. That is the
        caller's authenticated tenant, so this is not the self-comparison #952
        catalogues: what is checked is that the *referenced* document belongs to
        the tenant the new row is being written for.

        Fails closed with :class:`NotFoundError` → HTTP 404, never 403, so a
        foreign key's existence is never disclosed (no cross-tenant oracle).
        Globally seeded catalog rows (empty ``tenant_key``) stay referenceable,
        mirroring the hybrid-catalog read visibility.

        A row that carries no tenant of its own cannot be verified against
        anything, so the check is skipped — and said out loud, because a silent
        skip is how #952's fail-closed branches hid work they were not doing.
        Such a row is in any case invisible to every tenant-scoped read, so it is
        not a disclosure route; it is a defect in whichever write path failed to
        stamp it (see #951 for two of those).

        Args:
            model: The row about to be written.
            fields: Subset of :attr:`_owned_reference_fields` to check, as the
                same ``{field: collection}`` mapping. Defaults to all of them;
                :meth:`_verify_changed_owned_references` passes the ones an update
                actually re-points.
        """
        checked = self._owned_reference_fields if fields is None else fields
        if not checked:
            return
        tenant_key = getattr(model, "tenant_key", "") or ""
        if not tenant_key:
            logger.warning(
                "owned_reference_check_skipped_tenantless_row",
                collection=self._collection_name,
                fields=sorted(checked),
            )
            return
        for field, collection in checked.items():
            value = getattr(model, field, None)
            if value is None:
                continue
            if isinstance(value, str):
                if value:
                    self.verify_entity_ownership(collection, value, tenant_key)
            else:
                self.verify_entities_ownership(collection, value, tenant_key)

    @staticmethod
    def _reference_identity(value: Any) -> Any:
        """Normalise a reference value for the "did this update re-point it?" test.

        ``None``, a missing attribute and ``""`` all mean *no reference*, and a
        sequence is compared by its members, so a re-ordered list of keys is not
        mistaken for a new one.
        """
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return value
        return sorted(str(item) for item in value)

    def _verify_changed_owned_references(self, key: str, model: BaseModel) -> None:
        """Ownership-verify the declared references an **update** re-points (#1090).

        :meth:`_verify_owned_references` hangs off :meth:`create`, which leaves the
        guard bypassable in two requests — create the row with a global reference,
        then ``PUT`` the foreign key onto it. #1090 C-9 hit exactly that on
        ``plant_instance.cultivar_key``.

        Only a **changed** reference is verified, and that restriction is
        load-bearing rather than an optimisation:

        * A reference the caller did not touch must not become a reason to refuse
          the write. The referenced document may have been deleted since — a
          dangling key is an integrity defect, not a disclosure route — and
          re-verifying it would make the whole row uneditable, including through
          the internal paths (phase transitions, planting-run materialisation,
          removal) that rewrite the full model without caring about the reference.
        * It keeps the "no oracle" property intact. For a changed value, *absent*
          and *foreign* answer identically (404, via
          :func:`tenant_ownership.verify_entity_ownership`); for an unchanged one
          nothing is dialled, so the answer carries no information the caller did
          not already supply.

        Opt-in per repository via :attr:`_verify_references_on_update` — see there
        for why it is not (yet) on for every repository.
        """
        if not self._owned_reference_fields:
            return
        stored = self.collection.get(key)
        if stored is None:
            # The document is gone; :meth:`_update_doc` raises ``NotFoundError``
            # for it a moment later. There is no stored state to compare against
            # and nothing is written, so there is nothing to verify.
            return
        changed = {
            field: collection
            for field, collection in self._owned_reference_fields.items()
            if self._reference_identity(getattr(model, field, None)) != self._reference_identity(stored.get(field))
        }
        if changed:
            self._verify_owned_references(model, fields=changed)

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
        """Rewrite a document from a full model dump (:meth:`_to_doc` validates it).

        Null handling follows :attr:`_update_is_full_replace`; ``created_at`` is
        stripped in full-replace mode so a model without one cannot erase the
        stored timestamp.
        """
        full_replace = self._update_is_full_replace
        data = self._to_doc(model, exclude_none=not full_replace)
        if full_replace:
            data.pop("created_at", None)
        data["updated_at"] = self._now()
        try:
            result = self.collection.update({"_key": key, **data}, return_new=True, keep_none=not full_replace)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            if e.error_code == 1210:  # unique constraint violated
                field, value = self._describe_unique_conflict(e, data)
                raise DuplicateError(self._collection_name, field, value) from e
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

        ArangoDB's system attributes (:data:`_RESERVED_DOC_ATTRIBUTES`) are
        stripped from ``fields`` and ``_key`` is merged **last**, so a ``_key``
        smuggled into the caller's dict can never redirect the write onto another
        document, and ``_id``/``_rev``/``_from``/``_to`` can never be rewritten —
        the same protection :meth:`_to_doc` gives the full-document path.
        """
        data = {field: value for field, value in fields.items() if field not in _RESERVED_DOC_ATTRIBUTES}
        data["updated_at"] = self._now()
        try:
            result = self.collection.update({**data, "_key": key}, return_new=True, keep_none=True)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            if e.error_code == 1210:  # unique constraint violated
                field, value = self._describe_unique_conflict(e, data)
                raise DuplicateError(self._collection_name, field, value) from e
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

        Every foreign reference the repository declares in
        :attr:`_owned_reference_fields` is ownership-verified first (#948), so a
        write that points at another tenant's entity raises before anything is
        persisted.
        """
        self._verify_owned_references(model)
        return self._wrap(self._insert_doc(model, default_now_fields=default_now_fields))

    def update(self, key: str, model: TModel) -> TModel:
        """Replace a document from a full model, re-validating it first (#968).

        Every field is checked against its own annotation before anything is
        written, because no domain model sets ``validate_assignment=True`` and
        the services reach this method with objects they mutated attribute by
        attribute. The check itself is **not** invoked here: it lives in
        :meth:`_to_doc`, which :meth:`_update_doc` goes through, so this path
        validates exactly once and every hand-written writer that serialises the
        same way is covered too. See :meth:`_validate_model_before_write` for why
        the check exists at all and for the :meth:`update_fields` hole it does
        not close, and :attr:`_update_is_full_replace` for the null semantics.

        When the repository sets :attr:`_verify_references_on_update`, a declared
        foreign reference this update *re-points* is ownership-verified first
        (#1090 C-9), so the #948 guard cannot be walked around with a ``PUT``.
        """
        if self._verify_references_on_update:
            self._verify_changed_owned_references(key, model)
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

        **Caller obligation (mass-assignment).** ``fields`` is written into the
        document as given, so it must be built from an explicit allow-list (a
        literal dict, a validated schema's ``model_dump``, or a whitelist filter)
        — never a raw request body. ArangoDB's system attributes
        (``_key``/``_id``/``_rev``/``_from``/``_to``) are stripped defensively, so
        a payload can neither redirect the write onto another document nor
        re-point an edge; every *domain* field it names is still written.

        **No type check (#968).** :meth:`update` re-validates the full model it
        is handed; this method cannot, because it never sees one — ``fields`` is
        a bare ``dict`` and the stored document it merges into is not read back
        first. A ``{"reference_substrate_type": "gravel"}`` passed here is still
        persisted as a raw string. The caller obligation above is therefore the
        *only* thing standing between this method and an invalid document: build
        ``fields`` from a validated schema's ``model_dump()``, which types each
        value on the way in, rather than from a hand-rolled dict.
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
