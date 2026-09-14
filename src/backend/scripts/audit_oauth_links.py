#!/usr/bin/env python
"""Read-only audit of `auth_providers` rows that predate the #1399 gate (#1403).

**Reads only**, and it connects that way too: it opens the configured database
directly rather than through ``ArangoConnection``, whose ``connect()`` calls
``sys_db.create_database(...)`` when the database is absent. An audit that can
create its own empty target is an audit that can report "nothing was ever linked"
about a database it just made.

## Why this exists

Until #1399, `/admin/oidc-providers` carried no platform-admin gate, so any
authenticated member could point the installation at an identity provider. Until
#1403, the OAuth callback's auto-link branch passed a literal `True` for the
provider's `email_verified` claim, so an assertion of `email = victim@example.org`
linked to and logged in as the victim whenever the victim's local account was
email-verified — which every normally-registered account is.

Both are fixed, and both fixes are **changed-only**: they bound what happens from
now on and touch no row created earlier. A link forged during that window is
indistinguishable, at the data layer, from a legitimate one — which is exactly why
this reports rather than acts.

## Two windows, not one

The two defects closed at different times, and a row can fall in either window:

* **The admin gate** (#1399, PR #1400, merged 2026-09-11 15:20 UTC) stopped an
  ordinary member registering an identity provider. A provider planted before it
  stays configured afterwards — gating the route removed the way IN, not what was
  already there.
* **The auto-link branch** (#1403, PR #1413, merged 2026-09-12 20:19 UTC) kept
  passing ``True`` for the provider's ``email_verified`` claim for a further
  **29 hours**.

So ``before_gate`` and ``at_risk`` are computed against SEPARATE cut-offs and
neither is nested inside the other. An earlier version used one cut-off for both,
dated 2026-09-10 — a day and a half before the gate it claimed to name — which
dropped every row in a two-day window from the number the operator is asked to act
on. For a security audit that is the wrong direction to be wrong in.

`at_risk` is still not "compromised". It counts links the defective path *could*
have created: the local account is email-verified, so auto-link would have fired,
and the row predates the fix. In a single-operator installation the answer is
usually "one, your own", and that ends the question.

Usage::

    python scripts/audit_oauth_links.py
        [--gate-cutoff 2026-09-11T15:20:10Z] [--autolink-cutoff 2026-09-12T08:00:10Z]
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import UTC, datetime

from arango.exceptions import ArangoError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: WHEN THE FIX REACHED `develop`, not when it was written. Both defaults are the
#: MERGE time of the pull request that shipped the fix, because that is when the
#: defect stopped being reachable by anyone. An earlier version of this file dated
#: the auto-link boundary from `be551a3e6`, a commit on the unmerged feature branch
#: — twelve hours before the squash actually landed, so every row in between was
#: dropped from the count. Same error, same direction, as the one the commit before
#: it fixed.
#:
#: Each value is the named commit's COMMITTER date, which is what a clone can check
#: offline; GitHub's `mergedAt` for the same pull request is one second later, a
#: difference with no bearing on any row. `test_the_cutoffs_match_the_commits_they_name`
#: resolves both against git rather than against a literal copied from here.
#:
#: PR #1400, merge commit `5e9c8662b` — gated `/admin/oidc-providers` (#1399).
GATE_COMMIT = "5e9c8662b"
DEFAULT_GATE_CUTOFF = "2026-09-11T15:20:10+00:00"

#: PR #1413, merge commit `ce0ec3288` — replaced the literal `True` with the
#: provider's `email_verified` claim (#1403). Roughly 29 hours after the gate.
AUTOLINK_COMMIT = "ce0ec3288"
DEFAULT_AUTOLINK_CUTOFF = "2026-09-12T20:19:06+00:00"


def _parse(value: str | None) -> datetime | None:
    """Parse an ISO timestamp, reading a missing offset as UTC.

    The offset is not optional to the caller even though it looks it: every value
    compared here is UTC, and a naive datetime raises
    ``TypeError: can't compare offset-naive and offset-aware datetimes`` against an
    aware one. `--cutoff 2026-09-10` — a date, which the help text's "ISO timestamp"
    invites — therefore crashed the audit on its first dated row, while the default
    carried `+00:00` and hid it. The same applies in reverse to a stored timestamp
    written without an offset by an older schema version.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def stamp_of(row: dict) -> datetime | None:
    """The row's effective timestamp: ``linked_at``, else ``created_at``."""
    return _parse(row.get("linked_at")) or _parse(row.get("created_at"))


