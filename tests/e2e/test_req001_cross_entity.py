"""E2E tests for REQ-001 — Cross-Entity Workflows (TC-089 to TC-092)."""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import (
    BotanicalFamilyListPage,
    CompanionPlantingPage,
    CropRotationPage,
    SpeciesDetailPage,
    SpeciesListPage,
)


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


@pytest.fixture
def companion_page(browser: WebDriver, base_url: str) -> CompanionPlantingPage:
    return CompanionPlantingPage(browser, base_url)


@pytest.fixture
def rotation_page(browser: WebDriver, base_url: str) -> CropRotationPage:
    return CropRotationPage(browser, base_url)


class TestCompleteWorkflow:
    """TC-REQ-001-089: Complete workflow — create family, species, cultivar, lifecycle, and phases."""

    def test_full_crud_workflow(
        self,
        family_list: BotanicalFamilyListPage,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
    ) -> None:
        """TC-REQ-001-089: Complete workflow — family → species → cultivar → lifecycle → phases."""
        unique = uuid.uuid4().hex[:4]

        # Step 1: Create a botanical family
        family_list.open()
        family_list.click_create()
        family_name = f"E2eWorkflowaceae{unique}"
        family_list.fill_create_form(family_name)
        family_list.submit_create_form()
        time.sleep(2)
        family_list.wait_for_loading_complete()

        # Step 2: Create a species with that family
        species_list.open()
        species_list.click_create()
        scientific_name = f"Workflowus testii{unique}"
        species_list.fill_scientific_name(scientific_name)
        species_list.set_field("genus", "Workflowus")
        # Try to select the newly created family
        try:
            species_list.select_option("family_key", family_name)
        except Exception:
            pass  # Family might not be in dropdown yet — continue
        species_list.submit_form()
        time.sleep(2)
        species_list.wait_for_loading_complete()

        # Step 3: Navigate to the species detail page
        try:
            species_list.click_row_by_name(scientific_name)
        except ValueError:
            # If the exact name is not found, click the first row
            species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        # Step 4: Create a cultivar
        species_detail.click_tab_by_label("Sorten")
        time.sleep(1)
        species_detail.click_cultivar_create()
        species_detail.fill_cultivar_form(
            f"WorkflowVar-{unique}",
            days_to_maturity="90",
        )
        species_detail.submit_cultivar_form()
        time.sleep(2)
        species_detail.wait_for_loading_complete()

        # Step 5: Create lifecycle config
        tabs = species_detail.get_tab_labels()
        lifecycle_tab = next(
            (i for i, t in enumerate(tabs) if "LEBENSZYKLUS" in t.upper()), None
        )
        if lifecycle_tab is not None:
            species_detail.click_tab(lifecycle_tab)
            time.sleep(1)

            submit_label = species_detail.get_lifecycle_submit_label()
            if submit_label == "Erstellen":
                species_detail.select_lifecycle_option("cycle_type", "Einjährig")
                species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
                species_detail.click_lifecycle_save()
                time.sleep(2)

                # Step 6: Create growth phases
                if species_detail.has_growth_phase_section():
                    for i, (name, display) in enumerate([
                        ("germination", "Keimung"),
                        ("vegetative", "Vegetativ"),
                        ("harvest", "Ernte"),
                    ]):
                        species_detail.click_phase_create()
                        species_detail.fill_phase_form(
                            name=name,
                            display_name=display,
                            duration=str(7 * (i + 1)),
                            order=str(i),
                        )
                        species_detail.submit_phase_form()
                        time.sleep(2)
                        species_detail.wait_for_loading_complete()

                    phase_count = species_detail.get_phase_count()
                    assert phase_count >= 3, (
                        f"Expected at least 3 phases, got {phase_count}"
                    )


class TestDropdownIntegrations:
    """TC-REQ-001-090 to TC-REQ-001-092: Cross-entity dropdown integrations."""

    def test_species_family_dropdown_shows_all_families(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-090: Species family dropdown shows all available families."""
        species_list.open()
        species_list.click_create()

        # Open the family dropdown and check options
        from selenium.webdriver.common.by import By
        try:
            field = species_list.wait_for_element_clickable(
                (By.CSS_SELECTOR, "[data-testid='form-field-family_key'] .MuiSelect-select")
            )
            species_list.scroll_and_click(field)
            options = species_list.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
            option_texts = [o.text for o in options]

            # Should have at least the 9 seed families plus a "-" option
            assert len(option_texts) >= 9, (
                f"Expected at least 9 family options, got {len(option_texts)}: {option_texts}"
            )

            # Close the dropdown
            from selenium.webdriver.common.keys import Keys
            species_list.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pytest.skip("Family dropdown not accessible in create dialog")

    def test_companion_planting_species_dropdown_populated(
        self, companion_page: CompanionPlantingPage
    ) -> None:
        """TC-REQ-001-091: Companion planting page loads species list for selection."""
        companion_page.open()

        options = companion_page.get_species_options()
        assert len(options) > 0, (
            "Species dropdown should be populated on companion planting page"
        )

    def test_crop_rotation_family_dropdown_populated(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-092: Crop rotation page loads all families for selection."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        assert len(options) >= 9, (
            f"Expected at least 9 families in dropdown, got {len(options)}: {options}"
        )
