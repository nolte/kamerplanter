"""Unit tests for the LOWER-bucket list-page `get_row_count()` anchor (#946 wave 8).

## Scope

Wave 8 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
covers the remaining list-view page-objects: `PlantInstanceListPage`,
`SiteListPage`, `TankListPage`, `WateringLogListPage`, `WorkflowListPage`. All
five (`WorkflowListPage` aside, see below) carried the identical shape wave 7
found in the six DataTable list pages it fixed:

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

`nutrient_plan_list_page.py` was already converted by wave 7 (it shares the
DataTable cluster's shape) and is out of this wave's scope -- its pin lives in
`test_list_page_readers.py`, not here.

`PAGE` mounts synchronously on every one of these routes -- before the first
fetch resolves -- so a read taken right after `open()` can land in a frame
where none of the table's settled branches (rows, `EmptyState`, or the
`no-search-results` panel, where the page renders one) has committed yet.
Several call sites gate a `pytest.skip(...)` or a bidirectional count
comparison directly on this read, which is the exact `has_care_card` defect
class `pflege_dashboard_page.py` fixed for the HIGH bucket: an unanchored `0`
there is indistinguishable from a table that genuinely has no rows.

The fix adds a page-owned `wait_for_list_content()` anchor -- built the same
way as `PflegeDashboardPage.wait_for_dashboard_content()`, on
`wait_for_any_present` over the settled-branch locators, wrapped in
`suppress(AssertionError)` so a genuinely empty table is never blocked -- and
`get_row_count()`/`get_card_count()` calls it before reading. This module
pins the same two-part contract every anchored reader in `test_row_helpers.py`
is held to: it must **outlive a late render** (the anchor is a real wait, not
a renamed sample), and it must **still report a genuine, settled absence**
(the anchor does not silently convert "empty" into "always non-zero" or hang
past its budget).

`PlantInstanceListPage` gets the full, exhaustive pin (all three branches plus
the measured search-debounce boundary), mirroring `FertilizerListPage` in
wave 7's file -- it is the most heavily used page-object in this wave and its
three-branch shape is identical to the DataTable cluster's. `TankListPage` and
`WateringLogListPage` get the same three-branch contract, since their own
test files (`test_req014_tank.py`, `test_req004_watering_log.py`) route
search-then-count call sites through `wait_for_no_search_results`, which this
pins the settled side of. `SiteListPage` gets the two-branch contract: it
exposes no `search()` at all, so its `no-search-results` panel is not a
reachable branch through the UI (the locator is still inherited from
`BasePage` and included in the disjunction, since it costs nothing to check,
but nothing in this suite ever renders it).

`WorkflowListPage` is the one structural outlier and gets its own, narrower
class: `WorkflowTemplateListPage.tsx` renders no `data-testid='empty-state'`
and no `data-testid='no-search-results'` at all -- both its "no workflows"
and its "search matched nothing" branches are a bare, untagged `Box`. Its
`wait_for_list_content()` therefore disjoins over a single branch
(`WORKFLOW_CARDS`), and the genuinely-empty case always falls through to the
anchor's own bounded budget rather than reaching a fast branch -- pinned here
so that behaviour is not later mistaken for a hang.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py` and wave 7's
`test_list_page_readers.py`: a **real**
`selenium.webdriver.remote.webdriver.WebDriver` runs over a fake command
executor, so `WebDriverWait`, `resolve_settled_branch` and the real page
objects all run unmodified. Only the wire is fake. Provoking a "read one frame
too early" race in a real browser would mean hitting a React commit at a
precise instant -- the flakiest possible way to assert a deterministic
contract.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py` and wave 7's file

Per the wave-8 task brief: `test_row_helpers.py` is shared across parallel
absence-check waves and edits to it collide, and wave 7's own
`test_list_page_readers.py` is a sibling PR's file for the same reason. This
module imports the `Harness`/`TableDom`/`StubConnection`/`Command` stub from
`test_row_helpers` and adds no classes to either file.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.base_page import IMPLICIT_WAIT_EQUIVALENT
from tests.e2e.pages.plant_instance_list_page import PlantInstanceListPage
from tests.e2e.pages.site_list_page import SiteListPage
from tests.e2e.pages.tank_list_page import TankListPage
from tests.e2e.pages.watering_log_list_page import WateringLogListPage
from tests.e2e.pages.workflow_list_page import WorkflowListPage

# The stub itself, not the fixture function -- see wave 7's
# `test_list_page_readers.py` for why this is a thin local fixture over the
# same stub rather than a reused fixture function (Ruff F811).
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Slack applied to `IMPLICIT_WAIT_EQUIVALENT` for elapsed-time bounds, mirroring
#: `test_row_helpers.BUDGET_SLACK`.
BUDGET_SLACK = 1.5

#: How many probes the anchor's `wait_for_any_present` must survive before the
#: content is built. `wait_for_any_present` sweeps its branches through one
#: `execute_script` round-trip per attempt (`BasePage._PROBE_CSS_BRANCHES`), so
#: the render-after hook is armed on both `FIND_ELEMENTS` and
#: `W3C_EXECUTE_SCRIPT` -- exactly as wave 7's own helper does.
PROBES = 3


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times."""
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


