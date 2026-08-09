"""ArangoSpeciesRepository.get_cultivars tenant-scoping (C-3, #1090).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary,
doubled with MagicMock. No real ArangoDB connection.

These pin the *cultivar list* read to the shared hybrid-catalogue union predicate
(the F-4 helper) once a caller's tenant is supplied — own rows plus the global
catalogue, never a foreign tenant's (#324 both directions). The behavioural
both-direction proof lives at the service level in
``tests/unit/domain/services/test_cultivar_tenant_scope.py``; here we prove the
AQL the repository actually issues, because a fake-DB behavioural test alone
cannot see whether the narrowing happens in the query or nowhere.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.species_repository import ArangoSpeciesRepository

#: The exact three-arm union the shared helper emits. Pinned verbatim: a strict
#: ``== @tenant_key`` filter would reproduce #324 on the legacy population that
#: migration v0038 deliberately left global.
_UNION = 'doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null'


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.aql.execute.return_value = iter([])
    return db


@pytest.fixture
def repo(mock_db):
    return ArangoSpeciesRepository(mock_db)


def _query_and_vars(mock_db) -> tuple[str, dict]:
    call = mock_db.aql.execute.call_args
    return call.args[0], call.kwargs["bind_vars"]


class TestGetCultivarsTenantScope:
    def test_scoped_read_applies_the_three_arm_hybrid_union(self, repo, mock_db):
        repo.get_cultivars("sp_basil", tenant_key="tenant_x")

        query, bind_vars = _query_and_vars(mock_db)
        assert _UNION in query
        assert bind_vars["tenant_key"] == "tenant_x"

    def test_scoped_read_still_narrows_to_the_species(self, repo, mock_db):
        # The union is AND-composed with the species filter — the scoping must not
        # silently widen the read to every species' cultivars.
        repo.get_cultivars("sp_basil", tenant_key="tenant_x")

        query, bind_vars = _query_and_vars(mock_db)
        assert "doc.species_key == @species_key" in query
        assert bind_vars["species_key"] == "sp_basil"

    def test_the_tenant_value_is_bound_never_interpolated(self, repo, mock_db):
        # Injection surface: an attacker-controlled tenant key must never reach the
        # query text (SCR-007).
        repo.get_cultivars("sp_basil", tenant_key='" OR 1==1 //')

        query, bind_vars = _query_and_vars(mock_db)
        assert "OR 1==1" not in query
        assert bind_vars["tenant_key"] == '" OR 1==1 //'

    def test_empty_tenant_key_scopes_to_global_only_never_all_tenants(self, repo, mock_db):
        # An anonymous / light-mode caller resolves to "" (P4, REQ-027): the union
        # collapses to global-only, but the predicate must still be present — never
        # an unfiltered all-tenant read, and never an error.
        repo.get_cultivars("sp_basil", tenant_key="")

        query, bind_vars = _query_and_vars(mock_db)
        assert _UNION in query
        assert bind_vars["tenant_key"] == ""

    def test_none_tenant_key_is_the_unscoped_system_read(self, repo, mock_db):
        # P5: seed loaders and dereference paths must keep seeing every row — their
        # own ownership-aware matching depends on it (``seed_data.seed_cultivars``).
        repo.get_cultivars("sp_basil", tenant_key=None)

        query, bind_vars = _query_and_vars(mock_db)
        assert "tenant_key" not in query
        assert "tenant_key" not in bind_vars
        assert "species_key" in query

    def test_the_default_call_is_the_unscoped_system_read(self, repo, mock_db):
        # The signature is keyword-only with a ``None`` default, so every pre-#1090
        # caller (four seeders, six dereference sites) keeps its old behaviour.
        repo.get_cultivars("sp_basil")

        query, _bind_vars = _query_and_vars(mock_db)
        assert "tenant_key" not in query

    def test_scoped_rows_are_mapped_onto_the_cultivar_model(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter(
            [{"_key": "cv_1", "name": "Genovese", "species_key": "sp_basil", "tenant_key": ""}]
        )

        rows = repo.get_cultivars("sp_basil", tenant_key="tenant_x")

        assert [(c.key, c.name) for c in rows] == [("cv_1", "Genovese")]

    def test_the_repository_is_not_strict_tenant_scoped(self, repo):
        # P4: flipping ``is_tenant_scoped`` on would make a tenant-less read raise,
        # breaking the anonymous / light-mode catalogue (REQ-027) and every seeder.
        # The hybrid catalogue is guarded by the union predicate, not by strict mode.
        # Pinned for the cultivar sub-repository too — that is the one holding the
        # ``cultivars`` collection this package scopes.
        assert repo.is_tenant_scoped is False
        assert repo._cultivars.is_tenant_scoped is False  # noqa: SLF001 — pins the sub-repo's mode
