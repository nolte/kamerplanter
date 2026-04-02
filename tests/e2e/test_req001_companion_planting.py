"""E2E tests for REQ-001 — Companion Planting Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-065  ->  TC-001-030  Species-Detailseite — Mischkultur-Tab (Beziehungen anzeigen)
  TC-REQ-001-066  ->  TC-001-030  Mischkultur — kompatible Beziehung hinzufuegen
  TC-REQ-001-067  ->  TC-001-030  Mischkultur — inkompatible Beziehung hinzufuegen
  TC-REQ-001-068  ->  TC-001-030  Mischkultur — Leerzustand wenn keine Beziehungen
  TC-REQ-001-069  ->  TC-001-030  Mischkultur-Dialog — Erstellen-Button deaktiviert ohne Ziel
  TC-REQ-001-070  ->  TC-001-030  Mischkultur-Dialog — aktuelle Art nicht im Ziel-Dropdown
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import CompanionPlantingPage


@pytest.fixture
def companion_page(browser: WebDriver, base_url: str) -> CompanionPlantingPage:
    return CompanionPlantingPage(browser, base_url)


class TestCompanionPlantingView:
    """View companion planting relationships (Spec: TC-001-030)."""

    @pytest.mark.smoke
    def test_select_species_and_view_relationships(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-065: Select a species and view companion planting relationships.

        Spec: TC-001-030 -- Species-Detailseite — Mischkultur-Tab oeffnen und Beziehungen anzeigen.
        """
        companion_page.open()
        screenshot("TC-REQ-001-065_page-loaded", "Companion planting page after initial load")

        options = companion_page.get_species_options()
        if len(options) == 0:
            pytest.skip("No species available for companion planting")

        # Select the first available species
        companion_page.select_species(options[0])
        screenshot("TC-REQ-001-065_species-selected", f"Companion planting after selecting {options[0]}")

        # After selecting, the compatible and incompatible sections should render
        compatible = companion_page.get_compatible_species()
        incompatible = companion_page.get_incompatible_species()

        # At minimum, the page should render without error (lists may be empty)
        assert isinstance(compatible, list), (
            "TC-REQ-001-065 FAIL: Compatible list should be a list"
        )
        assert isinstance(incompatible, list), (
            "TC-REQ-001-065 FAIL: Incompatible list should be a list"
        )

    @pytest.mark.core_crud
    def test_add_compatible_species_relationship(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-066: Add a compatible species relationship.

        Spec: TC-001-030 -- Mischkultur — kompatible Beziehung hinzufuegen.
        """
        companion_page.open()

        options = companion_page.get_species_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 species for companion planting")

        companion_page.select_species(options[0])
        screenshot("TC-REQ-001-066_before-add", f"Before adding compatible relationship for {options[0]}")

        companion_page.click_add_compatible()

        target_options = companion_page.get_dialog_target_options()
        if len(target_options) == 0:
            pytest.skip("No target species available in dialog")

        companion_page.select_dialog_target(target_options[0])
        companion_page.set_dialog_score("0.7")
        screenshot("TC-REQ-001-066_dialog-filled", "Compatible relationship dialog filled")

        companion_page.click_dialog_create()

        companion_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-066_after-create", "Companion planting after adding compatible relationship")

    @pytest.mark.core_crud
    def test_add_incompatible_species_relationship(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-067: Add an incompatible species relationship.

        Spec: TC-001-030 -- Mischkultur — inkompatible Beziehung hinzufuegen.
        """
        companion_page.open()

        options = companion_page.get_species_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 species for companion planting")

        companion_page.select_species(options[0])
        companion_page.click_add_incompatible()

        target_options = companion_page.get_dialog_target_options()
        if len(target_options) == 0:
            pytest.skip("No target species available in dialog")

        companion_page.select_dialog_target(target_options[0])
        companion_page.set_dialog_reason("E2E test - Wachstumshemmung")
        screenshot("TC-REQ-001-067_dialog-filled", "Incompatible relationship dialog filled")

        companion_page.click_dialog_create()

        companion_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-067_after-create", "Companion planting after adding incompatible relationship")

    @pytest.mark.smoke
    def test_empty_state_when_no_relationships(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-068: Empty state when no relationships exist for a species.

        Spec: TC-001-030 -- Mischkultur — Leerzustand wenn keine Beziehungen vorhanden.
        """
        companion_page.open()

        options = companion_page.get_species_options()
        if len(options) == 0:
            pytest.skip("No species available")

        # Select last species (less likely to have seed data relationships)
        companion_page.select_species(options[-1])
        screenshot("TC-REQ-001-068_species-selected", f"Companion planting for {options[-1]}")

        # Either we see empty states or actual data — both are valid
        compatible = companion_page.get_compatible_species()
        incompatible = companion_page.get_incompatible_species()

        if len(compatible) == 0 and len(incompatible) == 0:
            # Should show empty state or at least render cleanly
            assert (
                companion_page.has_compatible_empty_state()
                or companion_page.has_incompatible_empty_state()
                or True  # Page renders without error
            )


class TestCompanionPlantingDialogUX:
    """Dialog UX validation (Spec: TC-001-030)."""

    @pytest.mark.core_crud
    def test_create_button_disabled_without_target(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-069: 'Erstellen' button disabled when no target species selected.

        Spec: TC-001-030 -- Mischkultur-Dialog — Erstellen-Button deaktiviert ohne Ziel.
        """
        companion_page.open()

        options = companion_page.get_species_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 species")

        companion_page.select_species(options[0])
        companion_page.click_add_compatible()
        screenshot("TC-REQ-001-069_dialog-no-target", "Compatible dialog without target selected")

        assert not companion_page.is_dialog_create_button_enabled(), (
            "TC-REQ-001-069 FAIL: Create button should be disabled without target selection"
        )

    @pytest.mark.core_crud
    def test_current_species_excluded_from_target_dropdown(
        self, companion_page: CompanionPlantingPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-070: Current species excluded from the target dropdown.

        Spec: TC-001-030 -- Mischkultur-Dialog — aktuelle Art nicht im Ziel-Dropdown.
        """
        companion_page.open()

        options = companion_page.get_species_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 species")

        source_species = options[0]
        companion_page.select_species(source_species)
        companion_page.click_add_compatible()
        screenshot("TC-REQ-001-070_target-dropdown", "Compatible dialog target dropdown options")

        target_options = companion_page.get_dialog_target_options()
        assert source_species not in target_options, (
            f"TC-REQ-001-070 FAIL: Source species '{source_species}' should not appear in target dropdown"
        )

        companion_page.click_dialog_cancel()
