"""Unit tests for `BasePage`'s branch-aware settling helpers.

They pin the properties the weak ``wait_for_loading_complete()`` lacked and the
new helpers exist to provide (`e2e-test-stability` §D):

* the wait cannot be satisfied before the content exists,
* which branch was reached is reported, not inferred,
* a non-accepted branch fails loudly and names what the app actually showed.

The last class in this file covers the same shape one level up: the settling a
*screenshot checkpoint* owes its caller, because `captureBeyondViewport` resizes
the page under test and the checkpoint has to hand it back the way it found it
(#959).
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from tests.e2e.conftest import _cdp_full_page_screenshot, _settle_after_capture
from tests.e2e.pages.base_page import BasePage, SettledState

from .fake_driver import FakeDriver

PAGE = (By.CSS_SELECTOR, "[data-testid='tank-detail-page']")
SKELETON = "[data-testid='loading-skeleton']"
ERROR = "[data-testid='error-display']"
ERROR_MESSAGE = "[data-testid='error-message']"
EMPTY = "[data-testid='empty-state']"


def page_for(driver: FakeDriver) -> BasePage:
    return BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]


# ── resolve_settled_branch: the pure contract ────────────────────────────────


class TestResolveSettledBranch:
    """Branch resolution is a pure function of the declared order."""

    def test_returns_none_when_nothing_is_present(self) -> None:
        assert BasePage.resolve_settled_branch({"content": PAGE}, []) is None

    def test_reports_the_reached_branch_and_its_locator(self) -> None:
        state = BasePage.resolve_settled_branch({"content": PAGE}, ["content"])
        assert state == SettledState(branch="content", locator=PAGE, present=("content",))

    def test_declared_order_decides_when_two_branches_are_present(self) -> None:
        """A page root plus a section-level error resolves to the root.

        The declaration is the contract: naming ``content`` first says "if the
        page root is there, that is the outcome I am reading".
        """
        branches = {"content": PAGE, "error": (By.CSS_SELECTOR, ERROR)}
        state = BasePage.resolve_settled_branch(branches, ["error", "content"])
        assert state is not None
        assert state.branch == "content"
        assert state.present == ("content", "error")

    def test_reversing_the_declaration_reverses_the_precedence(self) -> None:
        branches = {"error": (By.CSS_SELECTOR, ERROR), "content": PAGE}
        state = BasePage.resolve_settled_branch(branches, ["content", "error"])
        assert state is not None
        assert state.branch == "error"

    def test_present_entries_outside_the_declaration_are_ignored(self) -> None:
        state = BasePage.resolve_settled_branch({"content": PAGE}, ["empty", "content"])
        assert state is not None
        assert state.present == ("content",)

    def test_is_branch_compares_the_winner(self) -> None:
        state = BasePage.resolve_settled_branch({"content": PAGE}, ["content"])
        assert state is not None
        assert state.is_branch("content")
        assert not state.is_branch("error-display")


# ── probe_branches: one round-trip, declared order ───────────────────────────


class TestProbeBranches:
    def test_probes_every_css_branch_in_a_single_round_trip(self) -> None:
        driver = FakeDriver({ERROR})
        page = page_for(driver)
        present = page.probe_branches(
            {
                "content": PAGE,
                "error": (By.CSS_SELECTOR, ERROR),
                "empty": (By.CSS_SELECTOR, EMPTY),
            }
        )
        assert present == ("error",)
        # One script call for three branches, not three find_elements. The
        # original reason was cost -- each empty result paid the session's
        # implicit wait, which #835 removed. What the assertion now pins is
        # atomicity: three lookups are three instants, so a branch that appears
        # midway through the sweep could be reported next to one that has
        # already gone, and "exactly one branch matched" would describe the
        # sweep rather than the page.
        assert driver.script_calls == 1
        assert driver.find_elements_calls == 0

    def test_reports_in_declared_order_not_probe_order(self) -> None:
        driver = FakeDriver({ERROR, PAGE[1]})
        present = page_for(driver).probe_branches(
            {"content": PAGE, "error": (By.CSS_SELECTOR, ERROR)}
        )
        assert present == ("content", "error")

    def test_non_css_branches_fall_back_to_find_elements(self) -> None:
        driver = FakeDriver({"//div[@id='x']"})
        present = page_for(driver).probe_branches({"xpath": (By.XPATH, "//div[@id='x']")})
        assert present == ("xpath",)
        assert driver.find_elements_calls == 1


# ── wait_for_settled: cannot pass before the content exists ──────────────────


class TestWaitForSettled:
    def test_rejects_an_empty_disjunction(self) -> None:
        with pytest.raises(ValueError, match="at least one branch"):
            page_for(FakeDriver({PAGE[1]})).wait_for_settled({}, "empty map")

    def test_does_not_return_until_the_content_is_present(self) -> None:
        """The defining property: three empty polls, then the page root."""
        driver = FakeDriver(set(), set(), set(), {PAGE[1]})
        state = page_for(driver).wait_for_settled({"content": PAGE}, "tank detail", timeout=5)
        assert state.branch == "content"
        assert driver.polls >= 3

    def test_fails_loudly_naming_every_probed_branch(self) -> None:
        driver = FakeDriver(set())
        with pytest.raises(AssertionError) as exc:
            page_for(driver).wait_for_settled(
                {"content": PAGE, "error": (By.CSS_SELECTOR, ERROR)},
                "tank detail",
                timeout=1,
            )
        message = str(exc.value)
        assert "tank detail" in message
        assert PAGE[1] in message
        assert ERROR in message

    def test_a_skeleton_still_up_after_the_root_mounted_fails_loudly(self) -> None:
        """The page root rendered but its data never arrived -- a real finding.

        This is the window the weak wait could not see: the root is on screen,
        so "no skeleton" is now a falsifiable absence rather than "React has not
        got here yet".
        """
        driver = FakeDriver({PAGE[1], SKELETON})
        with pytest.raises(AssertionError, match="loading skeleton is still visible"):
            page_for(driver).wait_for_settled({"content": PAGE}, "tank detail", timeout=1)

    def test_require_no_skeleton_false_skips_the_second_phase(self) -> None:
        driver = FakeDriver({PAGE[1], SKELETON})
        state = page_for(driver).wait_for_settled(
            {"content": PAGE}, "tank detail", timeout=1, require_no_skeleton=False
        )
        assert state.branch == "content"


# ── the page-level wrappers ──────────────────────────────────────────────────


class TestPageBranches:
    def test_content_precedes_the_error_surfaces(self) -> None:
        branches = page_for(FakeDriver()).page_branches(PAGE)
        assert list(branches) == [
            BasePage.BRANCH_CONTENT,
            BasePage.BRANCH_ERROR,
            BasePage.BRANCH_ERROR_PAGE,
        ]

    def test_extra_branches_are_appended(self) -> None:
        branches = page_for(FakeDriver()).page_branches(
            PAGE, extra={BasePage.BRANCH_EMPTY: BasePage.EMPTY_STATE}
        )
        assert list(branches)[-1] == BasePage.BRANCH_EMPTY


class TestWaitForPageSettled:
    def test_reports_the_error_branch_instead_of_timing_out(self) -> None:
        driver = FakeDriver({ERROR})
        state = page_for(driver).wait_for_page_settled(PAGE, "unknown key", timeout=2)
        assert state.branch == BasePage.BRANCH_ERROR

    def test_reports_the_content_branch_on_the_happy_path(self) -> None:
        driver = FakeDriver({PAGE[1]})
        state = page_for(driver).wait_for_page_settled(PAGE, "tank detail", timeout=2)
        assert state.branch == BasePage.BRANCH_CONTENT


class TestWaitForContent:
    def test_passes_when_the_page_root_rendered(self) -> None:
        driver = FakeDriver({PAGE[1]})
        assert page_for(driver).wait_for_content(PAGE, "tank detail", timeout=2).branch == "content"

    def test_names_the_error_the_app_actually_showed(self) -> None:
        """A bare element wait would only say "element not found"."""
        driver = FakeDriver({ERROR, ERROR_MESSAGE}, texts={ERROR_MESSAGE: "Tank nicht gefunden"})
        with pytest.raises(AssertionError) as exc:
            page_for(driver).wait_for_content(PAGE, "tank detail", timeout=2)
        message = str(exc.value)
        assert BasePage.BRANCH_ERROR in message
        assert "Tank nicht gefunden" in message


class TestRequireBranch:
    def test_accepts_the_expected_branch(self) -> None:
        state = SettledState("content", PAGE, ("content",))
        page_for(FakeDriver()).require_branch(state, "content", "tank detail")

    def test_rejects_another_branch_and_lists_everything_present(self) -> None:
        state = SettledState("empty-state", BasePage.EMPTY_STATE, ("empty-state", "content"))
        with pytest.raises(AssertionError) as exc:
            page_for(FakeDriver()).require_branch(state, "content", "tank list")
        assert "empty-state, content" in str(exc.value)


class TestWaitForAnyPresent:
    def test_returns_the_locator_that_matched(self) -> None:
        driver = FakeDriver({ERROR})
        matched = page_for(driver).wait_for_any_present(
            (PAGE, (By.CSS_SELECTOR, ERROR)), "detail route", timeout=2
        )
        assert matched == (By.CSS_SELECTOR, ERROR)

    def test_ignores_a_still_visible_skeleton(self) -> None:
        """The positional form keeps its old, skeleton-agnostic semantics."""
        driver = FakeDriver({PAGE[1], SKELETON})
        assert page_for(driver).wait_for_any_present((PAGE,), "detail route", timeout=2) == PAGE


# ── The screenshot checkpoint's own settling (#959) ──────────────────────────
# `Page.captureScreenshot({captureBeyondViewport: true})` stretches the layout
# viewport and puts it back, firing two `resize` events and flipping every
# `useMediaQuery` on the way (measured; see the block comment in
# `tests/e2e/conftest.py`). A checkpoint that returns before the page is back at
# its own size hands the next line a re-laid-out page — which is how
# `has_remove_fertilizer_button()` came back `False` one line after a helper had
# waited for that button.
#
# There is no browser here, so what these pin is the *decision*: the restore is
# verified rather than assumed, an unrestored viewport fails loudly and in
# budget, and the frame barrier is actually awaited.


class ViewportDriver:
    """A driver whose viewport metrics are a scripted sequence.

    Each ``execute_script`` for the metrics consumes one entry; the last one
    repeats forever, so "comes back on the third poll" and "never comes back"
    are both expressible. ``execute_async_script`` records that the frame
    barrier ran instead of running one.
    """

    def __init__(
        self,
        *metrics: tuple[int, int] | None,
        cdp_fails: bool = False,
        screenshot_data: str = "aGk=",
    ) -> None:
        self.metrics = list(metrics) or [(800, 600)]
        self.reads = 0
        self.async_calls = 0
        self.cdp_calls = 0
        self.saved: list[str] = []
        self.cdp_fails = cdp_fails
        self.screenshot_data = screenshot_data

    def execute_script(self, _script: str) -> list[int] | None:
        value = self.metrics[min(self.reads, len(self.metrics) - 1)]
        self.reads += 1
        return None if value is None else [value[0], value[1]]

    def execute_async_script(self, _script: str) -> str:
        self.async_calls += 1
        return "frames"

    def execute_cdp_cmd(self, _method: str, _params: dict[str, object]) -> dict[str, str]:
        self.cdp_calls += 1
        if self.cdp_fails:
            raise WebDriverException("no CDP on this grid")
        return {"data": self.screenshot_data}

    def save_screenshot(self, path: str) -> bool:
        self.saved.append(path)
        return True


class TestCheckpointSettling:
    """`_settle_after_capture`: the checkpoint's post-condition on the page."""

    def test_it_returns_once_the_viewport_is_back_and_holds_one_frame(self) -> None:
        driver = ViewportDriver((800, 600))
        _settle_after_capture(driver, (800, 600))  # type: ignore[arg-type]
        assert driver.async_calls == 1, (
            "The frame barrier is the half that covers React's *asynchronous* "
            "re-render; without it the checkpoint only proves the metrics came "
            "back, which Chrome does on its own."
        )

    def test_it_polls_rather_than_sampling_once(self) -> None:
        """A single comparison would fail a page that is one poll from restored."""
        driver = ViewportDriver((800, 4000), (800, 4000), (800, 600))
        _settle_after_capture(driver, (800, 600), timeout=2)  # type: ignore[arg-type]
        assert driver.reads >= 3
        assert driver.async_calls == 1

    def test_a_viewport_that_never_comes_back_fails_loudly_and_in_budget(self) -> None:
        driver = ViewportDriver((800, 4000))
        with pytest.raises(AssertionError) as exc:
            _settle_after_capture(driver, (800, 600), timeout=0.3)  # type: ignore[arg-type]
        message = str(exc.value)
        assert "800x600" in message, "the message must name what was expected"
        assert "(800, 4000)" in message, "…and what the page actually reads now"
        assert "captureBeyondViewport" in message, "…and the mechanism that did it"
        assert driver.async_calls == 0, "a page that never settled must not be declared settled"

    def test_a_page_that_cannot_be_asked_is_not_reported_as_a_changed_viewport(self) -> None:
        """No baseline, no verdict.

        A dead session or an open alert answers "could not look", and that must
        not become "the viewport changed" — nor, in the other direction, a
        silent claim that the checkpoint was passive.
        """
        driver = ViewportDriver((800, 600))
        _settle_after_capture(driver, None)  # type: ignore[arg-type]
        assert driver.reads == 0
        assert driver.async_calls == 0


