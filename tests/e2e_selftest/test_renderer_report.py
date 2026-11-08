"""Browser-free self-test of the renderer measurement report (REQ-053 WP 9.6, D-01).

The measurement needs a browser; the report does not. Pinned here: the records are read from both channels the
test writes (JUnit property, JSON sidecar), the latest record per case and profile wins, and the Go/No-Go follows
D-01 - a measured violation is a Go, a missing record or an un-throttled mobile run leaves the decision open
instead of reading as No-Go, and the synthetic case's object count is its premise, not a finding.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

import pytest

from tests.e2e import _renderer_report as report


def _record(
    case="large",
    profile="desktop",
    *,
    drag_p95=16.7,
    visible=500,
    throttle=None,
    at="2026-11-08T10:00",
):
    return {
        "schema": report.RECORD_SCHEMA,
        "case": case,
        "profile": profile,
        "cpu_slowdown": 4 if profile == "mobile" else 1,
        "throttle": throttle or ("applied" if profile == "mobile" else "off"),
        "viewport": [390, 844] if profile == "mobile" else [1920, 1080],
        "budget_ms": 33 if profile == "mobile" else 16,
        "vsync_ms": 16.7,
        "plan": {"beds": 250, "slots": 5000, "plants": 5000},
        "census_fit": {"visible_objects": visible, "beds": 250},
        "census_zoomed": {"visible_objects": visible // 2, "beds": 40},
        "px_per_m_fit": 21.6,
        "px_per_m_zoomed": 130.0,
        "gestures": [
            {
                "name": "zoom_in",
                "frame_budget_ms": 16,
                "vsync_ms": 16.7,
                "frames": 50,
                "frame_p95_ms": 16.7,
                "frame_max_ms": 20.0,
                "exceeded": [],
            },
            {
                "name": "drag",
                "frame_budget_ms": 33 if profile == "mobile" else 16,
                "frames": 40,
                "frame_p95_ms": drag_p95,
                "frame_max_ms": 40.0,
                "vsync_ms": 16.7,
                "exceeded": [],
            },
        ],
        "recorded_at": at,
    }


def _complete(overrides: dict | None = None):
    """One record per case and profile; *overrides* maps ``(case, profile)`` to ``_record`` keywords."""
    changes = overrides or {}
    return [
        _record(case, profile, **changes.get((case, profile), {}))
        for case in report.CASES
        for profile in report.PROFILES
    ]


def test_a_complete_measurement_without_a_violation_is_no_go() -> None:
    literal, mobile = report.decide(_complete())
    assert (literal.verdict, mobile.verdict) == ("No-Go", "No-Go")
    assert literal.reasons == [] and literal.gaps == []


def test_a_drag_over_16_ms_is_a_go_on_any_profile() -> None:
    literal, mobile = report.decide(_complete({("large", "desktop"): {"drag_p95": 33.3}}))
    assert literal.verdict == "Go" and "large/desktop" in literal.reasons[0]
    # The placeholder reading looks at the mobile profile only.
    assert mobile.verdict == "No-Go"


def test_a_mobile_violation_is_a_go_in_both_readings() -> None:
    literal, mobile = report.decide(_complete({("synthetic_3000", "mobile"): {"drag_p95": 50.0}}))
    assert (literal.verdict, mobile.verdict) == ("Go", "Go")


def test_the_object_count_counts_for_the_large_class_only() -> None:
    literal, _ = report.decide(_complete({("synthetic_3000", "desktop"): {"visible": 3000 + 150}}))
    assert literal.verdict == "No-Go", (
        "the synthetic plan is built at the threshold; its count is no finding"
    )
    literal, _ = report.decide(_complete({("large", "desktop"): {"visible": 3001}}))
    assert literal.verdict == "Go" and "3001 sichtbare Objekte" in literal.reasons[0]


def test_a_missing_record_leaves_the_decision_open() -> None:
    records = [r for r in _complete() if (r["case"], r["profile"]) != ("large", "mobile")]
    literal, mobile = report.decide(records)
    assert (literal.verdict, mobile.verdict) == ("offen", "offen")
    assert any("large/mobile" in gap for gap in literal.gaps)


def test_an_unthrottled_mobile_run_does_not_count_as_the_mobile_profile() -> None:
    literal, mobile = report.decide(_complete({("large", "mobile"): {"throttle": "unavailable"}}))
    assert literal.verdict == "offen" and mobile.verdict == "offen"


def test_a_violation_wins_over_a_gap() -> None:
    records = [
        r
        for r in _complete({("large", "desktop"): {"drag_p95": 40.0}})
        if r["profile"] == "desktop"
    ]
    literal, _ = report.decide(records)
    assert literal.verdict == "Go" and literal.gaps


def test_both_channels_are_read_and_the_latest_record_wins(tmp_path: Path) -> None:
    old = _record(at="2026-11-07T10:00", drag_p95=50.0)
    new = _record(at="2026-11-08T10:00", drag_p95=16.7)
    (tmp_path / f"{report.RECORD_FILE_PREFIX}large-desktop.json").write_text(
        json.dumps(old), encoding="utf-8"
    )
    junit = tmp_path / "junit-default.xml"
    junit.write_text(
        "<testsuites><testsuite><testcase name='t'><properties>"
        f"<property name='tc_id' value='TC-053-083'/>"
        f"<property name={quoteattr(report.RECORD_PROPERTY)} value={quoteattr(json.dumps(new))}/>"
        "</properties></testcase></testsuite></testsuites>",
        encoding="utf-8",
    )
    records, sources = report.load_records([tmp_path])
    assert len(records) == 1 and records[0]["recorded_at"] == "2026-11-08T10:00"
    assert sorted(path.name for path in sources) == sorted(
        [f"{report.RECORD_FILE_PREFIX}large-desktop.json", "junit-default.xml"]
    )


def test_the_report_names_the_verdict_every_case_and_the_gaps(tmp_path: Path) -> None:
    records = [r for r in _complete() if r["case"] == "large"]
    text = report.render(records, date="2026-11-08", sources=[tmp_path / "junit.xml"])
    assert "# Renderer-Messung D-01 — 2026-11-08" in text
    assert "**Go/No-Go für WP 9.7 (D-01 wörtlich):** offen" in text
    assert text.count("| drag |") == 2 and "synthetic_3000/desktop: keine Messung" in text


def test_the_cli_writes_the_report_and_refuses_an_empty_input(tmp_path: Path) -> None:
    (tmp_path / f"{report.RECORD_FILE_PREFIX}large-desktop.json").write_text(
        json.dumps(_record()), encoding="utf-8"
    )
    target = tmp_path / "out" / "renderer-measurement.md"
    assert report.main([str(tmp_path), "--output", str(target), "--date", "2026-11-08"]) == 0
    assert "2026-11-08" in target.read_text(encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    assert report.main([str(empty), "--output", "-"]) == 1
    assert report.main([str(empty), "--output", "-", "--allow-empty"]) == 0


def test_a_record_of_another_schema_is_refused(tmp_path: Path) -> None:
    (tmp_path / f"{report.RECORD_FILE_PREFIX}x.json").write_text(
        json.dumps({**_record(), "schema": 99}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="schema 99"):
        report.load_records([tmp_path])


def test_the_tolerance_mirrors_the_probe() -> None:
    from tests.e2e._inp_probe import VSYNC_TOLERANCE

    assert report.VSYNC_TOLERANCE == VSYNC_TOLERANCE


def test_the_budget_column_holds_each_gesture_against_its_own_budget() -> None:
    records = _complete(
        {("large", "mobile"): {"drag_p95": 33.3}, ("large", "desktop"): {"drag_p95": 33.3}}
    )
    text = report.render(records, date="2026-11-08", sources=[])
    rows = [line for line in text.splitlines() if "| drag |" in line and "Klasse" in line]
    desktop, mobile = rows
    assert desktop.endswith("| über Budget |"), (
        "33.3 ms is one dropped frame on the 16 ms laptop budget"
    )
    assert mobile.endswith("| im Budget |"), (
        "33.3 ms is within the phone's 33 ms (+ refresh tolerance)"
    )


def test_the_report_says_the_phone_cannot_show_3000_at_fit() -> None:
    text = report.render(_complete(), date="2026-11-08", sources=[])
    assert "kann der Plan „3 000 Objekte“ in der Gesamtansicht keine 3 000 Objekte zeigen" in text
