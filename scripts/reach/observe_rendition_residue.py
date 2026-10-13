#!/usr/bin/env python3
"""Look at the subject's image renditions after its erasure: deleted or still stored (#1760).

Observation step of the ``requirement-req025-art17-storage-renditions-erased``
reach probe. For every file ``seed_stored_files.py`` uploaded it checks, on the
host side of the backend's object storage (``storage_root`` from
``.reach/stack.json``), whether the WebP renditions the seed rendered next to
it (``renditions`` in ``.reach/subjects/<subject>.files.json``) still exist. It
reads the files on disk, never the erasure's report or a log line.

Output, one member per line (the runner compares; this script states no verdict):

* ``renditions-deleted/<category>`` — none of the category's renditions exists;
* ``renditions-kept/<category>`` — all of them exist;
* ``renditions-partial/<category>=<present>/<seeded>`` — some exist;
* ``seeded/<n>`` — how many renditions the seed rendered, so the output is never empty.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, ReachError, read_stack  # noqa: E402
from observe_storage_residue import files_record  # noqa: E402


def present_counts(storage_root: Path, files: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    """``category -> (renditions present, renditions seeded)``; refuses a key outside the root."""
    root = storage_root.resolve()
    counts: dict[str, tuple[int, int]] = {}
    for entry in files:
        keys = entry.get("renditions")
        if not keys:
            raise ReachError(f"the {entry['category']} file has no rendered renditions; re-run the seed")
        present = 0
        for key in keys:
            path = (root / key).resolve()
            if root not in path.parents:
                raise ReachError(f"rendition key {key!r} resolves outside {root}")
            present += path.is_file()
        counts[entry["category"]] = (present, len(keys))
    return counts


def members(counts: dict[str, tuple[int, int]]) -> list[str]:
    """Member lines for the measured *counts* (pure; unit-tested)."""
    lines: list[str] = []
    for category in sorted(counts):
        present, seeded = counts[category]
        if present == 0:
            lines.append(f"renditions-deleted/{category}")
        elif present == seeded:
            lines.append(f"renditions-kept/{category}")
        else:
            lines.append(f"renditions-partial/{category}={present}/{seeded}")
    lines.append(f"seeded/{sum(seeded for _, seeded in counts.values())}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        record = files_record(args.subject)
        counts = present_counts(Path(read_stack()["storage_root"]), record["files"])
    except ReachError as exc:
        print(f"observe renditions: {exc}", file=sys.stderr)
        return 1
    for line in members(counts):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
