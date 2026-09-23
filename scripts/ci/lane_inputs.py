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

    # a docker-built job: what the build context hands the daemon
    python3 scripts/ci/lane_inputs.py derive-docker \\
        --workflow docker-lint-build.yml --job build-backend --filter backend \\
        --context src/backend --dockerfile src/backend/Dockerfile

    python3 scripts/ci/lane_inputs.py show .github/lane-inputs/<name>.yaml

Standard library plus PyYAML. Traces to #1596 (no TC-ID: a source-tree gate is
not a user-facing case).
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob as globmodule
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = REPO_ROOT / ".github" / "lane-inputs"
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

#: Manifest schema version. Bump when a field's meaning changes, so the guard
#: can refuse a manifest written under an older contract instead of misreading it.
SCHEMA = 1

#: The syscalls that decide "this file was read". ``openat``/``open`` for files,
#: ``getdents64`` for directory listings, ``execve`` so the followed subprocesses
#: are on record. ``readlink`` is included because a symlink's target is what a
#: ``git ls-files`` entry actually stores.
_TRACED_SYSCALLS = "openat,open,openat2,getdents64,execve,execveat,readlink,readlinkat"

_OPEN_LINE = re.compile(r"^(?:\d+\s+)?(?:open|openat|openat2)\((?P<args>.*)\)\s*=\s*(?P<fd>\d+)<(?P<path>[^>]*)>")
_GETDENTS_LINE = re.compile(r"^(?:\d+\s+)?getdents64\((?P<fd>\d+)<(?P<path>[^>]*)>")
_EXECVE_LINE = re.compile(r'^(?:\d+\s+)?execve(?:at)?\((?:\d+<[^>]*>,\s*)?"(?P<program>[^"]*)",\s*\[(?P<argv>.*?)\],')
_READLINK_LINE = re.compile(r'^(?:\d+\s+)?readlink(?:at)?\((?:(?:AT_FDCWD|\d+<[^>]*>),\s*)?"(?P<path>[^"]*)",')
_ARGV_ITEM = re.compile(r'"((?:[^"\\]|\\.)*)"')

EXIT_OK = 0
EXIT_USAGE = 2


class LaneInputsError(Exception):
    """A usage or environment problem, reported without a traceback."""


