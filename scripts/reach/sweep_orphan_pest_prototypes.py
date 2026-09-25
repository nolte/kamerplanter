#!/usr/bin/env python3
"""Run the pest-prototype orphan sweep the way the daily beat does (#1771).

The act half of the orphan-sweep reach probe:

1. read ``system_settings.pest_prototype_orphan_sweep.last_run_at`` (may be absent);
2. send ``pest_image.sweep_orphaned_prototypes`` — the task the beat schedules
   daily at 04:30 UTC — **through the broker** from the worker container
   (``celery call``), and the worker runs it;
3. wait until the sweep record carries a newer ``last_run_at``.

It says nothing about what the sweep removed: the record is the artefact's own
statement, and ``observe_orphan_pest_prototypes.py`` counts the rows in
``pest_embeddings`` instead. A sweep that fails records nothing, so the wait
times out and the act fails — the probe is then *not probed*, never reached.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    WORKER_SERVICE,
    Arango,
    ReachError,
    compose_command,
    log,
    read_stack,
    run,
    wait_until,
)

SWEEP_TIMEOUT_SECONDS = 180
TASK = "pest_image.sweep_orphaned_prototypes"

_LAST_RUN = """
FOR s IN system_settings
  FILTER s._key == "default"
  RETURN s.pest_prototype_orphan_sweep.last_run_at
"""


def last_run(arango: Arango) -> Any:
    rows = arango.aql(_LAST_RUN)
    return rows[0] if rows else None


def sweep() -> None:
    arango = Arango(read_stack())
    before = last_run(arango)
    log(f"sending {TASK} through the broker (previous run: {before or 'none'})")
    run(compose_command("exec", "-T", WORKER_SERVICE, "celery", "-A", "app.tasks", "call", TASK), timeout=120)

    def recorded() -> Any:
        current = last_run(arango)
        return current if current is not None and current != before else None

    after = wait_until(recorded, timeout=SWEEP_TIMEOUT_SECONDS, what="the orphan sweep to record a run")
    log(f"the orphan sweep recorded a run at {after} (the act's end, not an observation)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    try:
        sweep()
    except ReachError as exc:
        print(f"reach orphan sweep: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
