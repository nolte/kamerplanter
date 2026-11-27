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

#: The fixed first token of the direct-click line (``kind: "direct"``).
DIRECT_TAG = "E2E-CLICK-DIRECT"

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


def _is_direct(event: dict[str, Any]) -> bool:
    return event.get("kind") == "direct"


def _with_outcome(events: list[dict[str, Any]], outcome: str) -> list[dict[str, Any]]:
    return [e for e in events if e.get("outcome") == outcome]


def _detail(events: list[dict[str, Any]], covered: list[dict[str, Any]], noun: str) -> list[str]:
    """The ranked lines under one kind's summary line."""
    lines: list[str] = []
    helpers = Counter(f"{e.get('helper')}/{e.get('activation')}" for e in events)
    lines.append(f"{noun} by helper: " + ", ".join(f"{h}={n}" for h, n in helpers.most_common()))
    triggers = Counter(str(e.get("trigger")) for e in events)
    lines.append(f"{noun} by trigger: " + ", ".join(f"{t}={n}" for t, n in triggers.most_common()))
    if covered:
        lines.append(f"top covering elements (of {len(covered)} covered {noun}):")
        covering = Counter((describe_node(e.get("hit")), str(e.get("relation"))) for e in covered)
        for (node, relation), count in covering.most_common(TOP_N):
            lines.append(f"  {count:4d}x  {node}  ({relation})")
    lines.append(f"top tests by {noun} count:")
    per_test = Counter(str(e.get("nodeid")) for e in events)
    for nodeid, count in per_test.most_common(TOP_N):
        lines.append(f"  {count:4d}x  {nodeid}")
    return lines


def summarize(events: list[dict[str, Any]], profile: str, path: Path | None) -> list[str]:
    """Return the terminal summary lines for *events*.

    Two kinds, kept apart: the ``E2E-CLICK-FALLBACKS`` line counts only the
    fallbacks after a refused native click, the ``E2E-CLICK-DIRECT`` line only
    the deliberately coordinate-free clicks. Both lines are always printed --
    with zeros on a run that had none -- so "nothing happened" is visible as a
    measurement and cannot be confused with "the instrumentation did not run".

    On the direct line ``outside_viewport`` is counted on its own: the
    coordinate-free helper exists because a control's centre can lie below the
    fold, which is not *covered* but is the case where a user must scroll first.
    ``no_verdict`` there is what remains without a verdict (a detached node).

    Since step 2 the fallback line also counts what became of the refused clicks:
    ``raised`` -- covered, so the test failed naming the cover and no click was
    sent -- and ``covered_ok`` -- covered, clicked anyway on a caller's stated
    reason. The step-1 fields keep their meaning: ``covered`` still counts every
    covered fallback, raised or not. The opt-outs are listed with their reasons.
    """
    fallbacks = [e for e in events if not _is_direct(e)]
    direct = [e for e in events if _is_direct(e)]

    def ok(group: list[dict[str, Any]], covered: bool | None) -> list[dict[str, Any]]:
        return [e for e in group if e.get("probe") == "ok" and e.get("covered") is covered]

    f_covered = ok(fallbacks, True)
    lines = [
        f"{SUMMARY_TAG} profile={profile} fallbacks={len(fallbacks)} "
        f"tests={len({e.get('nodeid') for e in fallbacks})} "
        f"covered={len(f_covered)} covered_tests={len({e.get('nodeid') for e in f_covered})} "
        f"uncovered={len(ok(fallbacks, False))} no_verdict={len(ok(fallbacks, None))} "
        f"probe_failed={len([e for e in fallbacks if e.get('probe') != 'ok'])} "
        f"raised={len(_with_outcome(fallbacks, _click_fallback.OUTCOME_RAISED))} "
        f"covered_ok={len(_with_outcome(fallbacks, _click_fallback.OUTCOME_COVERED_OK))} "
        f"file={path if path is not None else '-'}"
    ]
    d_covered = ok(direct, True)
    d_offscreen = [e for e in ok(direct, None) if e.get("relation") == "outside_viewport"]
    lines.append(
        f"{DIRECT_TAG} profile={profile} clicks={len(direct)} "
        f"tests={len({e.get('nodeid') for e in direct})} "
        f"covered={len(d_covered)} covered_tests={len({e.get('nodeid') for e in d_covered})} "
        f"uncovered={len(ok(direct, False))} outside_viewport={len(d_offscreen)} "
        f"no_verdict={len(ok(direct, None)) - len(d_offscreen)} "
        f"probe_failed={len([e for e in direct if e.get('probe') != 'ok'])}"
    )
    if fallbacks:
        lines.extend(_detail(fallbacks, f_covered, "fallbacks"))
        opt_outs = _with_outcome(fallbacks, _click_fallback.OUTCOME_COVERED_OK)
        if opt_outs:
            lines.append(f"covered_ok opt-outs ({len(opt_outs)}):")
            reasons = Counter((str(e.get("caller")), str(e.get("covered_ok"))) for e in opt_outs)
            for (caller, reason), count in reasons.most_common(TOP_N):
                lines.append(f"  {count:4d}x  {caller}: {reason}")
    if direct:
        lines.extend(_detail(direct, d_covered, "direct clicks"))
        if d_offscreen:
            lines.append(f"top targets outside the viewport (of {len(d_offscreen)} direct clicks):")
            targets = Counter(describe_node(e.get("target")) for e in d_offscreen)
            for node, count in targets.most_common(TOP_N):
                lines.append(f"  {count:4d}x  {node}")
    return lines


def fail_a_skip_after_a_refused_click(report: Any, events: list[dict[str, Any]]) -> None:
    """Turn a phase that skipped after a refused click into a failure (#3157).

    A refused click raises :class:`_click_fallback.CoveredControlError`. Older
    tests wrap a step in ``except Exception: pytest.skip("... not available")``;
    there the refusal ended as "skipped", which reads as "nothing to test here"
    while a control was on screen and covered. The skip is the giveaway: no
    page object recovers from a refusal (the one retry on ``AssertionError``,
    ``choose_select_value``, lets it through). An expected failure (``xfail``)
    is left alone -- pytest reports it as skipped too, and it is declared; an
    ``xfail`` test that calls ``pytest.skip`` itself is a plain skip and fails.
    The message keeps the swallowing skip's reason and place.
    """
    if not getattr(report, "skipped", False) or getattr(report, "wasxfail", None) is not None:
        return
    refused = [e for e in events if e.get("outcome") == _click_fallback.OUTCOME_RAISED]
    if not refused:
        return
    skip = report.longrepr
    where = (
        f"{skip[0]}:{skip[1]}: {skip[2]}"
        if isinstance(skip, tuple) and len(skip) == 3
        else str(skip)
    )
    report.outcome = "failed"
    report.longrepr = (
        "The test skipped after a guarded click was refused on a covered control; a covered "
        "control is present, so this is a failure and not a skip (#3157).\n"
        f"The skip that swallowed it: {where}\n"
        + "\n".join(
            f"{_click_fallback.refusal_message(e, str(e.get('helper')))} Called from {e.get('caller')}."
            for e in refused
        )
    )


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
        if not events:
            return
        report = outcome.get_result()
        setattr(report, REPORT_ATTRIBUTE, events)
        fail_a_skip_after_a_refused_click(report, events)

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
