#!/usr/bin/env python3
"""After the subject's erasure: is the co-holder's copy of a shared photo still there? (#1770)

Observation step of the ``requirement-req025-art17-storage-shared-file-kept``
reach probe. ``seed_shared_file.py`` had the subject and a co-holder upload the
same bytes into a shared tenant (``.reach/subjects/<subject>.shared.json``). This
reads what is there now — the object's bytes on disk under the stack's
``storage_root`` and the ``attachments`` documents in ArangoDB — never the
erasure request's report or a log line, which are what the erasure says about
itself.

Output, one member per line (the runner compares; this script states no verdict):

* ``holder-file/present`` | ``holder-file/deleted`` — the shared object;
* ``holder-link/present`` | ``holder-link/absent`` — a record of the co-holder
  (``created_by`` the co-holder) pointing at that object;
* ``subject-link/present`` | ``subject-link/absent`` — a record of the subject
  over that object;
* ``control-file/present`` | ``control-file/deleted`` — the subject's photo no
  one else holds.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, Arango, ReachError, reach_dir, read_stack  # noqa: E402

_LINKS_QUERY = """
FOR att IN attachments
  FILTER att.tenant_key == @tenant_key AND att.storage_key == @storage_key
  RETURN att.created_by
"""


def _file_line(label: str, root: Path, storage_key: str) -> str:
    path = (root / storage_key).resolve()
    if root not in path.parents:
        raise ReachError(f"storage key {storage_key!r} resolves outside {root}")
    return f"{label}/{'present' if path.is_file() else 'deleted'}"


def members(*, holder_file: str, control_file: str, owners: list[str], subject: str, holder: str) -> list[str]:
    """The member lines for one observation (pure; unit-tested)."""
    return sorted(
        [
            holder_file,
            f"holder-link/{'present' if holder in owners else 'absent'}",
            f"subject-link/{'present' if subject in owners else 'absent'}",
            control_file,
        ]
    )


def shared_record(subject: str) -> dict[str, Any]:
    path = reach_dir() / "subjects" / f"{subject}.shared.json"
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:shared-file` first")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        record = shared_record(args.subject)
        stack = read_stack()
        root = Path(stack["storage_root"]).resolve()
        storage_key = record["shared"]["storage_key"]
        owners = Arango(stack).aql(_LINKS_QUERY, {"tenant_key": record["tenant_key"], "storage_key": storage_key})
        lines = members(
            holder_file=_file_line("holder-file", root, storage_key),
            control_file=_file_line("control-file", root, record["control"]["storage_key"]),
            owners=list(owners),
            subject=record["subject"],
            holder=record["co_holder"],
        )
    except ReachError as exc:
        print(f"observe shared file: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
