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

    python scripts/audit_oauth_links.py                        # develop-merge floor
    python scripts/audit_oauth_links.py --autolink-cutoff 2026-09-13T06:30:00Z

The second form is the one to use on a deployed installation: the defaults are when
each fix reached `develop`, and a cluster runs the defective image until the next
rollout. Pass the time YOUR deployment picked the fix up.

The defaults are derived from the merge commits and are not repeated here with a
second set of digits: the previous version of this example still showed the
superseded `--autolink-cutoff 2026-09-12T08:00:10Z`, twelve hours early, so an
operator who copy-pasted the documented invocation reproduced the very undercount
two commits had just been spent removing.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import UTC, datetime

from arango.exceptions import ArangoError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: WHEN THE FIX REACHED `develop` — which is NOT when it reached your installation.
#: This repository deploys by dispatching `docker-publish` and restarting the
#: rollout, so a cluster keeps running the defective image until that happens. Rows
#: forged in the gap have `linked_at >= DEFAULT_AUTOLINK_CUTOFF` and fall outside
#: both windows: the same undercount this file spends two paragraphs warning about,
#: one layer further out. The defaults are therefore a FLOOR, not the answer — pass
#: your own deploy timestamp with `--autolink-cutoff` and the report says so on
#: every run. The script cannot know your deploy time, so it asks rather than
#: guessing at one.
#:
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
    if not value or not isinstance(value, str):
        # `isinstance` and not just truthiness: a row whose `linked_at` was written
        # as an epoch int by an older schema version raised
        # `AttributeError: 'int' object has no attribute 'replace'` and aborted the
        # whole audit — in a script whose premise is reading defensively across
        # schema versions. A value this cannot read is treated as absent, which
        # `classify` already handles pessimistically.
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


def provider_configs_aql(oidc_provider_configs: str) -> str:
    """The registrations themselves, which are what #1399 actually let anyone create.

    The gate defect was that any authenticated member could REGISTER an identity
    provider; the artifact of that is a row in ``oidc_provider_configs``, not a link
    in ``auth_providers``. Auditing only the links answers a narrower question and
    misses the worse case entirely: a provider registered before the gate that
    nobody has signed in through yet reports zero links, reads as an all-clear, and
    is **still enabled** — so every link it mints from now on is after both cut-offs
    and lands in neither window.

    This module's own docstring made that argument — "gating the route removed the
    way IN, not what was already there" — and then did not run the query.
    """
    return f"""
    FOR cfg IN {oidc_provider_configs}
      RETURN {{
        key: cfg._key,
        slug: cfg.slug,
        display_name: cfg.display_name,
        issuer_url: cfg.issuer_url,
        enabled: cfg.enabled,
        created_at: cfg.created_at
      }}
    """


