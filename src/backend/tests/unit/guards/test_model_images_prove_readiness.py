"""#1609 — an image that ships a model must prove at build time that it serves it.

**The defect this is written against, measured 2026-09-20.**
``docker/reranker-service`` built green and could never become ready. Its ONNX
export stage wrote ``config.json``, ``model.onnx`` and ``model.onnx_data`` and
no tokenizer at all, so ``AutoTokenizer.from_pretrained()`` raised at startup —
in a *daemon thread*, so the process stayed up. ``/health`` kept answering 200,
the image's ``HEALTHCHECK`` opened a TCP socket on the uvicorn port and passed,
and ``/ready`` was a permanent 503. Nobody noticed, because the only pre-merge
lane that touches this image (``docker-lint-build.yml``) builds it and stops:
**a build is not a start.**

**The class, not the site.** The tokenizer was one way to ship an unusable
model. Any image that exports or downloads a model in a build stage and copies
it into the runtime can ship one that cannot be loaded — a truncated download, a
changed layout upstream, an exporter that silently drops a file. Three images in
this checkout have that shape (``docker/reranker-service``,
``docker/embedding-service``, ``src/inference-service``), and this file finds
them STRUCTURALLY — a Dockerfile that ``COPY --from=<stage>``s a ``/model``
directory — rather than by a list, so a fourth is covered the day it is written.

**The property.** For each member:

1. ``docker-lint-build.yml`` builds it with ``load: true`` — without that the
   built image never enters the daemon and nothing downstream can start it;
2. the same job then runs ``scripts/ci/smoke_model_image.sh``, which starts the
   container and fails unless its readiness signal arrives;
3. the image's own ``HEALTHCHECK`` asserts the SAME readiness surface the smoke
   step asserts — same path, and, where the smoke step requires a body fact, the
   ``HEALTHCHECK`` names that fact too. A ``HEALTHCHECK`` that only opens a
   socket is the #1609 lie itself and is a finding here;
4. the readiness path is actually served by the image's own source, so a path
   can never be named in two places and exist in neither.

**Not satisfiable by a comment.** Every assertion reads a parsed YAML step, a
Dockerfile instruction, or a route literal in the service source; shell comment
lines are stripped out of ``run:`` blocks before they are searched, and a
``#``-prefixed line in a Dockerfile is never an instruction. The vacuum trap
that was repaired four times in this repository in the days before this file was
written (most recently PR #1545, where a comment header satisfied the guard's
own positive test) has no purchase on a structural read.

Traces to #1609 (no TC-ID: CI and image configuration are not user-facing cases).
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "docker-lint-build.yml"
_SMOKE_SCRIPT = Path("scripts/ci/smoke_model_image.sh")

#: ``COPY --from=<stage> [flags] /model[/...] <dest>`` — the signature of "this
#: runtime stage ships a model produced by an earlier stage". Anchored on the
#: SOURCE path rather than on the destination, because the destination is a
#: per-image convention (``/app/models/onnx/...`` here, ``/app/models/dinov2``
#: there) and the source is the pattern all three already share. A registry
#: reference (``COPY --from=ghcr.io/...``) never matches: the source path must
#: begin with ``/model``.
_MODEL_COPY = re.compile(r"^\s*COPY\s+--from=(?P<stage>[\w.-]+)\s+(?:--[\w-]+=\S+\s+)*/model\b", re.MULTILINE)

#: ``HEALTHCHECK [flags] CMD <command>`` — continuation lines joined first.
_HEALTHCHECK = re.compile(r"^\s*HEALTHCHECK\b(?P<body>.*)$", re.MULTILINE | re.IGNORECASE)

#: ``EXPOSE <port>``.
_EXPOSE = re.compile(r"^\s*EXPOSE\s+(?P<port>\d+)", re.MULTILINE | re.IGNORECASE)

#: The socket-connect probe every one of these images shipped before #1609. It
#: passes the instant uvicorn binds and says nothing about the model.
_SOCKET_ONLY = "connect_ex"

_BUILD_ACTION = "docker/build-push-action@"


# --------------------------------------------------------------------------
# reading the repository
# --------------------------------------------------------------------------


def _join_continuations(text: str) -> str:
    """Fold ``\\``-continued Dockerfile lines into single logical lines."""
    return re.sub(r"\\\s*\n\s*", " ", text)


def _strip_dockerfile_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _strip_shell_comments(run: str) -> str:
    """Drop whole-line shell comments from a ``run:`` block.

    Without this a step could satisfy every assertion below with
    ``# scripts/ci/smoke_model_image.sh ...`` and run nothing — the vacuum trap
    this repository paid for four times in one day.
    """
    return "\n".join(line for line in run.splitlines() if not line.lstrip().startswith("#"))


def model_shipping_dockerfiles(root: Path) -> list[Path]:
    """Every tracked Dockerfile that copies a ``/model`` tree out of a build stage."""
    found = [
        path
        for path in sorted(root.glob("**/Dockerfile*"))
        if not {".git", ".venv", "node_modules"} & set(path.parts) and path.is_file()
        if _MODEL_COPY.search(_strip_dockerfile_comments(path.read_text()))
    ]
    return found


def healthcheck_of(dockerfile_text: str) -> str | None:
    """The last ``HEALTHCHECK`` command in *dockerfile_text*, comments removed.

    The last one: these files stack stages, and the stage that ships the model
    inherits the most recent ``HEALTHCHECK`` in the file.
    """
    folded = _join_continuations(_strip_dockerfile_comments(dockerfile_text))
    matches = _HEALTHCHECK.findall(folded)
    return matches[-1] if matches else None


def exposed_ports(dockerfile_text: str) -> set[str]:
    return set(_EXPOSE.findall(_strip_dockerfile_comments(dockerfile_text)))


def load(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    return document if isinstance(document, dict) else {}


def _jobs(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs = document.get("jobs")
    return {str(k): v for k, v in jobs.items() if isinstance(v, dict)} if isinstance(jobs, dict) else {}


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    steps = job.get("steps")
    return [step for step in steps if isinstance(step, dict)] if isinstance(steps, list) else []


def _built_file(step: dict[str, Any]) -> str | None:
    """The Dockerfile a ``docker/build-push-action`` step builds, or ``None``."""
    uses = step.get("uses")
    if not isinstance(uses, str) or not uses.startswith(_BUILD_ACTION):
        return None
    with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
    file = with_.get("file")
    if isinstance(file, str) and file:
        return file.strip()
    context = with_.get("context")
    return f"{context.rstrip('/')}/Dockerfile" if isinstance(context, str) and context else None


class SmokeCall:
    """One parsed ``scripts/ci/smoke_model_image.sh`` invocation.

    Two forms, because the class has two shapes of provable readiness:

    * ``<image> <port> <path> [required]`` — start the container, require the
      readiness endpoint. The better proof, and the one two of the three images
      can give.
    * ``<image> model <dir> <dim> <input-size>`` — load the shipped graph inside
      the image. For a service whose readiness legitimately depends on something
      that is not standing in the build job (the inference service's lifespan
      connects to pgvector before it loads the model), an HTTP probe would
      assert the absence of that dependency rather than the presence of a model.
    """

    MODEL = "model"

    def __init__(self, argv: list[str]) -> None:
        self.image = argv[1] if len(argv) > 1 else ""
        self.port = argv[2] if len(argv) > 2 else ""
        if self.port == self.MODEL:
            self.path = ""
            self.required = ""
            self.model_dir = argv[3] if len(argv) > 3 else ""
        else:
            self.path = argv[3] if len(argv) > 3 else ""
            self.required = argv[4] if len(argv) > 4 else ""
            self.model_dir = ""

    @property
    def loads_the_model_directly(self) -> bool:
        return self.port == self.MODEL

    @property
    def required_key(self) -> str:
        """The JSON key the required body substring asserts, e.g. ``model_loaded``."""
        return re.sub(r'^[\s"{,]*', "", self.required).split('"')[0].split(":")[0]


def smoke_calls(run: str) -> list[SmokeCall]:
    """Every smoke-script invocation in a ``run:`` block, comments stripped."""
    calls: list[SmokeCall] = []
    for line in _join_continuations(_strip_shell_comments(run)).splitlines():
        if str(_SMOKE_SCRIPT) not in line:
            continue
        try:
            argv = shlex.split(line)
        except ValueError:  # pragma: no cover — an unbalanced quote is a red anyway
            continue
        start = next((i for i, token in enumerate(argv) if str(_SMOKE_SCRIPT) in token), None)
        if start is not None:
            calls.append(SmokeCall(argv[start:]))
    return calls


# --------------------------------------------------------------------------
# the property
# --------------------------------------------------------------------------


def readiness_gaps(document: dict[str, Any], dockerfiles: dict[str, str]) -> dict[str, str]:
    """``dockerfile path -> why its readiness is not proven before merge``.

    *dockerfiles* maps a repository-relative Dockerfile path to its text, so the
    property can be driven over synthetic inputs as well as over the checkout.
    """
    findings: dict[str, str] = {}

    for path, text in sorted(dockerfiles.items()):
        job_id, step, job = _find_build(document, path)
        if step is None or job is None:
            findings[path] = (
                "ships a model but no `docker/build-push-action` step in docker-lint-build.yml builds it "
                "— nothing can start it before a merge"
            )
            continue

        with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
        if with_.get("load") is not True:
            findings[path] = (
                f"job {job_id!r} builds it without `load: true`, so the image never enters the docker "
                "daemon and the smoke step below cannot start it"
            )
            continue

        calls = [call for run in _runs(job) for call in smoke_calls(run)]
        if not calls:
            findings[path] = (
                f"job {job_id!r} builds it and never starts it: no {_SMOKE_SCRIPT} invocation. "
                "A green build is not a running service (#1609)"
            )
            continue

        tags = str(with_.get("tags") or "")
        matching = [call for call in calls if call.image and call.image in tags]
        if not matching:
            findings[path] = (
                f"job {job_id!r} smoke-tests {[call.image for call in calls]!r}, none of which is a tag "
                f"this build produces ({tags!r})"
            )
            continue
        call = matching[0]

        if call.loads_the_model_directly and not call.model_dir:
            findings[path] = f"job {job_id!r} smoke-tests it in `model` mode without naming a model directory"
            continue

        if not call.loads_the_model_directly and call.port and call.port not in exposed_ports(text):
            findings[path] = (
                f"the smoke step probes port {call.port}, which this Dockerfile does not EXPOSE "
                f"({sorted(exposed_ports(text))}) — `docker run -P` would publish nothing"
            )
            continue

        healthcheck = healthcheck_of(text)
        if healthcheck is None:
            findings[path] = "has no HEALTHCHECK at all, so `docker run` reports nothing about the model"
            continue
        if _SOCKET_ONLY in healthcheck:
            findings[path] = (
                "its HEALTHCHECK opens a TCP socket and nothing more. That passes the instant uvicorn "
                "binds, which is exactly how #1609 stayed invisible: a socket proves a process, not a "
                f"loaded model. Assert {call.path!r}, the surface the smoke step asserts"
            )
            continue
        if call.loads_the_model_directly:
            # No path to tie the HEALTHCHECK to; the socket-only check above is
            # the assertion that survives, and it is the one #1609 is about.
            continue

        if call.path and call.path not in healthcheck:
            findings[path] = (
                f"the smoke step proves {call.path!r} but the HEALTHCHECK asserts something else "
                f"({healthcheck.strip()!r}). The two must exercise the same readiness surface, or the "
                "container can report healthy while CI proved a different endpoint"
            )
            continue
        if call.required and call.required_key and call.required_key not in healthcheck:
            findings[path] = (
                f"the smoke step additionally requires {call.required!r} in the body, because a 200 on "
                f"{call.path!r} alone is not readiness. The HEALTHCHECK does not mention "
                f"{call.required_key!r} and therefore still reports the #1609 lie"
            )
            continue

        served = _serves(path, call.path)
        if served is False:
            findings[path] = (
                f"the readiness path {call.path!r} appears in the workflow and in the HEALTHCHECK, but in "
                "no source file of this image's build context — a path named twice and served nowhere"
            )

    return findings


def _runs(job: dict[str, Any]) -> list[str]:
    return [step["run"] for step in _steps(job) if isinstance(step.get("run"), str)]


def _find_build(
    document: dict[str, Any], dockerfile: str
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    for job_id, job in _jobs(document).items():
        for step in _steps(job):
            if _built_file(step) == dockerfile:
                return job_id, step, job
    return None, None, None


def _serves(dockerfile: str, route: str) -> bool | None:
    """Whether *route* appears as a literal in the image's build context.

    ``None`` when the context cannot be read (a synthetic document in the tests
    below), so the assertion is skipped rather than invented.
    """
    context = _REPO_ROOT / Path(dockerfile).parent
    if not route or not context.is_dir():
        return None
    return any(
        f'"{route}"' in source.read_text(errors="ignore")
        for source in context.glob("**/*.py")
        if "node_modules" not in source.parts
    )


# --------------------------------------------------------------------------
# the real checkout
# --------------------------------------------------------------------------


class TestTheRealRepository:
    def test_the_class_is_not_empty(self) -> None:
        """If the detector stopped finding images, every assertion below is vacuous."""
        found = model_shipping_dockerfiles(_REPO_ROOT)

        assert len(found) >= 2, (
            f"only {len(found)} model-shipping Dockerfile(s) detected: {found}. The detector reads "
            "`COPY --from=<stage> /model` — a new spelling of the same thing would shrink this sweep "
            "silently, which is the measuring-tool gap, not the gate's."
        )

    def test_the_smoke_script_exists_and_is_executable(self) -> None:
        script = _REPO_ROOT / _SMOKE_SCRIPT

        assert script.is_file(), f"{_SMOKE_SCRIPT} is missing; every smoke step below would fail to run"
        assert script.stat().st_mode & 0o111, f"{_SMOKE_SCRIPT} is not executable"

    def test_every_model_image_proves_its_readiness_before_merge(self) -> None:
        dockerfiles = {
            str(path.relative_to(_REPO_ROOT)): path.read_text() for path in model_shipping_dockerfiles(_REPO_ROOT)
        }
        gaps = readiness_gaps(load(_WORKFLOW), dockerfiles)

        assert gaps == {}, "an image that ships a model must be started before a merge (#1609):\n" + "\n".join(
            f"  - {path}: {why}" for path, why in sorted(gaps.items())
        )


# --------------------------------------------------------------------------
# the sweep must be able to go red
# --------------------------------------------------------------------------


class TestTheSweepCanGoRed:
    """Otherwise the green above certifies nothing (the 2026-08-15 class)."""

    _DOCKERFILE = """
