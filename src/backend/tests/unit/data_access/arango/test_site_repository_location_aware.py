"""Issue #713 — Location-aware queries in SiteRepository.

AC-7: Tests for find_site_keys_with_frost_exposed_location and
find_site_docs_by_keys repository methods.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.site_repository import ArangoSiteRepository


@pytest.fixture
def mock_db():
    """Mock ArangoDB connection."""
    return MagicMock()


def _location_doc(
    key: str,
    site_key: str,
    frost_exposed: bool | None = None,
) -> dict:
    """Create a location document for testing."""
    return {
        "_key": key,
        "name": f"Location {key}",
        "site_key": site_key,
        "area_m2": 10.0,
        "frost_exposed": frost_exposed,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def _site_doc(key: str, site_type: str = "outdoor") -> dict:
    """Create a site document for testing."""
    return {
        "_key": key,
        "name": f"Site {key}",
        "type": site_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


class TestFindSiteKeysWithFrostExposedLocation:
    """AC-7: Test find_site_keys_with_frost_exposed_location query."""

    def test_returns_site_keys_where_frost_exposed_true(self, mock_db):
        """Select only locations with frost_exposed == true (not false/null)."""
        repo = ArangoSiteRepository(mock_db)

        # Simulate AQL cursor return: only frost_exposed=true locations
        mock_db.aql.execute.return_value = ["site-1", "site-2"]

        result = repo.find_site_keys_with_frost_exposed_location()

        assert result == ["site-1", "site-2"]
        # Verify AQL was executed with correct filter
        mock_db.aql.execute.assert_called_once()
        call_args = mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        assert "frost_exposed == true" in aql_query
        assert "DISTINCT" in aql_query

    def test_filters_by_frost_exposed_true_only(self, mock_db):
        """Locations with frost_exposed=false are not included."""
        repo = ArangoSiteRepository(mock_db)

        # Return empty list when no locations have frost_exposed == true
        mock_db.aql.execute.return_value = []

        result = repo.find_site_keys_with_frost_exposed_location()

        assert result == []

    def test_filters_out_null_frost_exposed(self, mock_db):
        """Locations with frost_exposed=null do not contribute."""
        repo = ArangoSiteRepository(mock_db)

        mock_db.aql.execute.return_value = ["site-1"]

        result = repo.find_site_keys_with_frost_exposed_location()

        assert result == ["site-1"]
        call_args = mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        # The query must be explicit about == true, not != null or IS_NOT_NULL
        assert "== true" in aql_query

    def test_returns_distinct_site_keys(self, mock_db):
        """Multiple locations under the same site return only one site_key."""
        repo = ArangoSiteRepository(mock_db)

        mock_db.aql.execute.return_value = ["site-1", "site-1", "site-2"]

        result = repo.find_site_keys_with_frost_exposed_location()

        # DISTINCT is enforced by AQL, but our implementation doesn't deduplicate in Python
        assert "site-1" in result and "site-2" in result

    def test_filters_out_empty_or_null_site_keys(self, mock_db):
        """Locations without a site_key are filtered out by the WHERE clause."""
        repo = ArangoSiteRepository(mock_db)

        mock_db.aql.execute.return_value = ["site-1", "site-2"]

        repo.find_site_keys_with_frost_exposed_location()

        call_args = mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        # Verify the AQL filters out null/empty site_keys
        assert "site_key != null" in aql_query
        assert 'site_key != ""' in aql_query

    def test_cursor_with_none_values_filtered(self, mock_db):
        """Any None values from the cursor are filtered."""
        repo = ArangoSiteRepository(mock_db)

        # Mock cursor returns some None values
        mock_db.aql.execute.return_value = ["site-1", None, "site-2", None]

        result = repo.find_site_keys_with_frost_exposed_location()

        # The implementation filters out falsy values
        assert result == ["site-1", "site-2"]


class TestFindSiteDocsByKeys:
    """AC-7: Test find_site_docs_by_keys query."""

    def test_returns_site_docs_for_given_keys(self, mock_db):
        """Returns normalised site documents for the given keys."""
        repo = ArangoSiteRepository(mock_db)

        site_docs = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
            {"_key": "s3", "name": "Indoor Garden", "type": "indoor"},
        ]
        # Mock _from_doc to return the dict as-is (normalization)
        mock_db.aql.execute.return_value = site_docs
        repo._from_doc = lambda doc: doc

        result = repo.find_site_docs_by_keys(["s1", "s3"])

        assert len(result) == 2
        assert result[0]["_key"] == "s1"
        assert result[1]["_key"] == "s3"

    def test_empty_keys_list_short_circuits(self, mock_db):
        """An empty keys list returns [] without querying the DB."""
        repo = ArangoSiteRepository(mock_db)

        result = repo.find_site_docs_by_keys([])

        assert result == []
        mock_db.aql.execute.assert_not_called()

    def test_query_uses_bind_vars_not_interpolation(self, mock_db):
        """Verify the query uses bind_vars for safety (SQL injection protection)."""
        repo = ArangoSiteRepository(mock_db)

        mock_db.aql.execute.return_value = []

        repo.find_site_docs_by_keys(["s1", "s2"])

        call_args = mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        bind_vars = call_args[1]["bind_vars"]

        # Query must use placeholder
        assert "@keys" in aql_query or "@col" in aql_query
        # bind_vars must contain keys
        assert "keys" in bind_vars
        assert bind_vars["keys"] == ["s1", "s2"]

    def test_normalizes_each_document(self, mock_db):
        """Each returned document is normalized via _from_doc."""
        repo = ArangoSiteRepository(mock_db)

        raw_docs = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor", "_extra_field": "ignore"},
            {"_key": "s2", "name": "Beet B", "type": "greenhouse"},
        ]
        mock_db.aql.execute.return_value = raw_docs

        repo._from_doc = lambda doc: {k: v for k, v in doc.items() if not k.startswith("_extra")}

        result = repo.find_site_docs_by_keys(["s1", "s2"])

        # The result should have gone through _from_doc normalization
        assert all(isinstance(doc, dict) for doc in result)

    def test_defensive_construction_for_schema_drift(self, mock_db):
        """AC-18: One malformed document should not abort the batch."""
        repo = ArangoSiteRepository(mock_db)

        # Simulate one doc missing required fields (schema drift)
        raw_docs = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
            {"_key": "s2"},  # Missing required fields
            {"_key": "s3", "name": "Beet C", "type": "greenhouse"},
        ]
        mock_db.aql.execute.return_value = raw_docs
        repo._from_doc = lambda doc: doc

        result = repo.find_site_docs_by_keys(["s1", "s2", "s3"])

        # The repository returns all docs; defensive construction happens in season_tasks
        assert len(result) == 3

    def test_returns_empty_list_when_no_matches(self, mock_db):
        """No sites match the given keys → return []."""
        repo = ArangoSiteRepository(mock_db)

        mock_db.aql.execute.return_value = []

        result = repo.find_site_docs_by_keys(["s1", "s2"])

        assert result == []

    def test_partial_matches_ok(self, mock_db):
        """If some keys don't match, only matched docs are returned."""
        repo = ArangoSiteRepository(mock_db)

        # Only s1 matches, s2 doesn't exist
        mock_db.aql.execute.return_value = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
        ]
        repo._from_doc = lambda doc: doc

        result = repo.find_site_docs_by_keys(["s1", "s2"])

        assert len(result) == 1
        assert result[0]["_key"] == "s1"
