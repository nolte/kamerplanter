"""MT-052 (#2144) — the v0004 stamp audit command: exit codes and output, without a database.

The classification itself runs against a real ArangoDB in
``tests/integration/test_legacy_stamp_audit_reach.py``; this pins the operator surface.
"""

from __future__ import annotations

import pytest

from app.data_access.arango.legacy_stamp_audit import StampAuditReport, StampFinding
from app.migrations import audit_legacy_stamps


class _Audit:
    def __init__(self, report: StampAuditReport | None = None, error: Exception | None = None) -> None:
        self._report = report
        self._error = error

    def measure(self) -> StampAuditReport:
        if self._error is not None:
            raise self._error
        assert self._report is not None
        return self._report


def test_no_never_row_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    report = StampAuditReport(collections_scanned=3, findings=[StampFinding("tasks", "created_by", "member", 4, ["a"])])

    assert audit_legacy_stamps.main([], audit=_Audit(report)) == audit_legacy_stamps.EXIT_OK  # type: ignore[arg-type]
    assert "no sign of a v0004 stamp" in capsys.readouterr().out


def test_never_rows_exit_3_and_are_listed_first(capsys: pytest.CaptureFixture[str]) -> None:
    report = StampAuditReport(
        collections_scanned=2,
        findings=[
            StampFinding("tasks", "created_by", "member", 4, ["a"]),
            StampFinding("sites", "created_by", "never", 2, ["s1", "s2"]),
        ],
    )

    code = audit_legacy_stamps.main(["--dry-run"], audit=_Audit(report))  # type: ignore[arg-type]

    lines = capsys.readouterr().out.splitlines()
    assert code == audit_legacy_stamps.EXIT_FINDINGS
    assert "never" in lines[2] and "s1, s2" in lines[2]


def test_an_empty_measurement_says_so(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit_legacy_stamps.main([], audit=_Audit(StampAuditReport())) == 0  # type: ignore[arg-type]
    assert "Nothing to classify" in capsys.readouterr().out


def test_a_database_error_exits_1_and_names_no_data(capsys: pytest.CaptureFixture[str]) -> None:
    code = audit_legacy_stamps.main([], audit=_Audit(error=ConnectionError("db at 10.0.0.1 refused")))  # type: ignore[arg-type]

    failed = [line for line in capsys.readouterr().out.splitlines() if line.startswith("Failed:")]
    assert code == audit_legacy_stamps.EXIT_ERROR
    assert failed == ["Failed: ConnectionError: nothing was measured, nothing was changed."]


def test_an_out_of_range_sample_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        audit_legacy_stamps.main(["--sample", "99"], audit=_Audit(StampAuditReport()))  # type: ignore[arg-type]
    assert raised.value.code == 2
