#!/usr/bin/env python3
"""Count the cadence advances computed outside ``RecurrenceEngine`` (ADR-008 phase 0).

Invoked directly, or through ``task check:recurrence-boundary``::

    python3 scripts/check_recurrence_boundary.py                 # gate mode
    python3 scripts/check_recurrence_boundary.py --inventory     # never red, full list
    python3 scripts/check_recurrence_boundary.py --list          # also name justified sites
    python3 scripts/check_recurrence_boundary.py --json          # machine-readable

**What it measures.** ADR-008 boundary 1: ``RecurrenceEngine`` is the only place
that answers *"when is the next time"*, and the canonical cadence format is the
iCal ``RRULE`` (REQ-015 token). The domain engines stay the **interval
authority** — "every 6 days" is theirs to decide (boundary 2) — but turning that
interval into a date is not. In the ADR's own words: *"Ein zweites
``timedelta(days=...)`` im Service-Code ist ein Defekt, kein Sonderfall."*

This script is the (a) half of the phase-0 inventory the ADR makes its own
acceptance condition, and the ratchet baseline phases 1–3 drive to zero
(NFR-018 §2.1: computed here, on every run, never a versioned constant).

Counting definition (the shared vocabulary, F-6 acceptance-1)
-------------------------------------------------------------

A **site** is a date/datetime shifted by a literal ``timedelta(...)`` —
``base + timedelta(...)``, ``base - timedelta(...)``, ``base += timedelta(...)``
— that carries at least one of three signals:

``cadence_operand``
    The duration is built from a *recurring* quantity: an identifier, attribute
    or string key whose words include one of ``interval``, ``cadence``,
    ``frequency``, ``recurrence``, ``recurring``, ``snooze``, ``repeat``.
    ``timedelta(days=schedule.interval_days)`` is the shape the ADR names.

``occurrence_binding``
    The result is bound to a name that says it is the next one: words including
    ``next``, ``due``, ``upcoming``, ``occurrence`` — ``next_due = …``,
    ``task.due_date = …``, ``due_date=…`` as a keyword argument.

``occurrence_context``
    The enclosing function says so: ``calculate_due_date``,
    ``next_inspection_date``, ``get_next_watering_dates``.

What deliberately does **not** count, because the ADR's boundary is cadence and
not arithmetic on dates:

* **Template and clone offsets** — "this task is due N days after the run
  starts" (``timedelta(days=tt.days_offset)``). It answers *when is the first
  one*, not *when is the next one*, and it repeats nothing.
* **TTLs, expiries and retention horizons** — a refresh token, a cache entry, an
  export, an anonymisation deadline. One-shot deadlines, no recurrence.
* **Lookback windows and horizons** — ``now - timedelta(days=30)`` as a query
  cutoff, ``today + timedelta(days=horizon)`` as the end of a forecast range.
* **Durations** — a growth phase's typical length, a Karenz (safety interval), a
  recovery window. These *are* one date derived from another, but nothing about
  them repeats.

The line between the last group and a real cadence is a judgement, and where the
words happen to collide (``safety_interval_days`` reads as a cadence and is not
one) the answer is written **at the site**, not hidden in this file — see the
escape hatch below. That is deliberate: an exclusion list inside the scanner is a
rule nobody can argue with in review.

The escape hatch
----------------

A site may stand by carrying a justification on its own line, or in the comment
block directly above it::

    # recurrence-owner-ok: a Karenz period is a one-shot waiting time before
    # harvest, not a cadence — nothing recurs, so there is no rule to advance.
    safe_date = applied_at + timedelta(days=period["safety_interval_days"])

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer.

**A justification that no longer sits at a site is itself a finding**
(``stale_justification``). A register that can outlive its debt is how this
repository has been bitten before: the marker is written once, the code is fixed
later, and the pardon stays behind pardoning nothing. The rule is the one
``_KNOWN_OPEN`` in ``tests/unit/migrations/test_substrate_invariants.py``
already applies to seed data — an entry that has healed must be removed.

What this scan cannot see — stated rather than implied
------------------------------------------------------

A silently under-counting scan produces a baseline that looks better than
reality, which is worse than no baseline. The blind spots, all of them
one-directional (they *under*-count, so nothing can fake progress):

* **A duration behind a name.** ``step = timedelta(days=n)`` followed by
  ``base + step`` is not seen; only a literal ``timedelta(...)`` in the shift is.
* **A cadence behind a helper.** ``self._advance(base, schedule)`` hides the
  arithmetic in a callee this scan attributes to that callee, not to the caller —
  and if the callee's names carry none of the three signals, to nobody.
* **A cadence behind arithmetic that is not ``timedelta``.** ``relativedelta``,
  month/year stepping via ``.replace(...)``, ``fromordinal`` arithmetic, or a
  loop over a list of precomputed dates. *Measured on 2026-09-01: the backend
  imports no ``relativedelta`` and constructs no ``rrule`` outside the engine, so
  the whole of (a) is ``timedelta`` arithmetic today — but nothing stops the next
  one from arriving in another shape.*
* **A cadence with anonymous names.** ``base + timedelta(days=n)`` inside a
  function called ``_step`` carries no signal at all and is invisible.
* **Anything outside the scan root** (default ``src/backend/app``): the frontend
  computes no due dates today, and the E2E suite is not production code.

The consequence is the honest one: **the number this prints is a floor, not a
census.** It is a stable, monotone measure of the same shape in the same tree,
which is what a ratchet needs; it is not a proof that no other cadence exists.
The hand-check that accompanied the phase-0 baseline
(``.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md``) is where the
delta between this scan and a reading of the six named files is recorded.

Modes
-----

* default — **gate**: red when a site carries no reason, or when a reason has
  gone stale. This is the mode F-10 wires into the required ``static`` lane once
  phases 1–2 have driven the open count to zero. It is red today, on purpose,
  and is therefore *not* wired anywhere.
* ``--inventory`` — never red. Prints the counts and every site with
  ``file:line`` attribution. This is the phase-0 instrument.

Standard library only, no application import, no running stack: the ``static``
job is Python-only, and importing the domain modules would drag in settings and
database clients for a question answerable from the source text.

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

#: The owner of boundary 1. Sites inside it are the authority, not a violation.
OWNER_MODULES = ("domain/engines/recurrence_engine.py",)

#: The marker that exempts a site, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption.
JUSTIFICATION_MARKER = "# recurrence-owner-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: The duration constructors this scan recognises in a shift. ``timedelta`` is
#: the only one the backend uses today (measured); the docstring names what a
#: second shape would cost.
DURATION_CALLS = frozenset({"timedelta"})

#: Words that make a duration a *cadence* rather than a one-shot offset.
CADENCE_TOKENS = frozenset(
    {"interval", "intervals", "cadence", "frequency", "recurrence", "recurring", "snooze", "repeat"}
)

#: Words that make a name say "this is the next one".
OCCURRENCE_TOKENS = frozenset({"next", "due", "upcoming", "occurrence"})

#: Signal labels, in report order.
KIND_LABELS = {
    "cadence_operand": "cadence advance (the duration comes from a recurring interval)",
    "occurrence_binding": "cadence advance (the result is bound as the next occurrence)",
    "occurrence_context": "cadence advance (the enclosing function computes a next occurrence)",
    "stale_justification": "stale exemption (a reason that no longer sits at a site)",
}

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class RecurrenceBoundaryError(Exception):
    """A usage or environment problem — not a finding about the code."""


@dataclass(frozen=True)
class Site:
    """One cadence advance (or one stale exemption) at one place in the tree."""

    path: Path
    line: int
    kinds: tuple[str, ...]
    function: str
    detail: str
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)

    def identity(self) -> str:
        """A line-number-free identity, stable across edits above the site.

        The register in the ratchet selftest keys on this: a site that moves down
        a file is the same site, and pinning it by line would turn every unrelated
        edit into a false ratchet failure.
        """
        return f"{self.relative()}::{self.function or '<module>'}::{'+'.join(self.kinds)}"


# ── Name plumbing ────────────────────────────────────────────────────────────


def tokens(name: str) -> frozenset[str]:
    """Split a dotted / snake_case / camelCase name into lowercase words.

    ``schedule.interval_days`` → ``{schedule, interval, days}``;
    ``nextDueDate`` → ``{next, due, date}``.
    """
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return frozenset(part for part in _TOKEN_SPLIT.split(spaced.lower()) if part)


def identifier_names(node: ast.AST) -> list[str]:
    """Every identifier-ish string inside an expression.

    Names, attribute labels and string subscripts all carry the vocabulary this
    scan reads — ``period["safety_interval_days"]`` says "interval" exactly as
    loudly as ``schedule.interval_days`` does.
    """
    found: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.append(child.id)
        elif isinstance(child, ast.Attribute):
            found.append(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            found.append(child.value)
    return found


def target_name(node: ast.expr) -> str:
    """Render an assignment target as a readable name (``task.due_date``)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{target_name(node.value)}.{node.attr}".lstrip(".")
    if isinstance(node, ast.Subscript):
        return target_name(node.value)
    return ""


