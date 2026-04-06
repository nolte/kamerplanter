"""E2E tests for REQ-010 — IPM Navigation.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-010.md):
  TC-REQ-010-035  ->  TC-010-047  Navigation zwischen Pflanzenschutz-Unterseiten via Sidebar
  TC-REQ-010-036  ->  TC-010-048  Direktnavigation via URL zu Pflanzenschutz-Seiten (Diseases)
  TC-REQ-010-037  ->  TC-010-048  Direktnavigation via URL zu Pflanzenschutz-Seiten (Treatments)
  TC-REQ-010-038  ->  TC-010-047  Navigation zwischen allen drei IPM-Seiten
  TC-REQ-010-039  ->  TC-010-047  Alle IPM-Seiten haben Erstellen-Button
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

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
    """Cross-page navigation between IPM catalog pages (Spec: TC-010-047, TC-010-048)."""

    @pytest.mark.smoke
    def test_navigate_to_pest_list(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-035: Navigate directly to pest list page.

        Spec: TC-010-047 -- Navigation zwischen Pflanzenschutz-Unterseiten via Sidebar.
        """
        pest_list.open()
        screenshot("TC-REQ-010-035_nav-pests", "Direct navigation to pest list")

        page_el = pest_list.wait_for_element(PestListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-010-035 FAIL: Expected pest-list-page to be visible"
        )
        assert "pflanzenschutz/pests" in pest_list.driver.current_url, (
            f"TC-REQ-010-035 FAIL: Expected URL to contain 'pflanzenschutz/pests', "
            f"got {pest_list.driver.current_url}"
        )

    @pytest.mark.smoke
    def test_navigate_to_disease_list(
        self,
        disease_list: DiseaseListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-036: Navigate directly to disease list page.

        Spec: TC-010-048 -- Direktnavigation via URL zu Pflanzenschutz-Seiten (Diseases).
        """
        disease_list.open()
        screenshot("TC-REQ-010-036_nav-diseases", "Direct navigation to disease list")

        page_el = disease_list.wait_for_element(DiseaseListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-010-036 FAIL: Expected disease-list-page to be visible"
        )
        assert "pflanzenschutz/diseases" in disease_list.driver.current_url, (
            f"TC-REQ-010-036 FAIL: Expected URL to contain 'pflanzenschutz/diseases', "
            f"got {disease_list.driver.current_url}"
        )

    @pytest.mark.smoke
    def test_navigate_to_treatment_list(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-037: Navigate directly to treatment list page.

        Spec: TC-010-048 -- Direktnavigation via URL zu Pflanzenschutz-Seiten (Treatments).
        """
        treatment_list.open()
        screenshot("TC-REQ-010-037_nav-treatments", "Direct navigation to treatment list")

        page_el = treatment_list.wait_for_element(TreatmentListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-010-037 FAIL: Expected treatment-list-page to be visible"
        )
        assert "pflanzenschutz/treatments" in treatment_list.driver.current_url, (
            f"TC-REQ-010-037 FAIL: Expected URL to contain 'pflanzenschutz/treatments', "
            f"got {treatment_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_navigate_between_all_ipm_pages(
        self,
        pest_list: PestListPage,
        disease_list: DiseaseListPage,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-038: Navigate between all three IPM pages sequentially.

        Spec: TC-010-047 -- Navigation zwischen Pflanzenschutz-Unterseiten via Sidebar.
        """
        # Start at pests
        pest_list.open()
        screenshot("TC-REQ-010-038_nav-step1-pests", "Navigation step 1: pest list")
        assert pest_list.wait_for_element(PestListPage.PAGE).is_displayed(), (
            "TC-REQ-010-038 FAIL: Expected pest-list-page to be visible"
        )

        # Navigate to diseases
        disease_list.open()
        screenshot("TC-REQ-010-038_nav-step2-diseases", "Navigation step 2: disease list")
        assert disease_list.wait_for_element(DiseaseListPage.PAGE).is_displayed(), (
            "TC-REQ-010-038 FAIL: Expected disease-list-page to be visible"
        )

        # Navigate to treatments
        treatment_list.open()
        screenshot("TC-REQ-010-038_nav-step3-treatments", "Navigation step 3: treatment list")
        assert treatment_list.wait_for_element(TreatmentListPage.PAGE).is_displayed(), (
            "TC-REQ-010-038 FAIL: Expected treatment-list-page to be visible"
        )

    @pytest.mark.smoke
    def test_each_page_has_create_button(
        self,
        pest_list: PestListPage,
        disease_list: DiseaseListPage,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-039: All IPM pages have a create button.

        Spec: TC-010-047 -- Navigation zwischen Pflanzenschutz-Unterseiten via Sidebar.
        """
        pest_list.open()
        assert pest_list.wait_for_element(PestListPage.CREATE_BUTTON).is_displayed(), (
            "TC-REQ-010-039 FAIL: Pest page should have create button"
        )

        disease_list.open()
        assert disease_list.wait_for_element(DiseaseListPage.CREATE_BUTTON).is_displayed(), (
            "TC-REQ-010-039 FAIL: Disease page should have create button"
        )

        treatment_list.open()
        assert treatment_list.wait_for_element(TreatmentListPage.CREATE_BUTTON).is_displayed(), (
            "TC-REQ-010-039 FAIL: Treatment page should have create button"
        )

        screenshot("TC-REQ-010-039_all-create-buttons", "All IPM pages have create buttons")
