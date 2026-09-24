#!/usr/bin/env python3
"""Count what is left of the subject in the database after its erasure (#1680).

Observation step of the ``erasure-finalisation`` reach probe. It reads rows, never
the erasure request's ``status``, ``deleted_collections`` or the executor's
report: those are what the erasure says about itself.

For every collection the seed wrote a row of the subject into
(``.reach/subjects/<subject>.json``), it measures three things:

* ``gone`` — the subject's seeded rows that no longer exist;
* ``changed`` — the subject's seeded rows that still exist with a different
  ``_rev`` than the seed wrote;
* ``matching`` — rows **anywhere in the collection** that still point at the
  subject: whose content (every attribute except ``_key``/``_id``/``_rev``)
  contains the subject's key, or that reference one of the subject's seeded rows
  that is gone (an edge ``_from``/``_to``, or a top-level value equal to its key
  or id — a location assignment whose membership was removed). The subject's
  e-mail and display name contain its key by construction of the seed, and row
  keys are random, so a retained row that was properly redacted matches nothing.

Output, one member per line (the runner compares; this script states no verdict):

* ``erased/<collection>`` — ``matching`` is 0 and at least one seeded row is gone;
* ``redacted/<collection>`` — ``matching`` is 0 and at least one seeded row
  survived with changed content;
* ``residue/<collection>=<matching>`` — rows that still point at the subject;
* ``seeded/<n>`` — how many rows the seed wrote, so the output is never empty.

``--counts`` prints ``<collection> seeded=… gone=… changed=… matching=…`` instead.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, Arango, ReachError, read_stack, read_subject  # noqa: E402

_MATCHING = """
FOR doc IN @@collection
  LET content = UNSET(doc, "_key", "_id", "_rev")
  FILTER CONTAINS(TO_STRING(content), @subject)
    OR (HAS(doc, "_from") AND doc._from IN @gone)
    OR (HAS(doc, "_to") AND doc._to IN @gone)
    OR LENGTH(INTERSECTION(VALUES(UNSET(content, "_from", "_to")), @gone)) > 0
  COLLECT WITH COUNT INTO matching
  RETURN matching
"""


@dataclass
class Residue:
    collection: str
    seeded: int
    gone: int
    changed: int
    matching: int


def members(residues: list[Residue], seeded_total: int) -> list[str]:
    """Member lines for measured *residues* (pure; unit-tested)."""
    lines: list[str] = []
    for item in sorted(residues, key=lambda r: r.collection):
        if item.matching:
            lines.append(f"residue/{item.collection}={item.matching}")
            continue
        if item.gone:
            lines.append(f"erased/{item.collection}")
        if item.changed:
            lines.append(f"redacted/{item.collection}")
    lines.append(f"seeded/{seeded_total}")
    return lines


def measure(arango: Arango, subject: dict[str, Any]) -> list[Residue]:
    rows = subject["rows"]
    current = {row["id"]: arango.document(row["id"]) for row in rows}
    gone_refs: list[str] = []
    for row in rows:
        if current[row["id"]] is None:
            gone_refs += [row["id"], row["key"]]
    residues: list[Residue] = []
    for collection in sorted({row["collection"] for row in rows}):
        own = [row for row in rows if row["collection"] == collection]
        gone = [row for row in own if current[row["id"]] is None]
        changed = [row for row in own if current[row["id"]] is not None and current[row["id"]]["_rev"] != row["rev"]]
        bind_vars = {"@collection": collection, "subject": subject["subject"], "gone": gone_refs}
        matching = arango.aql(_MATCHING, bind_vars)[0]
        residues.append(Residue(collection, len(own), len(gone), len(changed), int(matching)))
    return residues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    parser.add_argument("--counts", action="store_true", help="print raw counts per collection instead")
    args = parser.parse_args(argv)
    try:
        subject = read_subject(args.subject)
        residues = measure(Arango(read_stack()), subject)
    except ReachError as exc:
        print(f"observe erasure: {exc}", file=sys.stderr)
        return 1
    if args.counts:
        for item in residues:
            counts = f"seeded={item.seeded} gone={item.gone} changed={item.changed} matching={item.matching}"
            print(f"{item.collection} {counts}")
        return 0
    for line in members(residues, len(subject["rows"])):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
