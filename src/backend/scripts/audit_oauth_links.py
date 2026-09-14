#!/usr/bin/env python
"""Read-only audit of `auth_providers` rows that predate the #1399 gate (#1403).

**Reads only.** No write, no delete, no argument that could become one — the point
is to answer "how many, and which?" before anyone decides what to do about them.

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

## What the numbers mean

`at_risk` is not "compromised". It counts links that *could* have been created by
the defective path: the local account is email-verified (so auto-link would have
fired) and the row predates the cut-off. In a single-operator installation the
answer is usually "one, your own", and that ends the question.

Usage::

    python scripts/audit_oauth_links.py [--cutoff 2026-09-10T00:00:00Z]

The default cut-off is the merge of PR #1400, which shipped #1399's gate. Rows
newer than it were created under the gate; rows older than it were not.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: PR #1400 (`5e9c8662b`) — the commit that gated `/admin/oidc-providers`.
DEFAULT_CUTOFF = "2026-09-10T00:00:00+00:00"


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify(rows: list[dict], cutoff: datetime) -> tuple[Counter[str], list[dict], list[dict], int]:
    """Split the links into ``(by_provider, before_gate, at_risk, undated)``.

    Extracted from ``main`` so the two decisions it encodes are testable without a
    database — they are decisions, not plumbing:

    **An undated row counts as before the gate.** Absence of a timestamp is not
    evidence of being recent, and for a question about a security window the
    pessimistic reading is the right one. A row written by an older schema version
    is exactly the kind that predates the gate.

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
        stamp = _parse(row.get("linked_at")) or _parse(row.get("created_at"))
        if stamp is None:
            undated += 1
            before_gate.append(row)
        elif stamp < cutoff:
            before_gate.append(row)
        else:
            continue
        if row.get("user_email_verified") is True:
            at_risk.append(row)

    return by_provider, before_gate, at_risk, undated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="ISO timestamp of the #1399 gate")
    args = parser.parse_args()

    cutoff = _parse(args.cutoff)
    if cutoff is None:
        print(f"unparseable cutoff: {args.cutoff!r}", file=sys.stderr)
        return 2

    from app.config.settings import settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection

    db = ArangoConnection(settings).db
    if not db.has_collection(col.AUTH_PROVIDERS):
        print("no auth_providers collection — nothing has ever been linked")
        return 0

    query = f"""
    FOR link IN {col.AUTH_PROVIDERS}
      LET user = FIRST(FOR u IN {col.USERS} FILTER u._key == link.user_key RETURN u)
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
    rows = list(db.aql.execute(query))

    if not rows:
        print("auth_providers is empty — no federated link has ever been created.")
        return 0

    by_provider, before_gate, at_risk, undated = classify(rows, cutoff)

    print(f"auth_providers rows:            {len(rows)}")
    print(f"  by provider:                  {dict(by_provider)}")
    print(f"created before the #1399 gate:  {len(before_gate)}  (cut-off {cutoff.isoformat()})")
    print(f"  of those, without a timestamp: {undated}  (counted as before, pessimistically)")
    print(f"reachable by the auto-link path: {len(at_risk)}")
    print()
    print("'reachable' means the local account is email-verified, so the defective")
    print("auto-link branch would have fired for it. It is NOT evidence that any of")
    print("these was forged — the data layer cannot tell the two apart, which is the")
    print("reason this script reports instead of acting (#1403).")

    if at_risk:
        print()
        print("keys (for a manual look, newest first):")
        for row in sorted(at_risk, key=lambda r: r.get("linked_at") or "", reverse=True)[:50]:
            stamp = row.get("linked_at") or row.get("created_at") or "no timestamp"
            print(f"  {row['key']}  user={row['user_key']}  provider={row.get('provider')}  {stamp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
