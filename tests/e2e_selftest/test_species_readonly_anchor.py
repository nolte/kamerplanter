"""`SpeciesDetailPage.is_read_only()` must answer about a page that has rendered.

## The failure this comes from

`test_edit_species_data` (TC-001-031) failed in the 2026-08-13 nightly with a
15 s timeout waiting for the description field. The checkpoint screenshot taken
one line earlier — `TC-REQ-001-039_before-edit` — shows the whole detail route
as a `LoadingSkeleton`: no title, no tabs, no form, no banner.

The read in between is the defect:

    species_list.click_row(0)
    species_list.wait_for_url_contains("/stammdaten/species/")
    ...
    if species_detail.is_read_only():
        pytest.skip(...)              # <- never taken
    species_detail.set_field("description", ...)   # <- 15 s timeout

`SpeciesDetailPage.tsx` returns `LoadingSkeleton` **instead of** the page while
its fetch is in flight, so the read-only banner does not exist yet — and a bare
`find_elements(READONLY_BANNER)` cannot tell "not loaded" from "not read-only".
The URL wait does not help: the URL changes on navigation, long before the
species is fetched. An origin-protected species therefore skipped its own skip
gate and went on to wait 15 s for an editable field it renders on no code path.

This is the `has_care_card` defect class of #946 wave 1, on a reader that had
not been swept: an unanchored absence read feeding a `pytest.skip(...)`.

## What the anchor is, and what it is not

`wait_for_detail_content()` waits for a *settled branch* of the route (the page
title, or one of the error surfaces) with the skeleton gone. It is an **anchor**,
not an assertion: it suppresses its own failure, because "this species has no
read-only banner" is a legitimate answer the caller must still be able to
observe. What it removes is the third state — "nothing has rendered" — being
reported as the second.

Both halves are pinned below. An anchor that always answered `True` would pass
the late-render test and fail the settled-editable one; an anchor that never
waited would pass the settled one and fail the late-render one.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.species_detail_page import SpeciesDetailPage

# The stub itself, not the fixture function -- see `test_list_page_readers.py`
# for why a thin local fixture over the same stub avoids Ruff's F811.
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Short enough that the loud cases do not spend `DEFAULT_TIMEOUT`, long enough
#: for several poll cycles -- the value the wave-9 module uses.
SETTLE_TIMEOUT = 2

#: Probes the anchor must survive before the content is built.
PROBES = 3


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed *probes* times.

    Hooked on both `find_elements` and the branch-probe script, because
    `wait_for_settled` sweeps its branches through one `execute_script`
    round-trip (`BasePage._PROBE_CSS_BRANCHES`) while the skeleton poll uses
    `find_elements`.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook
    harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook


class TestIsReadOnly:
    """The two-part contract: outlive a late render, still report a settled absence."""

    def _page(self, harness: Harness) -> SpeciesDetailPage:
        return SpeciesDetailPage(harness.driver, "http://stub.invalid")

    def _render_protected_species(self, harness: Harness) -> None:
        """The settled page of an origin-protected species.

        Title and banner in one snapshot because `SpeciesDetailPage.tsx` renders
        them in one commit -- the banner sits directly above the tab strip in
        the same returned tree, so a frame with the title but no banner is a
        frame in which the species genuinely is editable.
        """
        harness.dom.render_dialog("page-title")
        harness.dom.render_dialog("species-readonly-banner")

    def test_outlives_a_late_render_of_the_protected_page(self, harness: Harness) -> None:
        """The read must not sample the skeleton frame and call it "editable".

        This is the nightly failure, reduced: before the anchor the reader
        answered `False` on probe 1 and never looked again, so the skip gate
        below it could not fire and the test went on to wait for a field the
        page never renders.
        """
        _render_after(harness, PROBES, lambda: self._render_protected_species(harness))

        assert self._page(harness).is_read_only() is True

    def test_still_reports_a_settled_editable_species(self, harness: Harness) -> None:
        """A tenant-owned species is a real `False`, and a fast one.

        The half that keeps the anchor honest: it must not convert "no banner"
        into "wait for one", which would make every editable species pay the
        full budget and would report the same answer as an unanchored read for
        the wrong reason.
        """
        harness.dom.render_dialog("page-title")

        started = time.monotonic()
        assert self._page(harness).is_read_only() is False
        assert time.monotonic() - started < 1.0, (
            "the page is already settled -- the anchor must return at once"
        )

    def test_gives_up_rather_than_hangs_when_nothing_ever_settles(self, harness: Harness) -> None:
        """Neither branch arrives: the reader answers, bounded, instead of raising.

        A route that never settles is the caller's own assertion to fail -- and
        it will, since the field it goes on to read is not there either. What
        must not happen is this reader turning into the place a stuck page
        raises, since it is called from skip gates.
        """
        started = time.monotonic()

        assert self._page(harness).is_read_only(timeout=SETTLE_TIMEOUT) is False

        assert time.monotonic() - started <= SETTLE_TIMEOUT + 1.5, (
            "the anchor is called with SETTLE_TIMEOUT in this test and must "
            "not outrun it by more than one poll cycle"
        )

    def test_the_anchor_waits_for_the_skeleton_to_go(self, harness: Harness) -> None:
        """A settled branch alone is not enough while the skeleton is still up.

        `SpeciesDetailPage` mounts nothing but the skeleton while loading, but
        the branch probe would also be satisfied by a `page-title` left over
        from a route that is still being replaced -- the "read from the page you
        just left" shape. `require_no_skeleton` is what rules that frame out.

        The skeleton is *unmounted* by the late render, so this runs through the
        anchor's success path. Leaving it up would prove the same assertion
        through the suppressed timeout instead -- and cost the full budget in a
        tier that gates every PR.
        """
        harness.dom.render_dialog("page-title")
        skeleton = harness.dom.render_dialog("loading-skeleton")

        def settle() -> None:
            skeleton.attached = False
            self._render_protected_species(harness)

        _render_after(harness, PROBES, settle)

        started = time.monotonic()
        assert self._page(harness).is_read_only(timeout=SETTLE_TIMEOUT) is True
        assert time.monotonic() - started <= SETTLE_TIMEOUT + 1.5, (
            "the anchor must return once the skeleton is gone, not spend its budget"
        )


class TestWaitForDetailContent:
    """The anchor on its own: it is a wait, and it is not an assertion."""

    def test_returns_without_raising_when_the_route_never_settles(self, harness: Harness) -> None:
        page = SpeciesDetailPage(harness.driver, "http://stub.invalid")

        page.wait_for_detail_content(timeout=1)  # must not raise
