"""#1432 — the integration tier may not report green without a database.

``tests/integration/`` is the only place the repository and AQL layer is measured
against a real ArangoDB. Until this change each of its nine connecting modules
carried its own copy of an ``ARANGO_AVAILABLE`` probe and skipped itself when
nothing answered, so the tier could not be put into a gate: on a runner it
produced ``7 passed, 136 skipped`` and exit code 0 — measured on 2026-09-16.

This file drives the replacement from both ends:

* the discriminator, over every spelling of ``CI`` a build agent uses and over
  the two spellings of "not a build agent" (unset, empty);
* the gate end to end, as a **subprocess** pointed at an address nothing listens
  on, because the property under test is what a *whole session* does: under
  ``CI`` it must end in an error and a non-zero exit code, and locally it must
  end in a skip whose reason names the address. Asserting on the fixture
  function alone would certify the predicate and say nothing about whether the
  modules are attached to it;
* the absence of the old probe, so the nine copies cannot creep back in one
  module at a time — the drift shape this repository keeps meeting.

The unreachable address is ``127.0.0.1:1``: a port no server may bind, so the
run does not depend on whether the developer happens to have the dev stack up.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.conftest import _running_in_ci, _unavailable_message
from tests.support.execution_guards import find_project_root

#: ``src/backend`` — the checkout these tests belong to.
_PROJECT_ROOT = find_project_root(Path(__file__))

_INTEGRATION_DIR = _PROJECT_ROOT / "tests" / "integration"

#: One real module of the tier, small enough to run as a child session. Its
#: single case is gated exactly like the other 135.
_GATED_MODULE = "tests/integration/test_arango_integration.py"

#: The module of the tier that needs **no** server: it drives real engines
#: against in-memory repositories. It must stay unaffected by the gate, which is
#: why the gate is attached per module instead of being autouse.
_UNGATED_MODULE = "tests/integration/test_perennial_cycle_loop.py"

#: Nothing listens here, on any machine.
_UNREACHABLE = {"ARANGODB_HOST": "127.0.0.1", "ARANGODB_PORT": "1"}


class TestCiDiscriminator:
    """Which sessions must fail rather than skip."""

    @pytest.mark.parametrize("value", ["true", "1", "TRUE", "yes"])
    def test_any_non_empty_ci_value_counts_as_a_build_agent(self, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CI", value)

        assert _running_in_ci() is True

    @pytest.mark.parametrize("value", ["", "   "])
    def test_an_empty_ci_value_is_not_a_build_agent(self, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CI", value)

        assert _running_in_ci() is False

    def test_an_absent_ci_variable_is_not_a_build_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CI", raising=False)

        assert _running_in_ci() is False


class TestUnavailableMessage:
    """The message must let a reader act, which means naming what was tried."""

    def test_names_the_address_the_tier_tried(self, monkeypatch: pytest.MonkeyPatch) -> None:
        message = _unavailable_message("ConnectionAbortedError: nothing there")

        assert "http://" in message
        assert "8529" in message or "ARANGODB_PORT" in message
        assert "ConnectionAbortedError: nothing there" in message

    def test_names_the_environment_variables_that_move_the_address(self) -> None:
        message = _unavailable_message("boom")

        for variable in ("ARANGODB_HOST", "ARANGODB_PORT", "ARANGODB_USERNAME", "ARANGODB_PASSWORD"):
            assert variable in message


def _run(module: str, *, ci: bool, unreachable: bool = True) -> subprocess.CompletedProcess[str]:
    """Run one module of the integration tier in a child pytest session."""
    env = dict(os.environ)
    env.pop("CI", None)
    if ci:
        env["CI"] = "true"
    if unreachable:
        env.update(_UNREACHABLE)
    return subprocess.run(
        [sys.executable, "-m", "pytest", module, "-q", "-rs", "-p", "no:cacheprovider"],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env=env,
    )


class TestGateEndToEnd:
    """A real session, so a gate that were implemented but never attached reddens here."""

    def test_in_ci_a_missing_database_reddens_the_run(self) -> None:
        result = _run(_GATED_MODULE, ci=True)

        assert result.returncode != 0, result.stdout
        assert "ArangoDB did not answer at http://127.0.0.1:1" in result.stdout
        assert " skipped" not in result.stdout

    def test_locally_a_missing_database_skips_with_the_address_in_the_reason(self) -> None:
        result = _run(_GATED_MODULE, ci=False)

        assert result.returncode == 0, result.stdout
        assert "1 skipped" in result.stdout
        assert "ArangoDB did not answer at http://127.0.0.1:1" in result.stdout

    def test_the_skip_floor_reddens_even_the_local_skip(self) -> None:
        """``task test:backend:integration`` declares ``--max-skipped 0`` (#1434)."""
        env = dict(os.environ)
        env.pop("CI", None)
        env.update(_UNREACHABLE)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", _GATED_MODULE, "-q", "-p", "no:cacheprovider", "--max-skipped", "0"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
            env=env,
        )

        assert result.returncode != 0, result.stdout
        assert "skip floor exceeded" in result.stdout

    def test_the_server_free_module_of_the_tier_is_not_gated(self) -> None:
        """The gate hangs off the modules that connect, not off the directory."""
        result = _run(_UNGATED_MODULE, ci=True)

        assert result.returncode == 0, result.stdout
        assert " skipped" not in result.stdout
        assert " error" not in result.stdout