@dataclass
class Trace:
    """What one traced invocation touched, before the tracked-file filter."""

    files: set[str] = field(default_factory=set)
    listings: set[str] = field(default_factory=set)
    execs: list[list[str]] = field(default_factory=list)
    returncode: int = 0


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
    """Run *command* under ``strace -ff -y -z`` and parse every per-thread trace file.

    ``-ff`` writes one file per thread, so no line is ever split into
    ``<unfinished ...>`` / ``<... resumed>`` halves; ``-y`` decorates every file
    descriptor with the path it resolves to, which is how a relative ``openat``
    against a ``dirfd`` becomes an absolute path without re-implementing the
    kernel's resolution; ``-z`` keeps only successful calls, so a probe for a
    file that does not exist is never mistaken for a read of one.
    """
    strace = strace_binary()
    with tempfile.TemporaryDirectory(prefix="lane-inputs-") as scratch:
        prefix = Path(scratch) / "trace"
        argv = [
            strace,
            "-ff",
            "-y",
            "-z",
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
        completed = subprocess.run(argv, cwd=cwd, env=env, check=False)
        trace = Trace(returncode=completed.returncode)
        for trace_file in sorted(Path(scratch).glob("trace.*")):
            _parse_trace_file(trace_file, trace)
    return trace


def _parse_trace_file(path: Path, trace: Trace) -> None:
    with path.open("r", encoding="utf-8", errors="surrogateescape") as handle:
        for line in handle:
            match = _OPEN_LINE.match(line)
            if match:
                if "O_DIRECTORY" in match.group("args"):
                    continue  # a directory open is a lookup; its listing is the getdents below
                trace.files.add(_clean(match.group("path")))
                continue
            match = _GETDENTS_LINE.match(line)
            if match:
                trace.listings.add(_clean(match.group("path")))
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
    """SHA-256 of the parsed job, minus the ``filters`` input of any ``paths-filter`` step.

    The patterns are held against the manifest LIVE by the guard; they are not
    an input to what the job reads, so editing them must not demand a
    re-measurement. Everything else about the job — every step, every
    ``run:``, every ``with:`` — is part of the hash. The guard computes the
    same function; keep the two identical.
    """
    canonical = json.dumps(_without_filter_patterns(job), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def manifest_path(workflow: str, job: str) -> Path:
    stem = workflow.rsplit(".", 1)[0]
    return MANIFEST_DIR / f"{stem}--{job}.yaml"


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
        "# filter can be held against it (#1596). Do not edit `reads` by hand: re-run the\n"
        "# `invocations` below. The guard is\n"
        "# src/backend/tests/unit/guards/test_lane_filters_cover_measured_inputs.py.\n"
    )
    body = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(header + body)


def _fresh_manifest(args: argparse.Namespace, document: dict[str, Any]) -> dict[str, Any]:
    gate: dict[str, Any] = {"kind": "paths-filter" if args.filter else "on-paths"}
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


def _merge_into(
    manifest: dict[str, Any],
    *,
    invocation: dict[str, Any],
    reads: set[str],
    execs: list[list[str]],
    cwd: Path = REPO_ROOT,
) -> None:
    manifest["invocations"].append(invocation)
    known = set(manifest.get("reads") or [])
    manifest["reads"] = sorted(known | reads)
    programs = {str(entry) for entry in manifest.get("subprocesses") or [] if isinstance(entry, str)}
    programs |= {program_label(argv, cwd=cwd) for argv in execs}
    manifest["subprocesses"] = sorted(programs)
    manifest["measured_on"] = dt.date.today().isoformat()
    manifest["measured_at_commit"] = head_commit()


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
        target = manifest_path(args.workflow, args.job)
        write_manifest(target, manifest)
        print(
            f"lane-inputs: recorded an empty read set with its reason → {target.relative_to(REPO_ROOT)}",
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
            "is a read set of the failure path. Fix the run, or pass --allow-failure if the "
            "exit code is the invocation's verdict rather than a crash."
        )

    tracked = tracked_files()
    directories = implied_directories(tracked)
    files = to_repo_relative(trace.files, repo_root=REPO_ROOT, cwd=cwd)
    listings = to_repo_relative(trace.listings, repo_root=REPO_ROOT, cwd=cwd)
    reads = {entry for entry in files if entry in tracked}
    reads |= {f"{entry}/" if entry else "./" for entry in listings if entry in directories}
    dropped_untracked = len(files - tracked)

    target = manifest_path(args.workflow, args.job)
    if args.append and target.is_file():
        manifest = load_manifest(target)
        if manifest.get("job") != args.job or manifest.get("workflow") != args.workflow:
            raise LaneInputsError(f"{target} belongs to another lane; refusing to append")
        manifest["job_spec_sha256"] = job_spec_hash(document, args.job)
    else:
        manifest = _fresh_manifest(args, document)

    invocation = {
        "command": " ".join(args.command),
        "cwd": cwd.relative_to(REPO_ROOT).as_posix() or ".",
        "recorder": "strace -ff -y -z",
        "exit_code": trace.returncode,
        "env": sorted(args.env),
        "untracked_reads_dropped": dropped_untracked,
    }
    _merge_into(manifest, invocation=invocation, reads=reads, execs=trace.execs, cwd=cwd)
    manifest["status"] = "measured"
    write_manifest(target, manifest)
    print(
        f"lane-inputs: {len(reads)} tracked path(s) read ({dropped_untracked} untracked dropped), "
        f"{len(trace.execs)} subprocess exec(s) followed → {target.relative_to(REPO_ROOT)}",
        file=sys.stderr,
    )
    return EXIT_OK


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

    target = manifest_path(args.workflow, args.job)
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
        f"lane-inputs: {len(reads)} tracked path(s) in the narrowed context → {target.relative_to(REPO_ROOT)}",
        file=sys.stderr,
    )
    return EXIT_OK


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

    record = sub.add_parser("record", help="run an invocation under strace and record its tracked reads")
    lane_arguments(record)
    record.add_argument("--cwd", default=None, help="directory the invocation runs in, repo-relative")
    record.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    record.add_argument("--allow-failure", action="store_true")
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
