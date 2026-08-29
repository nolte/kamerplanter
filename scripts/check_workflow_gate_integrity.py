#!/usr/bin/env python3
"""Refuse a GitHub Actions gate that cannot fail.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_workflow_gate_integrity.py
    python3 scripts/check_workflow_gate_integrity.py --list   # name every site
    python3 scripts/check_workflow_gate_integrity.py --json   # machine-readable

**What it enforces.** NFR-018 §2: a check that cannot report a failure is
indistinguishable from one that is not running, and must not exist. The spec
says so and — §8, in its own words, the "unangenehme Pointe" — has no gate of
its own. This is that gate, in the minimal form the 2026-08-08 issue-pattern
audit asked for (measure P5.4). Cluster G is eighteen issues of checks that
reported green on nothing: #814 (a pre-commit hook printing ``Passed`` for a
check whose tool was absent), #828 (a required context that gated no test run),
the ZAP scaffold that echoed ``OK`` while scanning nothing.

Four shapes, all of which have occurred in this repository:

1. **``|| true`` in a ``run:`` step.** The step's verdict is discarded. Often
   correct — ``grep -c`` exits 1 on no match and a counting expression under
   ``set -e`` needs the guard — and that is exactly why it needs a reason
   rather than a ban: ``skaffold render … || true`` discarded a real render
   failure for months (see the header of ``skaffold-verify.yml``).

2. **``continue-on-error: true``.** The step or job cannot turn its check red.
   Legitimate for a *reporter* — a fork pull request's read-only token cannot
   create a check run, and the suite's own verdict is not that reporter's to
   give. Not legitimate for anything that measures.

3. **A job consuming ``needs.<x>.outputs`` without consulting
   ``needs.<x>.result``**, when its own ``if:`` overrides GitHub's dependency
   gating (``always()``, ``cancelled()``, ``failure()``). Without the override
   GitHub skips the dependent job when its dependency fails, and the shape is
   safe. *With* it, a failed or cancelled producer leaves every output an empty
   string, every comparison false, every step skipped — and a job whose steps
   are all skipped **reports success**. That is how ``lint-test-build (22)``
   would have gone green without tsc, ESLint, vitest or the build ever running;
   the comment in ``frontend.yml`` that describes the trap is the reason this
   third shape is checked at all.

4. **A comment on a line reached through a trailing ``\\``.** The ``#`` ends
   the logical line, so the command runs truncated at the previous argument and
   the next flag is executed as its own program. The step goes *red*, which
   looks self-reporting — but the truncated command is the one that writes the
   artefacts later steps gate on. ``security-nuclei-nightly.yml`` lost
   ``-tags``, ``-severity`` and both output flags this way; ``results.jsonl``
   and ``results.sarif`` were never written, so the SARIF upload
   (``if: hashFiles(...) != ''``) and the issue-opening step (an ``existsSync``
   early return) skipped silently for 22 consecutive nights, 2026-08-08 to
   2026-08-29 (#1010). Two inert gates behind one loud one.

**The escape hatch.** A site may stand by carrying a justification on its own
line or in the comment block directly above it::

    # gate-integrity-ok: grep -c exits 1 on no match; the count is the result
    hits=$(grep -c '^kind:' file || true)

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer. For shape 3 the marker goes in the comment block above the
job key, which is where this repository already explains its jobs.

**Best-effort, and deliberately so.** Shapes 1, 2 and 4 are found textually, so a
swallowed exit code spelled ``|| :`` or ``; true`` slips through; shape 3 reads
the parsed YAML but cannot see through a composite action or a reusable
workflow. A checker that tried to be exhaustive here would need a shell parser
and would still miss things, while its false positives got it switched off.
What it does guarantee is that the three shapes that have actually cost this
repository something cannot be *added* without somebody writing down why.

Standard library plus PyYAML — the same isolated pre-commit environment the
chart-digest hook uses, because the required ``static`` job runs on a bare
runner with none of the project's dependencies installed.

Traces to the 2026-08-08 issue-pattern audit, measure P5.4 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the workflows live, relative to the repository root.
DEFAULT_SCAN_ROOT = ".github/workflows"

#: The marker that exempts a site, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption.
JUSTIFICATION_MARKER = "# gate-integrity-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: A discarded exit code in a shell line.
SWALLOWED_EXIT = re.compile(r"\|\|\s*true\b")

#: ``continue-on-error: true`` at any indentation (job or step level).
CONTINUE_ON_ERROR = re.compile(r"^\s*continue-on-error:\s*true\s*$")

#: Expression functions that override GitHub's "skip me when my dependency
#: failed" behaviour. Their presence in a job-level ``if:`` is what turns a
#: missing ``needs.<x>.result`` check into a false green.
GATING_OVERRIDES = ("always()", "cancelled()", "failure()")

_NEEDS_OUTPUT = re.compile(r"needs\.([A-Za-z0-9_-]+)\.outputs\b")
_NEEDS_RESULT = re.compile(r"needs\.([A-Za-z0-9_*-]+)\.result\b")

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class WorkflowIntegrityCheckError(Exception):
    """A usage or environment problem — not a finding about the workflows."""


@dataclass(frozen=True)
class Finding:
    """One gate-integrity smell in one workflow file."""

    path: Path
    line: int
    kind: str
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


#: Human wording per finding kind, used in the report.
KIND_LABELS = {
    "swallowed_exit": "the step's exit code is discarded",
    "continue_on_error": "this cannot turn its check red",
    "unguarded_needs_output": "a failed dependency makes this job report success",
    "commented_continuation": "a comment ends this command early, so it runs truncated",
}


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the site on *line*, or ``None``.

    Accepted on the site's own line (trailing comment) and anywhere in the
    contiguous comment block directly above it. The block form matters here:
    this repository explains its jobs in a comment paragraph above the job key,
    and a marker is most useful inside the paragraph that already argues the
    point.
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


def _strip_comment(line: str) -> str:
    """Return the part of *line* before its first ``#``.

    Crude on purpose: a ``#`` inside a quoted string would truncate early, which
    can only ever *hide* a finding on that line, never invent one. The
    alternative — matching inside comments — reported the two ``|| true``
    occurrences that ``skaffold-verify.yml`` mentions in its own header while
    explaining that it removed them.
    """
    hash_index = line.find("#")
    return line if hash_index == -1 else line[:hash_index]


def _job_line(lines: list[str], name: str) -> int:
    """The 1-based line of the ``<name>:`` key in the ``jobs:`` mapping."""
    pattern = re.compile(rf"^\s{{2,4}}{re.escape(name)}:\s*$")
    for index, line in enumerate(lines, start=1):
        if pattern.match(line):
            return index
    return 1


def _strings(node: Any) -> list[str]:
    """Every string anywhere inside a parsed YAML node."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for value in node.values() for text in _strings(value)]
    if isinstance(node, list):
        return [text for value in node for text in _strings(value)]
    return []