def classify(
    rows: list[dict], gate_cutoff: datetime, autolink_cutoff: datetime
) -> tuple[Counter[str], list[dict], list[dict], int]:
    """Split the links into ``(by_provider, before_gate, at_risk, undated)``.

    Extracted from ``main`` so the decisions it encodes are testable without a
    database — they are decisions, not plumbing:

    **The two lists use different cut-offs and are computed independently.** Gating
    `/admin/oidc-providers` removed the way to register a rogue provider; it did not
    unconfigure one already registered, and the auto-link branch kept firing for a
    further 29 hours. A row can therefore be after the gate and still
    reachable by the defective path. Nesting `at_risk` inside `before_gate` — which
    an earlier version did — silently drops exactly those rows.

    **An undated row counts as inside BOTH windows.** Absence of a timestamp is not
    evidence of being recent, and for a question about a security window the
    pessimistic reading is the right one. A row written by an older schema version
    is exactly the kind that predates both fixes.

    **``at_risk`` requires ``user_email_verified is True``, not truthiness.** The
    defective auto-link branch fired on the victim's account being verified; a
    ``None`` (field absent, user gone) is not that, and counting it would inflate
    the number the operator has to act on.
    """
    by_provider: Counter[str] = Counter()
    before_gate: list[dict] = []
    at_risk: list[dict] = []
    undated = 0

    for row in rows:
        by_provider[row.get("provider") or "?"] += 1
        stamp = stamp_of(row)

        if stamp is None:
            undated += 1

        if stamp is None or stamp < gate_cutoff:
            before_gate.append(row)

        if (stamp is None or stamp < autolink_cutoff) and row.get("user_email_verified") is True:
            at_risk.append(row)

    return by_provider, before_gate, at_risk, undated


KEY_LISTING_LIMIT = 50


def _unreachable(settings, exc: Exception) -> str:
    return (
        f"cannot read database {settings.arangodb_database!r} at "
        f"{settings.arangodb_host}:{settings.arangodb_port}: {exc}\n"
        f"Check ARANGODB_DATABASE / host / port / credentials. This script does not "
        f"create anything."
    )


