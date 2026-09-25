#!/usr/bin/env python3
"""Request the seeded subject's Art. 17 erasure and run the scheduled finalisation (#1680).

The act half of the erasure reach probe, along the path production takes:

1. The subject signs in and ``POST /api/v1/privacy/erasure`` with its password
   creates the request (soft-delete now, hard delete scheduled 90 days out).
2. The request's ``hard_delete_scheduled_at`` is moved to the past. This is the
   one thing the act does *to* the data: it stands in for the 90-day grace
   period, which a probe cannot wait out. Nothing else about the request changes.
3. ``retention.execute_scheduled_erasures`` — the task the beat schedules daily at
   04:00 UTC — is sent **through the broker** from the worker container
   (``celery call``), exactly as the beat sends it, and the worker runs it.
4. The script waits until the request left ``scheduled`` / ``in_progress``.

It exits 0 whatever state the request ended in. That state is the artefact's own
record and is never read as an observation; ``observe_erasure_residue.py`` counts
the rows instead. Markers ``reach-marker:erasure:begin`` / ``:end`` bracket the
act in ArangoDB's query log for ``observe_executing_inventory.py``.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    DEFAULT_SUBJECT,
    WORKER_SERVICE,
    Arango,
    ReachError,
    compose_command,
    http_json,
    log,
    read_stack,
    read_subject,
    run,
    wait_until,
)
from run_export_for_subject import sign_in  # noqa: E402

#: The erasure walks object storage and ~60 collections in one transaction.
ERASURE_TIMEOUT_SECONDS = 300
TERMINAL = ("completed", "partially_completed")

_BACKDATE = """
FOR doc IN erasure_requests
  FILTER doc._key == @key
  UPDATE doc WITH { hard_delete_scheduled_at: @due } IN erasure_requests
  RETURN NEW._key
"""

_STATUS = """
FOR doc IN erasure_requests
  FILTER doc._key == @key
  RETURN doc.status
"""


def finalise(subject_key: str) -> str:
    stack = read_stack()
    subject = read_subject(subject_key)
    api = stack["api_url"]
    arango = Arango(stack)

    arango.mark("reach-marker:erasure:begin")
    headers = sign_in(api, subject)
    status, body = http_json(
        "POST",
        f"{api}/api/v1/privacy/erasure",
        body={"confirm_email": subject["email"], "password": subject["password"]},
        headers=headers,
    )
    if status != 201 or not isinstance(body, dict) or not body.get("key"):
        raise ReachError(f"POST /privacy/erasure answered {status}: {body}")
    erasure_key = body["key"]

    due = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    if arango.aql(_BACKDATE, {"key": erasure_key, "due": due}) != [erasure_key]:
        raise ReachError(f"erasure request {erasure_key} was not found to move its due date")
    log(f"erasure {erasure_key} requested and made due; sending the beat's task through the broker")

    run(
        compose_command(
            "exec", "-T", WORKER_SERVICE, "celery", "-A", "app.tasks", "call", "retention.execute_scheduled_erasures"
        ),
        timeout=120,
    )

    def terminal() -> str | None:
        states = arango.aql(_STATUS, {"key": erasure_key})
        return states[0] if states and states[0] in TERMINAL else None

    state = wait_until(terminal, timeout=ERASURE_TIMEOUT_SECONDS, what=f"erasure {erasure_key} to be finalised")
    arango.mark("reach-marker:erasure:end")
    log(f"erasure {erasure_key} ended in state {state!r} (the act's end, not an observation)")
    return erasure_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        finalise(args.subject)
    except ReachError as exc:
        print(f"reach erasure: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