FROM python:3.14-slim AS dl-thing
RUN python -c "import x; x.export('/model')"

FROM python:3.14-slim AS runtime
EXPOSE 9000
HEALTHCHECK --interval=30s CMD ["python", "-c", "import sys,urllib.request; \\
    sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/ready').status == 200 else 1)"]

FROM runtime AS final
COPY --from=dl-thing --chown=1000:1000 /model/ /app/models/thing/
USER 1000
"""

    _WORKFLOW_YAML = """
name: x
on:
  pull_request:
    paths: ['docker/thing/**']
jobs:
  build-thing:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@deadbeef
        with:
          context: docker/thing
          file: docker/thing/Dockerfile
          load: true
          tags: kp-thing:pr
          push: false
      - name: Smoke-test the built image
        run: |
          # a comment naming scripts/ci/smoke_model_image.sh proves nothing
          scripts/ci/smoke_model_image.sh kp-thing:pr 9000 /ready
"""

    def _files(self) -> dict[str, str]:
        return {"docker/thing/Dockerfile": self._DOCKERFILE}

    def _document(self, yaml_text: str | None = None) -> dict[str, Any]:
        return yaml.safe_load(yaml_text or self._WORKFLOW_YAML)

    def test_the_complete_shape_is_not_a_finding(self) -> None:
        """The positive control. Without it every red below could be an artefact."""
        assert readiness_gaps(self._document(), self._files()) == {}

    def test_the_detector_finds_the_synthetic_image(self, tmp_path: Path) -> None:
        """The detector, not just the property — a regex that matches nothing is vacuous."""
        (tmp_path / "docker" / "thing").mkdir(parents=True)
        (tmp_path / "docker" / "thing" / "Dockerfile").write_text(self._DOCKERFILE)

        assert [p.name for p in model_shipping_dockerfiles(tmp_path)] == ["Dockerfile"]

    def test_a_registry_copy_is_not_a_model_image(self, tmp_path: Path) -> None:
        """`COPY --from=ghcr.io/...` must not drag every image into the class."""
        (tmp_path / "Dockerfile").write_text("FROM scratch\nCOPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /bin/uv\n")

        assert model_shipping_dockerfiles(tmp_path) == []

    def test_a_commented_out_model_copy_is_not_a_model_image(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM scratch\n# COPY --from=dl-thing /model/ /app/m/\n")

        assert model_shipping_dockerfiles(tmp_path) == []

    def test_an_image_that_is_never_built_is_a_finding(self) -> None:
        findings = readiness_gaps({"jobs": {}}, self._files())

        assert "no `docker/build-push-action` step" in findings["docker/thing/Dockerfile"]

    def test_a_build_without_load_is_a_finding(self) -> None:
        findings = readiness_gaps(
            self._document(self._WORKFLOW_YAML.replace("          load: true\n", "")), self._files()
        )

        assert "without `load: true`" in findings["docker/thing/Dockerfile"]

    def test_a_build_that_never_starts_the_image_is_a_finding(self) -> None:
        """The #1609 defect itself: build green, never started."""
        no_smoke = self._WORKFLOW_YAML.split("      - name: Smoke-test")[0]
        findings = readiness_gaps(self._document(no_smoke), self._files())

        assert "builds it and never starts it" in findings["docker/thing/Dockerfile"]

    def test_a_smoke_step_that_is_only_a_comment_is_a_finding(self) -> None:
        """The vacuum trap: the script named, nothing run."""
        commented = self._WORKFLOW_YAML.replace(
            "          scripts/ci/smoke_model_image.sh kp-thing:pr 9000 /ready",
            "          # scripts/ci/smoke_model_image.sh kp-thing:pr 9000 /ready",
        )
        findings = readiness_gaps(self._document(commented), self._files())

        assert "never starts it" in findings["docker/thing/Dockerfile"]

    def test_smoking_a_different_image_is_a_finding(self) -> None:
        crossed = self._WORKFLOW_YAML.replace("smoke_model_image.sh kp-thing:pr", "smoke_model_image.sh kp-other:pr")
        findings = readiness_gaps(self._document(crossed), self._files())

        assert "none of which is a tag this build produces" in findings["docker/thing/Dockerfile"]

    def test_a_socket_only_healthcheck_is_a_finding(self) -> None:
        """The lie #1609 is named after."""
        socket_only = self._DOCKERFILE.replace(
            """HEALTHCHECK --interval=30s CMD ["python", "-c", "import sys,urllib.request; \\
    sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/ready').status == 200 else 1)"]""",
            """HEALTHCHECK --interval=30s CMD ["python", "-c", "import socket,sys; s=socket.socket(); \\
    sys.exit(s.connect_ex(('127.0.0.1',9000)))"]""",
        )
        findings = readiness_gaps(self._document(), {"docker/thing/Dockerfile": socket_only})

        assert "opens a TCP socket and nothing more" in findings["docker/thing/Dockerfile"]

    def test_a_missing_healthcheck_is_a_finding(self) -> None:
        stripped = "\n".join(
            line for line in self._DOCKERFILE.splitlines() if "HEALTHCHECK" not in line and "sys.exit" not in line
        )
        findings = readiness_gaps(self._document(), {"docker/thing/Dockerfile": stripped})

        assert "no HEALTHCHECK at all" in findings["docker/thing/Dockerfile"]

    def test_a_healthcheck_on_a_different_path_is_a_finding(self) -> None:
        drifted = self._DOCKERFILE.replace("9000/ready", "9000/health")
        findings = readiness_gaps(self._document(), {"docker/thing/Dockerfile": drifted})

        assert "must exercise the same readiness surface" in findings["docker/thing/Dockerfile"]

    def test_an_unexposed_smoke_port_is_a_finding(self) -> None:
        findings = readiness_gaps(
            self._document(), {"docker/thing/Dockerfile": self._DOCKERFILE.replace("EXPOSE 9000", "EXPOSE 9100")}
        )

        assert "does not EXPOSE" in findings["docker/thing/Dockerfile"]

    def test_a_body_requirement_the_healthcheck_ignores_is_a_finding(self) -> None:
        """A 200 on an always-200 `/health` is not readiness — both sides must say so."""
        body_checked = self._WORKFLOW_YAML.replace(
            "smoke_model_image.sh kp-thing:pr 9000 /ready",
            "smoke_model_image.sh kp-thing:pr 9000 /ready '\"model_loaded\":true'",
        )
        findings = readiness_gaps(self._document(body_checked), self._files())

        assert "model_loaded" in findings["docker/thing/Dockerfile"]

    #: The second form: the graph is loaded inside the image instead of served.
    _MODEL_MODE = _WORKFLOW_YAML.replace(
        "smoke_model_image.sh kp-thing:pr 9000 /ready",
        "smoke_model_image.sh kp-thing:pr model /app/models/thing 384 224",
    )

    def test_the_model_mode_shape_is_not_a_finding(self) -> None:
        """The positive control for the two properties below."""
        assert readiness_gaps(self._document(self._MODEL_MODE), self._files()) == {}

    def test_model_mode_without_a_directory_is_a_finding(self) -> None:
        nameless = self._MODEL_MODE.replace(
            "smoke_model_image.sh kp-thing:pr model /app/models/thing 384 224",
            "smoke_model_image.sh kp-thing:pr model",
        )
        findings = readiness_gaps(self._document(nameless), self._files())

        assert "without naming a model directory" in findings["docker/thing/Dockerfile"]

    def test_model_mode_does_not_excuse_a_socket_only_healthcheck(self) -> None:
        """The exemption is the PATH tie-in, never the #1609 assertion itself."""
        socket_only = self._DOCKERFILE.replace(
            """HEALTHCHECK --interval=30s CMD ["python", "-c", "import sys,urllib.request; \\
    sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/ready').status == 200 else 1)"]""",
            """HEALTHCHECK --interval=30s CMD ["python", "-c", "import socket,sys; s=socket.socket(); \\
    sys.exit(s.connect_ex(('127.0.0.1',9000)))"]""",
        )
        findings = readiness_gaps(self._document(self._MODEL_MODE), {"docker/thing/Dockerfile": socket_only})

        assert "opens a TCP socket and nothing more" in findings["docker/thing/Dockerfile"]

    def test_model_mode_ignores_a_port_the_dockerfile_does_not_expose(self) -> None:
        """`model` is not a port; reading it as one would invent a finding."""
        moved = self._DOCKERFILE.replace("EXPOSE 9000", "EXPOSE 9100")
        assert readiness_gaps(self._document(self._MODEL_MODE), {"docker/thing/Dockerfile": moved}) == {}

    def test_the_model_verifier_exists_and_is_readable(self) -> None:
        """`model` mode mounts this file into the image; a missing one is inert."""
        verifier = _REPO_ROOT / "scripts" / "ci" / "verify_onnx_model.py"
        assert verifier.is_file(), f"{verifier} is missing; every `model`-mode smoke step would fail to run"

    def test_a_body_requirement_the_healthcheck_honours_is_not_a_finding(self) -> None:
        body_checked = self._WORKFLOW_YAML.replace(
            "smoke_model_image.sh kp-thing:pr 9000 /ready",
            "smoke_model_image.sh kp-thing:pr 9000 /ready '\"model_loaded\":true'",
        )
        honouring = self._DOCKERFILE.replace(".status == 200", ".read().count(b'model_loaded') == 1")
        findings = readiness_gaps(self._document(body_checked), {"docker/thing/Dockerfile": honouring})

        assert findings == {}
