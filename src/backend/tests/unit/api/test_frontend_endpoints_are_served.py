"""Every frontend API call names a path some backend route serves (#1334).

A frontend endpoint module can name a path no route serves, and until #1334
nothing found out but a browser. `POST /planting-runs/{key}/batch-transition` was
live behind a button for as long as the button existed; its unit test asserted
that same wrong path, so it was green from the day it was written — a test that
checks the client against itself rather than against the contract.

The join is mechanical, and this tier is where it belongs: the backend unit tier
already imports the FastAPI app, and the frontend endpoint modules are text. #1334
supposed this would need a nightly lane because "the `static` lane does not have
the importable app" — measured, it needs neither: both operands are already here.

**What it does not claim.** It matches on method + path template only. A route
that exists but rejects the body, or returns a shape the client mis-reads, passes
here — that is exactly what happened *around* #1334, whose response fields did not
match either. This rules out the one failure a browser is otherwise needed to see:
a call that cannot reach any handler at all.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover - defensive
    pytest.skip("checkout root not found", allow_module_level=True)

_ENDPOINT_DIR = _REPO_ROOT / "src" / "frontend" / "src" / "api" / "endpoints"
if not _ENDPOINT_DIR.is_dir():  # pragma: no cover - frontend absent
    pytest.skip(f"{_ENDPOINT_DIR} does not exist", allow_module_level=True)

#: `client.<verb>(`…`)` — the request helpers every endpoint module goes through.
_CALL = re.compile(r"client\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*`([^`]+)`")
#: A module-level `const NAME = 'value'`, which is how each module names its base path.
_CONST = re.compile(r"const\s+([A-Z_][A-Z0-9_]*)\s*=\s*'([^']+)'")
#: Any `${…}` interpolation — a path parameter, whatever the local variable is called.
_INTERPOLATION = re.compile(r"\$\{[^}]*\}")

#: Calls known to reach no route, each with the issue that owns the decision.
#:
#: Registered rather than fixed here: all three need a product decision (build the
#: endpoint, or take the control out of the UI), which #1339 holds. The register
#: also fails when an entry is *repaired* and left behind, so it cannot outlive
#: the debt — the rule `_KNOWN_OPEN` in the substrate invariants established.
_KNOWN_UNSERVED: dict[tuple[str, str], str] = {
    ("PUT", "/tanks/sensors/{}"): "#1339 — no sensor update route exists at any prefix",
    ("DELETE", "/tanks/sensors/{}"): "#1339 — no sensor delete route exists at any prefix",
    ("POST", "/tasks/{}/photos"): "#1339 — task photo upload has no backend route",
}


def _mounted_routes() -> set[tuple[str, str]]:
    """Every (method, path) the app serves, with parameters normalised to ``{}``.

    Walks `original_router`, because `include_router` does **not** flatten: read
    `app.routes` directly and you find six routes instead of ~790, and the scan
    looks like it worked.
    """
    from app.main import app

    found: set[tuple[str, str]] = set()

    def walk(router: object, prefix: str = "") -> None:
        for route in getattr(router, "routes", []):
            path = prefix + getattr(route, "path", "")
            if getattr(route, "endpoint", None) is not None:
                for method in getattr(route, "methods", ()) or ():
                    if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                        found.add((method, re.sub(r"\{[^}]*\}", "{}", path)))
            inner = getattr(route, "original_router", None) or getattr(route, "app", None)
            if inner is not None and hasattr(inner, "routes"):
                walk(inner, path)

    walk(app)
    return found


def _frontend_calls() -> list[tuple[str, str, str]]:
    """Every ``(module, METHOD, path)`` the frontend issues, parameters as ``{}``."""
    calls: list[tuple[str, str, str]] = []
    for module in sorted(_ENDPOINT_DIR.glob("*.ts")):
        source = module.read_text(encoding="utf-8")
        constants = dict(_CONST.findall(source))
        for verb, template in _CALL.findall(source):
            path = template
            for name, value in constants.items():
                path = path.replace("${" + name + "}", value)
            path = _INTERPOLATION.sub("{}", path).split("?")[0].rstrip("/") or "/"
            calls.append((module.name, verb.upper(), path))
    return calls


def _is_served(method: str, path: str, mounted: set[tuple[str, str]]) -> bool:
    """A frontend path may be written with or without the API and tenant prefixes."""
    return any((method, candidate) in mounted for candidate in (f"/api/v1{path}", "/api/v1/t/{}" + path, path))


def test_the_scan_found_both_operands() -> None:
    """Neither side may be silently empty — an empty join passes vacuously.

    Without this the whole file reads green if `include_router` changes shape or
    the endpoint directory moves, which is the failure mode it exists to prevent.
    """
    assert len(_mounted_routes()) > 500
    assert len(_frontend_calls()) > 200


def test_every_frontend_call_reaches_a_route() -> None:
    mounted = _mounted_routes()

    unserved = {
        (method, path): module for module, method, path in _frontend_calls() if not _is_served(method, path, mounted)
    }

    unregistered = {key: module for key, module in unserved.items() if key not in _KNOWN_UNSERVED}
    assert not unregistered, "frontend calls no backend route serves: " + "; ".join(
        f"{method} {path} ({module})" for (method, path), module in sorted(unregistered.items())
    )


def test_the_register_does_not_outlive_the_debt() -> None:
    """A repaired entry left behind turns the register into a set of pre-approvals."""
    mounted = _mounted_routes()

    healed = [f"{method} {path}" for (method, path) in _KNOWN_UNSERVED if _is_served(method, path, mounted)]

    assert not healed, "these are served now and must be removed from _KNOWN_UNSERVED: " + ", ".join(sorted(healed))
