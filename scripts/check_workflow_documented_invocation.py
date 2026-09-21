#!/usr/bin/env python3
"""Refuse a workflow whose documented invocation the configuration does not carry.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_workflow_documented_invocation.py
    python3 scripts/check_workflow_documented_invocation.py --list
    python3 scripts/check_workflow_documented_invocation.py --json

**What it enforces.** NFR-018 §1: prose that describes a mechanism the
configuration does not carry. #1607 is the worked example. Two workflows told
their reader, in their own headers, to "label a pull request ``security-scan``"
to get a pre-merge scan. The label did not exist, so nobody could; and because
``pull_request: types: [labeled]`` cannot be filtered by label name at the
``on:`` level, the selection sat in the job's ``if:`` and every OTHER label
queued a run that immediately skipped — 300 runs per workflow over the week to
2026-09-20, none of which executed.

**Three shapes, none of them tied to that one site.** The check knows nothing
about ZAP, Nuclei, or a label called ``security-scan``. It compares what a
workflow SAYS about how to invoke it against what its ``on:`` block and its
body actually provide, for every workflow in the tree:

1. **A referenced input that is not declared.** An expression
   ``inputs.<name>`` or ``github.event.inputs.<name>`` outside a comment, with
   no matching key under ``on.workflow_dispatch.inputs`` or
   ``on.workflow_call.inputs``. GitHub does not error on this: the expression
   renders as the empty string, so the input is *accepted and silently
   ignored* — the same class as the label nobody could apply, one level down.

2. **A declared input that nothing reads.** A key under
   ``on.workflow_dispatch.inputs`` that appears nowhere in the workflow body.
   It shows up in the "Run workflow" dialog, invites a value, and changes
   nothing. The dialog is prose too.

3. **A ``gh workflow run`` example in a comment that does not work.** Every
   such example is an instruction, and an instruction is exactly what #1607
   got wrong. The named workflow file must exist, it must declare
   ``workflow_dispatch``, and every ``-f``/``--field``/``-F`` key in the
   example must be one of that workflow's declared inputs.

**What it deliberately does NOT do.** It does not verify that a documented
invocation is the RIGHT one, that a label named in prose exists (that lives in
GitHub, not in this tree — ``.github/settings.yml`` declares only the labels
this repository adds on top of the commons), or that a scan is worth running.
It checks reachability, which is mechanical, and leaves judgement to review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = ".github/workflows"

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

# `inputs.x` and `github.event.inputs.x`, only inside a `${{ }}` expression —
# a bare `inputs.` in a shell string is not a workflow expression.
_EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
_INPUT_REF = re.compile(r"\b(?:github\.event\.)?inputs\.([A-Za-z_][A-Za-z0-9_-]*)")
_GH_RUN = re.compile(r"gh\s+workflow\s+run\s+(\S+\.ya?ml)(.*)")
_GH_FIELD = re.compile(r"(?:-f|-F|--field|--raw-field)[= ]\s*([A-Za-z_][A-Za-z0-9_-]*)=")


class DocumentedInvocationCheckError(Exception):
    """The check could not run — a usage error, never a finding."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "rule": self.rule, "message": self.message}


