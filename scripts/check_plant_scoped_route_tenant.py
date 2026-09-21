#!/usr/bin/env python3
"""Every route that takes a TENANT-OWNABLE key from its path must scope it (#1619).

The defect
----------
``GET /t/{slug}/ipm/plants/{plant_key}/karenz`` (and ``/harvest-safety``,
``/treatment-applications``, ``/inspections``, ``/inspection-schedule``) took
``plant_key`` from the path and handed it to a by-key lookup. Three of the five
did not read ``ctx`` at all. A member of tenant A read tenant B's active
substance, treatment name, Karenz window and inspection notes with an HTTP 200.

Why a guard and not five fixes
------------------------------
The *write* routes beside them were already correct — they verify the plant at
the repository (#517) — so the whole asymmetry was invisible in review. That is
the #948 shape this repository keeps paying for: two of four sibling routes
repaired, the other two open for months. Repairing the five reads leaves the
sixth, added next month, exactly as open.

So this hook does not check "are the five routes fixed". It enumerates the
CLASS:

    every FastAPI route under ``src/backend/app/api/`` whose URL carries a
    NON-TERMINAL path parameter naming a tenant-ownable entity

and requires, for each such parameter, one of:

  (a) the handler reaches the parameter through at least one call expression
      that ALSO carries a tenant argument (``tenant_key=…``, a positional
      ``ctx.tenant_key``, …) — measured on the AST's call arguments;
  (b) the route, or the ``APIRouter`` it is declared on, carries an
      ownership-verifying dependency (:data:`VERIFYING_DEPENDENCIES`);
  (c) an explicit ``# tenant-scope-ok: <reason>`` marker in the contiguous
      comment block directly above the route decorator, or between the
      decorator and the handler's ``def``.

"Tenant-ownable" is derived from ``OWNERSHIP_VERIFIABLE_COLLECTIONS`` — the same
allowlist ``verify_entity_ownership`` gates on — via :data:`OWNABLE_PARAMS`, not
from a list of today's route literals. A new tenant-owned entity is added in one
place and every route that takes its key inherits the requirement.

A comment cannot satisfy it
---------------------------
(a) and (b) are read off the **AST**, where comments do not exist. A handler
whose only mention of the tenant is ``# scoped via ctx.tenant_key`` in a comment
is flagged exactly as if the comment were absent — the vacuum trap of PR #1545,
#1608 and #1610. Only the deliberate ``# tenant-scope-ok: <reason>`` escape
hatch is read from source text, and it must name a reason.

Known blind spots (the honest residue)
--------------------------------------
This is a static, single-file reader. It CANNOT resolve:

* a handler that delegates to a module-level helper which does the scoping
  (``_load(plant_key, ctx)`` reads as scoped only because ``ctx`` is an
  argument; ``_load(plant_key)`` reads as unscoped and is reported);
* a service method whose ``tenant_key`` has a default filled in elsewhere;
* a router mounted with ``include_router(..., dependencies=[...])`` in another
  module;
* whether a tenant token nested inside an argument expression is actually used
  for the lookup — ``service.create(plant_key, Model(tenant_key=ctx.tenant_key))``
  counts as carrying the tenant, because it does travel, but the callee might
  still look the plant up by key alone.

Spellings of the same thing it does NOT match, stated rather than assumed: a
tenant resolved inside the callee from a default; a parameter renamed between
path and handler; a route registered by ``router.add_api_route(...)`` instead of
a decorator; a URL built by string concatenation rather than a literal.

It therefore over-reports rather than under-reports: a false green needs a
tenant token in the call arguments that is not actually a tenant, a false red
needs only indirection. The marker is how a reviewed false red is retired, with
the reason recorded at the site instead of as a count nobody can argue with.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

API_ROOT = pathlib.Path("src/backend/app/api")
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

#: Path-parameter names that denote a key of an ownership-verifiable collection
#: (``app/data_access/arango/tenant_ownership.OWNERSHIP_VERIFIABLE_COLLECTIONS``).
#: Keep in step with that frozenset — a new tenant-ownable entity belongs here.
OWNABLE_PARAMS: frozenset[str] = frozenset(
    {
        "plant_key",  # plant_instances
        "run_key",  # planting_runs
        "observation_key",  # harvest_observations
        "fertilizer_key",  # fertilizers
        "tank_key",  # tanks
        "equipment_key",  # equipment
        "cultivar_key",  # cultivars
    }
)

#: Dependencies that resolve the entity and refuse a foreign one themselves.
VERIFYING_DEPENDENCIES: frozenset[str] = frozenset({"require_owned_plant"})

MARKER_RE = re.compile(r"#\s*tenant-scope-ok:\s*(\S.*)")


def _route_decorators(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[ast.Call, str, str]]:
    out = []
    for dec in fn.decorator_list:
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr in HTTP_METHODS
            and dec.args
            and isinstance(dec.args[0], ast.Constant)
            and isinstance(dec.args[0].value, str)
        ):
            out.append((dec, dec.func.attr.upper(), dec.args[0].value))
    return out


def _non_terminal_params(url: str) -> list[str]:
    """Path parameters that are followed by at least one further segment.

    The terminal key of ``/tanks/{key}`` is the resource the handler is *about*;
    the repository read for it is scoped or it is not, and that is a different
    (already-guarded) question. A NON-terminal key is a parent whose ownership
    decides whether the child rows may be seen at all — the #1619 shape.
    """
    segments = [s for s in url.split("/") if s]
    return [
        match.group(1)
        for segment in segments[:-1]
        if (match := re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", segment))
    ]


def _call_carries_tenant(call: ast.Call) -> bool:
    for keyword in call.keywords:
        if keyword.arg is None:
            return True  # ``**kwargs`` — unresolvable, never claimed as unsafe
        if "tenant" in keyword.arg:
            return True
    return any("tenant" in ast.dump(arg).lower() for arg in call.args)


def _uses_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id == name for child in ast.walk(node)
    )


def _router_level_dependencies(tree: ast.Module) -> set[str]:
    """Names inside any ``APIRouter(dependencies=[...])`` in this module."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "APIRouter"
        ):
            for keyword in node.keywords:
                if keyword.arg == "dependencies":
                    for child in ast.walk(keyword.value):
                        if isinstance(child, ast.Name):
                            names.add(child.id)
    return names


