#!/usr/bin/env python3
"""Refuse a caller-supplied ``tenant_key`` in a request body schema.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_tenant_body_field.py
    python3 scripts/check_tenant_body_field.py --list   # name every request schema
    python3 scripts/check_tenant_body_field.py --json   # machine-readable

**What it enforces.** The tenant a write belongs to is decided by the request's
*authenticated context* — ``get_current_tenant`` and the ``/api/v1/t/{slug}/``
path segment — never by the body. A body field named ``tenant_key`` invites the
handler to stamp the document with a value the caller chose, and a caller who
chooses another tenant's key has crossed the isolation boundary of REQ-024. The
rule existed in prose only: 18 of the last 200 issues sit in the tenant-isolation
cluster (#1000, #1003, #992, #952, #950, #948, #927, #901, …), and the
2026-08-08 issue-pattern audit found that "``tenant_key`` in the request body is
forbidden nowhere — and occurs".

**Why a gate and not review.** The defect is invisible in the diff that
introduces it. A schema field reads as ordinary plumbing; the damage appears one
layer down, in a service that trusts it. Every one of the eighteen issues above
was found after the fact, by someone reading a different file. A reviewer has to
know the invariant, remember it, and hold the whole request path in their head;
a parser has to match one identifier.

**Scope: request schemas only, resolved by binding — not by name.** A
``tenant_key`` on a *response* is not this defect. It tells the client which
tenant a record belongs to, which is information the client is entitled to, and
this repository ships fourteen such fields (``ActivityResponse``,
``ActuatorResponse``, ``NotificationResponse``, …). Flagging them would make the
check noise, and a noisy check is switched off. So the request set is derived,
not guessed:

1. every schema class bound as an annotated endpoint parameter under the scan
   root, unless the annotation carries a FastAPI dependency/parameter marker
   (``Depends``/``Query``/``Path``/``Header``/``Cookie``/``Security``/``File``/
   ``Form``) — those are not bodies;
2. every class whose name ends in one of :data:`REQUEST_NAME_SUFFIXES`, so a
   schema written before its router exists is covered rather than invisible;
3. transitively: the base classes of the above (Pydantic inherits fields, so a
   base is not a hiding place) and the model types of their fields (a nested
   ``list[ItemIn]`` is just as much request input as its container).

**The escape hatch.** A field may keep the name by carrying a justification on
its own line or in the comment block directly above it::

    # tenant-body-ok: legacy admin import, tenant checked against ctx before use
    tenant_key: str = ""

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer. What a reason has to establish is that the value is *not*
trusted: either it is verified against the authenticated context before any read
or write, or it is inert.

**What it deliberately does not catch.** A body field spelled differently
(``owner_tenant``, ``target_tenant_key``) or a raw ``dict`` body that carries the
key at runtime. Both are out of reach of a name match, and widening the match to
"any field containing 'tenant'" would flag ``default_tenant_key`` on the OIDC
provider config — a genuine admin setting — on the first run. Precision over
reach: this check reports only what is certainly the shape it is named after.

Standard library only, no application import, no running stack: the ``static`` CI
job is Python-only, and importing the application to answer a question that is
answerable from its source text would drag in settings and database clients.

Traces to the 2026-08-08 issue-pattern audit, measure P1.2 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the API layer lives, relative to the repository root. Only request
#: schemas are in scope, and every one of them is reachable from here.
DEFAULT_SCAN_ROOT = "src/backend/app/api"

#: The field names that may not appear on a request body. Exact matches only —
#: see the module docstring on why the match is not widened.
FORBIDDEN_FIELDS = ("tenant_key", "tenant_slug")

#: Class-name suffixes that mark a schema as request input even when no router
#: binds it yet. ``Response``/``Item``/``Detail`` are deliberately absent.
REQUEST_NAME_SUFFIXES = ("Request", "Create", "Update", "Patch", "Input", "Payload")

#: FastAPI markers that turn an annotated parameter into something other than a
#: body: a dependency, a query/path/header/cookie parameter, an upload.
NON_BODY_MARKERS = frozenset(
    {"Depends", "Query", "Path", "Header", "Cookie", "Security", "File", "Form"}
)

#: The marker that exempts a field, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption: the point of the hatch is
#: the reason, not the token.
JUSTIFICATION_MARKER = "# tenant-body-ok:"
MIN_JUSTIFICATION_CHARS = 12

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class TenantBodyCheckError(Exception):
    """A usage or environment problem — not a finding about the code."""


# ── The parsed tree ──────────────────────────────────────────────────────────


@dataclass
class ClassInfo:
    """One class definition found under the scan root."""

    module: "ModuleInfo"
    name: str
    node: ast.ClassDef

    @property
    def identity(self) -> tuple[str, str]:
        return (self.module.dotted, self.name)


@dataclass
class ModuleInfo:
    """One parsed module, with the import bindings needed to resolve names."""

    path: Path
    dotted: str
    tree: ast.Module
    source_lines: list[str]
    #: local name -> (source module, original name), from ``from X import Y``.
    imports: dict[str, tuple[str, str]] = field(default_factory=dict)
    classes: dict[str, ClassInfo] = field(default_factory=dict)


def dotted_module_name(path: Path) -> str:
    """Derive the dotted import name of *path* by walking up its packages.

    Walking up while ``__init__.py`` exists rather than slicing a fixed number
    of parents: the latter breaks silently the moment the tree is reorganised.
    """
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").is_file():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


def _resolve_relative(importer: str, module: str | None, level: int) -> str:
    """Resolve a relative ``from . import x`` against the importing module."""
    base = importer.split(".")
    # level 1 is the importing module's own package.
    trimmed = base[: max(len(base) - level, 0)]
    return ".".join([*trimmed, module]) if module else ".".join(trimmed)


def parse_module(path: Path) -> ModuleInfo:
    """Parse one source file into a :class:`ModuleInfo`."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TenantBodyCheckError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise TenantBodyCheckError(f"cannot parse {path}: {exc}") from exc

    module = ModuleInfo(
        path=path,
        dotted=dotted_module_name(path),
        tree=tree,
        source_lines=source.splitlines(),
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            origin = (
                _resolve_relative(module.dotted, node.module, node.level)
                if node.level
                else (node.module or "")
            )
            for alias in node.names:
                module.imports[alias.asname or alias.name] = (origin, alias.name)
        elif isinstance(node, ast.ClassDef):
            module.classes[node.name] = ClassInfo(module=module, name=node.name, node=node)
    return module


class SourceTree:
    """Every module under the scan root, with name resolution across them."""

    def __init__(self, modules: list[ModuleInfo]) -> None:
        self.modules = modules
        self.by_dotted = {module.dotted: module for module in modules}

    def resolve(self, module: ModuleInfo, name: str) -> ClassInfo | None:
        """Resolve *name* as seen from *module* to a class in the scanned tree.

        Returns ``None`` for anything defined outside the tree (``BaseModel``,
        a third-party type, an enum from ``app.common``) — those cannot carry a
        request field this check is about.
        """
        local = module.classes.get(name)
        if local is not None:
            return local
        imported = module.imports.get(name)
        if imported is None:
            return None
        origin, original = imported
        source = self.by_dotted.get(origin)
        if source is None:
            return None
        return source.classes.get(original)

    def is_pydantic_model(self, info: ClassInfo, _seen: frozenset[tuple[str, str]] | None = None) -> bool:
        """True when *info* derives from ``pydantic.BaseModel``.

        The base may be named directly (every schema module in this repository
        writes ``class X(BaseModel)``) or reached through another model in the
        tree.
        """
        seen = _seen or frozenset()
        if info.identity in seen:
            return False
        seen = seen | {info.identity}
        for base in info.node.bases:
            rendered = _render(base)
            if rendered.rsplit(".", 1)[-1] == "BaseModel":
                return True
            atom = rendered.split(".", 1)[0]
            parent = self.resolve(info.module, atom)
            if parent is not None and self.is_pydantic_model(parent, seen):
                return True
        return False


def _render(node: ast.expr) -> str:
    """A readable dotted rendering of a name/attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_render(node.value)}.{node.attr}"
    return "<expr>"


def _name_atoms(node: ast.expr) -> list[str]:
    """Every bare name appearing in an annotation expression."""
    return [inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name)]


def _carries_non_body_marker(annotation: ast.expr) -> bool:
    """True when the annotation binds a dependency or a non-body parameter."""
    for inner in ast.walk(annotation):
        if isinstance(inner, ast.Call) and _render(inner.func).rsplit(".", 1)[-1] in NON_BODY_MARKERS:
            return True
        if isinstance(inner, ast.Name) and inner.id in NON_BODY_MARKERS:
            return True
    return False


def _annotated_parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.expr]:
    """Every annotated parameter of *function*."""
    arguments = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    return [argument.annotation for argument in arguments if argument.annotation is not None]


# ── The request-schema set ───────────────────────────────────────────────────


def bound_request_schemas(tree: SourceTree) -> set[tuple[str, str]]:
    """Schemas bound as a request body on some endpoint under the scan root."""
    bound: set[tuple[str, str]] = set()
    for module in tree.modules:
        for function in ast.walk(module.tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for annotation in _annotated_parameters(function):
                if _carries_non_body_marker(annotation):
                    continue
                for atom in _name_atoms(annotation):
                    resolved = tree.resolve(module, atom)
                    if resolved is not None and tree.is_pydantic_model(resolved):
                        bound.add(resolved.identity)
    return bound


def named_request_schemas(tree: SourceTree) -> set[tuple[str, str]]:
    """Schemas whose class name declares them request input."""
    named: set[tuple[str, str]] = set()
    for module in tree.modules:
        for info in module.classes.values():
            if not info.name.endswith(REQUEST_NAME_SUFFIXES):
                continue
            if tree.is_pydantic_model(info):
                named.add(info.identity)
    return named


def _class_fields(info: ClassInfo) -> list[tuple[str, int]]:
    """The annotated class-body assignments of *info*, as ``(name, line)``."""
    fields: list[tuple[str, int]] = []
    for statement in info.node.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            fields.append((statement.target.id, statement.lineno))
    return fields


def expand(tree: SourceTree, seeds: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """Close *seeds* over base classes and nested field models.

    Pydantic inherits fields, so a base class carrying ``tenant_key`` is exactly
    as reachable from the wire as the subclass; and a nested model referenced
    from a field annotation is request input too.
    """
    lookup = {info.identity: info for module in tree.modules for info in module.classes.values()}
    closed: set[tuple[str, str]] = set()
    pending = [identity for identity in seeds if identity in lookup]
    while pending:
        identity = pending.pop()
        if identity in closed:
            continue
        closed.add(identity)
        info = lookup[identity]
        related: list[ast.expr] = list(info.node.bases)
        for statement in info.node.body:
            if isinstance(statement, ast.AnnAssign) and statement.annotation is not None:
                related.append(statement.annotation)
        for expression in related:
            for atom in _name_atoms(expression):
                resolved = tree.resolve(info.module, atom)
                if resolved is not None and resolved.identity not in closed and tree.is_pydantic_model(resolved):
                    pending.append(resolved.identity)
    return closed


# ── Findings ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    """One forbidden field on one request schema."""

    path: Path
    line: int
    class_name: str
    field_name: str
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the field on *line*, or ``None``.

    Accepted on the field's own line (trailing comment) and anywhere in the
    contiguous comment block directly above it — a long field declaration does
    not always leave room for a trailing comment within the line limit, and a
    field is often already introduced by a comment block.
    """
    candidates = [lines[line - 1]]
    index = line - 2
    while index >= 0 and lines[index].strip().startswith("#"):
        candidates.append(lines[index].strip())
        index -= 1
    for candidate in candidates:
        marker = candidate.find(JUSTIFICATION_MARKER)
        if marker == -1:
            continue
        reason = candidate[marker + len(JUSTIFICATION_MARKER) :].strip()
        if len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def collect(scan_root: Path) -> tuple[SourceTree, set[tuple[str, str]], list[Finding]]:
    """Parse *scan_root* and return the tree, the request set and the findings."""
    if not scan_root.exists():
        raise TenantBodyCheckError(f"scan root does not exist: {scan_root}")
    tree = SourceTree([parse_module(path) for path in sorted(scan_root.rglob("*.py"))])
    requests = expand(tree, bound_request_schemas(tree) | named_request_schemas(tree))

    lookup = {info.identity: info for module in tree.modules for info in module.classes.values()}
    findings: list[Finding] = []
    for identity in sorted(requests):
        info = lookup[identity]
        for name, line in _class_fields(info):
            if name not in FORBIDDEN_FIELDS:
                continue
            findings.append(
                Finding(
                    path=info.module.path,
                    line=line,
                    class_name=info.name,
                    field_name=name,
                    justification=justification_for(info.module.source_lines, line),
                )
            )
    findings.sort(key=lambda finding: (str(finding.path), finding.line))
    return tree, requests, findings


# ── Reporting ────────────────────────────────────────────────────────────────


def report(requests: set[tuple[str, str]], findings: list[Finding], *, list_all: bool, as_json: bool) -> int:
    """Print the outcome and return the process exit code."""
    unjustified = [finding for finding in findings if not finding.justified]
    justified = [finding for finding in findings if finding.justified]

    if as_json:
        print(
            json.dumps(
                {
                    "request_schemas": len(requests),
                    "justified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "schema": finding.class_name,
                            "field": finding.field_name,
                            "reason": finding.justification,
                        }
                        for finding in justified
                    ],
                    "unjustified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "schema": finding.class_name,
                            "field": finding.field_name,
                        }
                        for finding in unjustified
                    ],
                },
                indent=2,
            )
        )
        return EXIT_DEFECTS if unjustified else EXIT_OK

    if unjustified:
        print(f"check_tenant_body_field: {len(unjustified)} request schema field(s) name the tenant\n")
        for finding in unjustified:
            print(f"  {finding.relative()}:{finding.line}: {finding.class_name}.{finding.field_name}")
        print(
            "\nThe tenant of a write is decided by the authenticated context, not by the\n"
            "caller: take it from the `/api/v1/t/{tenant_slug}/` path segment through\n"
            "`get_current_tenant` and stamp it onto the domain model in the handler or the\n"
            "service. A body that carries it lets a caller name somebody else's tenant\n"
            "(REQ-024 isolation).\n"
            "\n"
            "If this field really is safe — verified against the context before use, or\n"
            "inert — say so where it stands, on the same line or in the comment block\n"
            "directly above it:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <why this field cannot cross a tenant boundary>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    if justified:
        print(
            f"check_tenant_body_field: OK — {len(requests)} request schemas, "
            f"{len(justified)} justified tenant field(s):"
        )
        for finding in justified:
            print(
                f"  {finding.relative()}:{finding.line}: "
                f"{finding.class_name}.{finding.field_name}: {finding.justification}"
            )
        return EXIT_OK

    print(
        f"check_tenant_body_field: OK — none of the {len(requests)} request schemas "
        "accepts a tenant identifier from the caller."
    )
    if list_all:
        for module_dotted, class_name in sorted(requests):
            print(f"  {module_dotted}.{class_name}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when no request schema carries an unjustified tenant field, 1 when at
        least one does, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_tenant_body_field.py",
        description=(
            "Refuse a caller-supplied tenant_key/tenant_slug on a request body schema. "
            f"A field may keep the name by carrying a '{JUSTIFICATION_MARKER} <reason>' comment "
            "on its own line or in the comment block directly above it."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the API package to scan (default: {DEFAULT_SCAN_ROOT})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every schema counted as request input",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    try:
        _tree, requests, findings = collect(scan_root)
    except TenantBodyCheckError as exc:
        print(f"check_tenant_body_field: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(requests, findings, list_all=args.list_all, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
