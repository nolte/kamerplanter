#!/usr/bin/env python3
"""Refuse a workflow job that holds a write permission while checking out pull-request code.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_untrusted_checkout_permissions.py
    python3 scripts/check_untrusted_checkout_permissions.py --list
    python3 scripts/check_untrusted_checkout_permissions.py --json

**What it enforces.** Two properties of one construction — a runner on which
code from a pull request and a writable ``GITHUB_TOKEN`` exist at the same
time:

1. ``untrusted-checkout-write-permission`` — a job that checks out
   pull-request code may not hold a ``write`` scope, whether the scope is
   declared on the job or inherited from the workflow level. #1614 is the
   worked example: ``security-zap-postmerge.yml`` resolved
   ``refs/pull/<n>/merge`` in a job that held ``issues: write``, and its
   Nuclei twin added ``security-events: write``. No escalation was reachable
   — the only issue-writing step was gated ``if: always() &&
   github.event_name == 'push'`` — but a single ``if:`` on a single step was
   the entire distance between the untrusted tree and the token. The
   defence-in-depth measure is to put the write in a job of its own.

2. ``untrusted-checkout-persists-credentials`` — a checkout that resolves an
   EXPLICIT pull-request ref must set ``persist-credentials: false``.
   ``actions/checkout`` defaults to ``true``, which writes the job token into
   ``.git/config`` as an ``http.extraheader`` — inside the very tree the job
   then executes.

**Why rule 2 is narrower than rule 1, measured rather than assumed.** Under a
plain ``pull_request`` trigger the persisted token carries exactly the
permissions the workflow declares, so on a read-only floor there is nothing to
persist. The dangerous shape is a job running on a TRUSTED trigger (``push``,
``workflow_dispatch``, ``pull_request_target``) that goes out of its way to
fetch pull-request code: there the token is the trusted lane's token. Rule 2
therefore binds the explicit-ref shape; extending it to every
``pull_request``-triggered checkout in the tree would touch ten workflows to
remove a credential that is already read-only.

**Three ways the same thing can be spelled, all of them matched.**

* a ``ref:`` built from an expression — ``format('refs/pull/{0}/merge', …)``
  is matched on the rendered marker, not on a literal;
* a ``run:`` block that fetches it itself — ``gh pr checkout``, or a ``git
  fetch`` of ``refs/pull/…``. The block is read through
  :mod:`scripts.source_text` first, so a shell COMMENT mentioning ``gh pr
  checkout`` neither raises a finding nor satisfies one;
* a local composite action that checks out on the job's behalf — ``uses:
  ./.github/actions/<name>`` is followed and its steps are scanned too.

And the permission side is read as GitHub resolves it: job block, else
workflow block, else the repository default — which is reported as a finding
in its own right, because a tree cannot know what that default is.

**Known limits, stated rather than hidden.**

* A REUSABLE workflow (``uses: owner/repo/.github/workflows/x.yml@ref``)
  carries its own permissions and is not followed. There are none in this
  tree; ``--list`` would show the caller job with no checkout.
* A third-party action that fetches pull-request code inside its own
  implementation is invisible here — only local composite actions are read.
* A job whose ``if:`` happens to exclude the pull-request event in a workflow
  that declares one is still treated as a class member. That is deliberate:
  an ``if:`` is what #1614 is about.

**Exceptions are data, not prose.** ``KNOWN_EXCEPTIONS`` below is a
no-growth ratchet: each entry names the workflow, the job, the scope, the
measurement that makes it tolerable and the issue that closes it. A comment in
a workflow cannot silence this check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_text import executable_source  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = ".github/workflows"

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

#: Text that, appearing in a checkout `ref:`, means "the pull request's own code".
_REF_MARKERS = (
    "refs/pull",
    "github.head_ref",
    "pull_request.head",
    "pull_request.merge_commit_sha",
)

#: Text that, appearing in an executable `run:` line, fetches pull-request code.
_RUN_MARKERS = ("gh pr checkout", "refs/pull/")

#: Triggers on which a checkout with no explicit `ref:` already IS pull-request code.
_UNTRUSTED_TRIGGERS = ("pull_request", "pull_request_target")

#: Measured exceptions to `untrusted-checkout-write-permission`. NO-GROWTH RATCHET:
#: an entry is removed when the site is repaired, and a new one needs its own
#: measurement in review. `(workflow file, job id, scope)`.
KNOWN_EXCEPTIONS: dict[tuple[str, str, str], str] = {
    ("e2e-smoke.yml", "smoke", "checks"): (
        "dorny/test-reporter renders the JUnit XML the suite just produced into a "
        "check run, and it reads that XML from the workspace this job scanned. "
        "Splitting it off means routing the reports through an artefact and the "
        "action's `artifact:` input — a behaviour change to the pre-merge E2E lane, "
        "not a permission move. `checks: write` can attach a check run to this run's "
        "own commit and nothing else: it cannot write repository content, file an "
        "issue, publish a package or touch a security alert. #1644 carries the split; "
        "this entry is the ratchet, not a dismissal."
    ),
}


class UntrustedCheckoutCheckError(Exception):
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
class Checkout:
    """A step that puts pull-request code on the runner."""

    where: str
    line: int
    explicit_ref: bool
    persists_credentials: bool


def _triggers(parsed: dict) -> list[str]:
    # YAML 1.1 reads a bare `on:` key as the boolean True.
    on = parsed.get("on", parsed.get(True))
    if isinstance(on, dict):
        return list(on)
    if isinstance(on, list):
        return list(on)
    return [on] if isinstance(on, str) else []


def _write_scopes(permissions: object) -> set[str] | None:
    """Write scopes a `permissions:` value grants, or None when it is absent."""
    if permissions is None:
        return None
    if permissions == "write-all":
        return {"write-all"}
    if isinstance(permissions, str):  # `read-all`, or anything else read-only
        return set()
    if isinstance(permissions, dict):
        return {str(k) for k, v in permissions.items() if str(v) == "write"}
    return set()


def _line_of(text: str, needle: str, *, after: int = 0) -> int:
    """First line at or after *after* that contains *needle*, 1-based, else 0."""
    for number, line in enumerate(text.splitlines(), start=1):
        if number >= after and needle in line:
            return number
    return 0


def _job_line(text: str, job_id: str) -> int:
    """Line the job's key is written on, so a finding points at its own job.

    Without this every checkout in a multi-job workflow reports the line of the
    FIRST one, which sends the reader to the wrong job — the report being
    plausible is exactly what makes that kind of wrongness survive.
    """
    pattern = re.compile(rf"^\s{{2}}{re.escape(job_id)}\s*:")
    for number, line in enumerate(text.splitlines(), start=1):
        if pattern.match(line):
            return number
    return 0


def _is_checkout(step: dict) -> bool:
    uses = str(step.get("uses", ""))
    return uses.startswith("actions/checkout@") or uses.startswith("actions/checkout ")


def _local_action(step: dict, scan_root: Path) -> Path | None:
    uses = str(step.get("uses", ""))
    if not uses.startswith("./"):
        return None
    base = REPO_ROOT / uses[2:]
    for candidate in (base / "action.yml", base / "action.yaml"):
        if candidate.is_file():
            return candidate
    return None


def _steps_of(node: object) -> list[dict]:
    steps = node.get("steps") if isinstance(node, dict) else None
    return [s for s in steps if isinstance(s, dict)] if isinstance(steps, list) else []


def _scan_steps(
    steps: list[dict],
    *,
    text: str,
    origin: str,
    untrusted_trigger: bool,
    scan_root: Path,
    seen: set[Path],
    after: int = 0,
) -> list[Checkout]:
    found: list[Checkout] = []
    for step in steps:
        if _is_checkout(step):
            with_block = step.get("with") if isinstance(step.get("with"), dict) else {}
            ref = str(with_block.get("ref", ""))
            persists = str(with_block.get("persist-credentials", "true")).lower() != "false"
            explicit = any(marker in ref for marker in _REF_MARKERS)
            if explicit or untrusted_trigger:
                found.append(
                    Checkout(
                        where=origin,
                        line=_line_of(text, "actions/checkout@", after=after),
                        explicit_ref=explicit,
                        persists_credentials=persists,
                    )
                )

        run = step.get("run")
        if isinstance(run, str):
            executable = executable_source(run, language="shell")
            for marker in _RUN_MARKERS:
                if marker in executable:
                    found.append(
                        Checkout(
                            where=origin,
                            line=_line_of(text, marker, after=after),
                            explicit_ref=True,
                            # A `run:` block does not write `.git/config` on the
                            # job's behalf; rule 2 has nothing to bind to here.
                            persists_credentials=False,
                        )
                    )
                    break

        action_path = _local_action(step, scan_root)
        if action_path is not None and action_path not in seen:
            seen.add(action_path)
            action_text = action_path.read_text(encoding="utf-8")
            action = yaml.safe_load(action_text) or {}
            found.extend(
                _scan_steps(
                    _steps_of(action.get("runs")),
                    text=action_text,
                    origin=str(action_path.relative_to(REPO_ROOT)),
                    untrusted_trigger=untrusted_trigger,
                    scan_root=scan_root,
                    seen=seen,
                )
            )
    return found


@dataclass(frozen=True)
class Site:
    workflow: str
    job: str
    checkouts: tuple[Checkout, ...]
    write_scopes: tuple[str, ...]
    inherits_default: bool


def survey(scan_root: Path) -> list[Site]:
    """Every job in the tree that puts pull-request code on a runner."""
    if not scan_root.is_dir():
        raise UntrustedCheckoutCheckError(f"not a directory: {scan_root}")

    sites: list[Site] = []
    for path in sorted(scan_root.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        try:
            parsed = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - actionlint reports it too
            raise UntrustedCheckoutCheckError(f"{path}: not valid YAML: {exc}") from exc
        if not isinstance(parsed, dict):
            continue

        untrusted_trigger = any(t in _triggers(parsed) for t in _UNTRUSTED_TRIGGERS)
        workflow_permissions = parsed.get("permissions")
        jobs = parsed.get("jobs") if isinstance(parsed.get("jobs"), dict) else {}

        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            checkouts = _scan_steps(
                _steps_of(job),
                text=text,
                origin=path.name,
                untrusted_trigger=untrusted_trigger,
                scan_root=scan_root,
                seen=set(),
                after=_job_line(text, str(job_id)),
            )
            if not checkouts:
                continue
            declared = job["permissions"] if "permissions" in job else workflow_permissions
            scopes = _write_scopes(declared)
            sites.append(
                Site(
                    workflow=path.name,
                    job=str(job_id),
                    checkouts=tuple(checkouts),
                    write_scopes=tuple(sorted(scopes or ())),
                    inherits_default=scopes is None,
                )
            )
    return sites


def collect(scan_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for site in survey(scan_root):
        rel = f"{DEFAULT_SCAN_ROOT}/{site.workflow}"
        line = site.checkouts[0].line

        if site.inherits_default:
            findings.append(
                Finding(
                    rel,
                    line,
                    "untrusted-checkout-write-permission",
                    f"job `{site.job}` checks out pull-request code and declares no "
                    f"`permissions:` — neither on the job nor on the workflow — so it "
                    f"runs with the repository's default token scope, which this tree "
                    f"cannot see and may be write.",
                )
            )

        for scope in site.write_scopes:
            if (site.workflow, site.job, scope) in KNOWN_EXCEPTIONS:
                continue
            findings.append(
                Finding(
                    rel,
                    line,
                    "untrusted-checkout-write-permission",
                    f"job `{site.job}` holds `{scope}: write` while pull-request code "
                    f"is on the runner. Move the step that needs the write into a job "
                    f"that does not check out pull-request code (#1614).",
                )
            )

        for checkout in site.checkouts:
            if checkout.explicit_ref and checkout.persists_credentials:
                findings.append(
                    Finding(
                        rel if checkout.where == site.workflow else checkout.where,
                        checkout.line,
                        "untrusted-checkout-persists-credentials",
                        f"job `{site.job}` resolves an explicit pull-request ref without "
                        f"`persist-credentials: false`, so the job token is written into "
                        f"`.git/config` inside the tree it then executes.",
                    )
                )
    return findings


def report(findings: list[Finding], *, list_all: bool, as_json: bool, sites: list[Site]) -> int:
    if as_json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
        return EXIT_FINDINGS if findings else EXIT_OK

    if not findings:
        print(
            f"check_untrusted_checkout_permissions: {len(sites)} job(s) put "
            f"pull-request code on a runner; none of them holds an unexcepted write "
            f"scope, and every explicit pull-request checkout drops its credential."
        )
        if list_all:
            _print_sites(sites)
        return EXIT_OK

    print(
        "check_untrusted_checkout_permissions: pull-request code and a writable token "
        "share a runner (#1614).\n",
        file=sys.stderr,
    )
    for finding in findings:
        where = f"{finding.path}:{finding.line}" if finding.line else finding.path
        print(f"  [{finding.rule}] {where}\n      {finding.message}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). Split the write into its own job, or record the "
        f"measurement in KNOWN_EXCEPTIONS with the issue that closes it.",
        file=sys.stderr,
    )
    if list_all:
        _print_sites(sites)
    return EXIT_FINDINGS


def _print_sites(sites: list[Site]) -> None:
    for site in sites:
        shapes = ",".join(
            "explicit-ref" if c.explicit_ref else "pull_request-trigger" for c in site.checkouts
        )
        scopes = ", ".join(site.write_scopes) if site.write_scopes else "no write scope"
        if site.inherits_default:
            scopes = "repository default (undeclared)"
        print(f"  {site.workflow}: job `{site.job}` [{shapes}] — {scopes}")
    print(f"  {len(sites)} checked site(s).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scan-root", metavar="PATH", default=None)
    parser.add_argument("--list", action="store_true", dest="list_all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    try:
        sites = survey(scan_root)
        findings = collect(scan_root)
    except UntrustedCheckoutCheckError as exc:
        print(f"check_untrusted_checkout_permissions: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(findings, list_all=args.list_all, as_json=args.json, sites=sites)


if __name__ == "__main__":
    raise SystemExit(main())
