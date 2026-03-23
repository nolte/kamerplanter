"""Page object for the Calendar page (REQ-015 Kalenderansicht).

Covers:
- View tabs (Month, List, Phases Timeline, Sowing Calendar, Season Overview)
- Month navigation (prev/next/today)
- Category filter chips
- Plant filter tree
- Event interaction (popover, click-through)
- Feed management (create, copy URL, regenerate token, delete)
- Sowing calendar specifics (frost chips, category filters, favorites)
- Season overview (12-month cards)
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage, DEFAULT_TIMEOUT


class CalendarPage(BasePage):
    """Page object for ``/kalender`` — the unified calendar page."""

    # ── Top-level page ──────────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='calendar-page']")

    # ── Month navigation ────────────────────────────────────────────────
    PREV_MONTH_BTN = (By.CSS_SELECTOR, "[data-testid='calendar-prev-month']")
    NEXT_MONTH_BTN = (By.CSS_SELECTOR, "[data-testid='calendar-next-month']")
    TODAY_BTN = (By.CSS_SELECTOR, "[data-testid='calendar-today-btn']")

    # ── View tabs ───────────────────────────────────────────────────────
    VIEW_TAB_MONTH = (By.CSS_SELECTOR, "[data-testid='calendar-view-month']")
    VIEW_TAB_LIST = (By.CSS_SELECTOR, "[data-testid='calendar-view-list']")
    VIEW_TAB_PHASES = (By.CSS_SELECTOR, "[data-testid='calendar-view-phases']")
    VIEW_TAB_SOWING = (By.CSS_SELECTOR, "[data-testid='calendar-view-sowing']")
    VIEW_TAB_SEASON = (By.CSS_SELECTOR, "[data-testid='calendar-view-season']")

    # ── Site select (sowing/season views) ───────────────────────────────
    SITE_SELECT = (By.CSS_SELECTOR, "[data-testid='calendar-site-select']")

    # ── Sowing favorites filter ─────────────────────────────────────────
    SOWING_FAVORITES_FILTER = (By.CSS_SELECTOR, "[data-testid='sowing-favorites-filter']")

    # ── Category filter chips (month/list views) ────────────────────────
    # Use category_filter_chip(cat) for individual categories.

    # ── Event popover ───────────────────────────────────────────────────
    EVENT_POPOVER = (By.CSS_SELECTOR, "[data-testid='event-popover']")
    DAY_POPOVER = (By.CSS_SELECTOR, "[data-testid='day-popover']")
    CONFIRM_WATERING_BTN = (By.CSS_SELECTOR, "[data-testid='confirm-watering-btn']")

    # ── Feed management ─────────────────────────────────────────────────
    FEEDS_TOGGLE = (By.CSS_SELECTOR, "[data-testid='feeds-toggle']")
    CREATE_FEED_BTN = (By.CSS_SELECTOR, "[data-testid='create-feed-btn']")
    CREATE_FEED_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-feed-dialog']")
    FEED_NAME_INPUT = (By.CSS_SELECTOR, "[data-testid='feed-name-input']")
    FEED_SAVE_BTN = (By.CSS_SELECTOR, "[data-testid='feed-save-btn']")
    FEED_CANCEL_BTN = (By.CSS_SELECTOR, "[data-testid='feed-cancel-btn']")

    # ── Sowing calendar sub-view ────────────────────────────────────────
    SOWING_CATEGORY_FILTER_CLEAR = (By.CSS_SELECTOR, "[data-testid='sowing-category-filter-clear']")

    # ── Plant filter tree ───────────────────────────────────────────────
    PLANT_FILTER_CLEAR = (By.CSS_SELECTOR, "[data-testid='plant-filter-clear']")
    PLANT_FILTER_SELECT_ALL = (By.CSS_SELECTOR, "[data-testid='plant-filter-select-all']")

    # ── Season overview sub-view ────────────────────────────────────────
    SEASON_MONTH_CARDS = (By.CSS_SELECTOR, ".MuiGrid-container .MuiCard-root")

    # ── Loading / empty ─────────────────────────────────────────────────
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Calendar grid (month view) ──────────────────────────────────────
    MONTH_GRID_COLUMN_HEADERS = (By.CSS_SELECTOR, "th, [role='columnheader']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> CalendarPage:
        """Navigate to the calendar page and wait for the container."""
        self.navigate("/kalender")
        self.wait_for_element(self.PAGE)
        return self

    # ── View switching ──────────────────────────────────────────────────

    def switch_to_month_view(self) -> None:
        """Click the Month tab."""
        self.wait_for_element_clickable(self.VIEW_TAB_MONTH).click()

    def switch_to_list_view(self) -> None:
        """Click the List tab."""
        self.wait_for_element_clickable(self.VIEW_TAB_LIST).click()

    def switch_to_phases_view(self) -> None:
        """Click the Phases Timeline tab."""
        self.wait_for_element_clickable(self.VIEW_TAB_PHASES).click()

    def switch_to_sowing_view(self) -> None:
        """Click the Sowing Calendar tab."""
        self.wait_for_element_clickable(self.VIEW_TAB_SOWING).click()

    def switch_to_season_view(self) -> None:
        """Click the Season Overview tab."""
        self.wait_for_element_clickable(self.VIEW_TAB_SEASON).click()

    def get_active_tab_value(self) -> str:
        """Return the ``aria-selected='true'`` tab's data-testid suffix (e.g. 'month')."""
        tabs = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='calendar-view-'][aria-selected='true']"
        )
        if not tabs:
            return ""
        testid = tabs[0].get_attribute("data-testid") or ""
        return testid.replace("calendar-view-", "")

    # ── Month navigation ────────────────────────────────────────────────

    def click_next_month(self) -> None:
        """Navigate to the next month."""
        self.wait_for_element_clickable(self.NEXT_MONTH_BTN).click()

    def click_prev_month(self) -> None:
        """Navigate to the previous month."""
        self.wait_for_element_clickable(self.PREV_MONTH_BTN).click()

    def click_today(self) -> None:
        """Click the Today button to return to the current month."""
        self.wait_for_element_clickable(self.TODAY_BTN).click()

    def get_month_header_text(self) -> str:
        """Return the visible month/year text in the header area.

        The header is a Typography right next to the navigation buttons.
        """
        # The month label is between the prev/next buttons
        header = self.driver.find_element(
            By.CSS_SELECTOR,
            "[data-testid='calendar-page'] h6, [data-testid='calendar-page'] .MuiTypography-h6",
        )
        return header.text.strip()

    # ── Calendar grid (month view) ──────────────────────────────────────

    def get_day_cell(self, day: int) -> WebElement:
        """Return the day cell element for a specific day number."""
        return self.wait_for_element(
            (By.CSS_SELECTOR, f"[data-testid='calendar-day-{day}']")
        )

    def get_event_dots(self) -> list[WebElement]:
        """Return all event dot elements in the month grid."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='calendar-event-dot-']"
        )

    def click_event_dot(self, event_id: str) -> None:
        """Click a specific event dot to open the popover."""
        dot = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='calendar-event-dot-{event_id}']")
        )
        self.scroll_and_click(dot)

    def click_day_cell(self, day: int) -> None:
        """Click a day cell to open the day popover."""
        cell = self.get_day_cell(day)
        self.scroll_and_click(cell)

    # ── Popovers ────────────────────────────────────────────────────────

    def is_event_popover_visible(self) -> bool:
        """Return True if the event popover is displayed."""
        elements = self.driver.find_elements(*self.EVENT_POPOVER)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_day_popover_visible(self) -> bool:
        """Return True if the day popover is displayed."""
        elements = self.driver.find_elements(*self.DAY_POPOVER)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_event_popover(self) -> WebElement:
        """Wait for and return the event popover element."""
        return self.wait_for_element_visible(self.EVENT_POPOVER)

    # ── Category filter chips ───────────────────────────────────────────

    def get_category_filter_chips(self) -> list[WebElement]:
        """Return all category filter chip elements."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='category-filter-']"
        )

    def click_category_filter(self, category: str) -> None:
        """Toggle a specific category filter chip."""
        chip = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='category-filter-{category}']")
        )
        self.scroll_and_click(chip)

    # ── Plant filter tree ───────────────────────────────────────────────

    def click_plant_filter_run(self, run_key: str) -> None:
        """Toggle a planting run in the plant filter tree."""
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='plant-filter-run-{run_key}']")
        )
        self.scroll_and_click(el)

    def click_plant_filter_plant(self, plant_key: str) -> None:
        """Toggle a plant in the plant filter tree."""
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='plant-filter-plant-{plant_key}']")
        )
        self.scroll_and_click(el)

    def click_plant_filter_select_all(self) -> None:
        """Click the Select All button in the plant filter tree."""
        self.wait_for_element_clickable(self.PLANT_FILTER_SELECT_ALL).click()

    def click_plant_filter_clear(self) -> None:
        """Click the Clear button in the plant filter tree."""
        self.wait_for_element_clickable(self.PLANT_FILTER_CLEAR).click()

    # ── Site select ─────────────────────────────────────────────────────

    def get_site_select(self) -> WebElement:
        """Return the site select element (visible in sowing/season views)."""
        return self.wait_for_element(self.SITE_SELECT)

    def is_site_select_visible(self) -> bool:
        """Return True if the site select dropdown is visible."""
        elements = self.driver.find_elements(*self.SITE_SELECT)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Sowing calendar specifics ───────────────────────────────────────

    def get_sowing_category_filter_chips(self) -> list[WebElement]:
        """Return all sowing category filter chip elements."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='sowing-category-filter-']"
        )

    def click_sowing_category_filter(self, category: str) -> None:
        """Toggle a plant-category filter chip in the sowing calendar."""
        chip = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='sowing-category-filter-{category}']")
        )
        self.scroll_and_click(chip)

    def click_sowing_favorites_filter(self) -> None:
        """Toggle the favorites-only filter in the sowing calendar."""
        self.wait_for_element_clickable(self.SOWING_FAVORITES_FILTER).click()

    def get_sowing_row_count(self) -> int:
        """Count the number of species/plant rows in the sowing calendar grid.

        Each row has a sticky label cell followed by week cells.
        """
        # The sowing calendar uses a CSS grid; label cells are sticky with species names.
        # Count unique label cells (they contain Typography with species names).
        # The SowingRow renders a Box (label) + 52 week cells. Label cells are sticky left.
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='calendar-page'] .MuiCardContent-root [style*='sticky'], "
            "[data-testid='calendar-page'] .MuiCardContent-root > div > div > div[style*='sticky']"
        )
        # Subtract the header row (first sticky element is the month header placeholder)
        return max(0, len(rows) - 1) if rows else 0

    def get_sowing_frost_chips(self) -> list[WebElement]:
        """Return frost info chips (last frost, Eisheilige) in sowing view."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='calendar-page'] .MuiChip-root.MuiChip-outlined"
        )

    def get_sowing_legend_items(self) -> list[WebElement]:
        """Return legend items in the sowing calendar view."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='calendar-page'] .MuiCardContent-root .MuiTypography-caption"
        )

    # ── Season overview specifics ───────────────────────────────────────

    def get_season_month_cards(self) -> list[WebElement]:
        """Return all 12 month cards in the season overview."""
        return self.driver.find_elements(*self.SEASON_MONTH_CARDS)

    def get_highlighted_season_card(self) -> WebElement | None:
        """Return the currently highlighted (outlined) month card, or None."""
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, ".MuiCard-outlined"
        )
        return cards[0] if cards else None

    # ── List view ───────────────────────────────────────────────────────

    def get_list_events(self) -> list[WebElement]:
        """Return all event items in the list/agenda view."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='calendar-list-event-']"
        )

    # ── Feed management ─────────────────────────────────────────────────

    def toggle_feeds_section(self) -> None:
        """Expand or collapse the iCal feeds section."""
        self.wait_for_element_clickable(self.FEEDS_TOGGLE).click()

    def click_create_feed(self) -> None:
        """Click the Create Feed button (opens the dialog)."""
        self.wait_for_element_clickable(self.CREATE_FEED_BTN).click()

    def is_create_feed_dialog_visible(self) -> bool:
        """Return True if the create feed dialog is open."""
        elements = self.driver.find_elements(*self.CREATE_FEED_DIALOG)
        return len(elements) > 0 and elements[0].is_displayed()

    def enter_feed_name(self, name: str) -> None:
        """Type a name into the feed name input field."""
        inp = self.wait_for_element(self.FEED_NAME_INPUT)
        # The data-testid is on the TextField wrapper; find the actual <input>
        actual_input = inp.find_element(By.TAG_NAME, "input")
        actual_input.clear()
        actual_input.send_keys(name)

    def save_feed(self) -> None:
        """Click the Save button in the feed creation dialog."""
        self.wait_for_element_clickable(self.FEED_SAVE_BTN).click()

    def cancel_feed(self) -> None:
        """Click the Cancel button in the feed creation dialog."""
        self.wait_for_element_clickable(self.FEED_CANCEL_BTN).click()

    def get_feed_items(self) -> list[WebElement]:
        """Return all feed list items."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='feed-item-']"
        )

    def click_feed_copy(self, feed_key: str) -> None:
        """Click the copy URL button for a feed."""
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='feed-copy-{feed_key}']")
        ).click()

    def click_feed_regenerate(self, feed_key: str) -> None:
        """Click the regenerate token button for a feed."""
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='feed-regenerate-{feed_key}']")
        ).click()

    def click_feed_delete(self, feed_key: str) -> None:
        """Click the delete button for a feed."""
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='feed-delete-{feed_key}']")
        ).click()

    # ── Watering confirmation ───────────────────────────────────────────

    def click_confirm_watering(self) -> None:
        """Click the confirm watering button in the event popover."""
        self.wait_for_element_clickable(self.CONFIRM_WATERING_BTN).click()

    def click_day_confirm_watering(self, plant_key: str) -> None:
        """Click the confirm watering button for a specific plant in the day popover."""
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='day-confirm-watering-{plant_key}']")
        ).click()

    # ── Snackbar / notification ─────────────────────────────────────────

    def get_snackbar_text(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of a MUI Snackbar/Alert notification."""
        snackbar = self.wait_for_element_visible(
            (By.CSS_SELECTOR, ".MuiSnackbar-root .MuiAlert-message, .notistack-MuiContent"),
            timeout=timeout,
        )
        return snackbar.text.strip()

    def is_snackbar_visible(self) -> bool:
        """Check if any snackbar/notification is currently visible."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".MuiSnackbar-root, [class*='notistack']",
        )
        return any(el.is_displayed() for el in elements)
