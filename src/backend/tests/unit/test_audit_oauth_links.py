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

CUTOFF = datetime(2026, 9, 10, tzinfo=UTC)


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
    _by_provider, before, at_risk, undated = audit.classify([_row(linked_at=None, created_at=None)], CUTOFF)

    assert undated == 1
    assert len(before) == 1
    assert len(at_risk) == 1


def test_a_row_after_the_cutoff_is_not_counted():
    """The control. Without it, "count everything" would satisfy the case above."""
    _by_provider, before, at_risk, undated = audit.classify([_row(linked_at="2026-09-11T00:00:00+00:00")], CUTOFF)

    assert (undated, before, at_risk) == (0, [], [])


def test_created_at_is_used_when_linked_at_is_absent():
    """Older rows carry only `created_at`; ignoring it would call them undated."""
    _by_provider, before, at_risk, undated = audit.classify(
        [_row(linked_at=None, created_at="2026-09-11T00:00:00+00:00")], CUTOFF
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

    _by_provider, before, at_risk, _undated = audit.classify(rows, CUTOFF)

    assert len(before) == 3, "all three predate the cutoff"
    assert [row["key"] for row in at_risk] == ["verified"]


def test_providers_are_counted_even_for_rows_after_the_cutoff():
    """The inventory is the whole table; only the *risk* window is filtered.

    An operator reading "3 links, 1 before the gate" learns something the filtered
    count alone does not say.
    """
    rows = [
        _row(provider="google", linked_at="2026-01-01T00:00:00+00:00"),
        _row(provider="github", linked_at="2026-09-11T00:00:00+00:00"),
        _row(provider="github", linked_at="2026-09-12T00:00:00+00:00"),
    ]

    by_provider, before, _at_risk, _undated = audit.classify(rows, CUTOFF)

    assert by_provider == {"google": 1, "github": 2}
    assert len(before) == 1


def test_an_unparseable_timestamp_does_not_crash_the_audit():
    """A malformed stamp is treated as absent, not as a reason to abort.

    The audit's job is to produce a number for an operator; dying on one bad row
    would leave them with nothing.
    """
    _by_provider, before, _at_risk, undated = audit.classify([_row(linked_at="not-a-date", created_at=None)], CUTOFF)

    assert undated == 1 and len(before) == 1
