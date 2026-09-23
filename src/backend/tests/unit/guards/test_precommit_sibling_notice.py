"""#1641/#1649 — `task precommit` must be able to say whether it ran alone.

`scripts/precommit_sibling_notice.sh` is the only thing that turns "nothing else
was running" from an assertion into an observation. A notice that has gone quiet
is worse than no notice at all, because a report would keep citing its silence
as evidence of isolation — which is the exact failure class the script exists to
close.

It reports two independent things, and both are covered here: an overlapping
sibling run (#1641), and a tree that changed while the suite was in flight
(#1649 — the mechanism that produced the one measured false green, where a file
staged mid-run sits outside the list pre-commit enumerated at the start).

So the guard is bidirectional, and deliberately so: it is not enough to show
that the banner appears when a sibling is registered. `test_no_notice_without_a
_sibling` is the half that would still be green if the script printed the banner
unconditionally, and `test_the_exit_code_is_the_hook_suites_own` is the half that
would go red if the wrapper ever started deciding the verdict itself.

The real suite is never invoked here. The script takes its runner from
`PRE_COMMIT_BIN`, so a stub that exits with a chosen code stands in for the
seven-minute hook run, and `PRE_COMMIT_HOME` points the sibling registry at a
temporary directory instead of the developer's store.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCRIPT = _REPO_ROOT / "scripts" / "precommit_sibling_notice.sh"
_REGISTRY_NAME = "kamerplanter-task-precommit"


def _stub_runner(tmp_path: Path, exit_code: int) -> Path:
    """A stand-in for `pre-commit`, so the guard never runs the real suite."""
    stub = tmp_path / "fake-pre-commit"
    stub.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    stub.chmod(0o755)
    return stub


def _run(tmp_path: Path, *, exit_code: int = 0) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PRE_COMMIT_HOME"] = str(tmp_path / "store")
    env["PRE_COMMIT_BIN"] = str(_stub_runner(tmp_path, exit_code))
    return subprocess.run(
        [str(_SCRIPT)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.fixture
def live_sibling(tmp_path: Path) -> Iterator[subprocess.Popen[bytes]]:
    """A registered, actually-running sibling — a pid the script can verify."""
    registry = tmp_path / "store" / _REGISTRY_NAME
    registry.mkdir(parents=True)
    proc = subprocess.Popen(["sleep", "60"])
    (registry / str(proc.pid)).write_text("/fake/other-worktree\n")
    yield proc
    proc.kill()
    proc.wait()


def test_the_script_is_executable() -> None:
    assert _SCRIPT.is_file(), f"{_SCRIPT} is gone — `task precommit` calls it"
    assert os.access(_SCRIPT, os.X_OK), f"{_SCRIPT} is not executable"


def test_a_live_sibling_is_named(tmp_path: Path, live_sibling: subprocess.Popen[bytes]) -> None:
    result = _run(tmp_path)

    assert "CONCURRENT 'task precommit'" in result.stderr
    assert str(live_sibling.pid) in result.stderr
    assert "/fake/other-worktree" in result.stderr


def test_no_notice_without_a_sibling(tmp_path: Path) -> None:
    """The half that fails if the banner is ever printed unconditionally."""
    result = _run(tmp_path)

    assert "CONCURRENT" not in result.stderr


def test_a_dead_sibling_is_reaped_not_reported(tmp_path: Path) -> None:
    """A pid whose process is gone is a leftover, not a concurrent run."""
    registry = tmp_path / "store" / _REGISTRY_NAME
    registry.mkdir(parents=True)
    dead = subprocess.Popen(["true"])
    dead.wait()
    time.sleep(0.05)
    stale = registry / str(dead.pid)
    stale.write_text("/fake/crashed-worktree\n")

    result = _run(tmp_path)

    assert "CONCURRENT" not in result.stderr
    assert not stale.exists(), "a stale registry entry must be removed, not kept"


@pytest.mark.parametrize("exit_code", [0, 1, 7])
def test_the_exit_code_is_the_hook_suites_own(tmp_path: Path, exit_code: int) -> None:
    """The wrapper reports; it never decides. A verdict it altered is a lie."""
    assert _run(tmp_path, exit_code=exit_code).returncode == exit_code


def test_the_taskfile_target_calls_the_wrapper() -> None:
    """A wrapper nothing invokes protects nothing.

    Read through the YAML parser rather than as text: a `precommit:` target that
    only *mentioned* the wrapper in its `desc:` would satisfy a substring search
    while running plain `pre-commit` (#1456).
    """
    checks = yaml.safe_load((_REPO_ROOT / ".taskfiles" / "checks.yaml").read_text())
    cmds = checks["tasks"]["precommit"]["cmds"]

    assert any(
        isinstance(cmd, str) and cmd.strip().startswith("./scripts/precommit_sibling_notice.sh") for cmd in cmds
    ), f"`task precommit` no longer runs the sibling notice: {cmds}"


def test_a_write_during_the_run_is_reported(tmp_path: Path) -> None:
    """The #1649 half: a tree that moved under the run must be named.

    The stub stands in for the hook suite AND for the second writer: it creates
    a file while it "runs", which is exactly what a concurrent editor does.
    """
    marker = _REPO_ROOT / "_tree_notice_guard_probe.txt"
    stub = tmp_path / "writing-pre-commit"
    stub.write_text(f"#!/bin/sh\necho probe > {marker}\nexit 0\n")
    stub.chmod(0o755)
    env = dict(os.environ)
    env["PRE_COMMIT_HOME"] = str(tmp_path / "store")
    env["PRE_COMMIT_BIN"] = str(stub)
    try:
        result = subprocess.run(
            [str(_SCRIPT)],
            cwd=_REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    finally:
        marker.unlink(missing_ok=True)

    assert "THE TREE CHANGED WHILE THIS RUN WAS IN FLIGHT" in result.stderr
    assert marker.name in result.stderr, "the notice must name the path, not just warn"


def test_no_tree_notice_when_nothing_moved(tmp_path: Path) -> None:
    """The half that fails if the tree notice is ever printed unconditionally."""
    result = _run(tmp_path)

    assert "THE TREE CHANGED" not in result.stderr
