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
from datetime import UTC, datetime
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit_oauth_links.py"
_spec = importlib.util.spec_from_file_location("audit_oauth_links", _SCRIPT)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

#: #1399's admin gate and #1403's auto-link fix are SEVENTEEN HOURS apart, and the
#: audit reports two different numbers against them. Held apart here so a test that
#: means "after the gate" cannot accidentally also mean "after the auto-link fix".
GATE_CUTOFF = datetime(2026, 9, 11, 15, 20, 10, tzinfo=UTC)
AUTOLINK_CUTOFF = datetime(2026, 9, 12, 8, 0, 10, tzinfo=UTC)


def _row(**overrides) -> dict:
    return {
        "key": "l1",
        "provider": "google",
        "linked_at": "2026-01-01T00:00:00+00:00",
        "created_at": None,
        "user_key": "u1",
        "user_exists": True,
        "user_email_verified": True,
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
    the callback kept passing the literal `True` until 2026-09-12 08:00 UTC. The
    first version of this audit computed `at_risk` INSIDE the before-gate branch, so
    every row in those seventeen hours was dropped from the number the operator is
    asked to act on — the wrong direction for a security audit to be wrong in.
    """
    between = _row(key="l-between", linked_at="2026-09-11T20:00:00+00:00")

    _by_provider, before, at_risk, _undated = audit.classify([between], GATE_CUTOFF, AUTOLINK_CUTOFF)

    assert before == [], "it was created after the gate"
    assert [r["key"] for r in at_risk] == ["l-between"], (
        "and it is still reachable: the auto-link branch was live for another 17 hours"
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


def test_the_shipped_defaults_are_the_dates_they_claim_to_be():
    """The constants name two commits; this pins the values against drift.

    The first version dated the gate 2026-09-10, a day and a half before the commit
    it named, and nothing said so — the docstring asserted the figure was that
    commit's, so the under-count was invisible in the output.
    """
    assert audit._parse(audit.DEFAULT_GATE_CUTOFF) == GATE_CUTOFF
    assert audit._parse(audit.DEFAULT_AUTOLINK_CUTOFF) == AUTOLINK_CUTOFF
    assert audit._parse(audit.DEFAULT_GATE_CUTOFF) < audit._parse(audit.DEFAULT_AUTOLINK_CUTOFF), (
        "the auto-link branch outlived the admin gate; if these ever invert, the "
        "two-window reasoning in classify() is wrong"
    )
