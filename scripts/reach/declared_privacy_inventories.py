#!/usr/bin/env python3
"""Print the two declared personal-data inventories as the running backend builds them (#1680).

Runs **inside the backend container** of the reach stack; invoked by
``observe_executing_inventory.py``. It calls the two builders the executing
paths call — ``DataExportEngine.build_export_manifest`` (the Art. 15 walk) and
``ErasureEngine.build_erasure_plan`` (the Art. 17 executor) — and prints, as
JSON, the ArangoDB collections each one declares:

* ``export-manifest`` — every disclosed source's collection and edge collection;
* ``erasure-plan`` — every ``edge`` / ``document`` / ``user`` step's collection
  and every anonymisation and audit-pseudonymisation rule's collection.

These are the *declarations* the observation compares the executed queries with.
What the code actually executed comes from ArangoDB's query log, not from here.
"""

from __future__ import annotations

import argparse
import json
import sys

from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", required=True)
    args = parser.parse_args(argv)

    manifest = [s for s in DataExportEngine().build_export_manifest(args.subject) if s.disclosure_gap is None]
    export = {s.collection for s in manifest} | {s.edge_collection for s in manifest if s.edge_collection}

    plan = ErasureEngine().build_erasure_plan(args.subject)
    erasure = {s.collection for s in plan.steps if s.kind in ("edge", "document", "user")}
    erasure |= {rule.collection for rule in plan.anonymize}
    erasure |= {rule.collection for rule in plan.pseudonymize_audit}

    json.dump({"export-manifest": sorted(export), "erasure-plan": sorted(erasure)}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
