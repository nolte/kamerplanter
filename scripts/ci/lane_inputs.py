#!/usr/bin/env python3
"""Record what a CI lane READS, so its relevance filter can be held against that.

A path filter — ``on.<event>.paths`` on a workflow, or a ``dorny/paths-filter``
step inside a job — is a claim: "no change outside these paths can alter this
job's verdict". Until #1596 the only thing that claim was ever checked against
was the text of the workflow (``scripts/check_workflow_gate_integrity.py``,
shape 5): the paths the workflow *mentions*. The property the filter must have
is about the paths the job *reads*, and the two differ by construction. The
``Write-route and tree guards`` lane says ``pytest tests/unit/api
tests/unit/guards`` and stops; what it reads includes 57 files under
``src/frontend/src/api/endpoints/``, every workflow file, ``renovate.json5``, and
eight ``pyproject.toml`` / ``uv.lock`` pairs outside its package. None of that is
in the text, so a shape-5 check would certify a filter that excluded the
frontend outright.

This script is the measuring instrument. It runs the lane's own invocation
under ``strace`` and records every **tracked** file the process tree opened
and every directory it enumerated, as one manifest per job under
``.github/lane-inputs/``. The guard
``src/backend/tests/unit/guards/test_lane_filters_cover_measured_inputs.py``
then holds every filter in ``.github/`` against its job's manifest — and refuses
a filtered job that has no manifest at all, which is what keeps this from being
one more opt-in list.

Why ``strace`` and not ``sys.addaudithook``
-------------------------------------------

The audit hook that produced #1596's first measurement sees only the Python
interpreter it is installed in. A file read by a subprocess — ``git log`` in
``test_model_field_renames_have_migrations.py``, ``task`` reading the Taskfiles,
``uv`` reading the lock, ``npx tsc`` reading the whole frontend — is invisible
to it, and a guard fed by that instrument would certify the class closed while
a subprocess reads outside the filter. ``strace -f`` follows every child, in
every language, at the syscall boundary, which is the only place "the job read
this file" is actually decided. The programs it followed as subprocesses are listed in
the manifest — by name, or repo-relative when they live in the checkout — so a
reviewer can see the instrument covered ``git``, ``task``, ``uv`` or ``node``
rather than take it on trust. Where a job's reads happen inside a container the daemon runs
(``docker build``), ``strace`` on the client cannot follow; :func:`derive_docker`
asks Docker itself which files a build context contains, applying the same
``.dockerignore`` the real build would, and narrows that to the ``COPY``/``ADD``
sources of the Dockerfile. Such a manifest is marked ``status: derived`` and
says how.

What counts as a read
---------------------

* a successful ``open``/``openat`` of a regular file under the checkout that
  ``git ls-files`` knows — untracked and generated files cannot appear in a
  pull request's diff, so no filter needs to cover them;
* a directory enumeration (``getdents64``) of a directory under the checkout,
  recorded with a trailing ``/`` — a job that lists a directory changes its
  verdict when a file is *added* there, which a filter can only express by
  covering the directory. ``_REPO_ROOT.rglob("pyproject.toml")`` is why: a new
  ``pyproject.toml`` anywhere in the tree changes the guards lane's verdict.

A ``stat``-only probe (``Path.exists()``) is deliberately **not** a read: it
depends on the file's presence, not its content, and recording it would turn
pytest's rootdir walk — which stats every ancestor for ``pytest.ini`` — into a
claim that every lane reads the checkout root.

Usage::

    # measure a job, from the directory its steps run in
    python3 scripts/ci/lane_inputs.py record \\
        --workflow backend-guards.yml --job integration --filter integration \\
        --cwd src/backend -- task test:backend:integration

    # add a second invocation of the same job to its manifest
    python3 scripts/ci/lane_inputs.py record --append ... -- task lint:backend

    # an invocation whose non-zero exit is its verdict, not a crash: say which
    # reads the failure path may have skipped (the guard refuses a bare failure)
    python3 scripts/ci/lane_inputs.py record --append \\
        --allow-failure 'exits 1 on develop by design: … reads it could not make: …' \\
        ... -- python3 scripts/check_chart_image_digests.py

    # a recording that is knowingly a SUBSET of the job's invocation: the
    # manifest is marked `status: partial` and the guard holds that against the
    # job's filter until the full invocation is recorded
    python3 scripts/ci/lane_inputs.py record \\
        --partial 'recorded from one test file to bootstrap; the full run is recorded in CI (#1683)' \\
        ... -- pytest tests/unit/one_file.py

    # a docker-built job: what the build context hands the daemon
    python3 scripts/ci/lane_inputs.py derive-docker \\
        --workflow docker-lint-build.yml --job build-backend --filter backend \\
        --context src/backend --dockerfile src/backend/Dockerfile

    python3 scripts/ci/lane_inputs.py show .github/lane-inputs/<name>.yaml

Where the manifests are actually recorded (#1683)
-------------------------------------------------

The commands above are the instrument; the place it is meant to run is the
advisory CI lane ``.github/workflows/lane-inputs.yml``, where the environment
is the real one (Linux, ``strace``, Docker, an ArangoDB service). That lane
does not keep a second list of what to run. It reads every manifest's own
``invocations`` and replays them::

    # the matrix: one leg per manifest with invocations, plus one per
    # `covered_by` delegation target that has no manifest yet (bootstrap)
    python3 scripts/ci/lane_inputs.py plan --github-output "$GITHUB_OUTPUT"

    # one leg: re-run the manifest's invocations under the recorder, writing a
    # fresh manifest into --out-dir; hand-written fields (gate, accepted_gaps,
    # unrecorded_invocations) are carried over, measured ones are re-measured
    python3 scripts/ci/lane_inputs.py replay --out-dir "$OUT_DIR" .github/lane-inputs/<name>.yaml

    # a delegation target without a manifest: its invocations are the job's own
    # held `run:` commands, read from the workflow
    python3 scripts/ci/lane_inputs.py replay --out-dir "$OUT_DIR" backend-guards.yml/guards

    # the verdict: committed vs recorded — new reads OUTSIDE the job's relevance filter,
    # job hash (action pins excluded), status, invocations, empty recordings
    python3 scripts/ci/lane_inputs.py compare recorded/lane-inputs --run-id "$GITHUB_RUN_ID"

A hand-edited ``reads:`` that drops a path outside the job's relevance filter
therefore disagrees with the next CI recording and fails ``compare``; a read
inside the filter that a later change adds is not drift (#1683) — the filter
already runs the job for it. A replay runs pytest with the manifest guard
deselected (:data:`REPLAY_DESELECTED_GUARD`), so a stale manifest cannot stop
the unit-suite legs from recording its successor. To refresh a manifest, download what CI recorded and commit
it, rather than re-measuring on a workstation::

    gh run download <run-id> -n lane-inputs -D /tmp/lane-inputs-<run-id>
    cp /tmp/lane-inputs-<run-id>/*.yaml .github/lane-inputs/

Absolute paths under ``/tmp/`` in a recorded command or ``env`` value are
scratch OUTPUT locations (an ``--out`` file, a ``UV_PROJECT_ENVIRONMENT``). A
replay maps each to ``SCRATCH_DIR/<basename>`` and ``compare`` normalises both
sides the same way, so a manifest recorded on a workstation and one recorded in
CI agree on the command when they agree on everything else.

Two things a replay reproduces from the real job rather than from a list kept
here. ``PATH``: a step that runs ``echo "$PWD/<dir>" >> "$GITHUB_PATH"`` (the
side-services and backend installs put their venv on ``PATH`` that way, and the
job's later ``python -m pytest`` resolves to it) is read from the workflow by
:func:`job_path_additions` and prepended for the replay — without it the replay
ran the runner's bare interpreter, ``No module named pytest``. Scratch INPUTS:
an invocation that reads a file a step before it produced and the lane cannot
produce (the ZAP report ``zap_gate.py`` judges comes out of a scan) records the
stand-in it was measured with as ``scratch_inputs: {<basename>: <content>}``
(``record --scratch-input NAME=CONTENT``); the replay writes it to
``SCRATCH_DIR/<basename>`` before tracing, and ``compare`` compares it like the
command, so the stand-in is on record instead of assumed.

Standard library plus PyYAML. Traces to #1596 (no TC-ID: a source-tree gate is
not a user-facing case).
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import functools
import glob as globmodule
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = REPO_ROOT / ".github" / "lane-inputs"
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

#: Manifest schema version. Bump when a field's meaning changes, so the guard
#: can refuse a manifest written under an older contract instead of misreading it.
#: 2 (review round of #1682): `status: partial` + `partial_reason`,
#: `invocations[].allow_failure_reason`, `unrecorded_invocations`. The guard's
#: `_SCHEMA` is the same number and the recorder test pins the two together.
SCHEMA = 2

#: A reason shorter than this is a label, not a reason (the guard's `_MIN_REASON_CHARS`).
MIN_REASON_CHARS = 40

# ------------------------------------------------------- per-leg replay timeout
#
# `replay` measures the wall clock of its own run and writes it into the
# manifest it produces as `replay_seconds` — a measurement like `reads`, written
# by this tool only (a workstation `record` drops it, `compare` does not compare
# it). `plan` turns it into the leg's `timeout_minutes`, which lane-inputs.yml
# puts on the replay STEP; the record job keeps its own `timeout-minutes` as the
# outer bound. Before this (#1683, 2026-09-24) one 90-minute job bound held a
# hung 2-minute leg (frontend--lighthouse, > 60 min in the replay step) as long
# as the slowest real one.
#
# Per manifest, not per invocation: the step the bound applies to runs ONE
# `replay`, i.e. every invocation of the manifest plus the recorder's own git
# calls between them, so that whole span is the quantity measured.

#: Headroom over one recorded duration. Measured over the five runs of
#: 2026-09-24 (35979465184, 35997205619, 36003779768, 36003712853, 36014274408):
#: for every leg whose replay took longer than a minute, the slowest successful
#: replay was at most 1.75× its fastest (backend-guards--integration 225–394 s,
#: backend--coverage 1222–1756 s). 3× clears that spread from whichever run was
#: recorded, while a hang — frontend--lighthouse at > 30× its usual 78–117 s — is
#: cut off at a tenth of the old bound.
TIMEOUT_FACTOR = 3
#: Short legs replay in seconds (a docker-derived leg in 0–24 s), where the
#: runner's own jitter (a cold uv cache, a slow `git ls-files`) dominates the
#: measurement; three times a few seconds is no bound anyone could rely on.
TIMEOUT_FLOOR_MINUTES = 10
#: The record job's own `timeout-minutes` in lane-inputs.yml (pinned by the
#: recorder test): a step bound above it would never fire, and a leg that has
#: never been measured (a bootstrap, or a manifest recorded on a workstation) gets
#: exactly the bound it had before.
TIMEOUT_CAP_MINUTES = 90
#: A replay that completed cannot have taken longer than the job that ran it, so
#: a larger value was not written by this tool (the guard's `_REPLAY_SECONDS_MAX`).
REPLAY_SECONDS_MAX = TIMEOUT_CAP_MINUTES * 60

#: The syscalls that decide "this file was read". ``openat``/``open`` for files,
#: ``getdents64`` for directory listings, ``execve`` so the followed subprocesses
#: are on record. ``readlink`` is included because a symlink's target is what a
#: ``git ls-files`` entry actually stores.
_TRACED_SYSCALLS = "openat,open,openat2,getdents64,execve,execveat,readlink,readlinkat"

#: ``-ttt`` puts a ``<seconds>.<microseconds>`` stamp before every call (#1749);
#: a pid prefix only appears without ``-ff``. Both are optional so a trace
#: written by either spelling parses.
_PREFIX = r"^(?:\d+\s+)?(?:(?P<ts>\d+\.\d+)\s+)?"
_OPEN_LINE = re.compile(_PREFIX + r"(?:open|openat|openat2)\((?P<args>.*)\)\s*=\s*(?P<fd>\d+)<(?P<path>[^>]*)>")
_GETDENTS_LINE = re.compile(_PREFIX + r"getdents64\((?P<fd>\d+)<(?P<path>[^>]*)>")
_EXECVE_LINE = re.compile(_PREFIX + r'execve(?:at)?\((?:\d+<[^>]*>,\s*)?"(?P<program>[^"]*)",\s*\[(?P<argv>.*?)\],')
_READLINK_LINE = re.compile(_PREFIX + r'readlink(?:at)?\((?:(?:AT_FDCWD|\d+<[^>]*>),\s*)?"(?P<path>[^"]*)",')
_ARGV_ITEM = re.compile(r'"((?:[^"\\]|\\.)*)"')

# ------------------------------------------------------- per-test attribution
#
# #1749: a delegated read (`accepted_gaps[].covered_by`) used to be held against
# the covering lane by PATH — "the guards lane reads it too". A new test in the
# delegating lane that reads a path some covering-lane test already reads kept
# that green while the new test itself ran only in the filtered lane. The
# recorder therefore attributes every read of a pytest invocation to the test
# MODULE that was active when it happened: the plugin below opens a marker file
# at each collection and each test (`scripts/ci/lane_inputs_pytest/`), strace
# stamps every call with `-ttt`, and a read belongs to the last marker before
# it — in whichever process of the tree it happened, so a subprocess or a thread
# a test started is the test's read too. What is recorded:
#
# * `test_modules` — every module of which at least one test RAN (a deselected
#   or skipped-at-collection module is not in it: it did not run there);
# * `readers` — `{module: [reads]}`, only the reads the job's own relevance
#   filter does NOT select: the only reads an accepted gap can explain, so the
#   only ones a delegation can be about.
#
# Reads outside any test (pytest start-up, conftest collection, a non-pytest
# invocation) have no reader and stay held by path only.

#: Where the marker plugin lives; put on PYTHONPATH for a recording, and its own
#: reads (the import, the directory listing) are the instrument's, not the job's.
MARKER_PLUGIN_DIR = REPO_ROOT / "scripts" / "ci" / "lane_inputs_pytest"
MARKER_PLUGIN = "lane_inputs_markers"
_MARKER_PLUGIN_PREFIX = MARKER_PLUGIN_DIR.relative_to(REPO_ROOT).as_posix() + "/"
_MARKERS_ENV = "LANE_INPUTS_MARKERS"
_MARKER_ROOT_ENV = "LANE_INPUTS_REPO_ROOT"
_MARKER_OWNER_ENV = "LANE_INPUTS_MARKER_PID"
#: A reader key for reads no test module made.
NO_READER = ""

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

#: Where a replay puts a recorded invocation's scratch outputs (see the module docstring).
SCRATCH_DIR = Path("/tmp/lane-inputs-scratch")
_SCRATCH_PATH = re.compile(r"/tmp/[^\s'\";|&<>()]+")

#: The gate kinds a manifest may declare. ``unfiltered`` is a job with no relevance
#: filter at all, recorded because another manifest delegates to it (``covered_by``).
GATE_KINDS = ("on-paths", "paths-filter", "unfiltered")


class LaneInputsError(Exception):
    """A usage or environment problem, reported without a traceback."""


def replay_seconds_problem(manifest: dict[str, Any]) -> str | None:
    """Why *manifest*'s ``replay_seconds`` is not a measurement this tool could have written, or ``None``.

    A whole number of seconds (rounded up, so at least 1) no larger than the job
    that ran the replay allows. ``bool`` is excluded explicitly: YAML's ``true``
    is an ``int`` to Python.
    """
    if "replay_seconds" not in manifest:
        return "has no `replay_seconds`"
    value = manifest["replay_seconds"]
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= REPLAY_SECONDS_MAX:
        return (
            f"`replay_seconds: {value!r}` is not a whole number of seconds between 1 and {REPLAY_SECONDS_MAX} "
            f"(the record job's own bound)"
        )
    return None


def leg_timeout_minutes(manifest: dict[str, Any] | None) -> int:
    """The replay step's bound for one leg: TIMEOUT_FACTOR × the measured replay, floored and capped.

    ``None`` (a bootstrap leg, no manifest yet) and a manifest without a usable
    measurement get the cap — the bound every leg had before it was measured.
    """
    if manifest is None or replay_seconds_problem(manifest) is not None:
        return TIMEOUT_CAP_MINUTES
    minutes = math.ceil(TIMEOUT_FACTOR * int(manifest["replay_seconds"]) / 60)
    return min(TIMEOUT_CAP_MINUTES, max(TIMEOUT_FLOOR_MINUTES, minutes))


def with_replay_seconds(manifest: dict[str, Any], seconds: int) -> dict[str, Any]:
    """*manifest* with ``replay_seconds`` placed after ``measured_at_commit``, beside the other run facts."""
    out: dict[str, Any] = {}
    for key, value in manifest.items():
        if key == "replay_seconds":
            continue
        out[key] = value
        if key == "measured_at_commit":
            out["replay_seconds"] = seconds
    out.setdefault("replay_seconds", seconds)
    return out


@dataclass
class Trace:
    """What one traced invocation touched, before the tracked-file filter."""

    files: set[str] = field(default_factory=set)
    listings: set[str] = field(default_factory=set)
    execs: list[list[str]] = field(default_factory=list)
    returncode: int = 0
    #: #1749: repo-relative test modules at least one test of which ran.
    test_modules: set[str] = field(default_factory=set)
    #: #1749: ``module -> raw paths`` it opened / listed while it was the active module.
    reader_files: dict[str, set[str]] = field(default_factory=dict)
    reader_listings: dict[str, set[str]] = field(default_factory=dict)


@dataclass
class MarkerTimeline:
    """The marker plugin's markers in the order the marking process set them (#1749)."""

    stamps: list[float] = field(default_factory=list)
    readers: list[str] = field(default_factory=list)

    def reader_at(self, stamp: float | None) -> str:
        """The module active at *stamp*: the last marker set at or before it."""
        if stamp is None or not self.stamps:
            return NO_READER
        index = bisect.bisect_right(self.stamps, stamp) - 1
        return self.readers[index] if index >= 0 else NO_READER


