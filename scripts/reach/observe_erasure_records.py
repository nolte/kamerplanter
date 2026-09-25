#!/usr/bin/env python3
"""Read the erasure records an immediate erasure persisted (#1767).

Observation step of the ``admin-delete-persists-proof`` reach probe. Until
#1767 the platform-admin delete persisted no erasure record at all; the probe's
declaration is that it now leaves one, closed only when every declared step was
reached, and that the record no longer names the subject once the ArangoDB plan
has run.

Output, one member per line (the runner compares; this script states no verdict):

* ``record/<origin>/<status>`` — one line per distinct pair among the
  ``erasure_requests`` documents that carry an ``origin`` (records written by
  an erasure entry, not the seed's audit rows);
* ``subject-in-records/<n>`` — how many ``erasure_requests`` documents still
  contain the subject's key anywhere in their content;
* ``records/<n>`` — how many documents the collection holds, so the output is
  never empty.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, Arango, ReachError, read_stack  # noqa: E402

_RECORDS = """
FOR doc IN erasure_requests
  RETURN {
    origin: doc.origin,
    status: doc.status,
    names_subject: CONTAINS(TO_STRING(UNSET(doc, "_id", "_rev")), @subject)
  }
"""


def observe(subject: str) -> list[str]:
    arango = Arango(read_stack())
    rows = arango.aql(_RECORDS, {"subject": subject})
    lines = sorted({f"record/{row['origin']}/{row['status']}" for row in rows if row.get("origin")})
    lines.append(f"subject-in-records/{sum(1 for row in rows if row['names_subject'])}")
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
