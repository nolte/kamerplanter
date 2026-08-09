"""Unit tests for ArangoSpeciesRepository.search family filtering.

Solitary unit tests with a MagicMock ``StandardDatabase``. Regression guard:
``search`` must filter species by the scalar ``family_key`` field (AND-composed
with the optional name predicate), never via the unmaintained
``belongs_to_family`` graph edge — the old traversal used the wrong direction
(``OUTBOUND``) and was silently skipped whenever a name was also supplied.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.species_repository import ArangoSpeciesRepository


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoSpeciesRepository(mock_db)


def _last_query(mock_db) -> str:
    return mock_db.aql.execute.call_args.args[0]


def _last_bind_vars(mock_db) -> dict:
    return mock_db.aql.execute.call_args.kwargs["bind_vars"]


class TestSearchByFamily:
    def test_family_only_filters_on_scalar_field(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(family_key="Rosaceae")

        query = _last_query(mock_db)
        assert "family_key" in query
        assert "belongs_to_family" not in query
        assert "OUTBOUND" not in query
        assert "Rosaceae" in _last_bind_vars(mock_db).values()

    def test_name_and_family_compose_with_and(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa", family_key="Rosaceae")

        query = _last_query(mock_db)
        # Both predicates must be present — the old code dropped the family
        # filter entirely when a name was supplied.
        assert query.count("FILTER") == 2
        assert "scientific_name" in query
        assert "family_key" in query
        assert set(_last_bind_vars(mock_db).values()) == {"%Rosa%", "Rosaceae"}


class TestSearchTenantScope:
    """SEC-005 (#808): a tenant-scoped search unions the hybrid catalogue.

    ``search`` has no HTTP caller today, but once given a ``tenant_key`` it must
    narrow exactly like ``get_all`` — own rows plus the global seeds, never a
    foreign tenant's — so a future search endpoint cannot re-open the leak F-5
    closed. Values stay bound, never interpolated.
    """

    def test_scoped_search_applies_the_three_arm_hybrid_union(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa", tenant_key="tenant_x")

        query = _last_query(mock_db)
        assert 'doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null' in query
        assert "doc.scientific_name LIKE @name" in query
        bind_vars = _last_bind_vars(mock_db)
        assert bind_vars["tenant_key"] == "tenant_x"
        assert bind_vars["name"] == "%Rosa%"

    def test_scoped_search_composes_family_with_the_union(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(family_key="Rosaceae", tenant_key="tenant_x")

        query = _last_query(mock_db)
        assert "doc.family_key == @family_key" in query
        assert "doc.tenant_key == @tenant_key" in query
        assert _last_bind_vars(mock_db)["family_key"] == "Rosaceae"

    def test_none_tenant_key_is_the_unscoped_search(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa", tenant_key=None)

        assert "tenant_key" not in _last_query(mock_db)


class TestSearchNameEscaping:
    """SCR-007: user-typed LIKE metacharacters must be escaped, not honoured.

    Without escaping, ``%``/``_`` act as wildcards and a trailing ``\\`` can
    swallow the closing wildcard, turning a literal name search into a pattern
    match. The bound LIKE value must carry each metacharacter backslash-escaped.
    """

    def test_percent_is_escaped(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa%")

        assert "%Rosa\\%%" in _last_bind_vars(mock_db).values()

    def test_underscore_is_escaped(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa_")

        assert "%Rosa\\_%" in _last_bind_vars(mock_db).values()

    def test_backslash_is_escaped(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="Rosa\\")

        assert "%Rosa\\\\%" in _last_bind_vars(mock_db).values()

    def test_backslash_is_escaped_before_wildcards(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.search(name="a%b_c\\d")

        # Backslash escaped first, then % and _, so no metacharacter leaks
        # through and the pre-existing backslash is not read as an escape.
        assert "%a\\%b\\_c\\\\d%" in _last_bind_vars(mock_db).values()