def marker_env(env: dict[str, str], marker_dir: Path) -> dict[str, str]:
    """*env* with the marker plugin loaded into every pytest the invocation starts."""
    out = dict(env)
    out[_MARKERS_ENV] = str(marker_dir)
    out[_MARKER_ROOT_ENV] = str(REPO_ROOT)
    out.pop(_MARKER_OWNER_ENV, None)
    out["PYTHONPATH"] = os.pathsep.join(p for p in (str(MARKER_PLUGIN_DIR), out.get("PYTHONPATH", "")) if p)
    out["PYTEST_ADDOPTS"] = " ".join(p for p in (out.get("PYTEST_ADDOPTS", "").strip(), f"-p {MARKER_PLUGIN}") if p)
    return out


def marker_timeline(trace_files: list[Path], marker_dir: Path) -> MarkerTimeline:
    """Every marker the plugin opened, from the one process that sets them, in its own order."""
    prefix = f"{marker_dir}/"
    timeline = MarkerTimeline()
    for path in trace_files:
        with path.open("r", encoding="utf-8", errors="surrogateescape") as handle:
            for line in handle:
                if prefix not in line:
                    continue
                match = _OPEN_LINE.match(line)
                if not match or not match.group("path").startswith(prefix) or match.group("ts") is None:
                    continue
                kind, _, quoted = match.group("path")[len(prefix) :].partition("~")
                module = urllib.parse.unquote(quoted) if kind in ("collect", "run") else NO_READER
                timeline.stamps.append(float(match.group("ts")))
                timeline.readers.append(module)
    order = sorted(range(len(timeline.stamps)), key=lambda i: timeline.stamps[i])
    return MarkerTimeline([timeline.stamps[i] for i in order], [timeline.readers[i] for i in order])


# --------------------------------------------------------------------------- git


def tracked_files(repo_root: Path = REPO_ROOT) -> frozenset[str]:
    """Every path the index knows, repo-relative, POSIX separators."""
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    return frozenset(entry.decode("utf-8", "surrogateescape") for entry in completed.stdout.split(b"\0") if entry)


def head_commit(repo_root: Path = REPO_ROOT) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def implied_directories(files: frozenset[str]) -> frozenset[str]:
    """Every directory a tracked file implies, plus ``""`` for the root."""
    directories: set[str] = {""}
    for entry in files:
        parent = entry.rpartition("/")[0]
        while parent and parent not in directories:
            directories.add(parent)
            parent = parent.rpartition("/")[0]
    return frozenset(directories)


# ------------------------------------------------------------------------ strace


def strace_binary() -> str:
    found = shutil.which("strace")
    if found is None:
        raise LaneInputsError(
            "strace is not on PATH. The recorder follows subprocesses at the syscall "
            "boundary and has no weaker mode on purpose: an instrument that sees only "
            "the parent interpreter certifies a filter over reads it never saw (#1596)."
        )
    return found


def run_traced(command: list[str], *, cwd: Path, env: dict[str, str]) -> Trace:
    """Run *command* under ``strace -ff -y -z -ttt`` and parse every per-thread trace file.

    ``-ff`` writes one file per thread, so no line is ever split into
    ``<unfinished ...>`` / ``<... resumed>`` halves; ``-y`` decorates every file
    descriptor with the path it resolves to, which is how a relative ``openat``
    against a ``dirfd`` becomes an absolute path without re-implementing the
    kernel's resolution; ``-z`` keeps only successful calls, so a probe for a
    file that does not exist is never mistaken for a read of one; ``-ttt``
    stamps every call, which is what puts the reads of every process on the
    marker plugin's timeline (#1749).
    """
    strace = strace_binary()
    with tempfile.TemporaryDirectory(prefix="lane-inputs-") as scratch:
        prefix = Path(scratch) / "trace"
        marker_dir = Path(scratch) / "markers"
        marker_dir.mkdir()
        argv = [
            strace,
            "-ff",
            "-y",
            "-z",
            "-ttt",
            "-qq",
            "-s",
            "512",
            "-e",
            f"trace={_TRACED_SYSCALLS}",
            "-e",
            "signal=none",
            "-o",
            str(prefix),
            "--",
            *command,
        ]
        completed = subprocess.run(argv, cwd=cwd, env=marker_env(env, marker_dir), check=False)
        trace = Trace(returncode=completed.returncode)
        trace_files = sorted(Path(scratch).glob("trace.*"))
        timeline = marker_timeline(trace_files, marker_dir)
        for trace_file in trace_files:
            _parse_trace_file(trace_file, trace, timeline=timeline, marker_dir=marker_dir)
    return trace


