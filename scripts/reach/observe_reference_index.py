#!/usr/bin/env python3
"""Look at the reference index after the subject's erasure: contribution gone, curated row kept (#1745).

Observation step of the ``requirement-req025-art17-reference-index-cleanup``
reach probe. It queries the rows of the pgvector ``species_embeddings`` table
``vectordb.py`` started and seeded — never the erasure request's
``reference_index_removed`` count or a log line: those are what the erasure says
about itself, and the no-op store reports its ``0`` as a successful cleanup.

From ``.reach/subjects/<subject>.embeddings.json`` it takes the two seeded row
ids and asks the store, in one query over ``docker exec … psql``, whether the
subject's contributed row still exists, how many rows are still attributed to
the subject (``contributed_by``), and whether the curated control row still
exists.

Output, one member per line (the runner compares; this script states no verdict):

* ``erased/species_embeddings`` — the seeded contribution is gone and no row is
  attributed to the subject any more;
* ``residue/species_embeddings=<n>`` — otherwise, with *n* the rows still
  attributed to the subject (``=0`` means the contributed vector survived with
  its attribution cleared);
* ``kept/curated`` / ``deleted/curated`` — whether the curated control row survived;
* ``seeded/<n>`` — how many rows the seed wrote, so the output is never empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, ReachError  # noqa: E402
from vectordb import embeddings_file, psql, read_record  # noqa: E402

#: The seed writes the subject's contribution and one curated control row.
SEEDED_ROWS = 2

_STATE = """
SELECT EXISTS (SELECT 1 FROM species_embeddings WHERE id = :'contributed_id'::integer),
       (SELECT count(*) FROM species_embeddings WHERE contributed_by = :'subject'),
       EXISTS (SELECT 1 FROM species_embeddings WHERE id = :'curated_id'::integer);
"""

_BOOLEAN = {"t": True, "f": False}


@dataclass
class IndexState:
    contributed_present: bool
    attributed: int
    curated_present: bool


def parse_state(output: str) -> IndexState:
    """Read the query's one ``t|<n>|f`` row (pure; unit-tested)."""
    fields = output.strip().split("|")
    if len(fields) != 3 or fields[0] not in _BOOLEAN or fields[2] not in _BOOLEAN or not fields[1].isdigit():
        raise ReachError(f"unreadable answer from the reference index: {output!r}")
    return IndexState(_BOOLEAN[fields[0]], int(fields[1]), _BOOLEAN[fields[2]])


def members(state: IndexState, seeded_total: int) -> list[str]:
    """Member lines for the measured *state* (pure; unit-tested)."""
    if state.contributed_present or state.attributed:
        lines = [f"residue/species_embeddings={state.attributed}"]
    else:
        lines = ["erased/species_embeddings"]
    lines.append("kept/curated" if state.curated_present else "deleted/curated")
    lines.append(f"seeded/{seeded_total}")
    return lines


def measure(subject: str) -> IndexState:
    path = embeddings_file(subject)
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:reference-embedding` first")
    seeded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    output = psql(
        read_record(),
        _STATE,
        {
            "subject": subject,
            "contributed_id": str(seeded["contributed_id"]),
            "curated_id": str(seeded["curated_id"]),
        },
    )
    return parse_state(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        state = measure(args.subject)
    except ReachError as exc:
        print(f"observe reference index: {exc}", file=sys.stderr)
        return 1
    for line in members(state, SEEDED_ROWS):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
