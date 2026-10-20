"""REQ-053 WP 6.1 (#2445): every GP-ACC acceptance criterion has a test, and the matrix is the generated one.

The matrix ``spec/e2e-testcases/GP-ACC-matrix.md`` is produced by ``scripts/gp_acc_matrix.py`` from the tests, never
by hand. Two rules, both measured against the live tree:

* (a) a criterion of the spec (section 30) without any test fails, unless ``GP-ACC-gaps.json`` lists it with a reason
  and a tracking issue (and a listed id that has gained a test must leave the list);
* (b) the committed matrix equals the regenerated one - a stale matrix fails.
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
