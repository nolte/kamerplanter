"""Unit tests for the generic ``BaseArangoRepository`` (AP-15).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. These tests pin the generic, typed
CRUD contract plus the AP-15 additions (``get_or_raise``, ``find_by_field``
options, ``find_one_by_field``, ``get_page``, ``delete_edges(direction=...)``)
and the legacy dict-compatibility mode that keeps unmigrated repositories
working.
"""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from app.common.exceptions import NotFoundError
from app.data_access.arango.base_repository import BaseArangoRepository


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


# ── Model binding / legacy dict mode ─────────────────────────────────────────


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

    def test_unbound_repo_returns_raw_dict(self, mock_db):
        # Backward compatibility: no model bound -> legacy dict behaviour.
        repo = BaseArangoRepository(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = _doc()

        result = repo.get_by_key("w1")

        assert isinstance(result, dict)
        assert result["name"] == "Hammer"

    def test_get_by_key_missing_returns_none(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_by_key("w1") is None


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

    def test_delete_returns_true(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("w1") is True

    def test_delete_swallows_error_returns_false(self, mock_db):
        repo = BoundRepo(mock_db, "widgets")
        mock_db.collection.return_value.delete.side_effect = Exception("nope")

        assert repo.delete("w1") is False


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
