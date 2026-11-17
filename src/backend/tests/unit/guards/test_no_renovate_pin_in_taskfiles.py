"""#2581 — no Renovate-aged pin lives in a Taskfile; they live in ``.pins/``.

**The defect class.** Every task-driven lane runs through ``task``, and ``task``
parses every included Taskfile on every invocation, so the frontend and
integration lanes' paths-filters select ``.taskfiles/**`` (and ``Taskfile.yaml``).
A path filter cannot tell a pin line from a real Taskfile change. While the
``renovate/renovate`` and ``hadolint`` image pins sat in ``.taskfiles/checks.yaml``
and ``.taskfiles/deploy.yaml``, every Renovate bump of either ran those required
lanes in full for a change none of them reads. The pins moved to
``.pins/images.yaml``, which no lane reads, and each task loads its value lazily
through a task-level dynamic var.

**What is asserted, and why both halves.**

* No Taskfile carries a ``# renovate: datasource=…`` marker or a digest-pinned
  image (``@sha256:<64 hex>``). Either is the start of the same regression: a
  marker makes Renovate bump the Taskfile, an unmarked digest pin is one a
  reviewer will "fix" by adding the marker.
* The docker regex manager in ``renovate.json5`` does not select ``.taskfiles/``
  or ``Taskfile.yaml`` (a pattern left there would invite the next pin back) and
  does select ``.pins/images.yaml`` (otherwise the moved pins would silently stop
  ageing). ``scripts/ci/check_renovate_dashboard.py`` cannot hold this: it judges
  the marker SHAPE, not the manager's file patterns.

Anti-vacuity: the Taskfile corpus must be non-empty, and the scanner is run on a
planted tree that must go red, so a broken glob or regex cannot pass on nothing.

Traces to #2581 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.support.renovate_config import load
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_CONFIG = _REPO_ROOT / "renovate.json5"
_PIN_FILE = ".pins/images.yaml"

#: Every Taskfile `task` parses: the root file and its includes.
_TASKFILE_GLOBS = (".taskfiles/*.yml", ".taskfiles/*.yaml", "Taskfile.yml", "Taskfile.yaml")

#: The Renovate regex-manager marker (not the task name `renovate:dry-run`).
_MARKER = re.compile(r"#\s*renovate:\s*datasource=")
#: A digest-pinned reference, as Renovate writes it.
_DIGEST_PIN = re.compile(r"@sha256:[0-9a-f]{64}")


def _taskfiles(root: Path) -> list[Path]:
    return sorted(
        {path for glob in _TASKFILE_GLOBS for path in root.glob(glob) if path.is_file()},
        key=lambda path: path.as_posix(),
    )


def renovate_pins_in_taskfiles(root: Path) -> list[str]:
    """``path:line`` for every Renovate marker or digest pin in a Taskfile under *root*."""
    found = []
    for path in _taskfiles(root):
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _MARKER.search(line) or _DIGEST_PIN.search(line):
                found.append(f"{relative}:{number}")
    return found


def _docker_manager_file_patterns() -> list[re.Pattern[str]]:
    """The ``managerFilePatterns`` of the custom regex manager that ages docker pins."""
    managers = load(_CONFIG.read_text(encoding="utf-8")).get("customManagers")
    assert isinstance(managers, list) and managers, "no customManagers parsed from renovate.json5"
    docker: list[dict[str, Any]] = [
        manager
        for manager in managers
        if manager.get("customType") == "regex" and manager.get("datasourceTemplate") == "docker"
    ]
    assert len(docker) == 1, f"expected exactly one docker regex custom manager, found {len(docker)}"
    raw = docker[0].get("managerFilePatterns")
    assert isinstance(raw, list) and raw, "the docker regex manager lists no managerFilePatterns"
    patterns = []
    for pattern in raw:
        assert isinstance(pattern, str) and pattern.startswith("/") and pattern.endswith("/"), (
            f"managerFilePatterns entry {pattern!r} is not a /regex/ — this guard cannot judge a glob"
        )
        patterns.append(re.compile(pattern[1:-1]))
    return patterns


class TestNoRenovatePinInTaskfiles:
    def test_the_taskfile_corpus_is_not_empty(self) -> None:
        files = [path.relative_to(_REPO_ROOT).as_posix() for path in _taskfiles(_REPO_ROOT)]
        assert "Taskfile.yaml" in files and len(files) >= 5, (
            f"only {files} found — has the Taskfile layout moved? The sweep below would be green over nothing."
        )

    def test_no_taskfile_carries_a_renovate_pin(self) -> None:
        assert renovate_pins_in_taskfiles(_REPO_ROOT) == [], (
            "a Renovate marker or digest-pinned image sits in a Taskfile. Every task-driven lane selects "
            ".taskfiles/** and Taskfile.yaml, so each bump of it runs those lanes for nothing (#2581). "
            f"Put the pin in {_PIN_FILE} and read it from a task-level dynamic var."
        )

    def test_a_planted_pin_goes_red(self, tmp_path: Path) -> None:
        taskfiles = tmp_path / ".taskfiles"
        taskfiles.mkdir()
        (tmp_path / "Taskfile.yaml").write_text("version: '3'\n")
        (taskfiles / "clean.yaml").write_text("tasks:\n  renovate:dry-run:\n    cmds: [echo]\n")
        (taskfiles / "marked.yaml").write_text(
            "vars:\n  # renovate: datasource=docker depName=renovate/renovate\n  IMAGE: renovate/renovate:44\n"
        )
        (taskfiles / "digest.yaml").write_text("vars:\n  IMAGE: busybox:1.38.0@sha256:" + "a" * 64 + "\n")

        assert renovate_pins_in_taskfiles(tmp_path) == [".taskfiles/digest.yaml:2", ".taskfiles/marked.yaml:2"]


class TestTheDockerManagerReadsThePinFileNotTheTaskfiles:
    def test_the_manager_does_not_select_a_taskfile(self) -> None:
        patterns = _docker_manager_file_patterns()
        selected = [
            path
            for path in (".taskfiles/checks.yaml", ".taskfiles/deploy.yaml", "Taskfile.yaml")
            if any(pattern.search(path) for pattern in patterns)
        ]
        assert not selected, (
            f"the docker regex manager still selects {selected}; Renovate-aged pins live in {_PIN_FILE} since #2581"
        )

    def test_the_manager_selects_the_pin_file(self) -> None:
        patterns = _docker_manager_file_patterns()
        assert (_REPO_ROOT / _PIN_FILE).is_file(), f"{_PIN_FILE} is missing"
        assert any(pattern.search(_PIN_FILE) for pattern in patterns), (
            f"the docker regex manager does not select {_PIN_FILE}; its pins would stop ageing"
        )

    def test_the_pin_file_carries_the_moved_pins(self) -> None:
        """Floor: the two pins #2581 moved are there, each marker directly above its key."""
        text = (_REPO_ROOT / _PIN_FILE).read_text(encoding="utf-8")
        for dep, key in (("renovate/renovate", "RENOVATE_IMAGE"), ("ghcr.io/hadolint/hadolint", "HADOLINT_IMAGE")):
            pattern = (
                rf"^# renovate: datasource=docker depName={re.escape(dep)}\n"
                rf"{key}: {re.escape(dep)}:\S+@sha256:[0-9a-f]{{64}}$"
            )
            # prose-permeable: the asserted artefact IS the `# renovate:` marker comment above the pin
            assert re.search(pattern, text, re.MULTILINE), f"{key} ({dep}) is not pinned in {_PIN_FILE}"
