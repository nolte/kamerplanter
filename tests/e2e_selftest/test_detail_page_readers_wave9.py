"""Unit tests for the LOWER-bucket detail-page readers fixed in #946 wave 9.

## Scope

Wave 9 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
covers the last five LOWER-bucket detail page-objects: `LocationDetailPage`,
`CultivarDetailPage`, `SpeciesDetailPage`, `NutrientPlanDetailPage`,
`SlotDetailPage`. Unlike the HIGH bucket (waves 1-6), none of these routes
unmount their whole content tree on every refetch, so most of their readers
turned out to be either already anchored by their one call site (a preceding
``open()``/``click_delete()`` that itself waits) or dead code with zero call
sites at all -- see the wave's chat report for the full per-reader ledger.

Two real defect classes survived that review, and this module pins both:

1. **The guarded-dismissal gap** (`SlotDetailPage.cancel_delete` /
   `NutrientPlanDetailPage.cancel_delete`): neither action waited for its
   `ConfirmDialog` to actually leave the DOM, so the test-file assertion right
   after cancelling was a raw, instantaneous, negated presence read --
   satisfiable by a dialog that is merely mid-fade-out. Same shape as the
   `TestTheGuardedDialogDismissals` section of `test_row_helpers.py` (#946
   waves 4-6), fixed here with the identical
   `wait_for_confirm_dialog_closed()`/`is_absent_within` pairing.

2. **The tab-switch content race** (`SpeciesDetailPage.get_cultivar_count` /
   `.get_phase_count`): `CultivarListSection` and `GrowthPhaseListSection`
   each mount fresh -- and start their own `useEffect`-driven fetch fresh --
   every time their tab becomes active (`TabPanel` unmounts a hidden panel's
   children entirely), independently of `SpeciesDetailPage`'s own top-level
   loading flag. `DataTable`'s `loading` prop then replaces rows *and*
   `EmptyState` alike with a skeleton for the length of every fetch --
   initial tab mount, and every subsequent create/edit/delete refetch. Both
   readers used to be a bare `find_elements` with no wait at all, and both
   feed a `pytest.skip(...)` gate or a before/after mutation count comparison
   in the test files -- the exact shape `has_care_card` (#945) and
   `get_row_count` (#946 wave 7) were fixed for elsewhere. The fix is the same
   two-branch `wait_for_any_present` anchor those already carry, scoped to
   this page's own two tab sections rather than reused from any of them.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py` and
`test_list_page_readers.py`: a **real**
`selenium.webdriver.remote.webdriver.WebDriver` runs over a fake command
executor, so `WebDriverWait`, `resolve_settled_branch` and the real page
objects all run unmodified. Only the wire is fake.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py`

Per the wave-9 task brief (matching wave 7's `test_list_page_readers.py`):
`test_row_helpers.py` is shared across parallel absence-check waves and edits
to it collide. This module imports the `Harness`/`TableDom`/`StubConnection`
stub from there and adds no classes to it -- and, per the brief, does not
touch `test_row_helpers.py` or any other wave's file either.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.nutrient_plan_detail_page import NutrientPlanDetailPage
from tests.e2e.pages.slot_detail_page import SlotDetailPage
from tests.e2e.pages.species_detail_page import SpeciesDetailPage

# The stub itself, not the fixture function -- see `test_list_page_readers.py`
# for why a thin local fixture over the same stub avoids Ruff's F811 rather
# than re-exporting `test_row_helpers.harness` directly.
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Short enough that the loud-failure cases do not spend `DEFAULT_TIMEOUT`,
#: long enough for `WebDriverWait`'s poll interval to run several cycles --
#: same value `test_row_helpers.py` uses for its own settling waits.
SETTLE_TIMEOUT = 2

#: How many probes an anchor's `wait_for_any_present` must survive before the
#: content is built, mirroring `test_row_helpers.py`'s
#: `TestTheAnchoredSectionReaders._render_after` / `test_list_page_readers.py`'s
#: `_render_after`.
PROBES = 3


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times.

    Hooked on both `find_elements` and the branch-probe script: the anchor's
    `wait_for_any_present` sweeps its branches through one `execute_script`
    round-trip (`BasePage._PROBE_CSS_BRANCHES`), so a hook on `find_elements`
    alone would never fire while the anchor itself is waiting.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


def _detach_after(harness: Harness, lookups: int, node: Any) -> None:
    """Detach *node* once the DOM has been scanned *lookups* times.

    Identical shape to `test_row_helpers.TestTheGuardedDialogDismissals
    ._detach_after` -- kept as a local copy since it is a three-line closure
    over this module's own `harness`, not that module's public surface.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == lookups:
            node.attached = False

    harness.connection.before[Command.FIND_ELEMENTS] = hook


ROWS = ["Alpha-Row", "Beta-Row", "Gamma-Row"]


# ── 1. Guarded delete-dialog dismissals (#946 wave 9) ────────────────────────


