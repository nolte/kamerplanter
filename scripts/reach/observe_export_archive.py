#!/usr/bin/env python3
"""Open the Art. 15 archive the export produced and list what of the subject it holds (#1680).

Observation step of the ``data-export-populated`` reach probe. It reads the
bundle file(s) the export worker wrote into object storage for the subject —
``<storage root>/privacy/exports/<subject>/*.json`` on the stack's shared
storage directory — and never the export request's ``status``, ``file_path`` or
``manifest_collections``: those are what the export says about itself.

A record in the archive counts as one of the subject's seeded rows only when it
carries that row's seed marker (``reach-seed:<row key>:<field>``, written by
``seed_privacy_subject.py`` into the row's plain text fields) or — for a row
whose disclosed fields hold no free text, such as a membership — when it is a
projection of the row's seeded content holding a value only the seed wrote. An archive of
empty sections, or of sections holding records that are not the subject's, lists
nothing — counting the sections present would measure presence, and a stub that
writes every section empty would pass.

Output, one member per line (the runner compares; this script states no verdict):

* ``collection/<name>`` — a section of that collection holds at least one of the
  subject's seeded rows of that collection;
* ``edge/<name>`` — the row the seed linked to the subject through that edge
  (``users/<subject>`` → the row) is in the archive. It says the subject's row
  on the far side of the edge was disclosed, not which route the walk took;
* ``archive/<file name>`` for every bundle opened, or ``archive/none`` when the
  export produced no file — so an absent archive is an observation, never silence.

``--detail`` adds ``records/<collection>=<n>`` and ``recognised/<collection>=<k>``
lines per section for a human reading the output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, ReachError, read_stack, read_subject  # noqa: E402

#: ``reach-seed:<row key>:<field>``, or ``reach-seed.<row key>.<field>@…`` in an e-mail field.
MARKER = re.compile(r"^reach-seed[:.](rs[0-9a-f]+|[A-Za-z0-9_-]+?)[:.]")


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def marked_row_keys(record: Any) -> set[str]:
    """Keys of the seeded rows whose marker appears anywhere in *record*."""
    keys: set[str] = set()
    for text in _strings(record):
        match = MARKER.match(text)
        if match:
            keys.add(match.group(1))
    return keys


def fingerprint_match(record: Any, row: dict[str, Any]) -> bool:
    """A record is *row* when it is a projection of the row's seeded content holding a value only it has.

    For rows whose disclosed fields carry no marker (a membership: keys, a role,
    flags; a past request: a status and timestamps). ``distinct`` lists the
    values only the seed wrote — the subject's tenant key, a subject reference, a
    unique timestamp — so a projection that holds one and agrees with the row on
    every field is that row, not a lookalike.
    """
    fingerprint = row.get("fingerprint")
    if not fingerprint or not isinstance(record, dict) or not record:
        return False
    if any(name not in fingerprint or fingerprint[name] != value for name, value in record.items()):
        return False
    distinct = set(row.get("distinct", []))
    return any(isinstance(value, str) and value in distinct for value in record.values())


def observe(bundles: list[dict[str, Any]], subject: dict[str, Any], *, detail: bool = False) -> list[str]:
    """The member lines for the opened *bundles* of *subject* (pure; unit-tested)."""
    rows_by_key = {row["key"]: row for row in subject["rows"] if row["kind"] != "edge"}
    fingerprinted = [row for row in rows_by_key.values() if row.get("fingerprint")]
    delivered: set[str] = set()
    delivered_collections: set[str] = set()
    lines: list[str] = []
    detail_lines: list[str] = []
    for bundle in bundles:
        for section in bundle.get("sections", []):
            collection = section.get("collection")
            records = section.get("records") or []
            recognised = 0
            for record in records:
                rows = [rows_by_key[key] for key in marked_row_keys(record) if key in rows_by_key]
                rows += [row for row in fingerprinted if row not in rows and fingerprint_match(record, row)]
                for row in rows:
                    if row["collection"] == collection:
                        delivered.add(row["id"])
                        delivered_collections.add(row["collection"])
                        recognised += 1
            detail_lines += [f"records/{collection}={len(records)}", f"recognised/{collection}={recognised}"]
    lines += [f"collection/{name}" for name in sorted(delivered_collections)]
    lines += [
        f"edge/{edge}" for edge, target in sorted(subject.get("subject_edges", {}).items()) if target in delivered
    ]
    return lines + (detail_lines if detail else [])


def bundle_files(storage_root: Path, subject: str) -> list[Path]:
    """The bundles in the subject's export folder (the storage adapter's ``*.meta.json`` sidecars excluded)."""
    folder = storage_root / "privacy" / "exports" / subject
    return sorted(path for path in folder.glob("*.json") if not path.name.endswith(".meta.json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    parser.add_argument("--detail", action="store_true", help="add per-section record counts")
    args = parser.parse_args(argv)
    try:
        stack = read_stack()
        subject = read_subject(args.subject)
    except ReachError as exc:
        print(f"observe export: {exc}", file=sys.stderr)
        return 1
    files = bundle_files(Path(stack["storage_root"]), args.subject)
    if not files:
        print("archive/none")
        return 0
    bundles = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    for line in observe(bundles, subject, detail=args.detail):
        print(line)
    for path in files:
        print(f"archive/{path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