def scan_text(path: Path, lines: list[str]) -> list[Finding]:
    """Find the two textual shapes: swallowed exits and continue-on-error."""
    findings: list[Finding] = []
    for number, line in enumerate(lines, start=1):
        code = _strip_comment(line)
        if SWALLOWED_EXIT.search(code):
            findings.append(
                Finding(
                    path=path,
                    line=number,
                    kind="swallowed_exit",
                    detail=code.strip(),
                    justification=justification_for(lines, number),
                )
            )
        if CONTINUE_ON_ERROR.match(code):
            findings.append(
                Finding(
                    path=path,
                    line=number,
                    kind="continue_on_error",
                    detail=code.strip(),
                    justification=justification_for(lines, number),
                )
            )
    return findings


def scan_continuations(path: Path, lines: list[str]) -> list[Finding]:
    """Find a command truncated by a comment on one of its continued lines.

    A ``#`` reached through a trailing ``\\`` ends the logical line: everything
    after it is a comment, and the *following* lines become separate commands.
    The shell runs the command truncated at the previous argument and then tries
    to execute the next flag as a program.

    Why this belongs in a gate-integrity check rather than in a shell linter:
    the visible symptom is a red step, which looks self-reporting — but the
    truncated command is the one that produces the artefacts the *later* steps
    gate on. ``security-nuclei-nightly.yml`` lost ``-tags``, ``-severity`` and
    both ``-o``/``-sarif-export`` this way, so ``results.jsonl`` and
    ``results.sarif`` were never written, and the two steps downstream —
    ``if: hashFiles('results.sarif') != ''`` and an ``existsSync`` early
    return — skipped silently for 22 consecutive nights while the scan appeared
    to run. Two inert gates, which is exactly NFR-018 §2.

    Detection is on the *code* part of each line, so a documentation block whose
    own comment line happens to end in a backslash is not a finding: stripping
    the comment leaves no trailing continuation to follow.
    """
    findings: list[Finding] = []
    for index, line in enumerate(lines):
        if not _strip_comment(line).rstrip().endswith("\\"):
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if not following.lstrip().startswith("#"):
            continue
        findings.append(
            Finding(
                path=path,
                line=index + 2,
                kind="commented_continuation",
                detail=following.strip(),
                justification=justification_for(lines, index + 2),
            )
        )
    return findings


def scan_needs(path: Path, lines: list[str], document: Any) -> list[Finding]:
    """Find jobs that read a dependency's outputs without reading its result.

    Only jobs whose own ``if:`` overrides GitHub's dependency gating are
    considered — see the module docstring for why the others are safe.
    """
    if not isinstance(document, dict):
        return []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []

    findings: list[Finding] = []
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        condition = job.get("if")
        condition_text = condition if isinstance(condition, str) else ""
        if not any(override in condition_text for override in GATING_OVERRIDES):
            continue

        texts = _strings(job)
        consumed = {match for text in texts for match in _NEEDS_OUTPUT.findall(text)}
        checked = {match for text in texts for match in _NEEDS_RESULT.findall(text)}
        if "*" in checked:
            continue
        unguarded = sorted(consumed - checked)
        if not unguarded:
            continue

        line = _job_line(lines, str(name))
        findings.append(
            Finding(
                path=path,
                line=line,
                kind="unguarded_needs_output",
                detail=f"job '{name}' reads needs.{', needs.'.join(unguarded)}.outputs, never .result",
                justification=justification_for(lines, line),
            )
        )
    return findings


def scan_file(path: Path) -> list[Finding]:
    """Every finding in one workflow file."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowIntegrityCheckError(f"cannot read {path}: {exc}") from exc
    lines = source.splitlines()
    try:
        document = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise WorkflowIntegrityCheckError(f"cannot parse {path}: {exc}") from exc

    findings = [
        *scan_text(path, lines),
        *scan_continuations(path, lines),
        *scan_needs(path, lines, document),
    ]
    return sorted(findings, key=lambda finding: (finding.line, finding.kind))


def collect(scan_root: Path) -> list[Finding]:
    """Every finding below *scan_root*, justified or not."""
    if not scan_root.exists():
        raise WorkflowIntegrityCheckError(f"scan root does not exist: {scan_root}")
    paths = sorted(
        path for path in scan_root.rglob("*") if path.suffix in {".yml", ".yaml"}
    )
    if not paths:
        raise WorkflowIntegrityCheckError(f"no workflow files under {scan_root}")
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return findings


def report(findings: list[Finding], *, list_all: bool, as_json: bool) -> int:
    """Print the outcome and return the process exit code."""
    unjustified = [finding for finding in findings if not finding.justified]
    justified = [finding for finding in findings if finding.justified]

    if as_json:
        print(
            json.dumps(
                {
                    "sites": len(findings),
                    "justified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                            "reason": finding.justification,
                        }
                        for finding in justified
                    ],
                    "unjustified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                        }
                        for finding in unjustified
                    ],
                },
                indent=2,
            )
        )
        return EXIT_DEFECTS if unjustified else EXIT_OK

    if unjustified:
        print(
            f"check_workflow_gate_integrity: {len(unjustified)} site(s) where a check cannot fail\n"
        )
        for finding in unjustified:
            print(f"  {finding.relative()}:{finding.line}: {KIND_LABELS[finding.kind]}")
            print(f"      {finding.detail}")
        print(
            "\nNFR-018 §2: a check that cannot report a failure is indistinguishable from\n"
            "one that is not running. Either restore the verdict, or say — where it\n"
            "stands, on the same line or in the comment block directly above it — why the\n"
            "discarded outcome is not a verdict:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <why this cannot hide a failure>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    print(
        f"check_workflow_gate_integrity: OK — {len(justified)} justified site(s), no unexplained "
        "swallowed verdict."
    )
    if list_all:
        for finding in justified:
            print(
                f"  {finding.relative()}:{finding.line} [{finding.kind}]: {finding.justification}"
            )
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every swallowed verdict carries a reason, 1 when at least one
        does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_workflow_gate_integrity.py",
        description=(
            "Refuse a GitHub Actions gate that cannot fail (NFR-018 §2): a discarded exit "
            "code, continue-on-error, or a job reading a dependency's outputs without its "
            f"result. A site may stand by carrying a '{JUSTIFICATION_MARKER} <reason>' comment."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the workflow directory to scan (default: {DEFAULT_SCAN_ROOT})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every justified site when the check passes",
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
        findings = collect(scan_root)
    except WorkflowIntegrityCheckError as exc:
        print(f"check_workflow_gate_integrity: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(findings, list_all=args.list_all, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
