"""Unit tests for the generic ``BaseArangoRepository`` (AP-15).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. These tests pin the generic, typed
CRUD contract plus the AP-15 additions (``get_or_raise``, ``find_by_field``
options, ``find_one_by_field``, ``get_page``, ``delete_edges(direction=...)``)
and the FR-002 A3 fail-fast contract: an unbound repository serves the typed
API only when it explicitly opts into raw dict mode (``raw=True``); otherwise
the typed methods raise ``TypeError`` instead of silently returning dicts.
"""

from enum import StrEnum
from unittest.mock import MagicMock

import pytest
from arango.exceptions import DocumentInsertError, DocumentUpdateError
from pydantic import BaseModel, Field

from app.common.exceptions import DuplicateError, NotFoundError, ValidationError, WriteConflictError
from app.data_access.arango.base_repository import BaseArangoRepository


class Material(StrEnum):
    """Test-local enum for the #968 re-validation tests."""

    STEEL = "steel"
    BRASS = "brass"


class Widget(BaseModel):
    key: str | None = None
    name: str
    color: str | None = None

    model_config = {"populate_by_name": True}


class BoundRepo(BaseArangoRepository[Widget]):
    """Subclass-bound repository (typed API returns ``Widget`` models)."""

    _model_cls = Widget


class NamedRepo(BaseArangoRepository[Widget]):
    _model_cls = Widget
    _entity_name = "Gadget"


@pytest.fixture
def mock_db():
    return MagicMock()


def _doc(**kwargs) -> dict:
    doc = {"_key": "w1", "name": "Hammer"}
    doc.update(kwargs)
    return doc


# ── Model binding / raw mode ─────────────────────────────────────────────────


