"""Collect the click-fallback events of a session into a file and a summary (#3157).

``pages/_click_fallback.py`` records an event at every covering-blind fallback
activation. This plugin moves those events from the process that ran the test to
one place, writes them as JSON Lines and prints a summary under the terminal
report, so the next nightly answers "how many tests rely on the fallback, and is
the target really covered when they do" without anyone downloading an artifact.

## How the events travel under pytest-xdist

Not through a shared file. Each phase's events are drained right after the phase
(:meth:`ClickFallbackReporter.pytest_runtest_makereport`) and attached to that
phase's ``TestReport`` as the attribute :data:`REPORT_ATTRIBUTE`. pytest's report
serialisation (``_report_to_json``) copies a report's ``__dict__``, so the list of
plain dicts crosses from an xdist worker to the controller intact, and the
controller's :meth:`ClickFallbackReporter.pytest_runtest_logreport` is then the
**single writer** -- no per-worker files to merge, no lock. Without xdist the one
process is both sides. The attribute, unlike ``user_properties``, does not reach
the JUnit XML.

## Where the file lands

``<protocol dir>/click-fallbacks-<profile>.jsonl``, next to ``checkpoint.jsonl``.
The protocol dir is ``test-reports/e2e/<timestamp>/`` (``--generate-protocol``,
set by every compose runner); ``scripts/run-e2e.sh`` moves that directory's
content into the run's report dir and the nightly uploads ``test-reports/e2e/``
as ``e2e-nightly-reports-<profile>``. The parallel profiles run two pytest passes
(``two_pass_entrypoint.sh``) and the second resumes the first's directory, so
both passes append to the same file; each pass prints its own summary. Without
``--generate-protocol`` no file is written and only the summary is printed.

Lines are appended as events arrive, so an interrupted run keeps what it
measured. Each line is one event: the fields of ``record_fallback`` plus
``nodeid``, ``phase`` and ``profile``.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from .pages import _click_fallback

#: The ``TestReport`` attribute that carries a phase's events to the controller.
REPORT_ATTRIBUTE = "e2e_click_fallbacks"

#: The fixed first token of the summary line, so the job log can be grepped for it.
SUMMARY_TAG = "E2E-CLICK-FALLBACKS"

#: How many covering elements / tests the summary lists.
TOP_N = 10


def profile_name(app_mode: str, device: str, override: str | None = None) -> str:
    """Name the run's profile the way ``scripts/run-e2e.sh --profile`` does.

    ``light``/``mobile``/``tablet`` are the light-mode runners, ``full``,
    ``full-mobile`` and ``full-tablet`` the full-mode ones. ``smoke`` cannot be
    told from ``light`` by mode and device; ``E2E_PROFILE`` (*override*) names it
    where that matters.
    """
    if override:
        return override
    if app_mode == "full":
        return "full" if device == "desktop" else f"full-{device}"
    return "light" if device == "desktop" else device


def describe_node(node: object) -> str:
    """Render a probe's element description as ``tag[data-testid='…']#id.cls``."""
    if not isinstance(node, dict):
        return "<none>"
    text = str(node.get("tag") or "?")
    if node.get("testid"):
        text += f"[data-testid='{node['testid']}']"
    if node.get("id"):
        text += f"#{node['id']}"
    if node.get("cls") and not node.get("testid"):
        text += "." + ".".join(str(node["cls"]).split()[:2])
    return text


def summarize(events: list[dict[str, Any]], profile: str, path: Path | None) -> list[str]:
    """Return the terminal summary lines for *events*.

    The first line is always printed -- with zeros on a run that needed no
    fallback -- so "nothing fell back" is visible as a measurement and cannot be
    confused with "the instrumentation did not run".
    """
    covered = [e for e in events if e.get("probe") == "ok" and e.get("covered") is True]
    uncovered = [e for e in events if e.get("probe") == "ok" and e.get("covered") is False]
    no_verdict = [e for e in events if e.get("probe") == "ok" and e.get("covered") is None]
    failed = [e for e in events if e.get("probe") != "ok"]
    tests = {e.get("nodeid") for e in events}
    covered_tests = {e.get("nodeid") for e in covered}
    lines = [
        f"{SUMMARY_TAG} profile={profile} fallbacks={len(events)} tests={len(tests)} "
        f"covered={len(covered)} covered_tests={len(covered_tests)} "
        f"uncovered={len(uncovered)} no_verdict={len(no_verdict)} probe_failed={len(failed)} "
        f"file={path if path is not None else '-'}"
    ]
    if not events:
        return lines
    helpers = Counter(f"{e.get('helper')}/{e.get('activation')}" for e in events)
    lines.append("by helper: " + ", ".join(f"{h}={n}" for h, n in helpers.most_common()))
    triggers = Counter(str(e.get("trigger")) for e in events)
    lines.append("by trigger: " + ", ".join(f"{t}={n}" for t, n in triggers.most_common()))
    if covered:
        lines.append(f"top covering elements (of {len(covered)} covered fallbacks):")
        covering = Counter((describe_node(e.get("hit")), str(e.get("relation"))) for e in covered)
        for (node, relation), count in covering.most_common(TOP_N):
            lines.append(f"  {count:4d}x  {node}  ({relation})")
    lines.append("top tests by fallback count:")
    per_test = Counter(str(e.get("nodeid")) for e in events)
    for nodeid, count in per_test.most_common(TOP_N):
        lines.append(f"  {count:4d}x  {nodeid}")
    return lines


class ClickFallbackReporter:
    """The pytest plugin: drain per phase, write and count on the controller."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.is_worker = hasattr(config, "workerinput")
        self.profile = profile_name(
            str(config.getoption("--app-mode", default="full")),
            str(config.getoption("--device", default="desktop")),
            os.environ.get("E2E_PROFILE"),
        )
        self.events: list[dict[str, Any]] = []
        self.write_errors = 0

    def output_path(self) -> Path | None:
        """The JSON Lines file, or ``None`` when the run keeps no protocol dir."""
        directory = getattr(self.config, "_protocol_output_dir", None)
        if directory is None:
            return None
        return Path(directory) / f"click-fallbacks-{self.profile}.jsonl"

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item) -> Generator[None, Any, None]:
        outcome = yield
        events = _click_fallback.drain()
        if events:
            setattr(outcome.get_result(), REPORT_ATTRIBUTE, events)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if self.is_worker:
            return
        events = getattr(report, REPORT_ATTRIBUTE, None)
        if not events:
            return
        enriched = [
            {**event, "nodeid": report.nodeid, "phase": report.when, "profile": self.profile}
            for event in events
            if isinstance(event, dict)
        ]
        self.events.extend(enriched)
        path = self.output_path()
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                for event in enriched:
                    handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        except OSError:
            # A measurement must not fail the run; the summary reports the loss.
            self.write_errors += 1

    def pytest_terminal_summary(self, terminalreporter: Any) -> None:
        # ``--collect-only`` runs no test, so there is nothing measured to report --
        # and the collection count is read as a change-surface check, kept clean.
        if self.is_worker or self.config.getoption("collectonly", default=False):
            return
        terminalreporter.section("E2E click fallbacks (#3157)")
        path = self.output_path() if self.events else None
        for line in summarize(self.events, self.profile, path):
            terminalreporter.write_line(line)
        if self.write_errors:
            terminalreporter.write_line(
                f"WARNING: {self.write_errors} report(s) with fallback events could not be "
                f"written to {self.output_path()}"
            )
