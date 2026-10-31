#!/usr/bin/env python3
"""Generate the REQ-053 acceptance matrix GP-ACC <-> test, from the tests (WP 6.1, #2445).

The matrix is never edited by hand. The acceptance criteria come from the spec
(``spec/req/REQ-053_*.md``, the ``- **GP-ACC-nnn**`` list of section 30); the tests are
scanned for the id they carry. One convention, the one the suites already use:

* the literal ``GP-ACC-nnn`` anywhere in a test file (module docstring, ``describe``/``it``
  title, comment), or
* ``gp_acc_nnn`` in a Python test-function name.

Scanned files: ``src/backend/tests/**/test_*.py`` (tier from the directory: ``unit``,
``api``, ``integration``, ``guards``), ``src/frontend/src/**/*.test.ts[x]`` (tier ``frontend``),
``tests/e2e/test_*.py`` and ``**/*.feature`` (tier ``e2e``). Fixtures, page objects and
production code that merely quote an id are not tests and are not scanned.

An id without a test fails the check unless ``spec/e2e-testcases/GP-ACC-gaps.json`` lists it
with a ``reason`` and a tracking ``issue``. That allowlist is the only way to carry an honest
gap, and the check fails again when a listed id has gained a test (remove it then).

Wave 7 (WP 7.27, #2493) adds a second matrix with the same rules: the SHOULD rows of wave 7 (GP-FR / GP-API /
GP-UX, listed in :data:`WAVE7_ROWS` from plan section 3 "Welle 7" and spec section 34) against the tests that carry
the row id. A test carries ``GP-FR-nnn`` (or ``GP-API-nnn`` / ``GP-UX-nnn``) literally; the shorthand
``GP-FR-158/159`` counts for each number. Output ``spec/e2e-testcases/GP-REQ-wave7-matrix.md``; honest gaps in
``GP-REQ-wave7-gaps.json`` - a full gap (no test at all) or, with ``"partial": true``, a row whose tests leave a
named part of it unproven (for example GP-FR-025: multi-duplicate is tested, the ``Ctrl/Cmd+D`` key is not wired).

Usage: ``python3 scripts/gp_acc_matrix.py [--write | --check]`` (default ``--check``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_GLOB = "spec/req/REQ-053_*.md"
MATRIX = ROOT / "spec/e2e-testcases/GP-ACC-matrix.md"
GAPS = ROOT / "spec/e2e-testcases/GP-ACC-gaps.json"

_SPEC_ID = re.compile(r"^- \*\*GP-ACC-(\d{3})\*\*\s*\(([^)]*)\)", re.MULTILINE)
_TEST_ID = re.compile(r"GP-ACC-(\d{3})|gp_acc_(\d{3})", re.IGNORECASE)
_SKIP_DIRS = {"node_modules", ".git", "fixtures", "__pycache__"}
_SELF = {"test_req053_acceptance_matrix.py"}

WAVE7_MATRIX = ROOT / "spec/e2e-testcases/GP-REQ-wave7-matrix.md"
WAVE7_GAPS = ROOT / "spec/e2e-testcases/GP-REQ-wave7-gaps.json"
_SPEC_ROW = re.compile(r"^\| GP-(FR|UX|API)-(\d{3}) \|([^|]*)\|", re.MULTILINE)
_TEST_ROW = re.compile(r"GP-(FR|API|UX)-(\d{3})((?:/\d{3})*)")

#: The SHOULD rows of wave 7 (plan section 3 "Welle 7", WP 7.1-7.24; spec section 34 row 7), with the part a row
#: contributes when only part of it is SHOULD. Not here, with the plan's reason: GP-FR-161-168 (wave 8 per section
#: 34), GP-FR-078/115/116/118 (COULD), GP-FR-086/087 (suggestions and template tasks hang on ADR-008 phase 2 / wave 8).
WAVE7_ROWS: dict[str, str] = {
    "GP-FR-012": "SHOULD part: snap to edges/corners of neighbouring objects",
    "GP-FR-025": "SHOULD part: multi-duplicate (count, direction, spacing, naming scheme)",
    "GP-FR-029": "align / distribute a multi-selection",
    "GP-FR-031": "SHOULD part: layer switches for zones and 'last watered'",
    "GP-FR-033": "background underlay with two-point calibration",
    "GP-FR-043": "height of raised bed / planter, pre-filled from the template",
    "GP-FR-044": "bed templates (tenant + system)",
    "GP-FR-045": "standard sizes as quick pick",
    "GP-FR-110": "irrigation zones: CRUD, assign beds, zone outline on the plan",
    "GP-FR-111": "water source object with capacity and last refill",
    "GP-FR-112": "last watering per zone and bed",
    "GP-FR-113": "zone demand from REQ-037 (net litres, gross with efficiency)",
    "GP-FR-114": "zone consumption (logged + actuator runtime x flow rate)",
    "GP-FR-117": "watering round of a zone (allocated total)",
    "GP-FR-119": "conflict hint zone type vs bed irrigation system",
    "GP-FR-148": "snapshots before replace, list and restore",
    "GP-FR-158": "sun profile (sun window chips)",
    "GP-FR-159": "foliage shade in summer",
    "GP-FR-169": "map layers sun / moisture-drainage / frost risk",
    "GP-FR-171": "new season from the previous year",
    "GP-FR-172": "partial export and import target",
    "GP-UX-004": "auto-save option, paused on conflict",
    "GP-UX-014": "mini-map",
    "GP-UX-031": "layer 'last watered'",
    "GP-UX-051": "import wizard (delivered with WP 5.3, listed in section 34 wave 7)",
    "GP-UX-057": "field-mode bed sheet with sun / moisture chips",
    "GP-UX-061": "plant-state layer and 'needs attention' filter",
    "GP-API-050": "irrigation zone CRUD",
    "GP-API-051": "replace the beds of a zone",
    "GP-API-052": "zone status",
    "GP-API-053": "log a watering round (allocation by_area | equal)",
    "GP-API-057": "new season from the previous year",
    "GP-API-058": "list plan snapshots",
    "GP-API-059": "restore a plan snapshot",
    "GP-API-060": "set / remove the plan underlay",
    "GP-API-061": "bed template catalogue CRUD",
    "GP-API-062": "place a bed from a template",
}


def spec_ids() -> dict[str, str]:
    """``{id: level}`` for every acceptance criterion of the spec (``I``/``E``/``U`` ...)."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    return {
        m.group(1): m.group(2).split(",")[0].strip()
        for m in _SPEC_ID.finditer(spec.read_text(encoding="utf-8"))
    }


