"""Unit tests for ArangoActivityRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection. Assertions
target the public interface (returned ``Activity`` models, totals) and the AQL
filter clauses / bind_vars the repository builds.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import ActivityCategory
from app.common.exceptions import NotFoundError
from app.data_access.arango.activity_repository import ArangoActivityRepository
from app.domain.models.activity import Activity


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoActivityRepository(mock_db)


def _activity_doc(**kwargs) -> dict:
    doc = {
        "_key": "a1",
        "name": "Topping",
        "category": ActivityCategory.TRAINING_HST.value,
        "sort_order": 0,
    }
    doc.update(kwargs)
    return doc


class TestGetAllNoFilter:
    def test_maps_models_and_total(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([_activity_doc()]), iter([1])]

        items, total = repo.get_all(offset=0, limit=50, tenant_key="t1")

        assert total == 1
        assert isinstance(items[0], Activity)
        assert items[0].name == "Topping"

    def test_sorts_on_a_total_order(self, repo, mock_db):
        """``get_all_pages`` pages over this read; equal sort values must not swap pages (#2015)."""
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(tenant_key="t1")

        assert "SORT doc.sort_order, doc.name, doc._key" in mock_db.aql.execute.call_args_list[0].args[0]


class TestTenantUnion:
    """#2119 (MT-023): activities are a hybrid catalogue — own ∪ global, never a foreign tenant's."""

    _ROWS = (
        _activity_doc(_key="g", tenant_key=""),
        _activity_doc(_key="a", tenant_key="tenant-a"),
        _activity_doc(_key="b", tenant_key="tenant-b"),
    )

    @staticmethod
    def _evaluate(query: str, bind_vars: dict, rows) -> list[dict]:
        """Apply the tenant arm of ``query`` to ``rows`` — the predicate the database would apply."""
        arm = '(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)'
        assert arm in query, query
        return [r for r in rows if r.get("tenant_key") in (bind_vars["tenant_key"], "", None)]

    def _read_as(self, repo, mock_db, tenant_key: str) -> list[str]:
        captured: list[tuple[str, dict]] = []

        def execute(query, bind_vars=None):
            captured.append((query, dict(bind_vars or {})))
            if "COLLECT WITH COUNT" in query:
                return iter([len(self._evaluate(query, bind_vars, self._ROWS))])
            return iter(self._evaluate(query, bind_vars, self._ROWS))

        mock_db.aql.execute.side_effect = execute
        items, total = repo.get_all(tenant_key=tenant_key)
        assert total == len(items)
        assert all(bind["tenant_key"] == tenant_key for _, bind in captured)
        return sorted(a.key for a in items)

    def test_tenant_a_reads_its_own_and_the_global_rows(self, repo, mock_db):
        assert self._read_as(repo, mock_db, "tenant-a") == ["a", "g"]

    def test_tenant_b_never_reads_tenant_a(self, repo, mock_db):
        assert self._read_as(repo, mock_db, "tenant-b") == ["b", "g"]

    def test_an_empty_tenant_reads_the_global_rows_only(self, repo, mock_db):
        assert self._read_as(repo, mock_db, "") == ["g"]

    def test_the_tenant_predicate_is_on_both_the_list_and_the_count(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"category": "pruning"}, tenant_key="tenant-a")

        for call in mock_db.aql.execute.call_args_list:
            assert "doc.tenant_key == @tenant_key" in call.args[0]
            assert call.kwargs["bind_vars"]["tenant_key"] == "tenant-a"

    def test_get_all_refuses_a_call_without_a_tenant(self, repo):
        with pytest.raises(TypeError):
            repo.get_all()

    def test_the_repository_declares_itself_tenant_scoped(self):
        assert ArangoActivityRepository.is_tenant_scoped is True


