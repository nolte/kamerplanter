#!/usr/bin/env python3
"""Count the notification writes made outside the propagation path (ADR-008 phase 0).

Invoked directly, or through ``task check:notification-write-boundary``::

    python3 scripts/check_notification_write_boundary.py              # gate mode
    python3 scripts/check_notification_write_boundary.py --inventory  # never red, full list
    python3 scripts/check_notification_write_boundary.py --list       # also name justified sites
    python3 scripts/check_notification_write_boundary.py --json       # machine-readable

**What it measures.** ADR-008 boundary 3: every state change at a source — a
task moved, reassigned, completed or deleted; a reminder confirmed, skipped or
rescheduled — reaches its derived in-app notification through **one**
propagation service, idempotent via ``group_key`` and fail-closed on tenant. In
the ADR's own words: *"Kein Aufrufer ruft mehr direkt Notification-Repositories."*

This script is the (b) half of the phase-0 inventory the ADR makes its own
acceptance condition, and the ratchet baseline phase 2 drives to zero
(NFR-018 §2.1: computed here, on every run, never a versioned constant).

Counting definition (the shared vocabulary, F-6 acceptance-1)
-------------------------------------------------------------

A **site** is a call to a mutating method — ``create``, ``update``, ``delete``,
``mark_read``, ``mark_acted``: the write half of ``INotificationRepository`` —
on a receiver this scan resolves to a notification repository, in any module
except the owner (``notification_propagation_service.py``).

The receiver is resolved three ways, in this order:

1. **By annotation.** A parameter annotated ``INotificationRepository`` (or a
   concrete implementation), and any attribute assigned from it inside the same
   module. This is what finds ``self._repo`` in the propagation service, and —
   more importantly — what keeps ``self._repo`` in ``task_service.py`` *out*: it
   is annotated ``ITaskRepository``, so it is a different repository with the
   same attribute name.
2. **By factory.** A local bound from ``get_notification_repo()``.
3. **By name.** A receiver whose words contain ``notification`` and
   ``repo``/``repository`` — ``self._notification_repo``.

Three write classes, and only one of them is debt
--------------------------------------------------

The distinction ADR-008 draws is about *why* a row is written, and no static
scan can read intent off a ``repo.create(...)``. So the classification is
**declared at the site**, and this check enforces that a declaration exists,
that it names a known class, and that it has not gone stale:

``propagation write`` — **counts against the boundary.**
    A notification written because its *source* changed. This is the class
    ADR-008 gives to one owner; outside the propagation service it is debt, and
    it is what phase 2 drives to zero. It carries no marker: it is the default.

``event`` — **named outside the boundary.**
    The first materialisation of an event that has no notification yet — a
    frost warning, a watering escalation, a digest. Nothing is being *followed*;
    a row is being born. Declared with
    ``# notification-write-ok: event: <reason>``.

``user-action`` — **named outside the boundary.**
    The user acting on their own notification: read, dismissed, acted upon
    (REQ-030 §5.2). The source did not change; the reader did. Declared with
    ``# notification-write-ok: user-action: <reason>``.

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer, and the class must be one of the two above — an unknown
class is reported like a missing marker. A marker may sit trailing on the site's
own line or anywhere in the comment block directly above it.

**A justification that no longer sits at a site is itself a finding**
(``stale_justification``). A register that can outlive its debt is how this
repository has been bitten before; the rule is the one ``_KNOWN_OPEN`` in
``tests/unit/migrations/test_substrate_invariants.py`` already applies to seed
data — an entry that has healed must be removed.

What this scan cannot see — stated rather than implied
------------------------------------------------------

This is the weaker of the two phase-0 halves, and pretending otherwise would be
the failure it is meant to prevent:

* **The missing edge is invisible, and it is the whole #769 class.** This scan
  finds writes that happen in the wrong place. It cannot find the write that
  *never happens* — a source mutation with no propagation call at all, which is
  exactly #742 and #769. A count of zero here does **not** mean every edge is
  wired; it means no caller is reaching around the owner. The pairing test that
  phase 2 owes (F-8) is what covers the other direction; this counter cannot.
* **Indirection.** A write reached through a helper, a callback or a repository
  handed in as a bare parameter that this module never annotates is not
  attributed here.
* **The channel path is deliberately out of scope.** ``NotificationService``'s
  ``send_*`` methods dispatch to Home Assistant / e-mail / Web Push
  (REQ-030 §4.1) and are asynchronous by design (ADR-008 alternative C); they
  are not the in-app propagation path and are not counted. A caller that
  propagates a source change by firing a *channel* send instead would therefore
  be missed.
* **Construction is not a write.** ``Notification(...)`` built and handed to a
  channel adapter (``ha_notification_channel.py``) persists nothing.
* **Anything outside the scan root** (default ``src/backend/app``).

All of these under-count, so the number cannot fake progress — but it is a
floor, not a census. The hand-check that accompanied the phase-0 baseline
(``.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md``) records the
delta between this scan and a reading of the six named files.

Modes
-----

* default — **gate**: red when a write carries no class declaration, when the
  class is unknown, or when a declaration has gone stale. This is the mode F-10
  wires into the required ``static`` lane once phase 2 is done.
* ``--inventory`` — never red. Prints the counts and every site with
  ``file:line`` attribution. This is the phase-0 instrument.

Standard library only, no application import, no running stack.

Traces to ADR-008 (phase 0) and issue #1061, feature F-6 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the backend application code lives, relative to the repository root.
DEFAULT_SCAN_ROOT = "src/backend/app"

#: The owner of boundary 3, relative to the scan root. Writes inside it are the
#: propagation path itself.
OWNER_MODULES = ("domain/services/notification_propagation_service.py",)

#: The repository *definition* modules. They declare the write methods rather
#: than calling them across the boundary, so a self-call inside the ArangoDB
#: implementation is not a caller reaching around the owner.
DEFINITION_MODULES = (
    "domain/interfaces/notification_repository.py",
    "data_access/arango/notification_repository.py",
)

#: The write half of ``INotificationRepository``.
MUTATING_METHODS = frozenset({"create", "update", "delete", "mark_read", "mark_acted"})

#: Annotations that identify a notification repository.
REPOSITORY_TYPES = frozenset({"INotificationRepository", "NotificationRepository", "ArangoNotificationRepository"})

#: Factories that hand one out.
REPOSITORY_FACTORIES = frozenset({"get_notification_repo", "get_notification_repository"})

JUSTIFICATION_MARKER = "# notification-write-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: The two write classes ADR-008 names as living outside the propagation path.
NAMED_WRITE_CLASSES = ("event", "user-action")

KIND_LABELS = {
    "notification_write": "notification write outside NotificationPropagationService",
    "unknown_write_class": "notification write declaring an unknown write class",
    "stale_justification": "stale exemption (a declaration that no longer sits at a write)",
}

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class NotificationWriteBoundaryError(Exception):
    """A usage or environment problem — not a finding about the code."""


@dataclass(frozen=True)
class Site:
    """One notification write (or one stale exemption) at one place in the tree."""

    path: Path
    line: int
    kind: str
    function: str
    receiver: str
    method: str
    detail: str
    write_class: str | None
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None and self.kind == "notification_write"

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)

    def identity(self) -> str:
        """A line-number-free identity, stable across edits above the site."""
        return f"{self.relative()}::{self.function or '<module>'}::{self.receiver}.{self.method}"


# ── Name plumbing ────────────────────────────────────────────────────────────


def tokens(name: str) -> frozenset[str]:
    """Split a dotted / snake_case name into lowercase words."""
    return frozenset(part for part in _TOKEN_SPLIT.split(name.lower()) if part)


def dotted(node: ast.expr) -> str:
    """Render an attribute chain as a readable name (``self._notification_repo``)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _annotation_names(node: ast.expr | None) -> set[str]:
    """Every bare type name mentioned in an annotation (``X | None`` → ``{X}``)."""
    if node is None:
        return set()
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            names.add(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            names.add(child.value.strip("'\" "))
    return names


def _looks_like_notification_repo(name: str) -> bool:
    """Name heuristic: ``self._notification_repo`` and friends."""
    words = tokens(name)
    return "notification" in words and bool(words & {"repo", "repository", "repositories"})


def repository_receivers(tree: ast.Module) -> set[str]:
    """Every receiver in this module that resolves to a notification repository.

    Module-scoped on purpose: ``self._repo`` is a notification repository in
    ``notification_propagation_service.py`` and a task repository in
    ``task_service.py``, and only the annotation in the module's own
    ``__init__`` can tell the two apart.
    """
    receivers: set[str] = set()
    parameters: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            for argument in arguments:
                if _annotation_names(argument.annotation) & REPOSITORY_TYPES:
                    parameters.add(argument.arg)
        elif isinstance(node, ast.AnnAssign) and _annotation_names(node.annotation) & REPOSITORY_TYPES:
            name = dotted(node.target)
            if name:
                receivers.add(name)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if value is None:
            continue
        bound = False
        if isinstance(value, ast.Name) and value.id in parameters:
            bound = True
        elif isinstance(value, ast.Call):
            callee = value.func
            callee_name = callee.attr if isinstance(callee, ast.Attribute) else getattr(callee, "id", "")
            bound = callee_name in REPOSITORY_FACTORIES or callee_name in REPOSITORY_TYPES
        if not bound:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            name = dotted(target)
            if name:
                receivers.add(name)

    return receivers | parameters


# ── Context maps ─────────────────────────────────────────────────────────────


def function_ranges(tree: ast.Module) -> list[tuple[int, int, str]]:
    """Every function's ``(start, end, name)``, widest first."""
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges.append((node.lineno, node.end_lineno or node.lineno, node.name))
    return sorted(ranges, key=lambda entry: entry[1] - entry[0], reverse=True)


def enclosing_function(ranges: list[tuple[int, int, str]], line: int) -> str:
    """The innermost function containing *line*, or an empty string."""
    name = ""
    for start, end, candidate in ranges:
        if start <= line <= end:
            name = candidate
    return name


# ── Justifications ───────────────────────────────────────────────────────────


def _declaration_from(text: str) -> tuple[str, str] | None:
    """Parse ``# notification-write-ok: <class>: <reason>`` out of one line.

    Returns:
        ``(write_class, reason)`` — the class is returned even when it is
        unknown, so the report can say *which* unknown class was written rather
        than only that something is missing. ``None`` when there is no marker or
        no separable reason.
    """
    position = text.find(JUSTIFICATION_MARKER)
    if position < 0:
        return None
    payload = text[position + len(JUSTIFICATION_MARKER) :].strip()
    write_class, separator, reason = payload.partition(":")
    if not separator:
        return None
    write_class, reason = write_class.strip().lower(), reason.strip()
    if not write_class or len(reason) < MIN_JUSTIFICATION_CHARS:
        return None
    return write_class, reason


def _continuation(lines: list[str], marker_line: int, stop_before: int) -> str:
    """Fold the rest of a marker's comment block into one readable reason."""
    parts: list[str] = []
    for index in range(marker_line + 1, stop_before):
        candidate = lines[index - 1].strip()
        if not candidate.startswith("#") or JUSTIFICATION_MARKER in candidate:
            break
        parts.append(candidate.lstrip("#").strip())
    return " ".join(part for part in parts if part)


def declaration_for(lines: list[str], line: int) -> tuple[tuple[str, str] | None, int | None]:
    """Find the write-class declaration covering the site at 1-based *line*."""
    if 0 < line <= len(lines):
        parsed = _declaration_from(lines[line - 1])
        if parsed:
            return parsed, line
    cursor = line - 1
    while cursor >= 1:
        candidate = lines[cursor - 1].strip()
        if not candidate.startswith("#"):
            break
        parsed = _declaration_from(candidate)
        if parsed:
            write_class, reason = parsed
            tail = _continuation(lines, cursor, line)
            return (write_class, f"{reason} {tail}".strip() if tail else reason), cursor
        cursor -= 1
    return None, None


# ── The scan ─────────────────────────────────────────────────────────────────


def scan_source(path: Path, source: str) -> list[Site]:
    """Every notification write and stale exemption in one module's source text."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise NotificationWriteBoundaryError(f"cannot parse {path}: {exc}") from exc

    lines = source.splitlines()
    ranges = function_ranges(tree)
    receivers = repository_receivers(tree)
    sites: list[Site] = []
    claimed: set[int] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        if method not in MUTATING_METHODS:
            continue
        receiver = dotted(node.func.value)
        if not receiver:
            continue
        if receiver not in receivers and not _looks_like_notification_repo(receiver):
            continue

        line = node.lineno
        parsed, marker_line = declaration_for(lines, line)
        if marker_line is not None:
            claimed.add(marker_line)
        write_class = parsed[0] if parsed else None
        reason = parsed[1] if parsed else None
        kind = "notification_write"
        if write_class is not None and write_class not in NAMED_WRITE_CLASSES:
            kind = "unknown_write_class"
        sites.append(
            Site(
                path=path,
                line=line,
                kind=kind,
                function=enclosing_function(ranges, line),
                receiver=receiver,
                method=method,
                detail=lines[line - 1].strip() if 0 < line <= len(lines) else "",
                write_class=write_class,
                justification=reason if kind == "notification_write" else None,
            )
        )

    for index, text in enumerate(lines, start=1):
        if _declaration_from(text) is not None and index not in claimed:
            sites.append(
                Site(
                    path=path,
                    line=index,
                    kind="stale_justification",
                    function=enclosing_function(ranges, index),
                    receiver="",
                    method="",
                    detail=text.strip(),
                    write_class=None,
                    justification=None,
                )
            )

    return sorted(sites, key=lambda site: (site.line, site.method))


def scan_file(path: Path) -> list[Site]:
    """Read and scan one module."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NotificationWriteBoundaryError(f"cannot read {path}: {exc}") from exc
    return scan_source(path, source)


def collect(scan_root: Path) -> list[Site]:
    """Every site below *scan_root*, justified or not."""
    if not scan_root.exists():
        raise NotificationWriteBoundaryError(f"scan root does not exist: {scan_root}")
    paths = sorted(path for path in scan_root.rglob("*.py"))
    if not paths:
        raise NotificationWriteBoundaryError(f"no Python modules under {scan_root}")
    excluded = set(OWNER_MODULES) | set(DEFINITION_MODULES)
    sites: list[Site] = []
    for path in paths:
        relative = path.relative_to(scan_root).as_posix()
        if relative in excluded:
            continue
        sites.extend(scan_file(path))
    return sites


# ── Reporting ────────────────────────────────────────────────────────────────


def _as_json(sites: list[Site]) -> str:
    open_sites = [site for site in sites if not site.justified]
    return json.dumps(
        {
            "boundary": "notification-write",
            "owner": "app.domain.services.notification_propagation_service.NotificationPropagationService",
            "total": len(sites),
            "open": len(open_sites),
            "justified": len(sites) - len(open_sites),
            "sites": [
                {
                    "file": site.relative(),
                    "line": site.line,
                    "function": site.function,
                    "kind": site.kind,
                    "call": f"{site.receiver}.{site.method}" if site.method else "",
                    "identity": site.identity(),
                    "detail": site.detail,
                    "write_class": site.write_class,
                    "reason": site.justification,
                }
                for site in sites
            ],
        },
        indent=2,
    )


def report(sites: list[Site], *, list_all: bool, as_json: bool, inventory: bool) -> int:
    """Print the outcome and return the process exit code."""
    open_sites = [site for site in sites if not site.justified]
    justified = [site for site in sites if site.justified]

    if as_json:
        print(_as_json(sites))
        return EXIT_OK if inventory or not open_sites else EXIT_DEFECTS

    if inventory:
        print(
            f"check_notification_write_boundary: {len(sites)} notification write(s) outside "
            f"NotificationPropagationService — {len(open_sites)} open, {len(justified)} declared.\n"
        )
        for site in sites:
            marker = "    " if site.justified else "  ! "
            call = f"{site.receiver}.{site.method}" if site.method else site.kind
            print(f"{marker}{site.relative()}:{site.line}  [{call}]  in {site.function or '<module>'}")
            print(f"        {site.detail}")
            if site.justified:
                print(f"        class: {site.write_class} — {site.justification}")
        print(
            "\nInventory mode never fails. This is ADR-008 phase 0 (b): the number above is\n"
            "the ratchet baseline phase 2 drives to zero, computed on every run and never\n"
            "recorded as a constant (NFR-018 §2.1). It counts writes made in the wrong\n"
            "place; it CANNOT see the propagation that never happens, which is the whole\n"
            "#769 class — see this script's docstring."
        )
        return EXIT_OK

    if open_sites:
        print(
            f"check_notification_write_boundary: {len(open_sites)} notification write(s) outside "
            "NotificationPropagationService\n"
        )
        for site in open_sites:
            print(f"  {site.relative()}:{site.line}: {KIND_LABELS[site.kind]}")
            print(f"      in {site.function or '<module>'}: {site.detail}")
            if site.kind == "unknown_write_class":
                print(f"      declared class {site.write_class!r} is not one of {NAMED_WRITE_CLASSES}")
        print(
            "\nADR-008 boundary 3: a source change reaches its in-app notification through\n"
            "NotificationPropagationService — idempotent via group_key, fail-closed on\n"
            "tenant — and no caller writes notification rows directly. Route the write\n"
            "through the propagation service, or declare which of the two classes that\n"
            "ADR-008 names outside the boundary this write belongs to:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} event: <what event is first materialised here>\n"
            f"    {JUSTIFICATION_MARKER} user-action: <what the reader did to their own row>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters.\n"
            "A propagation write — a notification following a change at its SOURCE — has no\n"
            "third option: it belongs to the owner."
        )
        if any(site.kind == "stale_justification" for site in open_sites):
            print(
                "\nA stale exemption is a declaration that no longer sits at a write: the call\n"
                "moved or went away and the pardon stayed behind. Delete it — a register that\n"
                "outlives its debt stops being evidence of anything."
            )
        return EXIT_DEFECTS

    print(
        f"check_notification_write_boundary: OK — {len(justified)} declared site(s), no undeclared notification write."
    )
    if list_all:
        for site in justified:
            print(f"  {site.relative()}:{site.line} [{site.write_class}]: {site.justification}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every notification write outside the propagation service declares
        a known write class (or in ``--inventory`` mode), 1 when at least one
        does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_notification_write_boundary.py",
        description=(
            "Count the notification writes made outside NotificationPropagationService "
            "(ADR-008 boundary 3, phase-0 inventory half (b)). A write may stand by "
            f"declaring its class: '{JUSTIFICATION_MARKER} <event|user-action>: <reason>'."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the source tree to scan (default: {DEFAULT_SCAN_ROOT})",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="report the counts and every site without ever failing (the phase-0 instrument)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every declared site when the check passes",
    )
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    try:
        sites = collect(scan_root)
    except NotificationWriteBoundaryError as exc:
        print(f"check_notification_write_boundary: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(sites, list_all=args.list_all, as_json=args.json, inventory=args.inventory)


if __name__ == "__main__":
    raise SystemExit(main())
