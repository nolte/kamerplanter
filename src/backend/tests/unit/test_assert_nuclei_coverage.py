"""Selftests for ``scripts/security/assert-nuclei-coverage.sh`` (#1308).

WHY THIS FILE EXISTS, and what its absence cost.

The script shipped in #1319 with real measurements behind every claim — and with
no committed test. So nothing re-ran those measurements, and one case was never
covered at all: a HEALTHY scan at full template breadth.

The first real nightly (run 33462544851) failed on it. Nuclei reports the ports
its TEMPLATES probed and found closed with the same ``Skipped … from target list``
line it uses for a configured target that went unreachable, and the script
counted both. It reported "3 of 2 targets were unreachable" — a ratio that cannot
exist — against a scan that had loaded 5902 templates and both targets correctly.

Every healthy night would have failed that way, which recreates precisely the
condition #1308 exists to remove: a lane red for a reason unrelated to coverage,
in which a real coverage failure cannot be distinguished from the noise.

``test_a_healthy_full_breadth_scan_passes`` is the regression that was missing.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "security" / "assert-nuclei-coverage.sh"
TARGETS = "http://127.0.0.1:8000 http://127.0.0.1:5173"

# Verbatim from run 33462544851, assembled so no source line exceeds the limit.
# The `chain=` fragments are the evidence and must stay: they show each skipped
# port was reached by a TEMPLATE (an SCCM path, a Spark UI path), not because a
# configured target went away.
_SKIP = "[INF] Skipped {a} from target list as found unresponsive permanently: "
_CAUSE = 'cause="port closed or filtered" address={a} '

HEALTHY_LOG = (
    "[INF] Templates loaded for current scan: 5902\n"
    "[INF] Targets loaded for current scan: 2\n"
    + _SKIP.format(a="127.0.0.1:43800")
    + _CAUSE.format(a="127.0.0.1:43800")
    + 'chain="connection refused; got err while executing '
    + 'http://127.0.0.1:43800/static-files/kFgSL40.txt"\n'
    + _SKIP.format(a="127.0.0.1:80")
    + _CAUSE.format(a="127.0.0.1:80")
    + 'chain="connection refused; got err while executing '
    + 'http://127.0.0.1:80/SMS_DP_SMSPKG$/Datalib"\n'
    + _SKIP.format(a="127.0.0.1:4040")
    + _CAUSE.format(a="127.0.0.1:4040")
    + 'chain="connection refused; got err while executing '
    + 'https://127.0.0.1:4040/jobs/"\n'
    + "[INF] Scan completed. No results found.\n"
)


def run(tmp_path: Path, log: str, *, targets: str | None = TARGETS, expect: int = 2, floor: int = 1000):
    """Invoke the script the way the workflows do, and return (rc, stderr, json)."""
    log_file = tmp_path / "run.log"
    log_file.write_text(log)
    results = tmp_path / "results.jsonl"
    results.write_text("")
    out = tmp_path / "coverage.json"

    argv = [
        str(SCRIPT),
        "--label",
        "selftest",
        "--log",
        str(log_file),
        "--results",
        str(results),
        "--expect-targets",
        str(expect),
        "--min-templates",
        str(floor),
        "--json-out",
        str(out),
    ]
    if targets is not None:
        argv += ["--targets", targets]

    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    parsed = json.loads(out.read_text()) if out.exists() else None
    return proc.returncode, proc.stderr, parsed


def test_a_healthy_full_breadth_scan_passes(tmp_path: Path) -> None:
    """The regression from run 33462544851.

    Three ports the templates probed and found closed, none of them configured.
    Against the pre-fix script this was a FAILURE reading "3 of 2 targets were
    unreachable"; it must be a pass, with the three recorded as information.
    """
    rc, stderr, parsed = run(tmp_path, HEALTHY_LOG)
    assert rc == 0, stderr
    assert parsed is not None
    assert parsed["verdict"] == "PASS"
    assert parsed["targets_unreachable"] == 0
    assert parsed["incidental_ports_skipped"] == 3


def test_a_dropped_configured_target_still_fails(tmp_path: Path) -> None:
    """The counter-proof: the fix must not have disabled the check.

    Same healthy log plus one drop of a CONFIGURED target.
    """
    log = HEALTHY_LOG + (
        "[INF] Skipped 127.0.0.1:5173 from target list as found unresponsive "
        'permanently: cause="port closed or filtered"\n'
    )
    rc, stderr, parsed = run(tmp_path, log)
    assert rc == 1
    assert "1 of 2 CONFIGURED targets were unreachable" in stderr
    assert "127.0.0.1:5173" in stderr
    assert parsed is not None and parsed["targets_unreachable"] == 1


def test_omitting_targets_is_a_usage_error_never_a_pass(tmp_path: Path) -> None:
    """The identity check must not be silently skippable.

    Making ``--targets`` optional would let a caller disable the drop verdict
    without saying so — the shape NFR-018 §2 forbids.
    """
    rc, _, _ = run(tmp_path, HEALTHY_LOG, targets=None)
    assert rc == 2


def test_a_scheme_default_port_matches_a_bare_authority(tmp_path: Path) -> None:
    """``https://host`` and ``host:443`` are the same target.

    Without the default-port rule a plain https target could never match a drop
    line, and the check would be quietly toothless for it.
    """
    log = (
        "[INF] Templates loaded for current scan: 5902\n"
        "[INF] Targets loaded for current scan: 1\n"
        "[INF] Skipped example.test:443 from target list as found unresponsive permanently: x\n"
    )
    rc, stderr, _ = run(tmp_path, log, targets="https://example.test", expect=1)
    assert rc == 1
    assert "1 of 1 CONFIGURED targets were unreachable" in stderr


@pytest.mark.parametrize(
    ("log", "fragment"),
    [
        ("[INF] Targets loaded for current scan: 2\n", "never reported 'Templates loaded"),
        ("[INF] Templates loaded for current scan: 5902\n", "never reported 'Targets loaded"),
        (
            "[INF] Templates loaded for current scan: 5\n[INF] Targets loaded for current scan: 2\n",
            "below the floor",
        ),
        (
            "[INF] Templates loaded for current scan: 5902\n[INF] Targets loaded for current scan: 1\n",
            "1 targets loaded, but 2 were configured",
        ),
    ],
)
def test_the_other_coverage_assertions_still_fire(tmp_path: Path, log: str, fragment: str) -> None:
    """The narrowing must not have loosened anything else."""
    rc, stderr, _ = run(tmp_path, log)
    assert rc == 1
    assert fragment in stderr


def test_an_impossible_ratio_is_reported_as_a_broken_parser(tmp_path: Path) -> None:
    """More drops than configured targets cannot happen and is not a coverage verdict.

    The pre-fix script reported exactly this as "3 of 2 targets were
    unreachable", and a reader had no way to tell a defect in the script from a
    defect in the scan. If the identity check ever regresses, this says which.
    """
    log = (
        "[INF] Templates loaded for current scan: 5902\n"
        "[INF] Targets loaded for current scan: 2\n"
        "[INF] Skipped 127.0.0.1:8000 from target list as found unresponsive permanently: x\n"
        "[INF] Skipped 127.0.0.1:5173 from target list as found unresponsive permanently: x\n"
    )
    rc, stderr, _ = run(tmp_path, log, expect=1)
    assert rc == 1
    assert "assert-nuclei-coverage is broken" in stderr
    assert "do NOT read this as a coverage failure" in stderr


def test_a_missing_run_log_is_not_a_clean_result(tmp_path: Path) -> None:
    """The original point of the script: absent artefacts mean the scan never ran."""
    results = tmp_path / "results.jsonl"
    results.write_text("")
    proc = subprocess.run(
        [
            str(SCRIPT),
            "--label",
            "selftest",
            "--log",
            str(tmp_path / "absent.log"),
            "--results",
            str(results),
            "--expect-targets",
            "2",
            "--targets",
            TARGETS,
            "--min-templates",
            "1000",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "did not execute" in proc.stderr
