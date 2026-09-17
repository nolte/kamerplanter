"""#1444 — the "plant without a care profile" predicate, and its one copy.

``count_plants_without_profile`` and the two query builders beside it decide which
population the audit script reports, which number the nightly run warns about, and
which rows a later backfill migration writes. Those three must select the SAME
plants; the tests here pin what a unit test can pin without a database:

* the three builders share one predicate body, character for character — a second
  FILTER is a second answer to "how many plants are affected";
* the scoped count carries the tenant filter and the unscoped one does not;
* the empty ``tenant_key`` sentinel is refused rather than read as "all tenants".

What they deliberately do NOT do is re-implement AQL to assert on semantics: an
in-memory interpreter written from the query it checks agrees with itself by
construction. The semantics were measured against the live kind cluster instead
(#1444).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.care_reminder_repository import (
    ArangoCareReminderRepository,
    unprofiled_plant_count_aql,
    unprofiled_plant_keys_aql,
    unprofiled_plants_by_tenant_aql,
)

#: The clauses that decide the population. Spelled out here rather than imported
#: from the private constant: a test that reads the very string it asserts on would
#: stay green through any edit to it, including one that drops the removal filter.
_PREDICATE_CLAUSES = (
    "FOR plant IN @@plants",
    "FILTER plant.removed_on == null",
    "FOR profile IN @@profiles",
    "FILTER profile.plant_key == plant._key",
)


class _Aql:
    def __init__(self, result: Any) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def execute(self, query: str, bind_vars: dict | None = None):
        self.calls.append((query, dict(bind_vars or {})))
        return iter([self.result])


class _Db:
    def __init__(self, result: Any = 0) -> None:
        self.aql = _Aql(result)


def _repo(result: Any = 0) -> tuple[ArangoCareReminderRepository, _Db]:
    db = _Db(result)
    return ArangoCareReminderRepository(db), db  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "query",
    [
        unprofiled_plants_by_tenant_aql(),
        unprofiled_plant_count_aql(scoped=False),
        unprofiled_plant_count_aql(scoped=True),
        unprofiled_plant_keys_aql(),
    ],
)
@pytest.mark.parametrize("clause", _PREDICATE_CLAUSES)
def test_every_builder_selects_the_same_population(query: str, clause: str) -> None:
    """Drop ``removed_on == null`` from one builder and the count an operator reads
    stops matching the rows the migration would write."""
    assert clause in query


def test_the_removal_filter_is_on_the_plant_not_on_the_profile() -> None:
    """The order matters and is easy to get wrong the other way round.

    Filtering ``profile.removed_on`` would be a filter on a field ``CareProfile``
    does not have — always true — so every plant would count as unprofiled.
    """
    query = unprofiled_plant_count_aql(scoped=False)

    assert "FILTER plant.removed_on == null" in query
    assert "profile.removed_on" not in query


def test_the_scoped_count_filters_on_the_tenant_and_the_unscoped_one_does_not() -> None:
    assert "FILTER plant.tenant_key == @tenant_key" in unprofiled_plant_count_aql(scoped=True)
    assert "@tenant_key" not in unprofiled_plant_count_aql(scoped=False)


def test_the_breakdown_groups_on_the_plants_own_tenant() -> None:
    """A ``CareProfile`` carries no ``tenant_key`` at all — the plant is the only
    authority on its tenant, which is the rule the nightly generator follows."""
    assert "COLLECT tenant_key = plant.tenant_key" in unprofiled_plants_by_tenant_aql()


class TestCountPlantsWithoutProfile:
    def test_none_counts_the_whole_installation(self) -> None:
        repo, db = _repo(7)

        assert repo.count_plants_without_profile(tenant_key=None) == 7

        query, bind_vars = db.aql.calls[0]
        assert "tenant_key" not in bind_vars
        assert bind_vars == {"@plants": col.PLANT_INSTANCES, "@profiles": col.CARE_PROFILES}
        assert "@tenant_key" not in query

    def test_a_tenant_key_binds_the_count_to_that_tenant(self) -> None:
        repo, db = _repo(2)

        assert repo.count_plants_without_profile(tenant_key="tenant-a") == 2

        query, bind_vars = db.aql.calls[0]
        assert bind_vars["tenant_key"] == "tenant-a"
        assert "FILTER plant.tenant_key == @tenant_key" in query

    def test_the_empty_sentinel_is_refused_and_never_read_as_all_tenants(self) -> None:
        """SEC-B4: the value a tenantless caller passes by accident must not become
        the broadest possible read."""
        repo, db = _repo(99)

        with pytest.raises(ValueError, match="tenant_key"):
            repo.count_plants_without_profile(tenant_key="")

        assert db.aql.calls == [], "the refusal lands before any query is issued"

    def test_an_empty_result_counts_as_zero(self) -> None:
        """``next(cursor, 0)`` — an installation with no plants at all answers 0
        rather than raising ``StopIteration`` inside the nightly run."""
        repo, db = _repo(0)
        db.aql.execute = lambda query, bind_vars=None: iter([])  # type: ignore[assignment]

        assert repo.count_plants_without_profile(tenant_key=None) == 0
