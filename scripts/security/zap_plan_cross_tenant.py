#!/usr/bin/env python3
"""Cross-tenant negative tests for the garden-plan mutation routes.

Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.3, REQ-053 §26 (WP 6.2).

The passive cross-tenant rule only fires on traffic the spider happens to
generate, and the spider sends no bodies, so it never reaches the plan routes
that need one. This step sends those requests itself, as tenant B, against a
site that belongs to tenant A, and requires a refusal (403 or 404):

    * URL space  - tenant B's token on tenant A's slug:  /t/<A>/sites/<keyA>/...
    * object     - tenant B's own slug, tenant A's site: /t/<B>/sites/<keyA>/...

Anything other than 403/404 for either is a cross-tenant leak and fails the
step (exit 1). A 401, or a request that dies before an answer, voids the run
(exit 2): a scan whose credentials failed proves nothing and must not read as
"no leak found" (NFR-018 §1).

Each route is first sent once as tenant A, the owner. That answer must not be
401/403/405, so a green result cannot come from a mistyped path or a dead
token. Tenant A's own answer may still be 404/422 for a made-up child key; only
the foreign answer carries the verdict.

Every body is harmless on purpose: the import is a dry run and the batch deletes
a key that does not exist. Nothing here may change tenant A's data when the
isolation holds; the only write is tenant A's own boundary, which also gives the
site the plan the other routes need.

Routes sent (all tenant-scoped, site-keyed, in app/api/v1/garden_plan):
    PUT  plan/boundary          POST plan/batch
    POST plan/import            POST plan/place-template
    POST plan/snapshots/{audit_key}/restore
Not sent: irrigation-zones/*, bed-templates/*, planting-runs/mixed-culture (they
need a seeded child resource of their own, so they are not the same pattern).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib import error, request

REFUSED = (403, 404)
VOID = (0, 401)

_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


@dataclass(frozen=True)
class Route:
    name: str
    method: str
    suffix: str
    body: dict[str, Any]


ROUTES: tuple[Route, ...] = (
    # First: it creates tenant A's plan, which the later control requests need.
    Route("plan/boundary", "PUT", "plan/boundary", {"boundary": _RECT, "north_angle_deg": 0}),
    Route(
        "plan/batch",
        "POST",
        "plan/batch",
        {"operations": [{"op": "delete", "entity": "garden_object", "key": "go_zap_probe"}]},
    ),
    Route(
        "plan/import",
        "POST",
        "plan/import",
        {
            "mode": "merge",
            "dry_run": True,
            "document": {"schema_version": "1", "site": {"name": "zap-probe"}, "locations": [], "garden_objects": []},
        },
    ),
    Route(
        "plan/place-template",
        "POST",
        "plan/place-template",
        {"template_key": "sys_raised_bed_2x1x0_8", "origin": [1.0, 1.0], "rotation_deg": 0},
    ),
    Route(
        "plan/snapshots/{audit_key}/restore",
        "POST",
        "plan/snapshots/zap_probe_audit/restore",
        {"dry_run": True, "force": False},
    ),
)


def send(method: str, url: str, token: str, body: dict[str, Any], timeout: float) -> int:
    req = request.Request(url, method=method, data=json.dumps(body).encode("utf-8"))
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except error.HTTPError as exc:
        return exc.code
    except (error.URLError, TimeoutError, OSError):
        return 0


def evaluate(
    routes: tuple[Route, ...],
    *,
    base: str,
    slug_a: str,
    slug_b: str,
    site_a: str,
    token_a: str,
    token_b: str,
    timeout: float,
    sender=send,
) -> tuple[list[str], list[str]]:
    """Return (leaks, void_reasons); both empty means every foreign request was refused."""
    leaks: list[str] = []
    void: list[str] = []
    for route in routes:
        own = f"{base}/api/v1/t/{slug_a}/sites/{site_a}/{route.suffix}"
        control = sender(route.method, own, token_a, route.body, timeout)
        if control in (0, 401, 403, 405):
            void.append(f"{route.method} {route.name} - owner control answered {control}")
            continue
        targets = (
            ("url-space", f"{base}/api/v1/t/{slug_a}/sites/{site_a}/{route.suffix}"),
            ("object", f"{base}/api/v1/t/{slug_b}/sites/{site_a}/{route.suffix}"),
        )
        for label, url in targets:
            status = sender(route.method, url, token_b, route.body, timeout)
            if status in VOID:
                void.append(f"{route.method} {route.name} [{label}] - tenant B token answered {status}")
            elif status not in REFUSED:
                leaks.append(f"{route.method} {route.name} [{label}] - foreign tenant got {status}, want 403/404")
    return leaks, void


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--tenant-a-slug", required=True)
    parser.add_argument("--tenant-b-slug", required=True)
    parser.add_argument("--site-key", required=True, help="a site of tenant A")
    parser.add_argument("--token-a", required=True)
    parser.add_argument("--token-b", required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    leaks, void = evaluate(
        ROUTES,
        base=args.base_url.rstrip("/"),
        slug_a=args.tenant_a_slug,
        slug_b=args.tenant_b_slug,
        site_a=args.site_key,
        token_a=args.token_a,
        token_b=args.token_b,
        timeout=args.timeout,
    )
    print(f"Plan routes probed: {len(ROUTES)} x 2 foreign requests (url-space, object).")
    for line in leaks:
        print(f"::error::CROSS-TENANT LEAK {line}")
    for line in void:
        print(f"::error::VOID RUN {line}")
    if leaks:
        return 1
    if void:
        return 2
    print("Every foreign-tenant plan request was refused (403/404).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
