#!/usr/bin/env python3
"""Look at the pest-recognition index after the orphan sweep: orphans gone, live and curated rows kept (#1771).

Observation step of the ``requirement-req025-art17-pest-prototype-orphan-sweep``
reach probe. It queries the pgvector ``pest_embeddings`` rows
``vectordb.py seed-pest-orphans`` wrote — never the sweep record or a log line:
those are what the sweep says about itself.

From ``.reach/subjects/<subject>.pest-orphans.json`` it takes the seeded row ids
and asks, in one query, how many ``user_contributed`` rows still carry an
orphaned contribution key, whether the live contribution's prototype still
exists, and whether the curated control row (same record id as an orphan,
other source) still exists.

Output, one member per line (the runner compares; this script states no verdict):

* ``erased/orphans`` — no ``user_contributed`` row carries an orphaned key;
  ``residue/orphans=<n>`` otherwise;
* ``kept/live`` / ``deleted/live`` — the prototype of the contribution whose
  document exists;
* ``kept/curated`` / ``deleted/curated`` — the curated control row;
* ``seeded/<n>`` — how many rows the seed wrote, so the output is never empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, ReachError  # noqa: E402
from vectordb import orphan_file, psql, read_record  # noqa: E402

_STATE = """
SELECT (SELECT count(*) FROM pest_embeddings
         WHERE source = 'user_contributed' AND source_record_id = ANY(string_to_array(:'orphan_keys', ','))),
       EXISTS (SELECT 1 FROM pest_embeddings WHERE id = ANY(string_to_array(:'live_ids', ',')::integer[])),
       EXISTS (SELECT 1 FROM pest_embeddings WHERE id = :'curated_id'::integer);
"""

_BOOLEAN = {"t": True, "f": False}


def parse_state(output: str) -> tuple[int, bool, bool]:
    """Read the query's one ``<n>|t|f`` row (pure; unit-tested)."""
    fields = output.strip().split("|")
    if len(fields) != 3 or not fields[0].isdigit() or fields[1] not in _BOOLEAN or fields[2] not in _BOOLEAN:
        raise ReachError(f"unreadable answer from the pest index: {output!r}")
    return int(fields[0]), _BOOLEAN[fields[1]], _BOOLEAN[fields[2]]


def members(state: tuple[int, bool, bool], seeded_total: int) -> list[str]:
    """Member lines for the measured *state* (pure; unit-tested)."""
    remaining, live_present, curated_present = state
    return [
        f"residue/orphans={remaining}" if remaining else "erased/orphans",
        "kept/live" if live_present else "deleted/live",
        "kept/curated" if curated_present else "deleted/curated",
        f"seeded/{seeded_total}",
    ]


def measure(subject: str) -> tuple[tuple[int, bool, bool], int]:
    path = orphan_file(subject)
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:pest-orphans` first")
    seeded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rows = seeded["rows"]
    orphan_keys = sorted({r["contribution_key"] for r in rows if r["role"] == "orphan"})
    live_ids = [str(r["id"]) for r in rows if r["role"] == "live"]
    if not orphan_keys or not live_ids:
        raise ReachError(f"{path} names no orphaned or no live row")
    output = psql(
        read_record(),
        _STATE,
        {
            "orphan_keys": ",".join(orphan_keys),
            "live_ids": ",".join(live_ids),
            "curated_id": str(seeded["curated_id"]),
        },
    )
    return parse_state(output), len(rows) + 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        state, seeded_rows = measure(args.subject)
    except ReachError as exc:
        print(f"observe orphan pest prototypes: {exc}", file=sys.stderr)
        return 1
    for line in members(state, seeded_rows):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
