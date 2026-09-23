"""A relevance filter is held against what its job READS, never against what its workflow mentions (#1596).

THE GAP THIS IS WRITTEN AGAINST, MEASURED 2026-09-20 AND AGAIN 2026-09-23.

A path filter — ``on.<event>.paths`` on a workflow, or a ``dorny/paths-filter``
step inside a job — is a claim that no change outside the listed paths can alter
the job's verdict. Until this file, the only check that claim ever met was
``scripts/check_workflow_gate_integrity.py`` shape 5, which holds a filter
against the repo-relative paths the workflow's TEXT references. That is a real
check of a real class, and it is strictly weaker than the property: a job reads
what its tests, scripts and tools open, and none of that is in the workflow's
text. The required ``Write-route and tree guards`` lane says ``pytest
tests/unit/api tests/unit/guards`` and opens 57 files under
``src/frontend/src/api/endpoints/``, every workflow file, ``renovate.json5`` and
eight ``pyproject.toml``/``uv.lock`` pairs outside its package — and lists the
checkout ROOT, so a new ``pyproject.toml`` anywhere changes its verdict. A
shape-5 check would have certified a filter that excluded the frontend outright.
Shape 5 also cannot see ``backend-guards.yml``'s filter at all: it reads
``paths:`` off diff-driven triggers, and that workflow's relevance decision
lives in a step input, by design.

The failure runs in exactly one direction. A filter that is too WIDE wastes a
run. A filter that is too NARROW makes the lane report green — or, for a
required context gated inside the job, report *success* — over a change it
never looked at: NFR-018 §1, and the twin of §4.1.

WHAT THIS FILE HOLDS, AND AGAINST WHAT.

``scripts/ci/lane_inputs.py`` records, per job, every tracked file the job's
own invocation opened and every directory it enumerated — under ``strace -f``,
so a read by a subprocess (``git``, ``task``, ``uv``, ``npx``) is on the record,
which is the blind spot the ``sys.addaudithook`` measurement in #1595 named and
could not close. One manifest per job lives under ``.github/lane-inputs/``.
This file then asserts, over the real tree:

1. **Population.** Every job in an ``on:``-path-filtered workflow has a
   manifest, and every ``paths-filter`` filter name is claimed by at least one
   manifest. A filtered lane without a measurement is the opt-in-list defect —
   the class #1402/#1406 paid for — and is a failure, not a pass.
2. **Coverage.** Every read path in every manifest is selected by every filter
   that applies to its job: the workflow's ``on:`` triggers (a trigger without
   ``paths`` fires for everything, so a workflow whose ``pull_request`` is
   unfiltered covers every path — ``frontend.yml``'s construction) AND the
   ``paths-filter`` filter(s) the manifest declares. A directory listing
   (``src/backend/tests/``) is covered when the filter would select a file
   *added* there. A read that is deliberately outside the filter is written
   down as an ``accepted_gaps`` entry with a reason and, where the argument is
   "another lane runs it", the name of that lane — which must then really be
   unfiltered, and, when it carries a manifest of its own, really read those
   paths. A gap entry that matches nothing uncovered is stale and fails.
3. **Freshness.** Each manifest records a hash of the PARSED job it measured.
   Change a step and the manifest describes a job that no longer exists;
   the check demands a re-measurement. Comments do not count. This is what
   the issue asked for as "a recorded set older than the lane's last change"
   — the anchor is the job's definition, not a commit, because ``develop`` is
   squash-merged and the recording commit does not survive the merge.
4. **Decision shape (#1596, W-5).** For a job whose check-run label is a
   REQUIRED context and whose relevance is decided inside the job, three
   properties held only by comment until now are held here: no job-level
   ``if:`` beyond ``always()`` (a skipped job reports a conclusion branch
   protection accepts), no ``continue-on-error`` on the detection step (the
   in-job shape is fail-safe *because* a failed detector kills the job), and
   the run flag defaults to RUN before the detection narrows it (invert the
   default and the fail-safe is a fail-open in one character).

THE MATCHER, AND WHY IT IS ALLOWED TO EXIST HERE.

``test_paths_filter_quantifier.py`` is deliberately matcher-free, because its
rules are structural and a matcher there would let the test reach the rule over
a different path than production. This file's rule IS "does this pattern select
this path", so a matcher is the rule, not a detour around it. It follows the
documented semantics both consumers share — ``*`` never crosses ``/``, ``**``
does, a leading ``**/`` matches zero or more directories, ``!`` negates — and
``TestTheMatcherAgreesWithTheDocumentedSemantics`` pins each of those on a
case that would have gone the other way under a naive translation. Which
concrete diff runs or skips a lane is still proven by running it (the
counter-proof runs in #1595); this file proves that the filter and the
measured read set agree.

Traces to #1596 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import hashlib
import json
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root, load_repo_script

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found; this guard reads .github/ and cannot run without it")

_DOT_GITHUB = _REPO_ROOT / ".github"
_MANIFEST_DIR = _DOT_GITHUB / "lane-inputs"
_REQUIRED_FIXTURE = Path(__file__).parent / "fixtures" / "required_status_contexts_develop.yaml"

_source_text = load_repo_script("source_text")

#: Anti-vacuity floors, set to today's inventory. A sweep that finds fewer
#: filtered workflows, fewer filter names or fewer manifests than the tree
#: carried when this was written has lost sight of something, and every
#: assertion over the smaller population is weaker than it looks. Raise when
#: the inventory grows; never lower without saying which lane went away.
_MINIMUM_FILTERED_WORKFLOWS = 12
_MINIMUM_FILTER_NAMES = 21
_MINIMUM_MANIFESTS = 30

#: Substring rather than the full digest-pinned spelling, as in the sibling guard.
_PATHS_FILTER = "paths-filter@"

_DIFF_TRIGGERS = ("push", "pull_request", "pull_request_target")

#: Probe file name used to ask "would a file added under this directory be selected?".
_PROBE = "__lane_inputs_probe__"

#: A reason shorter than this is a label, not a reason.
_MIN_REASON_CHARS = 40

_SCHEMA = 1


# --------------------------------------------------------------------- matcher


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub / picomatch path pattern into an anchored regex.

    ``*`` and ``?`` never cross ``/``; ``**`` does; a leading or embedded
    ``**/`` matches zero or more directories (so ``**/*.md`` selects a
    ``README.md`` at the root, which both GitHub's filter and picomatch do);
    a trailing ``/**`` selects the directory's content. Everything else is
    literal — notably ``.``.
    """
    out: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        if pattern.startswith("**", index):
            out.append(".*")
            index += 2
            continue
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        elif char == "[":
            close = pattern.find("]", index + 1)
            if close != -1:
                body = pattern[index + 1 : close]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append(f"[{body}]")
                index = close + 1
                continue
            out.append(re.escape(char))
        else:
            out.append(re.escape(char))
        index += 1
    return re.compile("^" + "".join(out) + "$")


