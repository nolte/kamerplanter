"""Unit tests for the shared base page-object readers fixed in #946 wave 13.

## Scope

Wave 13 is the closing wave of the #946 absence-check campaign
(`.audits/absence-check-campaign/plan.md`) and its single target is
`tests/e2e/pages/base_page.py`, the base class every page object inherits.
Waves 1-12 covered every concrete page object; this wave audited the shared
primitives they are built on.

The base page deliberately contains *non-waiting* primitives that callers
compose -- the bidirectional readers (`is_present`, `is_absent_within`,
`has_empty_state`, `has_search_chip`, `has_sort_chip`, `is_any_displayed`,
`has_alert_notification`, `is_error_displayed`) that legitimately serve both
``assert x()`` and ``assert not x()``, plus the polling readers that already
take a ``timeout=`` (`find_present`, `is_visible_within`, `await_presence`,
`is_absent_within`, `get_text_stable`). Converting any of those to wait would
make every negative assertion in the whole suite hang, so they are left exactly
as they are. The wave-13 audit found **one** genuinely-vacuous shape.

### The one conversion: the page-header-action readers

`has_header_action` and `is_header_action_enabled` both read through the private
`_header_action_element`, which -- before this wave -- issued two *raw*
``find_elements`` (the direct control, then the ``page-header-overflow``
trigger) in the same millisecond the caller invoked it. Taken right after an
``open()``/navigation, before the ``PageHeaderActions`` header has rendered,
*both* probes miss and the helper returns ``None`` -> the action reads as
absent. That is the unfalsifiable-absence shape `e2e-test-stability` §D forbids,
and it is the exact defect `click_header_action` was already fixed for (its own
docstring: "TC-REQ-001-030 failed exactly that way once #835 removed the
implicit wait that had been granting both probes 3 s").

It is not academic. The `test_req003_phasensteuerung.py` suite drives plant
selection and a negative assertion off it:

* ``assert not plant_detail.is_header_action_enabled("remove-button")``
  (TC-REQ-003-027, line 922) -- a vacuous ``None`` here makes ``assert not
  False`` pass however early it runs, certifying nothing about whether the
  remove action is actually disabled.
* the ``if not plant_detail.is_remove_button_enabled()`` /
  ``is_transition_button_enabled()`` gates (a dozen call sites) that *select*
  which plant a test operates on -- a premature ``False`` picks the wrong
  candidate.

The fix mirrors `click_header_action` exactly: before deciding the action is
absent, wait (bounded, ``IMPLICIT_WAIT_EQUIVALENT``) for the header to expose
either the action directly (``sm``+) or its overflow trigger (``xs``). A raw
read is only taken once that disjunction is present, so the ``None`` answer
means "the header rendered and this action is genuinely not on it", never "the
header has not rendered yet". `_header_action_element` has exactly two callers,
both read-only (`has_header_action`, `is_header_action_enabled`);
`click_header_action` does its own `wait_for_any_present` and does not route
through it, so this change touches nothing else.

## What is measured, and what is not

The two "outlives a late render" tests are **differential**: run against the
pre-fix body (a bare ``find_elements`` with no wait) they fail, because the
header is rendered only after several probes and the unwaited read answers
``None`` -> ``False``/disabled before it exists. Their red-first failures were
captured before the fix landed and are recorded in the wave-13 report.

The two "still reports a genuine absence" tests are **not** differential: a
header action that never renders reads as absent both before and after the fix,
so they only pin the bounded-timeout contract (the fixed reader must still be
able to say "no", and must not hang past ``IMPLICIT_WAIT_EQUIVALENT``). They are
reported honestly as non-differential -- they guard the *other* half of the
property, which is the half a naive "just wait" fix would break.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py` and the wave 7-12
files: a **real** ``selenium.webdriver.remote.webdriver.WebDriver`` runs over a
fake command executor, so ``WebDriverWait``, ``wait_for_any_present`` /
``probe_branches`` and the real `BasePage` all run unmodified. Only the wire is
fake. Provoking a "read one frame too early" race in a real browser would mean
hitting a React commit at a precise instant -- the flakiest possible way to
assert a deterministic contract.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py` and prior waves'

Per the wave-13 task brief, matching waves 7-12: `test_row_helpers.py` is shared
across parallel absence-check waves and edits to it collide, and each prior
wave's own file is a sibling PR's file for the same reason. This module imports
the `Harness`/`TableDom`/`StubConnection` stub from `test_row_helpers` and adds
no classes to it, and does not touch any other wave's file either.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage

# The stub itself, not the fixture function -- see wave 7-12's own files for why
# this is a thin local fixture over the same stub rather than a reused fixture
# function (Ruff F811).
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Slack applied to `IMPLICIT_WAIT_EQUIVALENT` for elapsed-time bounds,
#: mirroring `test_row_helpers.BUDGET_SLACK` / the prior waves' own constant.
BUDGET_SLACK = 1.5

#: How many probes the anchor's `wait_for_any_present` must survive before the
#: header action is built, mirroring wave 10's own `_render_after` / `PROBES`.
PROBES = 3


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times.

    Hooked on both `find_elements` and the branch-probe script:
    `wait_for_any_present` sweeps its branches through one `execute_script`
    round-trip per attempt (`BasePage._PROBE_CSS_BRANCHES`), so a hook on
    `find_elements` alone would never fire while the anchor itself is waiting.
    Identical shape to wave 10's `_render_after`.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


# ── The page-header-action readers ──────────────────────────────────────────


class TestHasHeaderAction:
    """`has_header_action` must outlive a header that renders a beat late, and
    must still report a genuinely absent action.

    The direct-control shape is what `test_req003_phasensteuerung.py`'s
    ``assert plant_detail.has_header_action("remove-button")`` (TC-REQ-003-015)
    and `TaskQueuePage.is_generate_reminders_visible` read.
    """

    def test_outlives_a_header_that_renders_late(self, harness: Harness) -> None:
        """Differential: the pre-fix raw read answers ``False`` before the
        header exists; the anchored read waits for it.

        The action is rendered only after `PROBES` DOM probes, i.e. the read is
        taken inside the window right after `open()` where the header has not
        committed yet -- exactly the instant the unwaited `find_elements`
        sampled.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render_dialog("remove-button"))

        assert harness.page.has_header_action("remove-button") is True

    def test_still_reports_a_genuinely_absent_action(self, harness: Harness) -> None:
        """Non-differential: an action that never renders (and no overflow
        trigger either) must still read as absent, bounded by the anchor's
        budget rather than hanging.

        This is the half a naive "just wait" fix would break: the reader is
        legitimately asked about actions that are *meant* to be missing
        (UI-NFR-018 R-012 omits a delete action for system data), so it has to
        keep answering ``False`` -- it simply must not do so one render too
        early.
        """
        started = time.monotonic()
        assert harness.page.has_header_action("remove-button") is False
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


