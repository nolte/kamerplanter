"""#2142 (REQ-056 AK-43, §7.8, §14) — the plan routes exist in full mode only; the quota view in both.

Light mode has no admin routes: its one tenant stays on ``standard`` and every limit is the instance
setting. The entitlements view hangs on the tenant routes, which both modes mount. Measured on the
assembled app of each mode in a fresh interpreter (``_all_routes``), not on the router object.
"""

from __future__ import annotations

from tests.api.test_ai_public_routes_light_mode_only import _all_routes

PLAN_ROUTES = {
    "GET /api/v1/admin/platform/plans",
    "POST /api/v1/admin/platform/plans",
    "PATCH /api/v1/admin/platform/plans/{plan_key}",
    "DELETE /api/v1/admin/platform/plans/{plan_key}",
    "GET /api/v1/admin/platform/tenants/{key}",
}
ENTITLEMENTS = "GET /api/v1/tenants/{tenant_slug}/entitlements"


def test_full_mode_mounts_the_plan_routes_and_the_quota_view() -> None:
    routes = _all_routes("full")

    assert routes >= PLAN_ROUTES
    assert ENTITLEMENTS in routes


def test_light_mode_mounts_no_plan_route() -> None:
    routes = _all_routes("light")

    assert PLAN_ROUTES & routes == set()
    assert ENTITLEMENTS in routes