def classify_providers(rows: list[dict], gate_cutoff: datetime) -> tuple[list[dict], list[dict], int]:
    """``(registered_before_gate, of_those_still_enabled, undated)``.

    Same pessimism as ``classify``: a registration with no ``created_at`` counts as
    predating the gate. ``still_enabled`` is the list that needs an answer today —
    a disabled rogue provider mints nothing; an enabled one keeps going.
    """
    before_gate: list[dict] = []
    undated = 0

    for row in rows:
        stamp = _parse(row.get("created_at"))
        if stamp is None:
            undated += 1
        if stamp is None or stamp < gate_cutoff:
            before_gate.append(row)

    still_enabled = [row for row in before_gate if row.get("enabled") is True]
    return before_gate, still_enabled, undated


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
        # Same hard-fail as `auth_providers` twenty lines up, for the same reason:
        # `OIDC_PROVIDER_CONFIGS` is in DOCUMENT_COLLECTIONS and created at
        # bootstrap, so its absence is an uninitialised database, not an empty one.
        # Defaulting to `[]` printed "identity providers registered: 0 … STILL
        # ENABLED: 0" — a clean bill of health about the half this script calls the
        # worse case, over a collection it never read.
        if not db.has_collection(col.OIDC_PROVIDER_CONFIGS):
            print(
                f"{col.OIDC_PROVIDER_CONFIGS} does not exist in "
                f"{settings.arangodb_database!r}. It is created at bootstrap beside "
                f"{col.AUTH_PROVIDERS}, so this database is uninitialised — check "
                f"ARANGODB_DATABASE. Refusing to report zero providers for a "
                f"collection that was never read.",
                file=sys.stderr,
            )
            return 1
        provider_rows = list(db.aql.execute(provider_configs_aql(col.OIDC_PROVIDER_CONFIGS)))
    except (ArangoError, OSError) as exc:
        print(_unreachable(settings, exc), file=sys.stderr)
        return 1

    registered_before, still_enabled, undated_providers = classify_providers(provider_rows, gate_cutoff)

    print(f"identity providers registered:   {len(provider_rows)}")
    print(
        f"  before the #1399 gate:         {len(registered_before)}  "
        f"({undated_providers} of them undated, counted as before)"
    )
    print(f"  of those, STILL ENABLED:       {len(still_enabled)}")
    if still_enabled:
        print()
        print("  These are the rows that still matter today — an enabled provider")
        print("  registered before the gate keeps minting links, and those links are")
        print("  after both cut-offs, so they appear in neither window below:")
        for cfg in still_enabled:
            print(
                f"    {cfg.get('slug')}  issuer={cfg.get('issuer_url')}  "
                f"created={cfg.get('created_at') or 'no timestamp'}"
            )
    print()

    if not rows:
        print(f"no federated links: {col.AUTH_PROVIDERS} holds {local_rows} local password row(s) and nothing else.")
        if still_enabled:
            # Never "so there is nothing to do" while an enabled pre-gate provider
            # is listed above — that combination IS the trap this script was
            # extended to catch, and closing with an all-clear would undo it.
            print(
                "That is NOT an all-clear: the enabled provider(s) listed above were "
                "registered before the gate and have simply not been used yet. Every "
                "link they mint from now on lands after both cut-offs."
            )
            return 0
        print("Nothing has ever been linked to an external identity provider.")
        return 0

    by_provider, before_gate, at_risk, undated = classify(rows, gate_cutoff, autolink_cutoff)
    orphaned = [row for row in rows if not row.get("user_exists")]

    print(f"federated links:                 {len(rows)}  ({local_rows} local password row(s) excluded)")
    print(f"  by provider:                   {dict(by_provider)}")
    print(f"  without a timestamp:           {undated}  (counted as inside BOTH windows)")
    print(f"  pointing at a deleted user:    {len(orphaned)}")
    print(f"created before the #1399 gate:   {len(before_gate)}  (< {gate_cutoff.isoformat()})")
    print(f"reachable by the auto-link path: {len(at_risk)}  (< {autolink_cutoff.isoformat()}, account email-verified)")
    if args.autolink_cutoff == DEFAULT_AUTOLINK_CUTOFF:
        print()
        print("NOTE: --autolink-cutoff is the develop-merge time, which is a FLOOR.")
        print("Your installation ran the defective image until its next rollout, and")
        print("links forged in that gap fall outside both windows. Re-run with")
        print("--autolink-cutoff <your deploy timestamp> for the number that applies")
        print("to this installation.")
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
        print("keys (for a manual look — most suspicious first: undated, then newest):")
        # Undated FIRST, not last. `classify` calls them the most suspicious rows
        # ("a row written by an older schema version is exactly the kind that
        # predates both fixes"), and sorting them to the bottom meant the listing
        # cap withheld precisely those on any installation with more than
        # KEY_LISTING_LIMIT of them.
        dated = [row for row in at_risk if stamp_of(row) is not None]
        undated_rows = [row for row in at_risk if stamp_of(row) is None]
        ordered = undated_rows + sorted(dated, key=stamp_of, reverse=True)
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
