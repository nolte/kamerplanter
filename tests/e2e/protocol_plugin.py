"""Test protocol generator plugin — NFR-008 §4.3/§4.4.

Activated via ``--generate-protocol`` CLI flag.  Produces a readable Markdown
report in ``test-reports/{timestamp}/protokoll.md`` containing:

* Metadata (date, git commit, branch, OS, browser, Python version)
* Per-class sections with spec references, descriptive text and embedded screenshots
* Failure details with error messages and failure screenshots
* Screenshot gallery at the end

Each test class section links to the corresponding:
- **Testfall-Spezifikation** (``spec/e2e-testcases/TC-REQ-XXX.md``)
- **Fachliche Anforderung** (``spec/req/REQ-XXX_*.md``)
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

# ── Spec resolution ──────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC_REQ_DIR = _REPO_ROOT / "spec" / "req"
_SPEC_TC_DIR = _REPO_ROOT / "spec" / "e2e-testcases"

# Pattern to extract REQ number from test file names or nodeids
_REQ_PATTERN = re.compile(r"req[_-]?(\d{3})", re.IGNORECASE)
# Pattern to extract TC-ID from docstrings like "TC-REQ-001-006: ..."
_TC_ID_PATTERN = re.compile(r"(TC-REQ-\d{3}-\d{3})")


def _find_req_spec(req_num: str) -> tuple[str, str] | None:
    """Find the fachliche Anforderung file for a REQ number.

    Returns (relative_path, title) or None.
    """
    for f in _SPEC_REQ_DIR.iterdir():
        if f.name.startswith(f"REQ-{req_num}") and f.suffix == ".md":
            # Extract title from filename: REQ-001_Stammdatenverwaltung.md → Stammdatenverwaltung
            title = f.stem.split("_", 1)[1].replace("-", " ") if "_" in f.stem else f.stem
            rel = f.relative_to(_REPO_ROOT)
            return str(rel), title
    return None


def _find_tc_spec(req_num: str) -> tuple[str, str] | None:
    """Find the Testfall-Spezifikation file for a REQ number.

    Returns (relative_path, title_from_frontmatter) or None.
    """
    tc_file = _SPEC_TC_DIR / f"TC-REQ-{req_num}.md"
    if not tc_file.exists():
        return None
    rel = tc_file.relative_to(_REPO_ROOT)
    # Try to extract title from frontmatter
    title = ""
    try:
        content = tc_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip("'")
                break
    except Exception:
        pass
    return str(rel), title or f"TC-REQ-{req_num}"


def _extract_req_num(nodeid: str) -> str | None:
    """Extract a 3-digit REQ number from a pytest nodeid."""
    m = _REQ_PATTERN.search(nodeid)
    return m.group(1) if m else None


def _extract_tc_id(docstring: str) -> str | None:
    """Extract TC-REQ-XXX-YYY from a test docstring."""
    m = _TC_ID_PATTERN.search(docstring)
    return m.group(1) if m else None


# Cache so we resolve each REQ only once
_req_spec_cache: dict[str, tuple[str, str] | None] = {}
_tc_spec_cache: dict[str, tuple[str, str] | None] = {}


def _get_req_spec(req_num: str) -> tuple[str, str] | None:
    if req_num not in _req_spec_cache:
        _req_spec_cache[req_num] = _find_req_spec(req_num)
    return _req_spec_cache[req_num]


def _get_tc_spec(req_num: str) -> tuple[str, str] | None:
    if req_num not in _tc_spec_cache:
        _tc_spec_cache[req_num] = _find_tc_spec(req_num)
    return _tc_spec_cache[req_num]


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ScreenshotEntry:
    """A single screenshot checkpoint captured during a test."""

    filename: str
    description: str
    test_nodeid: str


@dataclass
class TestResult:
    nodeid: str
    outcome: str  # "passed", "failed", "skipped"
    duration: float = 0.0
    message: str = ""
    docstring: str = ""
    screenshots: list[ScreenshotEntry] = field(default_factory=list)


@dataclass
class ProtocolGenerator:
    results: list[TestResult] = field(default_factory=list)
    start_time: datetime | None = None

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _class_display_name(nodeid: str) -> str:
        """Extract a readable class name from a pytest nodeid."""
        parts = nodeid.split("::")
        if len(parts) >= 2:
            return parts[-2]
        return parts[0]

    @staticmethod
    def _test_display_name(nodeid: str) -> str:
        """Extract the test function name."""
        return nodeid.split("::")[-1]

    @staticmethod
    def _file_display(nodeid: str) -> str:
        """Extract file path from nodeid."""
        return nodeid.split("::")[0]

    @staticmethod
    def _outcome_icon(outcome: str) -> str:
        return {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}.get(
            outcome, outcome.upper()
        )

    # ── generation ────────────────────────────────────────────────────────

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
        os_info = f"{platform.system()} {platform.release()}"
        python_version = platform.python_version()
        browser_info = os.environ.get("E2E_BROWSER", "chrome (headless)")

        lines: list[str] = []

        # ── Header & Metadata ────────────────────────────────────────────
        date_str = (
            f"{self.start_time:%Y-%m-%d %H:%M:%S} UTC" if self.start_time else "n/a"
        )
        lines.extend([
            f"# E2E-Testprotokoll — {date_str}",
            "",
            "## Metadaten",
            "",
            "| Feld | Wert |",
            "|---|---|",
            f"| **Datum** | {date_str} |",
            f"| **Commit** | `{git_commit}` |",
            f"| **Branch** | {git_branch} |",
            f"| **Betriebssystem** | {os_info} |",
            f"| **Browser** | {browser_info} |",
            f"| **Python** | {python_version} |",
            "",
        ])

        # ── Summary ──────────────────────────────────────────────────────
        lines.extend([
            "## Zusammenfassung",
            "",
            "| Gesamt | Bestanden | Fehlgeschlagen | Übersprungen |",
            "|--------|-----------|----------------|--------------|",
            f"| {total} | {passed} | {failed} | {skipped} |",
            "",
        ])

        if total > 0:
            pass_pct = passed / total * 100
            lines.extend([
                f"Erfolgsquote: **{pass_pct:.1f}%** ({passed}/{total})",
                "",
            ])

        # ── Covered requirements overview ────────────────────────────────
        req_nums_seen: dict[str, int] = {}
        for r in self.results:
            rn = _extract_req_num(r.nodeid)
            if rn:
                req_nums_seen[rn] = req_nums_seen.get(rn, 0) + 1

        if req_nums_seen:
            lines.extend([
                "## Abgedeckte Anforderungen",
                "",
                "| REQ | Fachliche Anforderung | Testfall-Spezifikation | Tests |",
                "|-----|----------------------|------------------------|-------|",
            ])
            for rn in sorted(req_nums_seen):
                req_spec = _get_req_spec(rn)
                tc_spec = _get_tc_spec(rn)
                req_link = f"[{req_spec[1]}]({req_spec[0]})" if req_spec else "—"
                tc_link = f"[TC-REQ-{rn}]({tc_spec[0]})" if tc_spec else "—"
                lines.append(
                    f"| REQ-{rn} | {req_link} | {tc_link} | {req_nums_seen[rn]} |"
                )
            lines.append("")

        # ── Failed tests detail ──────────────────────────────────────────
        failed_results = [r for r in self.results if r.outcome == "failed"]
        if failed_results:
            lines.extend([
                "## Fehlgeschlagene Tests",
                "",
            ])
            for r in failed_results:
                test_name = self._test_display_name(r.nodeid)
                file_path = self._file_display(r.nodeid)

                # Spec references
                req_num = _extract_req_num(r.nodeid)
                tc_id = _extract_tc_id(r.docstring) if r.docstring else None

                lines.extend([
                    f"### FAIL `{test_name}`",
                    "",
                    f"- **Datei:** `{file_path}`",
                ])
                if r.docstring:
                    lines.append(f"- **Beschreibung:** {r.docstring}")
                if tc_id:
                    lines.append(f"- **Testfall-ID:** {tc_id}")
                if req_num:
                    req_spec = _get_req_spec(req_num)
                    tc_spec = _get_tc_spec(req_num)
                    if req_spec:
                        lines.append(
                            f"- **Anforderung:** [REQ-{req_num} {req_spec[1]}]({req_spec[0]})"
                        )
                    if tc_spec:
                        lines.append(
                            f"- **Testfall-Spec:** [TC-REQ-{req_num}]({tc_spec[0]})"
                        )

                error_msg = r.message.replace("\n", "\n  ") if r.message else "n/a"
                lines.extend([
                    f"- **Fehler:**",
                    f"  ```",
                    f"  {error_msg[:500]}",
                    f"  ```",
                ])
                # Attach failure screenshots
                failure_shots = [
                    s for s in r.screenshots if s.filename.startswith("FAILURE_")
                ]
                for s in failure_shots:
                    lines.append(
                        f"- **Screenshot:** ![{s.description}](screenshots/{s.filename})"
                    )
                lines.append("")

        # ── Per-class sections ───────────────────────────────────────────
        lines.extend([
            "## Testergebnisse im Detail",
            "",
        ])

        # Group results by test class
        class_groups: dict[str, list[TestResult]] = {}
        for r in self.results:
            cls = self._class_display_name(r.nodeid)
            class_groups.setdefault(cls, []).append(r)

        for cls_name, results in class_groups.items():
            cls_passed = sum(1 for r in results if r.outcome == "passed")
            cls_failed = sum(1 for r in results if r.outcome == "failed")
            cls_skipped = sum(1 for r in results if r.outcome == "skipped")
            cls_total = len(results)

            # Resolve spec references from the first result's nodeid
            req_num = _extract_req_num(results[0].nodeid)

            # Section header with pass/fail summary
            status_badge = "PASS" if cls_failed == 0 else "FAIL"
            lines.extend([
                f"### {cls_name} [{status_badge}]",
                "",
            ])

            # Spec reference block
            if req_num:
                req_spec = _get_req_spec(req_num)
                tc_spec = _get_tc_spec(req_num)
                ref_parts: list[str] = []
                if req_spec:
                    ref_parts.append(
                        f"**Anforderung:** [REQ-{req_num} — {req_spec[1]}]({req_spec[0]})"
                    )
                if tc_spec:
                    ref_parts.append(
                        f"**Testfall-Spec:** [TC-REQ-{req_num} — {tc_spec[1]}]({tc_spec[0]})"
                    )
                if ref_parts:
                    lines.extend(ref_parts)
                    lines.append("")

            lines.extend([
                f"*{cls_total} Tests: {cls_passed} bestanden"
                + (f", {cls_failed} fehlgeschlagen" if cls_failed else "")
                + (f", {cls_skipped} übersprungen" if cls_skipped else "")
                + f"*",
                "",
            ])

            # File path
            file_path = self._file_display(results[0].nodeid)
            lines.extend([f"**Datei:** `{file_path}`", ""])

            # Test result table with TC-IDs and descriptions
            lines.extend([
                "| Test | TC-ID | Ergebnis | Dauer | Beschreibung |",
                "|------|-------|----------|-------|--------------|",
            ])
            for r in results:
                test_name = self._test_display_name(r.nodeid)
                icon = self._outcome_icon(r.outcome)
                duration = f"{r.duration:.2f}s"
                tc_id = _extract_tc_id(r.docstring) if r.docstring else None
                tc_id_str = tc_id or ""
                # Description: docstring without the TC-ID prefix
                desc = r.docstring
                if desc and tc_id:
                    desc = desc.replace(tc_id, "").lstrip(":").lstrip().lstrip("-").strip()
                desc = (desc[:100] if desc else "")
                lines.append(
                    f"| `{test_name}` | {tc_id_str} | {icon} | {duration} | {desc} |"
                )
            lines.append("")

            # Inline screenshots for this class
            class_screenshots = [
                s
                for r in results
                for s in r.screenshots
                if not s.filename.startswith("FAILURE_")
            ]
            if class_screenshots:
                lines.append("**Screenshots:**")
                lines.append("")
                for s in class_screenshots:
                    lines.extend([
                        f"*{s.description}*",
                        "",
                        f"![{s.description}](screenshots/{s.filename})",
                        "",
                    ])

        # ── Screenshot gallery ───────────────────────────────────────────
        screenshot_dir = output_dir / "screenshots"
        if screenshot_dir.is_dir():
            all_screenshots = sorted(screenshot_dir.iterdir())
            if all_screenshots:
                lines.extend([
                    "## Screenshot-Übersicht",
                    "",
                    "| Nr. | Datei | Beschreibung |",
                    "|-----|-------|--------------|",
                ])
                # Build a lookup from filename to description
                desc_map: dict[str, str] = {}
                for r in self.results:
                    for s in r.screenshots:
                        desc_map[s.filename] = s.description

                for i, f in enumerate(all_screenshots, 1):
                    if f.suffix.lower() == ".png":
                        desc = desc_map.get(f.name, f.stem.replace("_", " "))
                        lines.append(
                            f"| {i:03d} | ![{f.name}](screenshots/{f.name}) | {desc} |"
                        )
                lines.append("")

        # ── Footer ───────────────────────────────────────────────────────
        lines.extend([
            "---",
            f"*Protokoll automatisch generiert am {date_str} (NFR-008 §4.4)*",
            "",
        ])

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
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        _output_dir = Path("test-reports") / timestamp
        _generator = ProtocolGenerator()
        # Store on config so conftest.py can access the same output directory
        config._protocol_output_dir = _output_dir  # type: ignore[attr-defined]


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

    # Extract docstring from test function
    docstring = ""
    if item.obj and item.obj.__doc__:
        docstring = item.obj.__doc__.strip().split("\n")[0]

    # Collect screenshots registered during this test
    screenshots: list[ScreenshotEntry] = getattr(
        item, "_protocol_screenshots", []
    )

    _generator.add_result(
        TestResult(
            nodeid=item.nodeid,
            outcome=outcome,
            duration=call.duration,
            message=message,
            docstring=docstring,
            screenshots=screenshots,
        )
    )


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if _generator is None:
        return
    if report.when == "call" and report.skipped:
        for r in reversed(_generator.results):
            if r.nodeid == report.nodeid:
                r.outcome = "skipped"
                break


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _generator is not None and _output_dir is not None:
        path = _generator.generate(_output_dir)
        print(f"\nTestprotokoll geschrieben: {path}")
