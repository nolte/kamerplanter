#!/usr/bin/env python3
"""Delete the seeded subject through the platform-admin route (#1767).

The act half of the admin-delete reach probes, along the path production takes:

1. A platform admin is created the way an operator creates one: registered over
   ``POST /api/v1/auth/register`` and promoted with
   ``python -m app.migrations.add_platform_admin`` inside the backend container.
2. The admin signs in and sends ``DELETE /api/v1/admin/platform/users/{key}``
   for the seeded subject — the route that until #1767 discarded the erasure
   report.

It exits 0 whatever the route answered. The answer is logged for the operator,
never read as an observation; ``observe_erasure_residue.py`` counts the rows and
``observe_erasure_records.py`` reads the persisted erasure records instead.
Markers ``reach-marker:admin-delete:begin`` / ``:end`` bracket the act in
ArangoDB's query log.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    BACKEND_SERVICE,
    DEFAULT_SUBJECT,
    Arango,
    ReachError,
    compose_command,
    http_json,
    log,
    read_stack,
    read_subject,
    run,
)
from run_export_for_subject import sign_in  # noqa: E402

#: The erasure walks object storage and ~60 collections in one transaction.
DELETE_TIMEOUT_SECONDS = 300
ADMIN_EMAIL = "reach-platform-admin@example.com"


def _admin(api: str) -> dict[str, str]:
    password = secrets.token_urlsafe(18)
    status, body = http_json(
        "POST",
        f"{api}/api/v1/auth/register",
        body={"email": ADMIN_EMAIL, "password": password, "display_name": "Reach Platform Admin"},
    )
    if status != 201:
        raise ReachError(f"POST /auth/register for the admin answered {status}: {body}")
    run(
        compose_command("exec", "-T", BACKEND_SERVICE, "python", "-m", "app.migrations.add_platform_admin", ADMIN_EMAIL),
        timeout=120,
    )
    return {"email": ADMIN_EMAIL, "password": password}


def delete(subject_key: str) -> int:
    stack = read_stack()
    subject = read_subject(subject_key)
    api = stack["api_url"]
    arango = Arango(stack)

    headers = sign_in(api, _admin(api))
    arango.mark("reach-marker:admin-delete:begin")
    status, body = http_json(
        "DELETE",
        f"{api}/api/v1/admin/platform/users/{subject['subject']}",
        headers=headers,
        timeout=DELETE_TIMEOUT_SECONDS,
    )
    arango.mark("reach-marker:admin-delete:end")
    log(f"DELETE /admin/platform/users answered {status} (the act's end, not an observation): {body}")
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        delete(args.subject)
    except ReachError as exc:
        print(f"reach admin delete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
