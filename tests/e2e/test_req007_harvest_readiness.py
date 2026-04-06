"""E2E tests for REQ-007 — Erntemanagement: HarvestReadinessCard.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-007.md):
  TC-REQ-007-030  ->  TC-007-035  Erntereife-Karte zeigt Gesamtscore mit Fortschrittsbalken
  TC-REQ-007-031  ->  TC-007-036  Erntereife-Karte zeigt Empfehlungs-Chip
  TC-REQ-007-032  ->  TC-007-037  Erntereife-Karte zeigt Indikator-Aufschluesselungstabelle

Note: The HarvestReadinessCard is embedded in the plant detail page and requires
a plant with readiness data. If no such data exists, tests are skipped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.base_page import BasePage


# -- Locators for the HarvestReadinessCard -----------------------------------

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
DATA_TABLE_ROW = (By.CSS_SELECTOR, "[data-testid='data-table-row']")


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def base_page(browser: WebDriver, base_url: str) -> BasePage:
    """Return a BasePage for generic navigation."""
    return BasePage(browser, base_url)


def _find_readiness_card(driver: WebDriver) -> bool:
    """Return True if a HarvestReadinessCard is visible on the current page."""
    elements = driver.find_elements(*READINESS_CARD)
    return len(elements) > 0 and elements[0].is_displayed()


def _navigate_to_first_plant_detail(base_page: BasePage) -> None:
    """Navigate to the first plant instance detail page via list click."""
    base_page.navigate("/pflanzen")
    base_page.wait_for_loading_complete()

    # NFR-008a: find_elements used here because no dedicated page object
    # exists for the plant list -- this is a cross-page readiness card test.
    rows = base_page.driver.find_elements(*DATA_TABLE_ROW)
    if not rows:
        pytest.skip("No plant instances -- cannot test readiness card")

    base_page.scroll_and_click(rows[0])
    base_page.wait_for_loading_complete()


# -- Tests ------------------------------------------------------------------


class TestHarvestReadinessCard:
    """HarvestReadinessCard display and behavior (Spec: TC-007-035, TC-007-036, TC-007-037)."""

    @pytest.mark.core_crud
    def test_readiness_card_displays_score(
        self,
        base_page: BasePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-030: Readiness card shows overall score with progress bar.

        Spec: TC-007-035 -- Erntereife-Karte zeigt Gesamtscore mit Fortschrittsbalken.
        """
        _navigate_to_first_plant_detail(base_page)
        screenshot(
            "TC-REQ-007-030_plant-detail-for-readiness",
            "Plant detail page for readiness card check",
        )

        if not _find_readiness_card(base_page.driver):
            pytest.skip(
                "No HarvestReadinessCard visible on plant detail -- "
                "readiness data may not exist for this plant"
            )

        screenshot(
            "TC-REQ-007-030_readiness-card",
            "Harvest readiness card visible with score",
        )

        # NFR-008a: find_elements used here because readiness card is a
        # sub-component without its own page object.
        score_els = base_page.driver.find_elements(*READINESS_SCORE)
        assert len(score_els) > 0, (
            "TC-REQ-007-030 FAIL: Expected overall score value in readiness card"
        )

        progress_els = base_page.driver.find_elements(*READINESS_PROGRESS)
        assert len(progress_els) > 0, (
            "TC-REQ-007-030 FAIL: Expected LinearProgress in readiness card"
        )

    @pytest.mark.core_crud
    def test_readiness_card_recommendation_chip(
        self,
        base_page: BasePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-031: Readiness card shows recommendation chip.

        Spec: TC-007-036 -- Empfehlungs-Chip (optimal/approaching/developing).
        """
        _navigate_to_first_plant_detail(base_page)

        if not _find_readiness_card(base_page.driver):
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        # NFR-008a: find_elements used here -- sub-component without page object.
        chip_els = base_page.driver.find_elements(*READINESS_CHIP)
        screenshot(
            "TC-REQ-007-031_readiness-recommendation",
            "Readiness card recommendation chip",
        )

        assert len(chip_els) > 0, (
            "TC-REQ-007-031 FAIL: Expected recommendation chip in readiness card"
        )

        # Verify chip has an appropriate MUI color class
        chip = chip_els[0]
        classes = chip.get_attribute("class") or ""
        valid_colors = ["Success", "Warning", "Info", "Error"]
        has_color = any(c.lower() in classes.lower() for c in valid_colors)
        assert has_color, (
            f"TC-REQ-007-031 FAIL: Expected recommendation chip to have a "
            f"MUI color class, got: {classes}"
        )

    @pytest.mark.core_crud
    def test_readiness_card_indicator_table(
        self,
        base_page: BasePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-032: Readiness card shows indicator breakdown table.

        Spec: TC-007-037 -- Indikator-Aufschluesselungstabelle.
        """
        _navigate_to_first_plant_detail(base_page)

        if not _find_readiness_card(base_page.driver):
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        screenshot(
            "TC-REQ-007-032_readiness-indicators",
            "Readiness card indicator breakdown table",
        )

        # NFR-008a: find_elements used here -- sub-component without page object.
        table_els = base_page.driver.find_elements(*READINESS_INDICATOR_TABLE)
        if not table_els:
            # Indicator table is only shown when indicators exist
            pytest.skip("No indicator breakdown table -- indicators may be empty")

        indicator_rows = base_page.driver.find_elements(*READINESS_INDICATOR_ROWS)
        assert len(indicator_rows) > 0, (
            "TC-REQ-007-032 FAIL: Expected at least one indicator row in "
            "the breakdown table"
        )
