"""NFR-015 §3.3 / REQ-053 WP 6.2 - the verdict logic of the plan cross-tenant probe.

`scripts/security/zap_plan_cross_tenant.py` sends the requests in the nightly; this
pins what it counts as a leak and what as a void run, without a network.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from app.api.v1.router import api_router
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover - only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SCRIPT = _REPO_ROOT / "scripts" / "security" / "zap_plan_cross_tenant.py"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "security-zap-nightly.yml"

_spec = importlib.util.spec_from_file_location("_zap_plan_cross_tenant_under_test", _SCRIPT)
assert _spec is not None and _spec.loader is not None
probe = importlib.util.module_from_spec(_spec)
sys.modules["_zap_plan_cross_tenant_under_test"] = probe
_spec.loader.exec_module(probe)

_KW = {
    "base": "http://x",
    "slug_a": "a",
    "slug_b": "b",
    "site_a": "s1",
    "token_a": "TA",
    "token_b": "TB",
    "timeout": 1.0,
}


def _run(foreign: int, control: int = 200):
    def sender(method, url, token, body, timeout):
        return control if token == "TA" else foreign

    return probe.evaluate(probe.ROUTES, sender=sender, **_KW)


def test_routes_cover_import_and_batch() -> None:
    names = {r.name for r in probe.ROUTES}
    assert {"plan/import", "plan/batch"} <= names


@pytest.mark.parametrize("foreign", [403, 404])
def test_refusal_is_clean(foreign: int) -> None:
    assert _run(foreign) == ([], [])


@pytest.mark.parametrize("foreign", [200, 201, 409, 422, 500])
def test_anything_but_a_refusal_is_a_leak(foreign: int) -> None:
    leaks, void = _run(foreign)
    assert len(leaks) == 2 * len(probe.ROUTES)
    assert void == []


def test_dead_tenant_b_token_voids_the_run() -> None:
    leaks, void = _run(401)
    assert leaks == []
    assert len(void) == 2 * len(probe.ROUTES)


@pytest.mark.parametrize("control", [0, 401, 403, 405])
def test_dead_owner_control_voids_the_run(control: int) -> None:
    leaks, void = _run(404, control=control)
    assert leaks == []
    assert len(void) == len(probe.ROUTES)


def test_nightly_runs_the_probe_before_the_scan() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert text.index("zap_plan_cross_tenant.py") < text.index("zap-full-scan.py")


def _mounted() -> set[tuple[str, str]]:
    """(METHOD, path with every {param} reduced to {}) for each route the v1 router mounts."""
    found: set[tuple[str, str]] = set()

    def walk(router, prefix: str = "") -> None:
        for route in getattr(router, "routes", []):
            included = getattr(route, "original_router", None)
            if included is not None:
                context = getattr(route, "include_context", None)
                walk(included, prefix + (getattr(context, "prefix", "") or ""))
                continue
            path = prefix + (getattr(route, "path", "") or "")
            for method in getattr(route, "methods", ()) or ():
                found.add((method, re.sub(r"\{[^}]+\}", "{}", path)))

    walk(api_router)
    return found


@pytest.mark.parametrize("route", probe.ROUTES, ids=lambda r: r.name)
def test_every_probed_route_is_mounted(route) -> None:
    """The owner control may answer 404/422, so this is what proves the route exists (NFR-018 §1)."""
    expected = re.sub(r"\{[^}]+\}", "{}", f"/api/v1/t/{{tenant_slug}}/sites/{{key}}/{route.path_template}")
    assert (route.method, expected) in _mounted(), f"{route.method} {expected} is not mounted"


def test_a_renamed_route_would_fail_the_existence_check() -> None:
    assert ("POST", "/api/v1/t/{}/sites/{}/plan/bacth") not in _mounted()


def test_server_error_is_reported_as_unproven() -> None:
    leaks, void = _run(500)
    assert void == []
    assert all("isolation unproven" in line for line in leaks)


def test_redirects_are_not_followed() -> None:
    handler = probe._NoRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "http://x/y") is None
