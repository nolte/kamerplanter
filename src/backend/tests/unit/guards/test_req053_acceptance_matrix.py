"""REQ-053 WP 6.1 (#2445): every GP-ACC acceptance criterion has a test, and the matrix is the generated one.

The matrix ``spec/e2e-testcases/GP-ACC-matrix.md`` is produced by ``scripts/gp_acc_matrix.py`` from the tests, never
by hand. Two rules, both measured against the live tree:

* (a) a criterion of the spec (section 30) without any test fails, unless ``GP-ACC-gaps.json`` lists it with a reason
  and a tracking issue (and a listed id that has gained a test must leave the list);
* (b) the committed matrix equals the regenerated one - a stale matrix fails.

Wave 7 (WP 7.27, #2493) adds the same two rules for the SHOULD rows of wave 7 (GP-FR / GP-API / GP-UX, listed in
``WAVE7_ROWS``) against ``spec/e2e-testcases/GP-REQ-wave7-matrix.md`` and ``GP-REQ-wave7-gaps.json``; a gap there is
either full (no test) or ``partial`` (tests exist, a named part of the row is unproven).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[5] / "scripts" / "gp_acc_matrix.py"


@pytest.fixture(scope="module")
def matrix():
    spec = importlib.util.spec_from_file_location("gp_acc_matrix", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gp_acc_matrix"] = module
    spec.loader.exec_module(module)
    return module


def test_the_spec_lists_the_acceptance_criteria(matrix) -> None:
    ids = matrix.spec_ids()
    assert len(ids) >= 52 and "001" in ids and "052" in ids


def test_every_acceptance_criterion_has_a_test_or_a_reviewed_gap(matrix) -> None:
    errors = matrix.problems(matrix.spec_ids(), matrix.scan(), matrix.load_gaps())
    assert errors == []


def test_the_committed_matrix_is_the_generated_one(matrix) -> None:
    expected = matrix.render(matrix.spec_ids(), matrix.scan(), matrix.load_gaps())
    assert matrix.MATRIX.read_text(encoding="utf-8") == expected, "run: python3 scripts/gp_acc_matrix.py --write"


def test_a_criterion_without_a_test_is_reported(matrix) -> None:
    errors = matrix.problems({"001": "I", "999": "I"}, {"001": {"unit": {"a"}}}, {})
    assert errors == ["GP-ACC-999: no test references it and it is not in GP-ACC-gaps.json"]


def test_a_gap_entry_that_gained_a_test_must_go(matrix) -> None:
    errors = matrix.problems({"001": "I"}, {"001": {"unit": {"a"}}}, {"001": {"reason": "r", "issue": 1}})
    assert errors and "remove the entry" in errors[0]


def test_every_wave7_row_is_a_row_of_the_spec(matrix) -> None:
    rows = matrix.spec_rows()
    missing = [row for row in matrix.WAVE7_ROWS if row not in rows]
    assert missing == []


def test_every_wave7_row_has_a_test_or_a_reviewed_gap(matrix) -> None:
    errors = matrix.wave7_problems(matrix.spec_rows(), matrix.scan_rows(), matrix.load_wave7_gaps())
    assert errors == []


def test_the_committed_wave7_matrix_is_the_generated_one(matrix) -> None:
    expected = matrix.render_wave7(matrix.spec_rows(), matrix.scan_rows(), matrix.load_wave7_gaps())
    assert matrix.WAVE7_MATRIX.read_text(encoding="utf-8") == expected, "run: python3 scripts/gp_acc_matrix.py --write"


def test_a_wave7_row_without_a_test_is_reported(matrix) -> None:
    row = next(iter(matrix.WAVE7_ROWS))
    rows = dict.fromkeys(matrix.WAVE7_ROWS, "SHOULD")
    found = {r: {"unit": {"a"}} for r in matrix.WAVE7_ROWS if r != row}
    errors = matrix.wave7_problems(rows, found, {})
    assert errors == [f"{row}: no test references it and it is not in GP-REQ-wave7-gaps.json"]


def test_a_full_gap_that_gained_a_test_must_go_and_a_partial_gap_needs_a_test(matrix) -> None:
    rows = dict.fromkeys(matrix.WAVE7_ROWS, "SHOULD")
    tested, untested = list(matrix.WAVE7_ROWS)[:2]
    found = {r: {"unit": {"a"}} for r in matrix.WAVE7_ROWS if r != untested}
    gaps = {
        tested: {"reason": "r", "issue": 1},
        untested: {"reason": "r", "issue": 1, "partial": True},
    }
    errors = matrix.wave7_problems(rows, found, gaps)
    assert any(tested in e and "remove it or mark it partial" in e for e in errors)
    assert any(untested in e and "it is a full gap" in e for e in errors)


def test_the_shorthand_counts_for_each_number(matrix, tmp_path, monkeypatch) -> None:
    probe = tmp_path / "src" / "backend" / "tests" / "unit" / "test_probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text('"""Covers GP-FR-158/159 and GP-API-052."""\n', encoding="utf-8")
    monkeypatch.setattr(matrix, "ROOT", tmp_path)
    found = matrix.scan_rows()
    assert set(found) == {"GP-FR-158", "GP-FR-159", "GP-API-052"}
    assert found["GP-FR-159"] == {"unit": {"src/backend/tests/unit/test_probe.py"}}
