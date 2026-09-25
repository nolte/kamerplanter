#!/usr/bin/env python3
"""Count what is left of a tenant in the database after its deletion (#1769).

Observation step of the tenant-erasure reach probes. It reads rows, never the
deletion's own answer or the executor's report as evidence of reach; the
``--records`` mode reads the persisted proof, for the probe that asks whether the
proof exists.

Default output, one member per line (the runner compares; this script states no
verdict). For every seeded row of the tenant (``.reach/subjects/tenant-<tenant>.json``):

* ``erased/<collection>`` — a row the seed marked ``delete`` is gone (and
  ``erased/tenants`` for the tenant document);
* ``pseudonymised/<collection>`` — an ``anonymize`` row survived, changed, and
  no longer contains the member's account key;
* ``retained/<collection>`` — a ``retain`` row survived unchanged (``_rev``);
* ``residue/<collection>``, ``lost/<collection>``, ``changed/<collection>`` — the
  three ways each of the above can fail;
* ``dangling-edges/<n>`` — seeded edges of the tenant still present with an
  endpoint that is gone;
* ``stamped-elsewhere/<n>`` — rows carrying the tenant's key in any collection
  that holds none of its retained rows, other than the deletion record itself
  (a collection nobody declared shows here);
* ``control-changed/<n>`` — rows of the control tenant changed or gone.

``--records`` prints ``record/<origin>/<status>`` per persisted deletion record of
the tenant, ``record-unreached/<n>`` and ``member-in-records/<n>`` (records that
contain the member's key).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import Arango, ReachError, read_stack, read_subject  # noqa: E402

_CONTAINS = 'RETURN CONTAINS(TO_STRING(UNSET(DOCUMENT(@id), "_key", "_id", "_rev")), @needle)'
_STAMPED = "FOR doc IN @@collection FILTER doc.tenant_key == @tenant COLLECT WITH COUNT INTO n RETURN n"
#: The deletion's own proof carries the tenant's key by design; ``--records`` reads it.
_PROOF_COLLECTION = "tenant_erasure_records"
_RECORDS = f"FOR doc IN {_PROOF_COLLECTION} FILTER doc.tenant_key == @tenant RETURN doc"


def _contains(arango: Arango, doc_id: str, needle: str) -> bool:
    return bool(arango.aql(_CONTAINS, {"id": doc_id, "needle": needle})[0])


def members(arango: Arango, record: dict[str, Any]) -> list[str]:
    tenant, member = record["tenant"], record["member"]
    rows = record["rows"]
    current = {row["id"]: arango.document(row["id"]) for row in rows}
    gone = {row["id"] for row in rows if current[row["id"]] is None}
    lines: set[str] = set()
    retained_collections: set[str] = set()
    for row in rows:
        role, collection, now = row["role"], row["collection"], current[row["id"]]
        if not role.startswith("tenant:") or row["kind"] == "edge":
            continue
        action = role.split(":", 1)[1]
        if action in ("delete", "tenant"):
            lines.add(f"{'erased' if now is None else 'residue'}/{collection}")
        elif action == "anonymize":
            retained_collections.add(collection)
            if now is None:
                lines.add(f"lost/{collection}")
            elif now["_rev"] != row["rev"] and not _contains(arango, row["id"], member):
                lines.add(f"pseudonymised/{collection}")
            else:
                lines.add(f"residue/{collection}")
        elif action == "retain":
            retained_collections.add(collection)
            unchanged = now is not None and now["_rev"] == row["rev"]
            lines.add(f"{'retained' if unchanged else 'changed'}/{collection}")

    dangling = 0
    for row in rows:
        if row["role"] != "tenant:edge" or current[row["id"]] is None:
            continue
        edge = current[row["id"]]
        dangling += int(edge["_from"] in gone or edge["_to"] in gone)
    stamped = sum(
        int(arango.aql(_STAMPED, {"@collection": name, "tenant": tenant})[0])
        for name in sorted(arango.collections())
        if not name.startswith("_") and name not in retained_collections and name != _PROOF_COLLECTION
    )
    control = sum(
        1
        for row in rows
        if row["role"].startswith("control:") and (current[row["id"]] or {}).get("_rev") != row["rev"]
    )
    return sorted(lines) + [f"dangling-edges/{dangling}", f"stamped-elsewhere/{stamped}", f"control-changed/{control}"]


def record_members(arango: Arango, record: dict[str, Any]) -> list[str]:
    docs = arango.aql(_RECORDS, {"tenant": record["tenant"]})
    lines = [f"record/{doc['origin']}/{doc['status']}" for doc in docs]
    lines.append(f"record-unreached/{sum(len(doc.get('unreached') or []) for doc in docs)}")
    lines.append(f"member-in-records/{sum(1 for doc in docs if record['member'] in str(doc))}")
    return sorted(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--records", action="store_true", help="read the persisted deletion records instead")
    args = parser.parse_args(argv)
    try:
        record = read_subject(f"tenant-{args.tenant}")
        arango = Arango(read_stack())
        lines = record_members(arango, record) if args.records else members(arango, record)
    except ReachError as exc:
        print(f"observe tenant erasure: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