def _matches(pattern: str, path: str) -> bool:
    return glob_to_regex(pattern).match(path) is not None


def probe_path(read: str) -> str:
    """The path a filter must select for a recorded read to count as covered.

    A file is itself. A directory listing, recorded with a trailing ``/``,
    becomes a hypothetical file added inside it, because that is the change
    the listing makes the job sensitive to. The checkout root (``./``) becomes
    a hypothetical file at the top level — which only ``**`` selects, and that
    is the correct answer for a job that enumerates the whole tree.
    """
    if read == "./":
        return _PROBE
    if read.endswith("/"):
        return read + _PROBE
    return read


# ------------------------------------------------------------- filter surfaces


@dataclass(frozen=True)
class Trigger:
    event: str
    paths: tuple[str, ...]
    paths_ignore: tuple[str, ...]

    def fires_for(self, path: str) -> bool:
        if self.paths:
            selected = self.paths[0].startswith("!")  # a leading exclusion starts from "everything"
            for pattern in self.paths:
                negated = pattern.startswith("!")
                if _matches(pattern[1:] if negated else pattern, path):
                    selected = not negated
            return selected
        if self.paths_ignore:
            return not any(_matches(pattern, path) for pattern in self.paths_ignore)
        return True


@dataclass(frozen=True)
class StepFilter:
    workflow: str
    step_id: str | None
    name: str
    patterns: tuple[str, ...]
    quantifier: str

    def selects(self, path: str) -> bool:
        verdicts = []
        for pattern in self.patterns:
            negated = pattern.startswith("!")
            hit = _matches(pattern[1:] if negated else pattern, path)
            verdicts.append((not hit) if negated else hit)
        if not verdicts:
            return False
        return all(verdicts) if self.quantifier == "every" else any(verdicts)


@dataclass
class Workflow:
    name: str
    path: Path
    document: dict[str, Any]
    triggers: list[Trigger]
    step_filters: list[StepFilter]

    @property
    def on_filtered(self) -> bool:
        return any(trigger.paths or trigger.paths_ignore for trigger in self.triggers)

    def trigger_fires(self, path: str) -> bool:
        """Whether ANY diff-driven trigger would run this workflow for *path*."""
        return any(trigger.fires_for(path) for trigger in self.triggers)

    @property
    def jobs(self) -> dict[str, Any]:
        jobs = self.document.get("jobs")
        return jobs if isinstance(jobs, dict) else {}


def _trigger_block(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        return {}
    block = document.get("on", document.get(True))
    if isinstance(block, str):
        return {block: None}
    if isinstance(block, list):
        return dict.fromkeys(block)
    return dict(block) if isinstance(block, dict) else {}


def _string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str))


def _filter_patterns(raw: Any) -> dict[str, list[str]]:
    document = yaml.safe_load(raw) if isinstance(raw, str) else raw
    if not isinstance(document, dict):
        return {}
    out: dict[str, list[str]] = {}
    for name, value in document.items():
        entries = value if isinstance(value, list) else [value]
        patterns = []
        for entry in entries:
            if isinstance(entry, dict):
                entry = entry.get("path")
            if isinstance(entry, str):
                patterns.append(entry)
        out[str(name)] = patterns
    return out


