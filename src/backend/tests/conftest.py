"""Root fixtures for the backend suite, plus the two execution guards of #1434.

The guards answer "did this tier actually run?": the interpreter check at session
start refuses a session whose ``app`` comes from another checkout or whose
interpreter is not a virtual environment, and ``--max-skipped N`` reddens a run
that skipped more tests than the tier declares. Both mechanisms are pure
functions in ``tests/support/execution_guards.py``; this module only supplies the
live values and turns a message into a session failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import app
from app.common.exceptions import NotFoundError
from tests.support.execution_guards import (
    find_project_root,
    interpreter_violation,
    skip_floor_violation,
)

#: The checkout this conftest belongs to, found by walking up to the nearest
#: ``pyproject.toml``. Computed from ``__file__`` rather than from the working
#: directory: the working directory is exactly the thing that differs between a
#: correct run and the worktree mix-up the guard exists to catch.
_PROJECT_ROOT = find_project_root(Path(__file__))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--max-skipped`` — the tier's declared skip count (#1434)."""
    parser.addoption(
        "--max-skipped",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Fail the run if more than N tests were skipped. Each tier declares its "
            "measured number in .taskfiles/backend.yaml; the failure lists every skip "
            "reason so a new skip is identifiable."
        ),
    )
    parser.addoption(
        "--lane-inputs-drift",
        action="store_true",
        default=False,
        help=(
            "Run the tests marked `lane_inputs_drift` — the rules that hold the committed "
            ".github/lane-inputs/ manifests against the live workflows. Only lane-inputs.yml "
            "passes it (#1794); without it they are deselected, not skipped."
        ),
    )


#: #1794: the marker of the manifest-against-live-workflow rules. They need a CI
#: recording to turn green after a job changes, so a pull request cannot satisfy them
#: without one; they run in lane-inputs.yml on `develop`, which passes the option above.
LANE_INPUTS_DRIFT_MARKER = "lane_inputs_drift"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Deselect the ``lane_inputs_drift`` tests unless ``--lane-inputs-drift`` asks for them (#1794).

    Deselected, not skipped: a skip would count against every tier's
    ``--max-skipped`` floor, and a deselection is reported as such. A hook rather
    than ``-m``: the required guards lane already passes ``-m 'not advisory'``, and a
    second ``-m`` in ``addopts`` would be overridden by it, silently.
    """
    if config.getoption("--lane-inputs-drift"):
        return
    kept: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        (deselected if item.get_closest_marker(LANE_INPUTS_DRIFT_MARKER) else kept).append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept


def pytest_configure(config: pytest.Config) -> None:
    """Abort the session before collection if the interpreter is the wrong one (#1434).

    Raises:
        pytest.UsageError: naming both paths and the expectation. Deliberately an
            error and not a skip or a warning — the failure class this guards
            against is a run that looked green while measuring something else.
    """
    message = interpreter_violation(
        app_file=app.__file__,
        project_root=_PROJECT_ROOT,
        prefix=sys.prefix,
        base_prefix=sys.base_prefix,
        executable=sys.executable,
    )
    if message is not None:
        raise pytest.UsageError(message)


def _render_skip(report: pytest.TestReport | pytest.CollectReport) -> str:
    """Render one skip report the way ``-rs`` renders it: ``path:lineno: reason``."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        path, lineno, reason = longrepr
        # pytest's own `-rs` summary drops this prefix; keeping the rendering
        # identical is what lets a reader compare the two outputs line for line.
        reason = str(reason).removeprefix("Skipped: ")
        return f"{path}:{lineno}: {reason}"
    return f"{report.nodeid}: {longrepr}"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Redden a run that skipped more than its tier declares (#1434).

    ``exitstatus`` is the value pytest computed; ``wrap_session`` returns
    ``session.exitstatus`` after this hook, so assigning it here is what turns the
    violation into the process's exit code.
    """
    max_skipped = session.config.getoption("--max-skipped")
    if max_skipped is None:
        return

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:  # pragma: no cover - only absent under -p no:terminal
        return

    reasons = [_render_skip(report) for report in reporter.stats.get("skipped", [])]
    message = skip_floor_violation(max_skipped=max_skipped, reasons=reasons)
    if message is None:
        return

    reporter.write_line("")
    reporter.write_sep("=", "skip floor exceeded", red=True, bold=True)
    reporter.write_line(message)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


def wire_or_raise(
    mock,
    entity: str = "Entity",
    *,
    by_key: str = "get_by_key",
    or_raise: str = "get_or_raise",
):
    """Make a ``MagicMock`` repo's ``<or_raise>`` mirror its ``<by_key>`` stub.

    FR-002 (A) lifted the copied ``get_by_key`` + ``None`` check +
    ``NotFoundError`` service blocks into the repository's ``get_or_raise`` /
    facade ``get_<entity>_or_raise`` methods. Solitary service tests stub the
    underlying ``<by_key>`` getter; this helper lets those existing stubs keep
    driving both the found and not-found paths without touching every assertion.

    ``by_key``/``or_raise`` name the getter pair so the same helper covers the
    generic ``get_by_key``/``get_or_raise`` and the named facade pairs
    (``get_schedule_by_key``/``get_schedule_or_raise`` …).
    """

    def _or_raise(key):
        value = getattr(mock, by_key)(key)
        if value is None:
            raise NotFoundError(entity, key)
        return value

    getattr(mock, or_raise).side_effect = _or_raise
    return mock


def wire_get_or_raise(mock, entity: str = "Entity"):
    """Wire the generic ``get_or_raise`` to mirror ``get_by_key`` (see :func:`wire_or_raise`)."""
    return wire_or_raise(mock, entity)


@pytest.fixture
def sample_species_data():
    return {
        "scientific_name": "Solanum lycopersicum",
        "common_names": ["Tomato"],
        "genus": "Solanum",
        "growth_habit": "herb",
        "root_type": "fibrous",
        "allelopathy_score": 0.0,
        "base_temp": 10.0,
        "hardiness_zones": ["7a", "7b", "8a"],
    }


@pytest.fixture
def sample_site_data():
    return {
        "name": "Indoor Garden",
        "type": "indoor",
        "climate_zone": "8a",
        "total_area_m2": 20.0,
    }


@pytest.fixture
def sample_location_data():
    return {
        "name": "Grow Tent 1",
        "site_key": "site_1",
        "area_m2": 4.0,
        "light_type": "led",
        "irrigation_system": "drip",
        "dimensions": (2.0, 2.0, 2.0),
    }


@pytest.fixture
def sample_substrate_data():
    return {
        "type": "coco",
        "brand": "Canna",
        "ph_base": 6.0,
        "ec_base_ms": 0.3,
        "water_retention": "high",
        "air_porosity_percent": 30.0,
        "buffer_capacity": "medium",
        "reusable": True,
        "max_reuse_cycles": 3,
    }