class TestModelBinding:
    def test_subclass_binding_returns_model(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = _doc()

        result = repo.get_by_key("w1")

        assert isinstance(result, Widget)
        assert result.name == "Hammer"

    def test_composition_binding_returns_model(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", Widget)
        mock_db.collection.return_value.get.return_value = _doc()

        assert isinstance(repo.get_by_key("w1"), Widget)

    def test_get_by_key_missing_returns_none(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_by_key("w1") is None


# ── FR-002 A3: raw dict mode (opt-in) vs. fail-fast (unbound) ─────────────────


class TestRawMode:
    """An unbound repository serves the typed API only with ``raw=True``.

    (1) legitimate raw/dict use keeps working, (2) accidental unbound typed
    use fails fast instead of silently returning dicts.
    """

    def test_raw_mode_get_by_key_returns_dict(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", raw=True)
        mock_db.collection.return_value.get.return_value = _doc()

        result = repo.get_by_key("w1")

        assert isinstance(result, dict)
        assert result["name"] == "Hammer"

    def test_raw_mode_get_by_key_missing_returns_none(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", raw=True)
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_by_key("w1") is None

    def test_raw_mode_get_all_returns_dicts(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", raw=True)
        mock_db.aql.execute.side_effect = [iter([_doc()]), iter([1])]

        items, total = repo.get_all(offset=0, limit=50)

        assert total == 1
        assert isinstance(items[0], dict)
        assert items[0]["name"] == "Hammer"

    def test_raw_mode_create_returns_dict_and_sets_timestamps(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", raw=True)
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(name="Saw")}

        result = repo.create(Widget(name="Saw"))

        assert isinstance(result, dict)
        inserted = coll.insert.call_args.args[0]
        assert "created_at" in inserted
        assert "updated_at" in inserted

    def test_raw_mode_find_by_field_returns_dicts(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets", raw=True)
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.find_by_field("name", "Hammer")

        assert isinstance(result[0], dict)
        assert result[0]["name"] == "Hammer"


class TestUnboundFailsFast:
    """Unbound + not raw: the typed API raises ``TypeError`` (FR-002 A3)."""

    def test_get_by_key_fails_fast(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = _doc()

        with pytest.raises(TypeError, match="unbound"):
            repo.get_by_key("w1")

    def test_get_all_fails_fast(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.aql.execute.side_effect = [iter([_doc()]), iter([1])]

        with pytest.raises(TypeError, match="raw=True"):
            repo.get_all(offset=0, limit=50)

    def test_create_fails_fast(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.insert.return_value = {"new": _doc()}

        with pytest.raises(TypeError, match="requires a"):
            repo.create(Widget(name="Saw"))

    def test_update_fails_fast(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.update.return_value = {"new": _doc()}

        with pytest.raises(TypeError):
            repo.update("w1", Widget(name="Renamed"))

    def test_find_by_field_fails_fast(self, mock_db):
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([_doc()])

        with pytest.raises(TypeError):
            repo.find_by_field("name", "Hammer")

    def test_get_or_raise_fails_fast_before_not_found(self, mock_db):
        # Fail-fast wins over NotFoundError: even a present doc cannot be typed.
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = _doc()

        with pytest.raises(TypeError):
            repo.get_or_raise("w1")

    def test_get_by_key_missing_returns_none_without_raising(self, mock_db):
        # A missing doc short-circuits to None before wrapping, so no raise.
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_by_key("w1") is None

    def test_delete_works_unbound_without_raw(self, mock_db):
        # Model-agnostic methods stay available on an unbound repository.
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("w1") is True


# ── get_or_raise (DUP-B6) ────────────────────────────────────────────────────


class TestGetOrRaise:
    def test_returns_model_when_found(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = _doc()

        assert isinstance(repo.get_or_raise("w1"), Widget)

    def test_raises_not_found_with_model_name(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        with pytest.raises(NotFoundError) as exc:
            repo.get_or_raise("w1")

        assert "Widget with key 'w1'" in exc.value.message

    def test_entity_name_override(self, mock_db):
        repo = NamedRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        with pytest.raises(NotFoundError) as exc:
            repo.get_or_raise("w1")

        assert "Gadget with key 'w1'" in exc.value.message


class TestEveryNotFoundNamesTheSameThing:
    """``details[0].entity`` is a contract, so one repository must answer one word (O-3).

    ``get_or_raise`` raises with the *model* name (``Widget``), while the two update
    paths raised with the *collection* name (``widgets``) — the same missing row
    answering ``entity: "widget"`` or ``entity: "widgets"`` depending on which method
    the caller happened to use. A client branching on the value (``PhotoUpload``
    de-stages only on ``entity == "attachment"``) then has to know the call path,
    which is precisely what the structured field was added to avoid (#1437).
    """

    @staticmethod
    def _entity_of(error: NotFoundError) -> str:
        assert error.details, "a NotFoundError must carry its entity (NFR-006 §2.2a)"
        return error.details[0]["entity"]

    def _missing_on_update(self, mock_db):
        from arango.exceptions import DocumentUpdateError

        err = DocumentUpdateError.__new__(DocumentUpdateError)
        err.error_code = 1202
        mock_db.collection.return_value.update.side_effect = err

    def test_get_or_raise_names_the_model(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        with pytest.raises(NotFoundError) as exc:
            repo.get_or_raise("w1")

        assert self._entity_of(exc.value) == "widget"

    def test_a_full_update_of_a_missing_row_names_the_model_too(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        self._missing_on_update(mock_db)

        with pytest.raises(NotFoundError) as exc:
            repo.update("missing", Widget(name="Hammer"))

        assert self._entity_of(exc.value) == "widget"

    def test_a_partial_update_of_a_missing_row_names_the_model_too(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        self._missing_on_update(mock_db)

        with pytest.raises(NotFoundError) as exc:
            repo.update_fields("missing", {"color": "red"})

        assert self._entity_of(exc.value) == "widget"

    def test_the_entity_name_override_wins_on_every_path(self, mock_db):
        """A repository that names itself must be believed by all three raisers."""
        repo = NamedRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None
        self._missing_on_update(mock_db)

        entities = set()
        for call in (
            lambda: repo.get_or_raise("w1"),
            lambda: repo.update("missing", Widget(name="Hammer")),
            lambda: repo.update_fields("missing", {"color": "red"}),
        ):
            with pytest.raises(NotFoundError) as exc:
                call()
            entities.add(self._entity_of(exc.value))

        assert entities == {"gadget"}

    def test_no_raiser_in_the_base_passes_the_collection_name(self):
        """The absence guard: the drift is a *spelling* at the call site.

        Three behavioural tests above cover today's three raisers; a fourth added
        later would not be covered by them. This reads the source instead, so the
        next ``NotFoundError(self._collection_name, …)`` is red the moment it is
        written.
        """
        import ast
        import inspect

        from app.data_access.arango import base_repository

        tree = ast.parse(inspect.getsource(base_repository))
        offenders = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "NotFoundError"
            and node.args
            and ast.unparse(node.args[0]) == "self._collection_name"
        ]

        assert offenders == [], (
            "a NotFoundError in the base repository must name the entity "
            f"(self._require_entity_name()), not the collection: {offenders}"
        )


# ── create / update / delete ─────────────────────────────────────────────────


class TestWrite:
    def test_create_sets_timestamps_and_returns_model(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(name="Saw")}

        result = repo.create(Widget(name="Saw"))

        assert isinstance(result, Widget)
        inserted = coll.insert.call_args.args[0]
        assert "created_at" in inserted
        assert "updated_at" in inserted

    def test_create_default_now_fields_backfills_missing(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        repo.create(Widget(name="Saw"), default_now_fields=("applied_at",))

        inserted = coll.insert.call_args.args[0]
        assert inserted["applied_at"]

    def test_create_default_now_fields_keeps_existing(self, mock_db):
        class Timed(BaseModel):
            name: str
            applied_at: str | None = None

        repo = BaseArangoRepository(mock_db, "widgets", Timed)
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        repo.create(Timed(name="Saw", applied_at="2020-01-01T00:00:00Z"), default_now_fields=("applied_at",))

        inserted = coll.insert.call_args.args[0]
        assert inserted["applied_at"] == "2020-01-01T00:00:00Z"

    def test_update_returns_model(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        result = repo.update("w1", Widget(name="Renamed"))

        assert result.name == "Renamed"
        assert coll.update.call_args.args[0]["_key"] == "w1"

    def test_update_fields_sends_only_supplied_keys(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        repo.update_fields("w1", {"color": "red"})

        sent = coll.update.call_args.args[0]
        # Only the supplied field (+ _key + updated_at) is written — no full
        # model dump, so a concurrent disjoint update is not clobbered.
        assert sent["_key"] == "w1"
        assert sent["color"] == "red"
        assert "updated_at" in sent
        assert "name" not in sent

    def test_update_fields_uses_partial_merge_with_keep_none(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(color=None)}

        repo.update_fields("w1", {"color": None})

        # keep_none=True => an explicit None reaches ArangoDB (reset semantics),
        # return_new=True so the merged document comes back.
        assert coll.update.call_args.kwargs["keep_none"] is True
        assert coll.update.call_args.kwargs["return_new"] is True
        assert coll.update.call_args.args[0]["color"] is None

    def test_update_fields_returns_bound_model(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        result = repo.update_fields("w1", {"name": "Renamed"})

        assert isinstance(result, Widget)
        assert result.name == "Renamed"

    def test_update_fields_ignores_a_smuggled_target_key(self, mock_db):
        """SEC-004 — a ``_key`` inside ``fields`` must not redirect the write.

        The payload is spread into the update document, so before the strip a
        caller-supplied ``_key`` overrode the target: a partial update built from
        a request body could rewrite an arbitrary *other* document.
        """
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        repo.update_fields("w1", {"_key": "victim", "color": "red"})

        sent = coll.update.call_args.args[0]
        assert sent["_key"] == "w1"
        assert sent["color"] == "red"

    def test_update_fields_strips_every_reserved_attribute(self, mock_db):
        """SEC-004 — ``_id``/``_rev``/``_from``/``_to`` never reach the document.

        ``_id`` redirects like ``_key``, ``_rev`` forges the revision used for
        optimistic concurrency, and ``_from``/``_to`` re-point an edge.
        """
        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        repo.update_fields(
            "w1",
            {
                "_id": "widgets/victim",
                "_rev": "_forged",
                "_from": "widgets/a",
                "_to": "widgets/b",
                "color": "red",
            },
        )

        sent = coll.update.call_args.args[0]
        assert set(sent) == {"_key", "color", "updated_at"}
        assert sent["_key"] == "w1"

    def test_update_fields_missing_doc_raises_not_found(self, mock_db):
        from arango.exceptions import DocumentUpdateError

        repo = BoundRepo(mock_db, "widgets")
        coll = mock_db.collection.return_value
        err = DocumentUpdateError.__new__(DocumentUpdateError)
        err.error_code = 1202
        coll.update.side_effect = err

        with pytest.raises(NotFoundError):
            repo.update_fields("missing", {"color": "red"})

    def test_delete_returns_true(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("w1") is True

    def test_delete_swallows_error_returns_false(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.delete.side_effect = Exception("nope")

        assert repo.delete("w1") is False


# ── #968: update() re-validates the model it is handed ───────────────────────


class Gauge(BaseModel):
    """Stand-in for a domain model: an enum field and a bounded number.

    Mirrors ``NutrientPlan.reference_substrate_type`` (``SubstrateType``) and
    ``water_mix_ratio_ro_percent`` (``int``, ``0..100``) — the shapes #966/#967
    tripped over — without pulling a real domain model into a base-class test.
    """

    key: str | None = None
    name: str
    material: Material = Material.STEEL
    pressure_bar: int = Field(default=0, ge=0, le=10)

    model_config = {"populate_by_name": True}


class GaugeRepo(BaseArangoRepository[Gauge]):
    _model_cls = Gauge


class TestUpdateRevalidatesTheModel:
    """``update`` refuses a model that contradicts its own annotations.

    No domain model sets ``validate_assignment=True``, so a service that writes
    ``obj.material = "gravel"`` attribute-by-attribute puts a raw ``str`` into a
    field annotated as an enum and Pydantic says nothing until a later read
    trips over the type. These tests pin the choke-point check that stops such a
    document reaching ArangoDB.
    """

    def test_enum_field_assigned_a_bogus_string_is_rejected(self, mock_db):
        """The #967 shape: ``"gravel"`` into an enum field, via plain assignment."""
        repo = GaugeRepo(mock_db, "gauges")
        coll = mock_db.collection.return_value
        gauge = Gauge(name="Manometer")
        gauge.material = "gravel"  # type: ignore[assignment]  # exactly what a service does

        with pytest.raises(ValidationError) as excinfo:
            repo.update("g1", gauge)

        assert excinfo.value.status_code == 422
        assert [detail["field"] for detail in excinfo.value.details] == ["material"]
        coll.update.assert_not_called()

    def test_a_rejected_write_never_reaches_the_database(self, mock_db):
        """The point of the guard: the invalid document is not persisted."""
        repo = GaugeRepo(mock_db, "gauges")
        coll = mock_db.collection.return_value
        gauge = Gauge(name="Manometer")
        setattr(gauge, "pressure_bar", 99)  # noqa: B010 — the setattr() write path

        with pytest.raises(ValidationError):
            repo.update("g1", gauge)

        coll.update.assert_not_called()

    def test_constraint_violation_is_reported_with_its_field(self, mock_db):
        repo = GaugeRepo(mock_db, "gauges")
        gauge = Gauge(name="Manometer")
        gauge.pressure_bar = 99  # ``le=10``

        with pytest.raises(ValidationError) as excinfo:
            repo.update("g1", gauge)

        detail = excinfo.value.details[0]
        assert detail["field"] == "pressure_bar"
        assert detail["code"] == "less_than_equal"

    def test_every_offending_field_is_reported_not_just_the_first(self, mock_db):
        repo = GaugeRepo(mock_db, "gauges")
        gauge = Gauge(name="Manometer")
        gauge.material = "gravel"  # type: ignore[assignment]
        gauge.pressure_bar = 99

        with pytest.raises(ValidationError) as excinfo:
            repo.update("g1", gauge)

        assert {detail["field"] for detail in excinfo.value.details} == {"material", "pressure_bar"}

    def test_the_offending_value_is_not_echoed_back(self, mock_db):
        """The rejected value can be personal data (NFR-011) — field and reason suffice."""
        repo = GaugeRepo(mock_db, "gauges")
        gauge = Gauge(name="Manometer")
        gauge.material = "user@example.com"  # type: ignore[assignment]

        with pytest.raises(ValidationError) as excinfo:
            repo.update("g1", gauge)

        rendered = excinfo.value.message + str(excinfo.value.details)
        assert "user@example.com" not in rendered

    def test_a_valid_model_is_written_unchanged(self, mock_db):
        """No regression: the guard is invisible on the happy path."""
        repo = GaugeRepo(mock_db, "gauges")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": {"_key": "g1", "name": "Manometer", "material": "brass", "pressure_bar": 4}}
        gauge = Gauge(name="Manometer")
        gauge.material = Material.BRASS

        result = repo.update("g1", gauge)

        assert result.material is Material.BRASS
        assert coll.update.call_args.args[0]["_key"] == "g1"

    def test_a_composition_bound_view_is_covered_too(self, mock_db):
        """Validation keys off ``type(model)``, not ``_model_cls``.

        Composed views (``BaseArangoRepository(db, col, Gauge)``) and raw-mode
        repositories reach :meth:`update` with a real model just as subclass-bound
        ones do; the check must not depend on the binding style.
        """
        repo = BaseArangoRepository(mock_db, "gauges", Gauge)
        gauge = Gauge(name="Manometer")
        gauge.material = "gravel"  # type: ignore[assignment]

        with pytest.raises(ValidationError):
            repo.update("g1", gauge)

    def test_update_fields_is_still_unchecked(self, mock_db):
        """Characterisation, not endorsement — the hole #968 leaves open.

        ``update_fields`` takes a bare ``dict`` and never materialises a model,
        so the choke-point check cannot see it: the same ``"gravel"`` that
        :meth:`update` now rejects is written straight through here. This test
        exists so the gap is visible in the suite rather than only in a
        docstring, and so that closing it later shows up as a deliberate change
        to this expectation.
        """
        repo = GaugeRepo(mock_db, "gauges")
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": {"_key": "g1", "name": "Manometer", "material": "steel", "pressure_bar": 0}}

        repo.update_fields("g1", {"material": "gravel"})

        assert coll.update.call_args.args[0]["material"] == "gravel"


# ── get_all / get_page ───────────────────────────────────────────────────────


class TestGetAll:
    def test_list_then_count_order_preserved(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.side_effect = [iter([_doc()]), iter([1])]

        items, total = repo.get_all(offset=0, limit=50)

        assert total == 1
        assert isinstance(items[0], Widget)

    def test_tenant_scope_guard_raises_when_unbound(self, mock_db):
        class ScopedRepo(BaseArangoRepository[Widget]):
            _model_cls = Widget
            is_tenant_scoped = True

        repo = ScopedRepo(mock_db, "widgets")

        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all()


class TestGetPage:
    def test_filters_sort_and_pagination_bind(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.side_effect = [iter([_doc()]), iter([1])]

        items, total = repo.get_page(
            offset=5,
            limit=10,
            filters=[("color", "==", "red")],
            sort="name",
            sort_direction="DESC",
        )

        assert total == 1
        assert isinstance(items[0], Widget)
        list_query, list_kwargs = (
            mock_db.aql.execute.call_args_list[0].args[0],
            mock_db.aql.execute.call_args_list[0].kwargs,
        )
        assert "doc.color == @v0" in list_query
        assert "SORT doc.name DESC" in list_query
        assert "LIMIT @__offset, @__limit" in list_query
        assert list_kwargs["bind_vars"]["v0"] == "red"
        assert list_kwargs["bind_vars"]["__offset"] == 5
        assert list_kwargs["bind_vars"]["__limit"] == 10


# ── find_by_field / find_one_by_field (DUP-B3) ───────────────────────────────


class TestFindByField:
    def test_plain_equality_no_sort_no_limit(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.find_by_field("name", "Hammer")

        query = mock_db.aql.execute.call_args.args[0]
        assert "doc.name == @v0" in query
        assert "SORT" not in query
        assert "LIMIT" not in query
        assert isinstance(result[0], Widget)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["v0"] == "Hammer"

    def test_sort_limit_and_extra_filters(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([_doc()])

        repo.find_by_field(
            "user_key",
            "u1",
            sort="created_at",
            sort_direction="DESC",
            offset=0,
            limit=20,
            extra_filters=[("status", "IN", ["pending", "processing"])],
        )

        query = mock_db.aql.execute.call_args.args[0]
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert "doc.user_key == @v0" in query
        assert "doc.status IN @v1" in query
        assert "SORT DATE_TIMESTAMP(doc.created_at) DESC" in query
        assert "LIMIT @__offset, @__limit" in query
        assert bind_vars["v0"] == "u1"
        assert bind_vars["v1"] == ["pending", "processing"]

    def test_find_one_returns_first(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([_doc(name="First"), _doc(name="Second")])

        result = repo.find_one_by_field("slug", "abc")

        assert isinstance(result, Widget)
        assert result.name == "First"
        assert "LIMIT @__offset, @__limit" in mock_db.aql.execute.call_args.args[0]

    def test_find_one_returns_none_when_empty(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([])

        assert repo.find_one_by_field("slug", "missing") is None


# ── unique-constraint violation → DuplicateError (issue #744) ────────────────


def _insert_error(error_message: str | None) -> DocumentInsertError:
    """Build a bare ``DocumentInsertError`` (error 1210) without a live response."""
    err = DocumentInsertError.__new__(DocumentInsertError)
    err.error_code = 1210
    err.error_message = error_message
    return err


class TestUniqueConflictExtraction:
    @pytest.mark.parametrize(
        "message",
        [
            "unique constraint violated - in index 42 of type persistent over '[\"batch_id\"]'; conflicting key: 99",
            "unique constraint violated - in index 42 of type persistent over 'batch_id'; conflicting key: 99",
            'unique constraint violated ... over ["batch_id"] ...',
        ],
    )
    def test_extracts_field_name_from_arango_message(self, message):
        assert BaseArangoRepository._extract_unique_field(message) == "batch_id"

    def test_returns_none_for_unparseable_message(self):
        assert BaseArangoRepository._extract_unique_field("boom") is None
        assert BaseArangoRepository._extract_unique_field(None) is None

    def test_describe_pairs_field_with_document_value(self):
        err = _insert_error("... over '[\"batch_id\"]' ...")
        field, value = BaseArangoRepository._describe_unique_conflict(err, {"batch_id": "H-1"})
        assert (field, value) == ("batch_id", "H-1")

    def test_describe_falls_back_to_non_misleading_placeholder(self):
        err = _insert_error("something opaque")
        assert BaseArangoRepository._describe_unique_conflict(err, {"batch_id": "H-1"}) == ("field", "")

    def test_insert_raises_duplicate_error_naming_the_real_field(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.insert.side_effect = _insert_error(
            "unique constraint violated - in index 42 of type persistent over '[\"name\"]'; conflicting key: 7"
        )

        with pytest.raises(DuplicateError) as exc:
            repo.create(Widget(name="Hammer"))

        # No more misleading key='duplicate' — the real field/value are surfaced.
        assert "name='Hammer'" in exc.value.message
        assert exc.value.details[0]["field"] == "name"
        assert exc.value.error_code == "DUPLICATE_ENTRY"

    def test_insert_reraises_non_unique_errors(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        other = DocumentInsertError.__new__(DocumentInsertError)
        other.error_code = 1234
        other.error_message = "unrelated"
        mock_db.collection.return_value.insert.side_effect = other

        with pytest.raises(DocumentInsertError):
            repo.create(Widget(name="Hammer"))


# ── write-write conflict → WriteConflictError (issue #1436) ──────────────────


def _conflict_error() -> DocumentInsertError:
    """Build a bare ``DocumentInsertError`` carrying ArangoDB's 1200 (``CONFLICT``).

    Message copied from the failure measured in issue #1436, so the test is
    anchored to the real wire shape: a *write-write conflict* reported against a
    unique index — which is emphatically not the same server answer as 1210.
    """
    err = DocumentInsertError.__new__(DocumentInsertError)
    err.error_code = 1200
    err.error_message = (
        "write-write conflict - in index care_dedup_open_unique of type persistent "
        "over 'care_dedup_key'; document key: 800067; "
        'indexed values: ["tenant-alpha/plant-basil-1/watering"]'
    )
    return err


class TestWriteConflictMapping:
    """1200 must reach the domain as its own type, not as a raw driver error.

    Before #1436 ``_insert_doc`` mapped **only** 1210, so a concurrent insert that
    lost on a unique index was handed to the service layer as a bare
    ``DocumentInsertError`` — a 500 for what is, at worst, a retryable condition.
    """

    def test_insert_maps_write_conflict_to_domain_error(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.insert.side_effect = _conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.create(Widget(name="Hammer"))

        assert exc.value.error_code == "WRITE_CONFLICT"
        assert exc.value.status_code == 409
        assert "widgets" in exc.value.message

    def test_write_conflict_is_not_a_duplicate_error(self, mock_db):
        """The two codes must stay distinguishable at the type level.

        Collapsing 1200 into ``DuplicateError`` would let every existing
        ``except DuplicateError`` swallow a timing failure as "it already
        exists" — a claim 1200 does not support.
        """
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.insert.side_effect = _conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.create(Widget(name="Hammer"))

        assert not isinstance(exc.value, DuplicateError)


# ── create_edge: the same mapping, on the path that never inherited it (#1292) ─


def _edge_conflict_error() -> DocumentInsertError:
    """ArangoDB's 1200 as a *unique edge index* reports it.

    Message copied verbatim from the backend log of ``e2e-nightly`` run
    34814941664 (2026-09-14, profile ``mobile``), where two overlapping
    get-or-create requests for the same plant raced for the ``has_care_profile``
    edge and the loser's 500 failed the suite.
    """
    err = DocumentInsertError.__new__(DocumentInsertError)
    err.error_code = 1200
    err.error_message = (
        "write-write conflict - in index idx_1876288907249713152 of type "
        "persistent over '_from'; document key: 526429; "
        'indexed values: ["plant_instances/522789"]'
    )
    return err


class TestEdgeWriteConflictMapping:
    """Edges bypass ``_insert_doc``, so #1436's mapping did not reach them.

    ``create_edge`` calls ``collection.insert`` on the driver directly. A unique
    edge index — ``has_care_profile`` over ``_from``, one care profile per plant —
    therefore rejected a losing racer with a bare ``DocumentInsertError``, which
    every caller above turns into a 500.
    """

    def test_edge_insert_maps_write_conflict_to_domain_error(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.insert.side_effect = _edge_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.create_edge("has_care_profile", "plant_instances/522789", "care_profiles/526429")

        assert exc.value.status_code == 409
        assert "has_care_profile" in exc.value.message

    def test_the_driver_message_is_not_forwarded_to_the_client(self):
        """It names an index and a document key, and ``details`` are client-visible."""
        repo = BoundRepo(MagicMock(), "widgets")
        repo._db.collection.return_value.insert.side_effect = _edge_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.create_edge("has_care_profile", "plant_instances/522789", "care_profiles/526429")

        assert "idx_1876288907249713152" not in str(exc.value.details)
        assert "526429" not in str(exc.value.details)

    def test_edge_insert_maps_a_unique_violation_to_duplicate_error(self, mock_db):
        """The same index answers ``1210`` too, and that half was missing as well.

        Measured: one four-way race in
        ``tests/integration/test_care_profile_edge_concurrency.py`` produced a
        ``1200`` and two ``1210``s against the *same* ``has_care_profile`` index.
        """
        repo = BoundRepo(mock_db, "widgets")
        err = DocumentInsertError.__new__(DocumentInsertError)
        err.error_code = 1210
        err.error_message = (
            "unique constraint violated - in index idx_1876288907249713152 of type "
            "persistent over '_from'; conflicting key: 526429"
        )
        mock_db.collection.return_value.insert.side_effect = err

        with pytest.raises(DuplicateError) as exc:
            repo.create_edge("has_care_profile", "plant_instances/522789", "care_profiles/526429")

        assert exc.value.status_code == 409
        assert not isinstance(exc.value, WriteConflictError)

    def test_other_insert_errors_still_propagate_unchanged(self, mock_db):
        """Only 1200 is translated here; nothing else is reinterpreted."""
        repo = BoundRepo(mock_db, "widgets")
        other = DocumentInsertError.__new__(DocumentInsertError)
        other.error_code = 1203  # collection or view not found
        other.error_message = "collection or view not found"
        mock_db.collection.return_value.insert.side_effect = other

        with pytest.raises(DocumentInsertError):
            repo.create_edge("has_care_profile", "plant_instances/1", "care_profiles/2")


# ── delete_edges (DUP-B10) ───────────────────────────────────────────────────


class TestDeleteEdges:
    def test_outbound_default(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter(["e1", "e2"])

        removed = repo.delete_edges("uses", "widgets/w1")

        query = mock_db.aql.execute.call_args.args[0]
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert "e._from == @vertex" in query
        assert "@@edge" in query
        assert bind_vars == {"@edge": "uses", "vertex": "widgets/w1"}
        assert removed == 2

    def test_inbound(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([])

        repo.delete_edges("uses", vertex_id="widgets/w1", direction="inbound")

        assert "e._to == @vertex" in mock_db.aql.execute.call_args.args[0]

    def test_any_direction(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([])

        repo.delete_edges("uses", vertex_id="widgets/w1", direction="any")

        assert "(e._from == @vertex OR e._to == @vertex)" in mock_db.aql.execute.call_args.args[0]

    def test_legacy_from_and_to(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.aql.execute.return_value = iter([])

        repo.delete_edges("uses", "widgets/w1", "widgets/w2")

        query = mock_db.aql.execute.call_args.args[0]
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert "e._from == @vertex" in query
        assert "e._to == @other" in query
        assert bind_vars["vertex"] == "widgets/w1"
        assert bind_vars["other"] == "widgets/w2"

    def test_missing_vertex_raises(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")

        with pytest.raises(ValueError, match="from_id or vertex_id"):
            repo.delete_edges("uses")


# ── update: the same mapping, on the two helpers that never inherited it (#1458) ─


def _update_conflict_error() -> DocumentUpdateError:
    """ArangoDB's 1200 as a *document update* reports it.

    Shape copied from the insert exemplars above — the server answers the same
    ``[HTTP 409][ERR 1200]`` for an update it could not serialize against a
    concurrent transaction holding the same document key. The message names the
    key, which is why it is not forwarded to the client.
    """
    err = DocumentUpdateError.__new__(DocumentUpdateError)
    err.error_code = 1200
    err.error_message = (
        "write-write conflict - in index idx_1876288907249713152 of type persistent "
        "over 'user_key'; document key: 526429; indexed values: [\"users/42\"]"
    )
    return err


class TestUpdateWriteConflictMapping:
    """``_update_doc``/``_update_doc_fields`` mapped 1202 and 1210 only.

    #1436 gave ``_insert_doc`` the 1200 mapping and #1292 gave it to
    ``create_edge``; the two update helpers are the siblings that were never
    served — the "guard implemented, siblings never served" class. A losing
    updater therefore reached the service layer as a bare driver exception, and
    every caller above turns that into a 500 for what is a retryable condition.
    """

    def test_full_update_maps_write_conflict_to_domain_error(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.update.side_effect = _update_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.update("w1", Widget(name="Hammer"))

        assert exc.value.error_code == "WRITE_CONFLICT"
        assert exc.value.status_code == 409
        assert "widgets" in exc.value.message

    def test_partial_update_maps_write_conflict_to_domain_error(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.update.side_effect = _update_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.update_fields("w1", {"color": "red"})

        assert exc.value.error_code == "WRITE_CONFLICT"
        assert exc.value.status_code == 409

    def test_update_write_conflict_is_not_a_duplicate_error(self, mock_db):
        """Collapsing 1200 into ``DuplicateError`` would let every existing
        ``except DuplicateError`` read a timing failure as "it already exists"."""
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.update.side_effect = _update_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.update("w1", Widget(name="Hammer"))

        assert not isinstance(exc.value, DuplicateError)

    def test_the_driver_message_is_not_forwarded_to_the_client(self):
        """It names an index and a document key, and ``details`` are client-visible."""
        repo = BoundRepo(MagicMock(), "widgets")
        repo._db.collection.return_value.update.side_effect = _update_conflict_error()

        with pytest.raises(WriteConflictError) as exc:
            repo.update("w1", Widget(name="Hammer"))

        assert "idx_1876288907249713152" not in str(exc.value.details)
        assert "526429" not in str(exc.value.details)

    def test_the_other_update_codes_still_answer_what_they_answered(self, mock_db):
        """Additive: 1202 stays ``NotFoundError`` and 1210 stays ``DuplicateError``.

        The mapping is inserted *after* both, so this is the control that the new
        branch did not shadow either of them.
        """
        repo = BoundRepo(mock_db, "widgets")

        missing = DocumentUpdateError.__new__(DocumentUpdateError)
        missing.error_code = 1202
        missing.error_message = "document not found"
        mock_db.collection.return_value.update.side_effect = missing
        with pytest.raises(NotFoundError):
            repo.update("w1", Widget(name="Hammer"))

        duplicate = DocumentUpdateError.__new__(DocumentUpdateError)
        duplicate.error_code = 1210
        duplicate.error_message = (
            "unique constraint violated - in index 42 of type persistent over '[\"name\"]'; conflicting key: 7"
        )
        mock_db.collection.return_value.update.side_effect = duplicate
        with pytest.raises(DuplicateError):
            repo.update("w1", Widget(name="Hammer"))