def build_queries(auth_providers: str, users: str) -> tuple[str, str]:
    """The two AQL queries, at module level so a unit test can read the FILTER.

    ``FILTER LOWER(link.provider) != "local"`` is NOT cosmetic, and dropping it is
    not a small regression. ``auth_providers`` is not a table of federated links:
    ``AuthService`` writes a ``provider=LOCAL`` row for EVERY locally registered
    account (``auth_service.py:283``, and again at ``:690`` when a local password is
    first set), each with its own ``linked_at``. Counting those made ``at_risk``
    approximately "every email-verified user" — an alarming number the defective
    auto-link branch could never have produced. On a single-operator installation
    the "one, your own" that reads like a correct answer IS that local row rather
    than a federated link, which is exactly what hid this.

    A string assertion is the right level here: the filter runs in ArangoDB, and a
    unit test has no database. What it can do is notice the clause leaving.
    """
    federated = f"""
    FOR link IN {auth_providers}
      FILTER LOWER(link.provider) != "local"
      LET user = FIRST(FOR u IN {users} FILTER u._key == link.user_key RETURN u)
      RETURN {{
        key: link._key,
        provider: link.provider,
        linked_at: link.linked_at,
        created_at: link.created_at,
        user_key: link.user_key,
        user_exists: user != null,
        user_email_verified: user.email_verified
      }}
    """
    local_count = f"""
    FOR link IN {auth_providers}
      FILTER LOWER(link.provider) == "local"
      COLLECT WITH COUNT INTO n
      RETURN n
    """
    return federated, local_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate-cutoff",
        default=DEFAULT_GATE_CUTOFF,
        help="ISO timestamp of #1399's admin gate (assumed UTC if no offset)",
    )
    parser.add_argument(
        "--autolink-cutoff",
        default=DEFAULT_AUTOLINK_CUTOFF,
        help="ISO timestamp of #1403's auto-link fix (assumed UTC if no offset)",
    )
    args = parser.parse_args()

    gate_cutoff = _parse(args.gate_cutoff)
    autolink_cutoff = _parse(args.autolink_cutoff)
    for name, value, parsed in (
        ("--gate-cutoff", args.gate_cutoff, gate_cutoff),
        ("--autolink-cutoff", args.autolink_cutoff, autolink_cutoff),
    ):
        if parsed is None:
            print(f"unparseable {name}: {value!r}", file=sys.stderr)
            return 2

    if autolink_cutoff < gate_cutoff:
        # The two-window reasoning in classify() assumes the gate came first, which
        # it did. Swapped flags would relabel both counts and nothing in the output
        # would say so.
        print(
            f"--autolink-cutoff ({autolink_cutoff.isoformat()}) is before "
            f"--gate-cutoff ({gate_cutoff.isoformat()}). The admin gate shipped "
            f"first; if you meant to swap them, the labels in the report would be "
            f"wrong.",
            file=sys.stderr,
        )
        return 2

    from arango import ArangoClient

    from app.config.settings import settings
    from app.data_access.arango import collections as col

    # NOT `ArangoConnection`: its `connect()` creates the database when absent, so
    # a mistyped ARANGODB_DATABASE would leave this script reporting "nothing was
    # ever linked" about an empty database it had just created. A read-only audit
    # opens what is there and says so when it is not.
    client = ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")
    db = client.db(
        settings.arangodb_database,
        username=settings.arangodb_username,
        password=settings.arangodb_password,
    )

    try:
        has_links = db.has_collection(col.AUTH_PROVIDERS)
    except (ArangoError, OSError) as exc:
        # OSError as well as ArangoError: when every configured host fails,
        # python-arango raises the BUILT-IN `ConnectionAbortedError`, an OSError
        # subclass that is not an ArangoError. A mistyped ARANGODB_HOST or _PORT —
        # the failure this message exists for — produced a raw traceback instead.
        print(_unreachable(settings, exc), file=sys.stderr)
        return 1

    if not has_links:
        # `AUTH_PROVIDERS` is in DOCUMENT_COLLECTIONS and is created unconditionally
        # at bootstrap, so its absence cannot mean "nothing has ever been linked" —
        # it means this database was never initialised, i.e. the wrong target.
        print(
            f"{col.AUTH_PROVIDERS} does not exist in {settings.arangodb_database!r}. "
            f"That collection is created at bootstrap, so this is an uninitialised "
            f"database rather than an empty one — check ARANGODB_DATABASE.",
            file=sys.stderr,
        )
        return 1

    query, local_query = build_queries(col.AUTH_PROVIDERS, col.USERS)

    try:
        rows = list(db.aql.execute(query))
        local_rows = next(iter(db.aql.execute(local_query)), 0)
    except (ArangoError, OSError) as exc:
        print(_unreachable(settings, exc), file=sys.stderr)
        return 1

    if not rows:
        print(
            f"no federated links: {col.AUTH_PROVIDERS} holds {local_rows} local "
            f"password row(s) and nothing else. Nothing has ever been linked to an "
            f"external identity provider, so neither window has anything in it."
        )
        return 0

    by_provider, before_gate, at_risk, undated = classify(rows, gate_cutoff, autolink_cutoff)
    orphaned = [row for row in rows if not row.get("user_exists")]

    print(f"federated links:                 {len(rows)}  ({local_rows} local password row(s) excluded)")
    print(f"  by provider:                   {dict(by_provider)}")
    print(f"  without a timestamp:           {undated}  (counted as inside BOTH windows)")
    print(f"  pointing at a deleted user:    {len(orphaned)}")
    print(f"created before the #1399 gate:   {len(before_gate)}  (< {gate_cutoff.isoformat()})")
    print(f"reachable by the auto-link path: {len(at_risk)}  (< {autolink_cutoff.isoformat()}, account email-verified)")
    print()
    print("The two windows are separate on purpose: gating /admin/oidc-providers removed")
    print("the way to REGISTER a rogue provider, not one already registered, and the")
    print("auto-link branch kept firing for a further 29 hours. A row can be after")
    print("the gate and still reachable.")
    print()
    print("'reachable' is NOT evidence that any of these was forged — the data layer")
    print("cannot tell a forged link from a legitimate one, which is the reason this")
    print("script reports instead of acting (#1403).")

    if at_risk:
        print()
        print("keys (for a manual look, newest first):")
        ordered = sorted(
            at_risk,
            key=lambda r: (stamp_of(r) is not None, stamp_of(r) or _parse(DEFAULT_GATE_CUTOFF)),
            reverse=True,
        )
        for row in ordered[:KEY_LISTING_LIMIT]:
            when = stamp_of(row)
            print(
                f"  {row['key']}  user={row['user_key']}  provider={row.get('provider')}  "
                f"{when.isoformat() if when else 'no timestamp'}"
            )
        withheld = len(ordered) - KEY_LISTING_LIMIT
        if withheld > 0:
            print(f"  … and {withheld} more not shown (listing caps at {KEY_LISTING_LIMIT}).")
            print("  A manual review that stops here is incomplete — query the collection")
            print("  directly for the full set.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
