"""E2E tests for REQ-010 — IPM Navigation (TC-010-NAV).

Tests cover cross-page navigation between the three IPM catalog pages:
- /pflanzenschutz/pests
- /pflanzenschutz/diseases
- /pflanzenschutz/treatments

NFR-008 SS3.4 screenshot checkpoints at:
1. Page Load
2. After navigation actions
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.disease_list_page import DiseaseListPage
from .pages.pest_list_page import PestListPage
from .pages.treatment_list_page import TreatmentListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def pest_list(browser: WebDriver, base_url: str) -> PestListPage:
    return PestListPage(browser, base_url)


@pytest.fixture
def disease_list(browser: WebDriver, base_url: str) -> DiseaseListPage:
    return DiseaseListPage(browser, base_url)


@pytest.fixture
def treatment_list(browser: WebDriver, base_url: str) -> TreatmentListPage:
    return TreatmentListPage(browser, base_url)


# -- Navigation tests ---------------------------------------------------------


class TestIpmNavigation:
    """Cross-page navigation between IPM catalog pages."""

    def test_navigate_to_pest_list(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-NAV-001: Navigate directly to pest list page."""
        pest_list.open()
        screenshot("req010_060_nav_pests", "Direct navigation to pest list")

        assert pest_list.driver.find_element(
            *PestListPage.PAGE
        ).is_displayed(), "Expected pest-list-page to be visible"
        assert "pflanzenschutz/pests" in pest_list.driver.current_url, (
            f"Expected URL to contain 'pflanzenschutz/pests', got {pest_list.driver.current_url}"
        )

    def test_navigate_to_disease_list(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-NAV-002: Navigate directly to disease list page."""
        disease_list.open()
        screenshot("req010_061_nav_diseases", "Direct navigation to disease list")

        assert disease_list.driver.find_element(
            *DiseaseListPage.PAGE
        ).is_displayed(), "Expected disease-list-page to be visible"
        assert "pflanzenschutz/diseases" in disease_list.driver.current_url, (
            f"Expected URL to contain 'pflanzenschutz/diseases', got {disease_list.driver.current_url}"
        )

    def test_navigate_to_treatment_list(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-NAV-003: Navigate directly to treatment list page."""
        treatment_list.open()
        screenshot("req010_062_nav_treatments", "Direct navigation to treatment list")

        assert treatment_list.driver.find_element(
            *TreatmentListPage.PAGE
        ).is_displayed(), "Expected treatment-list-page to be visible"
        assert "pflanzenschutz/treatments" in treatment_list.driver.current_url, (
            f"Expected URL to contain 'pflanzenschutz/treatments', got {treatment_list.driver.current_url}"
        )

    def test_navigate_between_all_ipm_pages(
        self,
        pest_list: PestListPage,
        disease_list: DiseaseListPage,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-NAV-004: Navigate between all three IPM pages sequentially."""
        # Start at pests
        pest_list.open()
        screenshot("req010_063_nav_step1_pests", "Navigation step 1: pest list")
        assert pest_list.driver.find_element(*PestListPage.PAGE).is_displayed()

        # Navigate to diseases
        disease_list.open()
        screenshot("req010_064_nav_step2_diseases", "Navigation step 2: disease list")
        assert disease_list.driver.find_element(*DiseaseListPage.PAGE).is_displayed()

        # Navigate to treatments
        treatment_list.open()
        screenshot("req010_065_nav_step3_treatments", "Navigation step 3: treatment list")
        assert treatment_list.driver.find_element(*TreatmentListPage.PAGE).is_displayed()

    def test_each_page_has_create_button(
        self,
        pest_list: PestListPage,
        disease_list: DiseaseListPage,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-NAV-005: All IPM pages have a create button."""
        pest_list.open()
        assert pest_list.driver.find_element(
            *PestListPage.CREATE_BUTTON
        ).is_displayed(), "Pest page should have create button"

        disease_list.open()
        assert disease_list.driver.find_element(
            *DiseaseListPage.CREATE_BUTTON
        ).is_displayed(), "Disease page should have create button"

        treatment_list.open()
        assert treatment_list.driver.find_element(
            *TreatmentListPage.CREATE_BUTTON
        ).is_displayed(), "Treatment page should have create button"

        screenshot("req010_066_all_create_buttons", "All IPM pages have create buttons")
