#!/usr/bin/env python3
"""Drive the Art. 15 data export for the seeded subject through the real path (#1680).

The act half of the export reach probe: the subject signs in, ``POST
/api/v1/privacy/export`` creates the request, the API dispatches
``retention.process_data_export`` through the broker, and the Celery worker walks
the declared manifest and writes the bundle into object storage. This script
waits until the request reached a terminal state and exits 0 — whichever state
that is. It does **not** report on the export: the status it waits on is the
artefact's own record and says nothing about what the archive holds. Opening
the archive is ``observe_export_archive.py``'s job.

Before and after the act it leaves a marker query in ArangoDB's query log
(``reach-marker:export:begin`` / ``:end``), so ``observe_executing_inventory.py``
can tell the export's queries from the erasure's.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    DEFAULT_SUBJECT,
    Arango,
    ReachError,
    http_json,
    log,
    read_stack,
    read_subject,
    wait_until,
)

#: The export task retries with backoff on infrastructure errors (#1666); a
#: healthy run finishes in seconds.
EXPORT_TIMEOUT_SECONDS = 240
TERMINAL = ("completed", "failed")


def sign_in(api_url: str, subject: dict) -> dict[str, str]:
    """Bearer header of a fresh session of the subject."""
    status, body = http_json(
        "POST",
        f"{api_url}/api/v1/auth/login",
        body={"email": subject["email"], "password": subject["password"], "refresh_token_in_body": True},
    )
    if status != 200 or not isinstance(body, dict) or "access_token" not in body:
        raise ReachError(f"sign-in of the seeded subject answered {status}: {body}")
    return {"Authorization": f"Bearer {body['access_token']}"}


def run_export(subject_key: str) -> str:
    stack = read_stack()
    subject = read_subject(subject_key)
    api = stack["api_url"]
    arango = Arango(stack)

    arango.mark("reach-marker:export:begin")
    headers = sign_in(api, subject)
    status, body = http_json("POST", f"{api}/api/v1/privacy/export", headers=headers)
    if status != 201 or not isinstance(body, dict) or not body.get("key"):
        raise ReachError(f"POST /privacy/export answered {status}: {body}")
    export_key = body["key"]
    log(f"export {export_key} requested; waiting for the worker")

    def terminal() -> str | None:
        code, current = http_json("GET", f"{api}/api/v1/privacy/export/{export_key}", headers=headers)
        if code == 200 and isinstance(current, dict) and current.get("status") in TERMINAL:
            return str(current["status"])
        return None

    state = wait_until(terminal, timeout=EXPORT_TIMEOUT_SECONDS, what=f"export {export_key} to finish")
    arango.mark("reach-marker:export:end")
    log(f"export {export_key} ended in state {state!r} (the act's end, not an observation)")
    return export_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        run_export(args.subject)
    except ReachError as exc:
        print(f"reach export: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