class TestIsHeaderActionEnabled:
    """`is_header_action_enabled` must outlive a late header, and must still
    report a genuinely absent action as not-enabled.

    Read by `test_req003_phasensteuerung.py`'s dozen ``if not
    plant_detail.is_..._enabled()`` selection gates and its ``assert not
    plant_detail.is_header_action_enabled("remove-button")`` (TC-REQ-003-027).
    """

    def test_outlives_a_header_that_renders_late(self, harness: Harness) -> None:
        """Differential: the pre-fix raw read finds no element and answers
        ``False`` (reads as disabled) before the header exists.

        The stub answers `IS_ELEMENT_ENABLED` with ``True`` and has no
        ``disabled``/``aria-disabled`` attribute, so a *rendered* enabled
        control reads as enabled -- which is only reachable once the anchored
        read has waited for it to appear.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render_dialog("transition-button"))

        assert harness.page.is_header_action_enabled("transition-button") is True

    def test_still_reports_a_genuinely_absent_action(self, harness: Harness) -> None:
        """Non-differential: no control and no overflow means not-enabled, and
        the anchor must not turn that into a hang past its budget.
        """
        started = time.monotonic()
        assert harness.page.is_header_action_enabled("remove-button") is False
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── The primitives that are deliberately left non-waiting ────────────────────


class TestTheLeftAlonePrimitives:
    """The other half of wave 13's finding, pinned so the exclusions are not
    read as an oversight.

    These bidirectional primitives answer *right now* on purpose: they are the
    anchors other code waits ON, not readers that need anchoring. Converting one
    to wait would make every ``assert not primitive(...)`` in the suite hang
    until timeout. Asserted as "answers straight away", which is the observable
    difference from a wrapped helper that would spend a budget first.
    """

    def test_is_present_answers_immediately_when_absent(self, harness: Harness) -> None:
        """`is_present` must not wait -- a negative is an instantaneous verdict."""
        started = time.monotonic()
        assert harness.page.is_present(BasePage.DATA_TABLE_ROWS) is False
        assert time.monotonic() - started < 1.0

    def test_is_present_answers_immediately_when_present(self, harness: Harness) -> None:
        harness.dom.render(["alpha"])

        started = time.monotonic()
        assert harness.page.is_present(BasePage.DATA_TABLE_ROWS) is True
        assert time.monotonic() - started < 1.0