def _stamp(match: re.Match[str]) -> float | None:
    return float(match.group("ts")) if match.group("ts") else None


def _parse_trace_file(
    path: Path, trace: Trace, *, timeline: MarkerTimeline | None = None, marker_dir: Path | None = None
) -> None:
    timeline = timeline or MarkerTimeline()
    marker_prefix = f"{marker_dir}/" if marker_dir is not None else None
    with path.open("r", encoding="utf-8", errors="surrogateescape") as handle:
        for line in handle:
            match = _OPEN_LINE.match(line)
            if match:
                if "O_DIRECTORY" in match.group("args"):
                    continue  # a directory open is a lookup; its listing is the getdents below
                opened = _clean(match.group("path"))
                if marker_prefix is not None and opened.startswith(marker_prefix):
                    kind, _, quoted = opened[len(marker_prefix) :].partition("~")
                    if kind == "run":
                        trace.test_modules.add(urllib.parse.unquote(quoted))
                    continue  # the instrument's own marker, not a read
                trace.files.add(opened)
                reader = timeline.reader_at(_stamp(match))
                if reader != NO_READER:
                    trace.reader_files.setdefault(reader, set()).add(opened)
                continue
            match = _GETDENTS_LINE.match(line)
            if match:
                listed = _clean(match.group("path"))
                trace.listings.add(listed)
                reader = timeline.reader_at(_stamp(match))
                if reader != NO_READER:
                    trace.reader_listings.setdefault(reader, set()).add(listed)
                continue
            match = _EXECVE_LINE.match(line)
            if match:
                argv = [_unescape(item) for item in _ARGV_ITEM.findall(match.group("argv"))]
                trace.execs.append(argv or [match.group("program")])
                continue
            match = _READLINK_LINE.match(line)
            if match:
                trace.files.add(_clean(match.group("path")))


def _clean(path: str) -> str:
    """Strip strace's decorations from a ``-y`` path."""
    for suffix in (" (deleted)",):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
    return path


def _unescape(item: str) -> str:
    return item.encode("latin-1", "backslashreplace").decode("unicode_escape")


def to_repo_relative(paths: set[str], *, repo_root: Path, cwd: Path) -> set[str]:
    """Absolute or cwd-relative paths → repo-relative POSIX paths under the checkout."""
    root = repo_root.resolve()
    out: set[str] = set()
    for raw in paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = cwd / candidate
        try:
            resolved = candidate.resolve(strict=False)
        except OSError:
            continue
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            continue
        out.add(relative.as_posix())
    return out


# ---------------------------------------------------------------------- workflow


def load_workflow(name: str) -> tuple[Path, dict[str, Any]]:
    path = WORKFLOW_DIR / name
    if not path.is_file():
        raise LaneInputsError(f"no workflow named {name!r} under {WORKFLOW_DIR}")
    document = yaml.safe_load(path.read_text())
    if not isinstance(document, dict):
        raise LaneInputsError(f"{path} did not parse to a mapping")
    return path, document


def job_spec_hash(document: dict[str, Any], job: str) -> str:
    """A hash of the PARSED job — comments and formatting do not count.

    This is the staleness anchor. A manifest recorded against one job
    definition says nothing about another: change a step, add a step, move the
    invocation, and the recorded read set is a claim about a job that no longer
    exists. Hashing the parsed mapping rather than the file text means a comment
    edit does not demand a re-measurement, while any executable change does.
    Hashing rather than recording a commit SHA, because ``develop`` is
    squash-merged and the recording commit would not survive the merge.
    """
    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or job not in jobs:
        raise LaneInputsError(f"job {job!r} is not defined in this workflow (jobs: {sorted(jobs or [])})")
    return hash_job_spec(jobs[job])


