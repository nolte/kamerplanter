"""Unit tests for ArangoBotanicalFamilyRepository species-assignment queries.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.

Regression guard for the "species count is 0 everywhere" bug: the family-to-
species relation is the scalar ``family_key`` field on each species (written on
every create/import/seed path), NOT the ``belongs_to_family`` graph edge (only
ever produced by the dedup migration and absent for the vast majority of rows).
These tests pin the queries to the scalar field so a future refactor cannot
silently regress back to the empty edge traversal.

``TestSpeciesScopeConsistency`` adds the second guard (Issue #808): all three
species-facing reads must resolve the *same* set of species. Scoping the counts
without scoping the listing they link to — or the reverse — would leave the
number and the list disagreeing, which is worse than either alone. See the module
docstring of ``botanical_family_repository`` for why no tenant predicate applies
to the species catalogue today and what would have to change first.
"""

import re
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


#: Fields of the species document that express the *family assignment* rather
#: than the visibility scope. They legitimately differ between the per-family
#: reads (``s.family_key == @family_key``) and the bulk aggregate
#: (``s.family_key != null AND s.family_key != ""`` + ``COLLECT``), so they are
#: excluded when the scope predicates are compared.
_ASSIGNMENT_FIELDS = frozenset({"family_key"})


def _scope_predicate_fields(query: str) -> frozenset[str]:
    """Species-document fields a query filters on, minus the family assignment.

    Returns the set of ``s.<field>`` names appearing in the ``FILTER`` lines of
    ``query``. ``SORT`` / ``RETURN`` lines are ignored — they project or order the
    result, they do not narrow it — and :data:`_ASSIGNMENT_FIELDS` is subtracted so
    what remains is exactly the *visibility scope*: any origin, tenant or
    similar narrowing predicate the query applies on top of the family match.
    """
    fields: set[str] = set()
    for line in query.splitlines():
        stripped = line.strip()
        if not stripped.startswith("FILTER "):
            continue
        fields.update(re.findall(r"\bs\.(\w+)", stripped))
    return frozenset(fields) - _ASSIGNMENT_FIELDS


class TestSpeciesScopeConsistency:
    """The three species reads must never disagree about *which* species count.

    Regression guard for Issue #808. The bulk count feeds
    ``GET /botanical-families``, the per-family count feeds the single-row
    endpoints and the listing feeds ``GET /{key}/species`` — a user follows the
    number straight into the list. Narrowing one of them (a tenant filter, an
    ``origin`` filter, a soft-delete flag) without narrowing the other two makes
    the displayed count contradict the list it links to. These tests fail on that
    asymmetry regardless of *which* predicate is introduced, so they keep holding
    when the REQ-001 v4.0 tenant scope finally lands.
    """

    @staticmethod
    def _capture(repo, mock_db, call) -> str:
        mock_db.aql.execute.reset_mock()
        mock_db.aql.execute.return_value = iter([])
        call(repo)
        return _executed_query(mock_db)

    @pytest.fixture
    def queries(self, repo, mock_db) -> dict[str, str]:
        return {
            "listing": self._capture(repo, mock_db, lambda r: r.get_species_by_family("Rosaceae")),
            "single_count": self._capture(repo, mock_db, lambda r: r.get_species_count_by_family("Rosaceae")),
            "bulk_counts": self._capture(repo, mock_db, lambda r: r.get_species_counts_by_family()),
        }

    def test_all_three_reads_apply_the_same_scope(self, queries):
        scopes = {name: _scope_predicate_fields(query) for name, query in queries.items()}

        assert len(set(scopes.values())) == 1, (
            "The species listing, the per-family count and the bulk count must narrow "
            f"the species collection identically, but their scope predicates differ: {scopes}. "
            "Scoping the count without the list it links to (or vice versa) makes the "
            "displayed number contradict the list — see Issue #808."
        )

    def test_all_three_reads_query_the_same_collection(self, queries):
        collections = {name: frozenset(re.findall(r"\bIN\s+(\w+)", query)) for name, query in queries.items()}

        assert len(set(collections.values())) == 1, (
            f"All three reads must resolve species from the same collection, got {collections}."
        )

    def test_no_read_traverses_the_inert_family_edge(self, queries):
        offenders = [name for name, query in queries.items() if "belongs_to_family" in query]

        assert not offenders, (
            f"{offenders} fell back to the belongs_to_family edge, which only the dedup "
            "migration ever writes — it resolves to nothing for almost every species (#806)."
        )


class TestSpeciesScopeConsistencyWhenTenantScoped:
    """The same three reads stay scope-consistent once a tenant_key is applied (F-5, #808).

    ``TestSpeciesScopeConsistency`` proves the *unscoped* reads agree; this proves
    they still agree once F-5 threads the caller's active tenant in. All three must
    apply the identical hybrid-catalogue union predicate on ``s.tenant_key`` — own
    rows plus the global seeds — so a count can never contradict the list it links
    to (#816) and no read leaks a foreign tenant's species (#808 acceptance-2).
    """

    _TENANT = "tenant_x"

    @staticmethod
    def _capture(repo, mock_db, call) -> tuple[str, dict]:
        mock_db.aql.execute.reset_mock()
        mock_db.aql.execute.return_value = iter([])
        call(repo)
        first_call = mock_db.aql.execute.call_args_list[0]
        return first_call.args[0], first_call.kwargs["bind_vars"]

    @pytest.fixture
    def scoped(self, repo, mock_db) -> dict[str, tuple[str, dict]]:
        t = self._TENANT
        return {
            "listing": self._capture(repo, mock_db, lambda r: r.get_species_by_family("Rosaceae", tenant_key=t)),
            "single_count": self._capture(
                repo, mock_db, lambda r: r.get_species_count_by_family("Rosaceae", tenant_key=t)
            ),
            "bulk_counts": self._capture(repo, mock_db, lambda r: r.get_species_counts_by_family(tenant_key=t)),
        }

    def test_all_three_apply_the_identical_tenant_scope(self, scoped):
        scopes = {name: _scope_predicate_fields(query) for name, (query, _vars) in scoped.items()}

        assert set().union(*scopes.values()) == {"tenant_key"}, (
            f"Scoped reads must narrow on s.tenant_key, got {scopes}."
        )
        assert len(set(scopes.values())) == 1, (
            f"The three scoped reads must narrow the species collection identically, got {scopes} (#816)."
        )

    def test_all_three_apply_the_three_arm_hybrid_union(self, scoped):
        # Own rows OR the global seeds ("") OR legacy null — never a foreign tenant.
        for name, (query, bind_vars) in scoped.items():
            assert 's.tenant_key == @tenant_key OR s.tenant_key == "" OR s.tenant_key == null' in query, (
                f"{name} does not apply the three-arm hybrid-catalogue union (#324 both directions)."
            )
            assert bind_vars["tenant_key"] == self._TENANT, f"{name} did not bind the caller's tenant."

    def test_empty_tenant_key_still_scopes_to_global_only(self, repo, mock_db):
        # An anonymous / light-mode caller resolves to "" — the union collapses to
        # global-only, never all-tenants. The predicate must still be present.
        query, bind_vars = self._capture(repo, mock_db, lambda r: r.get_species_by_family("Rosaceae", tenant_key=""))

        assert "s.tenant_key ==" in query
        assert bind_vars["tenant_key"] == ""

    def test_unscoped_read_applies_no_tenant_predicate(self, repo, mock_db):
        # tenant_key=None is the internal/system whole-catalogue read — no scope.
        query, _vars = self._capture(repo, mock_db, lambda r: r.get_species_by_family("Rosaceae"))

        assert "tenant_key" not in query
