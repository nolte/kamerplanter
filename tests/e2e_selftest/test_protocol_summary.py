"""Browser-free checks for the protocol's run-summary reporting (#778 A6).

The protocol is how a run is read afterwards, so what it omits is invisible to
everyone. Two omissions mattered:

* a single "übersprungen" total cannot distinguish 98 structural light-mode
  skips from one class that silently stopped running;
* xfail and xpass were folded into skipped/passed, so a profile reported green
  with 34 xpasses looked identical to one green with none — and a marker that
  keeps xpassing is a marker that should be removed.

These run against the generator directly: no browser, no Grid, no stack.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_PLUGIN = Path(__file__).resolve().parents[1] / "e2e" / "protocol_plugin.py"


def _load_plugin():
    """Import ``protocol_plugin`` by path, the way the traceability script does.

    ``tests/e2e`` is not an importable package from here (its ``conftest``
    pulls in Selenium), so the module is loaded standalone.
    """
    spec = importlib.util.spec_from_file_location("_protocol_plugin", _PLUGIN)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_protocol_plugin"] = module
    spec.loader.exec_module(module)
    return module


plugin = _load_plugin()


def _result(nodeid: str, outcome: str):
    return plugin.TestResult(nodeid=nodeid, outcome=outcome, duration=0.1)


@pytest.fixture
def generator():
    gen = plugin.ProtocolGenerator()
    gen.start_time = None
    return gen


def _render(gen, tmp_path: Path) -> str:
    return (gen.generate(tmp_path)).read_text(encoding="utf-8")


def test_summary_counts_xfail_and_xpass_separately(generator, tmp_path):
    # Distinct nodeids so nothing is deduplicated by accident.
    generator.results = [
        _result("tests/e2e/test_req001_a.py::T::test_1", "passed"),
        _result("tests/e2e/test_req001_a.py::T::test_2", "passed"),
        _result("tests/e2e/test_req001_a.py::T::test_3", "failed"),
        _result("tests/e2e/test_req001_a.py::T::test_4", "skipped"),
        _result("tests/e2e/test_req002_b.py::T::test_5", "xfailed"),
        _result("tests/e2e/test_req002_b.py::T::test_6", "xpassed"),
        _result("tests/e2e/test_req002_b.py::T::test_7", "xpassed"),
    ]

    text = _render(generator, tmp_path)

    # 7 total: 2 passed, 1 failed, 1 skipped, 1 xfailed, 2 xpassed. Folding the
    # last three into pass/skip is what made an xpassing marker invisible.
    assert "| 7 | 2 | 1 | 1 | 1 | 2 |" in text
    assert "XFail" in text and "XPass" in text


def test_summary_breaks_skips_down_per_file(generator, tmp_path):
    generator.results = [
        _result("tests/e2e/test_req001_a.py::T::test_1", "skipped"),
        _result("tests/e2e/test_req001_a.py::T::test_2", "skipped"),
        _result("tests/e2e/test_req001_a.py::T::test_3", "passed"),
        _result("tests/e2e/test_req002_b.py::T::test_4", "skipped"),
        _result("tests/e2e/test_req002_b.py::T::test_5", "passed"),
    ]

    text = _render(generator, tmp_path)

    assert "### Übersprungene Tests je Datei" in text
    # Ordered by skip count descending, so the class that stopped running is at
    # the top rather than buried alphabetically.
    a_line = "| `tests/e2e/test_req001_a.py` | 2 | 3 |"
    b_line = "| `tests/e2e/test_req002_b.py` | 1 | 2 |"
    assert a_line in text
    assert b_line in text
    assert text.index(a_line) < text.index(b_line)


def test_no_skip_table_when_nothing_was_skipped(generator, tmp_path):
    generator.results = [_result("tests/e2e/test_req001_a.py::T::test_1", "passed")]

    text = _render(generator, tmp_path)

    # The section is a finding aid, not decoration — an all-green run should not
    # carry an empty table.
    assert "### Übersprungene Tests je Datei" not in text


def test_outcome_labels_cover_the_expected_failure_states(generator):
    label = plugin.ProtocolGenerator._outcome_icon
    assert label("xfailed") == "XFAIL"
    assert label("xpassed") == "XPASS"
    # The pre-existing three keep their labels: the protocol is read by humans
    # comparing runs across the campaign's archive.
    assert label("passed") == "PASS"
    assert label("failed") == "FAIL"
    assert label("skipped") == "SKIP"