def hash_job_spec(job: Any) -> str:
    """SHA-256 of the parsed job, minus paths-filter patterns and minus the ref of every ``uses:``.

    The patterns are held against the manifest LIVE by the guard; they are not
    an input to what the job reads, so editing them must not demand a
    re-measurement. The same holds for the ``@<ref>`` of a ``uses:`` (#1683):
    the recorder replays a job's ``run:`` commands, never its actions, so an
    action's version cannot change the recorded read set — yet a Renovate
    digest bump (#1734, ``github/codeql-action`` v4.38.1 → v4.38.2) staled
    ``report-findings`` and reddened the next unrelated pull request. The
    action's NAME stays in the hash (another action is another job), as does
    everything else about the job — every step, every ``run:``, every
    ``with:``, ``env``, ``working-directory``. The guard computes the same
    function; keep the two identical.
    """
    canonical = json.dumps(
        _without_action_refs(_without_filter_patterns(job)), sort_keys=True, default=str, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def action_name(uses: str) -> str:
    """``owner/repo[/path]@ref`` → ``owner/repo[/path]``; a local ``./path`` has no ref and is itself."""
    return uses.split("@", 1)[0] if not uses.startswith("./") else uses


def _without_action_refs(job: Any) -> Any:
    """*job* with every ``uses:`` — a step's, and a reusable-workflow call's at job level — reduced to its name."""
    if not isinstance(job, dict):
        return job
    copy = dict(job)
    if isinstance(copy.get("uses"), str):
        copy["uses"] = action_name(copy["uses"])
    steps = copy.get("steps")
    if isinstance(steps, list):
        copy["steps"] = [
            {**step, "uses": action_name(step["uses"])}
            if isinstance(step, dict) and isinstance(step.get("uses"), str)
            else step
            for step in steps
        ]
    return copy


def _without_filter_patterns(job: Any) -> Any:
    if not isinstance(job, dict):
        return job
    copy = dict(job)
    steps = copy.get("steps")
    if isinstance(steps, list):
        cleaned = []
        for step in steps:
            if (
                isinstance(step, dict)
                and "paths-filter@" in str(step.get("uses", ""))
                and isinstance(step.get("with"), dict)
            ):
                step = dict(step)
                step["with"] = {key: value for key, value in step["with"].items() if key != "filters"}
            cleaned.append(step)
        copy["steps"] = cleaned
    return copy


def manifest_stem(workflow: str, job: str) -> str:
    return f"{workflow.rsplit('.', 1)[0]}--{job}"


def manifest_path(workflow: str, job: str, directory: Path | None = None) -> Path:
    return (directory or MANIFEST_DIR) / f"{manifest_stem(workflow, job)}.yaml"


def _display(path: Path) -> str:
    """Repo-relative when inside the checkout, absolute otherwise (a replay writes to a scratch dir)."""
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _target(args: argparse.Namespace) -> Path:
    directory = Path(args.manifest_dir).resolve() if getattr(args, "manifest_dir", None) else None
    return manifest_path(args.workflow, args.job, directory)


# ---------------------------------------------------------------------- manifest


def load_manifest(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    if not isinstance(document, dict):
        raise LaneInputsError(f"{path} did not parse to a mapping")
    return document


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Recorded by scripts/ci/lane_inputs.py — what this job READS, so its relevance\n"
        "# filter can be held against it (#1596). Do not edit `reads` by hand: the CI lane\n"
        "# .github/workflows/lane-inputs.yml replays the `invocations` below and fails when\n"
        "# its recording differs from this file (#1683). The guard is\n"
        "# src/backend/tests/unit/guards/test_lane_filters_cover_measured_inputs.py.\n"
    )
    body = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(header + body)


def _fresh_manifest(args: argparse.Namespace, document: dict[str, Any]) -> dict[str, Any]:
    if args.filter:
        kind = "paths-filter"
    elif getattr(args, "unfiltered", False):
        kind = "unfiltered"
    else:
        kind = "on-paths"
    gate: dict[str, Any] = {"kind": kind}
    if args.filter:
        names = [name.strip() for name in args.filter.split(",") if name.strip()]
        gate["filter"] = names[0] if len(names) == 1 else names
    return {
        "schema": SCHEMA,
        "workflow": args.workflow,
        "job": args.job,
        "gate": gate,
        "status": "measured",
        "measured_on": dt.date.today().isoformat(),
        "measured_at_commit": head_commit(),
        "job_spec_sha256": job_spec_hash(document, args.job),
        "invocations": [],
        "subprocesses": [],
        "accepted_gaps": [],
        "reads": [],
        "test_modules": [],
        "readers": {},
    }


def program_label(argv: list[str], *, cwd: Path, repo_root: Path = REPO_ROOT) -> str:
    """A machine-independent name for a followed subprocess.

    Repo-relative when the program lives inside the checkout
    (``scripts/ci/determine_chart_version.sh``, ``src/backend/.venv/bin/python``),
    its basename otherwise (``git``, ``task``, ``uv``, ``node``). The manifest
    is committed; an absolute path under ``$HOME`` or a ``uv`` build scratch
    directory would make every re-recording a diff and say nothing a reviewer
    needs — what matters is *which* programs the instrument followed.
    """
    program = argv[0] if argv else ""
    if not program:
        return "?"
    if "/" not in program:
        return program
    candidate = Path(program)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        return candidate.resolve(strict=False).relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return candidate.name


def tracked_reads(
    files: set[str], listings: set[str], *, tracked: frozenset[str], directories: frozenset[str]
) -> set[str]:
    """Repo-relative opens and listings → the manifest's read entries, minus the marker plugin's own."""
    reads = {entry for entry in files if entry in tracked}
    reads |= {f"{entry}/" if entry else "./" for entry in listings if entry in directories}
    return {read for read in reads if not read.startswith(_MARKER_PLUGIN_PREFIX)}


def _merge_into(
    manifest: dict[str, Any],
    *,
    invocation: dict[str, Any],
    reads: set[str],
    execs: list[list[str]],
    cwd: Path = REPO_ROOT,
    test_modules: set[str] | None = None,
    readers: dict[str, set[str]] | None = None,
) -> None:
    manifest["invocations"].append(invocation)
    known = set(manifest.get("reads") or [])
    manifest["reads"] = sorted(known | reads)
    # #1749: always written, empty included — a manifest without the keys was
    # recorded before per-test attribution existed, which the guard refuses to
    # read as "no test read anything".
    manifest["test_modules"] = sorted(set(manifest.get("test_modules") or []) | (test_modules or set()))
    merged: dict[str, set[str]] = {
        str(module): set(paths or []) for module, paths in (manifest.get("readers") or {}).items()
    }
    for module, paths in (readers or {}).items():
        merged.setdefault(module, set()).update(paths)
    manifest["readers"] = {module: sorted(merged[module]) for module in sorted(merged)}
    programs = {str(entry) for entry in manifest.get("subprocesses") or [] if isinstance(entry, str)}
    programs |= {program_label(argv, cwd=cwd) for argv in execs}
    manifest["subprocesses"] = sorted(programs)
    manifest["measured_on"] = dt.date.today().isoformat()
    manifest["measured_at_commit"] = head_commit()
    # The duration described the invocations as they were; with one added or
    # re-recorded it describes nothing. `replay` writes a fresh one after its
    # last invocation, a workstation `record` leaves the leg unmeasured (the cap).
    manifest.pop("replay_seconds", None)


# ----------------------------------------------------------------------- record


def command_record(args: argparse.Namespace) -> int:
    _path, document = load_workflow(args.workflow)
    if args.empty_reads_reason is not None:
        if args.command:
            raise LaneInputsError("--empty-reads-reason replaces the invocation; give one or the other")
        if len(args.empty_reads_reason.strip()) < 40:
            raise LaneInputsError(
                "--empty-reads-reason must say, in at least 40 characters, why the job reads nothing from the tree"
            )
        manifest = _fresh_manifest(args, document)
        manifest["empty_reads_reason"] = args.empty_reads_reason.strip()
        target = _target(args)
        write_manifest(target, manifest)
        print(
            f"lane-inputs: recorded an empty read set with its reason → {_display(target)}",
            file=sys.stderr,
        )
        return EXIT_OK
    if not args.command:
        raise LaneInputsError("record needs the invocation after `--`")
    cwd = (REPO_ROOT / args.cwd).resolve() if args.cwd else REPO_ROOT
    if not cwd.is_dir():
        raise LaneInputsError(f"--cwd {args.cwd!r} is not a directory")
    env = dict(os.environ)
    for assignment in args.env:
        key, _, value = assignment.partition("=")
        env[key] = value
    scratch_inputs = _scratch_inputs(args.scratch_input, args.command)
    if scratch_inputs:
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        for name, content in scratch_inputs.items():
            (SCRATCH_DIR / name).write_text(content, encoding="utf-8")

    # Settle the index first. Right after a checkout or a write, entries whose
    # stat data git cannot trust ("racily clean") make the next `git diff` or
    # `git status` OPEN every such file to compare its content — measured on
    # this tree: 622 tracked files opened by `git diff --quiet -- docs/requirements.txt`
    # before a refresh, none after. Those reads are an artefact of the index's
    # timing, not of the job, and recording them would demand a filter over
    # the whole checkout for a lane that reads one file.
    subprocess.run(["git", "-C", str(REPO_ROOT), "update-index", "-q", "--refresh"], check=False)
    print(f"lane-inputs: tracing {' '.join(args.command)!r} in {cwd.relative_to(REPO_ROOT) or '.'}", file=sys.stderr)
    trace = run_traced(list(args.command), cwd=cwd, env=env)
    if trace.returncode != 0 and not args.allow_failure:
        raise LaneInputsError(
            f"the invocation exited {trace.returncode}; a read set recorded from a failed run "
            "is a read set of the failure path. Fix the run, or pass --allow-failure REASON if the "
            "exit code is the invocation's verdict rather than a crash — REASON says which reads "
            "the failure path may have skipped, and the guard refuses a failed invocation without it."
        )

    tracked = tracked_files()
    directories = implied_directories(tracked)
    files = to_repo_relative(trace.files, repo_root=REPO_ROOT, cwd=cwd)
    listings = to_repo_relative(trace.listings, repo_root=REPO_ROOT, cwd=cwd)
    reads = tracked_reads(files, listings, tracked=tracked, directories=directories)
    dropped_untracked = len(files - tracked)

    target = _target(args)
    if args.append and target.is_file():
        manifest = load_manifest(target)
        if manifest.get("job") != args.job or manifest.get("workflow") != args.workflow:
            raise LaneInputsError(f"{target} belongs to another lane; refusing to append")
        manifest["job_spec_sha256"] = job_spec_hash(document, args.job)
    else:
        manifest = _fresh_manifest(args, document)

    invocation = {
        # `shlex.join`, not `" ".join`: an argument with spaces (`--onlyAllow 'MIT;ISC;MIT AND ISC'`)
        # must survive as one token, or the guard's rule 5 cannot match it to the job's `run:`.
        "command": shlex.join(args.command),
        "cwd": cwd.relative_to(REPO_ROOT).as_posix() or ".",
        "recorder": "strace -ff -y -z",
        "exit_code": trace.returncode,
        "env": sorted(args.env),
        "untracked_reads_dropped": dropped_untracked,
    }
    if scratch_inputs:
        invocation["scratch_inputs"] = scratch_inputs
    if trace.returncode != 0:
        invocation["allow_failure_reason"] = args.allow_failure.strip()
    live = relevance_filter(document, manifest)
    readers: dict[str, set[str]] = {}
    for module in set(trace.reader_files) | set(trace.reader_listings):
        read_by_module = tracked_reads(
            to_repo_relative(trace.reader_files.get(module, set()), repo_root=REPO_ROOT, cwd=cwd),
            to_repo_relative(trace.reader_listings.get(module, set()), repo_root=REPO_ROOT, cwd=cwd),
            tracked=tracked,
            directories=directories,
        )
        outside = {read for read in read_by_module if live.rejects(read)}
        if outside:
            readers[module] = outside
    _merge_into(
        manifest,
        invocation=invocation,
        reads=reads,
        execs=trace.execs,
        cwd=cwd,
        test_modules=trace.test_modules,
        readers=readers,
    )
    if args.partial is not None:
        manifest["status"] = "partial"
        manifest["partial_reason"] = args.partial.strip()
    elif manifest.get("status") != "partial":
        manifest["status"] = "measured"
    write_manifest(target, manifest)
    print(
        f"lane-inputs: {len(reads)} tracked path(s) read ({dropped_untracked} untracked dropped), "
        f"{len(trace.execs)} subprocess exec(s) followed → {_display(target)}",
        file=sys.stderr,
    )
    return EXIT_OK


def _scratch_inputs(assignments: list[str], command: list[str]) -> dict[str, str]:
    """``--scratch-input NAME=CONTENT`` as ``{NAME: CONTENT}``, each NAME named by the command under SCRATCH_DIR."""
    out: dict[str, str] = {}
    joined = normalise_scratch(shlex.join(command))
    for assignment in assignments:
        name, sep, content = assignment.partition("=")
        if not sep or not name or "/" in name or name in (".", ".."):
            raise LaneInputsError(f"--scratch-input {assignment!r}: expected BASENAME=CONTENT")
        if f"{SCRATCH_DIR.as_posix()}/{name}" not in joined:
            raise LaneInputsError(
                f"--scratch-input {name!r} is not a path the invocation names under {SCRATCH_DIR}; a stand-in the "
                f"command does not read is not an input of it"
            )
        out[name] = content
    return out


# ---------------------------------------------------------------- derive-docker

_COPY_LINE = re.compile(r"^\s*(?:COPY|ADD)\s+(?P<rest>.*)$", re.IGNORECASE)
_LONG_FLAG = re.compile(r"^--[a-z-]+(?:=\S*)?$")


def dockerfile_copy_sources(dockerfile: Path) -> list[str]:
    """The context-relative sources of every ``COPY``/``ADD`` that reads the build context.

    A ``--from=<stage>`` copy reads another stage, not the context, and is
    skipped. Continuation lines are joined first. The last operand is the
    destination and is dropped. JSON-array form (``COPY ["a", "b"]``) is
    handled because the frontend Dockerfile is free to use it.
    """
    text = dockerfile.read_text()
    logical = re.sub(r"\\\r?\n", " ", text)
    sources: list[str] = []
    for line in logical.splitlines():
        match = _COPY_LINE.match(line)
        if not match:
            continue
        rest = match.group("rest").strip()
        if rest.startswith("["):
            try:
                operands = json.loads(rest)
            except json.JSONDecodeError:
                operands = rest.strip("[]").replace('"', "").split(",")
            operands = [str(item).strip() for item in operands]
        else:
            operands = rest.split()
        flags = [item for item in operands if _LONG_FLAG.match(item)]
        if any(flag.startswith("--from") for flag in flags):
            continue
        operands = [item for item in operands if not _LONG_FLAG.match(item)]
        if len(operands) < 2:
            continue
        sources.extend(operands[:-1])
    return sources


def docker_context_files(context: Path, dockerfile: Path) -> set[str]:
    """Ask Docker which files the build context contains, ``.dockerignore`` applied.

    A throwaway ``FROM scratch`` / ``COPY . /ctx`` build exported to a local
    directory (BuildKit's ``local`` exporter — no image is created, nothing is
    pulled). The ignore file is resolved the way the real build resolves it:
    ``<Dockerfile name>.dockerignore`` beside the Dockerfile wins, else the
    context root's ``.dockerignore``. Re-implementing Go's ``filepath.Match``
    plus ``**`` plus re-inclusion here would be a second matcher that could
    disagree with the one production uses.
    """
    docker = shutil.which("docker")
    if docker is None:
        raise LaneInputsError("docker is not on PATH; derive-docker asks the daemon for the context")
    with tempfile.TemporaryDirectory(prefix="lane-inputs-ctx-") as scratch:
        probe_dir = Path(scratch) / "probe"
        probe_dir.mkdir()
        # The probe Dockerfile carries the real Dockerfile's NAME so BuildKit picks
        # up a `<name>.dockerignore` sibling if the real build would.
        probe = probe_dir / dockerfile.name
        probe.write_text("FROM scratch\nCOPY . /ctx/\n")
        sibling_ignore = dockerfile.with_name(dockerfile.name + ".dockerignore")
        if sibling_ignore.is_file():
            shutil.copy(sibling_ignore, probe_dir / sibling_ignore.name)
        out_dir = Path(scratch) / "out"
        completed = subprocess.run(
            [
                docker,
                "build",
                "--quiet",
                "--no-cache",
                "-f",
                str(probe),
                "--output",
                f"type=local,dest={out_dir}",
                str(context),
            ],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "DOCKER_BUILDKIT": "1"},
        )
        if completed.returncode != 0:
            raise LaneInputsError(f"docker build of the context probe failed:\n{completed.stderr.strip()}")
        exported = out_dir / "ctx"
        files: set[str] = set()
        for entry in exported.rglob("*"):
            if entry.is_file() or entry.is_symlink():
                files.add(entry.relative_to(exported).as_posix())
        return files


def _match_copy_source(source: str, context_files: set[str]) -> set[str]:
    """Files of the context a ``COPY`` source operand selects (glob or prefix)."""
    normalised = source.strip("/").lstrip("./") or "."
    if normalised in (".", ""):
        return set(context_files)
    selected = {entry for entry in context_files if entry == normalised or entry.startswith(normalised + "/")}
    if not selected and any(char in normalised for char in "*?["):
        pattern = re.compile(globmodule.translate(normalised, recursive=True))
        selected = {entry for entry in context_files if pattern.match(entry) or pattern.match(entry.split("/", 1)[0])}
        # A glob on a directory name selects the directory's whole content.
        for entry in context_files:
            top = entry
            while "/" in top:
                top = top.rpartition("/")[0]
                if pattern.match(top):
                    selected.add(entry)
                    break
    return selected


