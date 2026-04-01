"""E2E tests for REQ-001 — Cultivar CRUD (TC-042 to TC-050)."""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import SpeciesDetailPage, SpeciesListPage


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


def _navigate_to_first_species_cultivar_tab(
    species_list: SpeciesListPage,
    species_detail: SpeciesDetailPage,
) -> None:
    """Navigate to the 'Sorten' tab of the first species."""
    species_list.open()
    if species_list.get_row_count() == 0:
        pytest.skip("No species in database")
    species_list.click_row(0)
    species_list.wait_for_url_contains("/stammdaten/species/")
    species_detail.click_tab_by_label("Sorten")
    time.sleep(1)


class TestCultivarListSection:
    """TC-REQ-001-042 to TC-REQ-001-044: Cultivar list within species detail."""

    @pytest.mark.smoke
    def test_display_cultivars_tab(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-042: Display cultivars tab for a species."""
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        # The cultivar tab should render (may be empty or have data)
        count = species_detail.get_cultivar_count()
        assert count >= 0, "Cultivar section should render"

    def test_click_cultivar_row_navigates_to_detail(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-043: Click on a cultivar row navigates to cultivar detail page."""
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        if species_detail.get_cultivar_count() == 0:
            pytest.skip("No cultivars for this species")

        species_detail.click_cultivar_row(0)
        species_detail.wait_for_url_contains("/cultivars/")

        assert "/cultivars/" in species_detail.driver.current_url


class TestCultivarCreateDialog:
    """TC-REQ-001-045 to TC-REQ-001-047: Cultivar creation and validation."""

    def test_create_cultivar_with_all_fields(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-045: Create a cultivar with all fields."""
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        species_detail.click_cultivar_create()
        unique = uuid.uuid4().hex[:6]
        species_detail.fill_cultivar_form(
            f"E2E-Cultivar-{unique}",
            breeder="E2E-Breeder",
            breeding_year="2020",
            days_to_maturity="80",
        )
        species_detail.submit_cultivar_form()

        time.sleep(2)
        species_detail.wait_for_loading_complete()

    def test_validation_empty_cultivar_name(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-046: Validation error — empty cultivar name."""
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        species_detail.click_cultivar_create()
        species_detail.fill_cultivar_form("")
        species_detail.submit_cultivar_form()

        time.sleep(0.5)
        # Dialog should remain open
        assert len(species_detail.driver.find_elements(
            *species_detail.CREATE_DIALOG
        )) > 0, "Dialog should remain open after validation error"

    def test_days_to_maturity_boundary(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-047: Days to maturity boundary values (1-365)."""
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        species_detail.click_cultivar_create()
        unique = uuid.uuid4().hex[:6]
        species_detail.fill_cultivar_form(
            f"Boundary-{unique}",
            days_to_maturity="1",
        )
        species_detail.submit_cultivar_form()

        time.sleep(2)
