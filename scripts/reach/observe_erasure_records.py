#!/usr/bin/env python3
"""Read the erasure records an immediate erasure persisted (#1767).

Observation step of the ``admin-delete-persists-proof`` reach probe. Until
#1767 the platform-admin delete persisted no erasure record at all; the probe's
declaration is that it now leaves one, closed only when every declared step was
reached, and that the record no longer names the subject once the ArangoDB plan
has run. Since #1814 the platform-admin record also carries the step-up it was
confirmed with and the admin who asked, as a salted reference only — never the
admin's account key, since the record outlives both accounts.

Output, one member per line (the runner compares; this script states no verdict):

* ``record/<origin>/<status>`` — one line per distinct pair among the
  ``erasure_requests`` documents that carry an ``origin`` (records written by
  an erasure entry, not the seed's audit rows);
* ``subject-in-records/<n>`` — how many ``erasure_requests`` documents still
  contain the subject's key anywhere in their content;
* ``step-up/<origin>/<step_up>`` — one line per distinct pair among the
  origin-bearing records (``none`` when the record carries no step-up);
* ``requested-by/<origin>/<n>`` — per origin, how many records carry a
  ``requested_by_subject``;
* ``requester-in-records/<n>`` — how many ``erasure_requests`` documents contain
  the account key of the platform admin the act signed in as
  (``admin_delete_subject.ADMIN_EMAIL``); ``requester-absent`` instead when no
  such account exists, so a missing act never reads as zero;
* ``records/<n>`` — how many documents the collection holds, so the output is
  never empty.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, Arango, ReachError, read_stack  # noqa: E402
from admin_delete_subject import ADMIN_EMAIL  # noqa: E402

_RECORDS = """
FOR doc IN erasure_requests
  RETURN {
    origin: doc.origin,
    status: doc.status,
    step_up: doc.step_up,
    requested_by: doc.requested_by_subject != null AND doc.requested_by_subject != "",
    content: TO_STRING(UNSET(doc, "_id", "_rev"))
  }
"""

_REQUESTER = """
FOR u IN users
  FILTER u.email == @email
  RETURN u._key
"""


def observe(subject: str) -> list[str]:
    arango = Arango(read_stack())
    rows = arango.aql(_RECORDS, {})
    with_origin = [row for row in rows if row.get("origin")]
    lines = sorted({f"record/{row['origin']}/{row['status']}" for row in with_origin})
    lines += sorted({f"step-up/{row['origin']}/{row.get('step_up') or 'none'}" for row in with_origin})
    origins = sorted({row["origin"] for row in with_origin})
    lines += [f"requested-by/{o}/{sum(1 for r in with_origin if r['origin'] == o and r['requested_by'])}" for o in origins]
    lines.append(f"subject-in-records/{sum(1 for row in rows if subject in row['content'])}")
    requester = arango.aql(_REQUESTER, {"email": ADMIN_EMAIL})
    if requester:
        lines.append(f"requester-in-records/{sum(1 for row in rows if requester[0] in row['content'])}")
    else:
        lines.append("requester-absent")
    lines.append(f"records/{len(rows)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        for line in observe(args.subject):
            print(line)
    except ReachError as exc:
        print(f"reach erasure records: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