def command_derive_docker(args: argparse.Namespace) -> int:
    _path, document = load_workflow(args.workflow)
    context = (REPO_ROOT / args.context).resolve()
    dockerfile = (REPO_ROOT / args.dockerfile).resolve()
    if not context.is_dir():
        raise LaneInputsError(f"--context {args.context!r} is not a directory")
    if not dockerfile.is_file():
        raise LaneInputsError(f"--dockerfile {args.dockerfile!r} is not a file")

    print(f"lane-inputs: deriving the docker build context {args.context!r} for {args.dockerfile!r}", file=sys.stderr)
    context_files = docker_context_files(context, dockerfile)
    sources = dockerfile_copy_sources(dockerfile)
    selected: set[str] = set()
    for source in sources:
        selected |= _match_copy_source(source, context_files)
    context_rel = context.relative_to(REPO_ROOT.resolve()).as_posix()
    prefix = "" if context_rel in (".", "") else context_rel + "/"
    tracked = tracked_files()
    reads = {prefix + entry for entry in selected if prefix + entry in tracked}
    reads.add(dockerfile.relative_to(REPO_ROOT.resolve()).as_posix())
    for ignore in (context / ".dockerignore", dockerfile.with_name(dockerfile.name + ".dockerignore")):
        if ignore.is_file():
            reads.add(ignore.relative_to(REPO_ROOT.resolve()).as_posix())

    target = _target(args)
    if args.append and target.is_file():
        manifest = load_manifest(target)
        manifest["job_spec_sha256"] = job_spec_hash(document, args.job)
    else:
        manifest = _fresh_manifest(args, document)
    invocation = {
        "command": f"derive-docker --context {args.context} --dockerfile {args.dockerfile}",
        "cwd": ".",
        "recorder": (
            "docker build context probe (FROM scratch, COPY . — the daemon applies .dockerignore) "
            "narrowed to the Dockerfile's COPY/ADD sources"
        ),
        "copy_sources": sources,
        "context_files_after_dockerignore": len(context_files),
    }
    _merge_into(manifest, invocation=invocation, reads=reads, execs=[])
    manifest["status"] = (
        "derived" if all(inv["recorder"].startswith("docker build") for inv in manifest["invocations"]) else "measured"
    )
    write_manifest(target, manifest)
    print(
        f"lane-inputs: {len(reads)} tracked path(s) in the narrowed context → {_display(target)}",
        file=sys.stderr,
    )
    return EXIT_OK


# ------------------------------------------------------------------ normalise


def normalise_scratch(text: str) -> str:
    """Map every ``/tmp/...`` path in *text* to ``SCRATCH_DIR/<basename>``.

    Idempotent: a path already under ``SCRATCH_DIR`` maps to itself. Used by
    ``replay`` to rewrite a recorded command before re-running it and by
    ``compare`` on both sides, so a workstation's scratchpad path and the CI
    lane's scratch path are the same token.
    """

    def _rewrite(match: re.Match[str]) -> str:
        name = match.group(0).rstrip("/").rpartition("/")[2]
        return f"{SCRATCH_DIR.as_posix()}/{name}"

    return _SCRATCH_PATH.sub(_rewrite, text)


# --------------------------------------------------------- held run: commands
#
# The guard's rule 5 holds a job's `run:` commands against its manifest; the
# bootstrap below derives a manifest's first invocations from the same
# commands. The two must select the same commands, so the recorder test pins
# `held_commands` against the guard's `job_commands` over every real job — the
# same arrangement as `hash_job_spec` / `job_spec_hash`.

_HELD_HEADS = ("task", "pytest", "python", "python3", "npx")
_ASSIGNMENT_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")