def _tier(rel: Path) -> str | None:
    parts, name = rel.parts, rel.name
    if (
        parts[:3] == ("src", "backend", "tests")
        and re.fullmatch(r"test_.*\.py", name)
        and name not in _SELF
    ):
        return next(
            (t for t in ("guards", "unit", "api", "integration") if t in parts[3:-1]),
            "backend",
        )
    if parts[:3] == ("src", "frontend", "src") and re.search(r"\.test\.tsx?$", name):
        return "frontend"
    if parts[:2] == ("tests", "e2e") and re.fullmatch(r"test_.*\.py", name):
        return "e2e"
    if parts[:1] in {("tests",), ("spec",)} and name.endswith(".feature"):
        return "e2e"
    return None


def scan() -> dict[str, dict[str, set[str]]]:
    """``{id: {tier: {file, ...}}}`` read from the tests."""
    found: dict[str, dict[str, set[str]]] = {}
    for base in (
        "src/backend/tests",
        "src/frontend/src",
        "tests/e2e",
        "spec/e2e-testcases",
    ):
        for path in sorted((ROOT / base).rglob("*")):
            rel = path.relative_to(ROOT)
            if not path.is_file() or _SKIP_DIRS & set(rel.parts[:-1]):
                continue
            tier = _tier(rel)
            if tier is None:
                continue
            for match in _TEST_ID.finditer(
                path.read_text(encoding="utf-8", errors="replace")
            ):
                number = match.group(1) or match.group(2)
                found.setdefault(number, {}).setdefault(tier, set()).add(rel.as_posix())
    return found


def load_gaps() -> dict[str, dict[str, str]]:
    return json.loads(GAPS.read_text(encoding="utf-8")) if GAPS.exists() else {}


def render(
    ids: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, str]],
) -> str:
    lines = [
        "# REQ-053 acceptance matrix GP-ACC <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "Source of the ids: `spec/req/REQ-053_*.md` section 30. Source of the tests: the id (`GP-ACC-nnn`, or",
        "`gp_acc_nnn` in a Python test name) in a test file; see `scripts/gp_acc_matrix.py`. A reference proves",
        "that a test claims the criterion; whether it proves it completely stays a review question.",
        "Honest gaps (no test yet) are listed in `GP-ACC-gaps.json` with a reason and an issue.",
        "",
    ]
    covered = [i for i in ids if i in found]
    gap_ids = [i for i in ids if i not in found]
    lines += [
        f"**{len(covered)} of {len(ids)} criteria covered, {len(gap_ids)} listed as gap.**",
        "",
    ]
    lines += ["| GP-ACC | Level | Tiers | Tests |", "|---|---|---|---|"]
    for number, level in ids.items():
        tiers = found.get(number, {})
        if tiers:
            tier_cell = ", ".join(sorted(tiers))
            files = "<br>".join(
                f"`{f}`" for t in sorted(tiers) for f in sorted(tiers[t])
            )
        else:
            gap = gaps.get(number, {})
            tier_cell = "**GAP**"
            files = f"{gap.get('reason', 'no test')} (#{gap.get('issue', '?')})"
        lines.append(f"| GP-ACC-{number} | {level} | {tier_cell} | {files} |")
    return "\n".join(lines) + "\n"


def problems(
    ids: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, str]],
) -> list[str]:
    out = [
        f"GP-ACC-{i}: no test references it and it is not in GP-ACC-gaps.json"
        for i in ids
        if i not in found and i not in gaps
    ]
    out += [
        f"GP-ACC-{i}: in GP-ACC-gaps.json but a test now covers it - remove the entry"
        for i in gaps
        if i in found
    ]
    out += [
        f"GP-ACC-{i}: in GP-ACC-gaps.json but not in the spec"
        for i in gaps
        if i not in ids
    ]
    out += [
        f"GP-ACC-{i}: a gap entry needs a non-empty reason and an issue number"
        for i, g in gaps.items()
        if not (g.get("reason") and g.get("issue"))
    ]
    out += [
        f"GP-ACC-{i}: referenced by a test but not in the spec"
        for i in found
        if i not in ids
    ]
    return out