def _steps_of(document: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if not isinstance(document, dict):
        return found
    for job in (document.get("jobs") or {}).values():
        if isinstance(job, dict) and isinstance(job.get("steps"), list):
            found += [step for step in job["steps"] if isinstance(step, dict)]
    runs = document.get("runs")
    if isinstance(runs, dict) and isinstance(runs.get("steps"), list):
        found += [step for step in runs["steps"] if isinstance(step, dict)]
    return found


def load_workflows(dot_github: Path) -> list[Workflow]:
    """Every workflow (and composite action) under *dot_github*, with its filter surfaces parsed."""
    files = sorted(p for p in (dot_github / "workflows").glob("*.y*ml") if p.is_file())
    files += sorted(p for p in (dot_github / "actions").rglob("action.y*ml") if p.is_file())
    workflows: list[Workflow] = []
    for path in files:
        document = yaml.safe_load(path.read_text())
        if not isinstance(document, dict):
            continue
        triggers = []
        for event, spec in _trigger_block(document).items():
            if event not in _DIFF_TRIGGERS:
                continue
            spec = spec if isinstance(spec, dict) else {}
            triggers.append(Trigger(event, _string_list(spec.get("paths")), _string_list(spec.get("paths-ignore"))))
        step_filters = []
        for step in _steps_of(document):
            uses = step.get("uses")
            if not isinstance(uses, str) or _PATHS_FILTER not in uses:
                continue
            inputs = step.get("with") if isinstance(step.get("with"), dict) else {}
            quantifier = str(inputs.get("predicate-quantifier", "some"))
            for name, patterns in _filter_patterns(inputs.get("filters")).items():
                step_filters.append(StepFilter(path.name, step.get("id"), name, tuple(patterns), quantifier))
        name = path.name if path.parent.name == "workflows" else path.relative_to(dot_github).as_posix()
        workflows.append(Workflow(name, path, document, triggers, step_filters))
    return workflows


# ------------------------------------------------------------------ manifests


def job_spec_hash(job: Any) -> str:
    """The recorder's ``hash_job_spec``, verbatim: the parsed job minus paths-filter patterns.

    The patterns are compared live by this file, so editing them must not
    stale the manifest; every other change to the job must.
    """
    if isinstance(job, dict) and isinstance(job.get("steps"), list):
        job = dict(job)
        cleaned = []
        for step in job["steps"]:
            if (
                isinstance(step, dict)
                and _PATHS_FILTER in str(step.get("uses", ""))
                and isinstance(step.get("with"), dict)
            ):
                step = dict(step)
                step["with"] = {key: value for key, value in step["with"].items() if key != "filters"}
            cleaned.append(step)
        job["steps"] = cleaned
    canonical = json.dumps(job, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Manifest:
    path: Path
    workflow: str
    job: str
    gate_kind: str
    filters: tuple[str, ...]
    status: str
    job_spec_sha256: str
    reads: tuple[str, ...]
    accepted_gaps: list[dict[str, Any]]
    schema: int
    empty_reads_reason: str | None = None
    problems: list[str] = field(default_factory=list)


def load_manifests(manifest_dir: Path) -> list[Manifest]:
    manifests: list[Manifest] = []
    for path in sorted(manifest_dir.glob("*.yaml")) if manifest_dir.is_dir() else []:
        document = yaml.safe_load(path.read_text())
        if not isinstance(document, dict):
            manifests.append(Manifest(path, "", "", "", (), "", "", (), [], 0, [f"{path.name}: not a mapping"]))
            continue
        gate = document.get("gate") if isinstance(document.get("gate"), dict) else {}
        raw_filters = gate.get("filter")
        if isinstance(raw_filters, str):
            filters: tuple[str, ...] = (raw_filters,)
        elif isinstance(raw_filters, list):
            filters = tuple(str(entry) for entry in raw_filters)
        else:
            filters = ()
        gaps = document.get("accepted_gaps")
        manifests.append(
            Manifest(
                path=path,
                workflow=str(document.get("workflow", "")),
                job=str(document.get("job", "")),
                gate_kind=str(gate.get("kind", "")),
                filters=filters,
                status=str(document.get("status", "")),
                job_spec_sha256=str(document.get("job_spec_sha256", "")),
                reads=tuple(str(entry) for entry in (document.get("reads") or [])),
                accepted_gaps=[entry for entry in (gaps or []) if isinstance(entry, dict)],
                schema=int(document.get("schema", 0) or 0),
                empty_reads_reason=str(document["empty_reads_reason"]) if document.get("empty_reads_reason") else None,
            )
        )
    return manifests


# ---------------------------------------------------------------------- rules


@dataclass
class Sweep:
    workflows: list[Workflow]
    manifests: list[Manifest]

    def workflow(self, name: str) -> Workflow | None:
        return next((wf for wf in self.workflows if wf.name == name), None)

    def manifests_for(self, workflow: str, job: str) -> list[Manifest]:
        return [m for m in self.manifests if m.workflow == workflow and m.job == job]


def sweep(dot_github: Path, manifest_dir: Path) -> Sweep:
    return Sweep(load_workflows(dot_github), load_manifests(manifest_dir))


def missing_manifests(s: Sweep) -> list[str]:
    """Filtered jobs and filter names that no manifest measures."""
    findings: list[str] = []
    for wf in s.workflows:
        if wf.on_filtered:
            for job in wf.jobs:
                if not s.manifests_for(wf.name, job):
                    findings.append(
                        f"{wf.name}: job {job!r} runs behind an on:-level paths filter and has no manifest "
                        f"under .github/lane-inputs/ — record one with scripts/ci/lane_inputs.py"
                    )
        claimed = {(m.workflow, name) for m in s.manifests for name in m.filters}
        for step_filter in wf.step_filters:
            if (wf.name, step_filter.name) not in claimed:
                findings.append(
                    f"{wf.name}: paths-filter filter {step_filter.name!r} gates a job that no manifest "
                    f"claims (gate.filter) — record the gated job with scripts/ci/lane_inputs.py"
                )
    return findings


def malformed_manifests(s: Sweep) -> list[str]:
    findings: list[str] = []
    for m in s.manifests:
        findings += m.problems
        if m.schema != _SCHEMA:
            findings.append(f"{m.path.name}: schema {m.schema} is not {_SCHEMA}")
        wf = s.workflow(m.workflow)
        if wf is None:
            findings.append(f"{m.path.name}: names workflow {m.workflow!r}, which does not exist")
            continue
        if m.job not in wf.jobs:
            findings.append(f"{m.path.name}: names job {m.job!r}, which {m.workflow} does not define")
        if m.gate_kind not in ("on-paths", "paths-filter"):
            findings.append(f"{m.path.name}: gate.kind {m.gate_kind!r} is neither on-paths nor paths-filter")
        if m.gate_kind == "on-paths" and not wf.on_filtered:
            findings.append(f"{m.path.name}: claims an on:-level filter, but {m.workflow} has none")
        known = {sf.name for sf in wf.step_filters}
        for name in m.filters:
            if name not in known:
                findings.append(
                    f"{m.path.name}: claims paths-filter filter {name!r}, which {m.workflow} does not define"
                )
        if m.gate_kind == "paths-filter" and not m.filters:
            findings.append(f"{m.path.name}: gate.kind is paths-filter but gate.filter names nothing")
        if not m.reads and not (m.empty_reads_reason and len(m.empty_reads_reason.strip()) >= _MIN_REASON_CHARS):
            findings.append(
                f"{m.path.name}: records no read at all — a job that reads nothing measured nothing, unless "
                f"`empty_reads_reason` says in at least {_MIN_REASON_CHARS} characters why "
                f"(checkout + paths-filter only, say)"
            )
        if m.status not in ("measured", "derived"):
            findings.append(f"{m.path.name}: status {m.status!r} is neither measured nor derived")
    return findings


def stale_manifests(s: Sweep) -> list[str]:
    findings: list[str] = []
    for m in s.manifests:
        wf = s.workflow(m.workflow)
        if wf is None or m.job not in wf.jobs:
            continue
        live = job_spec_hash(wf.jobs[m.job])
        if live != m.job_spec_sha256:
            findings.append(
                f"{m.path.name}: job {m.job!r} in {m.workflow} changed since it was measured "
                f"(recorded {m.job_spec_sha256[:12]}, live {live[:12]}) — re-record it, then re-check its filter"
            )
    return findings


def _applicable_filters(s: Sweep, m: Manifest) -> list[StepFilter]:
    wf = s.workflow(m.workflow)
    if wf is None:
        return []
    return [sf for sf in wf.step_filters if sf.name in m.filters]


def uncovered_reads(s: Sweep, m: Manifest) -> dict[str, list[str]]:
    """``read path -> the filter(s) that fail to select it``, before accepted gaps."""
    wf = s.workflow(m.workflow)
    if wf is None:
        return {}
    step_filters = _applicable_filters(s, m)
    out: dict[str, list[str]] = {}
    for read in m.reads:
        probe = probe_path(read)
        failed = []
        if wf.on_filtered and not wf.trigger_fires(probe):
            failed.append(f"{m.workflow} on:-level paths filter")
        if step_filters and not any(sf.selects(probe) for sf in step_filters):
            failed.append(f"{m.workflow} paths-filter {'|'.join(sf.name for sf in step_filters)}")
        if failed:
            out[read] = failed
    return out


def _gap_matches(gap: dict[str, Any], read: str) -> bool:
    pattern = gap.get("pattern")
    return isinstance(pattern, str) and (
        pattern == read or _matches(pattern, probe_path(read)) or _matches(pattern, read)
    )


def coverage_findings(s: Sweep, m: Manifest) -> list[str]:
    """Reads outside the filter that no accepted gap explains, plus gaps that explain nothing."""
    findings: list[str] = []
    uncovered = uncovered_reads(s, m)
    explained: set[str] = set()
    for index, gap in enumerate(m.accepted_gaps):
        reason = gap.get("reason")
        if not isinstance(reason, str) or len(reason.strip()) < _MIN_REASON_CHARS:
            findings.append(
                f"{m.path.name}: accepted_gaps[{index}] carries no reason of at least {_MIN_REASON_CHARS} characters"
            )
        hits = [read for read in uncovered if _gap_matches(gap, read)]
        if not hits:
            findings.append(
                f"{m.path.name}: accepted_gaps[{index}] ({gap.get('pattern')!r}) matches no read outside the filter — "
                f"it is stale; delete it or re-record"
            )
        explained.update(hits)
        covered_by = gap.get("covered_by")
        if covered_by is not None:
            findings += _delegation_findings(s, m, index, str(covered_by), hits)
    for read, failed in uncovered.items():
        if read in explained:
            continue
        findings.append(f"{m.path.name}: job {m.job!r} reads {read!r}, which {' and '.join(failed)} does not select")
    return findings


def _delegation_findings(s: Sweep, m: Manifest, index: int, covered_by: str, paths: list[str]) -> list[str]:
    """``covered_by: <workflow>/<job>`` is a claim; hold it against the tree."""
    findings: list[str] = []
    workflow_name, _, job = covered_by.partition("/")
    wf = s.workflow(workflow_name)
    prefix = f"{m.path.name}: accepted_gaps[{index}] covered_by {covered_by!r}"
    if wf is None or job not in wf.jobs:
        return [f"{prefix} names a job that does not exist"]
    if not any(not (t.paths or t.paths_ignore) and _fires_for_pull_requests(t, wf) for t in wf.triggers):
        findings.append(
            f"{prefix} is not an unfiltered lane: no diff-driven trigger of {workflow_name} "
            f"fires for every pull request"
        )
    covering_job = wf.jobs[job]
    if isinstance(covering_job, dict):
        if any(
            _PATHS_FILTER in str(step.get("uses", ""))
            for step in covering_job.get("steps") or []
            if isinstance(step, dict)
        ):
            findings.append(
                f"{prefix} decides its own relevance with a paths-filter step, so it is not an unconditional run"
            )
        if re.search(r"needs\.[A-Za-z0-9_-]+\.outputs", str(covering_job.get("if", ""))):
            findings.append(f"{prefix} is gated on another job's outputs, so it is not an unconditional run")
    for covering in s.manifests_for(workflow_name, job):
        covering_reads = set(covering.reads)
        unread = [p for p in paths if p not in covering_reads and not (p.endswith("/") and p in covering_reads)]
        if unread:
            findings.append(
                f"{prefix} does not read {unread[:5]}{'…' if len(unread) > 5 else ''} according to its own manifest"
            )
    return findings


def _fires_for_pull_requests(trigger: Trigger, wf: Workflow) -> bool:
    spec = _trigger_block(wf.document).get(trigger.event) or {}
    spec = spec if isinstance(spec, dict) else {}
    branches = spec.get("branches")
    if trigger.event == "push":
        return not branches and not spec.get("branches-ignore")
    return branches is None or "develop" in branches


# ------------------------------------------------------------ decision shape


def required_contexts() -> set[str]:
    document = yaml.safe_load(_REQUIRED_FIXTURE.read_text())
    contexts: set[str] = set()
    for key in ("branch_protection", "rulesets"):
        contexts.update(str(entry) for entry in (document.get(key) or []))
    return contexts


def _job_label(job_id: str, job: dict[str, Any]) -> str:
    name = job.get("name")
    return str(name) if name else job_id


_ENV_FLAG = re.compile(r"env\.([A-Za-z_][A-Za-z0-9_]*)\s*==\s*'true'")
_ASSIGNMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)=(\S+)", re.MULTILINE)


def decision_shape_findings(s: Sweep, contexts: set[str]) -> list[str]:
    """W-5: the three load-bearing properties of an in-job relevance decision on a required lane."""
    findings: list[str] = []
    for wf in s.workflows:
        for job_id, job in wf.jobs.items():
            if not isinstance(job, dict):
                continue
            steps = [step for step in job.get("steps") or [] if isinstance(step, dict)]
            flags = {flag for step in steps for flag in _ENV_FLAG.findall(str(step.get("if", "")))}
            detector = next((step for step in steps if _PATHS_FILTER in str(step.get("uses", ""))), None)
            if not flags and detector is None:
                continue  # relevance is not decided inside this job
            label = _job_label(job_id, job)
            required = label in contexts or any(context.startswith(label + " (") for context in contexts)
            if not required:
                continue
            where = f"{wf.name}: required job {job_id!r}"
            condition = str(job.get("if", "")).strip()
            if condition and condition != "always()":
                findings.append(
                    f"{where} carries a job-level if: ({condition!r}); a skipped job reports a conclusion branch "
                    f"protection accepts, so the required context can go green having run nothing"
                )
            if detector is not None and detector.get("continue-on-error"):
                findings.append(
                    f"{where}: the paths-filter step carries continue-on-error, "
                    f"so a failed detection no longer kills the job"
                )
            for flag in sorted(flags):
                findings += _default_findings(where, job, steps, flag)
    return findings


def _default_findings(where: str, job: dict[str, Any], steps: list[dict[str, Any]], flag: str) -> list[str]:
    """The run flag must be RUN by default and narrowed only by a successful, negative detection."""
    env = job.get("env") if isinstance(job.get("env"), dict) else {}
    if flag in env:
        expression = str(env[flag])
        if ".result != 'success'" not in expression.replace('"', "'"):
            return [
                f"{where}: env.{flag} is computed without a `needs.<job>.result != 'success'` clause, "
                f"so a failed detection skips the lane"
            ]
        return []
    for step in steps:
        script = step.get("run")
        if not isinstance(script, str):
            continue
        executable = _source_text.executable_source(script, language="shell")
        assignments = [
            (name, value)
            for name, value in _ASSIGNMENT.findall(executable)
            if name in (flag, flag.removeprefix("RUN_"), "RUN")
        ]
        if not assignments:
            continue
        if assignments[0][1].strip("\"'").lower() != "true":
            return [
                f"{where}: the first assignment of the run flag in the freeze step is {assignments[0][1]!r}, "
                f"not true — the default must be RUN"
            ]
        return []
    return [f"{where}: steps gate on env.{flag} but no step or job env sets it"]


# ------------------------------------------------------------------ fixtures


@pytest.fixture(scope="module")
def real() -> Sweep:
    s = sweep(_DOT_GITHUB, _MANIFEST_DIR)
    filtered = [wf.name for wf in s.workflows if wf.on_filtered]
    names = [(wf.name, sf.name) for wf in s.workflows for sf in wf.step_filters]
    assert len(filtered) >= _MINIMUM_FILTERED_WORKFLOWS, (
        f"only {len(filtered)} on:-path-filtered workflows found ({filtered}); the tree carried "
        f"{_MINIMUM_FILTERED_WORKFLOWS} when this guard was written. Either filters were retired — then "
        f"lower the floor and say which — or the sweep stopped seeing them, and every rule below is weaker."
    )
    assert len(names) >= _MINIMUM_FILTER_NAMES, (
        f"only {len(names)} paths-filter filter names found; the floor is {_MINIMUM_FILTER_NAMES}"
    )
    assert len(s.manifests) >= _MINIMUM_MANIFESTS, (
        f"only {len(s.manifests)} manifests under .github/lane-inputs/; the floor is {_MINIMUM_MANIFESTS}. "
        f"A manifest deleted without its lane is a filter nobody measures again."
    )
    return s


# --------------------------------------------------------------- real tree


class TestTheRealTree:
    def test_every_filtered_job_and_every_filter_name_is_measured(self, real: Sweep) -> None:
        findings = missing_manifests(real)
        assert not findings, "A relevance filter without a measured read set is an opt-in list:\n  " + "\n  ".join(
            findings
        )

    def test_every_manifest_is_well_formed_and_names_a_live_job(self, real: Sweep) -> None:
        findings = malformed_manifests(real)
        assert not findings, "\n  ".join(findings)

    def test_no_manifest_is_older_than_its_job(self, real: Sweep) -> None:
        findings = stale_manifests(real)
        assert not findings, (
            "A manifest describes the job it was measured under. Re-record with scripts/ci/lane_inputs.py "
            "(the invocations are listed in the file):\n  " + "\n  ".join(findings)
        )

    def test_every_read_is_selected_by_every_filter_that_gates_its_job(self, real: Sweep) -> None:
        findings = [finding for m in real.manifests for finding in coverage_findings(real, m)]
        assert not findings, (
            "A job reads a path its relevance filter does not select, so a change to that path cannot run "
            "the job that depends on it (#1596). Widen the filter, or write the gap down under accepted_gaps "
            "with a reason — and, if the argument is that another lane covers it, name that lane:\n  "
            + "\n  ".join(findings)
        )

    def test_required_in_job_decisions_keep_their_fail_safe_shape(self, real: Sweep) -> None:
        findings = decision_shape_findings(real, required_contexts())
        assert not findings, "\n  ".join(findings)

    def test_the_decision_shape_rule_measured_at_least_one_required_lane(self, real: Sweep) -> None:
        """Rule 4 asserts over the required, in-job-gated lanes; with none, it asserts over nothing."""
        contexts = required_contexts()
        gated = [
            (wf.name, job_id)
            for wf in real.workflows
            for job_id, job in wf.jobs.items()
            if isinstance(job, dict)
            and _job_label(job_id, job) in contexts
            and any(
                _ENV_FLAG.search(str(step.get("if", ""))) for step in job.get("steps") or [] if isinstance(step, dict)
            )
        ]
        assert gated, (
            "no required context decides its relevance inside the job any more; "
            "retire rule 4 with a reason rather than leave it green over nothing"
        )


class TestTheRealTreeCanGoRed:
    """Mutations of the real filters, in memory: removing a load-bearing pattern must surface a read."""

    def test_dropping_the_backend_pattern_from_the_integration_filter_names_backend_reads(self, real: Sweep) -> None:
        wf = real.workflow("backend-guards.yml")
        assert wf is not None
        original = next(sf for sf in wf.step_filters if sf.name == "integration")
        assert "src/backend/**" in original.patterns
        mutated = StepFilter(
            original.workflow,
            original.step_id,
            original.name,
            tuple(p for p in original.patterns if p != "src/backend/**"),
            original.quantifier,
        )
        wf.step_filters = [mutated if sf is original else sf for sf in wf.step_filters]
        try:
            manifests = real.manifests_for("backend-guards.yml", "integration")
            assert manifests, "the required integration lane has no manifest"
            uncovered = uncovered_reads(real, manifests[0])
        finally:
            wf.step_filters = [original if sf is mutated else sf for sf in wf.step_filters]
        assert uncovered, (
            "removing src/backend/** from the integration filter uncovered nothing — "
            "the manifest reads no backend file?"
        )
        assert any(read.startswith("src/backend/") for read in uncovered), sorted(uncovered)[:5]

    def test_dropping_a_pattern_from_an_on_level_filter_names_the_reads_it_covered(self, real: Sweep) -> None:
        wf = real.workflow("side-services.yml")
        assert wf is not None
        original = wf.triggers
        wf.triggers = [
            Trigger(t.event, tuple(p for p in t.paths if p != "src/libs/kp_vectordb/**"), t.paths_ignore)
            for t in original
        ]
        try:
            manifests = real.manifests_for("side-services.yml", "libs")
            assert manifests
            uncovered = uncovered_reads(real, manifests[0])
        finally:
            wf.triggers = original
        assert any(read.startswith("src/libs/kp_vectordb/") for read in uncovered), sorted(uncovered)[:5]


# ------------------------------------------------------------ planted trees


def _plant(root: Path, relative: str, body: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body).lstrip())