class TestFullPageCaptureIsPassive:
    """The wiring: the capture itself has to run the settle, not merely own it."""

    def test_the_capture_verifies_the_restore(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        driver = ViewportDriver((800, 600), (800, 4000))
        with pytest.raises(AssertionError) as exc:
            _cdp_full_page_screenshot(driver, tmp_path / "shot.png")  # type: ignore[arg-type]
        assert "screenshot checkpoint" in str(exc.value)
        assert (tmp_path / "shot.png").exists(), (
            "the image is still written — the failure is about the page the "
            "checkpoint left behind, not about the capture"
        )

    def test_a_restored_page_captures_without_complaint(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        driver = ViewportDriver((800, 600))
        _cdp_full_page_screenshot(driver, tmp_path / "shot.png")  # type: ignore[arg-type]
        assert (tmp_path / "shot.png").read_bytes() == b"hi"
        assert driver.async_calls == 1

    def test_the_non_cdp_fallback_settles_nothing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """`save_screenshot` resizes nothing, so there is nothing to wait out.

        Asserted rather than assumed because the fallback runs on Firefox and on
        grids without CDP, where a settle keyed on a resize that never happens
        would be a pure cost — and, on a browser whose metrics read differently,
        a false failure.
        """
        driver = ViewportDriver((800, 600), (800, 4000), cdp_fails=True)
        _cdp_full_page_screenshot(driver, tmp_path / "shot.png")  # type: ignore[arg-type]
        assert driver.saved == [str(tmp_path / "shot.png")]
        assert driver.async_calls == 0
