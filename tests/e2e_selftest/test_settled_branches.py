"""Unit tests for `BasePage`'s branch-aware settling helpers.

They pin the properties the weak ``wait_for_loading_complete()`` lacked and the
new helpers exist to provide (`e2e-test-stability` §D):

* the wait cannot be satisfied before the content exists,
* which branch was reached is reported, not inferred,
* a non-accepted branch fails loudly and names what the app actually showed.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

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
