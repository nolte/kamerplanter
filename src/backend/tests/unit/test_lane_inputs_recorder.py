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
        assert recorder.REPLAY_SECONDS_MAX == guard._REPLAY_SECONDS_MAX

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
        "replay_seconds": 120,
    }
    manifest.update(overrides)
    return manifest


def _unmeasured(**overrides: object) -> dict:
    """A manifest as a workstation `record` (or the recorder before #1683's per-leg timeout) wrote it."""
    manifest = _committed(**overrides)
    del manifest["replay_seconds"]
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
                "command": (
                    "pytest tests/unit/api tests/unit/guards"
                    # The frontend and e2e-helper readers the lane names since #1741.
                    " tests/unit/test_seed_catalogue_page_size_check.py tests/unit/entrypoints"
                    " tests/unit/test_route_role_guards_check.py"
                    " tests/unit/domain/services/test_oauth_auto_link_claim.py"
                    " tests/unit/test_e2e_a11y_helpers.py tests/unit/test_e2e_seed_log_redaction.py"
                    " tests/unit/test_e2e_tc_id_scope.py tests/unit/test_gherkin_line_classification.py"
                    " tests/contracts/test_plant_property_enum_sync.py"
                    " tests/contracts/test_dashboard_widgets_contract.py"
                    " tests/contracts/test_notification_channels_contract.py"
                    " tests/api/test_notification_act_role_gate.py"
                    " -q --max-skipped 0 -m 'not advisory'"
                ),
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


# ------------------------------------------------ per-leg replay timeout (#1683)


class TestThePlanSizesEachLegsTimeoutFromItsMeasuredReplay:
    """`plan` turns a manifest's measured `replay_seconds` into the leg's step timeout.

    Asserted through ``plan_matrix`` — the function ``plan --github-output``
    serialises into the matrix the ``record`` job reads — over a planted
    manifest directory, so the arithmetic is reached the way production reaches it.
    """

    @pytest.mark.parametrize(
        ("seconds", "minutes"),
        [
            (1, 10),  # a docker-derived leg: the floor, not 1 minute
            (200, 10),  # 3 × 200 s = 10 min exactly
            (201, 11),  # rounded UP: a bound rounded down is tighter than the rule
            (394, 20),  # backend-guards--integration, slowest of five runs on 2026-09-24
            (1756, 88),  # backend--coverage, slowest successful leg measured on 2026-09-24
            (1800, 90),
            (1801, 90),  # capped at the job-level bound
            (5400, 90),
        ],
    )
    def test_three_times_the_recorded_duration_between_floor_and_cap(
        self, tmp_path: Path, seconds: int, minutes: int
    ) -> None:
        _write(tmp_path, "w--j.yaml", _committed(replay_seconds=seconds))
        (leg,) = recorder.plan_matrix(tmp_path)
        assert leg["timeout_minutes"] == minutes

    @pytest.mark.parametrize("value", [None, 0, -5, "600", True, 12.5, 5401])
    def test_a_leg_without_a_usable_measurement_gets_the_job_level_bound(self, tmp_path: Path, value: object) -> None:
        manifest = _unmeasured() if value is None else _committed(replay_seconds=value)
        _write(tmp_path, "w--j.yaml", manifest)
        (leg,) = recorder.plan_matrix(tmp_path)
        assert leg["timeout_minutes"] == recorder.TIMEOUT_CAP_MINUTES == 90

    def test_a_bootstrap_leg_has_never_been_measured_and_gets_the_job_level_bound(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "w--j.yaml",
            _committed(
                replay_seconds=60,
                accepted_gaps=[{"pattern": "x", "reason": "r" * 50, "covered_by": "backend-guards.yml/guards"}],
            ),
        )
        legs = {leg["name"]: leg for leg in recorder.plan_matrix(tmp_path)}
        assert legs["w--j"]["timeout_minutes"] == 10
        assert legs["backend-guards--guards"]["timeout_minutes"] == recorder.TIMEOUT_CAP_MINUTES

    def test_the_cap_is_the_record_jobs_own_bound_and_the_replay_step_reads_the_leg(self) -> None:
        """The cap equals the job-level `timeout-minutes`, and the replay step is bounded by the matrix value."""
        _path, document = recorder.load_workflow("lane-inputs.yml")
        record = document["jobs"]["record"]
        assert record["timeout-minutes"] == recorder.TIMEOUT_CAP_MINUTES
        (replay,) = [step for step in record["steps"] if "lane_inputs.py replay" in str(step.get("run", ""))]
        assert replay.get("timeout-minutes") == "${{ matrix.timeout_minutes }}"


class TestTheReplayMeasuresItsOwnDuration:
    """`replay` writes `replay_seconds` — the wall clock of the step the timeout bounds — into its manifest."""

    def test_the_replayed_manifest_carries_the_measured_seconds_rounded_up(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Only the tracer is doubled: `replay` → `main(record …)` → `command_record` run as in CI.
        monkeypatch.setattr(
            recorder,
            "run_traced",
            lambda command, *, cwd, env: recorder.Trace(files={str(recorder.REPO_ROOT / "scripts/ci/lane_inputs.py")}),
        )
        clock = iter([1000.0, 1242.2])
        monkeypatch.setattr(recorder.time, "monotonic", lambda: next(clock))
        out = tmp_path / "out"
        code = recorder.main(["replay", "--out-dir", str(out), ".github/lane-inputs/lane-inputs--plan.yaml"])
        assert code == recorder.EXIT_OK
        manifest = recorder.load_manifest(out / "lane-inputs--plan.yaml")
        assert manifest["replay_seconds"] == 243
        assert manifest["reads"] == ["scripts/ci/lane_inputs.py"]
        assert manifest["schema"] == recorder.SCHEMA

    def test_a_replay_does_not_carry_the_committed_duration_over(self) -> None:
        assert "replay_seconds" not in recorder._replay_base(_committed(replay_seconds=600))

    def test_a_workstation_record_drops_a_duration_that_no_longer_describes_the_invocations(self) -> None:
        manifest = _committed(replay_seconds=600)
        recorder._merge_into(manifest, invocation={"command": "pytest"}, reads=set(), execs=[])
        assert "replay_seconds" not in manifest


class TestCompareDoesNotTreatTheDurationAsDrift:
    def test_a_different_duration_is_no_finding(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed(replay_seconds=100))
        _write(tmp_path / "recorded", "w--j.yaml", _committed(replay_seconds=900))
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == [], "wall-clock time varies run to run; it sizes a bound, it is not a read"


class TestCompareHoldsTheDurationsPresence:
    """The value is not compared; its absence where a replay happened is a finding (#1683 per-leg timeout)."""

    def test_a_committed_manifest_with_invocations_and_no_duration_is_a_finding(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _unmeasured())
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == [
            "w--j.yaml: the committed manifest has no `replay_seconds`, so `plan` gives its leg the job-level "
            "90-minute bound — commit the CI recording"
        ]

    def test_a_recording_without_a_duration_is_a_finding_against_the_recorder(self, tmp_path: Path) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed())
        _write(tmp_path / "recorded", "w--j.yaml", _unmeasured())
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == ["w--j.yaml: the CI recording has no `replay_seconds` — the replay did not measure itself"]

    @pytest.mark.parametrize("value", [0, 5401, "600", True, 12.5])
    def test_a_hand_edited_duration_is_a_finding(self, tmp_path: Path, value: object) -> None:
        _write(tmp_path / "committed", "w--j.yaml", _committed(replay_seconds=value))
        _write(tmp_path / "recorded", "w--j.yaml", _committed())
        (finding,) = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")[0]
        assert "is not a whole number of seconds between 1 and 5400" in finding

    def test_a_manifest_without_invocations_needs_none(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "committed",
            "w--changes.yaml",
            _unmeasured(invocations=[], reads=[], empty_reads_reason="checkout and paths-filter only, nothing read"),
        )
        (tmp_path / "recorded").mkdir()
        findings, _ = recorder.compare_manifests(tmp_path / "committed", tmp_path / "recorded")
        assert findings == []


# ------------------------------------ #1683: the job hash ignores action pins


#: `github/codeql-action/upload-sarif` before #1734 (v4.38.1) and after it (v4.38.2).
_CODEQL_BEFORE_1734 = "github/codeql-action/upload-sarif@1c5b675653bb5c22dbe9b12b556ec555138e09fd"
_CODEQL_AFTER_1734 = "github/codeql-action/upload-sarif@2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2"


def _report_findings_job() -> dict:
    """The live `report-findings` job of security-nuclei-postmerge.yml, the job #1734's bump staled."""
    _path, document = recorder.load_workflow("security-nuclei-postmerge.yml")
    return document["jobs"]["report-findings"]


def _with_uses(job: dict, old: str, new: str) -> dict:
    job = dict(job)
    job["steps"] = [
        {**step, "uses": step["uses"].replace(old, new)} if isinstance(step.get("uses"), str) else step
        for step in job["steps"]
    ]
    return job


