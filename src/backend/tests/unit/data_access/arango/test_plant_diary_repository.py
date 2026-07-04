"""Unit tests for ArangoPlantDiaryRepository (REQ-013).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.domain.models.plant_diary_entry import PlantDiaryEntry


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPlantDiaryRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "d1", "plant_key": "p1", "entry_type": "note", "text": "looks healthy"}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> PlantDiaryEntry:
    defaults = {"entry_type": "note", "text": "looks healthy", "plant_key": "p1"}
    defaults.update(kwargs)
    return PlantDiaryEntry(**defaults)


class TestCreate:
    def test_creates_entry_and_plant_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, PlantDiaryEntry)
        # entry doc insert + has_diary_entry edge
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "plant_instances/p1"
        assert edge["_to"] == "plant_diary_entries/d1"

    def test_skips_edge_without_plant_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(plant_key="")}

        repo.create(_model(plant_key=""))

        assert coll.insert.call_count == 1


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("d1"), PlantDiaryEntry)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("d1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(text="updated")}

        result = repo.update("d1", _model(text="updated"))

        assert result.text == "updated"


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("d1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {
            "@edge": "has_diary_entry",
            "vertex": "plant_diary_entries/d1",
        }
        mock_db.collection.return_value.delete.assert_called_once_with("d1")


class TestGetByPlant:
    def test_returns_entries_and_total(self, repo, mock_db):
        # First execute = count, second = list of entries.
        mock_db.aql.execute.side_effect = [iter([3]), iter([_doc()])]

        entries, total = repo.get_by_plant("p1", offset=0, limit=10)

        assert total == 3
        assert len(entries) == 1
        assert isinstance(entries[0], PlantDiaryEntry)
        # Count query binds the plant_id.
        count_call = mock_db.aql.execute.call_args_list[0]
        assert count_call.kwargs["bind_vars"] == {"plant_id": "plant_instances/p1"}

    def test_empty_count_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        entries, total = repo.get_by_plant("p1")

        assert total == 0
        assert entries == []


class TestGetByRun:
    def test_returns_context_dicts_with_serialized_entry(self, repo, mock_db):
        row = {
            "plant_key": "p1",
            "plant_id": "PL-001",
            "plant_name": "Tomate #1",
            "diary_entry": _doc(),
        }
        mock_db.aql.execute.side_effect = [iter([1]), iter([row])]

        results, total = repo.get_by_run("run1", offset=0, limit=10)

        assert total == 1
        assert len(results) == 1
        assert results[0]["plant_key"] == "p1"
        # The diary_entry was round-tripped through PlantDiaryEntry serialisation.
        assert results[0]["diary_entry"]["text"] == "looks healthy"
        count_call = mock_db.aql.execute.call_args_list[0]
        assert count_call.kwargs["bind_vars"]["run_id"] == "planting_runs/run1"

    def test_row_without_entry_is_passed_through(self, repo, mock_db):
        row = {"plant_key": "p1", "plant_id": "PL-001", "plant_name": "Tomate", "diary_entry": None}
        mock_db.aql.execute.side_effect = [iter([0]), iter([row])]

        results, total = repo.get_by_run("run1")

        assert total == 0
        assert results[0]["diary_entry"] is None
