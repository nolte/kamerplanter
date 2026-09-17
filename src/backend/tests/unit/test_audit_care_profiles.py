"""#1444 — what the care-profile audit decides, and what it refuses to say.

``scripts/audit_care_profiles.py`` answers "how many non-removed plants have no
``CareProfile``, per tenant?" It reads only. The counting itself is arithmetic;
what this file pins is everything around it that can make a count mean the wrong
thing:

* the exit code separates "found rows" (3) from "nothing found" (0) from "could
  not read" (1), so ``audit_care_profiles.py && echo clean`` cannot print ``clean``
  over a listing, and an uninitialised database cannot pass for an empty one;
* the predicate comes from the repository module, so the audit, the nightly
  warning and the later backfill migration select the same population — the script
  carries no ``FOR plant IN`` of its own;
* the number a migration is sized against (``expected_profiles_to_create``) is the
  same number the report prints, summed from the rows shown rather than from a
  second query that could disagree with them;
* the tenantless row is reported rather than dropped: those plants are invisible
  to every tenant-scoped generator run, which is exactly why an audit must show
  them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from arango.exceptions import ArangoError

from app.data_access.arango import collections as col

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit_care_profiles.py"
_spec = importlib.util.spec_from_file_location("audit_care_profiles", _SCRIPT)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

_TOTALS = {"plants_total": 10, "plants_active": 8, "profiles_total": 5, "orphan_profiles": 1}


class _FakeAql:
    """Answers each of the script's four queries by what it asks for.

    Dispatch on the query TEXT rather than on call order: the script is free to
    reorder its reads, and a fake that hands the tenant breakdown to the totals
    query would make every assertion below describe a shape the database never
    produces.
    """

    def __init__(self, *, totals: dict, by_tenant: list[dict], sample: list[dict], tenants: list[dict]) -> None:
        self._totals = totals
        self._by_tenant = by_tenant
        self._sample = sample
        self._tenants = tenants
        self.queries: list[str] = []
        self.bind_vars: list[dict] = []

    def execute(self, query: str, bind_vars: dict | None = None):
        self.queries.append(query)
        self.bind_vars.append(dict(bind_vars or {}))
        if "plants_total" in query:
            return iter([self._totals])
        if "COLLECT tenant_key = plant.tenant_key" in query:
            return iter(self._by_tenant)
        if "FOR plant IN" in query:
            return iter(self._sample)
        if col.TENANTS in query:
            return iter(self._tenants)
        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(self, aql: _FakeAql, *, missing_collection: str | None = None, raises: Exception | None = None):
        self.aql = aql
        self._missing = missing_collection
        self._raises = raises

    def has_collection(self, name: str) -> bool:
        if self._raises is not None:
            raise self._raises
        return name != self._missing


def _install_db(monkeypatch, db: _FakeDb) -> None:
    """Replace ``ArangoClient`` so ``main()`` opens the fake and never a socket.

    The class is patched on the ``arango`` package, which is where the script
    imports it from inside ``main()``. A live ArangoDB is reachable on this
    developer's machine (it is how a unit test that touches the database passes
    locally and fails in CI), so an unpatched run here would be green for the wrong
    reason.
    """
    import arango

    monkeypatch.setattr(arango, "ArangoClient", lambda hosts: _FakeClient(db))


class _FakeClient:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def db(self, *_args: Any, **_kwargs: Any) -> _FakeDb:
        return self._db


def _run(monkeypatch, capsys, *, by_tenant, totals=None, sample=None, tenants=None, argv=("audit",)):
    aql = _FakeAql(
        totals=totals or dict(_TOTALS),
        by_tenant=by_tenant,
        sample=sample or [],
        tenants=tenants or [],
    )
    db = _FakeDb(aql)
    _install_db(monkeypatch, db)
    monkeypatch.setattr(sys, "argv", list(argv))
    code = audit.main()
    return code, capsys.readouterr(), aql


# ── The report itself ────────────────────────────────────────────────────────


class TestBuildReport:
    def test_the_migration_figure_is_the_sum_of_the_rows_shown(self) -> None:
        """One number, one source. A separate count query could disagree with the
        breakdown, and if it ever did, the disagreeing pair would be the figure an
        operator reads and the figure a migration writes."""
        report = audit.build_report(
            [{"tenant_key": "t1", "missing": 3}, {"tenant_key": "t2", "missing": 4}],
            plants_total=10,
            plants_active=9,
            profiles_total=2,
            orphan_profiles=0,
            sample=[],
            tenant_names={},
        )

        assert report["missing_total"] == 7
        assert report["expected_profiles_to_create"] == 7
        assert report["tenants_affected"] == 2

    def test_removed_plants_are_derived_and_not_counted_as_missing(self) -> None:
        """A removed plant needs no reminder — the nightly run skips its profile —
        so counting it would inflate the population a migration is sized against."""
        report = audit.build_report(
            [{"tenant_key": "t1", "missing": 1}],
            plants_total=10,
            plants_active=6,
            profiles_total=5,
            orphan_profiles=2,
            sample=[],
            tenant_names={},
        )

        assert report["plants_removed"] == 4
        assert report["missing_total"] == 1

    def test_the_sample_is_capped_and_says_so_while_the_counts_are_not(self) -> None:
        sample = [{"key": f"p{i}", "tenant_key": "t1"} for i in range(audit.KEY_LISTING_LIMIT + 5)]

        report = audit.build_report(
            [{"tenant_key": "t1", "missing": 500}],
            plants_total=500,
            plants_active=500,
            profiles_total=0,
            orphan_profiles=0,
            sample=sample,
            tenant_names={},
        )

        assert len(report["sample_keys"]) == audit.KEY_LISTING_LIMIT
        assert report["sample_truncated"] is True
        assert report["missing_total"] == 500, "the count is never capped by the listing"


class TestLabelling:
    def test_the_tenantless_row_is_spelled_out(self) -> None:
        """Shown as an empty column it reads as a formatting glitch — and it is the
        row no tenant-scoped run will ever process."""
        assert "no tenant" in audit.label_for(audit.TENANTLESS, {})

    def test_a_known_tenant_carries_its_name_beside_its_key(self) -> None:
        assert audit.label_for("t1", {"t1": "Balkon"}) == "t1 (Balkon)"

    def test_an_unknown_tenant_still_reports_its_key(self) -> None:
        """A tenant row whose ``tenants`` document is gone must not vanish from the
        report — its plants are just as unprofiled."""
        assert audit.label_for("t9", {"t1": "Balkon"}) == "t9"


class TestRender:
    def test_a_clean_installation_says_no_backfill_is_warranted(self) -> None:
        report = audit.build_report(
            [], plants_total=4, plants_active=4, profiles_total=4, orphan_profiles=0, sample=[], tenant_names={}
        )

        text = "\n".join(audit.render(report, {}))

        assert "no backfill" in text

    def test_findings_name_the_exact_number_a_backfill_would_write(self) -> None:
        report = audit.build_report(
            [{"tenant_key": "t1", "missing": 12}],
            plants_total=20,
            plants_active=20,
            profiles_total=8,
            orphan_profiles=0,
            sample=[],
            tenant_names={},
        )

        text = "\n".join(audit.render(report, {"t1": "Balkon"}))

        assert "12" in text
        assert "Balkon" in text
        assert "must report 0" in text, "the re-run is the migration's positive control"


# ── Exit codes ───────────────────────────────────────────────────────────────


class TestExitCodes:
    def test_nothing_missing_exits_zero(self, monkeypatch, capsys) -> None:
        code, out, _aql = _run(monkeypatch, capsys, by_tenant=[])

        assert code == 0
        assert "Exit 3" not in out.out

    def test_findings_exit_three(self, monkeypatch, capsys) -> None:
        """Not 0: ``audit_care_profiles.py && echo clean`` printed ``clean`` over a
        rogue listing in the sibling audit, which is why that script grew this code
        and why this one starts with it."""
        code, out, _aql = _run(monkeypatch, capsys, by_tenant=[{"tenant_key": "t1", "missing": 2}])

        # The literal, NOT `audit.EXIT_FINDINGS`. Written against the constant, this
        # test stayed green while `EXIT_FINDINGS = 0` was injected — it reached the
        # rule through the very value the rule is about, and the audit would have
        # reported an all-clear over a listing. Measured on 2026-09-17.
        assert code == 3
        assert "2" in out.out

    def test_the_findings_code_is_distinct_from_success(self) -> None:
        """``audit_care_profiles.py && echo clean`` must not print ``clean``."""
        assert audit.EXIT_FINDINGS not in (0, None)

    def test_a_missing_collection_exits_one_and_reports_nothing(self, monkeypatch, capsys) -> None:
        """``plant_instances`` is created at bootstrap, so its absence means the wrong
        database — not an installation with no plants. Reporting "0 missing" here
        would be an all-clear over a collection that was never read."""
        aql = _FakeAql(totals=dict(_TOTALS), by_tenant=[], sample=[], tenants=[])
        db = _FakeDb(aql, missing_collection=col.PLANT_INSTANCES)
        _install_db(monkeypatch, db)
        monkeypatch.setattr(sys, "argv", ["audit"])

        code = audit.main()
        out = capsys.readouterr()

        assert code == 1
        assert col.PLANT_INSTANCES in out.err
        assert aql.queries == [], "nothing is counted once the target is known to be wrong"

    @pytest.mark.parametrize("collection", [col.CARE_PROFILES, col.TENANTS])
    def test_every_bootstrap_collection_is_checked_not_just_the_first(self, monkeypatch, capsys, collection) -> None:
        """The sibling audit shipped with exactly this gap: it hard-failed on one
        collection and defaulted another to ``[]``, printing a clean bill of health
        for the half it never read."""
        aql = _FakeAql(totals=dict(_TOTALS), by_tenant=[], sample=[], tenants=[])
        _install_db(monkeypatch, _FakeDb(aql, missing_collection=collection))
        monkeypatch.setattr(sys, "argv", ["audit"])

        assert audit.main() == 1
        assert collection in capsys.readouterr().err

    def test_an_unreachable_database_exits_one(self, monkeypatch, capsys) -> None:
        aql = _FakeAql(totals=dict(_TOTALS), by_tenant=[], sample=[], tenants=[])
        _install_db(monkeypatch, _FakeDb(aql, raises=ArangoError("no route to host")))
        monkeypatch.setattr(sys, "argv", ["audit"])

        assert audit.main() == 1
        assert "does not create anything" in capsys.readouterr().err

    def test_a_connection_error_is_caught_although_it_is_not_an_arango_error(self, monkeypatch, capsys) -> None:
        """python-arango raises the BUILT-IN ``ConnectionAbortedError`` when every
        configured host fails — an ``OSError``, not an ``ArangoError``. Catching only
        the latter turns a mistyped host into a raw traceback."""
        aql = _FakeAql(totals=dict(_TOTALS), by_tenant=[], sample=[], tenants=[])
        _install_db(monkeypatch, _FakeDb(aql, raises=ConnectionAbortedError("all hosts failed")))
        monkeypatch.setattr(sys, "argv", ["audit"])

        assert audit.main() == 1


# ── Output and the shared predicate ──────────────────────────────────────────


class TestOutput:
    def test_the_default_run_prints_both_the_summary_and_the_json(self, monkeypatch, capsys) -> None:
        code, out, _aql = _run(monkeypatch, capsys, by_tenant=[{"tenant_key": "t1", "missing": 2}])

        assert code == 3
        assert "plants WITHOUT a care profile" in out.out
        assert '"expected_profiles_to_create": 2' in out.out

    def test_the_json_flag_prints_json_alone_so_it_can_be_piped(self, monkeypatch, capsys) -> None:
        import json

        code, out, _aql = _run(
            monkeypatch,
            capsys,
            by_tenant=[{"tenant_key": "t1", "missing": 2}],
            argv=("audit", "--json"),
        )

        assert code == 3
        assert json.loads(out.out)["expected_profiles_to_create"] == 2

    def test_the_tenant_breakdown_survives_into_the_report(self, monkeypatch, capsys) -> None:
        import json

        _code, out, _aql = _run(
            monkeypatch,
            capsys,
            by_tenant=[{"tenant_key": "t1", "missing": 2}, {"tenant_key": "", "missing": 1}],
            tenants=[{"key": "t1", "name": "Balkon"}],
            argv=("audit", "--json"),
        )

        report = json.loads(out.out)
        assert report["by_tenant"] == [
            {"tenant_key": "t1", "tenant_name": "Balkon", "missing": 2},
            {"tenant_key": "", "tenant_name": None, "missing": 1},
        ]
        assert report["missing_total"] == 3, "the tenantless plants are counted, not dropped"


class TestSharedPredicate:
    def test_the_script_carries_no_predicate_of_its_own(self) -> None:
        """The audit, the nightly warning and the later backfill must select the same
        plants. A ``FOR plant IN`` written out here would be a second population that
        looks identical until one of the two is edited."""
        source = _SCRIPT.read_text(encoding="utf-8")

        assert "FOR plant IN" not in source
        assert "unprofiled_plants_by_tenant_aql" in source
        assert "unprofiled_plant_keys_aql" in source

    def test_the_queries_it_issues_are_the_repository_builders(self, monkeypatch, capsys) -> None:
        """Importing the builder proves nothing on its own — the issued query is what
        counts, and this asserts on the strings that actually reached the database."""
        from app.data_access.arango.care_reminder_repository import (
            unprofiled_plant_keys_aql,
            unprofiled_plants_by_tenant_aql,
        )

        _code, _out, aql = _run(monkeypatch, capsys, by_tenant=[{"tenant_key": "t1", "missing": 1}])

        assert unprofiled_plants_by_tenant_aql() in aql.queries
        assert unprofiled_plant_keys_aql() in aql.queries

    def test_the_collection_names_are_bound_and_never_interpolated(self, monkeypatch, capsys) -> None:
        _code, _out, aql = _run(monkeypatch, capsys, by_tenant=[{"tenant_key": "t1", "missing": 1}])

        bound = [bv for bv in aql.bind_vars if "@plants" in bv]
        assert bound, "the shared queries take their collections as bind parameters"
        for bind_vars in bound:
            assert bind_vars["@plants"] == col.PLANT_INSTANCES
            assert bind_vars["@profiles"] == col.CARE_PROFILES