ROWS = ["Alpha-Row", "Beta-Row", "Gamma-Row"]


# ── 1. PlantInstanceListPage: the full three-branch contract ────────────────


class TestPlantInstanceListGetRowCount:
    """The representative, exhaustive pin: all three settled branches plus the boundary."""

    def _page(self, harness: Harness) -> PlantInstanceListPage:
        return PlantInstanceListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """A read right after `open()` must not sample the pre-fetch instant.

        Before the fix this was a bare `find_elements`, answered `0` on probe 1
        and never looked again -- the exact shape every
        `pytest.skip("No plant instances...")` right after `open()` in
        `test_req001_plant_instance.py` turns into a silent skip of real
        coverage whenever the fetch has not landed yet.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        """A tenant with no plant instances is a real `0`, not a timeout."""
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0, (
            "EmptyState is already present -- the anchor must not spend its "
            "budget once a settled branch has been reached"
        )

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """The third branch: a search that legitimately matched nothing.

        Regression pin for `test_search_filters_plant_instances`'s
        `wait_for_no_search_results` fix in `test_req001_plant_instance.py`.
        """
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        """The anchor is `suppress(AssertionError)`-wrapped: it gives up, not hangs.

        Nothing is ever rendered here -- none of the three branches arrives
        within the anchor's budget. The read must still return (a real defect
        this models: the DataTable failed to mount at all), and it must return
        within `IMPLICIT_WAIT_EQUIVALENT`, not `DEFAULT_TIMEOUT` or forever.
        """
        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK

    def test_the_anchor_is_a_no_op_while_a_search_debounce_is_in_flight(
        self, harness: Harness
    ) -> None:
        """The measured boundary: stale rows satisfy the anchor immediately.

        Analytic, not a defect this wave introduces: `wait_for_list_content`
        only disjoins over *presence*, and the previous, unfiltered rows keep
        `TABLE_ROWS` satisfied throughout a debounce still in flight -- there is
        no frame in which none of the three branches holds, so
        `wait_for_any_present` returns at once and `get_row_count()` reads
        whatever is on screen *right now*, stale or not. This is exactly why
        `_journey_helpers.provision_plant` and every search-then-read call site
        in `test_req001_plant_instance.py` route through
        `wait_for_search_applied`/`wait_for_row_identity` first rather than
        relying on this anchor. Pinned so a future "improvement" to this
        anchor's disjunction is not read as covering a case it never claimed.
        """
        harness.dom.render(ROWS)  # the stale, pre-debounce rows -- never replaced

        started = time.monotonic()
        assert self._page(harness).get_row_count() == len(ROWS)
        assert time.monotonic() - started < 1.0, (
            "the anchor must have returned immediately -- TABLE_ROWS was already "
            "present, so it never actually waited for the debounce"
        )


# ── 2. SiteListPage: the two-branch contract (no reachable search()) ────────


class TestSiteListGetRowCount:
    """`SiteListPage` exposes no `search()`, so only rows/EmptyState are reachable."""

    def _page(self, harness: Harness) -> SiteListPage:
        return SiteListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """Regression pin for the `test_req005_hybrid_sensor.py` skip-gate."""
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        """No `search()` on this page-object, so its own boundary case is moot --
        pinned instead is that a page with neither rows nor EmptyState (a
        genuinely broken mount) still returns within budget rather than hanging.
        """
        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── 3. TankListPage: the full three-branch contract ─────────────────────────


class TestTankListGetRowCount:
    def _page(self, harness: Harness) -> TankListPage:
        return TankListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """Regression pin for the many skip-gates in `test_req014_tank.py`."""
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """Regression pin for `test_search_filters_tanks_by_name`'s
        `wait_for_no_search_results` gate in `test_req014_tank.py`.
        """
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_the_anchor_is_a_no_op_while_a_search_debounce_is_in_flight(
        self, harness: Harness
    ) -> None:
        """The measured boundary, same shape as `PlantInstanceListPage`'s.

        Why `test_req014_tank.py` routes its search-then-read call sites
        through `wait_for_search_applied`/`wait_for_no_search_results` rather
        than this anchor.
        """
        harness.dom.render(ROWS)

        started = time.monotonic()
        assert self._page(harness).get_row_count() == len(ROWS)
        assert time.monotonic() - started < 1.0


# ── 4. WateringLogListPage: the full three-branch contract ──────────────────


class TestWateringLogListGetRowCount:
    def _page(self, harness: Harness) -> WateringLogListPage:
        return WateringLogListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """Regression pin for the many skip-gates in `test_req004_watering_log.py`."""
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """Regression pin for `test_search_filters_table_rows`'s #946 fix.

        Before the fix, `filtered_count < row_count or has_search_chip()`
        stood in `test_req004_watering_log.py`: the chip half of that
        disjunction renders on any non-empty term regardless of whether the
        filter has actually run, which made the check pass even on a stale
        read. It is now `wait_for_no_search_results` followed by
        `assert filtered_count == 0`, which this pins the settled side of.
        """
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_the_anchor_is_a_no_op_while_a_search_debounce_is_in_flight(
        self, harness: Harness
    ) -> None:
        """The measured boundary -- `search()`'s own docstring makes this claim explicit."""
        harness.dom.render(ROWS)

        started = time.monotonic()
        assert self._page(harness).get_row_count() == len(ROWS)
        assert time.monotonic() - started < 1.0