class TestAnActionPinIsNotPartOfTheJobSpec:
    """A Renovate action bump changes no command the job runs and no file the recorder measures (#1683).

    #1734 moved `github/codeql-action/upload-sarif` from v4.38.1 to v4.38.2 in
    `report-findings`; the old hash went from 5e1a2241d031 to 2795890740be and
    the next unrelated backend PR inherited a red freshness guard. The recorder
    never replays an action (it replays `run:` commands), so an action's ref
    cannot be an input of the recorded read set. Asserted over the real job, for
    the recorder's hash and the guard's, which must stay the same function.
    """

    def test_the_1734_bump_leaves_the_hash_unchanged(self, guard: ModuleType) -> None:
        live = _report_findings_job()
        assert _CODEQL_AFTER_1734 in str(live), "the fixture is the job as #1734 left it"
        before = _with_uses(live, _CODEQL_AFTER_1734, _CODEQL_BEFORE_1734)
        assert recorder.hash_job_spec(before) == recorder.hash_job_spec(live)
        assert guard.job_spec_hash(before) == guard.job_spec_hash(live)

    def test_a_branch_or_tag_ref_is_a_pin_too(self) -> None:
        live = _report_findings_job()
        assert recorder.hash_job_spec(_with_uses(live, _CODEQL_AFTER_1734, "github/codeql-action/upload-sarif@v4")) == (
            recorder.hash_job_spec(live)
        )

    @pytest.mark.parametrize(
        "change",
        [
            "run",  # a command the job runs
            "with",  # an input the action is given
            "name",  # a different action altogether
            "env",
            "working-directory",
        ],
    )
    def test_everything_else_about_a_step_is_still_in_the_hash(self, guard: ModuleType, change: str) -> None:
        live = _report_findings_job()
        steps = list(live["steps"])
        index = next(i for i, step in enumerate(steps) if "codeql-action" in str(step.get("uses", "")))
        step = dict(steps[index])
        if change == "run":
            # report-findings runs no `run:` step; the plan job of lane-inputs.yml does.
            _path, document = recorder.load_workflow("lane-inputs.yml")
            live = document["jobs"]["plan"]
            steps = list(live["steps"])
            index = next(i for i, s in enumerate(steps) if isinstance(s.get("run"), str))
            step = {**steps[index], "run": steps[index]["run"] + "\necho changed"}
        elif change == "with":
            step["with"] = {**(step.get("with") or {}), "category": "changed"}
        elif change == "name":
            step["uses"] = step["uses"].replace("github/codeql-action/upload-sarif", "github/codeql-action/analyze")
        elif change == "env":
            step["env"] = {**(step.get("env") or {}), "CHANGED": "1"}
        else:
            step["working-directory"] = "src/changed"
        steps[index] = step
        changed = {**live, "steps": steps}
        assert recorder.hash_job_spec(changed) != recorder.hash_job_spec(live)
        assert guard.job_spec_hash(changed) == recorder.hash_job_spec(changed)

    def test_a_reusable_workflow_call_is_normalised_the_same_way(self, guard: ModuleType) -> None:
        call = {"uses": "nolte/gh-plumbing/.github/workflows/x.yml@" + "a" * 40, "with": {"k": "v"}}
        bumped = {**call, "uses": "nolte/gh-plumbing/.github/workflows/x.yml@" + "b" * 40}
        local = {"uses": "./.github/workflows/x.yml", "with": {"k": "v"}}
        assert recorder.hash_job_spec(call) == recorder.hash_job_spec(bumped) == guard.job_spec_hash(bumped)
        assert recorder.hash_job_spec(local) != recorder.hash_job_spec(call), "the called workflow's name counts"


# ------------------------ #1683: a replay does not run the guard against itself


class TestTheReplayDoesNotRunTheManifestGuardAgainstTheManifestsItReplaces:
    """The unit-suite legs replay `pytest tests/unit/`, which contains the manifest guard.

    That guard holds the COMMITTED manifests against the live tree — the very
    manifests the replay is producing successors for. A change to a recorded
    job staled one of them, the guard failed inside backend--lint-test and
    backend--coverage, their legs recorded nothing, and every such change cost
    two recordings (#1683, 2026-09-24). The replay deselects that one file;
    the real CI lanes still run it.
    """

    def test_every_replayed_invocation_runs_with_the_guard_deselected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def fake_trace(command: list[str], *, cwd: Path, env: dict[str, str]) -> object:
            seen.append(env.get("PYTEST_ADDOPTS", ""))
            return recorder.Trace(files={str(recorder.REPO_ROOT / "scripts/ci/lane_inputs.py")})

        monkeypatch.setattr(recorder, "run_traced", fake_trace)
        monkeypatch.setenv("PYTEST_ADDOPTS", "-p no:randomly")
        code = recorder.main(["replay", "--out-dir", str(tmp_path), ".github/lane-inputs/lane-inputs--record.yaml"])
        assert code == recorder.EXIT_OK
        assert len(seen) == 2
        assert all(
            value == "-p no:randomly --deselect tests/unit/guards/test_lane_filters_cover_measured_inputs.py"
            for value in seen
        ), seen
        assert recorder.os.environ["PYTEST_ADDOPTS"] == "-p no:randomly", "the replay restores the environment"

    def test_the_deselected_node_id_is_the_guards_own_file(self) -> None:
        backend = recorder.REPO_ROOT / "src" / "backend"
        assert (backend / recorder.REPLAY_DESELECTED_GUARD).is_file()
        assert (backend / "pyproject.toml").is_file(), "node ids are relative to src/backend, pytest's rootdir"

    def test_the_real_lanes_do_not_deselect_it(self) -> None:
        """No workflow step and no Taskfile command leaves the guard out; only the replay's environment does."""
        guard_file = recorder.REPLAY_DESELECTED_GUARD.rpartition("/")[2]
        sources = [*sorted(recorder.WORKFLOW_DIR.glob("*.yml")), recorder.REPO_ROOT / ".taskfiles" / "backend.yaml"]
        for path in sources:
            for line in path.read_text().splitlines():
                if guard_file in line:
                    assert not any(flag in line for flag in ("--deselect", "--ignore", "PYTEST_ADDOPTS")), (
                        f"{path.name}: {line.strip()}"
                    )


# ------------------------- #1683: only a read outside the filter is drift


_ON_PATHS_WORKFLOW = """\
on:
  pull_request:
    paths:
      - 'src/backend/**'
      - '!src/backend/docs/**'
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""

_STEP_FILTER_WORKFLOW = """\
on:
  pull_request:
jobs:
  changes:
    runs-on: ubuntu-latest
    steps:
      - uses: dorny/paths-filter@0000000000000000000000000000000000000000
        with:
          filters: |
            backend:
              - 'src/backend/**'
            frontend:
              - 'src/frontend/**'
  j:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""


