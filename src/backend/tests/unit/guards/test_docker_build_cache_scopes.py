"""#2409 — every pre-merge image build owns its BuildKit cache scope, shared only with the same build.

**The defect this is written against, measured 2026-10-31.** Six ``build-*`` jobs
of ``.github/workflows/docker-lint-build.yml`` declared ``cache-from: type=gha``
without ``scope=``. The gha cache backend then writes every one of them to the
default scope ``buildkit``, so each job's export replaces the cache index the
previous one wrote: the ``index-buildkit-*`` entries of one pull-request ref
alternated between four different index sizes — four images taking turns over
one index, the race ``build-embedding-service`` already documents for its legs
(#1764). Nothing went red; builds were merely slower than their cache allowed.
That is why it needs a guard: a cache that silently stops hitting has no other
symptom.

**The second property: the same build shares one scope across workflows.** The
backend and frontend images are built twice per pull request — here, and by the
e2e stack (``docker-compose.e2e.yml`` + the CI overlay
``docker-compose.e2e.ci.yml``) — from the identical definition: same context,
same Dockerfile, no build args, no target. The e2e workflows also write their
scope on ``develop``, which a pull request may read, while this workflow runs on
pull requests only, so a scope it used alone was never readable by the next pull
request. Aligning the two scopes is the reuse; this file keeps it from decaying
when either side renames its scope.

**What it does NOT claim.** A shared scope makes a cache hit possible, not
certain — whether BuildKit reuses a layer is decided by the layer's inputs at
build time, which a static check cannot observe. The guard holds the
configuration that the reuse depends on, nothing more.

Each rule is a pure function over parsed documents, and each is shown to fire on
a planted document below, so a green run over the live files is not a run that
could not have failed.

Traces to #2409 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "docker-lint-build.yml"
_COMPOSE = _REPO_ROOT / "docker-compose.e2e.yml"
_COMPOSE_CI = _REPO_ROOT / "docker-compose.e2e.ci.yml"

#: The build action, matched WITHOUT its digest — the pin is Renovate's to move.
_BUILD_ACTION = "docker/build-push-action@"

#: ``scope=<value>`` inside a cache spec such as ``type=gha,mode=max,scope=x``.
_SCOPE = re.compile(r"(?:^|,)\s*scope=(?P<scope>[^,\s]+)")

#: The builds that MUST be found on both sides. Without this the alignment rule
#: would pass vacuously the day a context is respelled on one side and the
#: matcher pairs nothing.
_EXPECTED_SHARED_CONTEXTS = frozenset({"src/backend", "src/frontend"})


def _load(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    return document if isinstance(document, dict) else {}


def _normalise_context(context: str) -> str:
    """``./src/backend/`` and ``src/backend`` are the same build context."""
    value = context.strip()
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/") or "."


def _scope_of(spec: Any) -> str | None:
    """The ``scope=`` of one gha cache spec, ``None`` when it names none."""
    if not isinstance(spec, str):
        return None
    match = _SCOPE.search(spec)
    return match.group("scope") if match else None


def _is_gha(spec: Any) -> bool:
    return isinstance(spec, str) and "type=gha" in spec


def workflow_builds(document: dict[str, Any]) -> list[dict[str, Any]]:
    """One record per build-push-action step: job, build definition and cache specs."""
    builds: list[dict[str, Any]] = []
    raw_jobs = document.get("jobs")
    jobs: dict[str, Any] = raw_jobs if isinstance(raw_jobs, dict) else {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not isinstance(uses, str) or not uses.startswith(_BUILD_ACTION):
                continue
            raw_with = step.get("with")
            with_: dict[str, Any] = raw_with if isinstance(raw_with, dict) else {}
            context = _normalise_context(str(with_.get("context", ".")))
            builds.append(
                {
                    "job": str(job_id),
                    "context": context,
                    "file": str(with_.get("file") or f"{context}/Dockerfile").strip(),
                    "target": with_.get("target"),
                    "build_args": with_.get("build-args"),
                    "cache_from": with_.get("cache-from"),
                    "cache_to": with_.get("cache-to"),
                }
            )
    return builds


def unscoped_cache_findings(builds: list[dict[str, Any]]) -> dict[str, str]:
    """``job -> why its gha cache does not own a scope``; empty when every build names one."""
    findings: dict[str, str] = {}
    for build in builds:
        cache_from, cache_to = build["cache_from"], build["cache_to"]
        if not (_is_gha(cache_from) or _is_gha(cache_to)):
            continue
        scope_from, scope_to = _scope_of(cache_from), _scope_of(cache_to)
        if scope_from is None or scope_to is None:
            findings[build["job"]] = (
                f"cache-from {cache_from!r} / cache-to {cache_to!r} name no `scope=`, so the build "
                "writes the shared default scope `buildkit` and overwrites the cache index of every "
                "other unscoped build"
            )
        elif scope_from != scope_to:
            findings[build["job"]] = (
                f"reads scope {scope_from!r} but writes {scope_to!r} — the next run never finds what this one exported"
            )
    return findings


def _definition(build: dict[str, Any]) -> tuple[str, str, str, str]:
    return (build["context"], build["file"], str(build["target"]), str(build["build_args"]))


def shared_scope_findings(builds: list[dict[str, Any]]) -> dict[str, str]:
    """``scope -> the different builds that share it``; empty when a scope belongs to one build definition."""
    owners: dict[str, dict[tuple[str, str, str, str], list[str]]] = {}
    for build in builds:
        scope = _scope_of(build["cache_to"])
        if scope is None:
            continue
        owners.setdefault(scope, {}).setdefault(_definition(build), []).append(build["job"])
    return {
        scope: "shared by different builds: " + "; ".join(f"{jobs} {definition}" for definition, jobs in by_def.items())
        for scope, by_def in owners.items()
        if len(by_def) > 1
    }


def compose_builds(compose: dict[str, Any], overlay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """``service -> {context, file, target, build_args, scope}`` for every built service.

    The overlay is merged the way compose merges it: the base file decides WHAT is
    built, the overlay adds the cache. A service the overlay leaves uncached has
    scope ``None``.
    """
    raw_services = compose.get("services")
    services: dict[str, Any] = raw_services if isinstance(raw_services, dict) else {}
    raw_overlay = overlay.get("services")
    overlay_services: dict[str, Any] = raw_overlay if isinstance(raw_overlay, dict) else {}
    found: dict[str, dict[str, Any]] = {}
    for name, service in services.items():
        if not isinstance(service, dict):
            continue
        build = service.get("build")
        if isinstance(build, str):
            build = {"context": build}
        if not isinstance(build, dict):
            continue
        context = _normalise_context(str(build.get("context", ".")))
        dockerfile = str(build.get("dockerfile") or "Dockerfile")
        overlay_build = (overlay_services.get(name) or {}).get("build") or {}
        cache_to = overlay_build.get("cache_to") if isinstance(overlay_build, dict) else None
        spec = cache_to[0] if isinstance(cache_to, list) and cache_to else cache_to
        found[str(name)] = {
            "context": context,
            "file": f"{context}/{dockerfile}",
            "target": build.get("target"),
            "build_args": build.get("args"),
            "scope": _scope_of(spec),
        }
    return found


def alignment_findings(
    builds: list[dict[str, Any]], compose: dict[str, dict[str, Any]]
) -> tuple[dict[str, str], set[str]]:
    """``(job -> why its scope differs from the e2e scope of the same build, contexts paired)``.

    Two builds are "the same" only when context, Dockerfile, target AND build args
    all agree — a build that differs in any of them produces other layers, and
    sharing a scope with it would be the overwrite race again, across workflows.
    """
    findings: dict[str, str] = {}
    paired: set[str] = set()
    for build in builds:
        scope = _scope_of(build["cache_to"])
        twins = {
            service: spec
            for service, spec in compose.items()
            if (spec["context"], spec["file"], str(spec["target"]), str(spec["build_args"])) == _definition(build)
        }
        if not twins:
            continue
        paired.add(build["context"])
        e2e_scopes = {spec["scope"] for spec in twins.values()}
        if e2e_scopes != {scope}:
            findings[build["job"]] = (
                f"builds the same image as e2e services {sorted(twins)} but uses scope {scope!r} where they use "
                f"{sorted(map(str, e2e_scopes))} — the pull request cannot reuse the cache develop's e2e runs wrote"
            )
    return findings, paired


# --------------------------------------------------------------------- live files


@pytest.fixture(scope="module")
def live_builds() -> list[dict[str, Any]]:
    return workflow_builds(_load(_WORKFLOW))


@pytest.fixture(scope="module")
def live_compose() -> dict[str, dict[str, Any]]:
    return compose_builds(_load(_COMPOSE), _load(_COMPOSE_CI))


def test_the_sweep_finds_every_build_of_the_workflow(live_builds: list[dict[str, Any]]) -> None:
    # Measuring-tool check: the workflow builds eight images; a matcher that found
    # fewer would certify a shrunken population.
    assert len({build["job"] for build in live_builds}) == 8, sorted(build["job"] for build in live_builds)


def test_every_pre_merge_build_owns_a_cache_scope(live_builds: list[dict[str, Any]]) -> None:
    assert unscoped_cache_findings(live_builds) == {}


def test_no_scope_is_shared_by_different_builds(live_builds: list[dict[str, Any]]) -> None:
    assert shared_scope_findings(live_builds) == {}


def test_builds_shared_with_the_e2e_stack_share_its_scope(
    live_builds: list[dict[str, Any]], live_compose: dict[str, dict[str, Any]]
) -> None:
    findings, paired = alignment_findings(live_builds, live_compose)
    assert findings == {}
    assert paired >= _EXPECTED_SHARED_CONTEXTS, (
        f"only {sorted(paired)} were paired with an e2e service; the rule above passed over the others "
        "without comparing anything"
    )


# ------------------------------------------------------------- planted documents


def _planted_workflow(*steps: tuple[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "jobs": {
            job: {"steps": [{"uses": "docker/build-push-action@0000000000000000000000000000000000000000", "with": w}]}
            for job, w in steps
        }
    }


def test_the_default_scope_is_a_finding() -> None:
    builds = workflow_builds(
        _planted_workflow(
            ("build-a", {"context": "a", "cache-from": "type=gha", "cache-to": "type=gha,mode=max"}),
        )
    )
    assert set(unscoped_cache_findings(builds)) == {"build-a"}


def test_a_scope_read_but_not_written_is_a_finding() -> None:
    builds = workflow_builds(
        _planted_workflow(
            ("build-a", {"context": "a", "cache-from": "type=gha,scope=a", "cache-to": "type=gha,mode=max,scope=b"}),
        )
    )
    assert set(unscoped_cache_findings(builds)) == {"build-a"}


def test_two_different_builds_on_one_scope_are_a_finding() -> None:
    builds = workflow_builds(
        _planted_workflow(
            ("build-a", {"context": "a", "cache-from": "type=gha,scope=x", "cache-to": "type=gha,mode=max,scope=x"}),
            ("build-b", {"context": "b", "cache-from": "type=gha,scope=x", "cache-to": "type=gha,mode=max,scope=x"}),
        )
    )
    assert set(shared_scope_findings(builds)) == {"x"}


def test_a_scope_that_drifts_from_the_e2e_twin_is_a_finding() -> None:
    builds = workflow_builds(
        _planted_workflow(
            (
                "build-backend",
                {
                    "context": "src/backend",
                    "file": "src/backend/Dockerfile",
                    "cache-from": "type=gha,scope=backend",
                    "cache-to": "type=gha,mode=max,scope=backend",
                },
            ),
        )
    )
    compose = compose_builds(
        {"services": {"backend": {"build": {"context": "./src/backend"}}}},
        {"services": {"backend": {"build": {"cache_to": ["type=gha,scope=e2e-backend,mode=max"]}}}},
    )
    findings, paired = alignment_findings(builds, compose)
    assert set(findings) == {"build-backend"}
    assert paired == {"src/backend"}


def test_a_build_with_other_args_is_not_the_e2e_twin() -> None:
    # docker-publish.yml passes BUILD_REVISION; such a build is another build and
    # must not be paired (nor be required to share) the e2e scope.
    builds = workflow_builds(
        _planted_workflow(
            (
                "build-backend",
                {
                    "context": "src/backend",
                    "build-args": "BUILD_REVISION=abc",
                    "cache-from": "type=gha,scope=backend",
                    "cache-to": "type=gha,mode=max,scope=backend",
                },
            ),
        )
    )
    compose = compose_builds(
        {"services": {"backend": {"build": {"context": "./src/backend"}}}},
        {"services": {"backend": {"build": {"cache_to": ["type=gha,scope=e2e-backend,mode=max"]}}}},
    )
    assert alignment_findings(builds, compose) == ({}, set())