# ── 5. WorkflowListPage: the one-branch contract (card grid, no empty-state hook) ──


class TestWorkflowListGetCardCount:
    """The structural outlier: no `EmptyState`/`no-search-results` testid exists.

    `WorkflowTemplateListPage.tsx` renders both its "no workflows" and its
    "search matched nothing" branches as a bare, untagged `Box`, so
    `wait_for_list_content` disjoins over `WORKFLOW_CARDS` alone. The
    genuinely-empty case therefore always spends the anchor's own bounded
    budget rather than reaching a fast branch -- the point pinned by the
    second test below, which would otherwise be indistinguishable from a hang.
    """

    def _page(self, harness: Harness) -> WorkflowListPage:
        return WorkflowListPage(harness.driver, "http://stub.invalid")

    def _render_cards(self, harness: Harness, names: list[str]) -> None:
        """Render *names* as `workflow-card-<name>` nodes.

        `TableDom.render()` hard-codes the `data-table-row` testid, so a
        card grid -- addressed by the `[data-testid^='workflow-card-']`
        *prefix* locator -- is modelled with `render_dialog`, which accepts an
        arbitrary testid, called once per card.
        """
        for name in names:
            harness.dom.render_dialog(f"workflow-card-{name}")

    def test_outlives_a_late_render_of_cards(self, harness: Harness) -> None:
        """Regression pin for the many skip-gates in `test_req006_workflow.py`.

        `WorkflowTemplateListPage.tsx`'s own `LoadingSkeletonCards` carries no
        `data-testid='loading-skeleton'`, so `open()`'s
        `wait_for_loading_complete()` is a no-op here -- this anchor is the
        *only* protection against the pre-fetch window on this page.
        """
        _render_after(harness, PROBES, lambda: self._render_cards(harness, ROWS))

        assert self._page(harness).get_card_count() == len(ROWS)

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        """The genuinely-empty case, which this page always reaches by budget.

        Unlike the DataTable pages, there is no `empty-state`/`no-search-results`
        fast branch to land on first -- pinned so this always-bounded, never-fast
        behaviour is read as intended rather than as a latent hang.
        """
        started = time.monotonic()
        assert self._page(harness).get_card_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK
