"""Unit tests for ArangoPhaseSequenceRepository.

Solitary unit tests: the injected ``StandardDatabase`` (and its ``aql`` /
``collection`` surfaces) is a genuine, owned I/O boundary, so it is doubled with
MagicMock. No real ArangoDB connection is made. Assertions target observable
behaviour through the public repository interface: returned domain models, and
the AQL query/bind_vars the repository sends to its collaborator.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.phase_sequence_repository import ArangoPhaseSequenceRepository
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPhaseSequenceRepository(mock_db)


def _def_doc(**kwargs) -> dict:
    doc = {"_key": "d1", "name": "vegetative", "typical_duration_days": 14}
    doc.update(kwargs)
    return doc


def _seq_doc(**kwargs) -> dict:
    doc = {"_key": "s1", "name": "tomato-cycle"}
    doc.update(kwargs)
    return doc


def _entry_doc(**kwargs) -> dict:
    doc = {"_key": "e1", "phase_sequence_key": "s1", "phase_definition_key": "d1", "sequence_order": 0}
    doc.update(kwargs)
    return doc


class TestGetAllDefinitions:
    def test_returns_models_and_total_without_filter(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([_def_doc()]), iter([7])]

        items, total = repo.get_all_definitions(offset=0, limit=10)

        assert total == 7
        assert len(items) == 1
        assert isinstance(items[0], PhaseDefinition)
        assert items[0].name == "vegetative"

    def test_name_filter_adds_like_clause_and_bind_var(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all_definitions(offset=5, limit=20, name_filter="veg")

        list_call = mock_db.aql.execute.call_args_list[0]
        query = list_call.args[0]
        bind_vars = list_call.kwargs["bind_vars"]
        assert "LIKE(doc.name, @name_filter, true)" in query
        assert bind_vars["name_filter"] == "%veg%"
        assert bind_vars["offset"] == 5
        assert bind_vars["limit"] == 20

    def test_count_query_excludes_pagination_bind_vars(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all_definitions(offset=0, limit=10, name_filter="veg")

        count_call = mock_db.aql.execute.call_args_list[1]
        count_bind = count_call.kwargs["bind_vars"]
        assert "offset" not in count_bind
        assert "limit" not in count_bind
        assert count_bind["name_filter"] == "%veg%"

    def test_empty_count_cursor_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        _, total = repo.get_all_definitions(offset=0, limit=10)

        assert total == 0


class TestGetDefinitionByKey:
    def test_returns_model_when_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _def_doc()

        result = repo.get_definition_by_key("d1")

        assert isinstance(result, PhaseDefinition)
        assert result.key == "d1"
        mock_db.collection.return_value.get.assert_called_once_with("d1")

    def test_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_definition_by_key("missing") is None


class TestGetDefinitionByName:
    def test_returns_first_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_def_doc(name="flowering")])

        result = repo.get_definition_by_name("flowering")

        assert isinstance(result, PhaseDefinition)
        assert result.name == "flowering"
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars == {"name": "flowering"}

    def test_returns_none_when_no_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_definition_by_name("nope") is None


class TestCreateDefinition:
    def test_inserts_with_timestamps_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _def_doc(name="seedling")}

        result = repo.create_definition(PhaseDefinition(name="seedling"))

        assert isinstance(result, PhaseDefinition)
        assert result.name == "seedling"
        inserted = coll.insert.call_args.args[0]
        assert "created_at" in inserted
        assert "updated_at" in inserted
        assert coll.insert.call_args.kwargs["return_new"] is True


class TestUpdateDefinition:
    def test_updates_with_key_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _def_doc(name="updated")}

        result = repo.update_definition("d1", PhaseDefinition(name="updated"))

        assert isinstance(result, PhaseDefinition)
        updated = coll.update.call_args.args[0]
        assert updated["_key"] == "d1"
        assert "updated_at" in updated


class TestDeleteDefinition:
    def test_returns_true_on_success(self, repo, mock_db):
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete_definition("d1") is True

    def test_returns_false_on_error(self, repo, mock_db):
        mock_db.collection.return_value.delete.side_effect = Exception("not found")

        assert repo.delete_definition("d1") is False


class TestUsageCounts:
    def test_definition_usage_count_returns_value(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([3])

        assert repo.get_definition_usage_count("d1") == 3

    def test_definition_usage_count_empty_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_definition_usage_count("d1") == 0

    def test_sequence_usage_count_returns_value(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([5])

        assert repo.get_sequence_usage_count("s1") == 5


class TestGetSequencesForDefinition:
    def test_maps_docs_to_sequences(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_seq_doc(), _seq_doc(_key="s2")])

        result = repo.get_sequences_for_definition("d1")

        assert len(result) == 2
        assert all(isinstance(s, PhaseSequence) for s in result)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"key": "d1"}


class TestGetSequenceBySpecies:
    def test_traverses_edge_with_species_id(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_seq_doc()])

        result = repo.get_sequence_by_species("sp1")

        assert isinstance(result, PhaseSequence)
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars == {"species_id": "species/sp1"}

    def test_returns_none_when_no_edge(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_sequence_by_species("sp1") is None


class TestGetSpeciesForSequence:
    def test_returns_raw_dicts_with_seq_id_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter(
            [{"key": "sp1", "scientific_name": "Solanum lycopersicum", "common_names": ["Tomate"]}]
        )

        result = repo.get_species_for_sequence("s1")

        assert result == [{"key": "sp1", "scientific_name": "Solanum lycopersicum", "common_names": ["Tomate"]}]
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"seq_id": "phase_sequences/s1"}


class TestGetAllSequences:
    def test_returns_models_and_total(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([_seq_doc()]), iter([1])]

        items, total = repo.get_all_sequences(offset=0, limit=10)

        assert total == 1
        assert isinstance(items[0], PhaseSequence)


class TestGetSequenceByKey:
    def test_returns_model_when_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _seq_doc()

        result = repo.get_sequence_by_key("s1")

        assert isinstance(result, PhaseSequence)
        assert result.key == "s1"

    def test_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_sequence_by_key("s1") is None


class TestCreateSequence:
    def test_creates_edge_to_species_when_species_key_set(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _seq_doc(species_key="sp1")}

        result = repo.create_sequence(PhaseSequence(name="cycle", species_key="sp1"))

        assert isinstance(result, PhaseSequence)
        # The edge insert is the second insert call (sequence doc, then edge).
        assert coll.insert.call_count == 2
        edge_data = coll.insert.call_args_list[1].args[0]
        assert edge_data["_from"] == "species/sp1"
        assert edge_data["_to"] == "phase_sequences/s1"

    def test_skips_edge_when_no_species_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _seq_doc(species_key="")}

        repo.create_sequence(PhaseSequence(name="cycle"))

        assert coll.insert.call_count == 1


class TestUpdateSequence:
    def test_updates_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _seq_doc(name="renamed")}

        result = repo.update_sequence("s1", PhaseSequence(name="renamed"))

        assert result.name == "renamed"
        assert coll.update.call_args.args[0]["_key"] == "s1"


class TestDeleteSequence:
    def test_cascade_deletes_entries_edges_and_returns_true(self, repo, mock_db):
        # First aql.execute returns entry keys, remaining edge/entry removals
        # return empty cursors. Collection.delete succeeds.
        mock_db.aql.execute.side_effect = [
            iter(["e1"]),  # entries_query -> entry keys
            iter([]),  # entry_uses_definition removal
            iter([]),  # seq_has_entry removal
            iter([]),  # delete entries
        ]
        mock_db.collection.return_value.delete.return_value = True

        result = repo.delete_sequence("s1")

        assert result is True
        # Sequence document itself is deleted by key.
        mock_db.collection.return_value.delete.assert_called_once_with("s1")

    def test_returns_false_when_final_delete_fails(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([]), iter([])]
        mock_db.collection.return_value.delete.side_effect = Exception("boom")

        assert repo.delete_sequence("s1") is False


class TestEntries:
    def test_get_entries_sorted_for_sequence(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_entry_doc(), _entry_doc(_key="e2", sequence_order=1)])

        result = repo.get_entries_for_sequence("s1")

        assert len(result) == 2
        assert all(isinstance(e, PhaseSequenceEntry) for e in result)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"seq_key": "s1"}

    def test_get_entry_by_key_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _entry_doc()

        result = repo.get_entry_by_key("e1")

        assert isinstance(result, PhaseSequenceEntry)
        assert result.key == "e1"

    def test_get_entry_by_key_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_entry_by_key("e1") is None

    def test_create_entry_creates_both_edges(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _entry_doc()}

        result = repo.create_entry(PhaseSequenceEntry(phase_sequence_key="s1", phase_definition_key="d1"))

        assert isinstance(result, PhaseSequenceEntry)
        # entry doc insert + seq_has_entry edge + entry_uses_definition edge
        assert coll.insert.call_count == 3
        edge1 = coll.insert.call_args_list[1].args[0]
        edge2 = coll.insert.call_args_list[2].args[0]
        assert edge1["_from"] == "phase_sequences/s1"
        assert edge1["_to"] == "phase_sequence_entries/e1"
        assert edge2["_from"] == "phase_sequence_entries/e1"
        assert edge2["_to"] == "phase_definitions/d1"

    def test_update_entry_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _entry_doc(sequence_order=3)}

        result = repo.update_entry("e1", PhaseSequenceEntry(sequence_order=3))

        assert result.sequence_order == 3

    def test_delete_entry_returns_true_on_success(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete_entry("e1") is True
        mock_db.collection.return_value.delete.assert_called_once_with("e1")

    def test_delete_entry_returns_false_on_error(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]
        mock_db.collection.return_value.delete.side_effect = Exception("nope")

        assert repo.delete_entry("e1") is False

    def test_reorder_entries_updates_each_and_returns_current(self, repo, mock_db):
        coll = mock_db.collection.return_value
        # The trailing get_entries_for_sequence call uses aql.execute.
        mock_db.aql.execute.return_value = iter([_entry_doc(sequence_order=0)])

        result = repo.reorder_entries("s1", [{"key": "e1", "sequence_order": 0}, {"key": "e2", "sequence_order": 1}])

        assert coll.update.call_count == 2
        first_update = coll.update.call_args_list[0].args[0]
        assert first_update["_key"] == "e1"
        assert first_update["sequence_order"] == 0
        assert "updated_at" in first_update
        assert len(result) == 1