def spec_rows() -> dict[str, str]:
    """``{row id: priority}`` for every GP-FR / GP-UX / GP-API table row of the spec (``API`` for the API rows)."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    rows: dict[str, str] = {}
    for match in _SPEC_ROW.finditer(spec.read_text(encoding="utf-8")):
        kind, number, cell = match.groups()
        row = f"GP-{kind}-{number}"
        if row not in rows:
            rows[row] = "API" if kind == "API" else cell.strip().split(" ")[0]
    return rows


def _test_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for base in (
        "src/backend/tests",
        "src/frontend/src",
        "tests/e2e",
        "spec/e2e-testcases",
    ):
        for path in sorted((ROOT / base).rglob("*")):
            rel = path.relative_to(ROOT)
            if not path.is_file() or _SKIP_DIRS & set(rel.parts[:-1]):
                continue
            tier = _tier(rel)
            if tier is not None:
                files.append((rel, tier))
    return files


def scan_rows() -> dict[str, dict[str, set[str]]]:
    """``{row id: {tier: {file, ...}}}`` - the GP-FR / GP-API / GP-UX ids the tests carry (``a/b`` shorthand expanded)."""
    found: dict[str, dict[str, set[str]]] = {}
    for rel, tier in _test_files():
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        for match in _TEST_ROW.finditer(text):
            kind, first, rest = match.groups()
            for number in [first, *filter(None, rest.split("/"))]:
                found.setdefault(f"GP-{kind}-{number}", {}).setdefault(tier, set()).add(
                    rel.as_posix()
                )
    return found


def load_wave7_gaps() -> dict[str, dict[str, object]]:
    return (
        json.loads(WAVE7_GAPS.read_text(encoding="utf-8"))
        if WAVE7_GAPS.exists()
        else {}
    )


def render_wave7(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> str:
    lines = [
        "# REQ-053 wave 7 requirement matrix GP-FR / GP-API / GP-UX (SHOULD) <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "The rows are the SHOULD rows of wave 7 (`WAVE7_ROWS` in `scripts/gp_acc_matrix.py`: plan section 3",
        '"Welle 7", spec section 34); the priority is read from the spec table. A test claims a row by carrying',
        "its id (`GP-FR-117`, or the shorthand `GP-FR-112/117`). A reference proves that a test claims the row;",
        "whether it proves it completely stays a review question. Honest gaps are listed in",
        "`GP-REQ-wave7-gaps.json` with a reason and an issue: **GAP** (no test) or **partial** (the tests leave",
        "the named part unproven).",
        "",
    ]
    covered = [r for r in WAVE7_ROWS if r in found]
    partial = [r for r in covered if gaps.get(r, {}).get("partial")]
    uncovered = [r for r in WAVE7_ROWS if r not in found]
    lines += [
        (
            f"**{len(covered)} of {len(WAVE7_ROWS)} wave-7 rows have a test, {len(partial)} of them with a partial"
            f" gap; {len(uncovered)} without a test.**"
        ),
        "",
        "| Row | Prio | Scope | Tiers | Tests |",
        "|---|---|---|---|---|",
    ]
    for row, scope in WAVE7_ROWS.items():
        tiers = found.get(row, {})
        gap = gaps.get(row, {})
        if tiers:
            tier_cell = ", ".join(sorted(tiers))
            files = "<br>".join(
                f"`{f}`" for t in sorted(tiers) for f in sorted(tiers[t])
            )
            if gap.get("partial"):
                tier_cell += " (**partial**)"
                files += (
                    f"<br>**Partial gap:** {gap.get('reason')} (#{gap.get('issue')})"
                )
        else:
            tier_cell = "**GAP**"
            files = f"{gap.get('reason', 'no test')} (#{gap.get('issue', '?')})"
        lines.append(
            f"| {row} | {rows.get(row, '?')} | {scope} | {tier_cell} | {files} |"
        )
    return "\n".join(lines) + "\n"


def wave7_problems(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    out = [
        f"{r}: listed in WAVE7_ROWS but not a row of the spec"
        for r in WAVE7_ROWS
        if r not in rows
    ]
    out += [
        f"{r}: no test references it and it is not in GP-REQ-wave7-gaps.json"
        for r in WAVE7_ROWS
        if r not in found and r not in gaps
    ]
    out += [
        f"{r}: a full gap in GP-REQ-wave7-gaps.json but a test now covers it - remove it or mark it partial"
        for r, g in gaps.items()
        if r in found and not g.get("partial")
    ]
    out += [
        f"{r}: marked partial in GP-REQ-wave7-gaps.json but no test references it - it is a full gap"
        for r, g in gaps.items()
        if g.get("partial") and r not in found
    ]
    out += [
        f"{r}: in GP-REQ-wave7-gaps.json but not a wave-7 row"
        for r in gaps
        if r not in WAVE7_ROWS
    ]
    out += [
        f"{r}: a gap entry needs a non-empty reason and an issue number"
        for r, g in gaps.items()
        if not (g.get("reason") and g.get("issue"))
    ]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--write", action="store_true", help="regenerate the committed matrix"
    )
    parser.add_argument("--check", action="store_true", help="verify (the default)")
    args = parser.parse_args()
    ids, found, gaps = spec_ids(), scan(), load_gaps()
    rows, found_rows, wave7_gaps = spec_rows(), scan_rows(), load_wave7_gaps()
    outputs = (
        (MATRIX, render(ids, found, gaps)),
        (WAVE7_MATRIX, render_wave7(rows, found_rows, wave7_gaps)),
    )
    errors = problems(ids, found, gaps) + wave7_problems(rows, found_rows, wave7_gaps)
    for path, text in outputs:
        if args.write:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            errors.append(
                f"{path.relative_to(ROOT)} is stale - run: python3 scripts/gp_acc_matrix.py --write"
            )
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