@dataclass(frozen=True)
class Workflow:
    path: Path
    text: str
    declared_inputs: frozenset[str]
    has_dispatch: bool

    @property
    def body_lines(self) -> list[tuple[int, str]]:
        """Lines that are not whole-line YAML comments, 1-based."""
        return [
            (n, line)
            for n, line in enumerate(self.text.splitlines(), start=1)
            if line.lstrip()[:1] != "#"
        ]

    @property
    def comment_lines(self) -> list[tuple[int, str]]:
        """Whole-line YAML comments with their marker stripped, 1-based."""
        out: list[tuple[int, str]] = []
        for n, line in enumerate(self.text.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped[:1] == "#":
                out.append((n, stripped.lstrip("#").strip()))
        return out


def _declared_inputs(parsed: object) -> tuple[frozenset[str], bool]:
    if not isinstance(parsed, dict):
        return frozenset(), False
    # YAML 1.1 reads a bare `on:` key as the boolean True.
    on = parsed.get("on", parsed.get(True))
    if not isinstance(on, dict):
        return frozenset(), False
    names: set[str] = set()
    for trigger in ("workflow_dispatch", "workflow_call"):
        block = on.get(trigger)
        if isinstance(block, dict) and isinstance(block.get("inputs"), dict):
            names.update(block["inputs"])
    return frozenset(names), "workflow_dispatch" in on


def load(path: Path) -> Workflow:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced by actionlint too
        raise DocumentedInvocationCheckError(f"{path}: not valid YAML: {exc}") from exc
    declared, has_dispatch = _declared_inputs(parsed)
    return Workflow(path=path, text=text, declared_inputs=declared, has_dispatch=has_dispatch)


def _rel(path: Path, scan_root: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path.relative_to(scan_root.parent))


def collect(scan_root: Path) -> list[Finding]:
    if not scan_root.is_dir():
        raise DocumentedInvocationCheckError(f"not a directory: {scan_root}")

    workflows = {p.name: load(p) for p in sorted(scan_root.glob("*.y*ml"))}
    findings: list[Finding] = []

    for wf in workflows.values():
        rel = _rel(wf.path, scan_root)
        referenced: dict[str, int] = {}

        # Shape 1 — a referenced input that is not declared.
        for line_no, line in wf.body_lines:
            for expression in _EXPRESSION.findall(line):
                for name in _INPUT_REF.findall(expression):
                    referenced.setdefault(name, line_no)
                    if name not in wf.declared_inputs:
                        findings.append(
                            Finding(
                                rel,
                                line_no,
                                "undeclared-input",
                                f"`inputs.{name}` is read but no trigger declares it; "
                                f"the expression renders empty, so the value is accepted "
                                f"and silently ignored.",
                            )
                        )

        # Shape 2 — a declared input that nothing reads.
        for name in sorted(wf.declared_inputs):
            if name not in referenced:
                findings.append(
                    Finding(
                        rel,
                        0,
                        "unread-input",
                        f"input `{name}` is offered by the Run-workflow dialog but read "
                        f"nowhere in this workflow.",
                    )
                )

        # Shape 3 — a `gh workflow run` example that does not work.
        for line_no, example in _joined_comment_examples(wf):
            match = _GH_RUN.search(example)
            if match is None:
                continue
            target_name = Path(match.group(1)).name
            target = workflows.get(target_name)
            if target is None:
                findings.append(
                    Finding(
                        rel,
                        line_no,
                        "documented-invocation",
                        f"documents `gh workflow run {target_name}`, but no such "
                        f"workflow exists in {_rel(scan_root, scan_root)}.",
                    )
                )
                continue
            if not target.has_dispatch:
                findings.append(
                    Finding(
                        rel,
                        line_no,
                        "documented-invocation",
                        f"documents `gh workflow run {target_name}`, but that workflow "
                        f"declares no `workflow_dispatch` trigger.",
                    )
                )
                continue
            for field in _GH_FIELD.findall(match.group(2)):
                if field not in target.declared_inputs:
                    findings.append(
                        Finding(
                            rel,
                            line_no,
                            "documented-invocation",
                            f"the documented invocation passes `-f {field}=`, which "
                            f"{target_name} does not declare as an input.",
                        )
                    )

    return findings


def _joined_comment_examples(wf: Workflow) -> list[tuple[int, str]]:
    """Comment lines, with backslash continuations folded into one logical line."""
    joined: list[tuple[int, str]] = []
    pending_line = 0
    pending = ""
    for line_no, text in wf.comment_lines:
        if pending:
            pending = f"{pending} {text.rstrip()}"
        else:
            pending_line, pending = line_no, text.rstrip()
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip()
            continue
        joined.append((pending_line, pending))
        pending = ""
    if pending:
        joined.append((pending_line, pending))
    return joined


def survey(scan_root: Path) -> list[str]:
    """Name every site the three shapes are actually checked at.

    A gate nobody has seen bite is a gate nobody knows is wired to anything, and
    a count of zero here would mean this check passes because it looks at
    nothing — the vacuous-guard shape NFR-018 §2 is about. ``--list`` prints it.
    """
    sites: list[str] = []
    workflows = {p.name: load(p) for p in sorted(scan_root.glob("*.y*ml"))}
    for wf in workflows.values():
        rel = _rel(wf.path, scan_root)
        for name in sorted(wf.declared_inputs):
            sites.append(f"{rel}: declared input `{name}`")
        for line_no, line in wf.body_lines:
            for expression in _EXPRESSION.findall(line):
                for name in _INPUT_REF.findall(expression):
                    sites.append(f"{rel}:{line_no}: reads `inputs.{name}`")
        for line_no, example in _joined_comment_examples(wf):
            match = _GH_RUN.search(example)
            if match is not None:
                sites.append(f"{rel}:{line_no}: documents `gh workflow run {match.group(1)}`")
    return sites


def report(findings: list[Finding], *, list_all: bool, as_json: bool, scanned: int,
           sites: list[str] | None = None) -> int:
    if as_json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
        return EXIT_FINDINGS if findings else EXIT_OK

    if not findings:
        print(
            f"check_workflow_documented_invocation: {scanned} workflow(s) — every "
            f"documented invocation path is carried by the configuration."
        )
        if list_all:
            for site in sites or []:
                print(f"  {site}")
            print(f"  {len(sites or [])} checked site(s).")
        return EXIT_OK

    print(
        "check_workflow_documented_invocation: a workflow documents a way to invoke "
        "it that its configuration does not provide (NFR-018 §1, #1607).\n",
        file=sys.stderr,
    )
    for finding in findings:
        where = f"{finding.path}:{finding.line}" if finding.line else finding.path
        print(f"  [{finding.rule}] {where}\n      {finding.message}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). Either make the configuration carry the "
        f"documented path, or change the prose to describe the one it does.",
        file=sys.stderr,
    )
    return EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scan-root", metavar="PATH", default=None)
    parser.add_argument("--list", action="store_true", dest="list_all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    try:
        findings = collect(scan_root)
    except DocumentedInvocationCheckError as exc:
        print(f"check_workflow_documented_invocation: {exc}", file=sys.stderr)
        return EXIT_USAGE

    scanned = len(list(scan_root.glob("*.y*ml")))
    sites = survey(scan_root) if args.list_all else []
    return report(
        findings, list_all=args.list_all, as_json=args.json, scanned=scanned, sites=sites
    )


if __name__ == "__main__":
    raise SystemExit(main())
