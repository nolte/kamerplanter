#!/usr/bin/env python3
"""Ratchet mypy's findings on ``src/backend/app`` against a recorded baseline (#2169).

Runs in the ``lint-test`` job of Backend CI (``task typecheck:backend``), as a
local pre-commit hook, and can be invoked directly from ``src/backend``::

    uv run --locked --extra dev python ../../scripts/check_mypy_ratchet.py
    uv run --locked --extra dev python ../../scripts/check_mypy_ratchet.py --tighten
    uv run --locked --extra dev python ../../scripts/check_mypy_ratchet.py --list

**Why it exists.** ``[tool.mypy]`` in ``src/backend/pyproject.toml`` has said
``strict = true`` since the first commit, and nothing ever ran it. Measured on
2026-10-10 with the locked toolchain (mypy 2.4.0): 3452 errors in 483 files.
Among them, since July, was a ``[call-arg]`` error at exactly the six
retention-task call sites that never ran (#2150) — the defect was in plain sight
for three months because a report nobody gates on is a report nobody reads.

**Why a ratchet and not a big bang.** 3452 findings cannot be fixed in one
change, and a gate that is red on ``develop`` from day one is ignored from day
one. The baseline freezes the debt that exists and refuses any that is new.

**The unit is (file, error code), not the line.** A finding is counted per file
and per mypy error code. Line numbers are deliberately not part of the key: an
edit above a known finding would otherwise move it and turn the gate red for a
change that added nothing. A file that has no entry in the baseline is held to
zero, so every new module has to be clean.

**Two rules, chosen by the error code.**

* :data:`EXACT_CODES` — the classes that mean *this call or attribute access
  cannot work at runtime*: ``call-arg`` (#2150), ``name-defined``,
  ``attr-defined``, ``call-overload``. Their count per file MUST equal the
  baseline. Growth is red, and so is a drop: a fixed finding whose entry is not
  removed in the same change would silently re-permit the next one in that file
  (NFR-018 §2.5, an exception register must be able to age). ``--tighten``
  writes the lower number.
* every other code — no-growth. A rise is red; a drop is green and printed as
  headroom, so a refactoring that happens to fix three ``union-attr`` findings is
  not taxed with a baseline edit (NFR-018 §2.1, the #973 merge-conflict lesson).

**Why the baseline is a versioned file, not computed (NFR-018 §2.1).** §2.1
prefers a ceiling computed from the tree. A mypy ratchet has no such reference
point: the count *is* the tree, and the lane runs on ``push`` and
``pull_request`` alike, so a merge-base re-run would double the job and still
have no answer on ``develop``. The file is the explicit operator decision of
#2169 ("eine Baseline/Ratchet-Datei als Gate"). The no-growth half keeps the
§2.1 property that cleaning up never forces an edit; only the narrow
:data:`EXACT_CODES` class trades that for aging.

**The gate cannot be green without measuring (NFR-018 §2).**

* mypy exit status 2 (a crash or a blocking error such as a syntax error) is red.
* mypy's own summary line is parsed and MUST agree with the number of findings
  this script parsed — a reporting format the parser no longer understands would
  otherwise read as "zero findings" (the measuring tool has the gap, not the
  guard).
* "checked 0 source files" is red.
* a baseline entry for a file that no longer exists is red (stale).

**What a green run does NOT mean.** It does not mean ``app/`` type-checks — read
the totals it prints. It does not cover a finding silenced with
``# type: ignore[...]``; those stay visible in review. And the counts are only
comparable under the locked toolchain: a different mypy or a different set of
installed stubs moves them, which is why every entry point runs through
``uv run --locked --extra dev`` and the baseline records the mypy version it was
written with.

Standard library only; mypy itself runs as ``sys.executable -m mypy`` so it is
the interpreter's (the locked environment's) mypy and configuration.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKEND_DIR = REPO_ROOT / "src" / "backend"
BASELINE_NAME = "mypy-ratchet-baseline.json"
TARGET = "app"
BASELINE_FORMAT = 1

#: Error codes whose count per file must match the baseline exactly. ``call-arg``
#: is mandatory (#2150, operator decision on #2169): it is the class that hid six
#: never-running retention tasks for three months.
EXACT_CODES: frozenset[str] = frozenset({"call-arg", "name-defined", "attr-defined", "call-overload"})

EXIT_OK = 0
EXIT_RED = 1
EXIT_USAGE = 2

# `app/x.py:12: error: Message  [code]` — with --no-pretty every finding is one
# line. The column part is optional so --show-column-numbers does not break it.
_FINDING = re.compile(
    r"^(?P<path>[^:\n]+\.pyi?):(?P<line>\d+)(?::\d+)?: error: (?P<message>.*?)\s+\[(?P<code>[a-z0-9-]+)\]$"
)
_SUMMARY_FOUND = re.compile(r"^Found (?P<errors>\d+) errors? in \d+ files? \(checked (?P<checked>\d+) source files?\)$")
_SUMMARY_CLEAN = re.compile(r"^Success: no issues found in (?P<checked>\d+) source files?$")

Key = tuple[str, str]


class RatchetError(Exception):
    """The gate could not measure — always red, never a pass."""


@dataclass(frozen=True)
class Finding:
    """One mypy error."""

    path: str
    line: int
    code: str
    message: str

    @property
    def key(self) -> Key:
        return (self.path, self.code)

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.message}  [{self.code}]"


@dataclass(frozen=True)
class MypyRun:
    """The parsed result of one mypy invocation."""

    findings: tuple[Finding, ...]
    checked_files: int
    mypy_version: str


@dataclass(frozen=True)
class Baseline:
    """The recorded per-(file, code) counts."""

    counts: Mapping[Key, int]
    mypy_version: str


@dataclass
class Verdict:
    """The comparison of one run against the baseline."""

    growth: list[tuple[Key, int, int]] = field(default_factory=list)
    stale: list[tuple[Key, int, int]] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    headroom: list[tuple[Key, int, int]] = field(default_factory=list)

    @property
    def red(self) -> bool:
        return bool(self.growth or self.stale or self.missing_files)


# ── Measuring ────────────────────────────────────────────────────────────────


def parse_mypy_output(output: str) -> tuple[list[Finding], int]:
    """Parse mypy's ``--no-pretty`` output into findings and the checked-file count.

    Args:
        output: Combined stdout of a mypy run, summary line included.

    Returns:
        The findings and the number of source files mypy reports having checked.

    Raises:
        RatchetError: When the summary line is missing or disagrees with the parsed
            findings — the parser would otherwise report a vacuous zero.
    """
    findings: list[Finding] = []
    summary_errors: int | None = None
    checked: int | None = None
    for raw in output.splitlines():
        line = raw.rstrip()
        match = _FINDING.match(line)
        if match:
            findings.append(
                Finding(
                    path=match["path"].replace("\\", "/"),
                    line=int(match["line"]),
                    code=match["code"],
                    message=match["message"],
                )
            )
            continue
        found = _SUMMARY_FOUND.match(line)
        if found:
            summary_errors, checked = int(found["errors"]), int(found["checked"])
            continue
        clean = _SUMMARY_CLEAN.match(line)
        if clean:
            summary_errors, checked = 0, int(clean["checked"])
    if summary_errors is None or checked is None:
        raise RatchetError("mypy printed no summary line; refusing to read its output as 'no findings'")
    if summary_errors != len(findings):
        raise RatchetError(
            f"mypy reports {summary_errors} errors but {len(findings)} were parsed — the output format "
            "changed and this gate would under-count; fix _FINDING before trusting a green run"
        )
    if checked == 0:
        raise RatchetError("mypy checked 0 source files; an empty input is not a passed check (NFR-018 §2)")
    return findings, checked


def run_mypy(backend_dir: Path, target: str = TARGET) -> MypyRun:
    """Run mypy over ``target`` from ``backend_dir`` with that directory's configuration."""
    if not (backend_dir / target).is_dir():
        raise RatchetError(f"{backend_dir / target} does not exist; nothing to check is not a pass")
    version_proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [sys.executable, "-m", "mypy", "--version"], capture_output=True, text=True, check=False, timeout=60
    )
    if version_proc.returncode != 0:
        raise RatchetError(f"mypy is not importable from {sys.executable}: {version_proc.stderr.strip()}")
    version = version_proc.stdout.split()[1] if len(version_proc.stdout.split()) > 1 else "unknown"
    proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [
            sys.executable,
            "-m",
            "mypy",
            target,
            "--no-pretty",
            "--no-color-output",
            "--show-error-codes",
            "--error-summary",
        ],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=1800,
    )
    if proc.returncode not in (0, 1):
        raise RatchetError(
            f"mypy exited {proc.returncode} (crash or blocking error):\n{proc.stdout}{proc.stderr}".rstrip()
        )
    findings, checked = parse_mypy_output(proc.stdout)
    if proc.returncode == 1 and not findings:
        raise RatchetError(f"mypy exited 1 without a parsable finding:\n{proc.stdout}{proc.stderr}".rstrip())
    return MypyRun(findings=tuple(findings), checked_files=checked, mypy_version=version)


