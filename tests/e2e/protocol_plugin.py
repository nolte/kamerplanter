"""Test protocol generator plugin — NFR-008 §4.4.

Activated via ``--generate-protocol`` CLI flag.  Produces a Markdown report
in ``test-reports/{timestamp}/protokoll.md`` containing:

* Date/time, git commit, branch
* Per-test result (PASSED / FAILED / SKIPPED)
* Summary statistics
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest


@dataclass
class TestResult:
    nodeid: str
    outcome: str  # "passed", "failed", "skipped"
    duration: float = 0.0
    message: str = ""


@dataclass
class ProtocolGenerator:
    results: list[TestResult] = field(default_factory=list)
    start_time: datetime | None = None

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)

    def generate(self, output_dir: Path) -> Path:
        """Write the protocol Markdown file and return its path."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / "protokoll.md"

        passed = sum(1 for r in self.results if r.outcome == "passed")
        failed = sum(1 for r in self.results if r.outcome == "failed")
        skipped = sum(1 for r in self.results if r.outcome == "skipped")
        total = len(self.results)

        git_commit = _git("rev-parse", "--short", "HEAD")
        git_branch = _git("rev-parse", "--abbrev-ref", "HEAD")

        lines = [
            "# E2E-Testprotokoll",
            "",
            f"**Datum:** {self.start_time:%Y-%m-%d %H:%M:%S UTC}" if self.start_time else "",
            f"**Git-Commit:** {git_commit}",
            f"**Git-Branch:** {git_branch}",
            "",
            "## Zusammenfassung",
            "",
            f"| Gesamt | Bestanden | Fehlgeschlagen | Übersprungen |",
            f"|--------|-----------|----------------|--------------|",
            f"| {total} | {passed} | {failed} | {skipped} |",
            "",
            "## Ergebnisse",
            "",
            "| Test | Ergebnis | Dauer (s) | Hinweis |",
            "|------|----------|-----------|---------|",
        ]

        for r in self.results:
            icon = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}.get(
                r.outcome, r.outcome.upper()
            )
            msg = r.message.replace("|", "\\|").replace("\n", " ")[:120] if r.message else ""
            lines.append(f"| `{r.nodeid}` | {icon} | {r.duration:.2f} | {msg} |")

        lines.append("")
        filepath.write_text("\n".join(lines), encoding="utf-8")
        return filepath


def _git(*args: str) -> str:
    """Run a git command and return stripped stdout, or 'n/a' on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() or "n/a"
    except Exception:
        return "n/a"


# ── pytest plugin hooks ──────────────────────────────────────────────────────

_generator: ProtocolGenerator | None = None
_output_dir: Path | None = None


def pytest_configure(config: pytest.Config) -> None:
    global _generator, _output_dir
    if config.getoption("--generate-protocol", default=False):
        _generator = ProtocolGenerator()
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        _output_dir = Path("test-reports") / timestamp


def pytest_sessionstart(session: pytest.Session) -> None:
    if _generator is not None:
        _generator.start_time = datetime.now(tz=timezone.utc)


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:  # type: ignore[type-arg]
    if _generator is None or call.when != "call":
        return
    outcome = "passed" if call.excinfo is None else "failed"
    message = ""
    if call.excinfo is not None:
        message = str(call.excinfo.value)
    _generator.add_result(
        TestResult(
            nodeid=item.nodeid,
            outcome=outcome,
            duration=call.duration,
            message=message,
        )
    )


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if _generator is None:
        return
    if report.when == "call" and report.skipped:
        # Override outcome for skipped tests
        for r in reversed(_generator.results):
            if r.nodeid == report.nodeid:
                r.outcome = "skipped"
                break


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _generator is not None and _output_dir is not None:
        path = _generator.generate(_output_dir)
        print(f"\nTestprotokoll geschrieben: {path}")
