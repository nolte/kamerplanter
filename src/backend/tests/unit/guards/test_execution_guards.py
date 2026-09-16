"""#1434 — the two guards that make a backend tier prove it actually ran.

Both mechanisms live in ``tests/support/execution_guards.py`` and are wired in
``tests/conftest.py``. This file drives them from both ends:

* the pure predicates, with a **faked** ``sys.prefix`` and a **faked**
  ``app.__file__`` — the two states that cannot be produced from inside a healthy
  session;
* the real wiring, by calling ``tests.conftest.pytest_configure`` with those fakes
  monkeypatched onto the live modules, so a guard that were implemented but never
  called would redden here (the failure class this repository keeps meeting:
  "implemented but inert");
* the skip floor end to end, as a subprocess against a tier file whose single
  skip is measured, pinning the comparison at its boundary — floor 1 with one
  skip must stay GREEN, floor 0 with one skip must go RED. Turning the ``>`` in
  :func:`skip_floor_violation` into ``>=`` reddens the first case; dropping the
  comparison altogether reddens the second.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import app
import tests.conftest as root_conftest
from tests.support.execution_guards import (
    find_project_root,
    interpreter_violation,
    skip_floor_violation,
)

#: ``src/backend`` — the checkout these tests belong to.
_PROJECT_ROOT = find_project_root(Path(__file__))

#: A tier module measured on 2026-09-16 to skip exactly one case: its own
#: allowlisted configuration file, which the parametrised guard skips by design
#: (``tests/unit/migrations/test_e2e_admin_env_containment.py:86``). Used as the
#: real input for the end-to-end skip-floor runs below.
_ONE_SKIP_MODULE = "tests/unit/migrations/test_e2e_admin_env_containment.py"


class TestFindProjectRoot:
    """The root is searched for, never counted to."""

    def test_finds_the_directory_holding_pyproject_toml(self) -> None:
        assert (_PROJECT_ROOT / "pyproject.toml").is_file()
        assert (_PROJECT_ROOT / "app").is_dir()

    def test_search_starts_at_the_given_file_and_walks_up(self) -> None:
        deep = _PROJECT_ROOT / "tests" / "unit" / "guards" / "test_execution_guards.py"

        assert find_project_root(deep) == _PROJECT_ROOT

    def test_raises_instead_of_guessing_when_no_marker_exists(self, tmp_path: Path) -> None:
        nowhere = tmp_path / "a" / "b"
        nowhere.mkdir(parents=True)

        with pytest.raises(RuntimeError, match="pyproject.toml"):
            find_project_root(nowhere)


class TestInterpreterViolation:
    """What the predicate accepts, and what it names when it refuses."""

    def test_accepts_this_very_session(self) -> None:
        assert (
            interpreter_violation(
                app_file=app.__file__,
                project_root=_PROJECT_ROOT,
                prefix=sys.prefix,
                base_prefix=sys.base_prefix,
                executable=sys.executable,
            )
            is None
        )

    def test_accepts_uv_run_which_exports_no_virtual_env_variable(self) -> None:
        """`uv run --locked` must pass — it is how the lock chain starts the suite.

        Measured 2026-09-16: it sets ``sys.prefix`` to ``src/backend/.venv`` and
        leaves ``VIRTUAL_ENV`` unset, so a guard keyed on the variable rather than
        on the prefix pair would reject the project's own runner.
        """
        assert (
            interpreter_violation(
                app_file=_PROJECT_ROOT / "app" / "__init__.py",
                project_root=_PROJECT_ROOT,
                prefix=str(_PROJECT_ROOT / ".venv"),
                base_prefix="/home/runner/.local/share/uv/python/cpython-3.14.2",
                executable=str(_PROJECT_ROOT / ".venv" / "bin" / "python"),
            )
            is None
        )

    def test_refuses_a_system_interpreter_and_names_both_prefixes(self) -> None:
        message = interpreter_violation(
            app_file=_PROJECT_ROOT / "app" / "__init__.py",
            project_root=_PROJECT_ROOT,
            prefix="/usr/lib/python3.14",
            base_prefix="/usr/lib/python3.14",
            executable="/usr/bin/python3",
        )

        assert message is not None
        assert "not a virtual environment" in message
        assert "sys.prefix      : /usr/lib/python3.14" in message
        assert "sys.base_prefix : /usr/lib/python3.14" in message
        assert "uv sync --locked --extra dev" in message

    def test_refuses_an_app_from_another_checkout_and_names_both_paths(self) -> None:
        foreign = Path("/home/dev/repos/github/kamerplanter/src/backend/app/__init__.py")

        message = interpreter_violation(
            app_file=foreign,
            project_root=_PROJECT_ROOT,
            prefix=str(_PROJECT_ROOT / ".venv"),
            base_prefix="/usr/lib/python3.14",
            executable=str(_PROJECT_ROOT / ".venv" / "bin" / "python"),
        )

        assert message is not None
        assert "DIFFERENT checkout" in message
        assert str(foreign) in message
        assert str(_PROJECT_ROOT) in message

    def test_reports_both_problems_when_both_hold(self) -> None:
        message = interpreter_violation(
            app_file="/somewhere/else/app/__init__.py",
            project_root=_PROJECT_ROOT,
            prefix="/usr/lib/python3.14",
            base_prefix="/usr/lib/python3.14",
            executable="/usr/bin/python3",
        )

        assert message is not None
        assert "  1. " in message
        assert "  2. " in message


class TestInterpreterGuardIsWired:
    """The predicate is called by the session hook — not merely present."""

    def test_faked_system_prefix_aborts_the_session(
        self, pytestconfig: pytest.Config, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "prefix", sys.base_prefix)

        with pytest.raises(pytest.UsageError) as excinfo:
            root_conftest.pytest_configure(pytestconfig)

        assert "not a virtual environment" in str(excinfo.value)

    def test_faked_foreign_app_file_aborts_the_session(
        self, pytestconfig: pytest.Config, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(app, "__file__", "/home/dev/other-checkout/src/backend/app/__init__.py")

        with pytest.raises(pytest.UsageError) as excinfo:
            root_conftest.pytest_configure(pytestconfig)

        assert "DIFFERENT checkout" in str(excinfo.value)
        assert "/home/dev/other-checkout/src/backend/app/__init__.py" in str(excinfo.value)

    def test_the_healthy_session_is_not_aborted(self, pytestconfig: pytest.Config) -> None:
        assert root_conftest.pytest_configure(pytestconfig) is None


class TestSkipFloorViolation:
    """The comparison, pinned at its boundary, and the reasons it must carry."""

    def test_no_skips_at_all_passes(self) -> None:
        assert skip_floor_violation(max_skipped=0, reasons=[]) is None

    def test_exactly_the_declared_number_passes(self) -> None:
        assert skip_floor_violation(max_skipped=1, reasons=["tests/unit/x.py:86: allowlisted"]) is None

    def test_one_above_the_declared_number_fails(self) -> None:
        message = skip_floor_violation(
            max_skipped=1,
            reasons=["tests/unit/x.py:86: allowlisted", "tests/unit/y.py:12: ArangoDB not available"],
        )

        assert message is not None
        assert "skipped 2 tests" in message
        assert "at most 1" in message

    def test_every_reason_is_named_so_the_new_skip_is_identifiable(self) -> None:
        message = skip_floor_violation(
            max_skipped=0,
            reasons=["tests/unit/x.py:86: allowlisted", "tests/unit/y.py:12: ArangoDB not available"],
        )

        assert message is not None
        assert "tests/unit/x.py:86: allowlisted" in message
        assert "tests/unit/y.py:12: ArangoDB not available" in message

    def test_identical_reasons_are_grouped_with_a_count_like_rs(self) -> None:
        reason = "tests/integration/test_repo.py:9: ArangoDB not available"

        message = skip_floor_violation(max_skipped=0, reasons=[reason] * 3)

        assert message is not None
        assert f"SKIPPED [3] {reason}" in message


def _run_tier(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the one-skip tier module in a child pytest, from this checkout's interpreter."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", _ONE_SKIP_MODULE, "-q", "-p", "no:cacheprovider", *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


class TestSkipFloorEndToEnd:
    """A real pytest session, so the hook's exit-code assignment is proven too."""

    def test_a_skip_above_the_floor_reddens_the_run_and_prints_the_reason(self) -> None:
        result = _run_tier("--max-skipped", "0")

        assert result.returncode != 0, result.stdout
        assert "skip floor exceeded" in result.stdout
        assert "skipped 1 tests; the tier declares at most 0" in result.stdout
        assert "the file that is allowed to set them" in result.stdout

    def test_the_declared_number_keeps_the_run_green(self) -> None:
        result = _run_tier("--max-skipped", "1")

        assert result.returncode == 0, result.stdout
        assert "skip floor exceeded" not in result.stdout

    def test_without_the_option_nothing_changes(self) -> None:
        result = _run_tier()

        assert result.returncode == 0, result.stdout
        assert "skip floor exceeded" not in result.stdout
