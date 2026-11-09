"""REQ-053 WP 6.1 (#2445): every GP-ACC acceptance criterion has a test, and the matrix is the generated one.

The matrix ``spec/e2e-testcases/GP-ACC-matrix.md`` is produced by ``scripts/gp_acc_matrix.py`` from the tests, never
by hand. Two rules, both measured against the live tree:

* (a) a criterion of the spec (section 30) without any test fails, unless ``GP-ACC-gaps.json`` lists it with a reason
  and a tracking issue (and a listed id that has gained a test must leave the list);
* (b) the committed matrix equals the regenerated one - a stale matrix fails.

Wave 7 (WP 7.27, #2493) adds the same two rules for the SHOULD rows of wave 7 (GP-FR / GP-API / GP-UX, listed in
``WAVE7_ROWS``) against ``spec/e2e-testcases/GP-REQ-wave7-matrix.md`` and ``GP-REQ-wave7-gaps.json``; a gap there is
either full (no test) or ``partial`` (tests exist, a named part of the row is unproven).

Wave 8 (WP 8.32, #2675) adds them a third time for the rows of wave 8 (``WAVE8_ROWS``, now with GP-NFR rows) against
``spec/e2e-testcases/GP-REQ-wave8-matrix.md`` and ``GP-REQ-wave8-gaps.json``.

Wave 9 (WP 9.17, #2757) adds them a fourth time for the REQ-053 rows of wave 9 (``WAVE9_ROWS``) and the UI-NFR-012
requirements wave 9 implements (``WAVE9_UINFR_ROWS``) against ``spec/e2e-testcases/GP-REQ-wave9-matrix.md`` and
``GP-REQ-wave9-gaps.json``. A UI-NFR-012 id counts only in a file that names UI-NFR-012 (the REQ documents have R-ids of
their own), and the matrix lists the TC-053 E2E functions per row.
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


def test_every_wave8_row_is_a_row_of_the_spec(matrix) -> None:
    rows = matrix.spec_rows()
    missing = [row for row in matrix.WAVE8_ROWS if row not in rows]
    assert missing == []


def test_the_spec_rows_include_the_nfr_table(matrix) -> None:
    rows = matrix.spec_rows()
    assert rows.get("GP-NFR-015") == "MUST" and rows.get("GP-NFR-072") == "SHOULD"


def test_every_wave8_row_has_a_test_or_a_reviewed_gap(matrix) -> None:
    errors = matrix.wave8_problems(matrix.spec_rows(), matrix.scan_rows(), matrix.load_wave8_gaps())
    assert errors == []


def test_the_committed_wave8_matrix_is_the_generated_one(matrix) -> None:
    expected = matrix.render_wave8(matrix.spec_rows(), matrix.scan_rows(), matrix.load_wave8_gaps())
    assert matrix.WAVE8_MATRIX.read_text(encoding="utf-8") == expected, "run: python3 scripts/gp_acc_matrix.py --write"


def test_a_wave8_row_without_a_test_is_reported_against_the_wave8_gap_file(matrix) -> None:
    row = "GP-NFR-063"
    rows = dict.fromkeys(matrix.WAVE8_ROWS, "SHOULD")
    found = {r: {"unit": {"a"}} for r in matrix.WAVE8_ROWS if r != row}
    errors = matrix.wave8_problems(rows, found, {})
    assert errors == [f"{row}: no test references it and it is not in GP-REQ-wave8-gaps.json"]


def test_a_wave8_gap_for_a_row_of_another_wave_is_reported(matrix) -> None:
    rows = dict.fromkeys(matrix.WAVE8_ROWS, "SHOULD")
    found = {r: {"unit": {"a"}} for r in matrix.WAVE8_ROWS}
    errors = matrix.wave8_problems(rows, found, {"GP-FR-117": {"reason": "r", "issue": 1, "partial": True}})
    assert any("GP-FR-117" in e and "not a wave-8 row" in e for e in errors)


def test_an_nfr_id_in_a_test_is_scanned(matrix, tmp_path, monkeypatch) -> None:
    probe = tmp_path / "tests" / "e2e" / "test_probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text('"""Measures GP-NFR-071."""\n', encoding="utf-8")
    monkeypatch.setattr(matrix, "ROOT", tmp_path)
    assert matrix.scan_rows() == {"GP-NFR-071": {"e2e": {"tests/e2e/test_probe.py"}}}


def test_a_longer_number_or_a_following_date_is_no_claim(matrix, tmp_path, monkeypatch) -> None:
    probe = tmp_path / "src" / "backend" / "tests" / "unit" / "test_probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text('"""GP-NFR-0151, XGP-FR-100, GP-FR-105/2026-11 and GP-FR-158/159."""\n', encoding="utf-8")
    monkeypatch.setattr(matrix, "ROOT", tmp_path)
    assert set(matrix.scan_rows()) == {"GP-FR-105", "GP-FR-158", "GP-FR-159"}


def test_no_test_claims_a_row_the_spec_does_not_have(matrix) -> None:
    assert matrix.stray_rows(matrix.spec_rows(), matrix.scan_rows()) == []


def test_a_claimed_id_outside_the_spec_is_reported(matrix) -> None:
    errors = matrix.stray_rows({"GP-FR-001": "MUST"}, {"GP-FR-999": {"unit": {"a.py"}}})
    assert errors == ["GP-FR-999: referenced by a.py but not a row of the spec"]


def test_every_wave9_row_is_a_row_of_its_spec(matrix) -> None:
    rows = matrix.wave9_spec_rows()
    missing = [row for row in matrix.wave9_rows() if row not in rows]
    assert missing == []


def test_the_ui_nfr_012_table_is_read_with_its_priority(matrix) -> None:
    rows = matrix.uinfr_rows()
    assert rows.get("UI-NFR-012 R-057") == "MUSS" and rows.get("UI-NFR-012 R-019") == "SOLL"
    assert "UI-NFR-012 R-020a" in rows


def test_every_wave9_row_has_a_test_or_a_reviewed_gap(matrix) -> None:
    errors = matrix.wave9_problems(matrix.wave9_spec_rows(), matrix.scan_wave9(), matrix.load_wave9_gaps())
    assert errors == []


def test_the_committed_wave9_matrix_is_the_generated_one(matrix) -> None:
    expected = matrix.render_wave9(
        matrix.wave9_spec_rows(), matrix.scan_wave9(), matrix.load_wave9_gaps(), matrix.scan_e2e_tcs()
    )
    assert matrix.WAVE9_MATRIX.read_text(encoding="utf-8") == expected, "run: python3 scripts/gp_acc_matrix.py --write"


def test_a_wave9_ui_nfr_row_without_a_test_is_reported_against_the_wave9_gap_file(matrix) -> None:
    row = "UI-NFR-012 R-057"
    rows = dict.fromkeys(matrix.wave9_rows(), "MUSS")
    found = {r: {"frontend": {"a"}} for r in matrix.wave9_rows() if r != row}
    errors = matrix.wave9_problems(rows, found, {})
    assert errors == [f"{row}: no test references it and it is not in GP-REQ-wave9-gaps.json"]


def test_a_ui_nfr_id_counts_only_in_a_file_that_names_ui_nfr_012(matrix, tmp_path, monkeypatch) -> None:
    claims = tmp_path / "src" / "frontend" / "src" / "a.test.ts"
    noise = tmp_path / "src" / "frontend" / "src" / "b.test.ts"
    claims.parent.mkdir(parents=True)
    claims.write_text("// UI-NFR-012 R-021…R-023, R-043/044 and R-057\n", encoding="utf-8")
    noise.write_text("// REQ-053 R-057 is a research id, UI-NFR-0120 R-001 nothing\n", encoding="utf-8")
    monkeypatch.setattr(matrix, "ROOT", tmp_path)
    found = matrix.scan_uinfr_rows()
    assert set(found) == {f"UI-NFR-012 R-{n}" for n in ("021", "022", "023", "043", "044", "057")}
    assert found["UI-NFR-012 R-022"] == {"frontend": {"src/frontend/src/a.test.ts"}}


def test_the_name_ui_nfr_012_itself_claims_no_r_012(matrix) -> None:
    assert matrix.uinfr_ids("UI-NFR-012 basis, see UI-NFR-012 section 3.2") == set()


def test_the_e2e_tc_column_reads_the_function_that_names_the_row(matrix, tmp_path, monkeypatch) -> None:
    probe = tmp_path / "tests" / "e2e" / "test_probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text(
        '"""UI-NFR-012 offline suite."""\n\n'
        'def test_tc_053_084_worker(driver):\n    """R-007, GP-UX-024."""\n\n\n'
        'def _helper():\n    return "GP-FR-144"\n\n\n'
        'def test_tc_053_091_png(driver):\n    """GP-FR-144."""\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(matrix, "ROOT", tmp_path)
    assert matrix.scan_e2e_tcs() == {
        "UI-NFR-012 R-007": {"084"},
        "GP-UX-024": {"084"},
        "GP-FR-144": {"091"},
    }