def split_script(script: str) -> list[list[str]]:
    """The simple commands of a ``run:`` script, as the guard's ``_split_script`` tokenises them."""
    joined = re.sub(r"\\\r?\n", " ", script)
    commands: list[list[str]] = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lexer = shlex.shlex(stripped, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError:
            continue
        current: list[str] = []
        for token in tokens:
            if token in (";", "&&", "||", "|", ";;", "&"):
                commands.append(current)
                current = []
            else:
                current.append(token)
        commands.append(current)
    out = []
    for command in commands:
        while command and (command[0] == "sudo" or _ASSIGNMENT_TOKEN.fullmatch(command[0])):
            command = command[1:]
        if command:
            out.append(command)
    return out


def _is_held(tokens: list[str]) -> bool:
    head = tokens[0][2:] if tokens[0].startswith("./") else tokens[0]
    if head in ("python", "python3") and tokens[1:3] == ["-m", "pip"]:
        return False
    return head in _HELD_HEADS or head.startswith("scripts/")


def _step_cwd(document: dict[str, Any], job: dict[str, Any], step: dict[str, Any]) -> str:
    for scope in (
        step,
        (job.get("defaults") or {}).get("run") or {},
        (document.get("defaults") or {}).get("run") or {},
    ):
        if isinstance(scope, dict) and isinstance(scope.get("working-directory"), str):
            return scope["working-directory"]
    return "."


def held_commands(document: dict[str, Any], job_id: str) -> list[tuple[list[str], str, dict[str, str]]]:
    """``(tokens, cwd, env)`` for every held ``run:`` command of *job_id*, env = job env + step env."""
    job = (document.get("jobs") or {}).get(job_id)
    if not isinstance(job, dict):
        raise LaneInputsError(f"job {job_id!r} is not defined in this workflow")
    job_env = job.get("env") if isinstance(job.get("env"), dict) else {}
    out: list[tuple[list[str], str, dict[str, str]]] = []
    for step in job.get("steps") or []:
        if not isinstance(step, dict) or not isinstance(step.get("run"), str):
            continue
        step_env = step.get("env") if isinstance(step.get("env"), dict) else {}
        env = {str(key): str(value) for key, value in {**job_env, **step_env}.items()}
        cwd = _step_cwd(document, job, step)
        for tokens in split_script(step["run"]):
            if _is_held(tokens):
                out.append((tokens, cwd, env))
    return out


_GITHUB_PATH_LINE = re.compile(
    r"""^\s*echo\s+(?P<q>["']?)\$\{?(?P<base>PWD|RUNNER_TEMP)\}?/(?P<rel>[^"'\s]+)(?P=q)\s*>>\s*["']?\$\{?GITHUB_PATH\}?["']?\s*$"""
)


def job_path_additions(document: dict[str, Any], job_id: str) -> list[str]:
    """Repo-relative directories *job_id*'s ``run:`` steps append to ``$GITHUB_PATH``, in step order.

    Only the spelling the workflows use — ``echo "$PWD/<dir>" >> "$GITHUB_PATH"``
    — resolved against the step's working directory. ``$RUNNER_TEMP/<dir>`` is a
    tool the job installed outside the checkout (hadolint copied out of its
    image); the replay does not reproduce it, the lane provides that tool itself
    and ``replay`` refuses an invocation whose program is missing. A
    ``$GITHUB_PATH`` write in any other spelling is refused rather than silently
    not reproduced: a replay that resolves ``python`` differently from the job
    records another job.
    """
    job = (document.get("jobs") or {}).get(job_id)
    if not isinstance(job, dict):
        raise LaneInputsError(f"job {job_id!r} is not defined in this workflow")
    out: list[str] = []
    for step in job.get("steps") or []:
        if not isinstance(step, dict) or not isinstance(step.get("run"), str):
            continue
        cwd = _step_cwd(document, job, step)
        for line in step["run"].splitlines():
            if "GITHUB_PATH" not in line:
                continue
            match = _GITHUB_PATH_LINE.match(line)
            if match is None:
                raise LaneInputsError(
                    f"job {job_id!r} writes $GITHUB_PATH as {line.strip()!r}; the replay reproduces only "
                    f'`echo "$PWD/<dir>" >> "$GITHUB_PATH"` — spell it that way or teach job_path_additions'
                )
            if match["base"] != "PWD":
                continue
            directory = (Path(cwd) / match["rel"]).as_posix()
            if directory not in out:
                out.append(directory)
    return out


def _has_paths_filter(job: Any) -> bool:
    return isinstance(job, dict) and any(
        isinstance(step, dict) and "paths-filter@" in str(step.get("uses", "")) for step in job.get("steps") or []
    )


def _on_filtered(document: dict[str, Any]) -> bool:
    block = document.get("on", document.get(True))
    if not isinstance(block, dict):
        return False
    return any(
        isinstance(spec, dict) and (spec.get("paths") or spec.get("paths-ignore"))
        for event, spec in block.items()
        if event in ("push", "pull_request", "pull_request_target")
    )


def bootstrap_invocations(workflow: str, job: str) -> list[dict[str, Any]]:
    """The first invocations of a manifest that does not exist yet: the job's own held commands.

    Only for a job with no relevance filter — the only kind a ``covered_by``
    may name, and the only kind whose manifest cannot be seeded by the lane's
    own filter. A command carrying an expression or an env value carrying one
    cannot be replayed outside the runner that resolves it and is refused
    rather than guessed at.
    """
    _path, document = load_workflow(workflow)
    jobs = document.get("jobs") or {}
    if job not in jobs:
        raise LaneInputsError(f"{workflow} defines no job {job!r}")
    if _on_filtered(document) or _has_paths_filter(jobs[job]):
        raise LaneInputsError(
            f"{workflow}/{job} decides its relevance with a filter; bootstrap records unfiltered "
            f"delegation targets only — record a filtered job with `record` and commit its manifest"
        )
    invocations: list[dict[str, Any]] = []
    for tokens, cwd, env in held_commands(document, job):
        unresolved = [token for token in tokens if "${{" in token or "$" in token] + [
            f"{key}={value}" for key, value in env.items() if "${{" in value
        ]
        if unresolved:
            raise LaneInputsError(
                f"{workflow}/{job} runs {shlex.join(tokens)!r} with run-time values {unresolved}; "
                f"a bootstrap cannot resolve them"
            )
        invocations.append(
            {"command": shlex.join(tokens), "cwd": cwd, "env": sorted(f"{k}={v}" for k, v in env.items())}
        )
    if not invocations:
        raise LaneInputsError(f"{workflow}/{job} runs no held command (task/pytest/python/npx/scripts)")
    return invocations


# --------------------------------------------------------------------- replay


#: The manifest guard, as a pytest node id relative to src/backend (pytest's rootdir).
#: A replay runs every invocation with ``--deselect`` of it in ``PYTEST_ADDOPTS``.
#: The guard holds the COMMITTED manifests against the live tree — exactly the
#: manifests a replay produces successors for. Run inside the replay of the
#: unit-suite legs (backend--lint-test: ``pytest tests/unit/``, and until #1741
#: backend--coverage; backend-guards--guards already leaves it out with
#: ``-m 'not advisory'``),
#: it failed whenever a change had staled one of them (as any change to a
#: recorded job does), those legs recorded nothing, and every such change cost
#: two recordings (#1683, 2026-09-24). The real CI lanes still run it; only the
#: replay leaves it out. What that costs: the reads the guard ALONE makes are not
#: in that manifest (most of them — the workflows, the manifests — are
#: read by the recorder's own tests in the same suite, which stay in).
REPLAY_DESELECTED_GUARD = "tests/unit/guards/test_lane_filters_cover_measured_inputs.py"


def _replay_pytest_addopts(existing: str) -> str:
    return " ".join(part for part in (existing.strip(), f"--deselect {REPLAY_DESELECTED_GUARD}") if part)


def _is_derived(invocation: dict[str, Any]) -> bool:
    return str(invocation.get("recorder", "")).startswith("docker build")


def _replay_base(committed: dict[str, Any]) -> dict[str, Any]:
    """The committed manifest minus everything a recording produces; hand-written fields survive."""
    base = dict(committed)
    base["invocations"] = []
    base["subprocesses"] = []
    base["reads"] = []
    base["test_modules"] = []
    base["readers"] = {}
    base["status"] = "measured"
    # Written under the recorder's contract, not the committed file's.
    base["schema"] = SCHEMA
    base.pop("partial_reason", None)
    base.pop("replay_seconds", None)
    return base


def _bootstrap_base(workflow: str, job: str) -> dict[str, Any]:
    _path, document = load_workflow(workflow)
    return {
        "schema": SCHEMA,
        "workflow": workflow,
        "job": job,
        "gate": {"kind": "unfiltered"},
        "status": "measured",
        "measured_on": dt.datetime.now(dt.UTC).date().isoformat(),
        "measured_at_commit": head_commit(),
        "job_spec_sha256": job_spec_hash(document, job),
        "invocations": [],
        "subprocesses": [],
        "accepted_gaps": [],
        "reads": [],
        "test_modules": [],
        "readers": {},
    }


def _program_available(program: str, cwd: Path) -> bool:
    if "/" in program:
        return (cwd / program).is_file()
    return shutil.which(program) is not None


def replay_argv(invocation: dict[str, Any], *, workflow: str, job: str, out_dir: Path) -> list[str]:
    """The ``lane_inputs.py`` argv that re-records *invocation* into *out_dir*."""
    common = ["--workflow", workflow, "--job", job, "--append", "--manifest-dir", str(out_dir)]
    command = normalise_scratch(str(invocation.get("command", "")))
    try:
        faithful = shlex.join(shlex.split(command)) == command
    except ValueError:
        faithful = False
    if not faithful and not _is_derived(invocation):
        # A command written before the recorder used `shlex.join` (a plain
        # " ".join) lost its quoting: `bash -c find … | wc -l` splits into
        # `bash -c find` plus stray words, and replaying it runs a DIFFERENT
        # command — measured: a bare `find` over the whole checkout, 462 reads
        # instead of 9. Refused rather than replayed.
        raise LaneInputsError(
            f"{command!r} does not survive shlex.split/shlex.join unchanged, so its quoting was lost when it was "
            f"written; re-spell it as the recorder writes it (shlex.join of the argv) before it can be replayed"
        )
    if _is_derived(invocation):
        tokens = shlex.split(command)
        options = dict(zip(tokens[1::2], tokens[2::2], strict=False))
        if tokens[:1] != ["derive-docker"] or "--context" not in options or "--dockerfile" not in options:
            raise LaneInputsError(f"cannot replay the derived invocation {command!r}")
        return ["derive-docker", *common, "--context", options["--context"], "--dockerfile", options["--dockerfile"]]
    argv = ["record", *common, "--cwd", str(invocation.get("cwd") or ".")]
    for assignment in invocation.get("env") or []:
        argv += ["--env", normalise_scratch(str(assignment))]
    scratch = invocation.get("scratch_inputs") or {}
    if not isinstance(scratch, dict):
        raise LaneInputsError(f"{command!r}: scratch_inputs must be a mapping of basename to content")
    for name, content in sorted(scratch.items()):
        argv += ["--scratch-input", f"{name}={content}"]
    reason = invocation.get("allow_failure_reason")
    if isinstance(reason, str) and reason.strip():
        argv += ["--allow-failure", reason.strip()]
    return [*argv, "--", *shlex.split(command)]


def command_replay(args: argparse.Namespace) -> int:
    lane = args.lane
    if lane.endswith((".yaml", ".yml")):
        source = Path(lane) if Path(lane).is_absolute() else REPO_ROOT / lane
        committed = load_manifest(source)
        workflow, job = str(committed.get("workflow", "")), str(committed.get("job", ""))
        invocations = [entry for entry in committed.get("invocations") or [] if isinstance(entry, dict)]
        if not invocations:
            raise LaneInputsError(
                f"{source.name} has no invocation to replay"
                + (
                    f" (empty_reads_reason: {committed['empty_reads_reason']})"
                    if committed.get("empty_reads_reason")
                    else ""
                )
            )
        base = _replay_base(committed)
        name = source.name
    else:
        workflow, _, job = lane.partition("/")
        invocations = bootstrap_invocations(workflow, job)
        base = _bootstrap_base(workflow, job)
        name = f"{manifest_stem(workflow, job)}.yaml"

    out_dir = Path(args.out_dir).resolve()
    argvs = [replay_argv(entry, workflow=workflow, job=job, out_dir=out_dir) for entry in invocations]
    _path, document = load_workflow(workflow)
    path_additions = job_path_additions(document, job)
    for directory in path_additions:
        print(f"lane-inputs: replay → PATH += {directory} (the job's own $GITHUB_PATH write)", file=sys.stderr)
    for argv in argvs:
        print(f"lane-inputs: replay → python3 scripts/ci/lane_inputs.py {shlex.join(argv)}", file=sys.stderr)
    if args.dry_run:
        return EXIT_OK

    saved_path = os.environ.get("PATH", "")
    saved_addopts = os.environ.get("PYTEST_ADDOPTS")
    os.environ["PYTEST_ADDOPTS"] = _replay_pytest_addopts(saved_addopts or "")
    if path_additions:
        # Prepended for every invocation, not from its step on: before the
        # install step runs, the directory does not exist and PATH lookup skips it.
        os.environ["PATH"] = os.pathsep.join([*(str(REPO_ROOT / d) for d in path_additions), saved_path])
    try:
        for argv, entry in zip(argvs, invocations, strict=True):
            if argv[0] != "record":
                continue
            program = argv[argv.index("--") + 1]
            cwd = REPO_ROOT / str(entry.get("cwd") or ".")
            if not _program_available(program, cwd):
                raise LaneInputsError(
                    f"{name}: {program!r} is not available in this environment, so {entry.get('command')!r} cannot be "
                    f"replayed. Provide it in .github/workflows/lane-inputs.yml (see `plan`'s environment flags) — the "
                    f"manifest is not recorded rather than recorded without this invocation"
                )
        out_dir.mkdir(parents=True, exist_ok=True)
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        target = out_dir / name
        write_manifest(target, base)
        started = time.monotonic()
        for index, argv in enumerate(argvs):
            code = main(argv)
            if code != EXIT_OK:
                target.unlink(missing_ok=True)
                raise LaneInputsError(
                    f"{name}: invocations[{index}] could not be recorded (exit {code}); no manifest was written, so "
                    f"`compare` reports this lane as unrecorded instead of certifying a shorter read set"
                )
        # Rounded up: the bound `plan` derives from it must not come out tighter than what was measured.
        seconds = max(1, math.ceil(time.monotonic() - started))
        write_manifest(target, with_replay_seconds(load_manifest(target), seconds))
    finally:
        os.environ["PATH"] = saved_path
        if saved_addopts is None:
            os.environ.pop("PYTEST_ADDOPTS", None)
        else:
            os.environ["PYTEST_ADDOPTS"] = saved_addopts
    print(
        f"lane-inputs: replayed {len(argvs)} invocation(s) in {seconds} s → {_display(target)}",
        file=sys.stderr,
    )
    return EXIT_OK


# ----------------------------------------------------------------------- plan

#: Environment the recorder lane provides only where a leg needs it; everything
#: else (Python, uv, Task, Node, strace, Docker, yq) is in every leg. Decided per
#: manifest from its own invocations, so the workflow carries no list of lanes.
_ENV_FLAGS = ("backend", "frontend", "helm", "skaffold", "nuclei", "hadolint", "arangodb")


def environment_flags(invocations: list[dict[str, Any]]) -> dict[str, bool]:
    flags = dict.fromkeys(_ENV_FLAGS, False)
    for invocation in invocations:
        if _is_derived(invocation):
            continue
        cwd = str(invocation.get("cwd") or ".")
        command = str(invocation.get("command", ""))
        try:
            head = shlex.split(command)[0]
        except (ValueError, IndexError):
            head = ""
        flags["backend"] |= cwd == "src/backend" or cwd.startswith("src/backend/")
        flags["frontend"] |= cwd == "src/frontend" or cwd.startswith("src/frontend/")
        flags["skaffold"] |= "skaffold" in command
        flags["helm"] |= head == "helm" or "skaffold" in command
        flags["nuclei"] |= head == "nuclei"
        flags["hadolint"] |= head == "hadolint"
        flags["arangodb"] |= any(str(entry).startswith("ARANGODB_HOST=") for entry in invocation.get("env") or [])
    return flags


def plan_matrix(manifest_dir: Path | None = None) -> list[dict[str, Any]]:
    """One matrix leg per manifest with invocations, plus one per unrecorded ``covered_by`` target.

    Each leg carries ``timeout_minutes`` (:func:`leg_timeout_minutes`) for the
    record job's replay step.
    """
    directory = manifest_dir or MANIFEST_DIR
    manifests = {path.name: load_manifest(path) for path in sorted(directory.glob("*.yaml"))}
    legs: list[dict[str, Any]] = []
    for name, manifest in manifests.items():
        invocations = [entry for entry in manifest.get("invocations") or [] if isinstance(entry, dict)]
        if not invocations:
            continue
        lane = f"{_display(directory / name)}"
        legs.append(
            {
                "name": name.removesuffix(".yaml"),
                "lane": lane,
                "timeout_minutes": leg_timeout_minutes(manifest),
                **environment_flags(invocations),
            }
        )
    recorded = {(str(m.get("workflow")), str(m.get("job"))) for m in manifests.values()}
    targets = sorted(
        {
            str(gap["covered_by"])
            for manifest in manifests.values()
            for gap in manifest.get("accepted_gaps") or []
            if isinstance(gap, dict) and gap.get("covered_by")
        }
    )
    for target in targets:
        workflow, _, job = target.partition("/")
        if (workflow, job) in recorded:
            continue
        legs.append(
            {
                "name": manifest_stem(workflow, job),
                "lane": target,
                "timeout_minutes": leg_timeout_minutes(None),
                **environment_flags(bootstrap_invocations(workflow, job)),
            }
        )
    return legs


def command_plan(args: argparse.Namespace) -> int:
    legs = plan_matrix()
    matrix = json.dumps({"include": legs}, separators=(",", ":"))
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"matrix={matrix}\n")
    print(json.dumps({"include": legs}, indent=2))
    print(f"lane-inputs: {len(legs)} lane(s) to record", file=sys.stderr)
    return EXIT_OK


# -------------------------------------------------------------------- compare


def _comparable_invocation(invocation: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "command": normalise_scratch(str(invocation.get("command", ""))),
        "cwd": str(invocation.get("cwd") or "."),
    }
    if _is_derived(invocation):
        out["copy_sources"] = list(invocation.get("copy_sources") or [])
    else:
        out["env"] = sorted(normalise_scratch(str(entry)) for entry in invocation.get("env") or [])
        out["exit_code"] = invocation.get("exit_code")
        out["scratch_inputs"] = dict(sorted((invocation.get("scratch_inputs") or {}).items()))
    return out


# The relevance-filter matcher `compare` needs to tell a read the filter selects
# from one it does not (#1683: only the latter is drift). It is the guard's
# matcher (`glob_to_regex`, `Trigger.fires_for`, `StepFilter.selects`,
# `probe_path`, `_gap_matches` in test_lane_filters_cover_measured_inputs.py),
# kept here because this script runs where pytest does not; the recorder test
# holds the two to the same verdict over every read of every committed manifest,
# the arrangement `hash_job_spec` / `job_spec_hash` already has.

_DIFF_TRIGGERS = ("push", "pull_request", "pull_request_target")
_PROBE = "__lane_inputs_probe__"


@functools.cache
def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """A GitHub / picomatch path pattern as an anchored regex (the guard's ``glob_to_regex``)."""
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
    """A file is itself; a listing ``dir/`` is a file added inside it; ``./`` a file at the root."""
    if read == "./":
        return _PROBE
    if read.endswith("/"):
        return read + _PROBE
    return read


def _trigger_fires(paths: list[str], paths_ignore: list[str], path: str) -> bool:
    if paths:
        selected = paths[0].startswith("!")
        for pattern in paths:
            negated = pattern.startswith("!")
            if _matches(pattern[1:] if negated else pattern, path):
                selected = not negated
        return selected
    if paths_ignore:
        return not any(_matches(pattern, path) for pattern in paths_ignore)
    return True


def _step_filter_selects(patterns: list[str], quantifier: str, path: str) -> bool:
    verdicts = []
    for pattern in patterns:
        negated = pattern.startswith("!")
        hit = _matches(pattern[1:] if negated else pattern, path)
        verdicts.append((not hit) if negated else hit)
    if not verdicts:
        return False
    return all(verdicts) if quantifier == "every" else any(verdicts)


def _string_list(value: Any) -> list[str]:
    return [entry for entry in value if isinstance(entry, str)] if isinstance(value, list) else []


def _step_filter_patterns(raw: Any) -> dict[str, list[str]]:
    document = yaml.safe_load(raw) if isinstance(raw, str) else raw
    if not isinstance(document, dict):
        return {}
    out: dict[str, list[str]] = {}
    for name, value in document.items():
        patterns = []
        for entry in value if isinstance(value, list) else [value]:
            if isinstance(entry, dict):
                entry = entry.get("path")
            if isinstance(entry, str):
                patterns.append(entry)
        out[str(name)] = patterns
    return out


@dataclass
class RelevanceFilter:
    """What decides whether a pull request runs one job: its workflow's ``on:`` paths and its paths-filter names."""

    triggers: list[tuple[list[str], list[str]]] = field(default_factory=list)
    step_filters: list[tuple[list[str], str]] = field(default_factory=list)

    def rejects(self, read: str) -> list[str]:
        """Which part of the filter does NOT select *read* (empty: the filter selects it)."""
        probe = probe_path(read)
        failed = []
        if any(paths or ignore for paths, ignore in self.triggers) and not any(
            _trigger_fires(paths, ignore, probe) for paths, ignore in self.triggers
        ):
            failed.append("the on:-level paths filter")
        if self.step_filters and not any(_step_filter_selects(p, q, probe) for p, q in self.step_filters):
            failed.append("the paths-filter")
        return failed


def relevance_filter(document: dict[str, Any], manifest: dict[str, Any]) -> RelevanceFilter:
    """The live filter of *manifest*'s job: its workflow's diff triggers plus the filters ``gate.filter`` names."""
    block = document.get("on", document.get(True))
    if isinstance(block, str):
        block = {block: None}
    elif isinstance(block, list):
        block = dict.fromkeys(block)
    triggers = []
    for event, spec in (block or {}).items() if isinstance(block, dict) else []:
        if event in _DIFF_TRIGGERS:
            spec = spec if isinstance(spec, dict) else {}
            triggers.append((_string_list(spec.get("paths")), _string_list(spec.get("paths-ignore"))))
    gate = manifest.get("gate") if isinstance(manifest.get("gate"), dict) else {}
    raw_names = gate.get("filter")
    names = [raw_names] if isinstance(raw_names, str) else [str(n) for n in raw_names or []]
    step_filters = []
    if names:
        for job in (document.get("jobs") or {}).values():
            for step in (job.get("steps") or []) if isinstance(job, dict) else []:
                if not isinstance(step, dict) or "paths-filter@" not in str(step.get("uses", "")):
                    continue
                inputs = step.get("with") if isinstance(step.get("with"), dict) else {}
                quantifier = str(inputs.get("predicate-quantifier", "some"))
                for name, patterns in _step_filter_patterns(inputs.get("filters")).items():
                    if name in names:
                        step_filters.append((patterns, quantifier))
    return RelevanceFilter(triggers, step_filters)


def gap_matches(gap: dict[str, Any], read: str) -> bool:
    """An ``accepted_gaps`` entry that explains *read* (the guard's ``_gap_matches``)."""
    pattern = gap.get("pattern")
    return isinstance(pattern, str) and (
        pattern == read or _matches(pattern, probe_path(read)) or _matches(pattern, read)
    )


def _sample(paths: list[str], limit: int = 10) -> str:
    return ", ".join(paths[:limit]) + (f", … (+{len(paths) - limit})" if len(paths) > limit else "")


def manifest_differences(name: str, committed: dict[str, Any], recorded: dict[str, Any]) -> list[str]:
    """What the committed manifest claims that the CI recording of the same lane does not agree with."""
    findings: list[str] = []
    # `replay_seconds` is not compared — wall clock varies run to run — but a
    # manifest that was replayed must carry one: the committed side, or its leg
    # is bounded at the job-level cap without anything saying so; the recorded
    # side, or the recorder stopped measuring itself.
    problem = replay_seconds_problem(committed)
    if problem == "has no `replay_seconds`":
        findings.append(
            f"{name}: the committed manifest {problem}, so `plan` gives its leg the job-level "
            f"{TIMEOUT_CAP_MINUTES}-minute bound — commit the CI recording"
        )
    elif problem is not None:
        findings.append(f"{name}: the committed manifest's {problem} — commit the CI recording")
    problem = replay_seconds_problem(recorded)
    if problem is not None:
        findings.append(f"{name}: the CI recording {problem} — the replay did not measure itself")
    if committed.get("job_spec_sha256") != recorded.get("job_spec_sha256"):
        findings.append(
            f"{name}: job_spec_sha256 {str(committed.get('job_spec_sha256'))[:12]} is not the live job's "
            f"{str(recorded.get('job_spec_sha256'))[:12]} — the committed read set describes another job definition"
        )
    if committed.get("status") != recorded.get("status"):
        findings.append(f"{name}: status {committed.get('status')!r} committed, {recorded.get('status')!r} recorded")
    ours = [_comparable_invocation(e) for e in committed.get("invocations") or [] if isinstance(e, dict)]
    theirs = [_comparable_invocation(e) for e in recorded.get("invocations") or [] if isinstance(e, dict)]
    if ours != theirs:
        for index in range(max(len(ours), len(theirs))):
            left = ours[index] if index < len(ours) else None
            right = theirs[index] if index < len(theirs) else None
            if left != right:
                findings.append(f"{name}: invocations[{index}] committed {left} ≠ recorded {right}")
                break
    if not recorded.get("reads") and any(isinstance(e, dict) for e in recorded.get("invocations") or []):
        findings.append(f"{name}: the CI recording read nothing at all — the instrument measured nothing")
    return findings


def read_drift(
    name: str,
    committed: dict[str, Any],
    recorded: dict[str, Any],
    *,
    reads_of: dict[tuple[str, str], set[str]],
    workflow_dir: Path = WORKFLOW_DIR,
) -> tuple[list[str], list[str]]:
    """``(findings, notes)`` over the READS of one lane: only a read its relevance filter does not select is drift.

    #1683: a new read INSIDE the filter changes no verdict the guard reaches —
    the filter already runs the job for a change to that path — so it is not a
    finding, and a pull request that adds a file under ``src/backend/`` no
    longer stales ``backend--lint-test``. A new read OUTSIDE the filter is: the
    job now depends on a path whose change would not run it. Unless the
    committed manifest's ``accepted_gaps`` already accepts it — then the guard's
    coverage rule reaches the same verdict with the read added — and, when that
    gap names a ``covered_by`` lane, that lane's recording reads it too.
    Reads the committed manifest lists and the run did not make are a note:
    a larger committed set only asks more of the filter.
    """
    findings: list[str] = []
    committed_reads = {str(entry) for entry in committed.get("reads") or []}
    recorded_reads = {str(entry) for entry in recorded.get("reads") or []}
    new = sorted(recorded_reads - committed_reads)
    gone = sorted(committed_reads - recorded_reads)
    notes = [f"{name}: {len(gone)} committed read(s) not made in this run (not drift)"] if gone else []
    if not new:
        return findings, notes
    workflow = workflow_dir / str(committed.get("workflow"))
    if not workflow.is_file():
        return [f"{name}: names workflow {committed.get('workflow')!r}, which does not exist"], notes
    live = relevance_filter(yaml.safe_load(workflow.read_text()) or {}, committed)
    gaps = [gap for gap in committed.get("accepted_gaps") or [] if isinstance(gap, dict)]
    outside: list[str] = []
    undelegated: list[str] = []
    inside = 0
    for read in new:
        failed = live.rejects(read)
        if not failed:
            inside += 1
            continue
        matching = [g for g in gaps if gap_matches(g, read)]
        if not matching:
            outside.append(f"{read} ({' and '.join(failed)})")
            continue
        # Every matching gap, not the first (#1683 review of #1747): the guard's
        # coverage rule holds each gap's delegation, so two overlapping gaps
        # naming different lanes owe the read to BOTH.
        for gap in matching:
            covered_by = gap.get("covered_by")
            if covered_by is None:
                continue
            target_workflow, _, target_job = str(covered_by).partition("/")
            if read not in reads_of.get((target_workflow, target_job), set()):
                undelegated.append(f"{read} (covered_by {covered_by})")
    if outside:
        findings.append(
            f"{name}: the CI run read {len(outside)} path(s) the job's relevance filter does not select and no "
            f"accepted gap explains — a change there would not run the job: {_sample(outside)}"
        )
    if undelegated:
        findings.append(
            f"{name}: {len(undelegated)} new read(s) fall under an accepted gap whose covered_by lane did not read "
            f"them in this run: {_sample(undelegated)}"
        )
    if inside:
        notes.append(f"{name}: {inside} new read(s) inside the relevance filter (not drift)")
    return findings, notes


def delegated_reads(
    committed: dict[str, dict[str, Any]], *, workflow_dir: Path = WORKFLOW_DIR
) -> dict[tuple[str, str], dict[str, str]]:
    """``(workflow, job) -> {read: delegating manifest}``: what each ``covered_by`` lane must read.

    The guard's ``_delegation_findings`` semantics: a delegating manifest's
    committed reads that its filter does not select and that a gap with
    ``covered_by`` explains are owed by the covering lane.
    """
    owed: dict[tuple[str, str], dict[str, str]] = {}
    for name, manifest in committed.items():
        gaps = [g for g in manifest.get("accepted_gaps") or [] if isinstance(g, dict) and g.get("covered_by")]
        workflow = workflow_dir / str(manifest.get("workflow"))
        if not gaps or not workflow.is_file():
            continue
        live = relevance_filter(yaml.safe_load(workflow.read_text()) or {}, manifest)
        for read in (str(entry) for entry in manifest.get("reads") or []):
            if not live.rejects(read):
                continue
            for gap in gaps:  # every matching gap: each one's lane owes the read
                if gap_matches(gap, read):
                    target_workflow, _, target_job = str(gap["covered_by"]).partition("/")
                    owed.setdefault((target_workflow, target_job), {}).setdefault(read, name)
    return owed


