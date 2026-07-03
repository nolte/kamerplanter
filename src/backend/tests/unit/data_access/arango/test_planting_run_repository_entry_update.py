"""REQ-013 GAP-B9 — ArangoPlantingRunRepository.update_entry edge-sync + null-write.

Solitary unit tests: the injected ``StandardDatabase`` (and its ``aql`` /
``collection`` surfaces) is a genuine, owned I/O boundary, so it is doubled with
MagicMock. No real ArangoDB connection is made. Assertions target the update
payload the repository writes and the ``entry_for_species`` edge maintenance.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.domain.models.planting_run import PlantingRunEntry


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPlantingRunRepository(mock_db)


def _entry(**overrides) -> PlantingRunEntry:
    data = {
        "_key": "e1",
        "run_key": "r1",
        "species_key": "species_tomato",
        "quantity": 3,
        "id_prefix": "TO",
    }
    data.update(overrides)
    return PlantingRunEntry(**data)


class TestUpdateEntry:
    def test_writes_null_for_cleared_nullable_field(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = {"_key": "e1", "species_key": "species_tomato"}
        coll.update.return_value = {"new": _entry(notes=None).model_dump(by_alias=True, mode="json")}

        repo.update_entry("e1", _entry(notes=None))

        # exclude_none must NOT be used: the payload keeps notes=None so Arango
        # (keepNull=True) overwrites the old value instead of preserving it.
        payload = coll.update.call_args.args[0]
        assert "notes" in payload
        assert payload["notes"] is None

    def test_species_change_relinks_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = {"_key": "e1", "species_key": "species_tomato"}
        coll.update.return_value = {"new": _entry(species_key="species_basil").model_dump(by_alias=True, mode="json")}

        repo.update_entry("e1", _entry(species_key="species_basil"))

        # Old edge removed via AQL, new edge inserted via create_edge.
        remove_calls = [c for c in mock_db.aql.execute.call_args_list if "REMOVE" in c.args[0]]
        assert len(remove_calls) == 1
        assert col.ENTRY_FOR_SPECIES in remove_calls[0].args[0]

        edge_inserts = [
            c for c in coll.insert.call_args_list if c.args and c.args[0].get("_to") == f"{col.SPECIES}/species_basil"
        ]
        assert len(edge_inserts) == 1
        assert edge_inserts[0].args[0]["_from"] == f"{col.PLANTING_RUN_ENTRIES}/e1"

    def test_no_species_change_leaves_edge_untouched(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = {"_key": "e1", "species_key": "species_tomato"}
        coll.update.return_value = {"new": _entry(quantity=9).model_dump(by_alias=True, mode="json")}

        repo.update_entry("e1", _entry(quantity=9))

        remove_calls = [c for c in mock_db.aql.execute.call_args_list if "REMOVE" in c.args[0]]
        assert remove_calls == []
        coll.insert.assert_not_called()