def _tier_sources() -> list[Path]:
    """Every module of the tier except the conftest that holds the contract."""
    return sorted(path for path in _INTEGRATION_DIR.glob("*.py") if path.name != "conftest.py")


def _defines_a_probe(paths: list[Path]) -> list[str]:
    """Modules that bind an ``ARANGO_AVAILABLE``-style name themselves.

    Read from the syntax tree, not by substring: the module docstrings of this
    tier *discuss* the old probe, and a sweep that counts prose as a violation
    would have to be weakened to stay green — which is how a guard stops
    guarding.
    """
    offenders = []
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        names = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        if any(name.startswith("ARANGO_AVAILABLE") for name in names):
            offenders.append(path.name)
    return offenders


def _hard_codes_the_address(paths: list[Path]) -> list[str]:
    """Modules with the server address in an executable string, docstrings excluded.

    Docstrings are excluded by identity (the exact nodes Python stores as
    ``__doc__``), so a prose reference like "…where ``localhost:8529`` answering
    on a developer machine…" is not a finding while an f-string, a default
    argument or a dict value is. ``ast.walk`` descends into ``JoinedStr``, so an
    interpolated spelling is caught too.
    """
    offenders = []
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        }
        literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
        ]
        if any("localhost:8529" in literal or literal == "rootpassword" for literal in literals):
            offenders.append(path.name)
    return offenders


class TestTheOldProbeIsGone:
    """The nine copies may not creep back one module at a time."""

    def test_no_module_carries_its_own_availability_probe(self) -> None:
        offenders = _defines_a_probe(_tier_sources())

        assert offenders == [], (
            f"{offenders} still decide availability for themselves. A module-local probe "
            "skips instead of failing, which is what kept this tier out of CI (#1432). "
            'Depend on the session fixture instead: pytestmark = pytest.mark.usefixtures("arango_db").'
        )

    def test_no_module_hard_codes_the_server_address(self) -> None:
        offenders = _hard_codes_the_address(_tier_sources())

        assert offenders == [], (
            f"{offenders} hard-code the address or the root password, so the CI lane cannot "
            "point the tier anywhere else. Import ARANGO_URL / ARANGO_USERNAME / "
            "ARANGO_PASSWORD from tests.support.arango_integration."
        )

    def test_both_sweeps_can_see_a_violation_at_all(self, tmp_path: Path) -> None:
        """The measuring tools must be able to go red — otherwise they prove nothing."""
        planted = tmp_path / "test_planted.py"
        planted.write_text(
            '"""A docstring mentioning localhost:8529, which is not a finding."""\n'
            "ARANGO_AVAILABLE = False\n"
            'HOST = f"http://localhost:8529/{1}"\n'
        )
        prose_only = tmp_path / "test_prose_only.py"
        prose_only.write_text('"""Needs a server on localhost:8529 with password rootpassword."""\n')

        assert _defines_a_probe([planted]) == ["test_planted.py"]
        assert _hard_codes_the_address([planted]) == ["test_planted.py"]
        assert _defines_a_probe([prose_only]) == []
        assert _hard_codes_the_address([prose_only]) == []