def stray_readers(
    name: str,
    committed: dict[str, Any],
    recorded: dict[str, Any],
    *,
    modules_of: dict[tuple[str, str], set[str]],
    workflow_dir: Path = WORKFLOW_DIR,
) -> list[str]:
    """Test modules of this run that make a delegated read while the covering lane does not run them (#1749).

    A ``covered_by`` gap says "a change to this path is judged in that lane".
    That holds for a read only if the TEST that makes it runs there: another
    test of the covering lane reading the same path judges its own assertions,
    not the new one's. ``modules_of`` is each lane's ``test_modules`` as this
    run recorded them (the committed ones where it recorded none).
    """
    gaps = [g for g in committed.get("accepted_gaps") or [] if isinstance(g, dict) and g.get("covered_by")]
    readers = recorded.get("readers") or {}
    workflow = workflow_dir / str(committed.get("workflow"))
    if not gaps or not readers or not workflow.is_file():
        return []
    live = relevance_filter(yaml.safe_load(workflow.read_text()) or {}, committed)
    stray: dict[str, list[str]] = {}
    for module, paths in sorted(readers.items()):
        for read in (str(entry) for entry in paths or []):
            if not live.rejects(read):
                continue
            for gap in gaps:
                target_workflow, _, target_job = str(gap["covered_by"]).partition("/")
                if gap_matches(gap, read) and module not in modules_of.get((target_workflow, target_job), set()):
                    stray.setdefault(module, []).append(f"{read} (covered_by {gap['covered_by']})")
    return [
        f"{name}: test module {module} makes {len(owed)} delegated read(s) but the covering lane does not run it, "
        f"so a change there is judged by no required test of that module — add the module to that lane's "
        f"invocation, or select the path in this job's filter: {_sample(owed, 5)}"
        for module, owed in stray.items()
    ]


def compare_manifests(
    committed_dir: Path, recorded_dir: Path, *, workflow_dir: Path = WORKFLOW_DIR
) -> tuple[list[str], list[str]]:
    """``(findings, notes)`` of the committed manifests against a CI recording of them.

    Compared: ``reads`` — as drift only where the job's live relevance filter
    does not select a new read (:func:`read_drift`, #1683) — ``job_spec_sha256``
    (which no longer moves with an action's pin), ``status``, the
    ``invocations`` (command, cwd, env, exit code — scratch paths normalised),
    and whether the recording read anything at all.
    Not compared: when and where the recording ran (``measured_on``,
    ``measured_at_commit``, ``subprocesses``, ``untracked_reads_dropped``), how
    long it took (``replay_seconds`` — wall clock varies run to run; it sizes the
    next run's step bound and is committed with the recording, and only its
    presence and range are held, on both sides) and
    the hand-written fields a replay carries over verbatim. A manifest with
    invocations that the recording lacks is a finding — its record leg failed
    or never ran, and silence there would read as agreement. A recorded manifest
    with no committed counterpart (a bootstrapped delegation target) is a
    finding too: it exists to be committed.
    """
    committed = {path.name: load_manifest(path) for path in sorted(committed_dir.glob("*.yaml"))}
    recorded = (
        {path.name: load_manifest(path) for path in sorted(recorded_dir.glob("*.yaml"))}
        if recorded_dir.is_dir()
        else {}
    )
    findings: list[str] = []
    notes: list[str] = []
    # A covered_by lane's reads as this run recorded them, the committed ones where it recorded none.
    reads_of: dict[tuple[str, str], set[str]] = {}
    modules_of: dict[tuple[str, str], set[str]] = {}
    for source in (committed, recorded):
        for manifest in source.values():
            key = (str(manifest.get("workflow")), str(manifest.get("job")))
            reads_of[key] = {str(entry) for entry in manifest.get("reads") or []}
            modules_of[key] = {str(entry) for entry in manifest.get("test_modules") or []}
    delegated = delegated_reads(committed, workflow_dir=workflow_dir)
    for name, manifest in committed.items():
        if not any(isinstance(entry, dict) for entry in manifest.get("invocations") or []):
            notes.append(f"{name}: no invocation to replay — {manifest.get('empty_reads_reason') or 'no reason given'}")
            continue
        counterpart = recorded.get(name)
        if counterpart is None:
            findings.append(
                f"{name}: the CI lane recorded no manifest for it — its record leg failed or did not run, so the "
                f"committed read set is unverified; see that leg's log"
            )
            continue
        findings += manifest_differences(name, manifest, counterpart)
        read_findings, read_notes = read_drift(
            name, manifest, counterpart, reads_of=reads_of, workflow_dir=workflow_dir
        )
        findings += read_findings
        notes += read_notes
        findings += stray_readers(name, manifest, counterpart, modules_of=modules_of, workflow_dir=workflow_dir)
        # Review of #1747: a covering lane that stops reading a path another lane
        # delegates to it would keep the stale committed read, and the guard's
        # delegation rule (which reads committed manifests) would stay green.
        owed = delegated.get((str(manifest.get("workflow")), str(manifest.get("job"))), {})
        recorded_reads = {str(entry) for entry in counterpart.get("reads") or []}
        dropped = sorted(read for read in owed if read not in recorded_reads)
        if dropped:
            findings.append(
                f"{name}: the CI run no longer reads {len(dropped)} path(s) other lanes delegate to it through "
                f"covered_by: {_sample([f'{read} ({owed[read]})' for read in dropped])}"
            )
    for name in sorted(set(recorded) - set(committed)):
        findings.append(f"{name}: recorded in CI and not committed — commit it (a delegation target's first manifest)")
    return findings, notes


def command_compare(args: argparse.Namespace) -> int:
    recorded_dir = Path(args.recorded_dir)
    committed_dir = Path(args.committed_dir) if args.committed_dir else MANIFEST_DIR
    findings, notes = compare_manifests(committed_dir, recorded_dir)
    run = args.run_id or "<run-id>"
    lines = [f"lane-inputs compare: {len(findings)} finding(s), {len(notes)} note(s)"]
    lines += [f"  FINDING {finding}" for finding in findings]
    lines += [f"  note    {note}" for note in notes]
    if findings:
        lines += [
            "",
            "The committed manifests disagree with what this run recorded. Do not edit `reads` by hand; commit",
            "the CI recording instead:",
            f"  gh run download {run} -n lane-inputs -D /tmp/lane-inputs-{run}",
            f"  cp /tmp/lane-inputs-{run}/*.yaml .github/lane-inputs/",
            "then re-run the guard (tests/unit/guards/test_lane_filters_cover_measured_inputs.py) against the result.",
        ]
    text = "\n".join(lines)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("```\n" + text + "\n```\n")
    return EXIT_FINDINGS if findings else EXIT_OK


# -------------------------------------------------------------------------- show


def command_show(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    reads = manifest.get("reads") or []
    top: dict[str, int] = {}
    for entry in reads:
        head = entry.split("/", 1)[0] if "/" in entry.rstrip("/") else entry
        top[head] = top.get(head, 0) + 1
    print(
        f"{manifest.get('workflow')} / {manifest.get('job')}  ({manifest.get('status')}, {manifest.get('measured_on')})"
    )
    print(f"  {len(reads)} read path(s), by top-level entry:")
    for head, count in sorted(top.items(), key=lambda item: (-item[1], item[0])):
        print(f"    {count:5d}  {head}")
    print(f"  {len(manifest.get('subprocesses') or [])} distinct program(s) followed as subprocesses")
    return EXIT_OK


# -------------------------------------------------------------------------- main


def _reason(text: str) -> str:
    if len(text.strip()) < MIN_REASON_CHARS:
        raise argparse.ArgumentTypeError(f"a reason has at least {MIN_REASON_CHARS} characters; {text!r} is a label")
    return text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    sub = parser.add_subparsers(dest="command_name", required=True)

    def lane_arguments(p: argparse.ArgumentParser) -> None:
        p.add_argument("--workflow", required=True, help="file name under .github/workflows/")
        p.add_argument("--job", required=True, help="job id inside that workflow")
        p.add_argument(
            "--filter",
            default=None,
            help="paths-filter filter name that gates this job (omit for an on:-level paths filter)",
        )
        p.add_argument("--append", action="store_true", help="merge into the existing manifest instead of replacing it")
        p.add_argument(
            "--unfiltered",
            action="store_true",
            help="the job has no relevance filter (gate.kind unfiltered): recorded because a covered_by names it",
        )
        p.add_argument(
            "--manifest-dir",
            default=None,
            help="write the manifest here instead of .github/lane-inputs/ (the CI replay's output directory)",
        )

    record = sub.add_parser("record", help="run an invocation under strace and record its tracked reads")
    lane_arguments(record)
    record.add_argument("--cwd", default=None, help="directory the invocation runs in, repo-relative")
    record.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    record.add_argument(
        "--scratch-input",
        action="append",
        default=[],
        metavar="BASENAME=CONTENT",
        help=(
            f"write CONTENT to {SCRATCH_DIR}/BASENAME before tracing: a stand-in for a file an earlier step of the "
            "job produces and the recorder cannot (a scan report); kept in the manifest as `scratch_inputs`"
        ),
    )
    record.add_argument(
        "--allow-failure",
        default=None,
        metavar="REASON",
        type=_reason,
        help=(
            "accept a non-zero exit as the invocation's verdict; REASON (at least "
            f"{MIN_REASON_CHARS} characters) says which reads the failure path may have skipped"
        ),
    )
    record.add_argument(
        "--partial",
        default=None,
        metavar="REASON",
        type=_reason,
        help=(
            "mark the manifest `status: partial`: the invocation is knowingly a subset of the job's; "
            f"REASON (at least {MIN_REASON_CHARS} characters) says which subset, and the guard holds it "
            "against the filter"
        ),
    )
    record.add_argument(
        "--empty-reads-reason",
        default=None,
        help=(
            "instead of an invocation: why this job reads nothing from the tree "
            "(e.g. it only runs checkout + paths-filter)"
        ),
    )
    record.add_argument("command", nargs=argparse.REMAINDER, help="the invocation, after `--`")
    record.set_defaults(func=command_record)

    derive = sub.add_parser("derive-docker", help="derive a docker build's reads from its context and Dockerfile")
    lane_arguments(derive)
    derive.add_argument("--context", required=True)
    derive.add_argument("--dockerfile", required=True)
    derive.set_defaults(func=command_derive_docker)

    replay = sub.add_parser("replay", help="re-record a manifest's own invocations (the CI lane, #1683)")
    replay.add_argument("lane", help="a manifest path, or WORKFLOW/JOB for a delegation target with no manifest yet")
    replay.add_argument("--out-dir", required=True, help="where the re-recorded manifest is written")
    replay.add_argument("--dry-run", action="store_true", help="print the record commands, run nothing")
    replay.set_defaults(func=command_replay)

    plan = sub.add_parser("plan", help="the CI lane's matrix: one leg per lane to record")
    plan.add_argument("--github-output", default=None, help="append `matrix=<json>` to this file")
    plan.set_defaults(func=command_plan)

    compare = sub.add_parser("compare", help="the committed manifests against a CI recording of them")
    compare.add_argument("recorded_dir")
    compare.add_argument("--committed-dir", default=None, help="default: .github/lane-inputs/")
    compare.add_argument("--run-id", default=None, help="the run whose `lane-inputs` artifact holds the recording")
    compare.set_defaults(func=command_compare)

    show = sub.add_parser("show", help="summarise a manifest")
    show.add_argument("manifest")
    show.set_defaults(func=command_show)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if getattr(args, "command", None) and args.command and args.command[0] == "--":
        args.command = args.command[1:]
    try:
        return int(args.func(args))
    except LaneInputsError as exc:
        print(f"lane-inputs: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
