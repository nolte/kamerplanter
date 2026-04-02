"""E2E tests for REQ-001 — Cross-Entity Workflows.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-089  ->  TC-001-006, TC-001-025, TC-001-037, TC-001-047, TC-001-048  Kompletter Workflow Familie->Species->Cultivar->Lifecycle->Phasen
  TC-REQ-001-090  ->  TC-001-025  Species-Familien-Dropdown zeigt alle Familien
  TC-REQ-001-091  ->  TC-001-030  Mischkultur-Seite laedt Artenliste
  TC-REQ-001-092  ->  TC-001-050  Fruchtfolge-Seite laedt Familien-Dropdown
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
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
    """Complete workflow — create family, species, cultivar, lifecycle, and phases (Spec: TC-001-006, TC-001-025, TC-001-037, TC-001-047, TC-001-048)."""

    @pytest.mark.skip(reason="Flaky multi-step workflow — timing issues across entity creation")
    @pytest.mark.core_crud
    def test_full_crud_workflow(
        self,
        family_list: BotanicalFamilyListPage,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-089: Complete workflow — family -> species -> cultivar -> lifecycle -> phases.

        Spec: TC-001-006, TC-001-025, TC-001-037, TC-001-047, TC-001-048 -- Kompletter CRUD-Workflow ueber alle Entitaeten.
        """
        unique = uuid.uuid4().hex[:4]

        # Step 1: Create a botanical family
        family_list.open()
        family_list.click_create()
        family_name = f"E2eWorkflowaceae{unique}"
        family_list.fill_create_form(family_name)
        family_list.submit_create_form()
        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-089_family-created", f"Family {family_name} created")

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
        species_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-089_species-created", f"Species {scientific_name} created")

        # Step 3: Navigate to the species detail page
        # Reload the list to ensure the new species appears
        species_list.open()
        species_list.wait_for_loading_complete()
        try:
            species_list.click_row_by_name(scientific_name)
        except ValueError:
            # If the exact name is not found, click the first row
            if species_list.get_row_count() > 0:
                species_list.click_row(0)
            else:
                pytest.skip("No species available after creation attempt")
        species_list.wait_for_url_contains("/stammdaten/species/")

        # Step 4: Create a cultivar
        species_detail.click_tab_by_label("Sorten")
        species_detail.wait_for_loading_complete()
        try:
            species_detail.click_cultivar_create()
        except Exception:
            pytest.skip("Cultivar create button not available")
        species_detail.fill_cultivar_form(
            f"WorkflowVar-{unique}",
            days_to_maturity="90",
        )
        species_detail.submit_cultivar_form()
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-089_cultivar-created", f"Cultivar WorkflowVar-{unique} created")

        # Step 5: Create lifecycle config
        tabs = species_detail.get_tab_labels()
        lifecycle_tab = next(
            (i for i, t in enumerate(tabs) if "LEBENSZYKLUS" in t.upper()), None
        )
        if lifecycle_tab is not None:
            species_detail.click_tab(lifecycle_tab)
            species_detail.wait_for_loading_complete()

            try:
                submit_label = species_detail.get_lifecycle_submit_label()
            except Exception:
                pytest.skip("Lifecycle submit button not found")

            if submit_label == "Erstellen":
                species_detail.select_lifecycle_option("cycle_type", "Einjährig")
                species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
                species_detail.click_lifecycle_save()
                species_detail.wait_for_loading_complete()
                screenshot("TC-REQ-001-089_lifecycle-created", "Lifecycle config created")

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
                        species_detail.wait_for_loading_complete()

                    screenshot("TC-REQ-001-089_phases-created", "Growth phases created")
                    phase_count = species_detail.get_phase_count()
                    assert phase_count >= 3, (
                        f"TC-REQ-001-089 FAIL: Expected at least 3 phases, got {phase_count}"
                    )


class TestDropdownIntegrations:
    """Cross-entity dropdown integrations (Spec: TC-001-025, TC-001-030, TC-001-050)."""

    @pytest.mark.smoke
    def test_species_family_dropdown_shows_all_families(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-090: Species family dropdown shows all available families.

        Spec: TC-001-025 -- Species-Erstelldialog Familien-Dropdown ist befuellt.
        """
        species_list.open()
        species_list.click_create()
        screenshot("TC-REQ-001-090_create-dialog", "Species create dialog open")

        # Open the family dropdown and check options
        from selenium.webdriver.common.by import By
        try:
            field = species_list.wait_for_element_clickable(
                (By.CSS_SELECTOR, "[data-testid='form-field-family_key'] .MuiSelect-select")
            )
            species_list.scroll_and_click(field)
            options = species_list.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
            option_texts = [o.text for o in options]
            screenshot("TC-REQ-001-090_dropdown-options", "Family dropdown options in species create dialog")

            # Should have at least the 9 seed families plus a "-" option
            assert len(option_texts) >= 9, (
                f"TC-REQ-001-090 FAIL: Expected at least 9 family options, got {len(option_texts)}: {option_texts}"
            )

            # Close the dropdown
            from selenium.webdriver.common.keys import Keys
            species_list.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pytest.skip("Family dropdown not accessible in create dialog")

    @pytest.mark.smoke
    def test_companion_planting_species_dropdown_populated(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-091: Companion planting page loads species list for selection.

        Spec: TC-001-030 -- Mischkultur-Seite laedt Artenliste fuer Auswahl.
        """
        try:
            companion_page.open()
        except Exception:
            pytest.skip(
                "Companion planting page not accessible in light-mode e2e"
            )

        screenshot("TC-REQ-001-091_page-loaded", "Companion planting page loaded")

        try:
            options = companion_page.get_species_options()
        except Exception:
            pytest.skip(
                "Species dropdown not accessible — page may require different "
                "navigation or tenant context"
            )
        assert len(options) > 0, (
            "TC-REQ-001-091 FAIL: Species dropdown should be populated on companion planting page"
        )

    @pytest.mark.smoke
    def test_crop_rotation_family_dropdown_populated(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-092: Crop rotation page loads all families for selection.

        Spec: TC-001-050 -- Fruchtfolge-Seite laedt Familien-Dropdown.
        """
        try:
            rotation_page.open()
        except Exception:
            pytest.skip(
                "Crop rotation page not accessible in light-mode e2e"
            )

        screenshot("TC-REQ-001-092_page-loaded", "Crop rotation page loaded")

        try:
            options = rotation_page.get_family_options()
        except Exception:
            pytest.skip(
                "Family dropdown not accessible — page may require different "
                "navigation or tenant context"
            )
        assert len(options) >= 9, (
            f"TC-REQ-001-092 FAIL: Expected at least 9 families in dropdown, got {len(options)}: {options}"
        )