def _workflow_with_on_filter(paths: list[str]) -> str:
    entries = "".join(f"      - '{p}'\n" for p in paths)
    return (
        "name: planted\n"
        "on:\n"
        "  pull_request:\n"
        "    paths:\n" + entries + "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: make\n"
    )


def _workflow_with_step_filter(
    patterns: list[str],
    *,
    quantifier: str | None = None,
    job_if: str | None = None,
    coe: bool = False,
    default: str = "true",
) -> str:
    entries = "".join(f"              - '{p}'\n" for p in patterns)
    quantifier_line = f"          predicate-quantifier: '{quantifier}'\n" if quantifier else ""
    if_line = f"    if: {job_if}\n" if job_if else ""
    coe_line = "        continue-on-error: true\n" if coe else ""
    return (
        "name: planted\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  integration:\n"
        "    name: Integration tests (ArangoDB)\n" + if_line + "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - id: relevance\n"
        "        uses: dorny/paths-filter@0000000000000000000000000000000000000000 # v4\n"
        + coe_line
        + "        with:\n"
        + quantifier_line
        + "          filters: |\n"
        "            integration:\n" + entries + "      - name: Freeze\n"
        "        run: |\n"
        f"          RUN={default}\n"
        '          if [ "$DETECTION" = success ] && [ "$RELEVANT" = false ]; then RUN=false; fi\n'
        '          echo "RUN_INTEGRATION=$RUN" >> "$GITHUB_ENV"\n'
        "      - name: Tests\n"
        "        if: env.RUN_INTEGRATION == 'true'\n"
        "        run: pytest\n"
    )


