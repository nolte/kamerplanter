#!/usr/bin/env python3
"""Delete the seeded tenant through the platform-admin route (#1769).

The act half of the tenant-erasure reach probes, along the path production takes:
a platform admin is registered and promoted the way ``admin_delete_subject.py``
does it, signs in and sends ``DELETE /api/v1/admin/platform/tenants/{key}`` —
the route that until #1769 removed four collections and left the rest.

It exits 0 whatever the route answered. The answer is logged for the operator,
never read as an observation; ``observe_tenant_residue.py`` reads the rows and
the persisted record instead. Markers ``reach-marker:tenant-delete:begin`` /
``:end`` bracket the act in ArangoDB's query log.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import Arango, ReachError, http_json, log, read_stack  # noqa: E402
from admin_delete_subject import DELETE_TIMEOUT_SECONDS, _admin  # noqa: E402
from run_export_for_subject import sign_in  # noqa: E402


def delete(tenant_key: str) -> int:
    stack = read_stack()
    api = stack["api_url"]
    arango = Arango(stack)
    admin = _admin(api)
    headers = sign_in(api, admin)
    arango.mark("reach-marker:tenant-delete:begin")
    # #1791: the deletion carries its step-up — the tenant's slug typed back
    # (``seed_tenant_for_erasure.py`` gives the tenant its key as slug) and the
    # admin's current password.
    status, body = http_json(
        "DELETE",
        f"{api}/api/v1/admin/platform/tenants/{tenant_key}",
        headers=headers,
        body={"confirm_slug": tenant_key, "password": admin["password"]},
        timeout=DELETE_TIMEOUT_SECONDS,
    )
    arango.mark("reach-marker:tenant-delete:end")
    log(f"DELETE /admin/platform/tenants answered {status} (the act's end, not an observation): {body}")
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    try:
        delete(args.tenant)
    except ReachError as exc:
        print(f"tenant delete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
