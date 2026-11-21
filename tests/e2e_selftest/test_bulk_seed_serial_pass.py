"""Bulk-seeding tests run alone, in a serial pass after the parallel one (#3032).

``tests/e2e/_renderer_plans.py:provision_grid_plan`` builds garden plans of
thousands of objects in the one shared tenant - the renderer measurement plants
8 000 plants through 280 planting runs on four threads. Run on one xdist worker
while the other three ran journeys, it pushed planting-run POSTs from 0.03 s to
5-7 s; the journeys' API helpers timed out and later pickers no longer listed
the journeys' new plants. Light mode has a single tenant, so isolating the
tenant is not an option: the runners now run the suite in two passes
(``tests/e2e/two_pass_entrypoint.sh``), and the second, serial pass picks the
tests marked ``bulk_seed``.

The separation holds only as long as three things stay true, and each is
silent when it breaks - the night just goes red again for reasons that look
like flaky journeys:

1. every test that reaches ``provision_grid_plan`` carries ``bulk_seed``
   (an unmarked one runs in the parallel pass again);
2. no runner in ``docker-compose.e2e.yml`` runs the whole suite on xdist
   workers outside the two-pass entrypoint;
3. the entrypoint runs pass 2 after a red pass 1, combines both exit codes and
   hands pass 2 pass 1's report directory.

Scope of (1), honestly: the analysis is per module and follows module-local
functions and fixtures (a fixture requested by parameter name, a helper called
by name). A provisioning fixture defined in ``conftest.py`` and requested from a
test module is not followed - importing ``tests/e2e`` would need Selenium and a
browser, which this tier exists to avoid. The rule is stricter than "planted
plans only": every current caller provisions thousands of objects (planted or
not - TC-053-097 imports 2 970 + 2 940 slots), and the helper exists for plans
of that size.
"""

from __future__ import annotations

import ast
import os
import pathlib
import re
import stat
import subprocess
import time

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_E2E = _ROOT / "tests" / "e2e"
_COMPOSE = _ROOT / "docker-compose.e2e.yml"
_ENTRYPOINT = _E2E / "two_pass_entrypoint.sh"
_PROVISIONER = "provision_grid_plan"
_MARKER = "bulk_seed"


# ── (1) every test reaching provision_grid_plan is marked ───────────────────


def _mark_names(decorators: list[ast.expr]) -> set[str]:
    """``pytest.mark.<name>`` names in a decorator list (called or bare)."""
    names: set[str] = set()
    for node in decorators:
        target = node.func if isinstance(node, ast.Call) else node
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Attribute)
            and target.value.attr == "mark"
        ):
            names.add(target.attr)
    return names


def _module_marks(tree: ast.Module) -> set[str]:
    """Marker names of a module-level ``pytestmark`` (single mark or list/tuple)."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets
        ):
            value = node.value
            items = value.elts if isinstance(value, ast.List | ast.Tuple) else [value]
            return _mark_names(items)
    return set()


def _functions(tree: ast.Module) -> list[tuple[ast.FunctionDef, set[str]]]:
    """Every function of the module with the marks its enclosing classes carry."""
    found: list[tuple[ast.FunctionDef, set[str]]] = []

    def visit(body: list[ast.stmt], inherited: set[str]) -> None:
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                found.append((node, inherited))  # type: ignore[arg-type]
            elif isinstance(node, ast.ClassDef):
                visit(node.body, inherited | _mark_names(node.decorator_list))

    visit(tree.body, set())
    return found


def _called_names(function: ast.FunctionDef) -> set[str]:
    return {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def _parameters(function: ast.FunctionDef) -> set[str]:
    args = function.args
    return {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}


def bulk_tests(source: str) -> dict[str, set[str]]:
    """Tests that reach the provisioner -> the marker names they carry (module, class, own).

    A function reaches it when it calls it, calls a module-local function that
    reaches it, or requests a module-local fixture that reaches it.
    """
    tree = ast.parse(source)
    functions = _functions(tree)
    reaching = {_PROVISIONER}
    changed = True
    while changed:
        changed = False
        for function, _marks in functions:
            if function.name in reaching:
                continue
            if _called_names(function) & reaching or _parameters(function) & reaching:
                reaching.add(function.name)
                changed = True
    module_marks = _module_marks(tree)
    return {
        function.name: module_marks | class_marks | _mark_names(function.decorator_list)
        for function, class_marks in functions
        if function.name.startswith("test_") and function.name in reaching
    }


def unmarked_bulk_tests(source: str) -> list[str]:
    """The tests reaching the provisioner that lack ``bulk_seed``."""
    return [name for name, marks in bulk_tests(source).items() if _MARKER not in marks]


def _provisioning_modules() -> list[pathlib.Path]:
    return sorted(
        path
        for path in _E2E.rglob("test_*.py")
        if re.search(rf"\b{_PROVISIONER}\b", path.read_text(encoding="utf-8"))
    )


def test_the_guard_sees_the_known_bulk_seeding_modules() -> None:
    """Non-vacuous: the two modules #3032 measured are found and their bulk tests recognised."""
    names = {path.name for path in _provisioning_modules()}
    assert {"test_req053_renderer_profile.py", "test_req053_wave9_export.py"} <= names, names
    for path in _provisioning_modules():
        assert bulk_tests(path.read_text(encoding="utf-8")), (
            f"{path.name} mentions {_PROVISIONER} but no test reaches it through a call or a "
            "module-local fixture - the guard cannot follow it; extend the analysis."
        )


@pytest.mark.parametrize("path", _provisioning_modules(), ids=lambda path: path.name)
def test_every_test_reaching_provision_grid_plan_runs_in_the_serial_pass(
    path: pathlib.Path,
) -> None:
    unmarked = unmarked_bulk_tests(path.read_text(encoding="utf-8"))
    assert not unmarked, (
        f"{path.name}: {unmarked} provision a grid plan of thousands of objects into the shared "
        f"tenant but carry no @pytest.mark.{_MARKER}. Unmarked, they run in the parallel pass next "
        "to the journeys and starve them (#3032). Mark the test (or the module's pytestmark)."
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "def test_a(x):\n    provision_grid_plan(1, 2, 3)\n",
            ["test_a"],
        ),
        (
            "import pytest\n@pytest.mark.bulk_seed\ndef test_a(x):\n    provision_grid_plan(1, 2, 3)\n",
            [],
        ),
        (
            "import pytest\npytestmark = [pytest.mark.requires_desktop, pytest.mark.bulk_seed]\n"
            "@pytest.fixture\ndef plan():\n    return provision_grid_plan(1, 2, 3)\n"
            "def test_a(plan):\n    pass\n",
            [],
        ),
        (
            "import pytest\n@pytest.fixture\ndef plan():\n    return _helper()\n"
            "def _helper():\n    return provision_grid_plan(1, 2, 3)\n"
            "def test_a(plan):\n    pass\ndef test_b():\n    pass\n",
            ["test_a"],
        ),
        (
            "import pytest\n@pytest.mark.bulk_seed\nclass TestX:\n"
            "    def test_a(self):\n        provision_grid_plan(1, 2, 3)\n",
            [],
        ),
    ],
    ids=["direct-unmarked", "decorated", "module-mark-via-fixture", "via-helper", "class-mark"],
)
def test_the_reachability_analysis(source: str, expected: list[str]) -> None:
    assert unmarked_bulk_tests(source) == expected


def test_the_marker_is_registered() -> None:
    """``--strict-markers`` is on: an unregistered ``bulk_seed`` breaks collection everywhere."""
    conftest = (_E2E / "conftest.py").read_text(encoding="utf-8")
    assert re.search(r'"bulk_seed: ', conftest), "conftest.py must register the bulk_seed marker"


