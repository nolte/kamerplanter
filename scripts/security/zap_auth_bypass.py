#!/usr/bin/env python3
"""Two-pass auth-bypass detection over the routes OpenAPI declares as protected.

Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §4.2, escalation §5.1.

For every route the document marks as requiring authentication, the same request
goes out twice — once with a valid Bearer token, once without — and the pair of
status classes is classified:

    anonymous | authenticated | verdict
    ----------+---------------+------------------------------------------
    2xx       | 2xx           | AUTH BYPASS. Critical, blocks. The route is
              |               | declared protected and answers anyone.
    2xx       | 401/403       | Spec drift. Medium. Declared protected, is
              |               | actually public — or the token is wrong.
    401/403   | 2xx           | Expected. No finding.
    401/403   | 401/403       | The token is not working. The RUN is void:
              |               | reported as an error, because a scan whose
              |               | credentials failed proves nothing and must
              |               | not read as "no bypasses found".

That last row is the reason this exists as its own script rather than as a rule
inside ZAP. A run in which authentication silently failed would otherwise
produce a green result from an entirely anonymous scan — the failure class
NFR-018 §1 catalogues, in its most expensive form.

Only safe methods are probed (GET, HEAD). A bypass on a read route is the
finding that matters and it costs nothing to check; mutating an ephemeral stack
mid-scan would pollute what the other profiles see. The count of routes skipped
for any reason is always reported: a check that silently narrowed its own scope
reads as broader coverage than it had.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

SAFE_METHODS = {"get", "head"}

# §3.4 — routes that are legitimately reachable without a token. Probing them
# anonymously would report every one as a bypass.
ANONYMOUS_BY_DESIGN = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/oauth",
    "/api/v1/auth/refresh",
    "/api/v1/calendar/feeds/",
    "/api/v1/health",
    "/api/v1/ready",
)


def is_protected(operation: dict[str, Any], document: dict[str, Any]) -> bool:
    """Does this operation require authentication per the document?"""
    security = operation.get("security", document.get("security"))
    if not security:
        return False
    # `security: [{}]` means "optional"; a non-empty requirement object means
    # a credential is required.
    return any(bool(req) for req in security)


def fill_path(path: str, values: dict[str, str]) -> str | None:
    """Substitute `{param}` placeholders, or return None when one is unknown."""
    out = path
    while "{" in out:
        start = out.index("{")
        end = out.index("}", start)
        name = out[start + 1 : end]
        if name not in values:
            return None
        out = out[:start] + values[name] + out[end + 1 :]
    return out


def probe(url: str, token: str | None, timeout: float) -> int:
    req = request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except error.HTTPError as exc:
        return exc.code
    except (error.URLError, TimeoutError, OSError):
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="value for an OpenAPI path parameter, e.g. tenant_slug=zap-tenant-a",
    )
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    values = dict(p.split("=", 1) for p in args.param)
    document = json.loads(args.openapi.read_text(encoding="utf-8"))

    bypasses: list[str] = []
    drift: list[str] = []
    skipped_unresolvable = 0
    skipped_by_design = 0
    checked = 0
    auth_failures = 0

    for path, item in sorted(document.get("paths", {}).items()):
        if path.startswith(ANONYMOUS_BY_DESIGN):
            skipped_by_design += 1
            continue
        for method, operation in item.items():
            if method.lower() not in SAFE_METHODS:
                continue
            if not is_protected(operation, document):
                continue
            concrete = fill_path(path, values)
            if concrete is None:
                skipped_unresolvable += 1
                continue

            url = args.base_url.rstrip("/") + concrete
            authed = probe(url, args.token, args.timeout)
            anon = probe(url, None, args.timeout)
            checked += 1

            authed_ok = 200 <= authed < 300
            anon_ok = 200 <= anon < 300
            authed_denied = authed in (401, 403)

            if anon_ok and authed_ok:
                bypasses.append(
                    f"{method.upper()} {concrete} — anonymous {anon}, authenticated {authed}"
                )
            elif anon_ok and authed_denied:
                drift.append(
                    f"{method.upper()} {concrete} — anonymous {anon}, authenticated {authed}"
                )
            elif authed_denied and anon in (401, 403):
                auth_failures += 1

    print(
        f"Auth-bypass two-pass: {checked} protected route(s) probed, "
        f"{skipped_by_design} anonymous-by-design, {skipped_unresolvable} skipped "
        f"(unresolvable path parameter)."
    )
    if skipped_unresolvable:
        print(
            f"::warning::{skipped_unresolvable} protected route(s) were not probed because a "
            f"path parameter had no fixture value. Coverage is narrower than the route count suggests."
        )
    for line in drift:
        print(
            f"::warning::Spec drift — declared protected but answered anonymously: {line}"
        )

    # An authenticated pass that is itself denied means the credentials are
    # broken. Reporting "no bypasses" from such a run would be a lie about
    # coverage, so the run is voided instead.
    if checked and auth_failures == checked:
        print(
            "::error::Every probed route denied the AUTHENTICATED request too. The token is "
            "not working, so this run proves nothing about auth bypasses — voiding it rather "
            "than reporting a clean result.",
            file=sys.stderr,
        )
        return 2

    if bypasses:
        print(
            "::error::AUTH BYPASS — routes declared as protected answered without a token "
            "(NFR-015 §5.1: Critical, always blocking):",
            file=sys.stderr,
        )
        for line in bypasses:
            print(f"  {line}", file=sys.stderr)
        return 1

    print("No auth bypasses found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
