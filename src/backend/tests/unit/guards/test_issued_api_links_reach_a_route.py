"""#2226 — every ``/api/v1`` URL the backend writes into a response names a mounted route.

The defect: the feed-management routes kept handing out iCal subscription URLs
(``/api/v1/calendar/feeds/{key}/feed.ics?token=…``) for six and a half months
after the route answering them had been deleted (``a5345fbfb``, March 2026). Every
URL a member copied into a calendar app answered ``404``, and nothing in the tree
compared the URL a handler builds with the routes the app mounts. The sweep for
the class found a second instance: the MCP ``search_glossary`` tool linked to
``/api/v1/glossary/terms``, which no route has ever served.

**Predicate** — a member is every string literal and every f-string under
``app/`` (docstrings and bare string statements excluded; the parts of an
f-string are judged as the whole) that contains ``/api/v1/``. Its path is cut
at ``?``/``#``, every ``{…}`` becomes one placeholder segment, and it must match
a route of the assembled application (``include_router`` does not flatten, so
the walk follows ``original_router``), the light-only routers included. An
f-string ending in a placeholder may be a prefix of a longer route.

**Not a URL, therefore listed:** a literal used as a *prefix*, not as a link —
the refresh cookie's ``path`` and the ``Cache-Control`` prefix in ``app.main``.

**What it cannot see**: a URL assembled from separate variables (no literal
carries ``/api/v1/``), and a link relative to a mount (``ctx.api_link("/x")``,
whose argument has no ``/api/v1/``).
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

#: ``(module relative to app/, literal)`` pairs that are prefixes, not links.
_PREFIXES: frozenset[tuple[str, str]] = frozenset(
    {
        ("api/v1/auth/router.py", "/api/v1/auth"),  # refresh-cookie path
        ("main.py", "/api/v1/"),  # Cache-Control: no-store prefix
    }
)

_PLACEHOLDER = re.compile(r"\{[^}]*\}")
_API_PATH = re.compile(r"/api/v1/[^\s\"'`]*")
_MAX_DEPTH = 10


def _normalise(path: str) -> str:
    return _PLACEHOLDER.sub("{}", path.split("?", 1)[0].split("#", 1)[0]).rstrip("/")


def _skipped_nodes(tree: ast.AST) -> set[int]:
    skipped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            skipped.add(id(node.value))
        if isinstance(node, ast.JoinedStr):
            skipped.update(id(value) for value in node.values)
    return skipped


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in node.values)  # type: ignore[misc]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def issued_api_paths(sources: Iterable[tuple[str, str]]) -> Iterator[tuple[str, int, str]]:
    """``(module, line, path)`` for every link-shaped ``/api/v1/`` literal in *sources*."""
    for module, source in sources:
        tree = ast.parse(source)
        skipped = _skipped_nodes(tree)
        for node in ast.walk(tree):
            if id(node) in skipped:
                continue
            text = _literal_text(node)
            if not text or "\n" in text or " " in text.strip():
                continue
            match = _API_PATH.search(text)
            if match:
                yield module, getattr(node, "lineno", 0), match.group(0)


def _route_paths(routes: Iterable[Any], prefix: str = "", depth: int = 0) -> Iterator[str]:
    assert depth < _MAX_DEPTH, "router graph deeper than expected — a cycle?"
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _route_paths(original.routes, prefix + route.include_context.prefix, depth + 1)
        elif hasattr(route, "path"):
            yield prefix + route.path


def _template_pattern(template: str) -> re.Pattern[str]:
    return re.compile(re.escape(template).replace(r"\{\}", "[^/]+"))


def unserved(paths: Iterable[tuple[str, int, str]], templates: set[str]) -> list[tuple[str, int, str]]:
    patterns = [_template_pattern(t) for t in templates]
    missing = []
    for module, line, raw in paths:
        if (module, raw) in _PREFIXES:
            continue
        path = _normalise(raw)
        if path in templates or any(p.fullmatch(path) for p in patterns):
            continue
        if path.endswith("{}") and any(t.startswith(path[:-2]) for t in templates):
            continue
        missing.append((module, line, raw))
    return missing


@pytest.fixture(scope="module")
def templates() -> set[str]:
    from fastapi import APIRouter

    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.api.v1.router import LIGHT_ONLY_ROUTERS
        from app.main import app

    found = {_normalise(p) for p in _route_paths(app.routes)}
    light = APIRouter(prefix="/api/v1")
    for router in LIGHT_ONLY_ROUTERS:
        light.include_router(router)
    found |= {_normalise(p) for p in _route_paths(light.routes)}
    return found


@pytest.fixture(scope="module")
def issued() -> list[tuple[str, int, str]]:
    sources = (
        (str(p.relative_to(APP)), p.read_text(encoding="utf-8"))
        for p in sorted(APP.rglob("*.py"))
        if "__pycache__" not in p.parts
    )
    return list(issued_api_paths(sources))


def test_the_walk_finds_the_links_it_was_written_for(issued: list[tuple[str, int, str]]) -> None:
    """Non-vacuity: the photo URLs the attachment routes write are seen (the feed URL is checked by value below)."""
    seen = {_normalise(path) for _module, _line, path in issued}

    assert "/api/v1/t/{}/attachments/{}" in seen
    assert len(issued) >= 20


def test_every_issued_api_link_reaches_a_route(issued: list[tuple[str, int, str]], templates: set[str]) -> None:
    missing = unserved(issued, templates)

    assert missing == [], (
        "These /api/v1 URLs are written into responses but no mounted route answers them:\n"
        + "\n".join(f"  app/{module}:{line}  {path}" for module, line, path in missing)
    )


def test_the_detector_reports_a_link_to_a_missing_route(templates: set[str]) -> None:
    """Falsification: the two shapes of the defect are caught, a served link is not."""
    source = (
        "def link(slug, key, token):\n"
        "    return f'/api/v1/calendar/feeds/{key}/feed.icz?token={token}'\n"
        "GLOSSARY = {'url': '/api/v1/glossary/terms'}\n"
        "SERVED = f'/api/v1/t/{slug}/attachments/{key}'\n"
    )
    found = list(issued_api_paths([("fixture.py", source)]))

    assert [path for _m, _l, path in unserved(found, templates)] == [
        "/api/v1/calendar/feeds/{}/feed.icz?token={}",
        "/api/v1/glossary/terms",
    ]


def test_the_feed_subscription_url_reaches_its_route(templates: set[str]) -> None:
    """The URL the feed routes issue (#2226) — built at runtime, so checked by value."""
    from app.api.v1.calendar.tenant_router import feed_subscription_url

    url = feed_subscription_url("https://kamerplanter.example", "feed-1", "tok")
    path = url.removeprefix("https://kamerplanter.example")

    assert unserved([("calendar", 0, path)], templates) == []