class TestCompareCountsOnlyReadsOutsideTheFilterAsDrift:
    """`compare` over a planted workflow: a new read the filter selects is no finding, one it does not select is.

    The filter is the live one of the manifest's workflow — ``on:`` paths or the
    paths-filter names in ``gate.filter`` — decided by the matcher the guard
    uses (pinned by ``test_the_matcher_agrees_with_the_guards_over_the_committed_reads``).
    """

    def _compare(self, tmp_path: Path, committed: dict, recorded: dict, workflow: str = _ON_PATHS_WORKFLOW) -> tuple:
        (tmp_path / "workflows").mkdir(exist_ok=True)
        (tmp_path / "workflows" / "w.yml").write_text(workflow)
        _write(tmp_path / "committed", "w--j.yaml", committed)
        _write(tmp_path / "recorded", "w--j.yaml", recorded)
        return recorder.compare_manifests(
            tmp_path / "committed", tmp_path / "recorded", workflow_dir=tmp_path / "workflows"
        )

    def test_a_new_read_inside_the_filter_is_not_drift(self, tmp_path: Path) -> None:
        """The #1683 churn: a pull request adding a file the job reads, under a path that already runs it."""
        findings, notes = self._compare(
            tmp_path,
            _committed(reads=["src/backend/a.py"]),
            _committed(reads=["src/backend/a.py", "src/backend/new.py", "src/backend/tests/"]),
        )
        assert findings == []
        assert notes == ["w--j.yaml: 2 new read(s) inside the relevance filter (not drift)"]

    def test_a_new_read_outside_the_filter_is_drift_naming_the_path(self, tmp_path: Path) -> None:
        findings, _ = self._compare(
            tmp_path,
            _committed(reads=["src/backend/a.py"]),
            _committed(reads=["src/backend/a.py", "renovate.json5", "src/backend/docs/x.md"]),
        )
        assert len(findings) == 1
        assert "2 path(s) the job's relevance filter does not select" in findings[0]
        assert "renovate.json5 (the on:-level paths filter)" in findings[0]
        assert "src/backend/docs/x.md" in findings[0], "a negated pattern takes a path back out"

    def test_a_listing_is_held_as_a_file_added_inside_it(self, tmp_path: Path) -> None:
        findings, _ = self._compare(
            tmp_path, _committed(reads=["src/backend/a.py"]), _committed(reads=["src/backend/a.py", "./"])
        )
        assert len(findings) == 1 and "./ (the on:-level paths filter)" in findings[0]

    def test_the_paths_filter_named_in_gate_filter_is_the_one_held(self, tmp_path: Path) -> None:
        gate = {"kind": "paths-filter", "filter": "backend"}
        findings, _ = self._compare(
            tmp_path,
            _committed(gate=gate, reads=["src/backend/a.py"]),
            _committed(gate=gate, reads=["src/backend/a.py", "src/backend/b.py", "src/frontend/c.ts"]),
            workflow=_STEP_FILTER_WORKFLOW,
        )
        assert len(findings) == 1 and "src/frontend/c.ts (the paths-filter)" in findings[0], findings

    def test_a_new_read_an_accepted_gap_already_accepts_is_not_drift(self, tmp_path: Path) -> None:
        gaps = [{"pattern": "renovate.json5", "reason": "r" * 50}]
        findings, _ = self._compare(
            tmp_path,
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "renovate.json5"]),
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "renovate.json5", "renovate.json5"]),
        )
        assert findings == []
        gaps = [{"pattern": "docs/**", "reason": "r" * 50}]
        findings, _ = self._compare(
            tmp_path,
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py"]),
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/new.md"]),
        )
        assert findings == []

    def test_a_gap_delegated_to_a_lane_that_did_not_read_the_new_path_is_drift(self, tmp_path: Path) -> None:
        gaps = [{"pattern": "docs/**", "reason": "r" * 50, "covered_by": "g.yml/guards"}]
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "g.yml").write_text("on: [pull_request]\njobs:\n  guards:\n    steps: []\n")
        _write(tmp_path / "committed", "g--guards.yaml", _committed(workflow="g.yml", job="guards", reads=["x"]))
        _write(tmp_path / "recorded", "g--guards.yaml", _committed(workflow="g.yml", job="guards", reads=["x"]))
        findings, _ = self._compare(
            tmp_path,
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py"]),
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/new.md"]),
        )
        assert findings == [
            "w--j.yaml: 1 new read(s) fall under an accepted gap whose covered_by lane did not read them in this "
            "run: docs/new.md (covered_by g.yml/guards)"
        ]
        _write(
            tmp_path / "recorded", "g--guards.yaml", _committed(workflow="g.yml", job="guards", reads=["docs/new.md"])
        )
        findings, _ = self._compare(
            tmp_path,
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py"]),
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/new.md"]),
        )
        assert findings == []

    def test_a_committed_read_the_run_did_not_make_is_a_note(self, tmp_path: Path) -> None:
        findings, notes = self._compare(
            tmp_path, _committed(reads=["src/backend/a.py", "renovate.json5"]), _committed(reads=["src/backend/a.py"])
        )
        assert findings == []
        assert notes == ["w--j.yaml: 1 committed read(s) not made in this run (not drift)"]

    def test_a_recording_that_read_nothing_is_a_finding(self, tmp_path: Path) -> None:
        findings, _ = self._compare(tmp_path, _committed(), _committed(reads=[]))
        assert findings == ["w--j.yaml: the CI recording read nothing at all — the instrument measured nothing"]

    def test_the_matcher_agrees_with_the_guards_over_the_committed_reads(self, guard: ModuleType) -> None:
        """A deterministic seventh of all committed reads, against every filtered manifest's filter, both matchers."""
        import dataclasses

        real = guard.sweep(guard._DOT_GITHUB, guard._MANIFEST_DIR)
        # Every 7th distinct read (deterministic; ~2k of ~15k) keeps this under a few seconds while
        # still reaching every top-level area, plus the root listing and a path no filter selects.
        every_read = sorted({read for m in real.manifests for read in m.reads})
        candidates = sorted(set(every_read[::7]) | {"./", "renovate.json5"})
        compared = disagreements = 0
        for m in real.manifests:
            wf = real.workflow(m.workflow)
            if wf is None or m.gate_kind == "unfiltered":
                continue
            theirs = set(guard.uncovered_reads(real, dataclasses.replace(m, reads=tuple(candidates))))
            ours_filter = recorder.relevance_filter(wf.document, recorder.load_manifest(m.path))
            ours = {read for read in candidates if ours_filter.rejects(read)}
            disagreements += len(ours ^ theirs)
            compared += len(candidates)
            assert ours == theirs, f"{m.path.name}: {sorted(ours ^ theirs)[:5]}"
        assert compared >= 10000 and disagreements == 0, compared


class TestACoveringLaneThatStopsReadingADelegatedPathIsDrift:
    """Review of #1747: a `covered_by` lane dropping a delegated read must not pass as a note.

    The guard's delegation rule holds the delegating manifest's gap hits against
    the covering lane's COMMITTED reads. A covering lane that stops reading one
    of them would keep the stale committed read and the guard green — the
    delegation assumed, not measured (B1 of the #1682 review).
    """

    def _tree(self, tmp_path: Path, covering_recorded: list[str]) -> tuple:
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "w.yml").write_text(_ON_PATHS_WORKFLOW)
        (tmp_path / "workflows" / "g.yml").write_text("on: [pull_request]\njobs:\n  guards:\n    steps: []\n")
        gaps = [{"pattern": "docs/**", "reason": "r" * 50, "covered_by": "g.yml/guards"}]
        delegating = _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/a.md"])
        covering = _committed(workflow="g.yml", job="guards", gate={"kind": "unfiltered"}, reads=["docs/a.md", "x"])
        for side in ("committed", "recorded"):
            _write(tmp_path / side, "w--j.yaml", delegating)
        _write(tmp_path / "committed", "g--guards.yaml", covering)
        _write(tmp_path / "recorded", "g--guards.yaml", {**covering, "reads": covering_recorded})
        return recorder.compare_manifests(
            tmp_path / "committed", tmp_path / "recorded", workflow_dir=tmp_path / "workflows"
        )

    def test_a_dropped_delegated_read_is_a_finding(self, tmp_path: Path) -> None:
        findings, _ = self._tree(tmp_path, ["x"])
        assert findings == [
            "g--guards.yaml: the CI run no longer reads 1 path(s) other lanes delegate to it through covered_by: "
            "docs/a.md (w--j.yaml)"
        ]

    def test_a_dropped_read_nobody_delegates_is_a_note(self, tmp_path: Path) -> None:
        findings, notes = self._tree(tmp_path, ["docs/a.md"])
        assert findings == []
        assert "g--guards.yaml: 1 committed read(s) not made in this run (not drift)" in notes


# ------------------------------------------------------ per-test attribution (#1749)

#: The marker directory a recording uses, and two trace files of one recording:
#: the pytest process (pid 10) setting markers, and a subprocess (pid 11) one of
#: its tests started. ``-ttt`` stamps put both on one timeline.
_MARKERS = "/tmp/lane-inputs-x/markers"


def _marker(stamp: str, name: str) -> str:
    path = f"{_MARKERS}/{name}"
    return f'{stamp} openat(AT_FDCWD, "{path}", O_WRONLY|O_CREAT|O_CLOEXEC, 0600) = 4<{path}>\n'


_A, _B = "src%2Fbackend%2Ftests%2Ftest_a.py", "src%2Fbackend%2Ftests%2Ftest_b.py"
#: A module whose only test was skipped: it was active, but no call phase executed.
_C = "src%2Fbackend%2Ftests%2Ftest_c.py"
_PYTEST_TRACE = (
    '100.000001 openat(AT_FDCWD</repo>, "src/backend/conftest.py", O_RDONLY) = 3</repo/src/backend/conftest.py>\n'
    + _marker("100.000002", f"collect~{_A}")
    + '100.000003 openat(AT_FDCWD</repo>, "docs/at-import.md", O_RDONLY) = 5</repo/docs/at-import.md>\n'
    + _marker("100.000004", "none~")
    + _marker("100.000010", f"run~{_A}")
    + '100.000011 openat(AT_FDCWD</repo>, "docs/a.md", O_RDONLY) = 5</repo/docs/a.md>\n'
    + _marker("100.000012", f"ran~{_A}")
    + '100.000013 openat(AT_FDCWD</repo>, "docs/a-teardown.md", O_RDONLY) = 5</repo/docs/a-teardown.md>\n'
    + _marker("100.000020", f"run~{_B}")
    + _marker("100.000025", f"ran~{_B}")
    + _marker("100.000026", f"run~{_C}")
    + _marker("100.000030", "none~")
    + '100.000031 openat(AT_FDCWD</repo>, "src/backend/after.py", O_RDONLY) = 5</repo/src/backend/after.py>\n'
)
_SUBPROCESS_TRACE = """\
100.000021 execve("/usr/bin/cat", ["cat", "/repo/docs/b.md"], 0x7ffe /* 85 vars */) = 0
100.000022 openat(AT_FDCWD</repo>, "/repo/docs/b.md", O_RDONLY) = 3</repo/docs/b.md>
100.000023 getdents64(3</repo/docs>, 0x5d7e /* 4 entries */, 32768) = 96
"""


