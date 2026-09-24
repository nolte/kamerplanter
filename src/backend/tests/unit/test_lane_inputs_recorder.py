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


class TestTheContractIsTheSameInBothFiles:
    """Schema number and reason floor: the recorder writes under them, the guard reads under them."""

    def test_schema_and_reason_floor(self, guard: ModuleType) -> None:
        assert recorder.SCHEMA == guard._SCHEMA, "a manifest written by this recorder must be one the guard accepts"
        assert recorder.MIN_REASON_CHARS == guard._MIN_REASON_CHARS

    def test_a_reason_shorter_than_the_floor_is_refused_at_the_command_line(self) -> None:
        import argparse

        with pytest.raises(argparse.ArgumentTypeError):
            recorder._reason("skips")
        assert recorder._reason("x" * recorder.MIN_REASON_CHARS) == "x" * recorder.MIN_REASON_CHARS


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


# ------------------------------------------------------------ the CI lane (#1683)


def _committed(**overrides: object) -> dict:
    manifest: dict = {
        "schema": recorder.SCHEMA,
        "workflow": "w.yml",
        "job": "j",
        "gate": {"kind": "on-paths"},
        "status": "measured",
        "job_spec_sha256": "a" * 64,
        "invocations": [
            {
                "command": "python -m x --out /tmp/claude-1000/some/scratchpad/out.json",
                "cwd": "src/backend",
                "recorder": "strace -ff -y -z",
                "exit_code": 0,
                "env": ["UV_PROJECT_ENVIRONMENT=/tmp/claude-1000/some/scratchpad/venv"],
                "untracked_reads_dropped": 3,
            }
        ],
        "subprocesses": ["python"],
        "accepted_gaps": [],
        "reads": ["src/backend/a.py", "src/backend/tests/"],
    }
    manifest.update(overrides)
    return manifest


