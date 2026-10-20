"""NFR-015 §3.3 / REQ-053 WP 6.2 - the verdict logic of the plan cross-tenant probe.

`scripts/security/zap_plan_cross_tenant.py` sends the requests in the nightly; this
pins what it counts as a leak and what as a void run, without a network.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

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

_KW = {"base": "http://x", "slug_a": "a", "slug_b": "b", "site_a": "s1", "token_a": "TA", "token_b": "TB", "timeout": 1.0}


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
