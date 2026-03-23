"""E2E tests for REQ-007 — Erntemanagement: HarvestReadinessCard (TC-007-035 to TC-007-042).

Tests cover:
- HarvestReadinessCard component display
- Overall score gauge (LinearProgress)
- Recommendation chip color coding
- Indicator breakdown table

NFR-008 §3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states

Note: The HarvestReadinessCard is embedded in the plant detail page and requires
a plant with readiness data. If no such data exists, tests are skipped.
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.base_page import BasePage


# -- Locators for the HarvestReadinessCard ---------------------------------

READINESS_CARD = (By.CSS_SELECTOR, "[data-testid='harvest-readiness-card']")
READINESS_SCORE = (
    By.CSS_SELECTOR,
    "[data-testid='harvest-readiness-card'] .MuiTypography-h4",
)
READINESS_PROGRESS = (
    By.CSS_SELECTOR,
    "[data-testid='harvest-readiness-card'] .MuiLinearProgress-root",
)
READINESS_CHIP = (
    By.CSS_SELECTOR,
    "[data-testid='harvest-readiness-card'] .MuiChip-root",
)
READINESS_INDICATOR_TABLE = (
    By.CSS_SELECTOR,
    "[data-testid='harvest-readiness-card'] table",
)
READINESS_INDICATOR_ROWS = (
    By.CSS_SELECTOR,
    "[data-testid='harvest-readiness-card'] table tbody tr",
)


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def base_page(browser: WebDriver, base_url: str) -> BasePage:
    """Return a BasePage for generic navigation."""
    return BasePage(browser, base_url)


def _find_readiness_card(driver: WebDriver) -> bool:
    """Return True if a HarvestReadinessCard is visible on the current page."""
    elements = driver.find_elements(*READINESS_CARD)
    return len(elements) > 0 and elements[0].is_displayed()


# -- Tests ------------------------------------------------------------------


class TestHarvestReadinessCard:
    """TC-007-035 to TC-007-042: HarvestReadinessCard display and behavior."""

    def test_readiness_card_displays_score(
        self,
        base_page: BasePage,
        screenshot,
    ) -> None:
        """TC-007-035: Readiness card shows overall score with progress bar."""
        # Readiness card is typically shown on plant detail pages.
        # We try to find it by navigating to a known plant detail page.
        # Since we do not know specific plant keys, navigate to the plant list first.
        base_page.navigate("/pflanzen")
        base_page.wait_for_loading_complete()

        # Try clicking the first plant to go to detail
        rows = base_page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table-row']"
        )
        if not rows:
            pytest.skip("No plant instances -- cannot test readiness card")

        base_page.scroll_and_click(rows[0])
        time.sleep(1)
        base_page.wait_for_loading_complete()
        screenshot("req007_060_plant_detail_for_readiness", "Pflanzendetail fuer Reifegrad-Karte")

        if not _find_readiness_card(base_page.driver):
            pytest.skip(
                "No HarvestReadinessCard visible on plant detail -- "
                "readiness data may not exist for this plant"
            )

        screenshot("req007_060_readiness_card", "Erntereife-Karte sichtbar")

        # Verify score is present
        score_els = base_page.driver.find_elements(*READINESS_SCORE)
        assert len(score_els) > 0, "Expected overall score value in readiness card"

        # Verify progress bar exists
        progress_els = base_page.driver.find_elements(*READINESS_PROGRESS)
        assert len(progress_els) > 0, "Expected LinearProgress in readiness card"

    def test_readiness_card_recommendation_chip(
        self,
        base_page: BasePage,
        screenshot,
    ) -> None:
        """TC-007-036: Readiness card shows a recommendation chip (optimal/approaching/developing)."""
        base_page.navigate("/pflanzen")
        base_page.wait_for_loading_complete()

        rows = base_page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table-row']"
        )
        if not rows:
            pytest.skip("No plant instances -- cannot test readiness card")

        base_page.scroll_and_click(rows[0])
        time.sleep(1)
        base_page.wait_for_loading_complete()

        if not _find_readiness_card(base_page.driver):
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        chip_els = base_page.driver.find_elements(*READINESS_CHIP)
        screenshot("req007_061_readiness_recommendation", "Empfehlungs-Chip der Erntereife")

        assert len(chip_els) > 0, "Expected recommendation chip in readiness card"

        # Verify chip has an appropriate MUI color class
        chip = chip_els[0]
        classes = chip.get_attribute("class") or ""
        valid_colors = ["Success", "Warning", "Info", "Error"]
        has_color = any(c.lower() in classes.lower() for c in valid_colors)
        assert has_color, (
            f"Expected recommendation chip to have a MUI color class, got: {classes}"
        )

    def test_readiness_card_indicator_table(
        self,
        base_page: BasePage,
        screenshot,
    ) -> None:
        """TC-007-037: Readiness card shows indicator breakdown table."""
        base_page.navigate("/pflanzen")
        base_page.wait_for_loading_complete()

        rows = base_page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table-row']"
        )
        if not rows:
            pytest.skip("No plant instances -- cannot test readiness card")

        base_page.scroll_and_click(rows[0])
        time.sleep(1)
        base_page.wait_for_loading_complete()

        if not _find_readiness_card(base_page.driver):
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        screenshot("req007_062_readiness_indicators", "Indikator-Aufschluesselung")

        table_els = base_page.driver.find_elements(*READINESS_INDICATOR_TABLE)
        if not table_els:
            # Indicator table is only shown when indicators exist
            pytest.skip("No indicator breakdown table -- indicators may be empty")

        indicator_rows = base_page.driver.find_elements(*READINESS_INDICATOR_ROWS)
        assert len(indicator_rows) > 0, (
            "Expected at least one indicator row in the breakdown table"
        )
