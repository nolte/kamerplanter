"""Unit tests for the LOWER-bucket list-page `get_row_count()` anchor (#946 wave 7).

## Scope

Wave 7 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
covers the DataTable list-page cluster: `FertilizerListPage`,
`BotanicalFamilyListPage`, `HarvestBatchListPage`, `NutrientPlanListPage`,
`DiseaseListPage`, `PestListPage`. All six carried the identical shape:

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

`PAGE` mounts synchronously on every one of these routes -- before the first
fetch resolves -- so a read taken right after `open()` can land in a frame
where none of the table's three settled branches (rows, `EmptyState`, or the
`no-search-results` panel) has committed yet. Several call sites gate a
`pytest.skip(...)` or a bidirectional count comparison directly on this read,
which is the exact `has_care_card` defect class `pflege_dashboard_page.py`
fixed for the HIGH bucket: an unanchored `0` there is indistinguishable from a
table that genuinely has no rows.

The fix adds a page-owned `wait_for_list_content()` anchor -- built the same
way as `PflegeDashboardPage.wait_for_dashboard_content()`, on
`wait_for_any_present` over the three settled-branch locators, wrapped in
`suppress(AssertionError)` so a genuinely empty table is never blocked -- and
`get_row_count()` calls it before reading. This module pins the same two-part
contract every anchored reader in `test_row_helpers.py` is held to: it must
**outlive a late render** (the anchor is a real wait, not a renamed sample),
and it must **still report a genuine, settled absence** (the anchor does not
silently convert "empty" into "always non-zero" or hang past its budget).

A third class per representative page pins the *measured boundary* of the fix,
because the page-object docstrings make an explicit negative claim: the anchor
does **not** protect a read taken while a specific search term's debounce is
still in flight, since the *previous*, unfiltered rows keep `TABLE_ROWS`
satisfied throughout that window and `wait_for_any_present` returns at once.
That is why the wave's test-file fixes route search-then-read call sites
through `wait_for_search_applied`/`wait_for_no_search_results` instead of
relying on this anchor -- pinned here so a later change cannot "fix" the
boundary claim without this test noticing the anchor started doing more than
it advertises (or silently doing less).

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py`: a **real**
`selenium.webdriver.remote.webdriver.WebDriver` runs over a fake command
executor, so `WebDriverWait`, `resolve_settled_branch` and the real page
objects all run unmodified. Only the wire is fake. Provoking a "read one frame
too early" race in a real browser would mean hitting a React commit at a
precise instant -- the flakiest possible way to assert a deterministic
contract.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py`

Per the wave-7 task brief: `test_row_helpers.py` is shared across parallel
absence-check waves and edits to it collide. This module imports the
`Harness`/`TableDom`/`Command` stub from there and adds no classes to it.
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
from tests.e2e.pages.botanical_family_list_page import BotanicalFamilyListPage
from tests.e2e.pages.disease_list_page import DiseaseListPage
from tests.e2e.pages.fertilizer_list_page import FertilizerListPage
from tests.e2e.pages.harvest_batch_list_page import HarvestBatchListPage
from tests.e2e.pages.nutrient_plan_list_page import NutrientPlanListPage
from tests.e2e.pages.pest_list_page import PestListPage

# The stub itself, not the fixture function: importing `test_row_helpers.harness`
# directly and reusing it as a fixture makes every `harness: Harness` parameter
# in this module read as "redefinition of unused import" to Ruff (F811), since
# Pyflakes cannot tell a fixture re-export from an accidental shadow. A thin
# local fixture over the same `TableDom`/`StubConnection`/`Harness` stub avoids
# that false positive while still importing the stub from `test_row_helpers`
# rather than duplicating it, per the wave-7 brief.
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
#: `W3C_EXECUTE_SCRIPT` -- exactly as `test_row_helpers.py`'s own
#: `TestTheAnchoredSectionReaders._render_after` does for `has_overdue_section`.
PROBES = 3


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times.

    Shared helper, structurally identical to
    `test_row_helpers.TestTheAnchoredSectionReaders._render_after` -- kept as a
    local copy rather than an import because it is a three-line closure over
    this module's own `harness`, not part of that module's public surface.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


ROWS = ["Alpha-Row", "Beta-Row", "Gamma-Row"]


# ── 1. FertilizerListPage: the full three-branch contract ───────────────────


class TestFertilizerListGetRowCount:
    """The representative, exhaustive pin: all three settled branches plus the boundary."""

    def _page(self, harness: Harness) -> FertilizerListPage:
        return FertilizerListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """A read right after `open()` must not sample the pre-fetch instant.

        Before the fix this was a bare `find_elements`, answered `0` on probe 1
        and never looked again -- the exact shape a `pytest.skip("No
        fertilizers...")` right after `open()` turns into a silent skip of real
        coverage whenever the fetch has not landed yet.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        """A tenant with an empty catalogue is a real `0`, not a timeout."""
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0, (
            "EmptyState is already present -- the anchor must not spend its "
            "budget once a settled branch has been reached"
        )

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """The third branch: a search that legitimately matched nothing."""
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
        the wave's test-file fixes route search-then-read call sites through
        `wait_for_search_applied`/`wait_for_no_search_results` first rather
        than relying on this anchor. Pinned so a future "improvement" to this
        anchor's disjunction is not read as covering a case it never claimed.
        """
        harness.dom.render(ROWS)  # the stale, pre-debounce rows -- never replaced

        started = time.monotonic()
        assert self._page(harness).get_row_count() == len(ROWS)
        assert time.monotonic() - started < 1.0, (
            "the anchor must have returned immediately -- TABLE_ROWS was already "
            "present, so it never actually waited for the debounce"
        )


# ── 2. The remaining five pages: the core two-part contract, per page-object ─
#
# Each page-object defines its own `wait_for_list_content`/`get_row_count`
# independently (no shared base-class implementation -- `base_page.py` is
# deliberately untouched by this wave, see the campaign plan §3), so each is
# pinned on its own rather than assumed identical to Fertilizer's.


class TestBotanicalFamilyListGetRowCount:
    def _page(self, harness: Harness) -> BotanicalFamilyListPage:
        return BotanicalFamilyListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0


class TestHarvestBatchListGetRowCount:
    def _page(self, harness: Harness) -> HarvestBatchListPage:
        return HarvestBatchListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0


class TestNutrientPlanListGetRowCount:
    def _page(self, harness: Harness) -> NutrientPlanListPage:
        return NutrientPlanListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0


class TestDiseaseListGetRowCount:
    def _page(self, harness: Harness) -> DiseaseListPage:
        return DiseaseListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """Regression pin for `test_search_no_results`'s #946 fix.

        Before the fix, `assert get_row_count() == 0` right after `search()`
        was satisfiable both by a debounce that had not fired yet (a stale
        non-zero read would have *failed* this specific assertion, which is
        why the test-file fix is `wait_for_no_search_results` rather than this
        anchor -- see `TestFertilizerListGetRowCount
        .test_the_anchor_is_a_no_op_while_a_search_debounce_is_in_flight`) and
        by a database seeded with zero diseases (nothing to filter at all).
        This pins that once the *panel itself* has settled, the count read
        behind it is instant and correct.
        """
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0


class TestPestListGetRowCount:
    def _page(self, harness: Harness) -> PestListPage:
        return PestListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """Regression pin for `test_search_no_results_shows_empty_message`'s #946 fix."""
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0
