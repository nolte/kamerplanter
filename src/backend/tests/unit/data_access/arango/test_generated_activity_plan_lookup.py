"""The one query copy-on-write turns on: which generated plan is *whose* (#1003).

``get_auto_generated_workflow_for_species`` had no tenant predicate at all, and
every plan ``ActivityPlanService`` persists is global (``tenant_key == ""``), so
it handed every tenant the same row — the read half of #1003. Adding a predicate
is the delicate part, because the obvious one is wrong in the expensive
direction: ``doc.tenant_key == @tenant_key`` matches **nothing** for a tenant
that has not forked yet, which is every tenant in every existing installation.
That refuses nobody visibly and simply loses the feature (PR #324's class, and
PR #999 records that it was live on this exact query).

So both directions are asserted here, at the query itself:

* a tenant with a private copy gets the **copy**;
* a tenant without one gets the **shared template** — not ``None``;
* a foreign tenant's copy is never returned to either of them.

The database double replays whichever predicates the query actually spells out
(:mod:`tests.support.tenant_replay`), so dropping the tenant filter turns the
first class red and narrowing it to an equality turns the second class red.
Observed against the pre-#1003 query, ``test_a_tenant_with_a_private_copy_gets_the_copy``
failed with ``assert 'wf-shared' == 'wf-a-copy'``.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

SPECIES = "solanum_lycopersicum"
OTHER_SPECIES = "cucumis_sativus"

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"

SHARED = "wf-shared"
A_COPY = "wf-a-copy"
B_COPY = "wf-b-copy"
OTHER_SPECIES_PLAN = "wf-cucumber"
AUTHORED = "wf-authored"


def _workflow(key: str, tenant_key: str, species_key: str, **overrides: Any) -> dict[str, Any]:
    return {
        "_key": key,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{key}",
        "tenant_key": tenant_key,
        "name": "Tomate",
        "auto_generated": True,
        "species_key": species_key,
        "created_at": "2026-01-01T00:00:00+00:00",
        **overrides,
    }


ROWS: list[dict[str, Any]] = [
    _workflow(SHARED, "", SPECIES),
    _workflow(A_COPY, TENANT_A, SPECIES, created_at="2026-02-01T00:00:00+00:00"),
    _workflow(B_COPY, TENANT_B, SPECIES, created_at="2026-02-02T00:00:00+00:00"),
    _workflow(OTHER_SPECIES_PLAN, "", OTHER_SPECIES),
    # An authored workflow of tenant A for the same species: not a generated
    # plan, so the lookup must not mistake it for one.
    _workflow(AUTHORED, TENANT_A, SPECIES, auto_generated=False),
]


def _repo(rows: list[dict[str, Any]] | None = None) -> ArangoTaskRepository:
    available = list(ROWS if rows is None else rows)

    def _lookup(query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        """Serve the rows the query's *literal* predicates select, then replay the rest.

        ``auto_generated``/``species_key`` compare against a literal and a bind
        var the fake understands; the tenant half is left to
        :func:`apply_predicates`, which applies exactly what the query text
        carries. A union it does not model is *relaxed*, never tightened — the
        preference between the two tiers is asserted separately below on the
        query's own ``SORT``.
        """
        rows_ = [
            row
            for row in available
            if row.get("auto_generated") and row.get("species_key") == bind_vars.get("species_key")
        ]
        if _UNION not in query:
            return apply_predicates(rows_, query, bind_vars)
        tenant_key = bind_vars["tenant_key"]
        rows_ = [row for row in rows_ if row.get("tenant_key", "") in (tenant_key, "")]
        rows_.sort(key=lambda row: (0 if row.get("tenant_key", "") == tenant_key else 1, row["created_at"]))
        return rows_[:1]

    aql = ReplayingAql().route(col.WORKFLOW_TEMPLATES, _lookup)
    return ArangoTaskRepository(ReplayingDatabase(aql))


#: The union shape the fixed query spells out; see ``_lookup`` above.
_UNION = 'doc.tenant_key == @tenant_key OR doc.tenant_key == ""'


class TestTheCallersOwnCopyWins:
    def test_a_tenant_with_a_private_copy_gets_the_copy(self):
        found = _repo().get_auto_generated_workflow_for_species(SPECIES, tenant_key=TENANT_A)

        assert found is not None
        assert found.key == A_COPY

    def test_the_other_tenant_gets_their_own_copy_not_the_first_ones(self):
        found = _repo().get_auto_generated_workflow_for_species(SPECIES, tenant_key=TENANT_B)

        assert found is not None
        assert found.key == B_COPY


class TestTheSharedTemplateIsStillReachable:
    """The #324 half: a strict predicate passes every isolation test by returning nothing."""

    def test_a_tenant_who_has_never_forked_gets_the_shared_template(self):
        rows = [row for row in ROWS if row["_key"] not in {A_COPY, B_COPY}]

        found = _repo(rows).get_auto_generated_workflow_for_species(SPECIES, tenant_key=TENANT_A)

        assert found is not None, "a strict tenant predicate matches nothing here — see #324"
        assert found.key == SHARED

    def test_the_shared_template_survives_another_tenant_forking_it(self):
        found = _repo().get_auto_generated_workflow_for_species(SPECIES, tenant_key="tenant-c")

        assert found is not None
        assert found.key == SHARED

    def test_no_tenant_at_all_still_answers_the_shared_template(self):
        """An internal caller reproduces the pre-#1003 answer exactly."""
        found = _repo().get_auto_generated_workflow_for_species(SPECIES)

        assert found is not None
        assert found.key == SHARED


class TestWhatTheLookupMustNotReturn:
    def test_a_foreign_tenants_copy_is_never_returned(self):
        rows = [row for row in ROWS if row["_key"] != A_COPY]

        found = _repo(rows).get_auto_generated_workflow_for_species(SPECIES, tenant_key=TENANT_A)

        assert found is not None
        assert found.key == SHARED

    def test_another_species_plan_is_not_returned(self):
        found = _repo().get_auto_generated_workflow_for_species("beta_vulgaris", tenant_key=TENANT_A)

        assert found is None

    def test_an_authored_workflow_of_the_same_tenant_and_species_is_not_a_plan(self):
        rows = [row for row in ROWS if row["_key"] != A_COPY]

        found = _repo(rows).get_auto_generated_workflow_for_species(SPECIES, tenant_key=TENANT_A)

        assert found is not None
        assert found.key != AUTHORED
