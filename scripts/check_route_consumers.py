#!/usr/bin/env python3
"""Name every mounted API operation that no consumer in this tree reaches.

Invoked directly::

    python3 scripts/check_route_consumers.py              # report the candidates
    python3 scripts/check_route_consumers.py --inventory  # full table, never fails
    python3 scripts/check_route_consumers.py --json       # machine-readable

**The reverse join of** ``scripts/check_frontend_calls_served.py`` **(#1478).**
That sibling asks whether every frontend call reaches a route. This one asks the
other direction: whether every route the app mounts is reached by anything at
all. #1416 was one instance — ``POST /me/providers/{slug}/link`` was mounted,
documented and gated, and nothing in the repository ever called it; it was
removed. Running the join instead of fixing its one instance turns up **175 of
797** mounted ``/api/v1`` operations with no textual consumer anywhere.

**Reproducing #1478's figure, and the one that differs.** The script #1478 was
measured with never landed in the tree, so this is a re-implementation and the
agreement is what has to be shown rather than assumed. Two operands reproduce
*exactly*: 797 mounted ``/api/v1`` operations, and 598 resolved frontend endpoint
calls. So do the write clusters the issue names — propagation 10, actuators 8,
planting-runs 5, species / privacy / phase-control-profiles / mcp / enrichment /
aquaponics 4 each — and all four of its spot-checked true positives. The
candidate total is **175 against the issue's 176** (admin 9 against 8, inventree
3 against 4). The textual surfaces are where the two differ: this scan finds 1650
/ 194 / 63 distinct path literals in the frontend / e2e / MCP trees against the
issue's 3021 / 256 / 80, which are counts of literal *sites* rather than of
distinct paths. That the two joins land within one operation of each other over
operands that differ by a factor of two is the evidence the difference is not
decision-bearing. The number is not a constant to be defended: the floor that
produces it is pinned in the tests from both sides, and moving it to two or four
segments moves the total to 172 or 178.

**This is an inventory, not a verdict.** A zero here means *this tree* holds no
reference to the path — it does not mean the route is dead. Home Assistant,
Grafana, external MCP clients and paired devices consume routes by design and
leave no string in this repository. That is what
``scripts/route_consumer_exemptions.yaml`` is for: an exemption carries a reason,
so the difference between "consumed elsewhere" and "nobody noticed it is dead"
stops being a judgement someone has to re-make every time the number is read.
Deliberately **not** wired into CI: promoting it to a gate is the triage
decision #1478 asks for, not a side effect of landing the instrument.

**The four surfaces counted as consumers.**

1. ``src/frontend/src/api/endpoints/*.ts`` — resolved through the sibling's own
   extractor, so an operation matched here is matched on **method + path +
   client scope**, the same three-way join the sibling enforces. This is the only
   exact surface.
2. Every string literal under ``src/frontend/src`` — the endpoint modules are
   not the only place a path is written (MSW handlers, tests, hard-coded fetch).
3. Every string literal under ``tests/e2e``.
4. Every string literal under ``src/backend/app/mcp_server`` — the MCP tools
   address the API by path, and the tool surface is a first-class consumer
   (REQ-033).

**How a reference is matched to an operation, said out loud.** Both sides are
normalised — ``${…}`` and ``{…}`` collapse to ``{}``, the query string is
dropped, the mount prefix (``/api/v1``, ``/api/v1/t/{}``) is stripped — and the
reference must then be a **segment-aligned suffix** of the operation's
remainder, carrying at least ``min(3, len(remainder))`` segments. Three is the
floor because a shorter suffix matches indiscriminately: ``/{}`` is a suffix of
roughly half the route table, and a join that matches everything reports a clean
result over nothing. Where the operation itself is shorter than three segments
(``/species``, ``/fertilizers``) the whole remainder is required instead, so a
short route is not made unreachable by its own length.

**Two ways this join is deliberately generous, and why.** Surfaces 2–4 are
matched on the **path only**, never the method: a path written anywhere counts
every method mounted on it as consumed. And a frontend *router* path that
happens to spell an API path (``/plants/{}``) counts too. Both widen the
consumer side, which can only ever *shrink* the candidate list. That is the
right direction for an instrument whose output a human triages: everything it
reports genuinely has no textual trace, so a name on the list is worth reading.
It is the wrong direction for a gate, which is the second reason this is not one
yet.

**The mounting trap, inherited.** ``include_router`` does not flatten. Read
``app.routes`` directly and you find six routes instead of ~800, and every
number below becomes fiction. The wrappers FastAPI leaves behind are
``_IncludedRouter`` objects carrying **no** ``path`` attribute at all — their
prefix lives in ``include_context.prefix``. :func:`collect_operations` walks it
the way the sibling's :func:`collect_mounted_routes` does, and
``tests/unit/test_route_consumers_check.py`` asserts the two walks return the
**same** ``(method, path)`` set, so this second walk cannot drift away from the
one that is already trusted.

Traces to #1478 / #1416 (no TC-ID: a source-tree instrument is not a
user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The backend package root, prepended to ``sys.path`` before importing the app.
DEFAULT_BACKEND_DIR = "src/backend"
#: Where the exemption registry lives.
DEFAULT_EXEMPTIONS = "scripts/route_consumer_exemptions.yaml"

#: The API prefix every mounted operation carries.
API_PREFIX = "/api/v1"
#: What the tenant-scoped routers additionally carry, slug normalised.
TENANT_PREFIX = "/api/v1/t/{}"

#: Consumer surfaces: label -> (directory, glob patterns).
CONSUMER_SURFACES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("frontend", "src/frontend/src", ("**/*.ts", "**/*.tsx")),
    ("e2e", "tests/e2e", ("**/*.py",)),
    ("mcp", "src/backend/app/mcp_server", ("**/*.py",)),
)
#: The surface the sibling extractor owns, matched exactly rather than textually.
SURFACE_ENDPOINTS = "endpoints"
#: Where that surface lives.
DEFAULT_ENDPOINT_DIR = "src/frontend/src/api/endpoints"

#: The minimum number of segments a textual reference must carry to count.
MIN_SUFFIX_SEGMENTS = 3

#: A quoted string literal in TypeScript or Python, backticks included.
_LITERAL = re.compile(r"[\"'`]([^\"'`\n]*)[\"'`]")
#: Any interpolation — ``${expr}`` (TS), ``{expr}`` (Python f-string, OpenAPI).
_INTERPOLATION = re.compile(r"\$?\{[^{}]*\}")
#: A path parameter on the backend side.
_PATH_PARAM = re.compile(r"\{[^{}]*\}")
#: A path-shaped literal: leading slash, no whitespace, nothing file-like.
_PATH_SHAPED = re.compile(r"^/[A-Za-z0-9_{}$/.:-]*$")

_HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


class RouteConsumerCheckError(RuntimeError):
    """The check could not run at all — a broken operand, not a finding."""


@dataclass(frozen=True, order=True)
class Operation:
    """One mounted ``(method, path)``, with the module and gate that own it."""

    method: str
    path: str
    module: str = ""
    gate: str = ""

    def describe(self) -> str:
        return f"{self.method} {self.path}"


@dataclass(frozen=True, order=True)
class Reference:
    """One place in the tree that names an API path."""

    path: str
    surface: str
    location: str

    def describe(self) -> str:
        return f"{self.path} [{self.surface}] ({self.location})"


@dataclass(frozen=True)
class Exemption:
    """A declared reason an operation has no consumer in this tree."""

    method: str
    path: str
    reason: str


@dataclass
class Finding:
    """An operation no surface reaches and no exemption covers."""

    operation: Operation
    consumers: list[Reference] = field(default_factory=list)


def _normalise(raw: str) -> str | None:
    """Turn a raw literal into a comparable path, or ``None`` if it is not one.

    Interpolations of either dialect collapse to ``{}``, the query string and
    fragment are dropped, and a trailing slash is removed. Returns ``None`` for
    anything that is not path-shaped, which is most of what a string literal
    scan picks up.
    """
    text = raw.strip()
    if not text.startswith("/"):
        return None
    text = _INTERPOLATION.sub("{}", text)
    text = text.split("?")[0].split("#")[0]
    if not _PATH_SHAPED.match(text):
        return None
    text = _PATH_PARAM.sub("{}", text)
    trimmed = text.rstrip("/")
    return trimmed or "/"


def _segments(path: str) -> tuple[str, ...]:
    return tuple(part for part in path.split("/") if part)


def remainder(path: str) -> tuple[str, ...]:
    """The path's segments with any mount prefix stripped.

    ``/api/v1/t/{}/plants/{}`` and ``/plants/{}`` both reduce to
    ``('plants', '{}')``, which is what lets a reference written relative to the
    axios ``baseURL`` join a route written absolutely.
    """
    parts = list(_segments(path))
    if parts[:2] == ["api", "v1"]:
        parts = parts[2:]
    if parts[:2] == ["t", "{}"]:
        parts = parts[2:]
    return tuple(parts)


def matches(operation_path: str, reference_path: str) -> bool:
    """Whether *reference_path* addresses *operation_path*.

    Segment-aligned suffix match on the two remainders, requiring at least
    :data:`MIN_SUFFIX_SEGMENTS` segments — or the whole remainder where the
    operation is shorter than that, so ``/species`` is not made unmatchable by
    its own length.
    """
    target = remainder(operation_path)
    candidate = remainder(reference_path)
    if not target or not candidate:
        return False
    required = min(MIN_SUFFIX_SEGMENTS, len(target))
    if len(candidate) < required or len(candidate) > len(target):
        return False
    return target[-len(candidate) :] == candidate


def _iter_files(root: Path, patterns: Iterable[str]) -> Iterator[Path]:
    for pattern in patterns:
        yield from sorted(root.glob(pattern))


def collect_references(
    repo_root: Path,
    surfaces: tuple[tuple[str, str, tuple[str, ...]], ...] = CONSUMER_SURFACES,
) -> list[Reference]:
    """Every path-shaped string literal on the textual consumer surfaces.

    Args:
        repo_root: The checkout root.
        surfaces: ``(label, directory, globs)`` triples to scan. Overridden only
            by the tests, which drive the extraction over a constructed tree.

    Returns:
        The references, deduplicated per (path, surface, file), sorted.

    Raises:
        RouteConsumerCheckError: If a declared surface directory is missing —
            a surface that silently scans nothing is the failure this whole
            instrument exists to catch.
    """
    seen: set[Reference] = set()
    for surface, relative, patterns in surfaces:
        root = repo_root / relative
        if not root.is_dir():
            msg = f"consumer surface {relative} is not a directory"
            raise RouteConsumerCheckError(msg)
        for file in _iter_files(root, patterns):
            try:
                source = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:  # pragma: no cover — defensive
                continue
            location = file.relative_to(repo_root).as_posix()
            for literal in _LITERAL.findall(source):
                path = _normalise(literal)
                if path is not None:
                    seen.add(Reference(path=path, surface=surface, location=location))
    return sorted(seen)


def collect_endpoint_references(endpoint_dir: Path) -> list[Reference]:
    """The frontend endpoint calls, resolved by the sibling's own extractor.

    This is the one surface matched on method **and** scope rather than on text,
    because the sibling already owns that resolution and a second copy of it
    would drift. Returns references carrying the fully-prefixed path, so the
    ordinary suffix join applies to them unchanged.

    Raises:
        RouteConsumerCheckError: If the sibling script cannot be loaded.
    """
    sibling = _load_sibling()
    try:
        calls = sibling.collect_frontend_calls(endpoint_dir)
    except sibling.FrontendCallCheckError as exc:
        raise RouteConsumerCheckError(str(exc)) from exc
    references: list[Reference] = []
    for call in calls:
        prefix = TENANT_PREFIX if call.scope == sibling.SCOPE_TENANT else API_PREFIX
        references.append(
            Reference(
                path=prefix + call.path,
                surface=SURFACE_ENDPOINTS,
                location=f"{call.module}:{call.line}",
            )
        )
    return sorted(set(references))


def _load_sibling() -> Any:
    """Import ``check_frontend_calls_served`` from the same ``scripts/`` dir."""
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import check_frontend_calls_served
    except ImportError as exc:  # pragma: no cover — only on a partial checkout
        msg = f"scripts/check_frontend_calls_served.py is not importable ({exc})"
        raise RouteConsumerCheckError(msg) from exc
    return check_frontend_calls_served


def _gate_of(route: Any) -> str:
    """The auth dependencies a route carries, as a comma-joined label.

    Every guard factory in ``app/common/auth.py`` returns a closure literally
    named ``_check``, so the readable name is the factory — which lives in the
    closure's ``__qualname__``, not its ``__name__``. Reading ``__name__`` here
    would label eight different gates identically.
    """
    names: list[str] = []
    for dependency in getattr(getattr(route, "dependant", None), "dependencies", []):
        call = getattr(dependency, "call", None)
        if call is None:
            continue
        qualname = getattr(call, "__qualname__", "") or getattr(call, "__name__", "")
        name = qualname.split(".<locals>.")[0].rsplit(".", 1)[-1]
        if name.startswith(("require_", "get_current_", "get_active_")):
            names.append(name)
    return ", ".join(dict.fromkeys(names)) or "-"


def collect_operations(app: Any) -> list[Operation]:
    """Every ``(method, path)`` the app mounts, with its module and gate.

    The walk mirrors the sibling's :func:`collect_mounted_routes` — including the
    ``_IncludedRouter`` / ``include_context.prefix`` handling that walk exists to
    get right — but keeps the route object so the module and gate can be read
    off it. The unit test asserts both walks yield the same operation set.

    Args:
        app: The mounted FastAPI application.

    Returns:
        The operations, sorted, restricted to those under ``/api/v1``.
    """
    found: dict[tuple[str, str], Operation] = {}

    def walk(router: Any, prefix: str = "") -> None:
        for route in getattr(router, "routes", []):
            included = getattr(route, "original_router", None)
            if included is not None:
                context = getattr(route, "include_context", None)
                walk(included, prefix + (getattr(context, "prefix", "") or ""))
                continue
            raw = prefix + (getattr(route, "path", "") or "")
            path = _PATH_PARAM.sub("{}", raw)
            endpoint = getattr(route, "endpoint", None)
            if endpoint is not None:
                module = getattr(endpoint, "__module__", "") or ""
                gate = _gate_of(route)
                for method in getattr(route, "methods", ()) or ():
                    if method in _HTTP_METHODS:
                        found.setdefault(
                            (method, path),
                            Operation(
                                method=method, path=path, module=module, gate=gate
                            ),
                        )
            sub = getattr(route, "app", None)
            if sub is not None and hasattr(sub, "routes"):
                walk(sub, raw)

    walk(app)
    return sorted(
        operation
        for operation in found.values()
        if operation.path.startswith(API_PREFIX)
    )


def load_exemptions(path: Path) -> list[Exemption]:
    """Read the exemption registry.

    Args:
        path: The registry file. A missing file is an empty registry.

    Returns:
        The declared exemptions.

    Raises:
        RouteConsumerCheckError: If the file is malformed or an entry omits its
            reason. An exemption without a stated reason is the thing this
            registry exists to prevent.
    """
    if not path.is_file():
        return []
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover — PyYAML is a backend dep
        msg = f"PyYAML is required to read {path} ({exc})"
        raise RouteConsumerCheckError(msg) from exc

    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        msg = f"{path} is not valid YAML ({exc})"
        raise RouteConsumerCheckError(msg) from exc
    if not isinstance(document, dict):
        msg = f"{path} must hold a mapping with an 'exemptions' key"
        raise RouteConsumerCheckError(msg)

    entries = document.get("exemptions") or []
    if not isinstance(entries, list):
        msg = f"{path}: 'exemptions' must be a list"
        raise RouteConsumerCheckError(msg)

    exemptions: list[Exemption] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            msg = f"{path}: exemption #{index + 1} is not a mapping"
            raise RouteConsumerCheckError(msg)
        method = str(entry.get("method", "")).strip().upper()
        route_path = str(entry.get("path", "")).strip()
        reason = str(entry.get("reason", "")).strip()
        if method not in _HTTP_METHODS:
            msg = f"{path}: exemption #{index + 1} has no usable HTTP method"
            raise RouteConsumerCheckError(msg)
        if not route_path.startswith("/"):
            msg = f"{path}: exemption #{index + 1} has no absolute path"
            raise RouteConsumerCheckError(msg)
        if not reason:
            msg = (
                f"{path}: exemption #{index + 1} ({method} {route_path}) states no "
                "reason; an exemption without one is indistinguishable from an oversight"
            )
            raise RouteConsumerCheckError(msg)
        exemptions.append(
            Exemption(
                method=method, path=_PATH_PARAM.sub("{}", route_path), reason=reason
            )
        )
    return exemptions


def find_consumers(
    operations: list[Operation], references: list[Reference]
) -> dict[Operation, list[Reference]]:
    """Join each operation onto every reference that addresses its path."""
    by_remainder: dict[tuple[str, ...], list[Reference]] = {}
    for reference in references:
        by_remainder.setdefault(remainder(reference.path), []).append(reference)

    joined: dict[Operation, list[Reference]] = {}
    for operation in operations:
        target = remainder(operation.path)
        hits: list[Reference] = []
        if target:
            required = min(MIN_SUFFIX_SEGMENTS, len(target))
            for length in range(required, len(target) + 1):
                hits.extend(by_remainder.get(target[-length:], ()))
        joined[operation] = sorted(set(hits))
    return joined


def find_unconsumed(
    joined: dict[Operation, list[Reference]], exemptions: list[Exemption]
) -> list[Finding]:
    """The operations with no consumer that no exemption covers."""
    exempt = {(item.method, item.path) for item in exemptions}
    return [
        Finding(operation=operation, consumers=consumers)
        for operation, consumers in sorted(joined.items())
        if not consumers and (operation.method, operation.path) not in exempt
    ]


def stale_exemptions(
    joined: dict[Operation, list[Reference]], exemptions: list[Exemption]
) -> list[Exemption]:
    """Exemptions that name an operation which is gone or has a consumer now.

    A registry nobody prunes is a registry that hides the next dead route, so a
    stale entry is a finding rather than a comment.
    """
    consumed = {
        (operation.method, operation.path)
        for operation, consumers in joined.items()
        if consumers
    }
    mounted = {(operation.method, operation.path) for operation in joined}
    return [
        item
        for item in exemptions
        if (item.method, item.path) not in mounted
        or (item.method, item.path) in consumed
    ]


def load_app(backend_dir: Path) -> Any:
    """Import the mounted FastAPI application from *backend_dir*.

    Raises:
        RouteConsumerCheckError: If the backend package is not importable.
    """
    sibling = _load_sibling()
    try:
        return sibling.load_app(backend_dir)
    except sibling.FrontendCallCheckError as exc:
        raise RouteConsumerCheckError(str(exc)) from exc


def _table(rows: list[tuple[str, str, str, str]]) -> str:
    headers = ("Route", "Module", "Gate", "Consumers")
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        if rows
        else len(headers[index])
        for index in range(4)
    ]
    lines = [
        "  ".join(headers[index].ljust(widths[index]) for index in range(4)).rstrip(),
        "  ".join("-" * widths[index] for index in range(4)),
    ]
    lines.extend(
        "  ".join(row[index].ljust(widths[index]) for index in range(4)).rstrip()
        for row in rows
    )
    return "\n".join(lines)


def report(
    joined: dict[Operation, list[Reference]],
    findings: list[Finding],
    stale: list[Exemption],
    exemptions: list[Exemption],
    *,
    inventory: bool = False,
    as_json: bool = False,
) -> int:
    """Print the outcome and return the process exit code."""
    if as_json:
        payload = {
            "operations": len(joined),
            "exemptions": [
                {"method": e.method, "path": e.path, "reason": e.reason}
                for e in exemptions
            ],
            "stale_exemptions": [
                {"method": e.method, "path": e.path, "reason": e.reason} for e in stale
            ],
            "unconsumed": [
                {
                    "method": f.operation.method,
                    "path": f.operation.path,
                    "module": f.operation.module,
                    "gate": f.operation.gate,
                    "consumers": 0,
                }
                for f in findings
            ],
            "inventory": [
                {
                    "method": operation.method,
                    "path": operation.path,
                    "module": operation.module,
                    "gate": operation.gate,
                    "consumers": len(consumers),
                    "surfaces": sorted({c.surface for c in consumers}),
                }
                for operation, consumers in sorted(joined.items())
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK if inventory else _code(findings, stale)

    if inventory:
        rows = [
            (
                operation.describe(),
                operation.module,
                operation.gate,
                str(len(consumers)),
            )
            for operation, consumers in sorted(joined.items())
        ]
        print(_table(rows))
        print(
            f"\ncheck_route_consumers: {len(joined)} mounted operations, "
            f"{len(findings)} without a consumer, {len(exemptions)} exempted."
        )
        return EXIT_OK

    if stale:
        print(
            f"check_route_consumers: {len(stale)} stale exemption(s) — the operation is "
            "gone or has a consumer again:",
            file=sys.stderr,
        )
        for item in stale:
            print(f"  {item.method} {item.path}: {item.reason}", file=sys.stderr)

    if findings:
        rows = [
            (
                finding.operation.describe(),
                finding.operation.module,
                finding.operation.gate,
                "0",
            )
            for finding in findings
        ]
        print(
            f"check_route_consumers: {len(findings)} of {len(joined)} mounted operations "
            "are reached by no consumer in the frontend, tests/e2e or the MCP server:",
            file=sys.stderr,
        )
        print(_table(rows), file=sys.stderr)
        print(
            "\nEach is one of three things (#1478): consumed outside this tree — declare "
            f"it in {DEFAULT_EXEMPTIONS} with a reason; a product gap — the consumer is "
            "missing and should exist; or dead — remove it with an absence test.",
            file=sys.stderr,
        )

    if not findings and not stale:
        print(
            f"check_route_consumers: {len(joined)} mounted operations, every one reached "
            f"by a consumer or covered by one of {len(exemptions)} exemptions."
        )
    return _code(findings, stale)


def _code(findings: list[Finding], stale: list[Exemption]) -> int:
    return EXIT_FINDINGS if (findings or stale) else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--backend-dir",
        metavar="PATH",
        default=None,
        help=f"backend package root to import the app from (default: {DEFAULT_BACKEND_DIR})",
    )
    parser.add_argument(
        "--endpoint-dir",
        metavar="PATH",
        default=None,
        help=f"frontend endpoint modules to resolve exactly (default: {DEFAULT_ENDPOINT_DIR})",
    )
    parser.add_argument(
        "--exemptions",
        metavar="PATH",
        default=None,
        help=f"exemption registry (default: {DEFAULT_EXEMPTIONS})",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="print the full table and always exit 0 — the phase-0 instrument",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    backend_dir = _resolve_path(args.backend_dir, DEFAULT_BACKEND_DIR)
    endpoint_dir = _resolve_path(args.endpoint_dir, DEFAULT_ENDPOINT_DIR)
    exemption_file = _resolve_path(args.exemptions, DEFAULT_EXEMPTIONS)

    try:
        operations = collect_operations(load_app(backend_dir))
        references = collect_references(REPO_ROOT)
        references.extend(collect_endpoint_references(endpoint_dir))
        exemptions = load_exemptions(exemption_file)
    except RouteConsumerCheckError as exc:
        print(f"check_route_consumers: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if not operations:
        print(
            "check_route_consumers: the app mounted no operations — a broken scan, "
            "never a pass",
            file=sys.stderr,
        )
        return EXIT_USAGE

    joined = find_consumers(operations, references)
    return report(
        joined,
        find_unconsumed(joined, exemptions),
        stale_exemptions(joined, exemptions),
        exemptions,
        inventory=args.inventory,
        as_json=args.json,
    )


def _resolve_path(raw: str | None, default: str) -> Path:
    value = raw or default
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