def _marker_lines(source: str) -> dict[int, str]:
    return {
        number: match.group(1).strip()
        for number, line in enumerate(source.splitlines(), start=1)
        if (match := MARKER_RE.search(line))
    }


def _marker_for(
    markers: dict[int, str],
    source_lines: list[str],
    decorator_line: int,
    def_line: int,
) -> str | None:
    """Find the marker for one route.

    Looked for between the decorator and the ``def`` (a decorator may span
    several lines), and in the contiguous comment block immediately above the
    decorator — where a reviewer naturally writes the reason, next to the
    decorator's own leading ``@``. The upward walk stops at the first line that
    is not a comment, so a marker belonging to an earlier route cannot drift
    down onto this one.
    """
    for line in range(decorator_line, def_line + 1):
        if line in markers:
            return markers[line]
    # ``@`` sits on the line before the decorator expression FastAPI parses.
    line = decorator_line - 1
    while line >= 1 and source_lines[line - 1].lstrip().startswith(("#", "@")):
        if line in markers:
            return markers[line]
        line -= 1
    return None


def check(root: pathlib.Path) -> tuple[list[str], list[str]]:
    violations: list[str] = []
    exempted: list[str] = []

    for path in sorted(root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        source_lines = source.splitlines()
        router_deps = _router_level_dependencies(tree)
        markers = _marker_lines(source)

        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            signature_deps = ast.dump(fn.args)
            covered_by_dependency = any(
                dep in router_deps or dep in signature_deps
                for dep in VERIFYING_DEPENDENCIES
            )

            for decorator, method, url in _route_decorators(fn):
                marker = _marker_for(markers, source_lines, decorator.lineno, fn.lineno)

                for param in _non_terminal_params(url):
                    if param not in OWNABLE_PARAMS:
                        continue
                    site = f"{path}:{fn.lineno} {method} {url} — parent '{param}'"
                    if covered_by_dependency:
                        continue
                    scoped = any(
                        isinstance(node, ast.Call)
                        and _uses_name(node, param)
                        and _call_carries_tenant(node)
                        for node in ast.walk(fn)
                    )
                    if scoped:
                        continue
                    if marker:
                        exempted.append(f"{site} [exempt: {marker}]")
                        continue
                    violations.append(site)

    return violations, exempted


def main() -> int:
    if not API_ROOT.is_dir():
        print(
            f"ERROR: {API_ROOT} not found — run from the repository root.",
            file=sys.stderr,
        )
        return 2

    violations, exempted = check(API_ROOT)
    for site in exempted:
        print(f"  ok   {site}")
    if violations:
        print(
            "\nA route takes a tenant-ownable key from its path and never verifies it\n"
            "against the caller's tenant (#1619). Pass the tenant into the lookup, mount\n"
            "an ownership dependency, or record why the site is safe with a\n"
            "`# tenant-scope-ok: <reason>` marker above the route decorator.\n",
            file=sys.stderr,
        )
        for site in violations:
            print(f"  FAIL {site}", file=sys.stderr)
        return 1
    print(f"tenant-scope: {len(exempted)} exempted site(s), no unscoped parent key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