class TestTheGuardedDialogDismissals:
    """`wait_for_confirm_dialog_closed`, replacing a raw negated presence read.

    MUI's Dialog unmounts only after its exit transition finishes, so
    `assert not page.is_confirm_dialog_visible()` (Slot) /
    `assert not page.is_confirm_dialog_open()` (NutrientPlan) sampled right
    after clicking Cancel could still see the dialog mid-fade-out and report
    it as open -- a guarded-dismissal gap
    (`spec/project/e2e-test-stability`), not a data-fetch one. Same shape as
    `test_row_helpers.TestTheGuardedDialogDismissals`, pinned independently
    here for the two page objects this wave touches.
    """

    def test_slot_confirm_dialog_outlives_the_fade_out(self, harness: Harness) -> None:
        node = harness.dom.render_dialog("confirm-dialog")
        _detach_after(harness, 3, node)
        page = SlotDetailPage(harness.driver, "http://stub.invalid")

        assert page.wait_for_confirm_dialog_closed(timeout=SETTLE_TIMEOUT) is True

    def test_slot_confirm_dialog_still_reports_a_dialog_that_stays(self, harness: Harness) -> None:
        harness.dom.render_dialog("confirm-dialog")
        page = SlotDetailPage(harness.driver, "http://stub.invalid")

        assert page.wait_for_confirm_dialog_closed(timeout=SETTLE_TIMEOUT) is False

    def test_nutrient_plan_confirm_dialog_outlives_the_fade_out(self, harness: Harness) -> None:
        node = harness.dom.render_dialog("confirm-dialog")
        _detach_after(harness, 3, node)
        page = NutrientPlanDetailPage(harness.driver, "http://stub.invalid")

        assert page.wait_for_confirm_dialog_closed(timeout=SETTLE_TIMEOUT) is True

    def test_nutrient_plan_confirm_dialog_still_reports_a_dialog_that_stays(
        self, harness: Harness
    ) -> None:
        harness.dom.render_dialog("confirm-dialog")
        page = NutrientPlanDetailPage(harness.driver, "http://stub.invalid")

        assert page.wait_for_confirm_dialog_closed(timeout=SETTLE_TIMEOUT) is False


# ── 2. SpeciesDetailPage: the cultivar-tab content anchor (#946 wave 9) ──────


class TestSpeciesDetailCultivarCount:
    """`wait_for_cultivars_content` / `get_cultivar_count`, the full two-part contract.

    `test_click_cultivar_row_navigates_to_detail` and
    `test_cultivar_traits_in_german` both gate a `pytest.skip(...)` on
    `get_cultivar_count() == 0` right after `click_tab_by_label("Sorten")` --
    the exact skip-gate-on-an-unanchored-reader shape #946 wave 1 fixed for
    `has_overdue_section`.
    """

    def _page(self, harness: Harness) -> SpeciesDetailPage:
        return SpeciesDetailPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """A read right after the tab switch must not sample the pre-fetch instant.

        Before the fix this was a bare `find_elements`, answered `0` on probe
        1 and never looked again -- silently turning "the tab is still
        loading" into "this species has no cultivars".
        """
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_cultivar_count() == len(ROWS)

    def test_still_reports_a_settled_empty_species(self, harness: Harness) -> None:
        """A species with no cultivars yet is a real `0`, not a timeout."""
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_cultivar_count() == 0
        assert time.monotonic() - started < 1.0, (
            "EmptyState is already present -- the anchor must not spend its "
            "budget once a settled branch has been reached"
        )

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        """Neither branch ever arrives -- the anchor gives up, not hangs."""
        started = time.monotonic()
        assert self._page(harness).get_cultivar_count() == 0
        assert time.monotonic() - started <= 3 + 1.5, (
            "wait_for_cultivars_content's default budget is IMPLICIT_WAIT_EQUIVALENT (3s); "
            "an un-settled tab must not cost more than that plus one retry's slack"
        )


# ── 3. SpeciesDetailPage: the growth-phase-tab content anchor (#946 wave 9) ──


class TestSpeciesDetailPhaseCount:
    """`wait_for_phases_content` / `get_phase_count`, the full two-part contract.

    `test_edit_growth_phase` skip-gates on `get_phase_count() == 0`;
    `test_create_growth_phase` / `test_delete_growth_phase` /
    `_provision_species_with_phase` all compare it before and after a
    mutation -- the bidirectional-counter shape #946 targets directly.
    """

    def _page(self, harness: Harness) -> SpeciesDetailPage:
        return SpeciesDetailPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_rows(self, harness: Harness) -> None:
        """A count taken mid-refetch (e.g. right after a create) must not read 0.

        Every create/edit/delete on this tab re-triggers
        `GrowthPhaseListSection`'s own `load()`, which swaps the table for a
        skeleton -- exactly the window `initial_count`/`provisioned_count`/
        `new_count` in `test_req001_lifecycle.py` read through.
        """
        _render_after(harness, PROBES, lambda: harness.dom.render(ROWS))

        assert self._page(harness).get_phase_count() == len(ROWS)

    def test_still_reports_a_settled_empty_lifecycle(self, harness: Harness) -> None:
        """A freshly created lifecycle config with no phases yet is a real `0`."""
        harness.dom.render_dialog("empty-state")

        started = time.monotonic()
        assert self._page(harness).get_phase_count() == 0
        assert time.monotonic() - started < 1.0

    def test_reports_zero_and_does_not_hang_when_nothing_ever_settles(
        self, harness: Harness
    ) -> None:
        started = time.monotonic()
        assert self._page(harness).get_phase_count() == 0
        assert time.monotonic() - started <= 3 + 1.5