class TestGetReadableOrRaise:
    def test_a_global_row_is_readable(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _activity_doc(tenant_key="")

        assert repo.get_readable_or_raise("a1", tenant_key="tenant-a").key == "a1"

    def test_the_own_row_is_readable(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _activity_doc(tenant_key="tenant-a")

        assert repo.get_readable_or_raise("a1", tenant_key="tenant-a").key == "a1"

    def test_a_foreign_row_is_not_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _activity_doc(tenant_key="tenant-b")

        with pytest.raises(NotFoundError):
            repo.get_readable_or_raise("a1", tenant_key="tenant-a")

    def test_an_empty_tenant_does_not_read_a_tenant_row(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _activity_doc(tenant_key="tenant-b")

        with pytest.raises(NotFoundError):
            repo.get_readable_or_raise("a1", tenant_key="")


class TestGetAllWithFilters:
    def test_scope_universal_filters_empty_species(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([_activity_doc()]), iter([1])]

        items, total = repo.get_all(filters={"scope": "universal"}, tenant_key="t1")

        assert total == 1
        assert isinstance(items[0], Activity)
        query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.species_compatible == null OR LENGTH(doc.species_compatible) == 0" in query

    def test_scope_restricted_filters_nonempty_species(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"scope": "restricted"}, tenant_key="t1")

        query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.species_compatible != null AND LENGTH(doc.species_compatible) > 0" in query

    def test_species_filter_lowercases_value_and_binds(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"species": "Tomato"}, tenant_key="t1")

        list_call = mock_db.aql.execute.call_args_list[0]
        bind_vars = list_call.kwargs["bind_vars"]
        assert bind_vars["val0"] == "tomato"

    def test_generic_field_filter_binds_equality(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"category": "pruning"}, tenant_key="t1")

        list_call = mock_db.aql.execute.call_args_list[0]
        assert "doc.category == @val0" in list_call.args[0]
        assert list_call.kwargs["bind_vars"]["val0"] == "pruning"

    def test_count_query_empty_cursor_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        _, total = repo.get_all(filters={"category": "pruning"}, tenant_key="t1")

        assert total == 0


class TestGetByKey:
    def test_returns_model_when_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _activity_doc()

        result = repo.get_by_key("a1")

        assert isinstance(result, Activity)
        assert result.key == "a1"

    def test_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_by_key("a1") is None


class TestCreate:
    def test_inserts_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _activity_doc(name="LST")}

        result = repo.create(Activity(name="LST"))

        assert isinstance(result, Activity)
        assert result.name == "LST"
        inserted = coll.insert.call_args.args[0]
        assert "created_at" in inserted


class TestUpdate:
    def test_updates_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _activity_doc(name="Renamed")}

        result = repo.update("a1", Activity(name="Renamed"))

        assert result.name == "Renamed"
        assert coll.update.call_args.args[0]["_key"] == "a1"


class TestDelete:
    def test_removes_inbound_edges_then_deletes_doc(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        result = repo.delete("a1")

        assert result is True
        # Edge cleanup query targets the activity _id.
        edge_call = mock_db.aql.execute.call_args
        assert edge_call.kwargs["bind_vars"] == {"aid": "activities/a1"}
        mock_db.collection.return_value.delete.assert_called_once_with("a1")

    def test_returns_false_when_doc_delete_fails(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.side_effect = Exception("nope")

        assert repo.delete("a1") is False


class TestGetSystemActivities:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_activity_doc(is_system=True)])

        result = repo.get_system_activities(tenant_key="t1")

        assert len(result) == 1
        assert isinstance(result[0], Activity)
        query = mock_db.aql.execute.call_args.args[0]
        assert "doc.is_system == true" in query
        assert "doc.tenant_key == @tenant_key" in query
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"tenant_key": "t1"}


class TestGetByCategory:
    def test_filters_by_category_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_activity_doc()])

        result = repo.get_by_category("training_hst", tenant_key="t1")

        assert len(result) == 1
        assert isinstance(result[0], Activity)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"category": "training_hst", "tenant_key": "t1"}
        assert "doc.tenant_key == @tenant_key" in mock_db.aql.execute.call_args.args[0]

    def test_empty_result(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_by_category("pruning", tenant_key="t1") == []
