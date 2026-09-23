"""The recorder behind ``.github/lane-inputs/`` parses what strace writes, and hashes what the guard hashes (#1596).

``scripts/ci/lane_inputs.py`` is the measuring instrument for
``tests/unit/guards/test_lane_filters_cover_measured_inputs.py``. Two things
about it have to be pinned rather than trusted:

* **The trace parser.** A recorder that silently stopped recognising strace's
  ``openat`` spelling would record an EMPTY read set, and the guard would then
  reject the manifest (a job that reads nothing measured nothing) — but a
  recorder that recognised *some* spellings and not others would record a
  SHORT read set, which the guard cannot tell from a complete one. So the
  parser is fed a trace with every line shape the recorder must understand,
  and asserted line by line.
* **The job hash.** The recorder writes ``job_spec_sha256`` and the guard
  recomputes it; the two functions live in different files and must be the
  same function. Asserted over every job of every real workflow, so a drift
  between them cannot hide behind a planted example.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found")


def _load_recorder() -> ModuleType:
    path = _REPO_ROOT / "scripts" / "ci" / "lane_inputs.py"
    spec = importlib.util.spec_from_file_location("_lane_inputs_recorder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


recorder = _load_recorder()


_TRACE = """\
execve("/usr/bin/git", ["git", "rev-parse", "HEAD"], 0x7ffe1685ca28 /* 85 vars */) = 0
openat(AT_FDCWD</repo>, "Taskfile.yaml", O_RDONLY|O_CLOEXEC) = 3</repo/Taskfile.yaml>
openat(AT_FDCWD</repo>, "src/backend", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4</repo/src/backend>
getdents64(4</repo/src/backend>, 0x5d7e05248b60 /* 15 entries */, 32768) = 640
openat(4</repo/src/backend>, "pyproject.toml", O_RDONLY|O_CLOEXEC) = 5</repo/src/backend/pyproject.toml>
open("/repo/docs/index.md", O_RDONLY) = 6</repo/docs/index.md>
readlink("/repo/link", "target", 4095) = 6
openat(AT_FDCWD</repo>, "gone.txt", O_RDONLY) = 7</repo/gone.txt (deleted)>
execveat(3</usr/bin>, "python3", ["python3", "-c", "print(1)"], 0x0, 0) = 0
"""


class TestTheTraceParser:
    def test_every_line_shape_is_understood(self, tmp_path: Path) -> None:
        trace_file = tmp_path / "trace.1"
        trace_file.write_text(_TRACE)
        trace = recorder.Trace()
        recorder._parse_trace_file(trace_file, trace)
        assert trace.files == {
            "/repo/Taskfile.yaml",
            "/repo/src/backend/pyproject.toml",
            "/repo/docs/index.md",
            "/repo/link",
            "/repo/gone.txt",
        }, "a file open in any of open/openat spellings, relative to a dirfd or absolute, is a read"
        assert trace.listings == {"/repo/src/backend"}, "getdents64 on a decorated fd is a listing"
        assert "/repo/src/backend" not in trace.files, "an O_DIRECTORY open is a lookup, not a read"
        assert trace.execs == [["git", "rev-parse", "HEAD"], ["python3", "-c", "print(1)"]]

    def test_a_failed_call_never_reaches_the_parser_by_construction(self, tmp_path: Path) -> None:
        """``-z`` keeps only successful calls; the regex ALSO demands a decorated result."""
        trace = recorder.Trace()
        trace_file = tmp_path / "trace.2"
        trace_file.write_text(
            'openat(AT_FDCWD</repo>, "missing.txt", O_RDONLY) = -1 ENOENT (No such file or directory)\n'
        )
        recorder._parse_trace_file(trace_file, trace)
        assert trace.files == set()


class TestSubprocessLabels:
    def test_a_program_is_named_without_the_machine_it_ran_on(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        (root / "scripts").mkdir(parents=True)

        def label(argv: list[str], cwd: Path = root) -> str:
            return recorder.program_label(argv, cwd=cwd, repo_root=root)

        assert label(["/usr/bin/git", "diff"]) == "git"
        assert label(["/home/someone/.asdf/installs/task/3.52.0/bin/task", "lint"]) == "task"
        assert label([str(root / "scripts" / "x.sh")]) == "scripts/x.sh"
        assert label(["./scripts/x.sh"]) == "scripts/x.sh"
        assert label(["../../scripts/x.sh"], cwd=root / "src" / "backend") == "scripts/x.sh"
        assert label(["uv", "run"]) == "uv"
        assert label([]) == "?"

    def test_merging_records_program_names_once(self) -> None:
        manifest = {"invocations": [], "reads": ["a"], "subprocesses": ["git"]}
        recorder._merge_into(
            manifest,
            invocation={"command": "x"},
            reads={"b"},
            execs=[["/usr/bin/git", "log"], ["/usr/bin/git", "diff"], ["/opt/node/bin/node", "x.js"]],
            cwd=_REPO_ROOT,
        )
        assert manifest["subprocesses"] == ["git", "node"]
        assert manifest["reads"] == ["a", "b"]


class TestRepoRelativeReads:
    def test_paths_outside_the_checkout_and_untracked_paths_are_dropped(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        (root / "src").mkdir(parents=True)
        (root / "src" / "a.py").write_text("")
        relative = recorder.to_repo_relative(
            {str(root / "src" / "a.py"), "/etc/hosts", "src/b.py"}, repo_root=root, cwd=root
        )
        assert relative == {"src/a.py", "src/b.py"}, "cwd-relative and absolute both resolve; /etc is outside"

    def test_implied_directories_include_the_root(self) -> None:
        assert recorder.implied_directories(frozenset({"src/backend/app/main.py"})) == frozenset(
            {"", "src", "src/backend", "src/backend/app"}
        )


class TestDockerfileCopySources:
    def test_copy_sources_skip_stage_copies_and_keep_context_ones(self, tmp_path: Path) -> None:
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(
            "FROM base AS build\n"
            "COPY pyproject.toml uv.lock ./\n"
            "COPY --chown=1000:1000 app/ ./app/\n"
            "COPY --from=build /out /out\n"
            'COPY ["public", "./public"]\n'
            "ADD scripts/x.sh \\\n    /x.sh\n"
            "COPY . .\n"
        )
        assert recorder.dockerfile_copy_sources(dockerfile) == [
            "pyproject.toml",
            "uv.lock",
            "app/",
            "public",
            "scripts/x.sh",
            ".",
        ]

    def test_a_source_selects_its_subtree_and_dot_selects_everything(self) -> None:
        context = {"app/main.py", "app/sub/x.py", "tests/t.py", "pyproject.toml"}
        assert recorder._match_copy_source("app/", context) == {"app/main.py", "app/sub/x.py"}
        assert recorder._match_copy_source("pyproject.toml", context) == {"pyproject.toml"}
        assert recorder._match_copy_source(".", context) == context
        assert recorder._match_copy_source("*.toml", context) == {"pyproject.toml"}


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    from tests.unit.guards import test_lane_filters_cover_measured_inputs as module

    return module


class TestTheJobHashIsTheSameFunctionInBothFiles:
    """The recorder writes it, the guard recomputes it; a drift would stale every manifest or none."""

    def test_over_every_job_of_every_workflow(self, guard: ModuleType) -> None:
        compared = 0
        for path in sorted((_REPO_ROOT / ".github" / "workflows").glob("*.y*ml")):
            document = yaml.safe_load(path.read_text())
            for job_id, job in (document.get("jobs") or {}).items():
                assert recorder.hash_job_spec(job) == guard.job_spec_hash(job), f"{path.name}:{job_id}"
                compared += 1
        assert compared >= 40, f"only {compared} jobs compared — the workflow sweep lost sight of something"

    def test_the_filter_patterns_are_outside_the_hash(self, guard: ModuleType) -> None:
        job = {
            "steps": [
                {"uses": "dorny/paths-filter@" + "0" * 40, "with": {"filters": "a:\n  - 'x/**'\n", "base": "develop"}},
                {"run": "pytest"},
            ]
        }
        widened = {
            "steps": [
                {
                    "uses": "dorny/paths-filter@" + "0" * 40,
                    "with": {"filters": "a:\n  - 'x/**'\n  - 'y'\n", "base": "develop"},
                },
                {"run": "pytest"},
            ]
        }
        changed_base = {
            "steps": [
                {"uses": "dorny/paths-filter@" + "0" * 40, "with": {"filters": "a:\n  - 'x/**'\n", "base": "main"}},
                {"run": "pytest"},
            ]
        }
        assert recorder.hash_job_spec(job) == recorder.hash_job_spec(widened) == guard.job_spec_hash(widened)
        assert recorder.hash_job_spec(job) != recorder.hash_job_spec(changed_base), (
            "every other input stays in the hash"
        )
