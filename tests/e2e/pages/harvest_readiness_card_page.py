"""Page object for the HarvestReadinessCard (REQ-007).

The HarvestReadinessCard is a sub-component embedded on the plant-instance
detail page (``/pflanzen/plant-instances/:key``) rather than a page of its
own; there is no dedicated page-level ``open()`` — callers navigate to a
plant detail page first (e.g. via ``PlantInstanceListPage`` or the generic
list-row-click helper below) and then query the card through this object.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class HarvestReadinessCardPage(BasePage):
    """Query the HarvestReadinessCard embedded on a plant detail page."""

    CARD = (By.CSS_SELECTOR, "[data-testid='harvest-readiness-card']")
    SCORE = (By.CSS_SELECTOR, "[data-testid='harvest-readiness-card'] .MuiTypography-h4")
    PROGRESS = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-readiness-card'] .MuiLinearProgress-root",
    )
    CHIP = (By.CSS_SELECTOR, "[data-testid='harvest-readiness-card'] .MuiChip-root")
    INDICATOR_TABLE = (By.CSS_SELECTOR, "[data-testid='harvest-readiness-card'] table")
    INDICATOR_ROWS = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-readiness-card'] table tbody tr",
    )
    DATA_TABLE_ROW = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    #: Identifying column of `PlantInstanceListPage`; the row's click target.
    INSTANCE_ID_COLUMN_ID = "instanceId"

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation helper (no dedicated plant-instance page object route) ──

    def open_first_plant_detail_via_list(self) -> bool:
        """Navigate to the plant list and click the first row.

        Returns True iff a row existed and was clicked (i.e. a detail page
        was reached); returns False when the list is empty, leaving the
        caller responsible for the ``pytest.skip`` (this object has no
        pytest dependency).
        """
        self.navigate("/pflanzen")
        self.wait_for_loading_complete()
        rows = self.driver.find_elements(*self.DATA_TABLE_ROW)
        if not rows:
            return False
        # Via the inert instance-id cell, not the row centre: the plant-instance
        # row carries `location` and `plantingRun` links plus an actions button,
        # all of which `stopPropagation`.
        self.click_row_via_column(rows[0], self.INSTANCE_ID_COLUMN_ID)
        self.wait_for_loading_complete()
        return True

    # ── Card presence ────────────────────────────────────────────────────

    def is_card_visible(self) -> bool:
        """Return True iff the HarvestReadinessCard is visible on the current page."""
        elements = self.driver.find_elements(*self.CARD)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Score / progress ─────────────────────────────────────────────────

    def has_score_value(self) -> bool:
        """Return True iff an overall score value is rendered in the card."""
        return len(self.driver.find_elements(*self.SCORE)) > 0

    def has_progress_bar(self) -> bool:
        """Return True iff a LinearProgress element is rendered in the card."""
        return len(self.driver.find_elements(*self.PROGRESS)) > 0

    # ── Recommendation chip ──────────────────────────────────────────────

    def get_recommendation_chip(self) -> WebElement | None:
        """Return the recommendation chip element, or None if absent."""
        chips = self.driver.find_elements(*self.CHIP)
        return chips[0] if chips else None

    def get_recommendation_chip_classes(self) -> str:
        """Return the CSS class attribute of the recommendation chip (empty if absent)."""
        chip = self.get_recommendation_chip()
        return (chip.get_attribute("class") or "") if chip else ""

    # ── Indicator breakdown table ────────────────────────────────────────

    def has_indicator_table(self) -> bool:
        """Return True iff the indicator breakdown table is rendered."""
        return len(self.driver.find_elements(*self.INDICATOR_TABLE)) > 0

    def get_indicator_row_count(self) -> int:
        """Return the number of rows in the indicator breakdown table."""
        return len(self.driver.find_elements(*self.INDICATOR_ROWS))