def is_duration_call(node: ast.expr) -> bool:
    """Whether *node* is a literal duration constructor call (``timedelta(...)``)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in DURATION_CALLS
    if isinstance(func, ast.Attribute):
        return func.attr in DURATION_CALLS
    return False


# ── Context maps ─────────────────────────────────────────────────────────────


def function_ranges(tree: ast.Module) -> list[tuple[int, int, str]]:
    """Every function's ``(start, end, name)``, innermost last after sorting."""
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges.append((node.lineno, node.end_lineno or node.lineno, node.name))
    # Narrowest range last, so a linear scan ends on the innermost enclosing one.
    return sorted(ranges, key=lambda entry: entry[1] - entry[0], reverse=True)


def enclosing_function(ranges: list[tuple[int, int, str]], line: int) -> str:
    """The innermost function containing *line*, or an empty string."""
    name = ""
    for start, end, candidate in ranges:
        if start <= line <= end:
            name = candidate
    return name


def binding_map(tree: ast.Module) -> dict[int, str]:
    """Map every expression node to the name its value is bound to.

    Assignments, annotated assignments, augmented assignments and keyword
    arguments all bind. ``ast.walk`` is breadth-first, so an inner keyword
    binding overwrites the outer assignment it sits inside — which is the
    reading a human gives ``x = Task(due_date=now + timedelta(...))`` too.
    """
    mapping: dict[int, str] = {}
    for node in ast.walk(tree):
        binding = ""
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            binding = next((target_name(t) for t in node.targets if target_name(t)), "")
            value = node.value
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            binding, value = target_name(node.target), node.value
        elif isinstance(node, ast.keyword) and node.arg:
            binding, value = node.arg, node.value
        if not binding or value is None:
            continue
        for sub in ast.walk(value):
            mapping[id(sub)] = binding
    return mapping


# ── Justifications ───────────────────────────────────────────────────────────


def _reason_from(text: str) -> str | None:
    """Extract a non-trivial reason following the marker in one source line."""
    position = text.find(JUSTIFICATION_MARKER)
    if position < 0:
        return None
    reason = text[position + len(JUSTIFICATION_MARKER) :].strip()
    return reason if len(reason) >= MIN_JUSTIFICATION_CHARS else None


def _continuation(lines: list[str], marker_line: int, stop_before: int) -> str:
    """Fold the rest of a marker's comment block into one readable reason.

    A reason worth writing rarely fits on one line, and a register that shows
    only its first clause is a register a reviewer cannot judge. Continuation
    lines are the plain ``#`` comments between the marker and the site.
    """
    parts: list[str] = []
    for index in range(marker_line + 1, stop_before):
        candidate = lines[index - 1].strip()
        if not candidate.startswith("#") or JUSTIFICATION_MARKER in candidate:
            break
        parts.append(candidate.lstrip("#").strip())
    return " ".join(part for part in parts if part)


def justification_for(lines: list[str], line: int) -> tuple[str | None, int | None]:
    """Find the reason exempting the site at 1-based *line*.

    Accepted placements: trailing on the site's own line, or anywhere in the
    contiguous comment block directly above it — the same two placements the
    sibling gates use, because that is where this repository already writes
    "why this one is different".

    Returns:
        The reason and the 1-based line the marker sits on, or ``(None, None)``.
    """
    if 0 < line <= len(lines):
        reason = _reason_from(lines[line - 1])
        if reason:
            return reason, line
    cursor = line - 1
    while cursor >= 1:
        candidate = lines[cursor - 1].strip()
        if not candidate.startswith("#"):
            break
        reason = _reason_from(candidate)
        if reason:
            tail = _continuation(lines, cursor, line)
            return (f"{reason} {tail}".strip() if tail else reason), cursor
        cursor -= 1
    return None, None


