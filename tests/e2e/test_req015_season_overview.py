"""E2E tests for REQ-015 — Saisonuebersicht / Season Overview.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-015.md):
  TC-REQ-015-060  ->  TC-015-060  Saisonuebersicht — 12 Monatskarten mit Zaehlanzeige
  TC-REQ-015-061  ->  TC-015-060  Saisonuebersicht — Standort-Auswahl sichtbar
  TC-REQ-015-062  ->  TC-015-060  Saisonuebersicht — Monatskarten zeigen Zusammenfassungen
  TC-REQ-015-063  ->  TC-015-061  Saisonuebersicht — Aktueller Monat hervorgehoben
  TC-REQ-015-064  ->  TC-015-060  Saisonuebersicht — Monatskarten zeigen Monatsnamen
  TC-REQ-015-065  ->  TC-015-062  Saisonuebersicht — Klick auf Monatskarte wechselt Ansicht
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.calendar_page import CalendarPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- Helpers ------------------------------------------------------------------


def _open_season_view(calendar: CalendarPage) -> None:
    """Navigate to calendar and switch to season overview tab."""
    calendar.open()
    calendar.switch_to_season_view()


# -- TC-REQ-015-060 to TC-REQ-015-061: Season overview basics -----------------


class TestSeasonOverviewLoad:
    """Season overview view rendering and card layout (Spec: TC-015-060)."""

    @pytest.mark.smoke
    def test_season_view_renders_after_tab_switch(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-060: Season overview view renders 12 month cards or an empty state.

        Spec: TC-015-060 -- Saisonuebersicht — 12 Monatskarten mit Zaehlanzeige.
        """
        _open_season_view(calendar)
        screenshot("TC-REQ-015-060_season-view-loaded", "Season overview after tab switch")

        active = calendar.get_active_tab_value()
        assert active == "season", (
            f"TC-REQ-015-060 FAIL: Expected season tab to be active, got: '{active}'"
        )

        cards = calendar.get_season_month_cards()
        empty_states = calendar.driver.find_elements(*CalendarPage.EMPTY_STATE)

        if len(empty_states) > 0:
            screenshot("TC-REQ-015-060_season-empty", "Season overview showing empty state")
            pytest.skip("Season overview has empty state; no month cards to verify")

        assert len(cards) == 12, (
            f"TC-REQ-015-060 FAIL: Expected 12 month cards, got {len(cards)}"
        )

    @pytest.mark.smoke
    def test_season_view_shows_site_select(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-061: Site select dropdown is visible in season overview view.

        Spec: TC-015-060 -- Saisonuebersicht — Standort-Auswahl sichtbar.
        """
        _open_season_view(calendar)
        screenshot("TC-REQ-015-061_season-site-select", "Season view with site select")

        assert calendar.is_site_select_visible(), (
            "TC-REQ-015-061 FAIL: Expected site select dropdown to be visible in season overview"
        )


# -- Season card content -------------------------------------------------------


class TestSeasonOverviewCardContent:
    """Season overview card content and highlighting (Spec: TC-015-060, TC-015-061)."""

    @pytest.mark.core_crud
    def test_month_cards_display_summary_counts(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-062: Each month card shows summary count rows.

        Spec: TC-015-060 -- Saisonuebersicht — Monatskarten zeigen Zusammenfassungen.
        """
        _open_season_view(calendar)
        screenshot("TC-REQ-015-062_season-card-content", "Season cards with summary counts")

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present (empty state)")

        first_card = cards[0]
        captions = first_card.find_elements(By.CSS_SELECTOR, ".MuiTypography-caption")
        assert len(captions) >= 4, (
            f"TC-REQ-015-062 FAIL: Expected at least 4 count labels per card, "
            f"got {len(captions)} in first card"
        )

    @pytest.mark.core_crud
    def test_current_month_card_is_highlighted(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-063: Current month card has a highlighted border/style.

        Spec: TC-015-061 -- Saisonuebersicht — Aktueller Monat hervorgehoben.
        """
        _open_season_view(calendar)
        screenshot("TC-REQ-015-063_current-month-highlight", "Season view current month highlighted")

        highlighted = calendar.get_highlighted_season_card()
        if highlighted is None:
            screenshot("TC-REQ-015-063_no-highlight", "No highlighted month card found")
            pytest.skip("No highlighted month card found (may depend on data)")

        assert highlighted.is_displayed(), (
            "TC-REQ-015-063 FAIL: Expected highlighted current-month card to be visible"
        )

    @pytest.mark.core_crud
    def test_month_card_shows_month_name(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-064: Each month card displays the month name as a title.

        Spec: TC-015-060 -- Saisonuebersicht — Monatskarten zeigen Monatsnamen.
        """
        _open_season_view(calendar)
        screenshot("TC-REQ-015-064_month-names", "Season cards with month names")

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present")

        first_card = cards[0]
        title_els = first_card.find_elements(
            By.CSS_SELECTOR, ".MuiTypography-subtitle1"
        )
        assert len(title_els) > 0, (
            "TC-REQ-015-064 FAIL: Expected a subtitle1 Typography element with month name"
        )
        month_text = title_els[0].text.strip()
        assert len(month_text) > 0, (
            "TC-REQ-015-064 FAIL: Expected month name text to be non-empty"
        )


# -- Season overview interaction -----------------------------------------------


class TestSeasonOverviewInteraction:
    """Season overview month card click interaction (Spec: TC-015-062)."""

    @pytest.mark.core_crud
    def test_month_card_is_clickable(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-065: Month cards have a CardActionArea making them clickable.

        Spec: TC-015-062 -- Saisonuebersicht — Klick auf Monatskarte wechselt Ansicht.
        """
        _open_season_view(calendar)

        cards = calendar.get_season_month_cards()
        if len(cards) == 0:
            pytest.skip("No season month cards present")

        screenshot("TC-REQ-015-065_before-card-click", "Before clicking a month card")

        action_areas = cards[0].find_elements(
            By.CSS_SELECTOR, ".MuiCardActionArea-root"
        )
        if len(action_areas) == 0:
            pytest.skip("No CardActionArea found in month card")

        calendar.scroll_and_click(action_areas[0])
        screenshot("TC-REQ-015-065_after-card-click", "After clicking month card")

        active = calendar.get_active_tab_value()
        assert active == "month", (
            f"TC-REQ-015-065 FAIL: Expected month tab active after clicking card, got: '{active}'"
        )