class TestReadsAreAttributedToTheTestModuleThatMadeThem:
    def _trace(self, tmp_path: Path):
        pytest_file, subprocess_file = tmp_path / "trace.10", tmp_path / "trace.11"
        pytest_file.write_text(_PYTEST_TRACE)
        subprocess_file.write_text(_SUBPROCESS_TRACE)
        marker_dir = Path(_MARKERS)
        timeline = recorder.marker_timeline([pytest_file, subprocess_file], marker_dir)
        trace = recorder.Trace()
        for path in (pytest_file, subprocess_file):
            recorder._parse_trace_file(path, trace, timeline=timeline, marker_dir=marker_dir)
        return trace

    def test_a_read_belongs_to_the_module_active_when_it_happened_in_any_process(self, tmp_path: Path) -> None:
        trace = self._trace(tmp_path)
        assert trace.reader_files == {
            "src/backend/tests/test_a.py": {"/repo/docs/at-import.md", "/repo/docs/a.md", "/repo/docs/a-teardown.md"},
            "src/backend/tests/test_b.py": {"/repo/docs/b.md"},
        }, "the collection read is its module's; the subprocess's read is the test's that started it"
        assert trace.reader_listings == {"src/backend/tests/test_b.py": {"/repo/docs"}}

    def test_reads_outside_any_test_have_no_reader_and_markers_are_not_reads(self, tmp_path: Path) -> None:
        trace = self._trace(tmp_path)
        assert "/repo/src/backend/conftest.py" in trace.files
        assert "/repo/src/backend/after.py" in trace.files
        assert not any(path.startswith(_MARKERS) for path in trace.files)
        attributed = set().union(*trace.reader_files.values())
        assert "/repo/src/backend/conftest.py" not in attributed and "/repo/src/backend/after.py" not in attributed

    def test_only_modules_whose_tests_ran_are_test_modules(self, tmp_path: Path) -> None:
        trace = self._trace(tmp_path)
        assert trace.test_modules == {"src/backend/tests/test_a.py", "src/backend/tests/test_b.py"}, (
            "test_c.py was active but its test skipped — it judged nothing in this lane"
        )

    def test_a_trace_without_stamps_parses_as_before_and_attributes_nothing(self, tmp_path: Path) -> None:
        trace_file = tmp_path / "trace.1"
        trace_file.write_text(_TRACE)
        trace = recorder.Trace()
        recorder._parse_trace_file(trace_file, trace, timeline=recorder.MarkerTimeline(), marker_dir=Path(_MARKERS))
        assert "/repo/Taskfile.yaml" in trace.files and trace.reader_files == {}


class TestTheMarkerPlugin:
    """The plugin the recorder loads, run in a real pytest process with the environment the recorder gives it."""

    def test_it_marks_collection_each_test_and_the_gaps_between(self, tmp_path: Path) -> None:
        import subprocess

        root = tmp_path / "repo"
        (root / "tests").mkdir(parents=True)
        (root / "tests" / "test_one.py").write_text("def test_x():\n    pass\n")
        (root / "tests" / "test_skipped.py").write_text(
            "import pytest\n\n@pytest.mark.skip(reason='x')\ndef test_y():\n    pass\n\n"
            "def test_z():\n    pytest.skip('inside the body: still a call phase, not an executed test')\n"
        )
        markers = tmp_path / "markers"
        markers.mkdir()
        env = recorder.marker_env({"PATH": "/usr/bin:/bin"}, markers)
        env[recorder._MARKER_ROOT_ENV] = str(root)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(root / "tests")],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert {p.name for p in markers.iterdir()} == {
            "collect~tests%2Ftest_one.py",
            "run~tests%2Ftest_one.py",
            "ran~tests%2Ftest_one.py",
            "collect~tests%2Ftest_skipped.py",
            "run~tests%2Ftest_skipped.py",
            "none~",
        }, "a skipped test is active but never `ran`"

    def test_the_recorder_loads_it_into_every_pytest_and_keeps_existing_options(self) -> None:
        env = recorder.marker_env({"PYTEST_ADDOPTS": "--deselect x.py", "PYTHONPATH": "/a"}, Path("/m"))
        assert env["PYTEST_ADDOPTS"] == f"--deselect x.py -p {recorder.MARKER_PLUGIN}"
        assert env["PYTHONPATH"].split(":") == [str(recorder.MARKER_PLUGIN_DIR), "/a"]
        assert (recorder.MARKER_PLUGIN_DIR / f"{recorder.MARKER_PLUGIN}.py").is_file()

    def test_the_plugins_own_reads_are_not_the_jobs(self) -> None:
        prefix = recorder._MARKER_PLUGIN_PREFIX
        tracked = frozenset({f"{prefix}{recorder.MARKER_PLUGIN}.py", "src/backend/a.py"})
        reads = recorder.tracked_reads(
            {f"{prefix}{recorder.MARKER_PLUGIN}.py", "src/backend/a.py"},
            {prefix.rstrip("/")},
            tracked=tracked,
            directories=recorder.implied_directories(tracked),
        )
        assert reads == {"src/backend/a.py"}


