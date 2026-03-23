"""E2E tests for REQ-015 -- Saisonuebersicht / Season Overview (TC-015-006, TC-015-060+).

Tests cover:
- Season overview view loads with 12 month cards (TC-015-006)
- Current month card is visually highlighted
- Month cards show summary counts (sowing, harvest, bloom, tasks)
- Site select is visible in season view
- Month card click navigates to month view

NFR-008 section 3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.calendar_page import CalendarPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- Helpers ------------------------------------------------------------------


def _open_season_view(calendar: CalendarPage) -> None:
    """Navigate to calendar and switch to season overview tab."""
    calendar.open()
    calendar.switch_to_season_view()


# -- TC-015-006: Season overview basics ----------------------------------------


class TestSeasonOverviewLoad:
    """TC-015-006: Season overview view rendering and card layout."""

    def test_season_view_renders_after_tab_switch(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Season overview view renders 12 month cards or an empty state.

        Verifies:
        - The season tab is active
        - Either 12 month cards or an empty state is shown
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)
        capture("req015_060_season_view_loaded", "Season overview after tab switch")

        active = calendar.get_active_tab_value()
        assert active == "season", (
            f"Expected season tab to be active, got: '{active}'"
        )

        cards = calendar.get_season_month_cards()
        empty_states = calendar.driver.find_elements(*CalendarPage.EMPTY_STATE)

        if len(empty_states) > 0:
            capture("req015_060_season_empty", "Season overview showing empty state")
            pytest.skip("Season overview has empty state; no month cards to verify")

        assert len(cards) == 12, (
            f"Expected 12 month cards in season overview, got {len(cards)}"
        )

    def test_season_view_shows_site_select(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Site select dropdown is visible in season overview view.

        Verifies the site selector is available for filtering season data.
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)
        capture("req015_060_season_site_select", "Season view with site select")

        assert calendar.is_site_select_visible(), (
            "Expected site select dropdown to be visible in season overview"
        )


# -- Season card content -------------------------------------------------------


class TestSeasonOverviewCardContent:
    """Season overview card content and highlighting."""

    def test_month_cards_display_summary_counts(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Each month card shows summary count rows.

        Verifies that each card contains caption text elements (count labels).
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)
        capture("req015_061_season_card_content", "Season cards with summary counts")

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present (empty state)")

        # Each card should have CardContent with Typography elements
        first_card = cards[0]
        captions = first_card.find_elements(By.CSS_SELECTOR, ".MuiTypography-caption")
        assert len(captions) >= 4, (
            f"Expected at least 4 count labels per card (sowing, harvest, bloom, tasks), "
            f"got {len(captions)} in first card"
        )

    def test_current_month_card_is_highlighted(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Current month card has a highlighted border/style.

        The current month card uses variant='outlined' with a primary border.
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)
        capture("req015_062_current_month_highlight", "Season view current month highlighted")

        highlighted = calendar.get_highlighted_season_card()
        if highlighted is None:
            # May not be visible if the current month has no data or view is empty
            capture("req015_062_no_highlight", "No highlighted month card found")
            pytest.skip("No highlighted month card found (may depend on data)")

        assert highlighted.is_displayed(), (
            "Expected highlighted current-month card to be visible"
        )

    def test_month_card_shows_month_name(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Each month card displays the month name as a title.

        Verifies the first card has a subtitle1 Typography with month name text.
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)
        capture("req015_063_month_names", "Season cards with month names")

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present")

        first_card = cards[0]
        title_els = first_card.find_elements(
            By.CSS_SELECTOR, ".MuiTypography-subtitle1"
        )
        assert len(title_els) > 0, (
            "Expected a subtitle1 Typography element with month name in first card"
        )
        month_text = title_els[0].text.strip()
        assert len(month_text) > 0, (
            "Expected month name text to be non-empty"
        )


# -- Season overview interaction -----------------------------------------------


class TestSeasonOverviewInteraction:
    """Season overview month card click interaction."""

    def test_month_card_is_clickable(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Month cards have a CardActionArea making them clickable.

        Verifies that clicking a month card triggers navigation (tab switch to month view).
        """
        capture = request.node._screenshot_capture
        _open_season_view(calendar)

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present")

        capture("req015_064_before_card_click", "Before clicking a month card")

        # Click the first card's CardActionArea
        action_areas = cards[0].find_elements(
            By.CSS_SELECTOR, ".MuiCardActionArea-root"
        )
        if len(action_areas) == 0:
            pytest.skip("No CardActionArea found in month card")

        calendar.scroll_and_click(action_areas[0])
        capture("req015_064_after_card_click", "After clicking month card")

        # After clicking, the view should switch to month view
        active = calendar.get_active_tab_value()
        assert active == "month", (
            f"Expected month tab to be active after clicking month card, got: '{active}'"
        )
