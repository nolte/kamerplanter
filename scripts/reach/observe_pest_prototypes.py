#!/usr/bin/env python3
"""Look at the pest-recognition index after the subject's erasure: prototype gone, curated row kept (#1759).

Observation step of the ``requirement-req025-art17-pest-prototype-cleanup``
reach probe. It queries the pgvector ``pest_embeddings`` rows ``vectordb.py
seed-pest`` wrote — never the erasure request's ``pest_prototypes_removed`` or a
log line: those are what the erasure says about itself, and the pre-#1759
erasure logged a "retract" while the row stayed.

From ``.reach/subjects/<subject>.pest-prototypes.json`` it takes the seeded row
ids and contribution keys and asks, in one query, whether any contributed row
still exists, how many ``user_contributed`` rows still carry one of the keys, and whether the curated control row (same record id, other
source) still exists.

Output, one member per line (the runner compares; this script states no verdict):

* ``erased/pest_embeddings`` — the seeded prototype is gone and no
  ``user_contributed`` row carries one of the contribution keys;
* ``residue/pest_embeddings=<n>`` — otherwise, *n* such rows remain;
* ``kept/curated`` / ``deleted/curated`` — whether the curated control row survived;
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
from vectordb import pest_file, psql, read_record  # noqa: E402

_STATE = """
SELECT EXISTS (SELECT 1 FROM pest_embeddings WHERE id = ANY(string_to_array(:'contributed_ids', ',')::integer[])),
       (SELECT count(*) FROM pest_embeddings
         WHERE source = 'user_contributed' AND source_record_id = ANY(string_to_array(:'contribution_keys', ','))),
       EXISTS (SELECT 1 FROM pest_embeddings WHERE id = :'curated_id'::integer);
"""

_BOOLEAN = {"t": True, "f": False}


def parse_state(output: str) -> tuple[bool, int, bool]:
    """Read the query's one ``t|<n>|f`` row (pure; unit-tested)."""
    fields = output.strip().split("|")
    if len(fields) != 3 or fields[0] not in _BOOLEAN or fields[2] not in _BOOLEAN or not fields[1].isdigit():
        raise ReachError(f"unreadable answer from the pest index: {output!r}")
    return _BOOLEAN[fields[0]], int(fields[1]), _BOOLEAN[fields[2]]


def members(state: tuple[bool, int, bool], seeded_total: int) -> list[str]:
    """Member lines for the measured *state* (pure; unit-tested)."""
    contributed_present, remaining, curated_present = state
    lines = [f"residue/pest_embeddings={remaining}" if contributed_present or remaining else "erased/pest_embeddings"]
    lines.append("kept/curated" if curated_present else "deleted/curated")
    lines.append(f"seeded/{seeded_total}")
    return lines


def measure(subject: str) -> tuple[tuple[bool, int, bool], int]:
    path = pest_file(subject)
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:pest-prototype` first")
    seeded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    contributions = seeded["contributions"]
    output = psql(
        read_record(),
        _STATE,
        {
            "contributed_ids": ",".join(str(c["contributed_id"]) for c in contributions),
            "contribution_keys": ",".join(c["contribution_key"] for c in contributions),
            "curated_id": str(seeded["curated_id"]),
        },
    )
    return parse_state(output), len(contributions) + 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        state, seeded_rows = measure(args.subject)
    except ReachError as exc:
        print(f"observe pest prototypes: {exc}", file=sys.stderr)
        return 1
    for line in members(state, seeded_rows):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
