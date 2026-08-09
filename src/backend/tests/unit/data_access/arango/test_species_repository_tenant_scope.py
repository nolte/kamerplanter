"""ArangoSpeciesRepository.get_all tenant-scoping (F-5, #808).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary,
doubled with MagicMock. No real ArangoDB connection.

These pin the *global* species list read to the shared hybrid-catalogue union
predicate (F-4 helper) once a caller's tenant is supplied — own rows plus the
global seeds, never a foreign tenant's (#324 both directions, #808 acceptance-2).
The behavioural both-direction proof (foreign species excluded, global + own
visible) lives at the service level in
``tests/unit/domain/services/test_species_tenant_scope.py``; here we prove the
AQL the repository actually issues.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.species_repository import ArangoSpeciesRepository


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoSpeciesRepository(mock_db)


def _list_query_and_vars(mock_db) -> tuple[str, dict]:
    """The AQL + bind_vars of the *first* execute call (the listing query)."""
    call = mock_db.aql.execute.call_args_list[0]
    return call.args[0], call.kwargs["bind_vars"]


class TestGetAllTenantScope:
    def test_scoped_read_applies_the_three_arm_hybrid_union(self, repo, mock_db):
        # First execute → list cursor, second → count cursor.
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(0, 50, tenant_key="tenant_x")

        query, bind_vars = _list_query_and_vars(mock_db)
        # Own rows OR the global seeds ("") OR legacy null — never a foreign tenant.
        assert 'doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null' in query
        assert bind_vars["tenant_key"] == "tenant_x"

    def test_scoped_count_uses_the_same_predicate(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(0, 50, tenant_key="tenant_x")

        count_call = mock_db.aql.execute.call_args_list[1]
        count_query = count_call.args[0]
        # The count must narrow identically to the listing, or the total would
        # contradict the page it summarises (#816).
        assert 'doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null' in count_query
        assert count_call.kwargs["bind_vars"]["tenant_key"] == "tenant_x"

    def test_empty_tenant_key_scopes_to_global_only_never_all_tenants(self, repo, mock_db):
        # An anonymous / light-mode caller resolves to "" — the union collapses to
        # global-only, but the predicate must still be present (never an all-tenant
        # read). This is the fail-safe direction of the F-5 mechanism.
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(0, 50, tenant_key="")

        query, bind_vars = _list_query_and_vars(mock_db)
        assert "doc.tenant_key ==" in query
        assert bind_vars["tenant_key"] == ""

    def test_none_tenant_key_is_the_unscoped_system_read(self, repo, mock_db):
        # No tenant → the whole catalogue (seed/import/enrichment/calendar paths).
        # It must NOT invent a tenant predicate.
        mock_db.aql.execute.side_effect = [iter([]), iter([0])]

        repo.get_all(0, 50, tenant_key=None)

        query, _vars = _list_query_and_vars(mock_db)
        assert "tenant_key" not in query
