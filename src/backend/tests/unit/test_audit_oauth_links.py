"""#1403 — the two judgement calls in the pre-gate OAuth link audit.

`scripts/audit_oauth_links.py` answers "how many `auth_providers` rows predate the
#1399 gate, and how many of those could the defective auto-link path have created?"
It reads only. What it *decides* is how to classify two awkward cases, and those are
what this file pins — the counting itself is arithmetic.

The audit exists because both fixes are changed-only: #1399 gated
`/admin/oidc-providers`, #1403 stopped the callback passing a literal `True` for the
provider's `email_verified` claim, and neither touches a row created earlier. A link
forged in that window is indistinguishable at the data layer from a legitimate one,
which is why the script reports and does not act.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit_oauth_links.py"
_spec = importlib.util.spec_from_file_location("audit_oauth_links", _SCRIPT)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

#: #1399's admin gate and #1403's auto-link fix are 29 HOURS apart, and the
#: audit reports two different numbers against them. Held apart here so a test that
#: means "after the gate" cannot accidentally also mean "after the auto-link fix".
GATE_CUTOFF = datetime(2026, 9, 11, 15, 20, 10, tzinfo=UTC)
AUTOLINK_CUTOFF = datetime(2026, 9, 12, 20, 19, 6, tzinfo=UTC)


def _row(**overrides) -> dict:
    return {
        "key": "l1",
        "provider": "google",
        "linked_at": "2026-01-01T00:00:00+00:00",
        "created_at": None,
        "user_key": "u1",
        "user_exists": True,
        "user_email_verified": True,
        "user_created_at": None,
        **overrides,
    }


def test_a_row_with_no_timestamp_counts_as_before_the_gate():
    """The pessimistic reading, and it is a decision rather than a fallback.

    Absence of a timestamp is not evidence of being recent — a row written by an
    older schema version is exactly the kind that predates the gate. Counting it as
    *after* would shrink the number the operator has to look at by hiding the rows
    least likely to be recent.
    """
    _by_provider, before, at_risk, undated = audit.classify(
        [_row(linked_at=None, created_at=None)], GATE_CUTOFF, AUTOLINK_CUTOFF
    )

    assert undated == 1
    assert len(before) == 1
    assert len(at_risk) == 1


def test_a_row_after_the_cutoff_is_not_counted():
    """The control. Without it, "count everything" would satisfy the case above."""
    _by_provider, before, at_risk, undated = audit.classify(
        [_row(linked_at="2026-09-20T00:00:00+00:00")], GATE_CUTOFF, AUTOLINK_CUTOFF
    )

    assert (undated, before, at_risk) == (0, [], [])


def test_created_at_is_used_when_linked_at_is_absent():
    """Older rows carry only `created_at`; ignoring it would call them undated."""
    _by_provider, before, at_risk, undated = audit.classify(
        [_row(linked_at=None, created_at="2026-09-20T00:00:00+00:00")], GATE_CUTOFF, AUTOLINK_CUTOFF
    )

    assert undated == 0, "a row with a usable created_at is not undated"
    assert before == [] and at_risk == []


def test_at_risk_needs_a_verified_account_not_a_truthy_one():
    """`is True`, not truthiness.

    The defective branch fired on the victim's local account being email-verified.
    A `None` — field absent, or the user row gone — is not that, and counting it
    would inflate the number the operator has to act on with rows the path could
    never have reached.
    """
    rows = [
        _row(key="verified", user_email_verified=True),
        _row(key="unverified", user_email_verified=False),
        _row(key="unknown", user_email_verified=None),
    ]

    _by_provider, before, at_risk, _undated = audit.classify(rows, GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert len(before) == 3, "all three predate the cutoff"
    assert [row["key"] for row in at_risk] == ["verified"]


def test_providers_are_counted_even_for_rows_after_the_cutoff():
    """The inventory is the whole table; only the *risk* window is filtered.

    An operator reading "3 links, 1 before the gate" learns something the filtered
    count alone does not say.
    """
    rows = [
        _row(provider="google", linked_at="2026-01-01T00:00:00+00:00"),
        _row(provider="github", linked_at="2026-09-20T00:00:00+00:00"),
        _row(provider="github", linked_at="2026-09-21T00:00:00+00:00"),
    ]

    by_provider, before, _at_risk, _undated = audit.classify(rows, GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert by_provider == {"google": 1, "github": 2}
    assert len(before) == 1


def test_an_unparseable_timestamp_does_not_crash_the_audit():
    """A malformed stamp is treated as absent, not as a reason to abort.

    The audit's job is to produce a number for an operator; dying on one bad row
    would leave them with nothing.
    """
    _by_provider, before, _at_risk, undated = audit.classify(
        [_row(linked_at="not-a-date", created_at=None)], GATE_CUTOFF, AUTOLINK_CUTOFF
    )

    assert undated == 1 and len(before) == 1


def test_the_two_windows_are_independent_not_nested():
    """A row created AFTER the gate can still be reachable by the auto-link path.

    Gating `/admin/oidc-providers` (#1399, 2026-09-11 15:20 UTC) removed the way to
    REGISTER a rogue provider; it did not unconfigure one already registered, and
    the callback kept passing the literal `True` until 2026-09-12 20:19 UTC. The
    first version of this audit computed `at_risk` INSIDE the before-gate branch, so
    every row in those 29 hours was dropped from the number the operator is
    asked to act on — the wrong direction for a security audit to be wrong in.
    """
    between = _row(key="l-between", linked_at="2026-09-11T20:00:00+00:00")

    _by_provider, before, at_risk, _undated = audit.classify([between], GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert before == [], "it was created after the gate"
    assert [r["key"] for r in at_risk] == ["l-between"], (
        "and it is still reachable: the auto-link branch was live for another 29 hours"
    )


def test_a_row_after_both_cutoffs_is_in_neither_list():
    after = _row(linked_at="2026-09-20T00:00:00+00:00")

    _by_provider, before, at_risk, _undated = audit.classify([after], GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert before == []
    assert at_risk == []


def test_an_undated_row_is_inside_both_windows():
    """Pessimistic on both counts, for the same reason it is pessimistic on one."""
    _by_provider, before, at_risk, undated = audit.classify(
        [_row(linked_at=None, created_at=None)], GATE_CUTOFF, AUTOLINK_CUTOFF
    )

    assert len(before) == 1
    assert len(at_risk) == 1
    assert undated == 1


def test_a_cutoff_without_an_offset_is_read_as_utc():
    """`--gate-cutoff 2026-09-11` is what an operator types, and it used to crash.

    `datetime.fromisoformat` returns a NAIVE datetime for a date or an offset-less
    timestamp, and comparing that to the aware timestamps in the rows raises
    `TypeError: can't compare offset-naive and offset-aware datetimes`. The defaults
    carry `+00:00`, so the only way to meet this was to pass the flag — which the
    help text ("ISO timestamp") invites.

    Every value this script compares is UTC, so reading a missing offset as UTC is
    the meaning, not a guess.
    """
    for spelling in ("2026-09-11", "2026-09-11T00:00:00", "2026-09-11T00:00:00Z"):
        parsed = audit._parse(spelling)

        assert parsed is not None, spelling
        assert parsed.tzinfo is not None, f"{spelling} parsed naive and would crash the compare"
        assert parsed == datetime(2026, 9, 11, tzinfo=UTC), spelling


def test_a_stored_timestamp_without_an_offset_does_not_crash_the_compare():
    """The same hazard from the other side: the row, not the flag.

    A row written by a schema version that stored `linked_at` without an offset
    would have produced a naive stamp against an aware cut-off — the identical
    TypeError, and one nobody could work around by changing how they invoke the
    script.
    """
    rows = [_row(linked_at="2026-01-01T00:00:00")]

    _by_provider, before, at_risk, undated = audit.classify(rows, GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert len(before) == 1
    assert len(at_risk) == 1
    assert undated == 0, "it has a timestamp — it is dated, just written without an offset"


def test_an_unparseable_cutoff_is_refused_rather_than_guessed():
    """`_parse` returning None is what `main` turns into exit 2.

    Pinned next to the tests above because the repair widens what parses, and the
    line between "read it as UTC" and "refuse it" is the thing that could drift.
    """
    assert audit._parse("last tuesday") is None
    assert audit._parse("") is None
    assert audit._parse(None) is None


def test_the_cutoffs_match_the_commits_they_name():
    """Resolved against git, because the version this replaces was circular.

    It asserted `_parse(DEFAULT_GATE_CUTOFF) == GATE_CUTOFF`, i.e. the constant
    against a literal copied from the constant. Both constants were wrong when it
    was green: the gate was dated a day and a half early, and the auto-link boundary
    came from `be551a3e6` — a commit on the unmerged feature branch, twelve hours
    before the squash reached `develop`. A test that reads the same number twice
    cannot see either.

    What matters about these dates is when the fix became reachable by everyone, so
    the check is: the named commit exists, it is an ancestor of `develop`, and its
    committer date is the constant. A shallow CI checkout cannot answer that, hence
    the skip — the value is at authoring time, which is when the mistake was made.
    """
    import subprocess

    repo = Path(__file__).resolve()
    for _ in range(8):
        repo = repo.parent
        if (repo / ".git").exists():
            break
    else:  # pragma: no cover - only outside a checkout
        pytest.skip("not inside a git checkout")

    def _git(*args: str) -> str | None:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    for commit, cutoff, what in (
        (audit.GATE_COMMIT, audit.DEFAULT_GATE_CUTOFF, "the #1399 admin gate"),
        (audit.AUTOLINK_COMMIT, audit.DEFAULT_AUTOLINK_CUTOFF, "the #1403 auto-link fix"),
    ):
        committed = _git("show", "-s", "--format=%cI", commit)
        if committed is None:  # pragma: no cover - shallow clone
            pytest.skip(f"{commit} is not in this checkout (shallow clone?)")

        on_develop = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, "origin/develop"],
            capture_output=True,
            check=False,
        )
        if on_develop.returncode not in (0, 1):  # pragma: no cover - no origin/develop
            pytest.skip("origin/develop is not available in this checkout")

        assert on_develop.returncode == 0, (
            f"{commit} ({what}) is not an ancestor of origin/develop. A fix that never "
            f"landed cannot be the moment the defect stopped being reachable — this is "
            f"exactly how the auto-link cut-off ended up twelve hours early."
        )
        assert datetime.fromisoformat(committed) == datetime.fromisoformat(cutoff), (
            f"{what}: {commit} was committed {committed}, the constant says {cutoff}"
        )


def test_the_gate_precedes_the_autolink_fix():
    """The ordering `classify()`'s two-window reasoning depends on."""
    assert audit._parse(audit.DEFAULT_GATE_CUTOFF) < audit._parse(audit.DEFAULT_AUTOLINK_CUTOFF), (
        "the auto-link branch outlived the admin gate; if these ever invert, the "
        "two-window reasoning in classify() is wrong"
    )


def test_the_federated_query_excludes_local_password_rows():
    """The Critical one, and it is invisible without knowing what the table holds.

    `auth_providers` is not a federated-links table: `AuthService` writes a
    `provider=LOCAL` row for every locally registered account, with its own
    `linked_at`. Without the filter, `at_risk` counted approximately every
    email-verified user — a number the defective auto-link branch could never have
    produced, presented to the operator as links to review.

    A string assertion because the filter runs in ArangoDB and a unit test has no
    database. It cannot prove the query is right; it can notice the clause leaving,
    which is the regression that matters.
    """
    federated, local_count = audit.build_queries("auth_providers", "users")

    assert 'FILTER LOWER(link.provider) != "local"' in federated, "the federated query must exclude local password rows"
    assert 'FILTER LOWER(link.provider) == "local"' in local_count
    assert "COLLECT WITH COUNT INTO n" in local_count


def test_the_two_queries_disagree_about_local_and_agree_about_the_collection():
    """The control: one filter is the negation of the other, over the same table.

    Written because the pair is easy to get half-right — filtering the federated
    query while counting everything in the other would report a local total larger
    than the table.
    """
    federated, local_count = audit.build_queries("ap_col", "users_col")

    assert "FOR link IN ap_col" in federated
    assert "FOR link IN ap_col" in local_count
    assert "FOR u IN users_col" in federated
    assert federated.count("FILTER LOWER(link.provider)") == 1
    assert local_count.count("FILTER LOWER(link.provider)") == 1


class TestUnreachableDatabase:
    """A mistyped host or database must produce a sentence, not a traceback.

    This is the failure an operator actually hits — the script is run by hand,
    against production, by someone who exported the wrong variable — so the
    behaviour is pinned rather than the source text. An earlier check of mine read
    the source for the word `OSError` and reported success against a file it had
    just mutated; reading behaviour cannot go wrong that way.
    """

    @staticmethod
    def _run(monkeypatch, raising: Exception):
        class _Client:
            def __init__(self, *args, **kwargs):
                pass

            def db(self, *args, **kwargs):
                return _Db()

        class _Db:
            def has_collection(self, _name):
                raise raising

        import arango

        monkeypatch.setattr(arango, "ArangoClient", _Client)
        monkeypatch.setattr(sys, "argv", ["audit_oauth_links.py"])
        return audit.main()

    def test_a_refused_connection_is_reported_not_raised(self, monkeypatch, capsys):
        """python-arango raises the BUILT-IN `ConnectionAbortedError` when every host
        fails — an `OSError`, not an `ArangoError`. Catching only `ArangoError` left
        a mistyped `ARANGODB_HOST` printing a traceback, which is the one case the
        message exists for.
        """
        code = self._run(monkeypatch, ConnectionAbortedError("cannot connect to any host"))

        assert code == 1
        err = capsys.readouterr().err
        assert "does not create anything" in err
        assert "ARANGODB_DATABASE / host / port / credentials" in err

    def test_an_arango_error_is_reported_the_same_way(self, monkeypatch, capsys):
        """Bad credentials come through as an `ArangoError`; same message, same exit."""
        from arango.exceptions import ArangoError

        code = self._run(monkeypatch, ArangoError("not authorized"))

        assert code == 1
        assert "does not create anything" in capsys.readouterr().err


class TestProviderRegistrations:
    """The #1399 window is about REGISTRATIONS, and they live in another collection.

    Auditing only `auth_providers` answers "who signed in through a provider" and
    misses the worse case: a provider registered before the gate that nobody has
    used yet reports zero links, reads as an all-clear, and is still enabled — so
    every link it mints from here on is after both cut-offs and appears in neither
    window. The module docstring made that argument before the query existed.
    """

    @staticmethod
    def _cfg(**overrides) -> dict:
        return {
            "key": "c1",
            "slug": "rogue",
            "display_name": "Rogue",
            "issuer_url": "https://evil.example/",
            "enabled": True,
            "created_at": "2026-09-09T00:00:00+00:00",
            **overrides,
        }

    def test_a_provider_registered_before_the_gate_is_reported(self):
        before, still_enabled, undated = audit.classify_providers([self._cfg()], GATE_CUTOFF)

        assert [c["slug"] for c in before] == ["rogue"]
        assert [c["slug"] for c in still_enabled] == ["rogue"]
        assert undated == 0

    def test_a_disabled_one_is_counted_but_not_flagged(self):
        """A disabled provider mints nothing; an enabled one keeps going."""
        before, still_enabled, _undated = audit.classify_providers([self._cfg(enabled=False)], GATE_CUTOFF)

        assert len(before) == 1
        assert still_enabled == []

    def test_a_provider_registered_after_the_gate_is_not_counted(self):
        """The control: without it, "report everything" satisfies the case above."""
        before, still_enabled, _undated = audit.classify_providers(
            [self._cfg(created_at="2026-09-20T00:00:00+00:00")], GATE_CUTOFF
        )

        assert before == []
        assert still_enabled == []

    def test_an_undated_registration_counts_as_before_the_gate(self):
        before, still_enabled, undated = audit.classify_providers([self._cfg(created_at=None)], GATE_CUTOFF)

        assert len(before) == 1
        assert len(still_enabled) == 1
        assert undated == 1

    def test_the_provider_query_reads_the_configs_collection(self):
        query = audit.provider_configs_aql("oidc_provider_configs")

        assert "FOR cfg IN oidc_provider_configs" in query
        for field in ("slug", "issuer_url", "enabled", "created_at"):
            assert field in query, f"the operator needs {field} to act on a row"


def test_a_non_string_timestamp_is_treated_as_absent_not_as_a_crash():
    """An epoch int from an older schema version used to abort the whole audit.

    `value.replace("Z", …)` raises `AttributeError` on an int, which nothing caught
    — in a script whose stated premise is reading defensively across schema
    versions. `test_an_unparseable_timestamp_does_not_crash_the_audit` claimed this
    invariant and only covered the `str` spelling of it.
    """
    rows = [_row(linked_at=1757604010, created_at=None)]

    _by_provider, before, at_risk, undated = audit.classify(rows, GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert undated == 1, "unreadable is absent, and absent is pessimistic"
    assert len(before) == 1
    assert len(at_risk) == 1


class TestPartiallyInitialisedDatabase:
    """A collection that is absent must stop the run, not report zero.

    `auth_providers` already did. `oidc_provider_configs` did not: it fell back to
    an empty list, so the report printed "identity providers registered: 0 … STILL
    ENABLED: 0" — a clean bill of health, about the half this script calls the worse
    case, over a collection it never read. The same reasoning twenty lines apart,
    applied to one sibling and not the other.
    """

    @staticmethod
    def _run(monkeypatch, present: set[str]):
        class _Client:
            def __init__(self, *args, **kwargs):
                pass

            def db(self, *args, **kwargs):
                return _Db()

        class _Db:
            def has_collection(self, name):
                return name in present

            @property
            def aql(self):
                return _Aql()

        class _Aql:
            def execute(self, _query):
                return iter(())

        import arango

        monkeypatch.setattr(arango, "ArangoClient", _Client)
        monkeypatch.setattr(sys, "argv", ["audit_oauth_links.py"])
        return audit.main()

    def test_a_missing_provider_config_collection_stops_the_run(self, monkeypatch, capsys):
        code = self._run(monkeypatch, present={"auth_providers"})

        assert code == 1
        err = capsys.readouterr().err
        assert "oidc_provider_configs does not exist" in err
        assert "Refusing to report zero providers" in err

    def test_a_missing_auth_providers_collection_stops_the_run(self, monkeypatch, capsys):
        """The control: the sibling branch this one was modelled on still behaves."""
        code = self._run(monkeypatch, present={"oidc_provider_configs"})

        assert code == 1
        assert "auth_providers does not exist" in capsys.readouterr().err


def test_the_default_run_says_the_cutoff_is_a_floor(monkeypatch, capsys):
    """Merged to `develop` is not deployed, and the operator has to be told.

    This repository ships by dispatching `docker-publish` and restarting the
    rollout, so a cluster runs the defective image until then. Links forged in that
    gap sit after both cut-offs and appear in neither window — the same undercount
    the file warns about twice, one layer further out. The script cannot know the
    deploy time, so it names the assumption on every default run instead of
    presenting the number as the answer.
    """

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def db(self, *args, **kwargs):
            return _Db()

    class _Db:
        def has_collection(self, _name):
            return True

        @property
        def aql(self):
            return _Aql()

    class _Aql:
        def execute(self, query):
            if "user_email_verified" in query:
                return iter(
                    [
                        {
                            "key": "l1",
                            "provider": "github",
                            "linked_at": "2026-01-01T00:00:00+00:00",
                            "created_at": None,
                            "user_key": "u1",
                            "user_exists": True,
                            "user_email_verified": True,
                        }
                    ]
                )
            return iter(())

    import arango

    monkeypatch.setattr(arango, "ArangoClient", _Client)
    monkeypatch.setattr(sys, "argv", ["audit_oauth_links.py"])

    assert audit.main() == 0
    out = capsys.readouterr().out
    assert "--gate-cutoff and --autolink-cutoff still hold the develop-merge time" in out, (
        "BOTH defaults are floors. The first version of this note covered the "
        "auto-link one only, leaving the gate window — which the script calls the "
        "worse case — to read as an answer rather than a lower bound."
    )
    assert "with your own deploy timestamp" in out


class TestRegistrationsAreNotAutoLinks:
    """`at_risk` must not count accounts the defective branch could never reach.

    `_register_oauth_user` sets `email_verified` from the provider's own claim
    (`auth_service.py:908`), so a user who has only ever signed in with Google has a
    verified account and a federated link. Auto-link needs a pre-existing LOCAL
    account to attach to, so it never ran for them — yet they were counted, and on
    an OAuth-first installation that made `at_risk` approach "every federated link".
    The same alarming-and-wrong number the `local` filter removed, one population
    over.
    """

    def test_a_link_made_with_the_account_is_a_registration(self):
        row = _row(
            linked_at="2026-01-01T10:00:00+00:00",
            user_created_at="2026-01-01T10:00:02+00:00",
        )

        _by_provider, before, at_risk, _undated = audit.classify([row], GATE_CUTOFF, AUTOLINK_CUTOFF)

        assert len(before) == 1, "it is still a link that predates the gate"
        assert at_risk == [], "but auto-link cannot have produced it"

    def test_a_link_made_long_after_the_account_stays_counted(self):
        """The control. Without it, excluding everything would satisfy the case above."""
        row = _row(
            linked_at="2026-06-01T10:00:00+00:00",
            user_created_at="2026-01-01T10:00:00+00:00",
        )

        _by_provider, _before, at_risk, _undated = audit.classify([row], GATE_CUTOFF, AUTOLINK_CUTOFF)

        assert len(at_risk) == 1

    def test_a_missing_user_creation_time_keeps_the_row(self):
        """Unknown keeps the row, like every other unknown here.

        Excluding a row that should have been counted is the dangerous error in a
        security audit; including one that need not be is noise. The heuristic is
        therefore allowed to fire only when both timestamps are present.
        """
        row = _row(linked_at="2026-01-01T10:00:00+00:00", user_created_at=None)

        _by_provider, _before, at_risk, _undated = audit.classify([row], GATE_CUTOFF, AUTOLINK_CUTOFF)

        assert len(at_risk) == 1

    def test_the_window_boundary_is_inclusive(self):
        row = _row(
            linked_at="2026-01-01T10:00:00+00:00",
            user_created_at="2026-01-01T10:01:00+00:00",
        )

        assert audit.was_created_through_the_provider(row) is True, (
            f"exactly {audit.REGISTRATION_WINDOW_SECONDS}s apart is still one flow"
        )

    def test_one_second_past_the_window_is_not_a_registration(self):
        row = _row(
            linked_at="2026-01-01T10:00:00+00:00",
            user_created_at="2026-01-01T10:01:01+00:00",
        )

        assert audit.was_created_through_the_provider(row) is False
