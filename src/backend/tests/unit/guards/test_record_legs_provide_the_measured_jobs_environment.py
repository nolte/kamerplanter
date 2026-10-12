"""#1683 — every record leg of ``lane-inputs.yml`` runs with the services and the env of the job it measures.

**The defect this is written against, measured 2026-10-12.** The weekly
``Lane inputs`` runs 37298982533 (2026-10-05) and 38241685935 (2026-10-12) lost
the ``Record backend-guards--integration`` leg. The leg replays ``task
test:backend:integration``, the command of ``backend-guards.yml``'s
``integration`` job. That job had gained a ``timescaledb`` service and four
``TIMESCALEDB_*`` variables in #1943 (2026-10-02); the leg had neither. It
started ArangoDB from its own copy of the digest, behind a flag derived from the
manifest's recorded ``ARANGODB_*``, and handed the replay exactly the env an
older recording had written down. 37 Timescale tests ERRORed
(``test_legacy_ha_readings_cleanup.py``, ``test_privacy_export_garden_readings_timescale.py``,
``test_sensor_ingest_after_erase.py``, ``test_timescale_aggregate_erasure.py``),
so the recording could only end red — before it got that far, the replay step's
bound (3 x the 474 s of the last recording) cut it off at 99 %.

**The property.** For EVERY leg ``plan`` emits — not only the integration leg:

* every ``services:`` entry of the measured job is started for the leg, with the
  job's image (digest included), every ``env`` pair, every port and the
  ``options`` — read through the step the record job really runs
  (``lane_inputs.py services "$LANE"``), which must exist, be unconditional and
  come before the replay;
* every ``env:`` variable the measured job declares for an invocation — the
  workflow's, the job's, and the step's that runs the command — reaches that
  invocation's replay with the job's value. A variable whose value is a
  ``${{ }}`` expression cannot be resolved off the runner: the manifest's
  stand-in satisfies it (``REF=refs/heads/develop``), otherwise it must be in
  :data:`_RUN_TIME_VALUES_NOT_REPRODUCED` with a reason. An entry there that no
  leg needs any more is a finding too.

**How it reaches the rule.** The expectation is read from the workflow YAML
here, independently of the recorder; what the leg GETS is read the way
production gets it — ``plan_matrix`` for the legs, the record job's own steps,
``service_containers`` for what ``services`` starts, ``replay_plan`` for the
argv ``replay`` runs. The step that runs an invocation is matched by the
invocation's command appearing as a line of the step's ``run:`` in the same
working directory, which is a different matcher from the recorder's on purpose.

WHAT THIS GUARD DOES NOT SEE:

* a container a leg would need that the measured job does not declare as a
  service (one started by a ``docker compose`` inside the replayed command is
  the command's own business, and is replayed with it);
* a job-level ``container:`` (no measured job uses one; it would not be a
  service and is not swept);
* whether a service is HEALTHY when the replay starts — that is
  ``start_services``' own wait, exercised in CI only;
* env the runner itself provides (``CI``, ``GITHUB_*``): the record job runs on
  the same runner image, so they are present without being declared.

Advisory like every lane-inputs rule (``pytestmark``): the required guards lane
deselects it with ``-m 'not advisory'``; promotion is #1683's decision on
measured history (NFR-018 §4). Traces to #1683 (no TC-ID: CI configuration is
not a user-facing case).
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root, load_repo_script

#: Deselected by the required lane (`-m 'not advisory'` in backend-guards.yml); promotion is #1683's.
pytestmark = pytest.mark.advisory

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found; this guard reads .github/ and cannot run without it")

_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"
_LANE_WORKFLOW = _WORKFLOWS / "lane-inputs.yml"
_SERVICES_CALL = "scripts/ci/lane_inputs.py services"
_REPLAY_CALL = "scripts/ci/lane_inputs.py replay"
_EXPRESSION = "${{"

recorder = load_repo_script("ci/lane_inputs")

#: ``(workflow, variable)`` → why a measured job's run-time ``${{ }}`` value is
#: not reproduced for its legs and the manifest carries no stand-in. Every entry
#: must still be needed by some leg; one that is not is a finding.
_RUN_TIME_VALUES_NOT_REPRODUCED: dict[tuple[str, str], str] = {
    ("frontend.yml", "RUN_FRONTEND"): (
        "decides the `if:` of the job's steps from `needs.changes`; the recorded "
        "invocations are the steps that ran, and none of them reads the variable"
    ),
    ("docker-publish.yml", "IMAGE_PREFIX"): (
        "workflow-level `ghcr.io/${{ github.repository_owner }}`, consumed by the "
        "image tags and the `helm push` step, which no recorded invocation runs"
    ),
}


def _load(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    assert isinstance(document, dict), f"{path} did not parse to a mapping"
    return document


def _record_steps() -> list[dict[str, Any]]:
    steps = _load(_LANE_WORKFLOW)["jobs"]["record"]["steps"]
    return [step for step in steps if isinstance(step, dict)]


def _legs() -> list[dict[str, Any]]:
    legs = recorder.plan_matrix()
    # Vacuity: the plan of this tree has ~40 legs; a plan that emitted none
    # would make every assertion below hold.
    assert len(legs) >= 30, f"plan_matrix emitted only {len(legs)} leg(s)"
    return legs


def _measured_job(leg: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    workflow, job_id = recorder.lane_job(leg["lane"])
    document = _load(_WORKFLOWS / workflow)
    job = (document.get("jobs") or {}).get(job_id)
    assert isinstance(job, dict), f"{leg['name']}: {workflow} defines no job {job_id!r}"
    return workflow, document, job


def _mapping(value: Any) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()} if isinstance(value, dict) else {}


def _step_cwd(document: dict[str, Any], job: dict[str, Any], step: dict[str, Any]) -> str:
    for scope in (step, (job.get("defaults") or {}).get("run"), (document.get("defaults") or {}).get("run")):
        if isinstance(scope, dict) and isinstance(scope.get("working-directory"), str):
            return str(scope["working-directory"])
    return "."


def _declared_env(document: dict[str, Any], job: dict[str, Any], invocation: dict[str, Any]) -> dict[str, str]:
    """What the job declares for *invocation*: workflow env, job env, then the env of the step that runs it."""
    env = {**_mapping(document.get("env")), **_mapping(job.get("env"))}
    command = recorder.normalise_scratch(str(invocation.get("command", "")))
    cwd = str(invocation.get("cwd") or ".")
    for step in job.get("steps") or []:
        if not isinstance(step, dict) or not isinstance(step.get("run"), str):
            continue
        if _step_cwd(document, job, step) != cwd:
            continue
        lines = {recorder.normalise_scratch(line.strip()) for line in step["run"].splitlines()}
        if command in lines:
            env.update(_mapping(step.get("env")))
            break
    return env


def _passed_env(argv: list[str]) -> dict[str, str]:
    head = argv[: argv.index("--")] if "--" in argv else argv
    env: dict[str, str] = {}
    for index, token in enumerate(head):
        if token == "--env":
            key, _, value = head[index + 1].partition("=")
            env[key] = value
    return env


class TestTheRecordJobStartsTheMeasuredJobsServices:
    def test_one_unconditional_services_step_runs_before_the_replay_for_the_legs_own_lane(self) -> None:
        steps = _record_steps()
        services = [i for i, step in enumerate(steps) if _SERVICES_CALL in str(step.get("run", ""))]
        replay = [i for i, step in enumerate(steps) if _REPLAY_CALL in str(step.get("run", ""))]
        assert len(replay) == 1, f"the record job must run `{_REPLAY_CALL}` exactly once"
        assert len(services) == 1, (
            f'the record job must start the measured job\'s services with `{_SERVICES_CALL} "$LANE"` — '
            f"a leg without them replays the job against servers it does not have (#1683)"
        )
        step = steps[services[0]]
        assert services[0] < replay[0], "the services must be up before the replay starts"
        assert "if" not in step, "the services step must run for every leg; `services` itself is a no-op without any"
        assert (step.get("env") or {}).get("LANE") == "${{ matrix.lane }}", "the step must start the LEG's job"
        assert '"$LANE"' in step["run"], "the step must pass the leg's lane to `services`"

    def test_no_step_keeps_its_own_server(self) -> None:
        """A `docker run` of its own is the shape #1683 removed: a second list of servers that the job outgrew."""
        own = [step.get("name") for step in _record_steps() if "docker run" in str(step.get("run", ""))]
        assert not own, f"record-job step(s) {own} start a container themselves; declare it as the job's service"

    def test_every_leg_gets_every_service_its_job_declares(self) -> None:
        findings: list[str] = []
        legs_with_services = 0
        for leg in _legs():
            workflow, _document, job = _measured_job(leg)
            declared = job.get("services") or {}
            if not declared:
                continue
            legs_with_services += 1
            started = {
                service.name: service for service in recorder.service_containers(*recorder.lane_job(leg["lane"]))
            }
            for name, spec in declared.items():
                where = f"{leg['name']}: {workflow} service {name!r}"
                service = started.get(str(name))
                if service is None:
                    findings.append(f"{where} is not started for the leg")
                    continue
                argv = service.run_argv()
                if argv[-1] != spec.get("image"):
                    findings.append(f"{where} starts {argv[-1]!r}, the job runs {spec.get('image')!r}")
                for key, value in _mapping(spec.get("env")).items():
                    if f"{key}={value}" not in argv:
                        findings.append(f"{where} lacks env {key}")
                for port in spec.get("ports") or []:
                    if str(port) not in argv:
                        findings.append(f"{where} does not publish {port}")
                options = shlex.split(str(spec.get("options") or ""))
                if options and argv[-1 - len(options) : -1] != options:
                    findings.append(f"{where} does not pass the job's `options` (health check)")
        assert legs_with_services >= 1, "no leg measures a job with services — the sweep checked nothing"
        assert not findings, "A record leg must run with the services of the job it measures (#1683):\n" + "\n".join(
            f"    {finding}" for finding in findings
        )


class TestEveryInvocationIsReplayedWithTheJobsEnv:
    def test_every_declared_variable_reaches_the_replay(self, tmp_path: Path) -> None:
        findings: list[str] = []
        needed: set[tuple[str, str]] = set()
        checked = 0
        for leg in _legs():
            workflow, document, job = _measured_job(leg)
            plan = recorder.replay_plan(leg["lane"], tmp_path)
            for index, (invocation, argv) in enumerate(zip(plan.invocations, plan.argvs, strict=True)):
                if argv[0] != "record":
                    continue  # a docker-derived invocation runs no process, so it has no env
                passed = _passed_env(argv)
                for key, value in _declared_env(document, job, invocation).items():
                    checked += 1
                    where = f"{leg['name']} invocations[{index}] ({invocation.get('command')!r}): {key}"
                    if _EXPRESSION not in value:
                        if passed.get(key) != value:
                            findings.append(f"{where} — the job sets {value!r}, the replay passes {passed.get(key)!r}")
                    elif key not in passed:
                        needed.add((workflow, key))
                        if (workflow, key) not in _RUN_TIME_VALUES_NOT_REPRODUCED:
                            findings.append(
                                f"{where} — a run-time value with no stand-in in the manifest and no entry in "
                                f"_RUN_TIME_VALUES_NOT_REPRODUCED"
                            )
        assert checked >= 10, f"only {checked} declared variable(s) checked — the sweep is not reaching the jobs"
        stale = sorted(set(_RUN_TIME_VALUES_NOT_REPRODUCED) - needed)
        findings += [
            f"{workflow}: {key} is registered as not reproduced, but no leg needs it" for workflow, key in stale
        ]
        assert not findings, "A record leg must replay with the env of the job it measures (#1683):\n" + "\n".join(
            f"    {finding}" for finding in findings
        )

    def test_the_registered_reasons_are_reasons(self) -> None:
        short = [key for key, reason in _RUN_TIME_VALUES_NOT_REPRODUCED.items() if len(reason) < 40]
        assert not short, f"a reason shorter than 40 characters is a label: {short}"