# ── Baseline ─────────────────────────────────────────────────────────────────


def count_findings(findings: Iterable[Finding]) -> Counter[Key]:
    return Counter(finding.key for finding in findings)


def load_baseline(path: Path) -> Baseline:
    """Read and validate the baseline file.

    Raises:
        RatchetError: On a missing file, a wrong format, or a non-positive count —
            a malformed baseline must not degrade into "everything is new" or
            "nothing is recorded".
    """
    if not path.is_file():
        raise RatchetError(f"baseline {path} is missing; record one with --record")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RatchetError(f"baseline {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("format") != BASELINE_FORMAT:
        raise RatchetError(f"baseline {path} has no 'format': {BASELINE_FORMAT} header")
    entries = data.get("files")
    if not isinstance(entries, dict):
        raise RatchetError(f"baseline {path} has no 'files' object")
    counts: dict[Key, int] = {}
    for file_path, codes in entries.items():
        if not isinstance(codes, dict) or not codes:
            raise RatchetError(f"baseline entry {file_path!r} must map error codes to counts")
        for code, count in codes.items():
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise RatchetError(f"baseline entry {file_path!r} [{code}] must be a positive integer, got {count!r}")
            counts[(file_path, code)] = count
    return Baseline(counts=counts, mypy_version=str(data.get("mypy_version", "unknown")))


def dump_baseline(counts: Mapping[Key, int], mypy_version: str) -> str:
    """Serialise counts deterministically (sorted, one file per object)."""
    files: dict[str, dict[str, int]] = {}
    for (file_path, code), count in sorted(counts.items()):
        if count > 0:
            files.setdefault(file_path, {})[code] = count
    payload = {
        "format": BASELINE_FORMAT,
        "comment": (
            "mypy ratchet baseline for src/backend/app (#2169), written by scripts/check_mypy_ratchet.py. "
            "Do not raise a count by hand without saying why in the pull request."
        ),
        "mypy_version": mypy_version,
        "total": sum(c for c in counts.values() if c > 0),
        "files": files,
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def tighten(baseline: Mapping[Key, int], current: Mapping[Key, int], exists: Callable[[str], bool]) -> dict[Key, int]:
    """Lower every entry to the current count; drop zeroes and vanished files. Never raises a count or adds a key."""
    return {
        key: min(count, current.get(key, 0))
        for key, count in baseline.items()
        if exists(key[0]) and min(count, current.get(key, 0)) > 0
    }


# ── Comparing ────────────────────────────────────────────────────────────────


def compare(current: Mapping[Key, int], baseline: Mapping[Key, int], exists: Callable[[str], bool]) -> Verdict:
    """Hold the current counts against the baseline under the two rules."""
    verdict = Verdict()
    for key in sorted(set(current) | set(baseline)):
        now, recorded = current.get(key, 0), baseline.get(key, 0)
        if now > recorded:
            verdict.growth.append((key, recorded, now))
        elif now < recorded:
            if key[1] in EXACT_CODES:
                verdict.stale.append((key, recorded, now))
            else:
                verdict.headroom.append((key, recorded, now))
    verdict.missing_files = sorted({file_path for file_path, _ in baseline if not exists(file_path)})
    return verdict


def report(verdict: Verdict, run: MypyRun, baseline: Baseline, findings_by_key: Mapping[Key, list[Finding]]) -> str:
    lines: list[str] = []
    total_now = len(run.findings)
    total_recorded = sum(baseline.counts.values())
    lines.append(
        f"mypy ratchet (src/backend/{TARGET}): {total_now} findings now, {total_recorded} recorded, "
        f"{run.checked_files} source files checked, mypy {run.mypy_version}"
    )
    if run.mypy_version != baseline.mypy_version:
        lines.append(
            f"  note: baseline was recorded with mypy {baseline.mypy_version}; a toolchain change moves the counts"
        )
    if verdict.growth:
        lines.append("")
        lines.append("NEW findings (red — fix them; a file without an entry is held to zero):")
        for (file_path, code), recorded, now in verdict.growth:
            lines.append(f"  {file_path} [{code}]: {recorded} -> {now}")
            lines.extend(f"      {finding.render()}" for finding in findings_by_key.get((file_path, code), []))
    if verdict.stale:
        lines.append("")
        lines.append(
            "FIXED findings of an exact-match class whose baseline entry was not lowered (red — run --tighten "
            "so the entry cannot re-permit the next one, NFR-018 §2.5):"
        )
        lines.extend(f"  {fp} [{code}]: {recorded} -> {now}" for (fp, code), recorded, now in verdict.stale)
    if verdict.missing_files:
        lines.append("")
        lines.append(
            "Baseline entries for files that no longer exist (red — run --tighten; on a rename move the entry):"
        )
        lines.extend(f"  {fp}" for fp in verdict.missing_files)
    if verdict.headroom:
        gained = sum(recorded - now for _, recorded, now in verdict.headroom)
        lines.append("")
        lines.append(
            f"Headroom: {gained} recorded findings no longer occur ({len(verdict.headroom)} entries). Green; "
            "--tighten records it, nothing requires it."
        )
    lines.append("")
    lines.append("RED" if verdict.red else "GREEN")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────


def _group(findings: Iterable[Finding]) -> dict[Key, list[Finding]]:
    grouped: dict[Key, list[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.key, []).append(finding)
    return grouped


def main(argv: list[str] | None = None) -> int:
    """Run the ratchet. 0 green, 1 red, 2 when the gate could not measure."""
    parser = argparse.ArgumentParser(
        prog="check_mypy_ratchet.py",
        description="Ratchet mypy's findings on src/backend/app per (file, error code) against a baseline (#2169).",
    )
    parser.add_argument("--backend-dir", type=Path, default=DEFAULT_BACKEND_DIR, help="directory mypy runs from")
    parser.add_argument("--baseline", type=Path, help=f"baseline file (default: <backend-dir>/{BASELINE_NAME})")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tighten", action="store_true", help="lower entries to the current counts; never raises one")
    mode.add_argument(
        "--record",
        action="store_true",
        help="overwrite the baseline with the current counts (bootstrap / deliberate toolchain bump only)",
    )
    parser.add_argument("--list", action="store_true", dest="list_all", help="print every current finding")
    args = parser.parse_args(argv)

    backend_dir: Path = args.backend_dir.resolve()
    baseline_path: Path = args.baseline or backend_dir / BASELINE_NAME

    def exists(file_path: str) -> bool:
        return (backend_dir / file_path).is_file()

    try:
        run = run_mypy(backend_dir)
        current = count_findings(run.findings)
        if args.record:
            baseline_path.write_text(dump_baseline(current, run.mypy_version), encoding="utf-8")
            print(f"recorded {len(run.findings)} findings in {len(current)} entries to {baseline_path}")
            print("A recorded baseline accepts every current finding — say why in the pull request.")
            return EXIT_OK
        baseline = load_baseline(baseline_path)
    except RatchetError as exc:
        print(f"check_mypy_ratchet: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.list_all:
        for finding in run.findings:
            print(finding.render())

    if args.tighten:
        lowered = tighten(baseline.counts, current, exists)
        baseline_path.write_text(dump_baseline(lowered, run.mypy_version), encoding="utf-8")
        removed = sum(baseline.counts.values()) - sum(lowered.values())
        print(f"tightened {baseline_path}: {removed} recorded findings removed")
        baseline = Baseline(counts=lowered, mypy_version=run.mypy_version)

    verdict = compare(current, baseline.counts, exists)
    print(report(verdict, run, baseline, _group(run.findings)))
    return EXIT_RED if verdict.red else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