def _write(directory: Path, name: str, manifest: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(yaml.safe_dump(manifest, sort_keys=False))


class TestScratchPathsAreOneToken:
    def test_a_workstation_scratchpad_and_the_ci_scratch_dir_normalise_to_the_same_path(self) -> None:
        workstation = "uv export -o /tmp/claude-1000/-home-x/abc/scratchpad/requirements.txt"
        ci = "uv export -o /tmp/lane-inputs-scratch/requirements.txt"
        assert recorder.normalise_scratch(workstation) == recorder.normalise_scratch(ci) == ci

    def test_a_path_inside_a_shell_string_is_rewritten_up_to_the_shell_punctuation(self) -> None:
        text = "sed x a.yml > /tmp/s/pad/out.yml; cp .env.example /tmp/s/pad/.env-x"
        assert recorder.normalise_scratch(text) == (
            "sed x a.yml > /tmp/lane-inputs-scratch/out.yml; cp .env.example /tmp/lane-inputs-scratch/.env-x"
        )

    def test_a_repo_relative_path_is_left_alone(self) -> None:
        assert recorder.normalise_scratch("pytest tests/unit --rootdir .") == "pytest tests/unit --rootdir ."


class TestCompare:
    """The verdict of lane-inputs.yml: committed manifests against a CI recording of them."""

    def test_an_identical_recording_is_no_finding(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed())
        ci = _committed(
            measured_on="2030-01-01",
            subprocesses=["python", "git"],
            invocations=[
                {
                    **_committed()["invocations"][0],
                    "command": "python -m x --out /tmp/lane-inputs-scratch/out.json",
                    "env": ["UV_PROJECT_ENVIRONMENT=/tmp/lane-inputs-scratch/venv"],
                    "untracked_reads_dropped": 900,
                }
            ],
        )
        _write(tmp_path / "recorded", "w--j.yaml", ci)
        findings, notes = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == [] and notes == [], "when and where it was recorded is not a difference"

    def test_a_hand_trimmed_reads_list_is_a_finding_naming_the_missing_path(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed(reads=["src/backend/a.py"]))
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert len(findings) == 1
        assert "does not list" in findings[0] and "src/backend/tests/" in findings[0]

    def test_a_listed_path_the_run_did_not_read_is_a_finding(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed(reads=["src/backend/a.py", "src/backend/tests/", "x"]))
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert len(findings) == 1 and "did not read" in findings[0] and "x" in findings[0]

    def test_a_hash_that_is_not_the_live_jobs_is_a_finding(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed())
        _write(tmp_path / "recorded", "w--j.yaml", _committed(job_spec_sha256="b" * 64))
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert len(findings) == 1 and "job_spec_sha256" in findings[0]

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("command", "python -m y"),
            ("cwd", "."),
            ("exit_code", 1),
            ("env", []),
            ("scratch_inputs", {"out.json": "{}"}),
        ],
    )
    def test_an_invocation_that_differs_is_a_finding(self, tmp_path: Path, field: str, value: object) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed())
        changed = {**_committed()["invocations"][0], field: value}
        _write(tmp_path / "recorded", "w--j.yaml", _committed(invocations=[changed]))
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert len(findings) == 1 and "invocations[0]" in findings[0], findings

    def test_a_partial_manifest_recorded_in_full_is_a_finding_until_committed(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed(status="partial", partial_reason="r" * 50))
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == ["w--j.yaml: status 'partial' committed, 'measured' recorded"]

    def test_a_lane_the_ci_run_did_not_record_is_a_finding_not_silence(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed())
        (tmp_path / "recorded").mkdir()
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert len(findings) == 1 and "recorded no manifest" in findings[0]

    def test_a_manifest_without_invocations_is_a_note_and_a_new_recording_is_a_finding(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "committed",
            "w--changes.yaml",
            _committed(invocations=[], reads=[], empty_reads_reason="checkout and paths-filter only, nothing read"),
        )
        _write(tmp_path / "recorded", "b--guards.yaml", _committed(workflow="b.yml", job="guards"))
        findings, notes = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert notes == ["w--changes.yaml: no invocation to replay — checkout and paths-filter only, nothing read"]
        assert findings == [
            "b--guards.yaml: recorded in CI and not committed — commit it (a delegation target's first manifest)"
        ]

    def test_the_cli_exits_red_and_says_how_to_commit_the_recording(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        _write(tmp_path / "committed", "w--j.yaml", _committed(reads=[]))
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        code = recorder.main(
            ["compare", str(tmp_path / "recorded"), "--committed-dir", str(tmp_path / "committed"), "--run-id", "42"]
        )
        out = capsys.readouterr().out
        assert code == recorder.EXIT_FINDINGS
        assert "gh run download 42 -n lane-inputs -D /tmp/lane-inputs-42" in out

    def test_the_committed_tree_compared_with_itself_is_green(self) -> None:
        """The recorded invocation of lane-inputs.yml/compare — it must stay replayable anywhere."""
        findings, _ = recorder.compare_manifests(recorder.MANIFEST_DIR, recorder.MANIFEST_DIR)
        assert findings == []


class TestReplay:
    def test_the_base_keeps_hand_written_fields_and_drops_measured_ones(self) -> None:
        committed = _committed(
            status="partial",
            partial_reason="r" * 50,
            accepted_gaps=[{"pattern": "x", "reason": "y" * 50}],
            unrecorded_invocations=[{"command": "z", "reason": "w" * 50}],
        )
        base = recorder._replay_base(committed)
        assert base["invocations"] == [] and base["reads"] == [] and base["subprocesses"] == []
        assert base["status"] == "measured" and "partial_reason" not in base
        assert base["accepted_gaps"] == committed["accepted_gaps"]
        assert base["unrecorded_invocations"] == committed["unrecorded_invocations"]
        assert base["gate"] == committed["gate"]

    def test_a_strace_invocation_replays_as_record_with_its_env_and_allow_failure(self, tmp_path: Path) -> None:
        invocation = {
            **_committed()["invocations"][0],
            "exit_code": 1,
            "allow_failure_reason": "exit 1 is the verdict, reached after every read of the gate",
        }
        argv = recorder.replay_argv(invocation, workflow="w.yml", job="j", out_dir=tmp_path)
        assert argv == [
            "record",
            "--workflow",
            "w.yml",
            "--job",
            "j",
            "--append",
            "--manifest-dir",
            str(tmp_path),
            "--cwd",
            "src/backend",
            "--env",
            "UV_PROJECT_ENVIRONMENT=/tmp/lane-inputs-scratch/venv",
            "--allow-failure",
            "exit 1 is the verdict, reached after every read of the gate",
            "--",
            "python",
            "-m",
            "x",
            "--out",
            "/tmp/lane-inputs-scratch/out.json",
        ]

    def test_a_derived_invocation_replays_as_derive_docker(self, tmp_path: Path) -> None:
        invocation = {
            "command": "derive-docker --context src/backend --dockerfile src/backend/Dockerfile",
            "cwd": ".",
            "recorder": "docker build context probe (FROM scratch, COPY . — …)",
            "copy_sources": ["."],
        }
        argv = recorder.replay_argv(invocation, workflow="w.yml", job="j", out_dir=tmp_path)
        assert argv[0] == "derive-docker"
        assert argv[-4:] == ["--context", "src/backend", "--dockerfile", "src/backend/Dockerfile"]

    def test_every_committed_manifest_can_be_turned_into_replay_commands(self, tmp_path: Path) -> None:
        """No invocation in the tree is in a shape the CI lane cannot replay."""
        replayed = 0
        for path in sorted(recorder.MANIFEST_DIR.glob("*.yaml")):
            manifest = recorder.load_manifest(path)
            for invocation in manifest.get("invocations") or []:
                recorder.replay_argv(invocation, workflow=manifest["workflow"], job=manifest["job"], out_dir=tmp_path)
                replayed += 1
        assert replayed >= 60, f"only {replayed} invocations — the sweep lost sight of something"

    def test_a_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        code = recorder.main(
            ["replay", "--dry-run", "--out-dir", str(tmp_path / "out"), ".github/lane-inputs/side-services--libs.yaml"]
        )
        assert code == recorder.EXIT_OK
        assert not (tmp_path / "out").exists()

    def test_a_missing_program_refuses_the_lane_instead_of_narrowing_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(recorder.shutil, "which", lambda _program: None)
        code = recorder.main(
            ["replay", "--out-dir", str(tmp_path / "out"), ".github/lane-inputs/docker-lint-build--changes.yaml"]
        )
        assert code == recorder.EXIT_USAGE
        assert not (tmp_path / "out" / "docker-lint-build--changes.yaml").exists()


class TestBootstrap:
    def test_the_unrecorded_delegation_target_is_derived_from_its_own_run_line(self) -> None:
        invocations = recorder.bootstrap_invocations("backend-guards.yml", "guards")
        assert invocations == [
            {
                "command": "pytest tests/unit/api tests/unit/guards -q --max-skipped 0 -m 'not advisory'",
                "cwd": "src/backend",
                "env": ["KAMERPLANTER_MODE=full"],
            }
        ]

    def test_a_filtered_job_is_refused(self) -> None:
        with pytest.raises(recorder.LaneInputsError, match="decides its relevance with a filter"):
            recorder.bootstrap_invocations("backend-guards.yml", "integration")

    def test_the_plan_names_every_manifest_with_invocations_and_the_unrecorded_target(self) -> None:
        legs = recorder.plan_matrix()
        lanes = {leg["lane"] for leg in legs}
        expected = {
            f".github/lane-inputs/{path.name}"
            for path in recorder.MANIFEST_DIR.glob("*.yaml")
            if recorder.load_manifest(path).get("invocations")
        }
        assert expected <= lanes
        assert {leg["name"] for leg in legs} == {lane.rpartition("/")[2].removesuffix(".yaml") for lane in expected} | {
            leg["name"] for leg in legs if not leg["lane"].endswith(".yaml")
        }
        integration = next(leg for leg in legs if leg["name"] == "backend-guards--integration")
        assert integration["arangodb"] and integration["backend"]

    def test_held_commands_select_what_the_guards_rule_5_holds(self, guard: ModuleType) -> None:
        """The bootstrap derives invocations from the same commands rule 5 holds a manifest against."""
        compared = 0
        for workflow in guard.load_workflows(_REPO_ROOT / ".github"):
            if workflow.path.parent.name != "workflows":
                continue
            for job_id, job in workflow.jobs.items():
                if not isinstance(job, dict):
                    continue
                ours = [(tokens, cwd) for tokens, cwd, _env in recorder.held_commands(workflow.document, job_id)]
                theirs = [(tokens, cwd) for _spelling, tokens, cwd in guard.job_commands(workflow, job)]
                assert ours == theirs, f"{workflow.name}:{job_id}"
                compared += len(ours)
        assert compared >= 30, f"only {compared} held commands compared"


class TestALossySpellingIsRefused:
    def test_a_command_whose_quoting_was_lost_is_not_replayed(self, tmp_path: Path) -> None:
        """The `bash -c find … | wc -l` spelling replayed as a bare `find` over the checkout (462 reads, not 9)."""
        invocation = {**_committed()["invocations"][0], "command": "bash -c find tests -name '*.yaml' | wc -l"}
        with pytest.raises(recorder.LaneInputsError, match="quoting was lost"):
            recorder.replay_argv(invocation, workflow="w.yml", job="j", out_dir=tmp_path)

    def test_the_same_command_spelled_by_shlex_join_is(self, tmp_path: Path) -> None:
        invocation = {
            **_committed()["invocations"][0],
            "command": "bash -c 'find tests -name '\"'\"'*.yaml'\"'\"' | wc -l'",
        }
        argv = recorder.replay_argv(invocation, workflow="w.yml", job="j", out_dir=tmp_path)
        assert argv[argv.index("--") + 1 :] == ["bash", "-c", "find tests -name '*.yaml' | wc -l"]


class TestTheReplayReproducesTheJobsPath:
    """A job that puts its venv on PATH via $GITHUB_PATH is replayed with that PATH (#1683, first CI run)."""

    def test_the_side_services_venvs_are_read_from_the_workflow(self) -> None:
        _path, document = recorder.load_workflow("side-services.yml")
        assert recorder.job_path_additions(document, "libs") == ["src/libs/kp_vectordb/.venv/bin"]
        assert recorder.job_path_additions(document, "inference-service") == ["src/inference-service/.venv/bin"]

    def test_a_runner_temp_tool_dir_is_the_lanes_to_provide_not_the_replays(self) -> None:
        document = {"jobs": {"j": {"steps": [{"run": 'echo "$RUNNER_TEMP/bin" >> "$GITHUB_PATH"'}]}}}
        assert recorder.job_path_additions(document, "j") == []

    def test_another_spelling_is_refused_rather_than_silently_not_reproduced(self) -> None:
        document = {"jobs": {"j": {"steps": [{"run": "echo /opt/x/bin >> $GITHUB_PATH"}]}}}
        with pytest.raises(recorder.LaneInputsError, match="GITHUB_PATH"):
            recorder.job_path_additions(document, "j")

    def test_every_live_job_that_writes_github_path_is_understood(self) -> None:
        """No workflow writes $GITHUB_PATH in a spelling the replay would refuse."""
        for path in sorted(recorder.WORKFLOW_DIR.glob("*.yml")):
            _p, document = recorder.load_workflow(path.name)
            for job in document.get("jobs") or {}:
                recorder.job_path_additions(document, job)

    def test_the_replay_leaves_path_as_it_found_it(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(recorder.shutil, "which", lambda _program: None)
        before = recorder.os.environ.get("PATH")
        code = recorder.main(
            ["replay", "--out-dir", str(tmp_path / "out"), ".github/lane-inputs/side-services--libs.yaml"]
        )
        assert code == recorder.EXIT_USAGE
        assert recorder.os.environ.get("PATH") == before


class TestScratchInputs:
    """A stand-in for a file an earlier step produced is declared in the manifest, not assumed."""

    def test_a_scratch_input_replays_as_an_argument(self, tmp_path: Path) -> None:
        invocation = {
            **_committed()["invocations"][0],
            "scratch_inputs": {"out.json": '{"site": []}'},
        }
        argv = recorder.replay_argv(invocation, workflow="w.yml", job="j", out_dir=tmp_path)
        assert argv[argv.index("--scratch-input") + 1] == 'out.json={"site": []}'

    def test_a_stand_in_the_command_does_not_name_is_refused(self) -> None:
        with pytest.raises(recorder.LaneInputsError, match="not a path the invocation names"):
            recorder._scratch_inputs(["other.json={}"], ["python", "x.py", "/tmp/lane-inputs-scratch/in.json"])

    def test_a_path_is_not_a_basename(self) -> None:
        with pytest.raises(recorder.LaneInputsError, match="BASENAME=CONTENT"):
            recorder._scratch_inputs(["a/b.json={}"], ["python", "/tmp/lane-inputs-scratch/a/b.json"])

    def test_a_workstation_scratch_path_names_the_same_input(self) -> None:
        command = ["python3", "gate.py", "/tmp/claude-1000/x/scratchpad/zap-empty.json"]
        assert recorder._scratch_inputs(["zap-empty.json={}"], command) == {"zap-empty.json": "{}"}

    def test_the_committed_zap_manifest_declares_its_report_stand_in(self) -> None:
        manifest = recorder.load_manifest(recorder.MANIFEST_DIR / "security-zap-postmerge--zap-scan.yaml")
        gates = [i for i in manifest["invocations"] if "zap_gate.py" in i["command"]]
        assert gates and all(i.get("scratch_inputs", {}).get("zap-empty.json") for i in gates)