def _manifest(
    workflow: str,
    job: str,
    *,
    reads: list[str],
    gate_kind: str = "on-paths",
    filters: list[str] | None = None,
    job_hash: str = "",
    gaps: list[dict[str, Any]] | None = None,
    schema: int = 1,
) -> str:
    gate: dict[str, Any] = {"kind": gate_kind}
    if filters:
        gate["filter"] = filters
    return yaml.safe_dump(
        {
            "schema": schema,
            "workflow": workflow,
            "job": job,
            "gate": gate,
            "status": "measured",
            "job_spec_sha256": job_hash,
            "accepted_gaps": gaps or [],
            "reads": reads,
        },
        sort_keys=False,
    )


def _hash_of(root: Path, workflow: str, job: str) -> str:
    document = yaml.safe_load((root / "workflows" / workflow).read_text())
    return job_spec_hash(document["jobs"][job])


class TestTheSweepCanGoRed:
    """Each rule planted against, each paired with the variant that clears it.

    A constructed ``.github/`` plus a constructed manifest directory rather than
    a mutation of the real ones. The production predicates are the ones called,
    so the planted cases reach each rule over the path ``TestTheRealTree`` does.
    """

    @pytest.fixture
    def tree(self, tmp_path: Path) -> tuple[Path, Path]:
        return tmp_path / ".github", tmp_path / ".github" / "lane-inputs"

    def test_a_read_outside_the_on_filter_is_reported_with_its_path(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/backend/**"]))
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml",
                "build",
                reads=["src/backend/app.py", "spec/nfr/NFR-006.md"],
                job_hash=_hash_of(github, "w.yml", "build"),
            ),
        )
        s = sweep(github, manifests)
        findings = coverage_findings(s, s.manifests[0])
        assert findings == [
            "w--build.yaml: job 'build' reads 'spec/nfr/NFR-006.md', which w.yml on:-level paths filter does not select"
        ]

    def test_the_same_read_inside_the_filter_is_not(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/backend/**", "spec/nfr/*.md"]))
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml",
                "build",
                reads=["src/backend/app.py", "spec/nfr/NFR-006.md"],
                job_hash=_hash_of(github, "w.yml", "build"),
            ),
        )
        s = sweep(github, manifests)
        assert coverage_findings(s, s.manifests[0]) == []

    def test_a_directory_listing_needs_the_directory_covered(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/backend/app/**"]))
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml",
                "build",
                reads=["src/backend/app/", "src/backend/tests/", "./"],
                job_hash=_hash_of(github, "w.yml", "build"),
            ),
        )
        s = sweep(github, manifests)
        uncovered = uncovered_reads(s, s.manifests[0])
        assert sorted(uncovered) == ["./", "src/backend/tests/"], (
            "the listed app/ directory is covered; tests/ and the root are not"
        )

    def test_a_paths_ignore_trigger_fires_for_everything_it_does_not_name(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(
            github,
            "workflows/w.yml",
            """
            name: planted
            on:
              push:
                paths-ignore:
                  - 'docs/**'
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - run: make
            """,
        )
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml", "build", reads=["src/a.py", "docs/index.md"], job_hash=_hash_of(github, "w.yml", "build")
            ),
        )
        s = sweep(github, manifests)
        assert sorted(uncovered_reads(s, s.manifests[0])) == ["docs/index.md"]

    def test_an_unfiltered_pull_request_trigger_covers_everything_the_push_filter_excludes(
        self, tree: tuple[Path, Path]
    ) -> None:
        """``frontend.yml``'s construction: the workflow is on-filtered on push only."""
        github, manifests = tree
        _plant(
            github,
            "workflows/w.yml",
            """
            name: planted
            on:
              push:
                paths:
                  - 'src/frontend/**'
              pull_request:
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - run: make
            """,
        )
        _plant(
            manifests,
            "w--build.yaml",
            _manifest("w.yml", "build", reads=["scripts/x.py"], job_hash=_hash_of(github, "w.yml", "build")),
        )
        s = sweep(github, manifests)
        assert s.workflows[0].on_filtered
        assert uncovered_reads(s, s.manifests[0]) == {}

    def test_a_read_outside_a_paths_filter_allow_list_is_reported(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_step_filter(["src/backend/**", "Taskfile.yaml"]))
        _plant(
            manifests,
            "w--integration.yaml",
            _manifest(
                "w.yml",
                "integration",
                reads=["src/backend/app.py", "Taskfile.yaml", ".taskfiles/backend.yaml"],
                gate_kind="paths-filter",
                filters=["integration"],
                job_hash=_hash_of(github, "w.yml", "integration"),
            ),
        )
        s = sweep(github, manifests)
        assert coverage_findings(s, s.manifests[0]) == [
            "w--integration.yaml: job 'integration' reads '.taskfiles/backend.yaml', "
            "which w.yml paths-filter integration does not select"
        ]

    def test_a_deny_list_under_every_covers_what_it_does_not_exclude(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(
            github, "workflows/w.yml", _workflow_with_step_filter(["**", "!docs/**", "!**/*.md"], quantifier="every")
        )
        _plant(
            manifests,
            "w--integration.yaml",
            _manifest(
                "w.yml",
                "integration",
                reads=["src/a.py", "docs/a.txt", "README.md", "src/b/README.md"],
                gate_kind="paths-filter",
                filters=["integration"],
                job_hash=_hash_of(github, "w.yml", "integration"),
            ),
        )
        s = sweep(github, manifests)
        assert sorted(uncovered_reads(s, s.manifests[0])) == ["README.md", "docs/a.txt", "src/b/README.md"]

    def test_a_filtered_job_without_a_manifest_is_reported(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/**"]))
        _plant(github, "workflows/s.yml", _workflow_with_step_filter(["src/**"]))
        manifests.mkdir(parents=True)
        findings = missing_manifests(sweep(github, manifests))
        assert len(findings) == 2
        joined = "\n".join(findings)
        assert "w.yml: job 'build' runs behind an on:-level paths filter and has no manifest" in joined
        assert "s.yml: paths-filter filter 'integration' gates a job that no manifest claims" in joined

    def test_a_manifest_measured_against_an_older_job_is_reported(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/**"]))
        _plant(manifests, "w--build.yaml", _manifest("w.yml", "build", reads=["src/a.py"], job_hash="0" * 64))
        findings = stale_manifests(sweep(github, manifests))
        assert len(findings) == 1 and "changed since it was measured" in findings[0]

    def test_a_comment_in_the_job_does_not_stale_its_manifest(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        body = _workflow_with_on_filter(["src/**"])
        _plant(github, "workflows/w.yml", body)
        digest = _hash_of(github, "w.yml", "build")
        _plant(
            github,
            "workflows/w.yml",
            body.replace(
                "      - run: make\n", "      # a comment, which is not a change to the job\n      - run: make\n"
            ),
        )
        _plant(manifests, "w--build.yaml", _manifest("w.yml", "build", reads=["src/a.py"], job_hash=digest))
        assert stale_manifests(sweep(github, manifests)) == []

    def test_editing_the_filter_patterns_does_not_stale_the_manifest_but_editing_a_step_does(
        self, tree: tuple[Path, Path]
    ) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_step_filter(["src/**"]))
        digest = _hash_of(github, "w.yml", "integration")
        _plant(
            manifests,
            "w--integration.yaml",
            _manifest(
                "w.yml",
                "integration",
                reads=["src/a.py"],
                gate_kind="paths-filter",
                filters=["integration"],
                job_hash=digest,
            ),
        )
        _plant(github, "workflows/w.yml", _workflow_with_step_filter(["src/**", "Taskfile.yaml"]))
        assert stale_manifests(sweep(github, manifests)) == [], (
            "the patterns are compared live; widening them is not a change to what the job reads"
        )
        _plant(
            github,
            "workflows/w.yml",
            _workflow_with_step_filter(["src/**", "Taskfile.yaml"]).replace(
                "run: pytest\n", "run: pytest tests/more\n"
            ),
        )
        assert len(stale_manifests(sweep(github, manifests))) == 1, "a changed step is a different job"

    def test_an_accepted_gap_needs_a_reason_and_must_match_an_uncovered_read(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/**"]))
        gaps = [
            {"pattern": "spec/**", "reason": "short"},
            {
                "pattern": "docs/**",
                "reason": "nothing under docs/ is read any more, this entry survived a re-measurement",
            },
        ]
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml",
                "build",
                reads=["src/a.py", "spec/x.md"],
                job_hash=_hash_of(github, "w.yml", "build"),
                gaps=gaps,
            ),
        )
        s = sweep(github, manifests)
        findings = coverage_findings(s, s.manifests[0])
        assert any("accepted_gaps[0] carries no reason" in f for f in findings)
        assert any("accepted_gaps[1] ('docs/**') matches no read outside the filter" in f for f in findings)
        assert not any("reads 'spec/x.md'" in f for f in findings), (
            "the gap with the short reason still explains the read; the reason is the finding"
        )

    def test_a_delegating_gap_is_held_against_the_named_lane(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_on_filter(["src/**"]))
        _plant(
            github,
            "workflows/guards.yml",
            """
            name: guards
            on:
              push:
            jobs:
              guards:
                runs-on: ubuntu-latest
                steps:
                  - run: pytest tests/unit/guards
            """,
        )
        _plant(
            github,
            "workflows/filtered.yml",
            """
            name: filtered
            on:
              push:
                branches: [develop]
            jobs:
              guards:
                runs-on: ubuntu-latest
                steps:
                  - run: pytest tests/unit/guards
            """,
        )
        reason = (
            "these reads belong to tests/unit/guards, which the unfiltered required lane runs on every pull request"
        )
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml",
                "build",
                reads=["src/a.py", "renovate.json5", "spec/nfr/NFR-006.md"],
                job_hash=_hash_of(github, "w.yml", "build"),
                gaps=[
                    {"pattern": "renovate.json5", "reason": reason, "covered_by": "guards.yml/guards"},
                    {"pattern": "spec/nfr/NFR-006.md", "reason": reason, "covered_by": "filtered.yml/guards"},
                ],
            ),
        )
        _plant(
            manifests,
            "guards--guards.yaml",
            _manifest(
                "guards.yml",
                "guards",
                reads=["tests/unit/guards/test_x.py"],
                job_hash=_hash_of(github, "guards.yml", "guards"),
            ),
        )
        s = sweep(github, manifests)
        findings = coverage_findings(s, next(m for m in s.manifests if m.job == "build"))
        assert any("covered_by 'guards.yml/guards' does not read ['renovate.json5']" in f for f in findings), findings
        assert any("covered_by 'filtered.yml/guards' is not an unfiltered lane" in f for f in findings), findings

    def test_the_decision_shape_rule_fires_on_each_of_its_three_properties(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        contexts = {"Integration tests (ArangoDB)"}
        _plant(github, "workflows/ok.yml", _workflow_with_step_filter(["src/**"]))
        assert decision_shape_findings(sweep(github, manifests), contexts) == []
        _plant(github, "workflows/ok.yml", _workflow_with_step_filter(["src/**"], job_if="github.event_name == 'push'"))
        assert any("carries a job-level if:" in f for f in decision_shape_findings(sweep(github, manifests), contexts))
        _plant(github, "workflows/ok.yml", _workflow_with_step_filter(["src/**"], coe=True))
        assert any("continue-on-error" in f for f in decision_shape_findings(sweep(github, manifests), contexts))
        _plant(github, "workflows/ok.yml", _workflow_with_step_filter(["src/**"], default="false"))
        assert any(
            "not true — the default must be RUN" in f
            for f in decision_shape_findings(sweep(github, manifests), contexts)
        )

    def test_the_decision_shape_rule_ignores_an_advisory_lane(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(
            github,
            "workflows/adv.yml",
            _workflow_with_step_filter(["src/**"], job_if="github.event_name == 'push'", coe=True, default="false"),
        )
        assert decision_shape_findings(sweep(github, manifests), {"something else"}) == []

    def test_a_commented_out_pattern_covers_nothing(self, tree: tuple[Path, Path]) -> None:
        """A pattern that survives only as a YAML comment is not a pattern, at ``on:`` or in ``filters:``.

        The filters are read parsed, never as text, so the line ``# - 'Taskfile.yaml'``
        cannot make the guard believe ``Taskfile.yaml`` is selected.
        """
        github, manifests = tree
        on_body = _workflow_with_on_filter(["src/backend/**"]).replace("jobs:\n", "      # - 'spec/**'\njobs:\n")
        _plant(github, "workflows/w.yml", on_body)
        _plant(
            manifests,
            "w--build.yaml",
            _manifest(
                "w.yml", "build", reads=["src/backend/app.py", "spec/x.md"], job_hash=_hash_of(github, "w.yml", "build")
            ),
        )
        step_body = _workflow_with_step_filter(["src/backend/**"]).replace(
            "              - 'src/backend/**'\n",
            "              - 'src/backend/**'\n              # - 'Taskfile.yaml'\n",
        )
        _plant(github, "workflows/s.yml", step_body)
        _plant(
            manifests,
            "s--integration.yaml",
            _manifest(
                "s.yml",
                "integration",
                reads=["src/backend/app.py", "Taskfile.yaml"],
                gate_kind="paths-filter",
                filters=["integration"],
                job_hash=_hash_of(github, "s.yml", "integration"),
            ),
        )
        s = sweep(github, manifests)
        findings = [finding for m in s.manifests for finding in coverage_findings(s, m)]
        assert findings == [
            "s--integration.yaml: job 'integration' reads 'Taskfile.yaml', "
            "which s.yml paths-filter integration does not select",
            "w--build.yaml: job 'build' reads 'spec/x.md', which w.yml on:-level paths filter does not select",
        ]

    def test_a_commented_default_does_not_satisfy_the_decision_shape_rule(self, tree: tuple[Path, Path]) -> None:
        """``# RUN=true`` above ``RUN=false`` is prose; the executable default is still false."""
        github, manifests = tree
        contexts = {"Integration tests (ArangoDB)"}
        body = _workflow_with_step_filter(["src/**"], default="false").replace(
            "          RUN=false\n", "          # RUN=true is the documented default\n          RUN=false\n"
        )
        _plant(github, "workflows/ok.yml", body)
        findings = decision_shape_findings(sweep(github, manifests), contexts)
        assert any("not true — the default must be RUN" in f for f in findings), findings

    def test_a_manifest_naming_a_filter_the_workflow_lacks_is_malformed(self, tree: tuple[Path, Path]) -> None:
        github, manifests = tree
        _plant(github, "workflows/w.yml", _workflow_with_step_filter(["src/**"]))
        _plant(
            manifests,
            "w--integration.yaml",
            _manifest(
                "w.yml",
                "integration",
                reads=["src/a.py"],
                gate_kind="paths-filter",
                filters=["frontend"],
                job_hash=_hash_of(github, "w.yml", "integration"),
            ),
        )
        findings = malformed_manifests(sweep(github, manifests))
        assert findings == ["w--integration.yaml: claims paths-filter filter 'frontend', which w.yml does not define"]


class TestTheMatcherAgreesWithTheDocumentedSemantics:
    """Each case would go the other way under a naive ``fnmatch`` translation."""

    @pytest.mark.parametrize(
        ("pattern", "path", "expected"),
        [
            ("src/backend/**", "src/backend/app/main.py", True),
            ("src/backend/**", "src/backend-old/main.py", False),
            ("src/*.py", "src/a/b.py", False),  # `*` never crosses `/`
            ("**/*.md", "README.md", True),  # a leading `**/` matches zero directories
            ("**/*.md", "docs/de/index.md", True),
            ("**", "anything/at/all", True),
            ("docs/**", "docs", False),  # the directory itself is not its content
            ("Taskfile.yaml", "Taskfile.yaml", True),
            ("Taskfile.yaml", "Taskfile.yml", False),  # `.` is literal
            ("src/backend/Dockerfile*", "src/backend/Dockerfile.dev", True),
            ("tests/security/zap-**", "tests/security/zap-rules.tsv", True),
        ],
    )
    def test_case(self, pattern: str, path: str, expected: bool) -> None:
        assert _matches(pattern, path) is expected

    def test_probe_paths(self) -> None:
        assert probe_path("src/backend/") == f"src/backend/{_PROBE}"
        assert probe_path("./") == _PROBE
        assert probe_path("src/a.py") == "src/a.py"
