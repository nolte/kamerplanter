"""Unit tests for the LOWER-bucket readers fixed in #946 wave 10.

## Scope

Wave 10 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
covers the two flagged wave-8 duplicates plus the remaining LOWER-bucket
list/section page-objects: `PlantInstanceListExt` (`phase_transition_page.py`,
the pre-fix duplicate of the now-fixed `PlantInstanceListPage.get_row_count`),
`PlantInstanceDetailExt` (same file, a *separate* class -- only its phase
history readers were in scope), `FeedingEventListPage`, `CalendarPage`
(season overview + sowing calendar views), `CompanionPlantingPage`,
`CropRotationPage`, and `NotificationCenterPage`.

Per reader, the fix is one of:

1. **The `has_care_card` shape** (`PlantInstanceListExt.get_row_count`,
   `FeedingEventListPage.get_row_count`): a bare `find_elements` read right
   after `open()`, in the pre-fetch window before the table's rows/`EmptyState`/
   `no-search-results` panel has committed. Fixed with the same
   `wait_for_list_content()` anchor wave 7/8 built for the DataTable cluster.
2. **The forbidden fixed-sleep anti-pattern** (`CompanionPlantingPage.
   select_species`, `CropRotationPage.select_family`): both used to follow a
   species/family selection with a bare `time.sleep(1)` -- replaced with a
   condition-based `wait_for_companion_data()`/`wait_for_successor_content()`
   anchor over the two cards / successor-list-or-empty-state the selection's
   own async fetch settles into.
3. **The tab-switch content race** (`CalendarPage.wait_for_season_content`/
   `.wait_for_sowing_content`): `CalendarPage.tsx` refetches
   `seasonOverview`/`sowingEntries` fresh on every switch into those views,
   replacing the whole view (cards *and* its own `EmptyState`) with a
   `LoadingSkeleton` for the length of the fetch -- the same class
   `SpeciesDetailPage.get_cultivar_count` was fixed for in wave 9, here at the
   view-switch entry point rather than in each of the five readers scoped to
   each view.
4. **The silent-empty-reader duplicate** (`NotificationCenterPage.
   get_notification_cards`/`.has_notification`): the sibling reader
   `get_action_done_buttons` was already fixed (wave 5) for the exact same
   per-open refetch race this page's `NotificationDrawer.tsx` has; these two
   were never converted to the same `await_presence` anchor.

## Why three anchors are *not* measured end-to-end here

`PlantInstanceDetailExt.wait_for_phase_history_content` and
`CompanionPlantingPage.wait_for_companion_data` are anchored on selector
shapes this module's stub cannot resolve at all -- a compound descendant
selector (`"[data-testid='phases-tab-content'] [data-testid='data-table']"`)
for the former, and a By.XPATH ancestor-of-text-node locator
(`COMPATIBLE_CARD`/`INCOMPATIBLE_CARD`) for the latter. `test_row_helpers.py`
documents the identical gap for `PlantInstanceDetailPage.wait_for_phases_tab_
content`'s sibling reader `get_task_rows`: "measured directly for the anchor
... rather than through the row count they guard" is not available here
either, because *neither* branch of either anchor is a selector shape
`_matches` answers -- not even the anchor's own presence poll can observe a
late-arriving match. Both are therefore pinned only for the property that
*is* observable regardless (a genuine, bounded "never settles" does not hang
past budget); their "outlives a late render" direction is analytic, not
measured, exactly the stub gap wave 3 hit on the sibling class before this one.

`CropRotationPage.wait_for_successor_content` and `CalendarPage.
wait_for_season_content`/`.wait_for_sowing_content` are the partial case: one
branch of each (`SUCCESSOR_ITEMS`'s testid *prefix*; `EMPTY_STATE`'s exact
testid) is a matchable shape, the other (`SUCCESSOR_LIST`'s bare-MUI-class
compound; `SOWING_CARDS`'s/`SEASON_MONTH_CARDS`'s compound descendant/class
selectors) is not. Each is therefore measured end-to-end through its
matchable branch (the anchor genuinely outlives a late render, not merely a
one-shot sample) and only the unmatchable branch stays analytic.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py` and the wave 7-9
files: a **real** `selenium.webdriver.remote.webdriver.WebDriver` runs over a
fake command executor, so `WebDriverWait`, `resolve_settled_branch`/
`wait_for_any_present` and the real page objects all run unmodified. Only the
wire is fake. Provoking a "read one frame too early" race in a real browser
would mean hitting a React commit at a precise instant -- the flakiest
possible way to assert a deterministic contract.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py` and prior waves' files

Per the wave-10 task brief, matching waves 7-9: `test_row_helpers.py` is
shared across parallel absence-check waves and edits to it collide, and each
prior wave's own file is a sibling PR's file for the same reason. This module
imports the `Harness`/`TableDom`/`StubConnection`/`Command` stub from
`test_row_helpers` and adds no classes to it, and does not touch any other
wave's file either.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.base_page import DEFAULT_TIMEOUT, IMPLICIT_WAIT_EQUIVALENT
from tests.e2e.pages.calendar_page import CalendarPage
from tests.e2e.pages.companion_planting_page import CompanionPlantingPage
from tests.e2e.pages.crop_rotation_page import CropRotationPage
from tests.e2e.pages.feeding_event_list_page import FeedingEventListPage
from tests.e2e.pages.notification_center_page import NotificationCenterPage
from tests.e2e.pages.phase_transition_page import PlantInstanceDetailExt, PlantInstanceListExt

# The stub itself, not the fixture function -- see wave 7/8/9's own files for
# why this is a thin local fixture over the same stub rather than a reused
# fixture function (Ruff F811).
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Slack applied to `IMPLICIT_WAIT_EQUIVALENT` for elapsed-time bounds,
#: mirroring `test_row_helpers.BUDGET_SLACK` / wave 8's own constant.
BUDGET_SLACK = 1.5

#: How many probes an anchor's `wait_for_any_present` must survive before the
#: content is built, mirroring wave 7/8/9's own `_render_after`.
PROBES = 3

#: Short enough that the loud-failure/no-hang cases below do not spend
#: `DEFAULT_TIMEOUT`, matching wave 9's `SETTLE_TIMEOUT`.
SETTLE_TIMEOUT = 2

ROWS = ["Alpha-Row", "Beta-Row", "Gamma-Row"]


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times.

    Hooked on both `find_elements` and the branch-probe script:
    `wait_for_any_present` sweeps its branches through one `execute_script`
    round-trip per attempt (`BasePage._PROBE_CSS_BRANCHES`), so a hook on
    `find_elements` alone would never fire while the anchor itself is waiting.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


# ── 1. PlantInstanceListExt.get_row_count: the wave-8 duplicate, fixed ──────


class TestPlantInstanceListExtGetRowCount:
    """`phase_transition_page.PlantInstanceListExt`, flagged by wave 8 as a
    verbatim duplicate of `PlantInstanceListPage`'s pre-fix `get_row_count`
    shape. Same three-branch contract as wave 8's own pin for that class.
    """

    def _page(self, harness: Harness) -> PlantInstanceListExt:
        return PlantInstanceListExt(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """Regression pin for the skip-gates and row-index loops in
        `test_req003_phasensteuerung.py` (`_get_first_plant_key`, `_ensure_plants`,
        and the `TestPhaseStateMachineEdgeCases` row loops all read this right
        after `open()`).
        """
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── 2. FeedingEventListPage.get_row_count: the plain vacuous shape ──────────


class TestFeedingEventListGetRowCount:
    """`feeding_event_list_page.py` -- the same unanchored `find_elements`
    shape wave 7/8 fixed across the DataTable cluster, gating a `pytest.skip`
    and the search-filter bidirectional count comparison in
    `test_req004_feeding_events.py`.
    """

    def _page(self, harness: Harness) -> FeedingEventListPage:
        return FeedingEventListPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_row_count() == len(ROWS)

    def test_still_reports_a_settled_empty_state(self, harness: Harness) -> None:
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_still_reports_a_settled_no_search_results_panel(self, harness: Harness) -> None:
        """Regression pin for `test_feeding_event_search_filters_results`'s
        `wait_for_no_search_results` reroute (#946 wave 10's debounce-trap fix).
        """
        harness.dom.render_dialog("no-search-results")

        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started < 1.0

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        started = time.monotonic()
        assert self._page(harness).get_row_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── 3. CropRotationPage.wait_for_successor_content: fixed-sleep replacement ─


class TestCropRotationSuccessorContent:
    """`select_family`'s `time.sleep(1)` replaced with a condition wait.

    Measured through the matchable branch (`SUCCESSOR_ITEMS`, a testid
    *prefix*) and the matchable `EMPTY_STATE` (an exact testid); `SUCCESSOR_
    LIST` (`.MuiList-root .MuiListItem-root`, a compound bare-class selector)
    is not a shape `test_row_helpers._matches` resolves, so `get_successor_
    count`'s own *positive* read stays analytic -- see the module docstring.
    """

    def _page(self, harness: Harness) -> CropRotationPage:
        return CropRotationPage(harness.driver, "http://stub.invalid")

    def test_anchor_outlives_a_late_render_of_successor_items(self, harness: Harness) -> None:
        """The anchor itself must not sample the pre-fetch instant.

        Before the fix this was a fixed `time.sleep(1)`: too short on a loaded
        CI runner leaves `get_successor_count()`/`get_successor_names()`
        reading the *previous* family's successors (or a bare skeleton).
        """
        _render_after(
            harness,
            PROBES,
            lambda: harness.dom.render_dialog("successor-family-link-solanaceae"),
        )
        page = self._page(harness)

        page.wait_for_successor_content(timeout=SETTLE_TIMEOUT)

        assert page.driver.find_elements(*page.SUCCESSOR_ITEMS), (
            "the anchor returned before the late-rendered branch actually appeared"
        )

    def test_get_successor_count_reports_a_settled_empty_state_fast(self, harness: Harness) -> None:
        """A family with zero rotation successors is a real `0`, not a timeout.

        Regression pin for `test_empty_state_when_no_successors`'s `assert
        has_empty_state() or True` -> `assert has_empty_state()` fix: this
        settled-empty branch must be reached fast, not by spending the anchor's
        full budget, for that assertion to be meaningfully falsifiable.
        """
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_successor_count() == 0
        assert time.monotonic() - started < 1.0, (
            "EMPTY_STATE is already present -- the anchor must not spend its "
            "budget once a settled branch has been reached"
        )

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        started = time.monotonic()
        assert self._page(harness).get_successor_count() == 0
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── 4. CalendarPage: the season overview / sowing calendar tab-switch race ──


class TestCalendarSeasonAndSowingContent:
    """`switch_to_season_view`/`switch_to_sowing_view` now anchor on the async
    fetch each view's tab switch triggers (`CalendarPage.tsx`'s `seasonLoading`/
    `sowingLoading`), rather than leaving every reader scoped to either view
    (`get_season_month_cards`, `get_sowing_cards`, `get_column_header_count`,
    `get_sowing_frost_chips`, `get_sowing_category_filter_chips`,
    `get_sowing_legend_items`) to read the pre-fetch window right after the
    tab click.

    Measured through the matchable `EMPTY_STATE` branch; `SEASON_MONTH_CARDS`
    (`.MuiGrid-container .MuiCard-root`) and `SOWING_CARDS`
    (`"[data-testid='calendar-page'] .MuiCard-root"`) are compound selector
    shapes `test_row_helpers._matches` does not resolve, so the populated-view
    direction stays analytic -- see the module docstring.
    """

    def _page(self, harness: Harness) -> CalendarPage:
        return CalendarPage(harness.driver, "http://stub.invalid")

    def test_season_content_outlives_a_late_render_of_empty_state(self, harness: Harness) -> None:
        """Regression pin for the `pytest.skip(...)` gates in
        `test_req015_season_overview.py` -- all four readers of
        `get_season_month_cards()` sit right after `_open_season_view()`.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render_dialog("empty-state"))
        page = self._page(harness)

        page.wait_for_season_content(timeout=SETTLE_TIMEOUT)

        assert page.driver.find_elements(*page.EMPTY_STATE), (
            "the anchor returned before the late-rendered branch actually appeared"
        )

    def test_season_content_does_not_hang_when_nothing_ever_settles(self, harness: Harness) -> None:
        page = self._page(harness)
        started = time.monotonic()

        page.wait_for_season_content(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK

    def test_sowing_content_outlives_a_late_render_of_empty_state(self, harness: Harness) -> None:
        """Regression pin for the `pytest.skip(...)` gate in
        `test_sowing_category_chip_toggle` (`test_req015_sowing_calendar.py`),
        which reads `get_sowing_category_filter_chips()` right after
        `_open_sowing_view()`.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render_dialog("empty-state"))
        page = self._page(harness)

        page.wait_for_sowing_content(timeout=SETTLE_TIMEOUT)

        assert page.driver.find_elements(*page.EMPTY_STATE), (
            "the anchor returned before the late-rendered branch actually appeared"
        )

    def test_sowing_content_does_not_hang_when_nothing_ever_settles(self, harness: Harness) -> None:
        page = self._page(harness)
        started = time.monotonic()

        page.wait_for_sowing_content(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK


# ── 5. NotificationCenterPage: the get_action_done_buttons duplicate ────────


class TestNotificationCenterGetNotificationCards:
    """`get_notification_cards`/`has_notification` never got the anchor their
    sibling `get_action_done_buttons` (wave 5) already carries, for the
    identical per-`open_drawer()` refetch race documented on both.

    Like `WorkflowListPage` (wave 8) and `get_action_done_buttons` itself,
    there is no dedicated empty-state testid on this page (`NotificationDrawer.
    tsx` renders its "nothing to show" branch as a bare, untestid'd `Box`), so
    the genuinely-empty case always spends the anchor's own bounded budget
    rather than reaching a fast branch.
    """

    def _page(self, harness: Harness) -> NotificationCenterPage:
        return NotificationCenterPage(harness.driver, "http://stub.invalid")

    def _render_cards(self, harness: Harness, keys: list[str]) -> None:
        for key in keys:
            harness.dom.render_dialog(f"notification-card-{key}")

    def test_get_notification_cards_outlives_a_late_render(self, harness: Harness) -> None:
        """Regression pin for `_drawer_notification_texts`/`_care_notification_key`
        (`test_req030_notifications.py`), both of which read
        `get_notification_keys()` -> `get_notification_cards()` right after
        `open_drawer()`.
        """
        _render_after(harness, PROBES, lambda: self._render_cards(harness, ["a", "b", "c"]))

        assert len(self._page(harness).get_notification_cards()) == 3

    def test_get_notification_cards_reports_zero_without_hanging(self, harness: Harness) -> None:
        """No empty-state fast branch exists on this page -- the reader must
        still return, bounded, once a genuinely empty drawer's budget is spent.

        Bounded by `DEFAULT_TIMEOUT`, not `IMPLICIT_WAIT_EQUIVALENT`:
        `get_notification_cards` calls `await_presence` with no explicit
        timeout, so it inherits that helper's own default -- the same budget
        `get_action_done_buttons` already spends for the identical reason.
        """
        started = time.monotonic()
        assert self._page(harness).get_notification_cards() == []
        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK

    def test_has_notification_outlives_a_late_render_of_its_key(self, harness: Harness) -> None:
        """The specific-key check must not sample before the drawer's own
        per-open refetch resolves either -- routed through `get_notification_
        keys()` rather than a bare presence check on the one testid.
        """
        _render_after(
            harness,
            PROBES,
            lambda: self._render_cards(harness, ["needle", "other"]),
        )

        assert self._page(harness).has_notification("needle") is True

    def test_has_notification_reports_a_genuine_absence(self, harness: Harness) -> None:
        """A card that never renders -- a real 'not found', not a premature one.

        Regression pin for `test_reminder_confirmation_marks_notification_read`
        (TC-REQ-030-009): a premature `False` here used to make `was_unread and
        not now_unread` pass whether or not the reminder had actually been
        confirmed, because the same premature `False` fed `now_unread` too.
        """
        self._render_cards(harness, ["other"])

        started = time.monotonic()
        assert self._page(harness).has_notification("needle") is False
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK


# ── 6. Analytic-only anchors: unmatchable selector shapes ───────────────────


class TestTheAnalyticOnlyAnchors:
    """`PlantInstanceDetailExt.wait_for_phase_history_content` and
    `CompanionPlantingPage.wait_for_companion_data` -- see the module
    docstring for why neither branch of either anchor is a selector shape this
    stub can resolve, so only the bounded "never settles" property is
    measured here. The "outlives a late render" claim for both is analytic:
    each anchor is built from the same `wait_for_any_present`/`suppress
    (AssertionError)` primitive every measured anchor above uses, and that
    primitive's own late-render behaviour *is* measured, repeatedly, in this
    module and in `test_row_helpers.py`.
    """

    def test_phase_history_content_does_not_hang(self, harness: Harness) -> None:
        page = PlantInstanceDetailExt(harness.driver, "http://stub.invalid")
        started = time.monotonic()

        page.wait_for_phase_history_content(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK
        assert page.has_phase_history() is False
        assert page.get_phase_history_count() == 0

    def test_companion_data_does_not_hang(self, harness: Harness) -> None:
        page = CompanionPlantingPage(harness.driver, "http://stub.invalid")
        started = time.monotonic()

        page.wait_for_companion_data(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK
