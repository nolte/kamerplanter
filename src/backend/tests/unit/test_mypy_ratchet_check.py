"""Tests for the backend mypy ratchet (``scripts/check_mypy_ratchet.py``, #2169).

**What is under test.** The parser, the two comparison rules, the baseline
format and — in :class:`TestAgainstRealMypy` — the whole gate driven against a
constructed package in ``tmp_path`` with the real mypy. Never against the real
``src/backend/app`` tree: that is the ``mypy ratchet`` step of Backend CI, and a
test that asserted "app has 3442 findings" would teach nobody anything.

**The negative controls NFR-018 §2 asks for.** Each rule has a case in which the
gate is demonstrably red: a new ``[call-arg]`` (the #2150 class) in an otherwise
recorded package, a finding in a file the baseline does not know, a fixed
exact-match finding whose entry was not lowered, a baseline entry for a deleted
file, a mypy summary that disagrees with the parsed lines, a crash.

The script lives outside the backend package, so it is loaded **by path**, the
same mechanism ``test_schema_example_ratchet.py`` uses.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise AssertionError(f"no checkout root above {start}")


def _load(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None, f"{path} is not loadable"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
ratchet = _load("_mypy_ratchet_under_test", _REPO_ROOT / "scripts" / "check_mypy_ratchet.py")


def _always(_: str) -> bool:
    return True


def _finding_line(path: str, line: int, code: str, message: str = "Something is wrong") -> str:
    return f"{path}:{line}: error: {message}  [{code}]"


# ── Parsing ──────────────────────────────────────────────────────────────────


class TestParse:
    def test_findings_and_summary(self):
        output = "\n".join(
            [
                _finding_line("app/a.py", 3, "call-arg", 'Unexpected keyword argument "x" for "f"'),
                'app/a.py:3: note: "f" defined here',
                _finding_line("app/b.py", 9, "union-attr"),
                "Found 2 errors in 2 files (checked 5 source files)",
            ]
        )
        findings, checked = ratchet.parse_mypy_output(output)
        assert checked == 5
        assert [(f.path, f.line, f.code) for f in findings] == [
            ("app/a.py", 3, "call-arg"),
            ("app/b.py", 9, "union-attr"),
        ]

    def test_clean_run(self):
        findings, checked = ratchet.parse_mypy_output("Success: no issues found in 7 source files\n")
        assert findings == [] and checked == 7

    def test_column_numbers_are_tolerated(self):
        findings, _ = ratchet.parse_mypy_output(
            "app/a.py:3:5: error: Bad  [arg-type]\nFound 1 error in 1 file (checked 1 source file)\n"
        )
        assert findings[0].code == "arg-type"

    def test_missing_summary_is_not_zero_findings(self):
        with pytest.raises(ratchet.RatchetError, match="no summary"):
            ratchet.parse_mypy_output(_finding_line("app/a.py", 1, "call-arg"))

    def test_summary_disagreeing_with_parsed_lines_is_red(self):
        # A format the parser no longer understands must not read as "fewer findings".
        output = "app/a.py:1: error: Bad (code moved)\nFound 1 error in 1 file (checked 1 source file)\n"
        with pytest.raises(ratchet.RatchetError, match="reports 1 errors but 0 were parsed"):
            ratchet.parse_mypy_output(output)

    def test_zero_checked_files_is_red(self):
        with pytest.raises(ratchet.RatchetError, match="0 source files"):
            ratchet.parse_mypy_output("Success: no issues found in 0 source files\n")


# ── Comparing ────────────────────────────────────────────────────────────────


class TestCompare:
    def test_equal_counts_are_green(self):
        counts = {("app/a.py", "call-arg"): 2, ("app/a.py", "union-attr"): 5}
        assert not ratchet.compare(counts, counts, _always).red

    def test_growth_in_a_recorded_file_is_red(self):
        verdict = ratchet.compare({("app/a.py", "union-attr"): 6}, {("app/a.py", "union-attr"): 5}, _always)
        assert verdict.red and verdict.growth == [(("app/a.py", "union-attr"), 5, 6)]

    def test_a_file_without_entry_is_held_to_zero(self):
        verdict = ratchet.compare({("app/new_module.py", "type-arg"): 1}, {}, _always)
        assert verdict.red and verdict.growth == [(("app/new_module.py", "type-arg"), 0, 1)]

    def test_a_new_code_in_a_recorded_file_is_red(self):
        verdict = ratchet.compare(
            {("app/a.py", "union-attr"): 5, ("app/a.py", "call-arg"): 1}, {("app/a.py", "union-attr"): 5}, _always
        )
        assert verdict.red and [g[0] for g in verdict.growth] == [("app/a.py", "call-arg")]

    def test_a_drop_of_an_ordinary_code_is_green_headroom(self):
        verdict = ratchet.compare({("app/a.py", "union-attr"): 2}, {("app/a.py", "union-attr"): 5}, _always)
        assert not verdict.red and verdict.headroom == [(("app/a.py", "union-attr"), 5, 2)]

    @pytest.mark.parametrize("code", sorted(ratchet.EXACT_CODES))
    def test_a_drop_of_an_exact_code_is_red_until_tightened(self, code):
        verdict = ratchet.compare({}, {("app/a.py", code): 1}, _always)
        assert verdict.red and verdict.stale == [(("app/a.py", code), 1, 0)]

    def test_a_baseline_entry_for_a_deleted_file_is_red(self):
        verdict = ratchet.compare({}, {("app/gone.py", "union-attr"): 3}, lambda path: path != "app/gone.py")
        assert verdict.red and verdict.missing_files == ["app/gone.py"]

    def test_call_arg_is_an_exact_code(self):
        # #2150: the class that hid six never-running retention tasks. Operator
        # decision on #2169 — the gate MUST cover it with the strict rule.
        assert "call-arg" in ratchet.EXACT_CODES


# ── Baseline file ────────────────────────────────────────────────────────────


class TestBaselineFile:
    def test_round_trip(self, tmp_path):
        counts = {("app/b.py", "union-attr"): 3, ("app/a.py", "call-arg"): 1}
        path = tmp_path / "baseline.json"
        path.write_text(ratchet.dump_baseline(counts, "9.9.9"), encoding="utf-8")
        loaded = ratchet.load_baseline(path)
        assert dict(loaded.counts) == counts and loaded.mypy_version == "9.9.9"
        assert json.loads(path.read_text())["total"] == 4

    def test_missing_file_is_an_error_not_an_empty_baseline(self, tmp_path):
        with pytest.raises(ratchet.RatchetError, match="missing"):
            ratchet.load_baseline(tmp_path / "absent.json")

    @pytest.mark.parametrize(
        "payload",
        [
            {"files": {}},
            {"format": 1},
            {"format": 1, "files": {"app/a.py": {"call-arg": 0}}},
            {"format": 1, "files": {"app/a.py": {"call-arg": True}}},
            {"format": 1, "files": {"app/a.py": {}}},
        ],
    )
    def test_malformed_baseline_is_an_error(self, tmp_path, payload):
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ratchet.RatchetError):
            ratchet.load_baseline(path)

    def test_tighten_lowers_and_drops_but_never_raises_or_adds(self):
        baseline = {("app/a.py", "union-attr"): 5, ("app/a.py", "call-arg"): 2, ("app/gone.py", "type-arg"): 1}
        current = {("app/a.py", "union-attr"): 7, ("app/a.py", "call-arg"): 0, ("app/new.py", "type-arg"): 4}
        lowered = ratchet.tighten(baseline, current, lambda path: path != "app/gone.py")
        assert lowered == {("app/a.py", "union-attr"): 5}

    def test_committed_baseline_is_well_formed_and_names_existing_files(self):
        backend = _REPO_ROOT / "src" / "backend"
        baseline = ratchet.load_baseline(backend / ratchet.BASELINE_NAME)
        assert baseline.counts, "an empty committed baseline would hold app/ to zero findings"
        missing = sorted({path for path, _ in baseline.counts if not (backend / path).is_file()})
        assert missing == [], f"baseline entries for files that no longer exist: {missing}"


# ── The whole gate, real mypy ────────────────────────────────────────────────


_CLEAN = textwrap.dedent(
    """
    def greet(name: str) -> str:
        return "hello " + name


    def caller() -> str:
        return greet("x")
    """
)


def _package(tmp_path: Path, source: str) -> Path:
    backend = tmp_path / "backend"
    (backend / "app").mkdir(parents=True, exist_ok=True)
    (backend / "pyproject.toml").write_text('[tool.mypy]\nstrict = true\npython_version = "3.14"\n', encoding="utf-8")
    (backend / "app" / "__init__.py").write_text("", encoding="utf-8")
    (backend / "app" / "mod.py").write_text(source, encoding="utf-8")
    return backend


def _run(backend: Path, *extra: str) -> int:
    return ratchet.main(["--backend-dir", str(backend), *extra])


class TestAgainstRealMypy:
    """The falsification of the gate itself (NFR-018 §2): red on the #2150 class."""

    def test_new_call_arg_is_red_and_its_fix_is_green(self, tmp_path, capsys):
        backend = _package(tmp_path, _CLEAN)
        assert _run(backend, "--record") == 0
        assert _run(backend) == 0

        # The #2150 shape: a call passing a keyword the callee does not accept.
        (backend / "app" / "mod.py").write_text(_CLEAN.replace('greet("x")', 'greet("x", tenant_key="t")'))
        capsys.readouterr()
        assert _run(backend) == 1
        out = capsys.readouterr().out
        assert "app/mod.py [call-arg]: 0 -> 1" in out
        assert 'Unexpected keyword argument "tenant_key"' in out

        (backend / "app" / "mod.py").write_text(_CLEAN)
        assert _run(backend) == 0

    def test_fixed_exact_finding_is_red_until_tightened(self, tmp_path, capsys):
        backend = _package(tmp_path, _CLEAN.replace('greet("x")', "greet()"))
        assert _run(backend, "--record") == 0
        (backend / "app" / "mod.py").write_text(_CLEAN)
        capsys.readouterr()
        assert _run(backend) == 1
        assert "app/mod.py [call-arg]: 1 -> 0" in capsys.readouterr().out
        assert _run(backend, "--tighten") == 0
        assert _run(backend) == 0

    def test_a_blocking_mypy_error_is_not_a_pass(self, tmp_path):
        backend = _package(tmp_path, _CLEAN)
        assert _run(backend, "--record") == 0
        (backend / "app" / "mod.py").write_text("def broken(:\n")
        assert _run(backend) == ratchet.EXIT_USAGE

    def test_a_missing_target_is_not_a_pass(self, tmp_path):
        assert _run(tmp_path) == ratchet.EXIT_USAGE
