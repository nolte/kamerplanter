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
from arango.exceptions import DocumentInsertError
from pydantic import BaseModel, Field

from app.common.exceptions import DuplicateError, NotFoundError, ValidationError
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
        assert "SORT doc.created_at DESC" in query
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