# ── The scan ─────────────────────────────────────────────────────────────────


def _shifts(tree: ast.Module) -> list[tuple[ast.AST, ast.Call, str]]:
    """Every ``date ± timedelta(...)`` in the module as ``(node, duration, binding)``."""
    bindings = binding_map(tree)
    found: list[tuple[ast.AST, ast.Call, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign):
            if isinstance(node.op, (ast.Add, ast.Sub)) and is_duration_call(node.value):
                assert isinstance(node.value, ast.Call)
                found.append((node, node.value, target_name(node.target)))
            continue
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, (ast.Add, ast.Sub)):
            continue
        for side in (node.right, node.left):
            if is_duration_call(side) and not is_duration_call(node.left if side is node.right else node.right):
                assert isinstance(side, ast.Call)
                found.append((node, side, bindings.get(id(node), "")))
                break
    return found


def scan_source(path: Path, source: str) -> list[Site]:
    """Every cadence advance and stale exemption in one module's source text."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise RecurrenceBoundaryError(f"cannot parse {path}: {exc}") from exc

    lines = source.splitlines()
    ranges = function_ranges(tree)
    sites: list[Site] = []
    claimed: set[int] = set()

    for node, duration, binding in _shifts(tree):
        line = node.lineno
        function = enclosing_function(ranges, line)
        kinds: list[str] = []
        if tokens(" ".join(identifier_names(duration))) & CADENCE_TOKENS:
            kinds.append("cadence_operand")
        if binding and tokens(binding) & OCCURRENCE_TOKENS:
            kinds.append("occurrence_binding")
        if function and tokens(function) & OCCURRENCE_TOKENS:
            kinds.append("occurrence_context")
        if not kinds:
            continue
        reason, marker_line = justification_for(lines, line)
        if marker_line is not None:
            claimed.add(marker_line)
        sites.append(
            Site(
                path=path,
                line=line,
                kinds=tuple(kinds),
                function=function,
                detail=lines[line - 1].strip() if 0 < line <= len(lines) else "",
                justification=reason,
            )
        )

    for index, text in enumerate(lines, start=1):
        if _reason_from(text) is not None and index not in claimed:
            sites.append(
                Site(
                    path=path,
                    line=index,
                    kinds=("stale_justification",),
                    function=enclosing_function(ranges, index),
                    detail=text.strip(),
                    justification=None,
                )
            )

    return sorted(sites, key=lambda site: (site.line, site.kinds))


def scan_file(path: Path) -> list[Site]:
    """Read and scan one module."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecurrenceBoundaryError(f"cannot read {path}: {exc}") from exc
    return scan_source(path, source)