class TestCompareHoldsADelegatedReadByItsReader:
    """#1749 in `compare`: a module of THIS run that makes a delegated read must run in the covering lane."""

    def _compare(self, tmp_path: Path, covering_modules: list[str]) -> list[str]:
        (tmp_path / "workflows").mkdir(exist_ok=True)
        (tmp_path / "workflows" / "w.yml").write_text(_ON_PATHS_WORKFLOW)
        (tmp_path / "workflows" / "g.yml").write_text("on: [pull_request]\njobs:\n  guards:\n    steps: []\n")
        gaps = [{"pattern": "docs/**", "reason": "r" * 50, "covered_by": "g.yml/guards"}]
        old, new = "src/backend/tests/guards/test_old.py", "src/backend/tests/test_new.py"
        delegating = _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/a.md"])
        recorded = {**delegating, "test_modules": [old, new], "readers": {old: ["docs/a.md"], new: ["docs/a.md"]}}
        covering = _committed(
            workflow="g.yml", job="guards", gate={"kind": "unfiltered"}, reads=["docs/a.md"], test_modules=[old]
        )
        _write(tmp_path / "committed", "w--j.yaml", delegating)
        _write(tmp_path / "recorded", "w--j.yaml", recorded)
        _write(tmp_path / "committed", "g--guards.yaml", covering)
        _write(tmp_path / "recorded", "g--guards.yaml", {**covering, "test_modules": covering_modules})
        findings, _ = recorder.compare_manifests(
            tmp_path / "committed", tmp_path / "recorded", workflow_dir=tmp_path / "workflows"
        )
        return findings

    def test_a_new_reader_outside_the_covering_lane_is_a_finding_though_the_path_is_read_there(
        self, tmp_path: Path
    ) -> None:
        (finding,) = self._compare(tmp_path, ["src/backend/tests/guards/test_old.py"])
        assert finding.startswith(
            "w--j.yaml: test module src/backend/tests/test_new.py makes 1 delegated read(s) but the covering lane "
            "does not run it"
        )
        assert finding.endswith("docs/a.md (covered_by g.yml/guards)")

    def test_the_reader_running_in_the_covering_lane_clears_it(self, tmp_path: Path) -> None:
        both = ["src/backend/tests/guards/test_old.py", "src/backend/tests/test_new.py"]
        assert self._compare(tmp_path, both) == []