# ── (2) no whole-suite runner on xdist outside the two-pass entrypoint ──────


def _entrypoints() -> dict[str, list[str]]:
    """Service name -> list-form entrypoint of every compose service that has one."""
    services: dict[str, list[str]] = {}
    current: str | None = None
    in_entrypoint = False
    for line in _COMPOSE.read_text(encoding="utf-8").splitlines():
        if service := re.fullmatch(r"  ([a-z0-9-]+):\s*", line):
            current, in_entrypoint = service.group(1), False
            continue
        if re.fullmatch(r"    entrypoint:\s*", line):
            in_entrypoint = True
            services[current or "?"] = []
            continue
        if in_entrypoint:
            if item := re.fullmatch(r"      - (.+?)\s*", line):
                services[current or "?"].append(item.group(1).strip('"'))
            elif line.strip() and not line.lstrip().startswith("#"):
                in_entrypoint = False
    return services


#: The runners #3032 moved to two passes - the suite's parallel profiles.
_TWO_PASS_RUNNERS = {
    "e2e-tests",
    "e2e-tests-full",
    "e2e-tests-mobile",
    "e2e-tests-tablet",
    "e2e-tests-full-mobile",
    "e2e-tests-full-tablet",
}


def test_the_parallel_profile_runners_use_the_two_pass_entrypoint() -> None:
    entrypoints = _entrypoints()
    assert _TWO_PASS_RUNNERS <= set(entrypoints), sorted(entrypoints)
    for name in sorted(_TWO_PASS_RUNNERS):
        command = entrypoints[name]
        assert command[:2] == ["bash", "/app/two_pass_entrypoint.sh"], (name, command)
        stem = command[2]
        assert re.fullmatch(r"junit-[a-z-]+", stem), (
            f"{name}: the JUnit stem {stem!r} must keep the junit-*.xml shape the report steps glob"
        )
        assert "-n" not in command and "-m" not in command, (name, command)


def test_no_runner_runs_the_whole_suite_on_xdist_workers() -> None:
    """A pytest entrypoint with ``-n`` selects by marker, and never a marker the bulk tests carry."""
    bulk_marks: set[str] = set()
    for path in _provisioning_modules():
        for marks in bulk_tests(path.read_text(encoding="utf-8")).values():
            bulk_marks |= marks
        # The REQ axis marker conftest derives from the file name (``-m req053``).
        if req := re.match(r"test_req(\d{3})_", path.name):
            bulk_marks.add(f"req{req.group(1)}")
    # Device/browser gates and parametrize select nothing.
    bulk_marks -= {"requires_desktop", "requires_chrome", "parametrize", _MARKER}
    for name, command in _entrypoints().items():
        if not command or command[0] != "pytest" or "-n" not in command:
            continue
        assert "-m" in command, (
            f"{name} runs the whole suite on xdist workers, bulk_seed tests included (#3032); "
            "use /app/two_pass_entrypoint.sh"
        )
        expression = command[command.index("-m") + 1]
        assert set(re.findall(r"\w+", expression)).isdisjoint(bulk_marks), (
            f"{name}: -m {expression!r} would select a bulk_seed test on xdist workers"
        )


# ── (3) the entrypoint's passes and exit codes ──────────────────────────────

_FAKE_PYTEST = """#!/usr/bin/env bash
n=$(( $(cat "$FAKE_DIR/count" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$FAKE_DIR/count"
printf '%s\\n' "$@" > "$FAKE_DIR/call$n.args"
if [ "$n" = 1 ] && [ -n "${FAKE_MKDIR:-}" ]; then mkdir -p "test-reports/e2e/$FAKE_MKDIR"; fi
read -ra codes <<< "$FAKE_CODES"
exit "${codes[$((n - 1))]}"
"""


def _run(
    tmp_path: pathlib.Path, codes: str, *args: str, mkdir: str = ""
) -> tuple[int, list[list[str]]]:
    fake_dir = tmp_path / "fake"
    fake_dir.mkdir(exist_ok=True)
    fake = fake_dir / "pytest"
    fake.write_text(_FAKE_PYTEST, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    work = tmp_path / "work"
    (work / "test-reports" / "e2e").mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "E2E_PYTEST": str(fake),
        "FAKE_DIR": str(fake_dir),
        "FAKE_CODES": codes,
        "FAKE_MKDIR": mkdir,
    }
    done = subprocess.run(
        ["bash", str(_ENTRYPOINT), "junit-x", *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    calls = sorted(fake_dir.glob("call*.args"))
    return done.returncode, [c.read_text(encoding="utf-8").splitlines() for c in calls]


@pytest.mark.parametrize(
    ("codes", "expected"),
    [
        ("0 0", 0),
        ("1 0", 1),
        ("0 1", 1),
        ("0 5", 0),  # no bulk_seed test selected is not a failure
        ("5 0", 5),  # an empty parallel pass still is, as before the split
        ("1 5", 1),
        ("4 1", 4),
        ("0 2", 2),
    ],
)
def test_both_passes_run_and_their_exit_codes_combine(
    tmp_path: pathlib.Path, codes: str, expected: int
) -> None:
    status, calls = _run(tmp_path, codes, "--tb=short")
    assert len(calls) == 2, "pass 2 must run after any finished pass 1"
    assert status == expected, (codes, status)


@pytest.mark.parametrize("interrupted", ["2", "130", "143"])
def test_an_interrupted_parallel_pass_skips_the_serial_pass(
    tmp_path: pathlib.Path, interrupted: str
) -> None:
    """pytest's 2 (interrupted) or a signal: a stopped run must not go on loading the tenant."""
    status, calls = _run(tmp_path, f"{interrupted} 0", "--tb=short")
    assert len(calls) == 1
    assert status == int(interrupted)


def test_the_passes_select_split_the_suite_and_write_two_junit_files(
    tmp_path: pathlib.Path,
) -> None:
    _status, (parallel, serial) = _run(tmp_path, "0 0", "--tb=short", "--base-url=http://x")
    assert parallel[:6] == ["-n", "4", "--dist=loadfile", "-m", "not bulk_seed",
                            "--junitxml=test-reports/e2e/junit-x.xml"]  # fmt: skip
    assert serial[:3] == ["-m", "bulk_seed", "--junitxml=test-reports/e2e/junit-x-bulk-seed.xml"]
    assert "-n" not in serial
    assert parallel[-2:] == serial[-2:] == ["--tb=short", "--base-url=http://x"]


def test_a_callers_marker_expression_is_combined_not_replaced(tmp_path: pathlib.Path) -> None:
    _status, (parallel, serial) = _run(tmp_path, "0 0", "-m", "req053 or smoke", "--tb=short")
    assert parallel[parallel.index("-m") + 1] == "(req053 or smoke) and not bulk_seed"
    assert serial[serial.index("-m") + 1] == "(req053 or smoke) and bulk_seed"
    assert parallel.count("-m") == serial.count("-m") == 1


def test_pass_two_resumes_the_report_directory_of_pass_one(tmp_path: pathlib.Path) -> None:
    """Older run directories are never picked - only the one pass 1 created."""
    older = tmp_path / "work" / "test-reports" / "e2e" / "29991231_235959"
    older.mkdir(parents=True)
    past = time.time() - 3600
    os.utime(older, (past, past))
    _status, (_parallel, serial) = _run(
        tmp_path, "1 0", "--generate-protocol", mkdir="20261121_120000"
    )
    assert serial[serial.index("--resume") + 1] == "test-reports/e2e/20261121_120000", serial


def test_without_a_report_directory_pass_two_does_not_resume(tmp_path: pathlib.Path) -> None:
    _status, (_parallel, serial) = _run(tmp_path, "0 0", "--generate-protocol")
    assert "--resume" not in serial
