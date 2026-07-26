"""Unit tests for ArangoBotanicalFamilyRepository species-assignment queries.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.

Regression guard for the "species count is 0 everywhere" bug: the family-to-
species relation is the scalar ``family_key`` field on each species (written on
every create/import/seed path), NOT the ``belongs_to_family`` graph edge (only
ever produced by the dedup migration and absent for the vast majority of rows).
These tests pin the queries to the scalar field so a future refactor cannot
silently regress back to the empty edge traversal.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoBotanicalFamilyRepository(mock_db)


def _executed_query(mock_db) -> str:
    """Return the AQL text of the most recent ``aql.execute`` call."""
    call = mock_db.aql.execute.call_args
    # query is the first positional arg
    return call.args[0]


def _executed_bind_vars(mock_db) -> dict:
    return mock_db.aql.execute.call_args.kwargs["bind_vars"]


class TestGetSpeciesCountByFamily:
    def test_filters_on_scalar_family_key_not_edge(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([7])

        count = repo.get_species_count_by_family("Rosaceae")

        assert count == 7
        query = _executed_query(mock_db)
        assert "s.family_key == @family_key" in query
        # The broken edge traversal must never come back.
        assert "belongs_to_family" not in query
        assert _executed_bind_vars(mock_db) == {"family_key": "Rosaceae"}

    def test_defaults_to_zero_on_empty_cursor(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_species_count_by_family("Nonexistent") == 0


class TestGetSpeciesCountsByFamily:
    def test_aggregates_all_families_in_one_query(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter(
            [
                {"family_key": "Rosaceae", "count": 7},
                {"family_key": "Fabaceae", "count": 3},
            ]
        )

        result = repo.get_species_counts_by_family()

        assert result == {"Rosaceae": 7, "Fabaceae": 3}
        # A single aggregate round-trip — no per-family traversal.
        assert mock_db.aql.execute.call_count == 1
        query = _executed_query(mock_db)
        assert "COLLECT" in query
        assert "belongs_to_family" not in query

    def test_returns_empty_map_without_species(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.get_species_counts_by_family() == {}


class TestGetSpeciesByFamily:
    def test_filters_on_scalar_family_key_not_edge(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.get_species_by_family("Rosaceae")

        query = _executed_query(mock_db)
        assert "s.family_key == @family_key" in query
        assert "belongs_to_family" not in query
        assert _executed_bind_vars(mock_db) == {"family_key": "Rosaceae"}