class TestEveryMatchingGapIsHeldNotTheFirst:
    """#1683 review of #1747: `read_drift`/`delegated_reads` took the first matching gap; the guard takes each."""

    def _tree(self, tmp_path: Path, *, a_reads: list[str], b_reads: list[str]) -> tuple:
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "w.yml").write_text(_ON_PATHS_WORKFLOW)
        for lane in ("a", "b"):
            (tmp_path / "workflows" / f"{lane}.yml").write_text("on: [pull_request]\njobs:\n  guards:\n    steps: []\n")
        gaps = [
            {"pattern": "docs/**", "reason": "r" * 50, "covered_by": "a.yml/guards"},
            {"pattern": "docs/x/**", "reason": "r" * 50, "covered_by": "b.yml/guards"},
        ]
        _write(tmp_path / "committed", "w--j.yaml", _committed(accepted_gaps=gaps, reads=["src/backend/a.py"]))
        _write(
            tmp_path / "recorded",
            "w--j.yaml",
            _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/x/new.md"]),
        )
        for lane, reads in (("a", a_reads), ("b", b_reads)):
            covering = _committed(workflow=f"{lane}.yml", job="guards", gate={"kind": "unfiltered"}, reads=reads)
            _write(tmp_path / "committed", f"{lane}--guards.yaml", covering)
            _write(tmp_path / "recorded", f"{lane}--guards.yaml", covering)
        return recorder.compare_manifests(
            tmp_path / "committed", tmp_path / "recorded", workflow_dir=tmp_path / "workflows"
        )

    def test_the_second_gaps_lane_must_read_it_too(self, tmp_path: Path) -> None:
        findings, _ = self._tree(tmp_path, a_reads=["docs/x/new.md"], b_reads=["y"])
        assert findings == [
            "w--j.yaml: 1 new read(s) fall under an accepted gap whose covered_by lane did not read them in this "
            "run: docs/x/new.md (covered_by b.yml/guards)"
        ]

    def test_both_lanes_reading_it_is_green(self, tmp_path: Path) -> None:
        findings, _ = self._tree(tmp_path, a_reads=["docs/x/new.md"], b_reads=["docs/x/new.md"])
        assert findings == []

    def test_each_lane_owes_the_committed_read(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as scratch:
            workflows = Path(scratch)
            (workflows / "w.yml").write_text(_ON_PATHS_WORKFLOW)
            gaps = [
                {"pattern": "docs/**", "reason": "r" * 50, "covered_by": "a.yml/guards"},
                {"pattern": "docs/x/**", "reason": "r" * 50, "covered_by": "b.yml/guards"},
            ]
            owed = recorder.delegated_reads(
                {"w--j.yaml": _committed(accepted_gaps=gaps, reads=["docs/x/new.md"])}, workflow_dir=workflows
            )
        assert owed == {
            ("a.yml", "guards"): {"docs/x/new.md": "w--j.yaml"},
            ("b.yml", "guards"): {"docs/x/new.md": "w--j.yaml"},
        }


class TestTheMergeWritesTheAttribution:
    def test_test_modules_and_readers_are_written_even_when_empty_and_merged_on_append(self) -> None:
        manifest = {"invocations": [], "reads": [], "subprocesses": []}
        recorder._merge_into(manifest, invocation={"command": "task lint"}, reads={"a"}, execs=[])
        assert manifest["test_modules"] == [] and manifest["readers"] == {}
        recorder._merge_into(
            manifest,
            invocation={"command": "pytest"},
            reads={"b"},
            execs=[],
            test_modules={"t/test_b.py"},
            readers={"t/test_b.py": {"docs/b.md"}},
        )
        recorder._merge_into(
            manifest,
            invocation={"command": "pytest"},
            reads={"c"},
            execs=[],
            test_modules={"t/test_c.py"},
            readers={"t/test_b.py": {"docs/a.md"}},
        )
        assert manifest["test_modules"] == ["t/test_b.py", "t/test_c.py"]
        assert manifest["readers"] == {"t/test_b.py": ["docs/a.md", "docs/b.md"]}

    def test_a_replay_starts_from_no_attribution(self) -> None:
        base = recorder._replay_base(_committed(test_modules=["x"], readers={"x": ["y"]}))
        assert base["test_modules"] == [] and base["readers"] == {}


def test_a_read_two_overlapping_gaps_delegate_is_named_once(tmp_path: Path) -> None:
    """Measured on the first CI recording (run 36094119498): `src/**` and `src/frontend/**` listed each read twice."""
    (tmp_path / "w.yml").write_text(_ON_PATHS_WORKFLOW)
    gaps = [
        {"pattern": "docs/**", "reason": "r" * 50, "covered_by": "g.yml/guards"},
        {"pattern": "docs/x/**", "reason": "r" * 50, "covered_by": "g.yml/guards"},
    ]
    (finding,) = recorder.stray_readers(
        "w--j.yaml",
        _committed(accepted_gaps=gaps),
        {"readers": {"t/test_new.py": ["docs/x/a.md"]}},
        modules_of={("g.yml", "guards"): set()},
        workflow_dir=tmp_path,
    )
    assert "makes 1 delegated read(s)" in finding and finding.endswith("docs/x/a.md (covered_by g.yml/guards)")


class TestTheReadersScopeIsTheSameFunctionInBothFiles:
    """Review of #1749: the guard recomputes the recorder's scope fingerprint; both must hash the same set."""

    def test_the_fingerprint_over_the_same_outside_set_agrees(self, guard: ModuleType) -> None:
        reads = ["src/backend/a.py", "docs/b.md", "renovate.json5", "docs/"]
        rejects = lambda read: not read.startswith("src/backend/")  # noqa: E731
        assert recorder.readers_scope_sha256(reads, rejects) == guard._readers_scope_sha256(
            ["docs/b.md", "renovate.json5", "docs/"]
        )

    def test_the_committed_delegating_manifest_matches_its_live_filter(self, guard: ModuleType) -> None:
        real = guard.sweep(guard._DOT_GITHUB, guard._MANIFEST_DIR)
        delegating = [m for m in real.manifests if any(g.get("covered_by") for g in m.accepted_gaps)]
        assert delegating, "backend--lint-test delegates to the guards lane"
        for m in delegating:
            assert m.readers_scope_sha256 == guard._readers_scope_sha256(list(guard.uncovered_reads(real, m))), (
                m.path.name
            )


def test_a_read_two_overlapping_gaps_leave_undelegated_is_counted_once(tmp_path: Path) -> None:
    """Review of #1749: `src/**` and `src/frontend/**` both delegate to the guards lane; one read, one entry."""
    (tmp_path / "w.yml").write_text(_ON_PATHS_WORKFLOW)
    gaps = [
        {"pattern": "docs/**", "reason": "r" * 50, "covered_by": "g.yml/guards"},
        {"pattern": "docs/x/**", "reason": "r" * 50, "covered_by": "g.yml/guards"},
    ]
    findings, _ = recorder.read_drift(
        "w--j.yaml",
        _committed(accepted_gaps=gaps, reads=["src/backend/a.py"]),
        _committed(accepted_gaps=gaps, reads=["src/backend/a.py", "docs/x/new.md"]),
        reads_of={("g.yml", "guards"): set()},
        workflow_dir=tmp_path,
    )
    assert findings == [
        "w--j.yaml: 1 new read(s) fall under an accepted gap whose covered_by lane did not read them in this "
        "run: docs/x/new.md (covered_by g.yml/guards)"
    ]