def collect(scan_root: Path) -> list[Site]:
    """Every site below *scan_root*, justified or not.

    The owner module is skipped: ``RecurrenceEngine`` *is* the authority, so an
    advance inside it is the rule rather than a breach of it.
    """
    if not scan_root.exists():
        raise RecurrenceBoundaryError(f"scan root does not exist: {scan_root}")
    paths = sorted(path for path in scan_root.rglob("*.py"))
    if not paths:
        raise RecurrenceBoundaryError(f"no Python modules under {scan_root}")
    sites: list[Site] = []
    for path in paths:
        if path.relative_to(scan_root).as_posix() in OWNER_MODULES:
            continue
        sites.extend(scan_file(path))
    return sites


# ── Reporting ────────────────────────────────────────────────────────────────


def _as_json(sites: list[Site]) -> str:
    open_sites = [site for site in sites if not site.justified]
    justified = [site for site in sites if site.justified]
    return json.dumps(
        {
            "boundary": "recurrence",
            "owner": "app.domain.engines.recurrence_engine.RecurrenceEngine",
            "total": len(sites),
            "open": len(open_sites),
            "justified": len(justified),
            "sites": [
                {
                    "file": site.relative(),
                    "line": site.line,
                    "function": site.function,
                    "kinds": list(site.kinds),
                    "identity": site.identity(),
                    "detail": site.detail,
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
            f"check_recurrence_boundary: {len(sites)} cadence advance(s) outside RecurrenceEngine "
            f"— {len(open_sites)} open, {len(justified)} justified.\n"
        )
        for site in sites:
            marker = "    " if site.justified else "  ! "
            print(f"{marker}{site.relative()}:{site.line}  [{'+'.join(site.kinds)}]  in {site.function or '<module>'}")
            print(f"        {site.detail}")
            if site.justification:
                print(f"        reason: {site.justification}")
        print(
            "\nInventory mode never fails. This is ADR-008 phase 0 (a): the number above is\n"
            "the ratchet baseline phases 1-2 drive to zero, computed on every run and never\n"
            "recorded as a constant (NFR-018 §2.1). It is a floor, not a census — see this\n"
            "script's docstring for what the scan cannot see."
        )
        return EXIT_OK

    if open_sites:
        print(f"check_recurrence_boundary: {len(open_sites)} cadence advance(s) outside RecurrenceEngine\n")
        for site in open_sites:
            print(f"  {site.relative()}:{site.line}: {KIND_LABELS[site.kinds[0]]}")
            print(f"      in {site.function or '<module>'}: {site.detail}")
        print(
            "\nADR-008 boundary 1: RecurrenceEngine is the only place that turns a cadence\n"
            "into the next date. The domain engine still decides WHAT the interval is; it\n"
            "no longer decides which day that lands on. Express the cadence as an RRULE\n"
            "(RecurrenceEngine.fixed_interval_rule) and advance it with\n"
            "RecurrenceEngine.next_occurrence — or say, where it stands, why this shift is\n"
            "not a cadence at all:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <why nothing here recurs>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        if any(site.kinds[0] == "stale_justification" for site in open_sites):
            print(
                "\nA stale exemption is a reason that no longer sits at a site: the code was\n"
                "fixed and the pardon stayed behind. Delete it — a register that outlives its\n"
                "debt stops being evidence of anything."
            )
        return EXIT_DEFECTS

    print(f"check_recurrence_boundary: OK — {len(justified)} justified site(s), no unexplained cadence advance.")
    if list_all:
        for site in justified:
            print(f"  {site.relative()}:{site.line} [{'+'.join(site.kinds)}]: {site.justification}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every cadence advance carries a reason (or in ``--inventory``
        mode), 1 when at least one does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_recurrence_boundary.py",
        description=(
            "Count the cadence advances computed outside RecurrenceEngine (ADR-008 boundary 1, "
            "phase-0 inventory half (a)). A site may stand by carrying a "
            f"'{JUSTIFICATION_MARKER} <reason>' comment."
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
        help="also name every justified site when the check passes",
    )
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    try:
        sites = collect(scan_root)
    except RecurrenceBoundaryError as exc:
        print(f"check_recurrence_boundary: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(sites, list_all=args.list_all, as_json=args.json, inventory=args.inventory)


if __name__ == "__main__":
    raise SystemExit(main())
