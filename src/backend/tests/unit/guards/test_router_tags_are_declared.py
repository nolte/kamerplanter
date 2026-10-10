"""#2167 — every tag a mounted route carries is declared in ``OPENAPI_TAGS``.

The defect: #2163 (#2112) mounted a router tagged ``admin-ha-entity-grants``
without declaring the tag in ``app/api/v1/openapi_tags.py``. The only check that
knew the rule was ``scripts/export_openapi.py`` in the ``OpenAPI export + lint``
lane of ``api-docs.yml`` — path-filtered and advisory — so the pull request
merged with that lane red, ``develop`` stayed red, and the failure surfaced on
the next pull request (#2164, fixed there in 4cdc0c31c).

This file moves the rule into the unit tier. ``tests/unit/guards`` is run by the
required ``Write-route and tree guards`` context (``backend-guards.yml``, an
unfiltered ``on: push``), so an undeclared tag now blocks the merge.

**Predicate** — a member is every ``APIRoute`` reachable from the assembled
application, found by walking ``_IncludedRouter.original_router`` (this FastAPI
version does not flatten ``include_router`` onto ``app.routes``). A member's tags
are the ones FastAPI itself assigns: every enclosing ``include_context.tags``
(which already carries the parent router's own ``tags=``) plus ``route.tags``.

**Surface** — the walk runs in a subprocess with the export's own pin,
:data:`scripts.export_openapi.FULL_SURFACE_ENV`, because two routers mount only
in full mode or with the knowledge service enabled. The guard therefore sees
exactly the surface the export lane sees, independent of this process's flags.

**What it cannot see**: tags written into the document after generation (none
are — ``_openapi_postprocessed`` only touches ``security`` and path parameters),
and the Spectral rules of the same lane, which stay advisory.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]

#: Bounds the recursion; a router graph is never this deep, a cycle would hang.
_MAX_DEPTH = 10


def _tag_name(tag: str | Enum) -> str:
    return str(tag.value) if isinstance(tag, Enum) else tag


def route_tags(
    routes: Iterable[Any], inherited: tuple[str, ...] = (), prefix: str = "", _depth: int = 0
) -> Iterator[tuple[str, frozenset[str]]]:
    """Yield ``("<METHODS> <path>", tags)`` for every ``APIRoute`` below *routes*.

    Mirrors FastAPI's own composition (``_RouterIncludeContext.combine`` and
    ``_EffectiveRouteContext.from_api_route``): the tags of a leaf route are the
    tags of every enclosing include context followed by its own.
    """
    if _depth > _MAX_DEPTH:
        return
    for route in routes:
        if isinstance(route, APIRoute):
            label = f"{','.join(sorted(route.methods or ()))} {prefix}{route.path}"
            yield label, frozenset(_tag_name(t) for t in (*inherited, *route.tags))
            continue
        nested = getattr(route, "original_router", None)
        if nested is None:
            continue
        context = route.include_context
        yield from route_tags(
            nested.routes,
            (*inherited, *(_tag_name(t) for t in context.tags)),
            prefix + context.prefix,
            _depth + 1,
        )


def undeclared_route_tags(application: FastAPI, declared: Iterable[str]) -> dict[str, list[str]]:
    """Map every tag used by a route of *application* but missing from *declared* to its routes."""
    declared_names = set(declared)
    undeclared: dict[str, list[str]] = {}
    for label, tags in route_tags(application.routes):
        for tag in sorted(tags - declared_names):
            undeclared.setdefault(tag, []).append(label)
    return undeclared


def used_route_tags(application: FastAPI) -> set[str]:
    return set().union(*(tags for _, tags in route_tags(application.routes)))


def _declared_names() -> list[str]:
    from app.api.v1.openapi_tags import OPENAPI_TAGS

    return [tag["name"] for tag in OPENAPI_TAGS]


# Runs in a fresh interpreter with FULL_SURFACE_ENV applied before ``app.main``
# is imported; prints one JSON object as its last stdout line.
_FULL_SURFACE_PROBE = """
import json, structlog, sys
structlog.configure(logger_factory=structlog.PrintLoggerFactory(sys.stderr))
import app
from app.config.settings import settings
from app.main import app as application
from tests.unit.guards.test_router_tags_are_declared import (
    _declared_names, undeclared_route_tags, used_route_tags,
)
print(json.dumps({
    "app_file": app.__file__,
    "mode": settings.kamerplanter_mode,
    "knowledge": settings.knowledge_service_enabled,
    "used": sorted(used_route_tags(application)),
    "undeclared": undeclared_route_tags(application, _declared_names()),
}))
"""


def _probe_full_surface() -> dict[str, Any]:
    from scripts.export_openapi import FULL_SURFACE_ENV

    python_path = os.pathsep.join(p for p in (str(BACKEND_ROOT), os.environ.get("PYTHONPATH", "")) if p)
    env = {**os.environ, **FULL_SURFACE_ENV, "PYTHONPATH": python_path}
    probe = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _FULL_SURFACE_PROBE],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    return json.loads(probe.stdout.strip().splitlines()[-1])


def test_every_route_tag_on_the_full_surface_is_declared() -> None:
    """The rule ``scripts/export_openapi.py`` enforces, run where a merge is blocked."""
    result = _probe_full_surface()

    # The probe imported THIS tree and mounted the superset the export pins —
    # otherwise an empty or partial surface would pass vacuously.
    assert pathlib.Path(result["app_file"]).resolve().is_relative_to(BACKEND_ROOT), result["app_file"]
    assert result["mode"] == "full"
    assert result["knowledge"] is True
    assert len(result["used"]) > 1, result["used"]

    assert result["undeclared"] == {}, (
        "Route tags missing from app/api/v1/openapi_tags.py (declare each with a description): "
        + json.dumps(result["undeclared"], indent=2)
    )


def test_the_walk_sees_every_tag_the_openapi_document_uses() -> None:
    """The walk reads FastAPI internals; if an upgrade hides routes from it, fail instead of passing silently."""
    from app.main import app

    documented: set[str] = set()
    for path_item in app.openapi()["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                documented.update(operation.get("tags", []))

    assert documented, "the OpenAPI document carries no tags — the comparison would be vacuous"
    assert documented <= used_route_tags(app), sorted(documented - used_route_tags(app))


def test_the_detector_reports_a_real_tag_removed_from_the_declaration() -> None:
    """Same detector, same application, one real declaration withheld: it must be reported."""
    from app.main import app

    declared = _declared_names()
    assert "health" in declared
    undeclared = undeclared_route_tags(app, [name for name in declared if name != "health"])

    assert set(undeclared) == {"health"}
    assert "GET /api/health" in undeclared["health"]


class _Tag(Enum):
    ENUM = "enum-tag"


def test_the_detector_finds_tags_at_every_level_of_nesting() -> None:
    """A tag can enter through the router, the include call, the route, or an enum — each is reported."""
    leaf = APIRouter(tags=["leaf-router"])

    @leaf.get("/item", tags=["route", _Tag.ENUM])
    def _item() -> dict[str, str]:
        return {}

    middle = APIRouter(prefix="/middle")
    middle.include_router(leaf, prefix="/leaf", tags=["leaf-include"])
    application = FastAPI()
    application.include_router(middle, prefix="/api", tags=["top-include"])

    expected = {"leaf-router", "route", "enum-tag", "leaf-include", "top-include"}
    assert used_route_tags(application) == expected

    for withheld in sorted(expected):
        undeclared = undeclared_route_tags(application, expected - {withheld})
        assert undeclared == {withheld: ["GET /api/middle/leaf/item"]}, withheld

    assert undeclared_route_tags(application, expected) == {}
