"""Unit tests for ArangoActivityRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection. Assertions
target the public interface (returned ``Activity`` models, totals) and the AQL
filter clauses / bind_vars the repository builds.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import ActivityCategory
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
    def test_delegates_to_base_and_maps_models(self, repo, mock_db):
        # Base.get_all issues a list query then a count query.
        mock_db.aql.execute.side_effect = [iter([_activity_doc()]), iter([1])]

        items, total = repo.get_all(offset=0, limit=50)

        assert total == 1
        assert isinstance(items[0], Activity)
        assert items[0].name == "Topping"


class TestGetAllWithFilters:
    def test_scope_universal_filters_empty_species(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([_activity_doc()]), iter([1])]

        items, total = repo.get_all(filters={"scope": "universal"})

        assert total == 1
        assert isinstance(items[0], Activity)
        query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.species_compatible == null OR LENGTH(doc.species_compatible) == 0" in query

    def test_scope_restricted_filters_nonempty_species(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"scope": "restricted"})

        query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.species_compatible != null AND LENGTH(doc.species_compatible) > 0" in query

    def test_species_filter_lowercases_value_and_binds(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"species": "Tomato"})

        list_call = mock_db.aql.execute.call_args_list[0]
        bind_vars = list_call.kwargs["bind_vars"]
        assert bind_vars["val0"] == "tomato"

    def test_generic_field_filter_binds_equality(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(filters={"category": "pruning"})

        list_call = mock_db.aql.execute.call_args_list[0]
        assert "doc.category == @val0" in list_call.args[0]
        assert list_call.kwargs["bind_vars"]["val0"] == "pruning"

    def test_count_query_empty_cursor_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        _, total = repo.get_all(filters={"category": "pruning"})

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


class TestGetByName:
    def test_returns_first_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_activity_doc(name="Pruning")])

        result = repo.get_by_name("Pruning")

        assert isinstance(result, Activity)
        assert result.name == "Pruning"

    def test_returns_none_when_no_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_by_name("missing") is None


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

        result = repo.get_system_activities()

        assert len(result) == 1
        assert isinstance(result[0], Activity)
        assert "doc.is_system == true" in mock_db.aql.execute.call_args.args[0]


class TestGetByCategory:
    def test_filters_by_category_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_activity_doc()])

        result = repo.get_by_category("training_hst")

        assert len(result) == 1
        assert isinstance(result[0], Activity)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"category": "training_hst"}

    def test_empty_result(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_by_category("pruning") == []
